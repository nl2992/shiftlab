"""WP2 smoke: always-continue vs uniform-query + naive switch on one dev family, paired, 20 seeds.

Smoke/integrity only; not evidence about any method. Usage:
  PYTHONPATH=src python scripts/d2a_rar/run_contract_smoke.py [family] [cost_vector]
"""

import sys
import time

from shiftlab.bench.contract import (
    AlwaysContinue,
    BudgetSpec,
    ClockSpec,
    EnvSpec,
    UniformQueryNaiveSwitch,
    load_cost_vectors,
    load_family,
    run_paired,
)

fam = sys.argv[1] if len(sys.argv) > 1 else "iid_shift_d10"
cv = sys.argv[2] if len(sys.argv) > 2 else "balanced"
t0 = time.time()
spec = load_family(fam)
env = EnvSpec(
    T=spec.T,
    costs=load_cost_vectors()[cv],
    budget=BudgetSpec(label_cap=50),
    clocks=ClockSpec(retrain_duration=20),
)
pr = run_paired(
    {"always_continue": AlwaysContinue, "uniform_query_naive_switch": UniformQueryNaiveSwitch},
    spec,
    env,
    seeds=range(110_900_000, 110_900_020),
)
for k in ("J", "loss", "cost_N_q", "cost_N_s"):
    m, lo, hi = pr.ci("uniform_query_naive_switch", "always_continue", k)
    print(f"{k:9s} naive - continue: {m:+.2f}  95% paired-bootstrap CI [{lo:+.2f}, {hi:+.2f}]")
print(
    f"mean J continue={pr.J('always_continue').mean():.2f} "
    f"naive={pr.J('uniform_query_naive_switch').mean():.2f}; family={fam} cost={cv}"
)
print(f"runtime {time.time() - t0:.2f}s (smoke only)")
