"""Prospectively frozen overlap cases for the repaired finite controller class."""

import hashlib
import json
import time
from datetime import UTC, datetime
from fractions import Fraction as F
from pathlib import Path

from scripts.exhaustive_evaluation.pilot_controller_synthesis import (
    StreakController,
    alternative_cost,
    exact_root_mixture,
)
from scripts.exhaustive_evaluation.test_controller_abandonment import EvaluationController, embed
from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.risk_preserving_approx.controller_risk_verifier import verify_causal_null_risk

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"


def main():
    path = DOC / "controller_transfer_registration.json"
    if path.exists():
        raise FileExistsError("retain registration; inspect live/terminal run before restart")
    prior = json.loads((DOC / "controller_abandonment_registration.json").read_text())
    classes = {"StreakController": StreakController, "EvaluationController": EvaluationController}
    configs = [
        classes[c["type"]](**{k: v for k, v in c.items() if k != "type"})
        for c in prior["controllers"]
    ]
    sources = [
        "scripts/exhaustive_evaluation/validate_controller_transfer.py",
        "scripts/exhaustive_evaluation/test_controller_abandonment.py",
        "scripts/exhaustive_evaluation/pilot_controller_synthesis.py",
        "src/shiftlab/dive/causal_switching_game.py",
        "src/shiftlab/dive/delayed_regime_information.py",
        "src/shiftlab/dive/risk_preserving_approx/controller_risk_verifier.py",
    ]
    reg = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "stage": "prospective new-cell known-model quality check; not real-data confirmation",
        "class": "same92 frozen prior controllers, thresholds unchanged",
        "class_registration_sha256": hashlib.sha256(
            (DOC / "controller_abandonment_registration.json").read_bytes()
        ).hexdigest(),
        "cells": [
            [6, 4, 1, "4/5"],
            [6, 3, 2, "4/5"],
            [6, 2, 3, "4/5"],
            [6, 4, 1, "3/5"],
            [6, 4, 1, "9/10"],
        ],
        "alpha": "1/20",
        "query_cost": "1/100",
        "switch_cost": "1/10",
        "node_cap": 200000,
        "primary": "class cost versus independently exact-verified feasible unrestricted reference; <=1percent relative quality tolerance; report all failures/caps",
        "limits": "numerical LP not exact lower bound, matching feasible policies does not prove optimum; no hardware speed claim",
        "sources_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
    }
    path.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    statuspath = DOC / "controller_transfer_status.json"
    status = {"status": "running", "completed": []}
    statuspath.write_text(json.dumps(status), encoding="utf-8")
    rows = []
    for cell in reg["cells"]:
        h, b, d, p = cell
        p = F(p)
        start = time.perf_counter()
        records = []
        for c in configs:
            risk = verify_causal_null_risk(c, horizon=h, budget=b, delay=d).risk
            cost, _ = alternative_cost(c, horizon=h, budget=b, delay=d, positive=p)
            records.append({"risk": risk, "cost": cost})
        upper, mix = exact_root_mixture(records, F(1, 20))
        parent, _ = exact_root_mixture(records[:32], F(1, 20))
        class_time = time.perf_counter() - start
        model = RegimeModel(
            transition01=0, transition10=0, emission0=F(1, 5), emission1=p, prior1=1
        )
        game = CausalSwitchingGame(
            GameConfig(
                horizon=h,
                budget=b,
                delay=d,
                alpha=F(1, 20),
                query_cost=F(1, 100),
                switch_cost=F(1, 10),
                max_nodes=200000,
            ),
            model,
        )
        row = {
            "cell": cell,
            "parent_class_cost": str(parent),
            "repaired_class_cost": str(upper),
            "class_seconds": class_time,
            "mixture": [
                {"id": i, "weight": str(w), "controller": prior["controllers"][i]} for i, w in mix
            ],
        }
        start = time.perf_counter()
        try:
            report, _policy, _records = game.solve()
            row["game_seconds"] = time.perf_counter() - start
            for i, _w in mix:
                pol = embed(configs[i], game)
                assert sum(game.expected_metrics(pol)[:3]) == records[i]["cost"]
                assert game.null_risk(pol) == records[i]["risk"]
            assert F(report["calibrated_risk_bound"]) <= F(1, 20)
            ref = F(report["calibrated_total_cost"])
            difference = upper - ref
            row.update(
                status="completed",
                game_report=report,
                exact_difference_vs_feasible_reference=str(difference),
                relative_difference_vs_feasible_reference=float(difference / ref),
                quality_gate_failed_by_feasible_witness=difference > ref / 100,
            )
        except RuntimeError as exc:
            row.update(
                status="capped_or_solver_failure",
                error=str(exc),
                game_seconds=time.perf_counter() - start,
            )
        rows.append(row)
        (DOC / "controller_transfer_results.json").write_text(
            json.dumps({"rows": rows}, indent=2), encoding="utf-8"
        )
        status["completed"].append(cell)
        statuspath.write_text(json.dumps(status), encoding="utf-8")
        print(cell, row["status"], row.get("relative_difference_vs_feasible_reference"), flush=True)
    status["status"] = "completed"
    statuspath.write_text(json.dumps(status), encoding="utf-8")


if __name__ == "__main__":
    main()
