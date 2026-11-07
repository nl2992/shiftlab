"""WP2 (sprint 2): reproduce the registered twin-null streams and build independent v2 splits.

* ``reproduce``: runs the FROZEN ``twin_null.build`` with its output directory redirected to a scratch
  folder, and also this module's split-parameterised copy (``build_splits``) on splits 0..19; both must
  match ``array_content_sha256`` in data/sprint_twin_losses/stats.json. data/sprint_twin_losses/ is
  never written.
* ``v2``: the same construction on NEW split indices 20..39 (the registered seed function
  ``twin_null._seed(name, s, k)`` with s >= 20 was never evaluated before), written to
  data/sprint_twin_losses_v2/twin2_<dataset>.npz (derived data only).

    uv run python scripts/sota_sprint/wp2_twins.py reproduce --scratch <dir>
    uv run python scripts/sota_sprint/wp2_twins.py v2
    uv run python scripts/sota_sprint/wp2_twins.py variants   # T=1000/4000 re-windowings of v2
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import twin_null
from fam_a import rho_mle
from fresh_real import CATEGORICAL, DELAYS, LOADERS, MAX_EPS, T_EP, prep

ROOT = HERE.parents[1]
REG = ROOT / "data/sprint_twin_losses"
V2 = ROOT / "data/sprint_twin_losses_v2"
V2_SPLITS = range(20, 40)


def content_hash(l0: np.ndarray, l1: np.ndarray) -> str:
    return hashlib.sha256(l0.tobytes() + l1.tobytes()).hexdigest()


def build_splits(name: str, splits) -> dict:
    """twin_null.build with an explicit split range; returns arrays and statistics (no file I/O)."""
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
    for s in splits:
        half = twin_null._seed(name, s, 0).random(n30) < 0.5
        preds = []
        for m in (half, ~half):
            clf = HistGradientBoostingClassifier(
                max_iter=100, max_depth=4, learning_rate=0.1, random_state=0
            ).fit(xtr[m], y[:n30][m])
            preds.append((clf.predict(xe) != y[n30:end]).astype(np.int8).reshape(k, T_EP))
        if twin_null._seed(name, s, 1).random() < 0.5:
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
    adv = np.array(adv)
    per_split = adv.reshape(len(list(splits)), k).mean(axis=1)
    stats = {
        "dataset": name,
        "splits": [int(s) for s in splits],
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
        "array_content_sha256": content_hash(l0, l1),
    }
    return {"l0": l0, "l1": l1, "split": np.array(split), "ep": np.array(ep), "stats": stats}


def reproduce(scratch: Path) -> dict:
    reg = json.loads((REG / "stats.json").read_text())
    scratch.mkdir(parents=True, exist_ok=True)
    twin_null.OUT = scratch  # redirect the frozen builder; the registered folder is never written
    out = {}
    for nm in LOADERS:
        frozen = twin_null.build(nm)["array_content_sha256"]
        copy = build_splits(nm, range(20))["stats"]["array_content_sha256"]
        z = np.load(REG / f"twin_{nm}.npz")
        on_disk = content_hash(z["l0"], z["l1"])
        out[nm] = {
            "registered": reg[nm]["array_content_sha256"],
            "frozen_rebuild": frozen,
            "wp2_copy_rebuild": copy,
            "registered_file": on_disk,
            "match": frozen == copy == on_disk == reg[nm]["array_content_sha256"],
        }
        print(nm, out[nm]["match"])
    return out


def build_v2() -> dict:
    V2.mkdir(parents=True, exist_ok=True)
    stats = {}
    for nm in LOADERS:
        b = build_splits(nm, V2_SPLITS)
        np.savez(V2 / f"twin2_{nm}.npz", l0=b["l0"], l1=b["l1"], split=b["split"], ep=b["ep"])
        stats[nm] = b["stats"]
        print(
            nm,
            {
                k: (round(v, 4) if isinstance(v, float) else v)
                for k, v in b["stats"].items()
                if k not in ("splits", "array_content_sha256")
            },
        )
    (V2 / "stats.json").write_text(json.dumps(stats, indent=1) + "\n")
    return stats


def rewindow(z, T: int) -> dict:
    """Re-window a split-major (S*K, 2000) twin file to episode length T in {1000, 4000}, within split."""
    l0, l1, split = z["l0"], z["l1"], z["split"]
    L0, L1, S, E = [], [], [], []
    for s in np.unique(split):
        a0, a1 = l0[split == s].reshape(-1), l1[split == s].reshape(-1)
        k = len(a0) // T
        L0.append(a0[: k * T].reshape(k, T))
        L1.append(a1[: k * T].reshape(k, T))
        S += [int(s)] * k
        E += list(range(k))
    return {
        "l0": np.concatenate(L0),
        "l1": np.concatenate(L1),
        "split": np.array(S),
        "ep": np.array(E),
    }


def build_variants() -> dict:
    out = {}
    for nm in LOADERS:
        z = np.load(V2 / f"twin2_{nm}.npz")
        for T in (1000, 4000):
            v = rewindow(z, T)
            np.savez(V2 / f"twin2_{nm}_T{T}.npz", **v)
            out[f"{nm}_T{T}"] = {
                "episodes": int(v["l0"].shape[0]),
                "array_content_sha256": content_hash(v["l0"], v["l1"]),
            }
    (V2 / "variants.json").write_text(json.dumps(out, indent=1) + "\n")
    print(out)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=("reproduce", "v2", "variants"))
    ap.add_argument("--scratch", default=str(ROOT / "outputs/sprint2/WP2/repro_scratch"))
    ap.add_argument("--out", default=str(ROOT / "docs/sprint2/wp2/reproduction.json"))
    a = ap.parse_args(argv)
    if a.cmd == "reproduce":
        res = reproduce(Path(a.scratch))
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=1) + "\n")
    elif a.cmd == "v2":
        build_v2()
    else:
        build_variants()


if __name__ == "__main__":
    main()
