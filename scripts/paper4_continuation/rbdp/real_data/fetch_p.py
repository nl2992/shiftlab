"""Phase 2 fetchers (Addendum A of PROTOCOL.md): P1..P30. Public key-free endpoints only; one attempt per request,
no retries/workarounds; a non-200 reply is recorded as a fetch failure with the reason.

Tick streams (P1-P22): trades in time order; x_t = 1 when price rose versus the previous trade, trades with equal
price dropped (price changes only); the most recent 2000 non-zero changes are kept. Paging backwards until 2000
changes are available or the raw-byte cap (5 MB) / page cap is reached; if fewer than 500 changes result the
candidate is a fetch failure, if 500..1999 the shorter stream is used and n is recorded.
  Binance aggTrades: limit=1000, then fromId = (smallest id so far) - 1000.
  Coinbase: /products/<id>/trades?limit=1000, then after=<cb-after header> (older).
  Kraken: /0/public/Trades?pair=..; later pages use since = (oldest time ns) - window, window halved until the
          page's last trade reaches the oldest known trade (overlap), duplicates removed by trade id.
  Bitstamp: /api/v2/transactions/<pair>/?time=day (the only look-back the endpoint offers beyond an hour).
P23/P24: Rdatasets faithful / MASS geyser, waiting > 70 (strict). P25-P30: Binance 1 s klines, close > open,
zero-move seconds dropped, last 1000 non-zero, paged back with endTime.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import time

import numpy as np
import requests

import fetch as F

CAP = 5_000_000
MAX_PAGES = 60
HDR = {"User-Agent": "research-fetch/1.0"}
BIN = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "LTCUSDT", "LINKUSDT", "AVAXUSDT"]
CB = ["BTC-USD", "ETH-USD", "SOL-USD", "LTC-USD"]
KR = ["XBTUSD", "ETHUSD", "SOLUSD", "XRPUSD"]
BS = ["btcusd", "ethusd", "ltcusd", "xrpusd"]
K1 = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT"]


def spec(n):
    if 1 <= n <= 10:
        return ("binance_agg", BIN[n - 1], f"p{n:02d}_binance_agg_{BIN[n-1].lower()}")
    if 11 <= n <= 14:
        return ("coinbase", CB[n - 11], f"p{n:02d}_coinbase_{CB[n-11].lower()}")
    if 15 <= n <= 18:
        return ("kraken", KR[n - 15], f"p{n:02d}_kraken_{KR[n-15].lower()}")
    if 19 <= n <= 22:
        return ("bitstamp", BS[n - 19], f"p{n:02d}_bitstamp_{BS[n-19]}")
    if n == 23:
        return ("rd", "datasets/faithful", "p23_faithful_waiting")
    if n == 24:
        return ("rd", "MASS/geyser", "p24_geyser_waiting")
    return ("kline1s", K1[n - 25], f"p{n:02d}_binance_1s_{K1[n-25].lower()}")


def pid(n):
    return spec(n)[2]


class Budget:
    def __init__(self):
        self.bytes = 0
        self.pages = 0
        self.urls = []


def get(url, bud, params=None):
    time.sleep(0.35)
    r = requests.get(url, params=params, timeout=60, headers=HDR)
    if r.status_code != 200:
        raise F.FetchError(f"HTTP {r.status_code} for {r.url}: {r.text[:120]!r}")
    if len(r.content) > CAP:
        raise F.FetchError(f"skipped: single response {len(r.content)} bytes > {CAP}")
    bud.bytes += len(r.content)
    bud.pages += 1
    bud.urls.append(r.url)
    return r


def changes(prices):
    p = np.asarray(prices, float)
    d = np.diff(p)
    d = d[d != 0]
    return (d > 0).astype(int)


def done(prices, bud):
    return len(changes(prices)) >= 2000 or bud.bytes > CAP or bud.pages >= MAX_PAGES


def trades_binance(sym, bud):
    base = "https://api.binance.com/api/v3/aggTrades"
    rows = get(base, bud, {"symbol": sym, "limit": 1000}).json()
    allr = {r["a"]: r for r in rows}
    while True:
        prices = [float(allr[k]["p"]) for k in sorted(allr)]
        lo = min(allr)
        if done(prices, bud) or lo == 0:
            break
        frm = max(0, lo - 1000)
        rows = get(base, bud, {"symbol": sym, "fromId": frm, "limit": min(1000, lo - frm)}).json()
        if not rows:
            break
        for r in rows:
            allr[r["a"]] = r
    ks = sorted(allr)
    return [float(allr[k]["p"]) for k in ks], dict(first_id=ks[0], last_id=ks[-1])


def trades_coinbase(prod, bud):
    url = f"https://api.exchange.coinbase.com/products/{prod}/trades"
    r = get(url, bud, {"limit": 1000})
    allr = {t["trade_id"]: t for t in r.json()}
    after = r.headers.get("cb-after")
    while True:
        prices = [float(allr[k]["price"]) for k in sorted(allr)]
        if done(prices, bud) or not after:
            break
        r = get(url, bud, {"limit": 1000, "after": after})
        rows = r.json()
        if not rows:
            break
        for t in rows:
            allr[t["trade_id"]] = t
        after = r.headers.get("cb-after")
    ks = sorted(allr)
    return [float(allr[k]["price"]) for k in ks], dict(first_id=ks[0], last_id=ks[-1])


def trades_kraken(pair, bud):
    url = "https://api.kraken.com/0/public/Trades"

    def page(since=None):
        prm = {"pair": pair}
        if since is not None:
            prm["since"] = str(int(since))
        j = get(url, bud, prm).json()
        if j.get("error"):
            raise F.FetchError(f"kraken error {j['error']}")
        res = j["result"]
        key = [k for k in res if k != "last"][0]
        return res[key]

    allr = {}
    rows = page()
    for t in rows:
        allr[t[6]] = t
    window = 300.0
    while True:
        srt = sorted(allr.values(), key=lambda t: (t[2], t[6]))
        prices = [float(t[0]) for t in srt]
        if done(prices, bud):
            break
        oldest = srt[0][2]
        tries = 0
        while tries < 8:
            rows = page((oldest - window) * 1e9)
            if not rows:
                break
            if rows[-1][2] >= oldest:  # overlap reached
                break
            window /= 2
            tries += 1
        if not rows or rows[-1][2] < oldest:
            break
        before = len(allr)
        for t in rows:
            allr[t[6]] = t
        if len(allr) == before:
            break
        window *= 2
    srt = sorted(allr.values(), key=lambda t: (t[2], t[6]))
    return [float(t[0]) for t in srt], dict(first_time=srt[0][2], last_time=srt[-1][2])


def trades_bitstamp(pair, bud):
    r = get(f"https://www.bitstamp.net/api/v2/transactions/{pair}/", bud, {"time": "day"})
    rows = sorted(r.json(), key=lambda t: int(t["tid"]))
    return [float(t["price"]) for t in rows], dict(first_tid=rows[0]["tid"], last_tid=rows[-1]["tid"])


def klines_1s(sym, bud):
    url = "https://api.binance.com/api/v3/klines"
    allk = {}
    end = None
    while True:
        prm = {"symbol": sym, "interval": "1s", "limit": 1000}
        if end:
            prm["endTime"] = end
        rows = get(url, bud, prm).json()
        if not rows:
            break
        for k in rows:
            allk[k[0]] = k
        ks = sorted(allk)
        nz = sum(1 for k in ks if allk[k][1] != allk[k][4] and float(allk[k][1]) != float(allk[k][4]))
        end = ks[0] - 1
        if nz >= 1000 or bud.bytes > CAP or bud.pages >= MAX_PAGES:
            break
    ks = sorted(allk)
    x = [int(float(allk[k][4]) > float(allk[k][1])) for k in ks if float(allk[k][4]) != float(allk[k][1])]
    return x, dict(first_open_ms=ks[0], last_open_ms=ks[-1], n_seconds=len(ks)), {k: allk[k] for k in ks}


def fetch(n):
    kind, arg, name = spec(n)
    d = F.RAW / name
    d.mkdir(parents=True, exist_ok=True)
    bud = Budget()
    try:
        raw = None
        if kind == "rd":
            b, info = F.http_get(f"{F.RD}{arg}.csv")
            rows = F.read_csv(b)
            v = F.col(rows, "waiting")
            x = (v > 70).astype(int)
            meta = dict(rule="waiting > 70 (strict)", n_raw=len(v))
            raw, ext, url = b, "csv", info["url"]
        elif kind == "kline1s":
            xs, meta, allk = klines_1s(arg, bud)
            x = np.array(xs[-1000:], int)
            meta.update(rule="1s klines, close > open, zero-move seconds dropped, last 1000 non-zero",
                        n_nonzero_available=len(xs), pages=bud.pages)
            raw, ext, url = json.dumps(list(allk.values())).encode(), "json", "https://api.binance.com/api/v3/klines (interval=1s, paged by endTime)"
        else:
            fn = dict(binance_agg=trades_binance, coinbase=trades_coinbase, kraken=trades_kraken, bitstamp=trades_bitstamp)[kind]
            prices, meta = fn(arg, bud)
            ch = changes(prices)
            if len(ch) < 500:
                raise F.FetchError(f"only {len(ch)} price changes in {len(prices)} trades ({bud.bytes} bytes)")
            x = ch[-2000:]
            meta.update(rule="x=1 when price rose vs previous trade, equal-price trades dropped, last 2000 changes",
                        n_trades_fetched=len(prices), n_changes_available=len(ch), pages=bud.pages)
            raw, ext, url = json.dumps(prices).encode(), "json", bud.urls[0] + " (+%d paged requests)" % (bud.pages - 1)
    except (F.FetchError, requests.RequestException, ValueError, KeyError, IndexError, OSError) as ex:
        return {"id": name, "ok": False, "error": f"{type(ex).__name__}: {ex}"}
    (d / f"raw.{ext}").write_bytes(raw)
    np.savetxt(d / "stream.csv", x, fmt="%d", header="x", comments="")
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sha = hashlib.sha256(raw).hexdigest()
    nbytes = bud.bytes if bud.bytes else len(raw)
    (d / "SOURCE.txt").write_text(f"URL: {url}\nretrieved_utc: {ts}\nbytes_downloaded: {nbytes}\nstored_raw_bytes: {len(raw)}\nsha256_of_stored_raw: {sha}\n")
    meta.update(id=name, n=int(len(x)), n_ones=int(x.sum()), url=url, retrieved_utc=ts, bytes=nbytes, sha256=sha)
    (d / "meta.json").write_text(json.dumps(meta, indent=1, default=str))
    return {"id": name, "ok": True, **meta}


if __name__ == "__main__":
    print(json.dumps(fetch(int(sys.argv[1])), default=str)[:600])
