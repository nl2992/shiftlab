"""Exchangeable-twin known-null real loss streams (docs/sota_sprint/p2_known_null_protocol.md).

For each fresh UCI dataset and split s, two identically specified HGB models are trained on disjoint
iid-coin halves of the chronological training window; a second coin picks the incumbent. Over the
construction's randomisation E[l0_t - l1_t] = 0 at every event, while the untouched evaluation stream
keeps its real serial dependence. Output: data/sprint_twin_losses/twin_<dataset>.npz with l0, l1
(S*K, 2000), split, ep.

    uv run python scripts/sota_sprint/twin_null.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fam_a import rho_mle
from fresh_real import CATEGORICAL, DELAYS, LOADERS, MAX_EPS, T_EP, prep

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/sprint_twin_losses"
SPLITS = 20


def _seed(name: str, s: int, k: int) -> np.random.Generator:
    h = int.from_bytes(hashlib.sha256(f"{name}|{s}|{k}".encode()).digest()[:4], "big")
    return np.random.default_rng([2026110620, h])


def build(name: str) -> dict:
    x, yraw, _ = LOADERS[name]()
    cat = CATEGORICAL.get(name, [])
    for c in cat:
        x[c] = x[c].astype(str)
    n = len(x)
    n30 = int(0.30 * n)
    thr = float(np.median(yraw.to_numpy()[:n30]))
    y = (yraw.to_numpy() > thr).astype(int)
    f = prep(x.iloc[:n30], cat)
    xtr = f(x.iloc[:n30])
    k = min(MAX_EPS, (n - n30) // T_EP)
    end = n30 + k * T_EP
    xe = f(x.iloc[n30:end])
    L0, L1, split, ep, adv, rhos = [], [], [], [], [], []
    for s in range(SPLITS):
        half = _seed(name, s, 0).random(n30) < 0.5
        preds = []
        for m in (half, ~half):
            clf = HistGradientBoostingClassifier(
                max_iter=100, max_depth=4, learning_rate=0.1, random_state=0
            ).fit(xtr[m], y[:n30][m])
            preds.append((clf.predict(xe) != y[n30:end]).astype(np.int8).reshape(k, T_EP))
        if _seed(name, s, 1).random() < 0.5:
            preds = preds[::-1]
        L0.append(preds[0])
        L1.append(preds[1])
        split += [s] * k
        ep += list(range(k))
        for e in range(k):
            d = preds[0][e].astype(int) - preds[1][e]
            adv.append(float(d.mean()))
            t = np.flatnonzero(d != 0)
            if len(t) >= 20:
                rhos.append(rho_mle((d[t] > 0).astype(int), t))
    l0, l1 = np.concatenate(L0), np.concatenate(L1)
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez(OUT / f"twin_{name}.npz", l0=l0, l1=l1, split=np.array(split), ep=np.array(ep))
    adv = np.array(adv)
    per_split = adv.reshape(SPLITS, k).mean(axis=1)
    return {
        "dataset": name,
        "splits": SPLITS,
        "K": int(k),
        "episodes": int(l0.shape[0]),
        "delay": DELAYS[name],
        "err0": float(l0.mean()),
        "err1": float(l1.mean()),
        "disagreement": float((l0 != l1).mean()),
        "mean_adv_over_splits": float(per_split.mean()),
        "sd_adv_over_splits": float(per_split.std(ddof=1)),
        "abs_adv_episode_median": float(np.median(np.abs(adv))),
        "median_rho_hat": float(np.median(rhos)) if rhos else None,
        "n_rho": len(rhos),
        "array_content_sha256": hashlib.sha256(l0.tobytes() + l1.tobytes()).hexdigest(),
    }


def main() -> None:
    stats = {nm: build(nm) for nm in LOADERS}
    (OUT / "stats.json").write_text(json.dumps(stats, indent=1) + "\n")
    for nm, v in stats.items():
        print(
            nm,
            {
                k: (round(x, 4) if isinstance(x, float) else x)
                for k, x in v.items()
                if k not in ("dataset", "array_content_sha256")
            },
        )


if __name__ == "__main__":
    main()
