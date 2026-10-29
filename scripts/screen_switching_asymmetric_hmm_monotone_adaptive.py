"""Exploratory asymmetric-HMM screen for adaptive monotone-promotion restriction.

This compares exact rational evaluations of numerically recovered policies; it does
not certify either LP optimum. It is a small-cell structural screen, not efficacy.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import product
from pathlib import Path

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


def main() -> None:
    transition_values = (F(1, 10), F(1, 4), F(1, 2))
    transition_pairs = tuple((a, b) for a, b in product(transition_values, repeat=2) if a != b)
    emission_priors = (
        (F(1, 10), F(9, 10), F(1, 2)),
        (F(1, 4), F(3, 4), F(1, 4)),
        (F(1, 4), F(3, 4), F(3, 4)),
        (F(1, 10), F(3, 4), F(1, 3)),
    )
    configs = ((3, 2, 1), (4, 2, 1), (4, 3, 2), (5, 3, 1))
    rows = []
    for horizon, budget, delay in configs:
        for transition01, transition10 in transition_pairs:
            for emission0, emission1, prior1 in emission_priors:
                for alpha in (F(1, 20), F(1, 10), F(1, 5)):
                    for query_cost, switch_cost in ((F(0), F(0)), (F(1, 100), F(1, 10))):
                        config = GameConfig(
                            horizon=horizon,
                            budget=budget,
                            delay=delay,
                            alpha=alpha,
                            query_cost=query_cost,
                            switch_cost=switch_cost,
                            max_nodes=200_000,
                        )
                        model = RegimeModel(
                            transition01=transition01,
                            transition10=transition10,
                            emission0=emission0,
                            emission1=emission1,
                            prior1=prior1,
                        )
                        unrestricted, _, _ = CausalSwitchingGame(config, model).solve(
                            monotone_promotion=False
                        )
                        monotone, _, _ = CausalSwitchingGame(config, model).solve(
                            monotone_promotion=True
                        )
                        cost_u = F(unrestricted["calibrated_total_cost"])
                        cost_m = F(monotone["calibrated_total_cost"])
                        rows.append(
                            {
                                "horizon": horizon,
                                "budget": budget,
                                "delay": delay,
                                "transition01": str(transition01),
                                "transition10": str(transition10),
                                "emission0": str(emission0),
                                "emission1": str(emission1),
                                "prior1": str(prior1),
                                "alpha": str(alpha),
                                "query_cost": str(query_cost),
                                "switch_cost": str(switch_cost),
                                "unrestricted_recovered_cost": str(cost_u),
                                "monotone_recovered_cost": str(cost_m),
                                "recovered_cost_gap": str(cost_m - cost_u),
                                "unrestricted_solver_objective": unrestricted["solver_objective"],
                                "monotone_solver_objective": monotone["solver_objective"],
                                "unrestricted_risk": unrestricted["raw_causal_null_risk"],
                                "monotone_risk": monotone["raw_causal_null_risk"],
                            }
                        )
    gaps = [F(row["recovered_cost_gap"]) for row in rows]
    sources = (
        "src/shiftlab/dive/causal_switching_game.py",
        "src/shiftlab/dive/delayed_regime_information.py",
        "scripts/screen_switching_asymmetric_hmm_monotone_adaptive.py",
    )
    output = {
        "status": "exploratory_recovered_policy_screen_not_optimum_certificate",
        "cells": len(rows),
        "asymmetric_transition_pairs": [list(map(str, pair)) for pair in transition_pairs],
        "summary": {
            "positive_recovered_cost_gaps": sum(gap > 0 for gap in gaps),
            "negative_recovered_cost_gaps": sum(gap < 0 for gap in gaps),
            "zero_recovered_cost_gaps": sum(gap == 0 for gap in gaps),
            "maximum_recovered_cost_gap": str(max(gaps)),
            "minimum_recovered_cost_gap": str(min(gaps)),
        },
        "interpretation": (
            "The sequence-form LPs are solved numerically and policies rationalized on recovery. "
            "Equal recovered costs do not certify equal optima or prove monotone optimality. "
            "This screen is not empirical efficacy evidence or a novelty result."
        ),
        "source_sha256": {
            path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in sources
        },
        "rows": rows,
    }
    target = Path("outputs/switching_asymmetric_hmm_monotone_adaptive_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "results.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {key: output[key] for key in ("status", "cells", "summary", "interpretation")}, indent=2
        )
    )


if __name__ == "__main__":
    main()
