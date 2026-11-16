"""Numerical checks of 03F Propositions 3 and 4 (dev seeds, offsets 50000+; exploratory).

Prop 4: full-sampling shield over AlwaysChallenger, label budget not binding (B = T), stationary
challenger advantage p; fraction of runs with >= 1 forced rollback vs the bound
((1-p)/p)^(floor(m)+1), m = R - 2k - d, and vs exp(-2 mu m), mu = 2p - 1.
Prop 3: all-harm tape with delay d; the shield's first deployment spell lasts exactly
floor(R - 2k) rounds, so it permits every feedback-blind hold the lower bound allows.
"""

import dataclasses
import json
import math

import numpy as np

from shiftlab.paper3.baselines import AlwaysChallenger
from shiftlab.paper3.riskbudget.harness import ROOT
from shiftlab.paper3.riskbudget.shield import RiskBudgetShield
from shiftlab.paper3.simulation import (
    Tape,
    generate_tape,
    load_regimes,
    make_spec,
    run_policy,
    seeds_for,
)

T, N = 300, 2000
out = {"prop4": [], "prop3": []}
base = load_regimes()["stationary_better"]
for p in (0.6, 0.7, 0.8):
    for d in (1, 5):
        prm = {**base.params, "path": {"type": "steps", "knots": [[0, p]]}}
        prm["delay"] = {"kind": "fixed", "d": d}
        reg = dataclasses.replace(base, params=prm, B=T)
        spec = make_spec(reg, T)
        k = spec.costs.k
        tapes = [generate_tape(reg, s, T)[0] for s in seeds_for("dev", N, 50000)]
        for R in (10, 12, 15, 20):
            m = R - 2 * k - d
            fr = 0
            for i, tp in enumerate(tapes):
                sh = RiskBudgetShield(AlwaysChallenger(), R, delta=0.0, ride_out=False)
                run_policy(sh, tp, spec, 50000 + i)
                fr += sh.n_forced_rollbacks > 0
            q = (1 - p) / p
            row = {
                "p": p,
                "d": d,
                "R": R,
                "m": m,
                "forced_frac": fr / N,
                "bound_ruin": q ** (math.floor(m) + 1) if m >= 0 else 1.0,
                "bound_hoeffding": math.exp(-2 * (2 * p - 1) * m) if m >= 0 else 1.0,
            }
            row["ok"] = row["forced_frac"] <= row["bound_ruin"] + 3 * math.sqrt(
                max(row["bound_ruin"] * (1 - row["bound_ruin"]), 1e-4) / N
            )
            out["prop4"].append(row)
            print(row, flush=True)

# Prop 3: every round a disagreement with Z = -1 (harm 1 per deployed round), fixed delay d
for d in (1, 3, 5, 10):
    for R in (8, 12, 20):
        ell = np.column_stack([np.zeros(60), np.ones(60)])
        tp = Tape(ell, np.ones(60, bool), np.zeros((60, 2)), np.full(60, d))
        spec = dataclasses.replace(make_spec(base, 60), B=60, delay_known=d)
        k = spec.costs.k
        sh = RiskBudgetShield(AlwaysChallenger(), R, delta=0.0, ride_out=False)
        rec = run_policy(sh, tp, spec, 0)
        spell = int(np.argmin(rec.a)) if rec.a[0] == 1 else 0  # length of first deployment spell
        # Prop 3: holding a first promotion for m feedback-blind rounds needs 2k + m <= R. On an
        # all-harm tape the shield holds exactly floor(R - 2k) rounds: every hold the lower bound
        # allows within the blind window (m <= d) is permitted, and the budget is never exceeded.
        cap = math.floor(R - 2 * k)
        row = {
            "d": d,
            "R": R,
            "first_spell": spell,
            "floor_R_minus_2k": cap,
            "blind_hold_allowed": min(d, cap),
            "attains": spell == cap,
        }
        out["prop3"].append(row)
        print(row, flush=True)
p = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme/results/riskbudget/props_check.json"
p.write_text(json.dumps(out, indent=1))
