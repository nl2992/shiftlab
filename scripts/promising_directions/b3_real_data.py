"""B3: registered real-data evaluation of certified switching (P3b) on chronological streams.

Protocol: docs/promising_directions/protocols/B3-real-data-certified-switching.md (sha256 pinned
below). P0, P1 (reference), P2, P3b come from scripts/promising_directions/b1_certified_switching.py
exactly as at commit 041bc26 (run_policies with b2=True on real per-event 0/1 losses; no policy
code is modified). P6 (fixed-sample paired batch test) is implemented here.

Phases:
  smoke   dev windows only (2 episodes per stream, 5 seeds); locked windows are never parsed.
  run     the registered run (locked windows); resumable JSONL per stream; writes summary.json.
  summary recompute summary.json from the JSONL files.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import time
import warnings
import zipfile
from datetime import UTC, datetime
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy import sparse
from scipy.stats import binomtest
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/promising_directions/protocols/B3-real-data-certified-switching.md"
PROTOCOL_SHA256 = "b17b5a318e65be5ed7729357fb1f0692c0764b6444a4f686797756fb420cba3a"
B1_PATH = ROOT / "scripts/promising_directions/b1_certified_switching.py"
B1_COMMIT = "041bc26"
AUDIT = ROOT / "docs/promising_directions/results/realdata_audit"
OUT = ROOT / "docs/promising_directions/results/b3"
RAW = Path("C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/data/raw")

T_EP = 2000
N_SEEDS = 100
SEED_BASE = 20261101
BOOT = 2000
CQ = 0.05
SAFE_MARGIN = 0.02
P6_N = 50
POLICIES = ("P0", "P1", "P2", "P3b", "P6")
SETTINGS = {
    "B200_cs5": (200, 5.0),
    "B200_cs20": (200, 20.0),
    "B400_cs5": (400, 5.0),
}
PRIMARY = "B200_cs5"

# Row counts, imposed delays (protocol table) and exposure status.
STREAMS = {
    "airlines": {"n": 539383, "delay": 100, "status": "unexposed"},
    "weather": {"n": 18159, "delay": 1, "status": "unexposed"},
    "spam": {"n": 9324, "delay": 50, "status": "unexposed"},
    "bank": {"n": 41188, "delay": 100, "status": "unexposed"},
    "rialto": {"n": 82250, "delay": 100, "status": "unexposed"},
    "elec2": {"n": 45312, "delay": 48, "status": "partly exposed", "locked_start": 36250},
    "criteo": {"n": 16468027, "delay": 100, "status": "partly exposed (label-maturity counts)"},
}
FETCHED = ("airlines", "weather", "spam", "bank", "rialto")


# ----------------------------------------------------------------------------- b1 import
def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=False
    )


def load_b1():
    """Import b1_certified_switching as at commit 041bc26. Returns (module, record)."""
    rel = str(B1_PATH.relative_to(ROOT)).replace("\\", "/")
    unchanged = git("diff", "--quiet", B1_COMMIT, "--", rel).returncode == 0
    path, how = B1_PATH, "worktree file (git diff --quiet 041bc26 is clean)"
    if not unchanged:
        src = git("show", f"{B1_COMMIT}:{rel}")
        path = Path(tempfile.mkdtemp()) / "b1_certified_switching.py"
        path.write_text(src.stdout, encoding="utf-8")
        how = "extracted from 041bc26 via git show (worktree file differs)"
    spec = importlib.util.spec_from_file_location("b1_certified_switching", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    rec = {"commit": B1_COMMIT, "source": how, "path": str(path)}
    rec["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return mod, rec


b1, B1_RECORD = load_b1()


# ----------------------------------------------------------------------------- episodes
def episode_plan(start: int, length: int, kmax: int = 50) -> list[int]:
    """K = min(kmax, floor(L / 2000)) non-overlapping episodes at start + i * floor(L / K)."""
    k = min(kmax, length // T_EP)
    step = length // k
    return [start + i * step for i in range(k)]


def episode_u(ep_index: int, n_seeds: int) -> np.ndarray:
    """(T, n_seeds) query-randomisation draws; column j depends only on (episode, seed j)."""
    cols = [
        np.random.default_rng(np.random.SeedSequence([SEED_BASE, ep_index, j])).random(T_EP)
        for j in range(n_seeds)
    ]
    return np.stack(cols, axis=1)


# ----------------------------------------------------------------------------- P6
@cache
def p6_reject(k: int, n: int) -> bool:
    """One-sided exact binomial test of H0: P(challenger correct | disagreement) <= 1/2."""
    if n <= 0:
        return False
    return bool(binomtest(int(k), int(n), 0.5, alternative="greater").pvalue <= 0.05)


def run_p6(l0, l1, u, budget: int, p) -> dict:
    """P6: query disagreements with P3b's pacing; test the first 50 released labels once.

    Labels are issued at t and released at t + delay (as in b1's Cert). Issuing stops once the test
    has run. If the budget is exhausted before 50 labels exist, the test runs on the released
    labels once all issued ones are released. Promote on rejection; never roll back.
    """
    t_len, n = u.shape
    dis_all = l0 != l1
    dep = np.zeros(n, dtype=np.int8)
    loss = np.zeros(n)
    rem = np.full(n, budget)
    queries = np.zeros(n, dtype=np.int64)
    xbuf = np.zeros((p.delay, n), dtype=np.int8)  # 0 none, 1 challenger correct, 2 incumbent
    rel = np.zeros(n, dtype=np.int64)
    kcnt = np.zeros(n, dtype=np.int64)
    tested = np.zeros(n, dtype=bool)
    t_prom = np.full(n, np.nan)
    ndis = np.zeros(n)
    for t in range(t_len):
        l0t, l1t = l0[t], l1[t]
        loss += np.where(dep == 0, l0t, l1t)
        slot = t % p.delay
        rate = (ndis + p.prior_rate * p.prior_w) / (t + p.prior_w)
        q = np.clip(rem / np.maximum(rate * (p.T - t), 1e-9), p.pmin, 1.0)
        q = np.where(rem > 0, q, 0.0)
        ask = dis_all[t] & (u[t] < q) & ~tested
        rem = rem - ask
        queries += ask
        if t - p.delay >= 0:
            code = xbuf[slot]
            got = code > 0
            take = got & (rel < P6_N)
            kcnt += take & (code == 1)
            rel += got
        xbuf[slot] = np.where(ask, np.where(l1t == 0, 1, 2), 0).astype(np.int8)
        in_flight = queries - rel
        fire = ~tested & ((rel >= P6_N) | ((rem == 0) & (in_flight == 0) & (queries > 0)))
        for i in np.flatnonzero(fire):
            if p6_reject(int(kcnt[i]), int(min(rel[i], P6_N))):
                dep[i] = 1
                t_prom[i] = t + 1
        tested |= fire
        ndis = ndis + dis_all[t]
    return {
        "loss": loss,
        "queries": queries,
        "switches": (~np.isnan(t_prom)).astype(np.int64),
        "rollbacks": np.zeros(n, dtype=np.int64),
        "t_prom": t_prom,
    }


# ----------------------------------------------------------------------------- one episode
def run_episode(l0, l1, u, budget: int, delay: int, base_err: float) -> dict:
    """All five policies on one episode. l0, l1: (T,) 0/1 losses; u: (T, n_seeds)."""
    p = b1.Params(T=T_EP, delay=delay, base_err=base_err, eps=0.05)
    n = u.shape[1]
    a0 = np.repeat(np.asarray(l0, dtype=np.int8)[:, None], n, axis=1)
    a1 = np.repeat(np.asarray(l1, dtype=np.int8)[:, None], n, axis=1)
    res = b1.run_policies(a0, a1, u, budget, (), p, b2=True)
    p0, p1 = b1.simple_out(a0, a1)
    return {
        "P0": p0,
        "P1": p1,
        "P2": res["P2"],
        "P3b": res["P3b"],
        "P6": run_p6(a0, a1, u, budget, p),
    }


def episode_rows(stream: str, ep: int, start: int, pols: dict, delay: int, n_seeds: int, st):
    rows = []
    for key, (budget, cs) in SETTINGS.items():
        out = {}
        for name in POLICIES:
            d = pols[budget][name]
            cost = d["loss"] + CQ * d["queries"] + cs * d["switches"]
            out[name] = {
                "mean_cost": float(cost.mean()),
                "mean_loss": float(np.mean(d["loss"])),
                "mean_labels": float(np.mean(d["queries"])),
                "mean_switches": float(np.mean(d["switches"])),
                "mean_rollbacks": float(np.mean(d["rollbacks"])),
                "promotion_rate": float(np.mean(~np.isnan(d["t_prom"]))),
                "cost_seeds": [round(float(x), 6) for x in cost],
            }
        rows.append(
            {
                "stream": stream,
                "episode": ep,
                "start": int(start),
                "setting": key,
                "budget": budget,
                "cs": cs,
                "delay": delay,
                "n_seeds": n_seeds,
                "episode_stats": st,
                "policies": out,
            }
        )
    return rows


# ----------------------------------------------------------------------------- models
def mk_fetched(kind: str):
    if kind == "LR":
        return LogisticRegression(max_iter=300, C=1.0)
    return HistGradientBoostingClassifier(
        max_iter=100, max_depth=4, learning_rate=0.1, random_state=0
    )


def mk_lr_pipe():
    return make_pipeline(
        SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(C=1.0, max_iter=300)
    )


def mk_hgb_pipe():
    return HistGradientBoostingClassifier(
        max_iter=100, learning_rate=0.1, max_leaf_nodes=15, random_state=0
    )


def prep(xtr):
    """Train-only preprocessing, as the archived fetch_audit.py."""
    if sparse.issparse(xtr):
        return lambda a: a
    num = xtr.select_dtypes("number").columns.tolist()
    cat = [c for c in xtr.columns if c not in num]
    sc = StandardScaler().fit(xtr[num]) if num else None
    oh = (
        OneHotEncoder(handle_unknown="ignore", min_frequency=20, sparse_output=False).fit(xtr[cat])
        if cat
        else None
    )

    def f(a):
        parts = []
        if sc is not None:
            parts.append(sc.transform(a[num]))
        if oh is not None:
            parts.append(oh.transform(a[cat]))
        return np.hstack(parts)

    return f


# ----------------------------------------------------------------------------- audit JSON
def audit_expected(stream: str) -> dict:
    if stream in FETCHED:
        d = json.loads((AUDIT / "fetched" / f"{stream}_dev_audit.json").read_text())
        sel = d["selected_pair"]
        r = d["pairs"][sel]
        return {
            "pair": sel,
            "inc_err": r["inc_err"],
            "chal_err": r["chal_err"],
            "disagree": r["disagree"],
            "mean_adv": r["mean_adv"],
        }
    d = json.loads((AUDIT / f"{stream}_dev.json").read_text())
    rows = d["pairs"]["click"] if stream == "criteo" else d["pairs"]
    r = next(x for x in rows if x["pair"] == "B")
    return {
        "pair": "B",
        "inc_err": r["err0"],
        "chal_err": r["err1"],
        "disagree": r["disagree"],
        "mean_adv": r["adv_mean"],
    }


def dev_check(stream: str, l0, l1) -> dict:
    got = {
        "inc_err": float(l0.mean()),
        "chal_err": float(l1.mean()),
        "disagree": float((l0 != l1).mean()),
        "mean_adv": float((l0.astype(float) - l1).mean()),
    }
    exp = audit_expected(stream)
    diff = {k: abs(got[k] - exp[k]) for k in got}
    return {
        "pair": exp["pair"],
        "recomputed": got,
        "audit": {k: exp[k] for k in got},
        "abs_diff": diff,
        "max_abs_diff": max(diff.values()),
        "match_1e-9": bool(max(diff.values()) < 1e-9),
        "dev_rows": len(l0),
    }


# ----------------------------------------------------------------------------- loaders
def load_fetched(name: str, limit: int):
    """Features and labels for rows < limit. Rows beyond `limit` are discarded at load."""
    if name == "bank":
        z = zipfile.ZipFile(RAW / "uci_bank_marketing/bank-marketing.zip")
        z2 = zipfile.ZipFile(io.BytesIO(z.read("bank-additional.zip")))
        d = pd.read_csv(io.BytesIO(z2.read("bank-additional/bank-additional-full.csv")), sep=";")
        d = d.iloc[:limit]
        y = (d["y"] == "yes").to_numpy().astype(int)
        return d.drop(columns=["y", "duration"]), y
    if name == "airlines":
        d = pd.read_parquet(RAW / "openml_airlines_1169/dataset_1169.pq").iloc[:limit]
        y = (d["Delay"].astype(str) == "1").to_numpy().astype(int)
        x = d.drop(columns=["Delay"]).copy()
        for c in ["Airline", "AirportFrom", "AirportTo", "DayOfWeek"]:
            x[c] = x[c].astype(str)
        return x, y
    if name == "weather":
        x = pd.read_csv(RAW / "weather_elwell_polikar/NEweather_data.csv", header=None, nrows=limit)
        y = pd.read_csv(
            RAW / "weather_elwell_polikar/NEweather_class.csv", header=None, nrows=limit
        )[0].to_numpy()
        return x, y.astype(int)
    if name == "rialto":
        x = pd.read_csv(RAW / "rialto/rialto.data", sep=" ", header=None, nrows=limit)
        y = np.loadtxt(RAW / "rialto/rialto.labels", dtype=int, max_rows=limit)
        return x, y
    z = zipfile.ZipFile(RAW / "spam_katakis/spam.zip")
    y = np.loadtxt(io.BytesIO(z.read("spam/spam.labels")), dtype=int)[:limit]
    rows = []
    with z.open("spam/spam.data") as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            rows.append(sparse.csr_matrix(np.array(line.split(), dtype=np.float32)))
    return sparse.vstack(rows).tocsr(), y


def build_fetched(name: str, ep_starts: list[int] | None, dev_eps: int):
    """Train the frozen pair; return dev losses and episode losses (locked or dev)."""
    n = STREAMS[name]["n"]
    n15, n30, n60 = int(0.15 * n), int(0.3 * n), int(0.6 * n)
    limit = n60 if ep_starts is None else max(n60, max(ep_starts) + T_EP)
    x, y = load_fetched(name, limit)
    classes = np.unique(y[:n60])
    if len(classes) > 2:
        vals, cnt = np.unique(y[:n30], return_counts=True)
        y = (y == int(vals[np.argmax(cnt)])).astype(int)
    else:
        y = (y == classes.max()).astype(int)
    sl = (lambda a, b: x[a:b]) if sparse.issparse(x) else (lambda a, b: x.iloc[a:b])
    f = prep(sl(0, n30))
    spec = {
        "airlines": (("LR", 0, n15), ("HGB", n15, n30)),
        "weather": (("LR", 0, n15), ("HGB", 0, n30)),
        "spam": (("LR", 0, n15), ("LR", n15, n30)),
        "bank": (("LR", 0, n15), ("LR", n15, n30)),
        "rialto": (("LR", 0, n15), ("HGB", 0, n30)),
    }[name]
    models = []
    for kind, a, b in spec:
        if len(np.unique(y[a:b])) < 2:
            models.append(int(y[a:b][0]))
        else:
            models.append(mk_fetched(kind).fit(f(sl(a, b)), y[a:b]))

    def loss(m, a, b):
        xx = f(sl(a, b))
        pr = np.full(xx.shape[0], m) if isinstance(m, int) else m.predict(xx)
        return (pr != y[a:b]).astype(np.int8)

    l0, l1 = loss(models[0], n30, n60), loss(models[1], n30, n60)
    eps = []
    if ep_starts is None:
        for s in episode_plan(0, len(l0), dev_eps):
            eps.append((s + n30, l0[s : s + T_EP], l1[s : s + T_EP]))
    else:
        for s in ep_starts:
            eps.append((s, loss(models[0], s, s + T_EP), loss(models[1], s, s + T_EP)))
    return l0, l1, eps


ELEC_COLS = ["date", "day", "period", "nswprice", "nswdemand", "vicprice", "vicdemand", "transfer"]


def build_elec2(ep_starts: list[int] | None, dev_eps: int):
    n = STREAMS["elec2"]["n"]
    ntr, nd = int(0.3 * n), int(0.6 * n)
    limit = nd if ep_starts is None else max(ep_starts) + T_EP
    lines = (RAW / "elec2/electricity-normalized.arff").read_text(encoding="utf8").splitlines()
    k = next(i for i, ln in enumerate(lines) if ln.strip().lower() == "@data") + 1
    data = [ln for ln in lines[k:] if ln.strip()]
    if len(data) != n:
        raise RuntimeError(f"elec2 row count {len(data)} != {n}")
    df = pd.read_csv(io.StringIO("\n".join(data[:limit])), header=None, names=[*ELEC_COLS, "cls"])
    y = (df.pop("cls").str.strip() == "UP").astype(int).to_numpy()
    x = df[ELEC_COLS[2:]].to_numpy().astype(float)
    h = ntr // 2
    m0 = mk_lr_pipe().fit(x[:h], y[:h])
    m1 = mk_hgb_pipe().fit(x[h:ntr], y[h:ntr])

    def loss(m, a, b):
        return (m.predict(x[a:b]) != y[a:b]).astype(np.int8)

    l0, l1 = loss(m0, ntr, nd), loss(m1, ntr, nd)
    eps = []
    if ep_starts is None:
        for s in episode_plan(0, len(l0), dev_eps):
            eps.append((s + ntr, l0[s : s + T_EP], l1[s : s + T_EP]))
    else:
        for s in ep_starts:
            eps.append((s, loss(m0, s, s + T_EP), loss(m1, s, s + T_EP)))
    return l0, l1, eps


def build_criteo(ep_starts: list[int] | None, dev_eps: int):
    n = STREAMS["criteo"]["n"]
    ne = int(0.6 * n)
    use = ["timestamp", "campaign", "conversion", "conversion_timestamp", "click"]
    use += ["time_since_last_click", *[f"cat{i}" for i in range(1, 10)]]
    path = RAW / "criteo_attribution/criteo_attribution_dataset.tsv.gz"
    want = [] if ep_starts is None else [(s, s + T_EP) for s in ep_starts]
    parts, locked = [], {}
    g0 = 0
    for ch in pd.read_csv(path, sep="\t", usecols=use, chunksize=1_000_000):
        g1 = g0 + len(ch)
        if g0 < ne:
            parts.append(ch.iloc[: ne - g0 : 10] if g1 > ne else ch.iloc[::10])
        for a, b in want:
            lo, hi = max(a, g0), min(b, g1)
            if lo < hi:
                locked.setdefault(a, []).append(ch.iloc[lo - g0 : hi - g0])
        g0 = g1
        if not want and g0 >= ne:
            break
        if want and g0 >= max(b for _, b in want):
            break
    d = pd.concat(parts).reset_index(drop=True)
    tcut = float(d["timestamp"].iloc[-1])
    d = d[d.timestamp + 86400 <= tcut].reset_index(drop=True)
    ntr = len(d) // 2
    cat = ["campaign"] + [f"cat{i}" for i in range(1, 10)]
    maps = {c: d[c].iloc[:ntr].value_counts() for c in cat}

    def feats(df):
        xc = np.zeros((len(df), len(cat)))
        for j, c in enumerate(cat):
            xc[:, j] = np.log1p(df[c].map(maps[c]).fillna(0).to_numpy())
        tslc = df.time_since_last_click
        return np.c_[xc, tslc.where(tslc >= 0).to_numpy(), (tslc < 0).astype(int).to_numpy()]

    x, y = feats(d), d["click"].to_numpy()
    xtr, ytr, xd, yd = x[:ntr], y[:ntr], x[ntr:], y[ntr:]
    # replay the audit's module-level rng: LR_old, LR_new, 2 x 5 shuffles, then HGB_new
    rng = np.random.default_rng(0)
    h = ntr // 2
    maxfit = 150000

    def sub(lo, hi):
        idx = np.arange(ntr)[lo:hi]
        return np.sort(rng.choice(idx, maxfit, replace=False)) if len(idx) > maxfit else idx

    i_old = sub(0, h)
    sub(h, ntr)
    for _ in range(10):
        rng.permutation(len(yd))
    i_new = sub(h, ntr)
    m0 = mk_lr_pipe().fit(xtr[i_old], ytr[i_old])
    m1 = mk_hgb_pipe().fit(xtr[i_new], ytr[i_new])
    l0 = (m0.predict(xd) != yd).astype(np.int8)
    l1 = (m1.predict(xd) != yd).astype(np.int8)
    eps = []
    if not want:
        for s in episode_plan(0, len(yd), dev_eps):
            eps.append((s + ntr, l0[s : s + T_EP], l1[s : s + T_EP]))
    else:
        for s in ep_starts:
            de = pd.concat(locked[s]).reset_index(drop=True)
            if len(de) != T_EP:
                raise RuntimeError(f"criteo episode at {s} has {len(de)} rows")
            xe, ye = feats(de), de["click"].to_numpy()
            eps.append(
                (s, (m0.predict(xe) != ye).astype(np.int8), (m1.predict(xe) != ye).astype(np.int8))
            )
    return l0, l1, eps


def locked_plan(stream: str) -> list[int]:
    n = STREAMS[stream]["n"]
    start = STREAMS[stream].get("locked_start", int(0.6 * n))
    return episode_plan(start, n - start)


def build(stream: str, locked: bool, dev_eps: int = 2):
    starts = locked_plan(stream) if locked else None
    if stream in FETCHED:
        return build_fetched(stream, starts, dev_eps)
    if stream == "elec2":
        return build_elec2(starts, dev_eps)
    return build_criteo(starts, dev_eps)


# ----------------------------------------------------------------------------- phases
def append_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(b1.jsonable(r)) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return list({(r["episode"], r["setting"]): r for r in rows}.values())  # last row wins


def update_check(out: Path, stream: str, phase: str, rec: dict) -> None:
    path = out / "pairs_check.json"
    cur = json.loads(path.read_text()) if path.exists() else {}
    cur.setdefault(stream, {})[phase] = rec
    path.write_text(json.dumps(b1.jsonable(cur), indent=2), encoding="utf-8")


def process_stream(stream: str, phase: str, out: Path, n_seeds: int, dev_eps: int) -> dict:
    """Train pair, check dev stats, run all episodes (resumable)."""
    t0 = time.time()
    locked = phase == "run"
    jsonl = out / f"{stream}.jsonl"
    delay = STREAMS[stream]["delay"]
    n_all = STREAMS[stream]["n"]
    dev_len = int(0.6 * n_all) - int(0.3 * n_all)
    n_ep = len(locked_plan(stream)) if locked else min(dev_eps, dev_len // T_EP)
    done = {(r["episode"], r["setting"]) for r in read_jsonl(jsonl)}
    full = {i for i in range(n_ep) if all((i, k) in done for k in SETTINGS)}
    if len(full) == n_ep:
        return {"stream": stream, "skipped": "complete", "seconds": 0.0}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        l0d, l1d, eps = build(stream, locked, dev_eps)
    chk = dev_check(stream, l0d, l1d)
    chk["episode_start_rows"] = [int(e[0]) for e in eps]
    update_check(out, stream, phase, chk)
    if not chk["match_1e-9"]:
        raise RuntimeError(f"{stream}: dev stats do not reproduce the audit: {chk['abs_diff']}")
    (out / "losses").mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out / "losses" / f"{stream}.npz",
        starts=np.array([e[0] for e in eps]),
        l0=np.stack([e[1] for e in eps]),
        l1=np.stack([e[2] for e in eps]),
    )
    base_err = audit_expected(stream)["inc_err"]
    for i, (start, l0, l1) in enumerate(eps):
        if i in full:
            continue
        u = episode_u(i, n_seeds)
        pols = {b: run_episode(l0, l1, u, b, delay, base_err) for b in (200, 400)}
        st = {
            "err_incumbent": float(l0.mean()),
            "err_challenger": float(l1.mean()),
            "disagree": float((l0 != l1).mean()),
        }
        append_jsonl(jsonl, episode_rows(stream, i, start, pols, delay, n_seeds, st))
        print(f"[{stream}] episode {i + 1}/{n_ep} {time.time() - t0:.0f}s", flush=True)
    return {"stream": stream, "seconds": time.time() - t0}


# ----------------------------------------------------------------------------- summary
def boot_diff(per_ep: np.ndarray, per_seed: np.ndarray, rng) -> dict:
    """CI for the mean of a paired difference: episodes if K >= 5, else seeds (LOW-POWER)."""
    low = len(per_ep) < 5
    arr = per_seed if low else per_ep
    idx = rng.integers(0, len(arr), size=(BOOT, len(arr)))
    m = arr[idx].mean(1)
    return {
        "mean": float(per_ep.mean()),
        "lo": float(np.percentile(m, 2.5)),
        "hi": float(np.percentile(m, 97.5)),
        "bootstrap_level": "seed" if low else "episode",
        "low_power": bool(low),
    }


def stream_summary(rows: list[dict], setting: str, rng) -> dict:
    rs = sorted((r for r in rows if r["setting"] == setting), key=lambda r: r["episode"])
    ep = {p: np.array([r["policies"][p]["mean_cost"] for r in rs]) for p in POLICIES}
    seeds = {p: np.mean([r["policies"][p]["cost_seeds"] for r in rs], axis=0) for p in POLICIES}
    mean = {p: float(ep[p].mean()) for p in POLICIES}

    def diff(a, b):
        return boot_diff(ep[a] - ep[b], seeds[a] - seeds[b], rng)

    def avg(field, pol):
        return float(np.mean([r["policies"][pol][field] for r in rs]))

    denom = mean["P0"] - min(mean["P0"], mean["P1"])
    spend = CQ * avg("mean_labels", "P3b")
    bound = mean["P0"] + spend + SAFE_MARGIN * mean["P0"]
    d_p0 = diff("P3b", "P0")
    return {
        "episodes": len(rs),
        "mean_cost": mean,
        "paired": {
            "P3b_minus_P0": d_p0,
            "P3b_minus_P2": diff("P3b", "P2"),
            "P3b_minus_P1": diff("P3b", "P1"),
            "P3b_minus_P6": diff("P3b", "P6"),
        },
        "headroom_capture": float((mean["P0"] - mean["P3b"]) / denom) if denom > 0 else None,
        "p3b_query_spend": spend,
        "safe_bound": bound,
        "WIN": bool(d_p0["hi"] < 0 and mean["P3b"] <= mean["P2"]),
        "SAFE": bool(mean["P3b"] <= bound),
        "diagnostics": {
            p: {
                "mean_labels": avg("mean_labels", p),
                "mean_switches": avg("mean_switches", p),
                "mean_rollbacks": avg("mean_rollbacks", p),
                "promotion_rate": avg("promotion_rate", p),
            }
            for p in POLICIES
        },
    }


def programme(streams: dict) -> dict:
    wins = [s for s, v in streams.items() if v["primary"].get("WIN")]
    safe_fail = [s for s, v in streams.items() if not v["primary"].get("SAFE")]
    if len(wins) >= 3 and not safe_fail:
        outcome = "SUCCESS"
    elif 1 <= len(wins) <= 2 or len(safe_fail) == 1:
        outcome = "PARTIAL"
    else:
        outcome = "FAIL"
    return {"outcome": outcome, "win_streams": wins, "safe_failures": safe_fail}


def summarise(out: Path, names: list[str], phase: str) -> dict:
    rng = np.random.default_rng(SEED_BASE + 7)
    streams = {}
    for s in names:
        rows = read_jsonl(out / f"{s}.jsonl")
        if not rows:
            streams[s] = {"primary": {"WIN": False, "SAFE": False}, "error": "no rows"}
            continue
        settings = {k: stream_summary(rows, k, rng) for k in SETTINGS}
        streams[s] = {
            "status": STREAMS[s]["status"],
            "delay": STREAMS[s]["delay"],
            "episodes": settings[PRIMARY]["episodes"],
            "low_power": settings[PRIMARY]["paired"]["P3b_minus_P0"]["low_power"],
            "primary": settings[PRIMARY],
            "sensitivity": {k: v for k, v in settings.items() if k != PRIMARY},
        }
    return {
        "protocol": str(PROTOCOL.relative_to(ROOT)).replace("\\", "/"),
        "protocol_sha256": PROTOCOL_SHA256,
        "phase": phase,
        "registered": phase == "run",
        "decision_rule": "WIN: CI(P3b-P0) hi<0 and mean P3b<=mean P2; SAFE: P3b<=P0+spend+2%P0",
        "failed_streams_count_as": "not WIN and not SAFE",
        "streams": streams,
        "programme": programme(streams),
        "created_utc": datetime.now(UTC).isoformat(),
    }


# ----------------------------------------------------------------------------- provenance
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 22), b""):
            h.update(blk)
    return h.hexdigest()


def data_files() -> dict:
    files = {
        "elec2": RAW / "elec2/electricity-normalized.arff",
        "criteo": RAW / "criteo_attribution/criteo_attribution_dataset.tsv.gz",
        "airlines": RAW / "openml_airlines_1169/dataset_1169.pq",
        "weather_data": RAW / "weather_elwell_polikar/NEweather_data.csv",
        "weather_class": RAW / "weather_elwell_polikar/NEweather_class.csv",
        "spam": RAW / "spam_katakis/spam.zip",
        "bank": RAW / "uci_bank_marketing/bank-marketing.zip",
        "rialto_data": RAW / "rialto/rialto.data",
        "rialto_labels": RAW / "rialto/rialto.labels",
    }
    rec = {}
    for k, p in files.items():
        got = sha256_file(p)
        receipt = Path(str(p) + ".receipt.json")
        exp = json.loads(receipt.read_text())["sha256"] if receipt.exists() else None
        rec[k] = {
            "path": str(p),
            "bytes": p.stat().st_size,
            "sha256": got,
            "receipt_sha256": exp,
            "receipt_match": None if exp is None else bool(exp == got),
        }
    return rec


def write_provenance(out: Path, pid: int) -> None:
    rel = str(B1_PATH.relative_to(ROOT)).replace("\\", "/")
    prov = {
        "protocol_sha256": PROTOCOL_SHA256,
        "protocol_sha256_verified": sha256_file(PROTOCOL) == PROTOCOL_SHA256,
        "repo_head": git("rev-parse", "HEAD").stdout.strip(),
        "b1_policy_code": B1_RECORD,
        "b1_worktree_identical_to_041bc26": git("diff", "--quiet", B1_COMMIT, "--", rel).returncode
        == 0,
        "b3_script_sha256": sha256_file(Path(__file__)),
        "params": {**b1.Params(T=T_EP).__dict__, "seeds": N_SEEDS, "seed_base": SEED_BASE},
        "settings": {k: {"budget": b, "cs": c} for k, (b, c) in SETTINGS.items()},
        "streams": STREAMS,
        "libraries": {
            "python": sys.version,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "sklearn": sklearn.__version__,
        },
        "data_files": data_files(),
        "pid": pid,
        "started_utc": datetime.now(UTC).isoformat(),
    }
    (out / "provenance.json").write_text(json.dumps(b1.jsonable(prov), indent=2), encoding="utf-8")


def write_sha256sums(out: Path) -> None:
    items = sorted(
        p
        for p in out.rglob("*")
        if p.is_file() and p.suffix in {".json", ".jsonl", ".npz"} and "smoke" not in p.parts
    )
    extra = [Path(__file__), ROOT / "tests/promising_directions/test_b3_real_data.py"]
    lines = [f"{sha256_file(p)} *{p.relative_to(out).as_posix()}" for p in items]
    lines += [f"{sha256_file(p)} *{p.relative_to(ROOT).as_posix()}" for p in extra if p.exists()]
    (out / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------- main
def main() -> None:
    import os

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phase", choices=["smoke", "run", "summary"], required=True)
    ap.add_argument("--streams", nargs="*", default=list(STREAMS))
    ap.add_argument("--seeds", type=int, default=None)
    ap.add_argument("--dev-episodes", type=int, default=2)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    a = ap.parse_args()
    if sha256_file(PROTOCOL) != PROTOCOL_SHA256:
        raise SystemExit("protocol file does not match the registered sha256")
    out = a.out_dir / "smoke" if a.phase == "smoke" else a.out_dir
    out.mkdir(parents=True, exist_ok=True)
    n_seeds = a.seeds or (5 if a.phase == "smoke" else N_SEEDS)
    if a.phase == "run":
        write_provenance(out, os.getpid())
    if a.phase in ("smoke", "run"):
        status = {}
        for s in a.streams:
            try:
                status[s] = process_stream(s, a.phase, out, n_seeds, a.dev_episodes)
            except Exception as e:  # noqa: BLE001 - a failed stream is recorded and not re-tuned
                status[s] = {"stream": s, "error": repr(e)}
                (out / f"{s}.error.json").write_text(json.dumps(status[s]), encoding="utf-8")
                print(f"[{s}] FAILED: {e!r}", flush=True)
        (out / "run_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    name = "summary_smoke.json" if a.phase == "smoke" else "summary.json"
    summ = summarise(out, a.streams, a.phase)
    (out / name).write_text(json.dumps(b1.jsonable(summ), indent=2), encoding="utf-8")
    if a.phase == "run":
        write_sha256sums(out)
    print(json.dumps(summ["programme"]), flush=True)


if __name__ == "__main__":
    main()
