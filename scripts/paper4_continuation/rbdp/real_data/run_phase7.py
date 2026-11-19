"""Phase 7 (PROTOCOL.md Addendum G): model-promotion streams (A), fresh benchmarks (B, B-ext) until total = 35.

Usage: PYTHONPATH=src uv run --no-sync python scripts/paper4_continuation/rbdp/real_data/run_phase7.py [--smoke] [--families A,B,Bext]
"""

from __future__ import annotations

import sys
from pathlib import Path

import json

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_phase5 as p5  # noqa: E402

ROOT, RES = p5.ROOT, p5.RES
p5.RAW = ROOT / "data/raw/real_chains/phase7"
p5.OUT = RES / "attempts_phase7.jsonl"
p5.LOG = RES / "phase7_run.log"
p5.MANIFEST = p5.RAW / "SOURCE_manifest.jsonl"
p5.START = 25
TARGET = 35
SMOKE = "--smoke" in sys.argv
PROMO = ROOT / "data/raw/real_chains/promotion"
CAP, MIN_N = 3000, 200
FAMS = next((a.split("=")[1] for a in sys.argv if a.startswith("--families=")), "A,B,Bext").split(",")


def stream_from_losses(l0, l1):
    """Challenger-wins stream on disagreement rounds, concatenated over episodes in file order, capped."""
    l0, l1 = np.atleast_2d(l0), np.atleast_2d(l1)
    out, n_ep = [], 0
    for a, b in zip(l0, l1):
        d = a != b
        out.append(((a == 1) & (b == 0))[d].astype(int))
        n_ep += 1
        if sum(len(o) for o in out) >= CAP:
            break
    x = np.concatenate(out) if out else np.zeros(0, int)
    return x[:CAP], n_ep


def family_A():
    order = [("atlas_v2_losses", n) for n in "airlines bank criteo elec2 openml_ldpa rialto spam uci_occupancy weather".split()]
    order += [("sprint_fresh_losses", n) for n in "appliances beijing_pm25 bike_hour household_power metro".split()]
    scr = sorted(p.stem for p in (PROMO / "screen100_losses").glob("*.npz"))
    order += [("screen100_losses", n) for n in scr]
    for d, n in order:
        cid = f"A:{d.replace('_losses', '')}/{n}"
        z = np.load(PROMO / d / f"{n}.npz")
        x, n_ep = stream_from_losses(z["l0"], z["l1"])
        meta = {"family": "A", "source_dir": d, "name": n, "episodes_used": n_ep}
        if len(x) < MIN_N:
            yield cid, {**meta, "status": f"too short ({len(x)})", "n": int(len(x))}, None
        else:
            yield cid, meta, p5.both(x)


# ---------------------------------------------------------------- Families B / B-ext: fresh benchmarks
import gzip  # noqa: E402
import io  # noqa: E402
import time  # noqa: E402

BLOCK, WIN_FRAC, WIN_CAP = 2000, 0.10, 50_000


