"""SAES development streams with unlabeled signals (EXPOSED data only; counts for nothing).

For each exposed raw source (B3 loaders), one recipe: incumbent = logistic regression on the
first 15% (train-old), challenger = gradient boosting on the next 15% (train-new); preprocessing
is fitted on train rows only. The post-training stream is cut into 2,000-event episodes.

Per event it stores what a deployed system observes **before** any label:
  s0, s1  : P(y=1) of incumbent and challenger
  drift   : mean squared train-standardised feature value (train-only scaler), a cheap
            per-event feature-drift statistic
and, evaluator-side only (never shown to a policy except through paid, delayed feedback):
  l0, l1  : 0/1 losses.

Output: data/saes_dev/<name>.npz (gitignored). Usage: python saes_dev_build.py [names...]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import sparse
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/promising_directions"))
import b3_real_data as b3

OUT = ROOT / "data/saes_dev"
T_EP = 2000
CAP = {"airlines": 200_000}
DELAY = {"airlines": 100, "weather": 1, "spam": 50, "bank": 100, "rialto": 100, "elec2": 48}


def load(name):
    if name == "elec2":
        import io

        lines = (
            (b3.RAW / "elec2/electricity-normalized.arff").read_text(encoding="utf8").splitlines()
        )
        k = next(i for i, ln in enumerate(lines) if ln.strip().lower() == "@data") + 1
        import pandas as pd

        df = pd.read_csv(
            io.StringIO("\n".join(ln for ln in lines[k:] if ln.strip())),
            header=None,
            names=[*b3.ELEC_COLS, "cls"],
        )
        y = (df.pop("cls").str.strip() == "UP").astype(int).to_numpy()
        return df[b3.ELEC_COLS[2:]].astype(float), y
    n = CAP.get(name, b3.STREAMS[name]["n"])
    x, y = b3.load_fetched(name, n)
    y = np.asarray(y)
    cls = np.unique(y[: int(0.3 * len(y))])
    if len(cls) > 2:
        vals, cnt = np.unique(y[: int(0.3 * len(y))], return_counts=True)
        y = (y == vals[np.argmax(cnt)]).astype(int)
    else:
        y = (y == cls.max()).astype(int)
    return x, y


def build(name):
    x, y = load(name)
    n = len(y)
    a, b = int(0.15 * n), int(0.3 * n)
    sl = (lambda i, j: x[i:j]) if sparse.issparse(x) else (lambda i, j: x.iloc[i:j])
    f = b3.prep(sl(0, b))  # train-only preprocessing (both training windows)
    dense = (lambda m: m.toarray()) if sparse.issparse(x) else (lambda m: m)
    Xtr0, Xtr1 = dense(f(sl(0, a))), dense(f(sl(a, b)))
    m0 = LogisticRegression(max_iter=500, C=1.0).fit(Xtr0, y[:a])
    m1 = HistGradientBoostingClassifier(max_iter=100, max_depth=4, random_state=0).fit(Xtr1, y[a:b])
    mu = np.vstack([Xtr0, Xtr1]).mean(0)
    sd = np.vstack([Xtr0, Xtr1]).std(0) + 1e-6
    k = (n - b) // T_EP
    Xs = dense(f(sl(b, b + k * T_EP)))
    ys = y[b : b + k * T_EP]
    s0, s1 = m0.predict_proba(Xs)[:, 1], m1.predict_proba(Xs)[:, 1]
    drift = (((Xs - mu) / sd) ** 2).mean(1)
    l0 = ((s0 >= 0.5).astype(int) != ys).astype(np.int8)
    l1 = ((s1 >= 0.5).astype(int) != ys).astype(np.int8)
    rs = lambda v, dt: v.reshape(k, T_EP).astype(dt)
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez(
        OUT / f"{name}.npz",
        l0=rs(l0, np.int8),
        l1=rs(l1, np.int8),
        s0=rs(s0, np.float32),
        s1=rs(s1, np.float32),
        drift=rs(drift, np.float32),
        starts=(b + np.arange(k) * T_EP).astype(np.int64),
        delay=np.int64(DELAY[name]),
    )
    print(
        f"{name}: n={n} episodes={k} err0={l0.mean():.3f} err1={l1.mean():.3f} "
        f"dis={(l0 != l1).mean():.3f}",
        flush=True,
    )


# --- sprint streams: exact fresh_real.py recipe, plus scores and drift --------------------------
def build_sprint(name):
    import hashlib

    sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))
    import fresh_real as fr

    x, yraw, _ts = fr.LOADERS[name]()
    cat = fr.CATEGORICAL.get(name, [])
    for c in cat:
        x[c] = x[c].astype(str)
    n = len(x)
    n15, n30 = int(0.15 * n), int(0.30 * n)
    thr = float(np.median(yraw.to_numpy()[:n30]))
    y = (yraw.to_numpy() > thr).astype(int)
    f = fr.prep(x.iloc[:n30], cat)
    m0 = LogisticRegression(max_iter=300, C=1.0).fit(f(x.iloc[:n15]), y[:n15])
    m1 = HistGradientBoostingClassifier(
        max_iter=100, max_depth=4, learning_rate=0.1, random_state=0
    ).fit(f(x.iloc[:n30]), y[:n30])
    k = min(fr.MAX_EPS, (n - n30) // T_EP)
    starts = np.array([n30 + i * T_EP for i in range(k)], dtype=np.int64)
    end = n30 + k * T_EP
    xe = f(x.iloc[n30:end])
    l0 = (m0.predict(xe) != y[n30:end]).astype(np.int8).reshape(k, T_EP)
    l1 = (m1.predict(xe) != y[n30:end]).astype(np.int8).reshape(k, T_EP)
    content = hashlib.sha256(l0.tobytes() + l1.tobytes() + starts.tobytes()).hexdigest()
    xtr = f(x.iloc[:n30])
    mu, sd = xtr.mean(0), xtr.std(0) + 1e-6
    s0 = m0.predict_proba(xe)[:, 1].reshape(k, T_EP).astype(np.float32)
    s1 = m1.predict_proba(xe)[:, 1].reshape(k, T_EP).astype(np.float32)
    drift = (((xe - mu) / sd) ** 2).mean(1).reshape(k, T_EP).astype(np.float32)
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez(
        OUT / f"{name}.npz",
        l0=l0,
        l1=l1,
        s0=s0,
        s1=s1,
        drift=drift,
        starts=starts,
        delay=np.int64(fr.DELAYS[name]),
    )
    print(
        f"{name}: episodes={k} array_content_sha256={content} raw={fr.sha256(fr.raw_zip(name))}",
        flush=True,
    )


SPRINT = ("metro", "beijing_pm25", "bike_hour", "appliances", "household_power")

if __name__ == "__main__":
    for nm in sys.argv[1:] or list(DELAY):
        build_sprint(nm) if nm in SPRINT else build(nm)
