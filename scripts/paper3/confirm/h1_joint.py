"""H1 confirmation: tuned A0 (and A1,A3,A5) vs tuned wald_cut, 24 regimes, T=300,
seeds_for('confirmation', 100, 0). Checkpoint per regime. usage: h1_joint.py [--workers 16] [--analyze-only]"""

import argparse
import json
import os
import sys
import time

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "joint"))
import numpy as np
from _common import OUT as COUT
from _common import ledger

from shiftlab.paper3.joint import harness as H
from shiftlab.paper3.simulation import seeds_for

OUT = COUT / "h1"
KEEP = ["wald_cut", "A0", "A1", "A3", "A5"]
TUNE = os.path.join(HERE, "..", "..", "..", "outputs", "paper3", "joint", "tuning")


def specs():
    names, sp = ["never"], [{"kind": "never", "params": {}, "name": "never"}]
    for m in KEEP:
        s = json.load(open(os.path.join(TUNE, f"{m}.json")))["best_spec"]  # noqa: SIM115
        names.append(m)
        sp.append({**s, "name": m})
    return names, sp


def boot(D, nb=10000, seed=12345):
    """D: (n_regime, n_seed) paired differences. pooled per seed = equal-weight mean over regimes."""
    pooled = D.mean(0)
    rng = np.random.default_rng(seed)
    ns = len(pooled)
    idx = rng.integers(0, ns, (nb, ns))
    bs = pooled[idx].mean(1)
    return float(pooled.mean()), float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975))


def analyze(names, rids, sl):
    rows = []
    for rid in rids:
        rows += json.loads((OUT / f"{rid}.json").read_text())["rows"]
    J = H.to_array(rows, len(names), rids, sl, "J")
    NQ = H.to_array(rows, len(names), rids, sl, "n_queries")
    NS = H.to_array(rows, len(names), rids, sl, "n_switches")
    assert not np.isnan(J).any()
    ref = names.index("wald_cut")
    jref = float(J[ref].mean())
    res = {
        "n_seeds": len(sl),
        "n_regimes": len(rids),
        "n_runs": int(J.size),
        "pooled_J": {m: float(J[i].mean()) for i, m in enumerate(names)},
        "labels": {m: float(NQ[i].mean()) for i, m in enumerate(names)},
        "switches": {m: float(NS[i].mean()) for i, m in enumerate(names)},
        "J_wald_cut": jref,
        "threshold_1pct": -0.01 * jref,
        "contrasts": {},
    }
    for m in ["A0", "A1", "A3", "A5"]:
        d, lo, hi = boot(J[names.index(m)] - J[ref])
        res["contrasts"][m] = {
            "dJ": d,
            "lo": lo,
            "hi": hi,
            "rel_pct": 100 * d / jref,
            "lo_rel_pct": 100 * lo / jref,
            "hi_rel_pct": 100 * hi / jref,
            "supported_rule": bool(lo > -0.01 * jref),
        }
    # per regime A0 - wald_cut
    res["A0_per_regime"] = {
        rid: float((J[names.index("A0")][i] - J[ref][i]).mean()) for i, rid in enumerate(rids)
    }
    res["H1_SUPPORTED"] = res["contrasts"]["A0"]["supported_rule"]
    (OUT / "summary.json").write_text(json.dumps(res, indent=1))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--analyze-only", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    rids = H.regime_ids()
    sl = seeds_for("confirmation", 100, 0)
    names, sp = specs()
    t0 = time.time()
    if not a.analyze_only:
        cfg = {
            "methods": names,
            "seeds": [sl[0], sl[-1]],
            "n_seeds": len(sl),
            "T": H.T_DEFAULT,
            "regimes": len(rids),
        }
        (OUT / "config.json").write_text(json.dumps(cfg))
        for rid in rids:
            f = OUT / f"{rid}.json"
            if f.exists():
                continue
            rows = H.run_batch(sp, [rid], sl, H.T_DEFAULT, a.workers)
            tmp = OUT / f"{rid}.json.tmp"
            H.dump(tmp, {"names": names, "rows": rows})
            os.replace(tmp, f)
            print(f"{rid} done ({time.time() - t0:.0f}s)", flush=True)
    res = analyze(names, rids, sl)
    ledger(
        "H1",
        "confirm_run",
        {"methods": names, "seeds": [sl[0], sl[-1]], "T": H.T_DEFAULT},
        res,
        time.time() - t0,
        "wall includes only this invocation (resume skips finished regimes)",
    )
    print(json.dumps(res["contrasts"], indent=1), res["H1_SUPPORTED"])


if __name__ == "__main__":
    main()