def promotion_losses(X, y):
    """Fixed chronological pipeline: incumbent = logistic regression on the first 10%% of the stream (capped at 50k rows);
    challenger = the same model retrained every 2,000 rounds on the most recent 10%% window; 0/1 loss on the next 2,000
    rounds. Blocks are produced lazily until the disagreement stream has CAP rounds. Returns (l0, l1) as episode lists."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    X = np.asarray(X, float)
    y = np.asarray(y)
    n = len(y)
    w = int(min(max(WIN_FRAC * n, 50), WIN_CAP))

    def fit(a, b):
        if len(np.unique(y[a:b])) < 2:
            return None
        m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=200))
        m.fit(X[a:b], y[a:b])
        return m

    inc = fit(0, w)
    L0, L1, got = [], [], 0
    t = w
    while t + BLOCK <= n and got < CAP and inc is not None:
        ch = fit(max(0, t - w), t)
        if ch is None:
            t += BLOCK
            continue
        sl = slice(t, t + BLOCK)
        a = (inc.predict(X[sl]) != y[sl]).astype(int)
        b = (ch.predict(X[sl]) != y[sl]).astype(int)
        L0.append(a)
        L1.append(b)
        got += int((a != b).sum())
        t += BLOCK
    return L0, L1


def _fetch(url, name, timeout=300):
    dest = p5.RAW / "raw" / name
    if dest.exists() and dest.stat().st_size > 0:
        return dest.read_bytes()
    time.sleep(0.4)
    return p5.curl(url, dest, timeout=timeout)


def _csv(data, gz=False, **kw):
    import pandas as pd

    if gz:
        data = gzip.decompress(data)
    return pd.read_csv(io.BytesIO(data), **kw)


def _openml(name):
    from sklearn.datasets import fetch_openml

    d = fetch_openml(name=name, version=1, as_frame=True, data_home=str(p5.RAW / "openml"), parser="auto")
    return d


def _tab_from_frame(df, target):
    import pandas as pd

    y = df[target]
    X = df.drop(columns=[target])
    X = X.drop(columns=[c for c in X.columns if (X[c].dtype == object or str(X[c].dtype) == "category") and X[c].nunique() > 50])
    X = pd.get_dummies(X, dtype=float)
    return X.to_numpy(float), (y.astype("category").cat.codes.to_numpy())


def load_covtype():
    d = _fetch("https://archive.ics.uci.edu/ml/machine-learning-databases/covtype/covtype.data.gz", "covtype.data.gz", 600)
    if d is None:
        return None
    df = _csv(d, gz=True, header=None)
    return df.iloc[:, :-1].to_numpy(float), (df.iloc[:, -1].to_numpy() == df.iloc[:, -1].mode()[0]).astype(int)


def load_poker():
    parts = []
    for f in ("poker-hand-training-true.data", "poker-hand-testing.data"):
        d = _fetch(f"https://archive.ics.uci.edu/ml/machine-learning-databases/poker/{f}", f, 600)
        if d is None:
            return None
        parts.append(_csv(d, header=None))
    import pandas as pd

    df = pd.concat(parts, ignore_index=True)
    X = df.iloc[:, :-1].to_numpy(float)
    return X, (df.iloc[:, -1].to_numpy() > 0).astype(int)  # target: any scoring hand


def load_kdd():
    """KDD Cup 99 (10%): the UCI gz files are empty placeholders, so the same file is taken from the figshare mirror."""
    d = _fetch("https://ndownloader.figshare.com/files/5976042", "kddcup99_10.gz", 300)
    if d is None:
        return None
    df = _csv(d, gz=True, header=None)
    y = (df.iloc[:, -1] != "normal.").astype(int).to_numpy()
    import pandas as pd

    X = pd.get_dummies(df.iloc[:, :-1], columns=[1, 2, 3], dtype=float).to_numpy(float)
    return X, y


def load_sensor():
    d = _fetch("https://db.csail.mit.edu/labdata/data.txt.gz", "intel_data.txt.gz", 900)
    if d is None:
        return None
    df = _csv(d, gz=True, sep=r"\s+", header=None, names="date time epoch moteid temp hum light volt".split(),
              on_bad_lines="skip", nrows=600_000)
    df = df.dropna(subset=["temp", "hum", "light", "volt", "moteid"])
    y = (df["temp"] > df["temp"].iloc[: int(0.1 * len(df))].median()).astype(int).to_numpy()
    return df[["hum", "light", "volt", "moteid"]].to_numpy(float), y


def load_ozone():
    d = _fetch("https://archive.ics.uci.edu/ml/machine-learning-databases/ozone/eighthr.data", "ozone_eighthr.data")
    if d is None:
        return None
    df = _csv(d, header=None, na_values="?").iloc[:, 1:]
    df = df.fillna(df.median())
    return df.iloc[:, :-1].to_numpy(float), df.iloc[:, -1].to_numpy().astype(int)


def load_openml_target(name, target=None, max_rows=None):
    def f():
        import pandas as pd

        d = _openml(name)
        df = d.frame
        tcol = target or (d.target.name if getattr(d, "target", None) is not None and hasattr(d.target, "name") else df.columns[-1])
        if max_rows:
            df = df.iloc[:max_rows]
        df = df.dropna()
        yv = df[tcol]
        if pd.api.types.is_numeric_dtype(yv) and yv.nunique() > 20:  # regression target -> above median
            df = df.assign(**{tcol: (yv > yv.median()).astype(int)})
        X, y = _tab_from_frame(df, tcol)
        return X, y
    return f


def load_insects():
    """INSECTS (Souza et al. 2020) is hosted on a Google Drive share, not on OpenML/UCI/Zenodo; not fetched."""
    return None


def benchmark_list_B():
    out = []
    out.append(("B:INSECTS", load_insects))
    out += [("B:covtype", load_covtype), ("B:poker", load_poker), ("B:kdd99_10pct", load_kdd),
            ("B:intel_sensor", load_sensor), ("B:ozone", load_ozone)]
    return out


def benchmark_list_Bext():
    out = []
    for nm in ["electricity", "Bike_Sharing_Demand", "MagicTelescope", "Higgs", "PhishingWebsites", "SMSSpam", "adult",
               "bank-marketing", "default-of-credit-card-clients", "OnlineNewsPopularity", "occupancy", "gas-drift"]:
        out.append((f"Bext:{nm}", load_openml_target(nm, max_rows=200_000 if nm == "Higgs" else None)))
    return out


def _bench_family(lst, fam):
    for cid, loader in lst:
        meta = {"family": fam, "name": cid.split(":", 1)[1]}
        try:
            data = loader()
        except Exception as e:  # source failure: record and move on
            yield cid, {**meta, "status": "fetch failed", "error": repr(e)[:200]}, None
            continue
        if data is None:
            yield cid, {**meta, "status": "fetch failed"}, None
            continue
        X, y = data
        meta["n_rows"] = int(len(y))
        try:
            L0, L1 = promotion_losses(X, y)
        except Exception as e:
            yield cid, {**meta, "status": "pipeline failed", "error": repr(e)[:200]}, None
            continue
        x, n_ep = stream_from_losses(np.array(L0), np.array(L1)) if L0 else (np.zeros(0, int), 0)
        meta["episodes_used"] = n_ep
        if len(x) < MIN_N:
            yield cid, {**meta, "status": f"too short ({len(x)})", "n": int(len(x))}, None
        else:
            yield cid, meta, p5.both(x)


def family_B():
    yield from _bench_family(benchmark_list_B(), "B")


def family_Bext():
    yield from _bench_family(benchmark_list_Bext(), "Bext")


SHARD = next((a.split("=")[1] for a in sys.argv if a.startswith("--shard=")), None)


def merge():
    """Replay the shard outputs in the protocol order into attempts_phase7.jsonl, stopping when the total reaches 35."""
    import json

    recs = {}
    for f in sorted(RES.glob("attempts_phase7_shard*.jsonl")):
        for line in open(f):
            d = json.loads(line)
            recs[d["id"]] = d
    done = p5.done_ids()
    for fam in ("A", "B", "Bext"):
        if fam not in FAMS:
            continue
        gen = {"A": family_A, "B": family_B, "Bext": family_Bext}[fam]
        for cid, _, _ in gen():
            if cid in done:
                continue
            if p5.tally() >= TARGET:
                p5.log("TARGET reached in merge; stopping")
                return
            if cid not in recs:
                p5.log("merge: missing", cid)
                return
            p5.emit(recs[cid])
            p5.log("DONE(merge)", cid, recs[cid].get("status"), "positive", recs[cid].get("positive"), "TALLY", p5.tally())


def main():
    RES.mkdir(parents=True, exist_ok=True)
    if "--merge" in sys.argv:
        return merge()
    if SHARD:
        k, n = map(int, SHARD.split("/"))
        p5.OUT_MAIN = p5.OUT
        p5.OUT = RES / f"attempts_phase7_shard{k}.jsonl"
        p5.LOG = RES / f"phase7_shard{k}.log"
    done = p5.done_ids()
    if SHARD:
        main_done = {json.loads(line)["id"] for line in open(p5.OUT_MAIN)} if p5.OUT_MAIN.exists() else set()
        done |= main_done
    fams = {"A": family_A, "B": family_B, "Bext": family_Bext}
    idx = -1
    for f in FAMS:
        for cid, meta, streams in fams[f]():
            idx += 1
            if SHARD and (idx % n != k or cid in main_done):
                continue
            if SMOKE:
                print(cid, meta, None if streams is None else [(o, len(x), int(np.sum(x)), round(float(np.corrcoef(x[:-1], x[1:])[0, 1]), 3) if x.std() else None) for o, x in streams[:1]], flush=True)
                continue
            if cid in done:
                continue
            if not SHARD and p5.tally() >= TARGET:
                p5.log("TARGET reached; stopping")
                return
            rec = {"id": cid, **meta}
            if streams is None:
                rec.setdefault("status", "fetch failed")
                rec["positive"] = False
            else:
                rec.update(p5.eval_streams(cid, streams))
            p5.emit(rec)
            p5.log("DONE", cid, rec.get("status"), "positive", rec.get("positive"), "TALLY", p5.tally())
        p5.log("family", f, "finished; tally", p5.tally())
    p5.log("lists exhausted; final tally", p5.tally())


if __name__ == "__main__":
    main()
