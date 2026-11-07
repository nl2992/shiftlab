"""Prospective stronger verifier reference; never reruns original one-shot T18 cell."""

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from shiftlab.dive.risk_preserving_approx.controller_risk_lp import verify_controller_lp
from shiftlab.dive.risk_preserving_approx.controller_risk_verifier import verify_causal_null_risk

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"
REG = DOC / "controller_lp_comparison_registration.json"
OUT = DOC / "controller_lp_comparison_results.json"


@dataclass(frozen=True)
class RunController:
    threshold: int
    initial_state: int = 0

    def step(self, memory, time, released, previous_action, remaining_queries):
        for y in released:
            memory = memory + 1 if y else 0
        if memory >= self.threshold:
            return 1, 0, memory
        return 0, int(remaining_queries > 0), memory


def main(action):
    if action == "register":
        if REG.exists():
            raise FileExistsError("comparison registration exists")
        value = {
            "registered_utc": datetime.now(UTC).isoformat(),
            "question": "J DP versus standard product-MDP LP, not full synthesis",
            "cells": [
                {"T": T, "B": B, "d": d, "k": k}
                for T, B, d, k in [
                    (12, 6, 1, 3),
                    (24, 12, 1, 3),
                    (24, 12, 2, 3),
                    (24, 12, 4, 3),
                    (48, 24, 2, 6),
                    (48, 24, 4, 6),
                ]
            ],
            "original_one_shot_T18_not_repeated": True,
            "criterion": "risk difference <=1e-10; record wall time and states, no novelty claim",
            "scope": "LP reference is known Bellman inequality algorithm, not author robust-FSC solver",
            "sources": {
                p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                for p in [
                    "src/shiftlab/dive/risk_preserving_approx/controller_risk_lp.py",
                    "src/shiftlab/dive/risk_preserving_approx/controller_risk_verifier.py",
                    "scripts/exhaustive_evaluation/benchmark_standard_controller_lp.py",
                ]
            },
        }
        REG.write_text(json.dumps(value, indent=2), encoding="utf-8")
        return
    reg = json.loads(REG.read_text())
    assert all(
        hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in reg["sources"].items()
    )
    if OUT.exists():
        raise FileExistsError("comparison already executed")
    result = {"status": "running", "cells": []}
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    for cell in reg["cells"]:
        c = RunController(cell["k"])
        kw = {"horizon": cell["T"], "budget": cell["B"], "delay": cell["d"]}
        start = perf_counter()
        exact = verify_causal_null_risk(c, **kw)
        seconds_dp = perf_counter() - start
        start = perf_counter()
        lp = verify_controller_lp(c, **kw)
        seconds_lp = perf_counter() - start
        error = abs(float(exact.risk) - lp.risk)
        assert error <= 1e-10
        result["cells"].append(
            dict(
                **cell,
                exact_risk=str(exact.risk),
                lp=asdict(lp),
                risk_absolute_error=error,
                dp_seconds=seconds_dp,
                lp_seconds=seconds_lp,
                ratio_lp_over_dp=seconds_lp / seconds_dp,
            )
        )
        OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(
            cell, "risk matches;", round(seconds_dp, 4), round(seconds_lp, 4), "seconds", flush=True
        )
    result["status"] = "completed"
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["register", "run"])
    main(parser.parse_args().action)
