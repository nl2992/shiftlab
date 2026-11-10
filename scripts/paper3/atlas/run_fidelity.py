"""DISCERN psi_E fidelity audit: rerun a small Failure Atlas v2 reproduction with IDENTICAL seeds before
(legacy psi_E, missing /4) and after the fix, using the unmodified v2 harness (scripts/failure_atlas_v2).
Pre-fix numbers are archived for comparison only and are NOT calibrated comparators.
"""

import inspect
import json
import sys
import textwrap
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
V2 = ROOT / "scripts/failure_atlas_v2"
sys.path.insert(0, str(V2))

REGS = [
    "V_late_1000_p72",
    "V_better_p62",
    "V_better_p70",
    "V_null",
    "V_dep_null_r8",
    "V_late_1000_d50",
]
POLS = ["gated_deployment", "discern_style", "discern_style+RMM", "gated_deployment+RMM"]
SEEDS = list(range(5000, 5020))  # v2 validation seeds, seed_base 20261104 (identical pre/post)
CFG = {"budget": 200, "cq": 0.05, "cs": 5.0, "alpha": 0.05, "seed_base": 20261104}


def job(a):
    variant, reg = a
    import certificate_stops as cs_mod
    import run_atlas_v2 as R

    if variant == "pre":
        src = textwrap.dedent(inspect.getsource(cs_mod.PrPlEBCS.update))
        assert "/ 4.0" in src
        ns = dict(vars(cs_mod))
        exec(src.replace("(-math.log1p(-lam) - lam) / 4.0", "(-math.log1p(-lam) - lam)"), ns)  # noqa: S102 (reproduces pre-fix legacy code)
        cs_mod.PrPlEBCS.update = ns["update"]
    return variant, reg, R._job(("syn", reg, 0, SEEDS, CFG, POLS, "v2_candidates"))


if __name__ == "__main__":
    out = ROOT / "outputs/paper3/atlas/fidelity"
    out.mkdir(parents=True, exist_ok=True)
    t = time.time()
    jobs = [(v, r) for v in ("pre", "post") for r in REGS]
    with ProcessPoolExecutor(12) as ex:
        res = list(ex.map(job, jobs))
    rows = [dict(variant=v, regime=r, **row) for v, r, rr in res for row in rr]
    (out / "records.json").write_text(json.dumps(rows))
    print("done", len(rows), time.time() - t)
