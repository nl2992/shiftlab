"""Small paired synthetic diagnostic, not a SOTA performance benchmark.

Compare the repository's PPE transform with direct IPW bounded betting. Both
use the same Bernoulli queries, fixed stakes and risk threshold. The proxy is
fixed before outcomes; only queried labels enter learner updates. This first
slice uses immediate labels and an expected, not hard, query budget.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np

from shiftlab.dive.eprocess import BoundedMeanEProcess
from shiftlab.dive.prediction_powered_evalues import PredictionPoweredEProcess


def simulate(*, method: str, risk: float, seed: int, horizon: int = 512) -> dict:
    if method not in ("ppe", "ipw"):
        raise ValueError("unknown method")
    rng = np.random.default_rng(seed)
    # Generator/evaluator variables stay outside the monitor interface.
    outcomes = rng.binomial(1, risk, horizon)
    queries = rng.random(horizon) < 0.2
    threshold, propensity, stake = 0.2, 0.2, 0.08
    ppe = PredictionPoweredEProcess(lower=1 - stake, upper=1 + stake)
    ipw = BoundedMeanEProcess(bound=1 / propensity, stakes=(stake / propensity,))
    first_alarm = None
    for t in range(horizon):
        queried = bool(queries[t])
        observed = float(outcomes[t]) if queried else None
        if method == "ppe":
            ppe.update(
                proxy_factor=1.0,
                queried=queried,
                propensity=propensity,
                observed_factor=1 + stake * (observed - threshold) if queried else None,
            )
            alarm = ppe.wealth >= 20
        else:
            increment = (observed - threshold) / propensity if queried else 0.0
            ipw.update(increment)
            alarm = ipw.alarm
        if alarm and first_alarm is None:
            first_alarm = t + 1
    return {
        "primary_metric": {"alarm_by_horizon": first_alarm is not None},
        "secondary_metrics": {
            "first_alarm": first_alarm,
            "censored_delay": first_alarm or horizon,
            "horizon": horizon,
            "true_risk": risk,
            "comparison_note": "effective coefficients matched; constant-proxy factors coincide",
        },
        "labels_used": int(queries.sum()),
        "uncertainty_estimates": None,
        "validity_status": "diagnostic_only_iid_known_risk_null_expected_label_budget",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", required=True, choices=("ppe", "ipw"))
    parser.add_argument("--risk", required=True, type=float)
    parser.add_argument("--seed", required=True, type=int)
    args = parser.parse_args()
    result = simulate(method=args.method, risk=args.risk, seed=args.seed)
    with Path(os.environ["SOTA_RESULT_PATH"]).open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)


if __name__ == "__main__":
    main()
