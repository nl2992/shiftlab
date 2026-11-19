"""Fetch one protocol candidate and write its binary stream.

Usage: uv run --no-sync python scripts/paper4_continuation/rbdp/real_data/fetch.py <candidate number 1..30>

Writes data/raw/real_chains/<id>/{raw.*, stream.csv, SOURCE.txt, meta.json}. Only the public sources named in
docs/paper4_continuation/rbdp/real_data/PROTOCOL.md are contacted; no cookies, keys or logins; files > ~5 MB skipped.

Binarisation choices left open by the protocol table (declared here before any fitting):
  * "above median": strictly greater than numpy.median of the (NA-dropped) series; ties map to 0.
  * "rises"/"return > 0": strictly positive first difference / log return; ties map to 0.
  * AirPassengers: centred 2x12 moving average (weights 1/24, 10 x 1/12, 1/24); the first and last 6 months,
    where it is undefined, are dropped.
  * UKgas: annual mean = mean of the four quarters of the same calendar year (series covers whole years).
  * Binance klines: the last 1000 completed-or-current candles returned by one call at retrieval time; x = 1 when
    close > open (ties 0); volume stream: base-asset volume > median of the 1000 values.
  * GHCN-Daily PRCP: element PRCP, rows with empty quality flag, the last 3650 calendar days of the file
    (days with no valid record are dropped, not imputed); x = 1 when PRCP > 0 (tenths of mm).
  * FRED USREC: x = 1 when USREC == 1, whole series as served.
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import requests

ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / "data/raw/real_chains"
RD = "https://vincentarelbundock.github.io/Rdatasets/csv/"
MAX_BYTES = 5_000_000
HEADERS = {"User-Agent": "research-fetch/1.0"}


def above_median(v):
    v = np.asarray(v, float)
    return (v > np.median(v)).astype(int)


def rises(v):
    return (np.diff(np.asarray(v, float)) > 0).astype(int)


def logret_pos(v):
    return (np.diff(np.log(np.asarray(v, float))) > 0).astype(int)


def col(rows, name, drop_na=False):
    out = []
    for r in rows:
        s = r[name]
        if s in ("NA", ""):
            if drop_na:
                continue
            raise ValueError(f"NA in {name}")
        out.append(float(s))
    return np.array(out)


def b_gt(thr):
    return lambda v: (np.asarray(v, float) > thr).astype(int)


# id -> (name, kind, source spec, column, binariser, description)
RDS = {
    1: ("faithful", "datasets/faithful", "eruptions", b_gt(3.0), "eruption duration > 3 min", False),
    2: ("geyser", "MASS/geyser", "duration", b_gt(3.0), "duration > 3 min", False),
    3: ("lynx", "datasets/lynx", "value", above_median, "above median", False),
    4: ("sunspot_year", "datasets/sunspot.year", "value", above_median, "above median", False),
    5: ("nottem", "datasets/nottem", "value", above_median, "above overall median", False),
    6: ("airquality_ozone", "datasets/airquality", "Ozone", above_median, "above median (NA dropped)", True),
    7: ("nile", "datasets/Nile", "value", above_median, "above median", False),
    8: ("lakehuron", "datasets/LakeHuron", "value", above_median, "above median", False),
    9: ("discoveries", "datasets/discoveries", "value", b_gt(3.0), "count > 3", False),
    10: ("nhtemp", "datasets/nhtemp", "value", above_median, "above median", False),
    11: ("eustock_dax", "datasets/EuStockMarkets", "DAX", logret_pos, "daily log return > 0", False),
    12: ("eustock_ftse", "datasets/EuStockMarkets", "FTSE", logret_pos, "daily log return > 0", False),
    22: ("usaccdeaths", "datasets/USAccDeaths", "value", above_median, "above median", False),
    23: ("presidents", "datasets/presidents", "value", above_median, "above median (NA dropped)", True),
    24: ("co2", "datasets/co2", "value", rises, "month-on-month rise", False),
    25: ("lakehuron_diff", "datasets/LakeHuron", "value", rises, "level rises (first difference > 0)", False),
    26: ("nile_diff", "datasets/Nile", "value", rises, "flow rises", False),
    27: ("lynx_diff", "datasets/lynx", "value", rises, "rises", False),
    28: ("sunspot_year_diff", "datasets/sunspot.year", "value", rises, "rises", False),
    29: ("eustock_smi", "datasets/EuStockMarkets", "SMI", logret_pos, "daily log return > 0", False),
    30: ("eustock_cac", "datasets/EuStockMarkets", "CAC", logret_pos, "daily log return > 0", False),
}
SPECIAL = {
    13: ("binance_ethusdt_1m", "binance", ("ETHUSDT", "1m", "dir")),
    14: ("binance_btcusdt_1m", "binance", ("BTCUSDT", "1m", "dir")),
    15: ("binance_ethusdt_1m_volume", "binance", ("ETHUSDT", "1m", "vol")),
    16: ("binance_ethusdt_1h", "binance", ("ETHUSDT", "1h", "dir")),
    17: ("fred_usrec", "fred", None),
    18: ("ghcn_seatac_prcp", "ghcn", "USW00024233"),
    19: ("ghcn_centralpark_prcp", "ghcn", "USW00094728"),
    20: ("airpassengers", "rd_special", "datasets/AirPassengers"),
    21: ("ukgas", "rd_special", "datasets/UKgas"),
}


def cid(n: int) -> str:
    name = RDS[n][0] if n in RDS else SPECIAL[n][0]
    return f"c{n:02d}_{name}"


class FetchError(Exception):
    pass


def http_get(url: str, head_check: bool = True) -> tuple[bytes, dict]:
    if head_check:
        try:
            h = requests.head(url, timeout=60, allow_redirects=True, headers=HEADERS)
            cl = h.headers.get("Content-Length")
            if cl and int(cl) > MAX_BYTES:
                raise FetchError(f"skipped: Content-Length {cl} > {MAX_BYTES} bytes")
        except requests.RequestException:
            pass
    r = requests.get(url, timeout=60, headers=HEADERS)
    if r.status_code != 200:
        raise FetchError(f"HTTP {r.status_code} for {url}")
    if len(r.content) > MAX_BYTES:
        raise FetchError(f"skipped: body {len(r.content)} bytes > {MAX_BYTES}")
    return r.content, {"url": url, "bytes": len(r.content)}


def read_csv(b: bytes) -> list[dict]:
    return list(csv.DictReader(io.StringIO(b.decode("utf-8"))))


def build(n: int):
    """Return (raw_bytes, raw_ext, source_info, stream, meta) for candidate n."""
    if n in RDS:
        name, path, column, binf, desc, dropna = RDS[n]
        b, info = http_get(f"{RD}{path}.csv")
        rows = read_csv(b)
        v = col(rows, column, drop_na=dropna)
        x = binf(v)
        meta = dict(n_raw=len(rows), n_used_series=len(v), rule=desc, column=column,
                    note="strict inequality; ties -> 0")
        return b, "csv", info, x, meta
    name, kind, arg = SPECIAL[n]
    if kind == "rd_special":
        b, info = http_get(f"{RD}{arg}.csv")
        rows = read_csv(b)
        v = col(rows, "value")
        if n == 20:
            w = np.array([1 / 24] + [1 / 12] * 11 + [1 / 24])
            ma = np.convolve(v, w[::-1], mode="valid")  # centred, length len(v)-12
            x = (v[6:-6] > ma).astype(int)
            meta = dict(n_raw=len(v), rule="above centred 2x12 moving average; first/last 6 months dropped",
                        n_dropped_edges=12)
        else:  # UKgas
            times = col(rows, "time")
            years = np.floor(times + 1e-9).astype(int)
            x = np.zeros(len(v), int)
            for y in np.unique(years):
                m = years == y
                if m.sum() != 4:
                    raise FetchError(f"UKgas year {y} has {m.sum()} quarters")
                x[m] = (v[m] > v[m].mean()).astype(int)
            meta = dict(n_raw=len(v), rule="above mean of the same calendar year (4 quarters)")
        return b, "csv", info, x, meta
    if kind == "fred":
        b, info = http_get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=USREC")
        rows = read_csv(b)
        vals = [r["USREC"] for r in rows if r["USREC"] not in (".", "")]
        x = np.array([int(float(s) == 1.0) for s in vals])
        meta = dict(n_raw=len(rows), rule="USREC == 1", first=rows[0], last=rows[-1])
        return b, "csv", info, x, meta
    if kind == "binance":
        sym, itv, what = arg
        last_err = None
        for host in ("https://api.binance.com", "https://data-api.binance.vision"):
            url = f"{host}/api/v3/klines?symbol={sym}&interval={itv}&limit=1000"
            try:
                b, info = http_get(url, head_check=False)
                break
            except (FetchError, requests.RequestException) as ex:
                last_err = ex
        else:
            raise FetchError(f"binance unavailable: {last_err}")
        k = json.loads(b)
        op = np.array([float(r[1]) for r in k])
        cl = np.array([float(r[4]) for r in k])
        vol = np.array([float(r[5]) for r in k])
        x = (cl > op).astype(int) if what == "dir" else above_median(vol)
        meta = dict(n_raw=len(k), rule="close > open" if what == "dir" else "base volume > median",
                    first_open_time_ms=k[0][0], last_open_time_ms=k[-1][0], host=info["url"].split("/api")[0])
        return b, "json", info, x, meta
    if kind == "ghcn":
        url = f"https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/{arg}.csv.gz"
        b, info = http_get(url)
        txt = gzip.decompress(b).decode("utf-8")
        recs = {}
        for r in csv.reader(io.StringIO(txt)):
            # ID, DATE, ELEMENT, VALUE, M, Q, S, OBS
            if len(r) >= 6 and r[2] == "PRCP" and r[5] == "":
                recs[r[1]] = int(r[3])
        days = sorted(recs)
        last = dt.datetime.strptime(days[-1], "%Y%m%d").date()
        cutoff = last - dt.timedelta(days=3649)
        sel = [d for d in days if dt.datetime.strptime(d, "%Y%m%d").date() >= cutoff]
        x = np.array([int(recs[d] > 0) for d in sel])
        meta = dict(n_raw=len(days), rule="PRCP > 0, last 3650 calendar days, valid-quality records only",
                    first_day=sel[0], last_day=sel[-1], n_window_days=3650, n_valid_days=len(sel))
        return b, "csv.gz", info, x, meta
    raise FetchError("unknown kind")


def fetch(n: int) -> dict:
    d = RAW / cid(n)
    d.mkdir(parents=True, exist_ok=True)
    try:
        b, ext, info, x, meta = build(n)
    except (FetchError, requests.RequestException, ValueError, KeyError, OSError) as ex:
        return {"id": cid(n), "ok": False, "error": f"{type(ex).__name__}: {ex}"}
    (d / f"raw.{ext}").write_bytes(b)
    np.savetxt(d / "stream.csv", x, fmt="%d", header="x", comments="")
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sha = hashlib.sha256(b).hexdigest()
    (d / "SOURCE.txt").write_text(f"URL: {info['url']}\nretrieved_utc: {ts}\nbytes: {info['bytes']}\nsha256: {sha}\n")
    meta.update(id=cid(n), n=int(len(x)), n_ones=int(x.sum()), url=info["url"], retrieved_utc=ts,
                bytes=info["bytes"], sha256=sha)
    (d / "meta.json").write_text(json.dumps(meta, indent=1, default=str))
    return {"id": cid(n), "ok": True, **meta}


if __name__ == "__main__":
    print(json.dumps(fetch(int(sys.argv[1])), default=str))
