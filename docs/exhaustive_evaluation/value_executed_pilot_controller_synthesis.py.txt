"""Exact finite-class controller search and root randomization; known LP geometry."""

import hashlib
import importlib.util
import json
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from fractions import Fraction as F
from functools import cache
from itertools import combinations, product
from pathlib import Path

from shiftlab.dive.risk_preserving_approx.controller_risk_verifier import verify_causal_null_risk

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"


@dataclass(frozen=True)
class StreakController:
    start: int
    stride: int
    streak: int
    special: str = ""

    @property
    def initial_state(self):
        return 0

    def step(self, memory, time, released, previous_action, remaining_queries):
        for y in released:
            memory = memory + 1 if y else 0
        action = int(
            self.special == "always"
            or previous_action
            or (self.special != "never" and memory >= self.streak)
        )
        query = int(
            not action
            and self.special not in ("never", "always")
            and remaining_queries > 0
            and time >= self.start
            and (time - self.start) % self.stride == 0
        )
        return action, query, min(memory, self.streak)


def alternative_cost(controller, *, horizon, budget, delay, positive=F(4, 5)):
    @cache
    def value(t, memory, old, remaining, pending):
        if t > horizon:
            return F(0)
        released = tuple(v[2] for v in pending if v[0] == t)
        rest = tuple(v for v in pending if v[0] != t)
        action, query, nxt = controller.step(memory, t, released, old, remaining)
        assert not query or remaining > 0
        immediate = (
            (positive if not action else 1 - positive)
            + F(1, 100) * query
            + F(1, 10) * (action != old)
        )
        if not query:
            return immediate + value(t + 1, nxt, action, remaining, rest)
        return (
            immediate
            + (1 - positive) * value(t + 1, nxt, action, remaining - 1, rest + ((t + delay, t, 0),))
            + positive * value(t + 1, nxt, action, remaining - 1, rest + ((t + delay, t, 1),))
        )

    result = value(1, controller.initial_state, 0, budget, ())
    return result, value.cache_info().currsize


def exact_root_mixture(rows, alpha):
    # A finite simplex with one risk inequality has an optimum on <=2 vertices.
    options = [(r["cost"], [(i, F(1))]) for i, r in enumerate(rows) if r["risk"] <= alpha]
    for i, j in combinations(range(len(rows)), 2):
        a, b = rows[i], rows[j]
        if a["risk"] > b["risk"]:
            i, j = j, i
            a, b = b, a
        if not a["risk"] < alpha < b["risk"]:
            continue
        weight = (b["risk"] - alpha) / (b["risk"] - a["risk"])
        options.append(
            (weight * a["cost"] + (1 - weight) * b["cost"], [(i, weight), (j, 1 - weight)])
        )
    return min(options, key=lambda v: v[0])


def main():
    regpath = DOC / "controller_synthesis_pilot_registration.json"
    if regpath.exists():
        raise FileExistsError("inspect existing pilot; do not overwrite")
    configs = [
        StreakController(a, b, k) for a, b, k in product([1, 3, 5, 7], [1, 2, 3], range(2, 8))
    ] + [StreakController(1, 1, 1, "never"), StreakController(1, 1, 1, "always")]
    sources = [
        Path(__file__),
        ROOT / "src/shiftlab/dive/risk_preserving_approx/controller_risk_verifier.py",
    ]
    reg = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "stage": "exact finite-class synthesis pilot, NOT novel planner or unrestricted value certificate",
        "controllers": [asdict(c) for c in configs],
        "cells": [[12, 6, 2], [24, 12, 2]],
        "alpha": "1/20",
        "alternative": "IID positive4/5; zero/one action expected costs4/5,1/5; query1/100 switch1/10",
        "randomization": "root mixture draw hidden from Nature; each component has full causal-null risk<=its verified upper; convex risk mixture sufficient even if Nature infers component",
        "primary": "exact best deterministic and root-mixture cost in declared finite class; total enumeration time/states; no comparison to unrestricted optimum inferred",
        "sources_sha256": {
            p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sources
        },
    }
    regpath.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    rows = []
    cells = []
    for horizon, budget, delay in reg["cells"]:
        start = time.perf_counter()
        records = []
        for c in configs:
            risk = verify_causal_null_risk(c, horizon=horizon, budget=budget, delay=delay)
            cost, states = alternative_cost(c, horizon=horizon, budget=budget, delay=delay)
            records.append(
                {
                    "risk": risk.risk,
                    "cost": cost,
                    "risk_states": risk.visited_states,
                    "alternative_states": states,
                }
            )
        alpha = F(1, 20)
        cost, mix = exact_root_mixture(records, alpha)
        assert sum(w for _, w in mix) == 1
        achieved = sum(records[i]["risk"] * w for i, w in mix)
        assert achieved <= alpha
        deterministic = min((r["cost"], i) for i, r in enumerate(records) if r["risk"] <= alpha)
        cells.append(
            {
                "horizon": horizon,
                "budget": budget,
                "delay": delay,
                "elapsed_seconds": time.perf_counter() - start,
                "best_deterministic_cost": str(deterministic[0]),
                "best_deterministic_id": deterministic[1],
                "best_root_mixture_cost": str(cost),
                "mixture_risk_upper": str(achieved),
                "mixture": [
                    {"id": i, "weight": str(w), "controller": asdict(configs[i])} for i, w in mix
                ],
                "summed_risk_states": sum(r["risk_states"] for r in records),
                "summed_alternative_states": sum(r["alternative_states"] for r in records),
            }
        )
        rows.extend(
            [
                {
                    "horizon": horizon,
                    "id": i,
                    **{k: str(v) if isinstance(v, F) else v for k, v in r.items()},
                }
                for i, r in enumerate(records)
            ]
        )
        print("exact finite class complete", horizon, flush=True)
    dependencies = {
        name: importlib.util.find_spec(name) is not None
        for name in ["stormpy", "gurobipy", "pycarl", "cdd", "pipenv"]
    }
    output = {
        "status": "completed",
        "cells": cells,
        "records": rows,
        "native_solver_dependencies_available": dependencies,
        "limits": "root mixture bound sufficient, not necessarily tight under hidden randomization; no unrestricted optimum/value gap, no author SCP execution, no new safety or complexity theorem",
    }
    (DOC / "controller_synthesis_pilot_results.json").write_text(
        json.dumps(output, indent=2), encoding="utf-8"
    )
    print(json.dumps(cells, indent=2))


if __name__ == "__main__":
    main()
