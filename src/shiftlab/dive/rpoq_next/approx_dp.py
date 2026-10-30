"""Candidate C: wealth-snapping approximation of the exact RPOQ dynamic program.

Snaps resolved-prefix wealth to a log grid of width ``delta`` inside the value recursion; the
resulting policy is then evaluated *exactly* (true dynamics) by ``rpoq_exact.Evaluator``, so the
reported power and false-alarm probability are certificates, not estimates.
See docs/rpoq_next/SYNTHETIC_PROTOCOL_C1.md.
"""

from __future__ import annotations

import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from shiftlab.dive.rpoq_exact import Evaluator, Instance, constant_table


@dataclass
class SnappedEvaluator(Evaluator):
    delta: float = 0.25

    def _snap(self, w: float) -> float:
        return math.exp(round(math.log(w) / self.delta) * self.delta)

    def post_value(self, t, w, buf, b):
        return super().post_value(t, self._snap(w), buf, b)

    def act(self, t, ctx, w, buf, b):
        return super().act(t, ctx, self._snap(w), buf, b)


def certify(inst: Instance, delta: float) -> dict:
    t0 = time.time()
    ev = SnappedEvaluator(inst, inst.p_alt, inst.budget, delta=delta)
    approx_value = ev.value()
    solve_s = time.time() - t0
    power = Evaluator(inst, inst.p_alt, inst.budget, policy=ev.act).value()
    null = Evaluator(inst, inst.p_null, inst.budget, policy=ev.act).value()
    return {
        "delta": delta,
        "states": len(ev._post),
        "solve_seconds": solve_s,
        "snapped_model_value": approx_value,
        "exact_power": power,
        "exact_null_alarm": null,
    }


def main():
    budgets = [int(a) for a in sys.argv[1:]] or [3, 4, 6]
    s3 = {
        r["budget"]: r
        for r in json.loads(Path("outputs/rpoq_s3_structure_v1/results.json").read_text())[
            "results"
        ]
    }
    sys.setrecursionlimit(10000)
    rows = []
    for b in budgets:
        inst = Instance(budget=b)
        t0 = time.time()
        exact = Evaluator(inst, inst.p_alt, b)
        exact_power = exact.value()
        exact_s = time.time() - t0
        best_const = max(
            Evaluator(inst, inst.p_alt, b, policy=constant_table({0: qa, 1: qb})).value()
            for qa in inst.grid
            for qb in inst.grid
        )
        base = {
            "budget": b,
            "exact_power": exact_power,
            "exact_states": len(exact._post),
            "exact_seconds": exact_s,
            "best_constant_power": best_const,
            "s3_registered_power": s3[b]["power_optimal"],
        }
        for delta in (0.5, 0.25, 0.1):
            r = certify(inst, delta)
            gap = exact_power - best_const
            r["recovery"] = (r["exact_power"] - best_const) / gap if gap > 0.01 else None
            r["state_ratio"] = base["exact_states"] / r["states"]
            r["speedup"] = exact_s / r["solve_seconds"]
            rows.append({**base, **r})
            print(
                {k: (round(v, 4) if isinstance(v, float) else v) for k, v in rows[-1].items()},
                flush=True,
            )
    out = Path("outputs/rpoq_next/c1")
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
