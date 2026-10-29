"""Exact solver for the RPOQ S3 structure test (resolved-prefix optimal querying).

Toy instance only: binary paired contrast, two contexts with different proxies, fixed label
delay, hard pathwise query budget, and a betting e-process updated through the contiguous
resolved prefix. See ``docs/rpoq_s3_structure_protocol_v1.md``. This is a structure probe on a
synthetic instance, not a method and not evidence of novelty.
"""

from __future__ import annotations

import itertools
import json
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

Entry = tuple  # ("d", factor) resolved, or ("p", arrival, context, q) pending


@dataclass(frozen=True)
class Instance:
    horizon: int = 10
    delay: int = 2
    budget: int = 4
    alpha: float = 0.2
    bet_fraction: float = 0.5
    p_context: tuple[float, ...] = (0.5, 0.5)
    p_alt: tuple[float, ...] = (0.8, 0.7)
    p_null: tuple[float, ...] = (0.5, 0.5)
    proxy: tuple[float, ...] = (0.6, 0.0)
    grid: tuple[float, ...] = (0.25, 0.5, 0.75, 1.0)

    @property
    def threshold(self) -> float:
        return 1.0 / self.alpha

    def bet(self, context: int, q: float) -> float:
        h = self.proxy[context]
        x_min = min(h, h + (-1.0 - h) / q, h + (1.0 - h) / q)
        return self.bet_fraction / abs(x_min)

    def factor(self, context: int, q: float, z: int) -> float:
        h = self.proxy[context]
        return 1.0 + self.bet(context, q) * (h + (z - h) / q)

    def unqueried_factor(self, context: int, q: float) -> float:
        return 1.0 + self.bet(context, q) * self.proxy[context]


Policy = Callable[[int, int, float, tuple, int], float]


@dataclass
class Evaluator:
    """Success probability of a policy (or the optimum when ``policy`` is None)."""

    inst: Instance
    p_z: tuple[float, ...]
    budget: int
    policy: Policy | None = None
    _post: dict = field(default_factory=dict)
    _start: dict = field(default_factory=dict)
    groups: dict = field(default_factory=dict)

    @staticmethod
    def _key(w: float) -> float:
        return round(w, 10)

    def _flush(self, w: float, buf: tuple) -> tuple[float, tuple, bool]:
        while buf and buf[0][0] == "d":
            w = self._key(w * buf[0][1])
            buf = buf[1:]
            if w >= self.inst.threshold - 1e-12:
                return w, buf, True
        return w, buf, False

    def _arrive(self, t: int, w: float, buf: tuple):
        idx = [i for i, e in enumerate(buf) if e[0] == "p" and e[1] == t]
        if not idx:
            return [(1.0, w, buf, False)]
        outs = []
        for zs in itertools.product((-1, 1), repeat=len(idx)):
            prob = 1.0
            new = list(buf)
            for i, z in zip(idx, zs, strict=True):
                _, _, ctx, q = buf[i]
                pz = self.p_z[ctx]
                prob *= pz if z == 1 else 1.0 - pz
                new[i] = ("d", self.inst.factor(ctx, q, z))
            w2, b2, succ = self._flush(w, tuple(new))
            outs.append((prob, w2, b2, succ))
        return outs

    def start_value(self, t: int, w: float, buf: tuple, b: int) -> float:
        key = (t, w, buf, b)
        hit = self._start.get(key)
        if hit is not None:
            return hit
        total = 0.0
        for prob, w2, b2, succ in self._arrive(t, w, buf):
            total += prob if succ else prob * self.post_value(t, w2, b2, b)
        self._start[key] = total
        return total

    def _continue(self, t: int, w: float, buf: tuple, b: int) -> float:
        w, buf, succ = self._flush(w, buf)
        return 1.0 if succ else self.start_value(t + 1, w, buf, b)

    def q_value(self, t: int, ctx: int, w: float, buf: tuple, b: int, q: float) -> float:
        inst = self.inst
        v_no = self._continue(
            t, w, (*buf, ("d", inst.unqueried_factor(ctx, q))), b
        ) if q < 1.0 else 0.0
        v_yes = self._continue(t, w, (*buf, ("p", t + inst.delay, ctx, q)), b - 1)
        return (1.0 - q) * v_no + q * v_yes

    def post_value(self, t: int, w: float, buf: tuple, b: int) -> float:
        key = (t, w, buf, b)
        hit = self._post.get(key)
        if hit is not None:
            return hit
        inst = self.inst
        if t >= inst.horizon:
            val = self.start_value(t + 1, w, buf, b) if buf else 0.0
        else:
            val = 0.0
            for ctx, pc in enumerate(inst.p_context):
                if b == 0:
                    val += pc * self._continue(t, w, buf, 0)
                    continue
                if self.policy is not None:
                    q = self.policy(t, ctx, w, buf, b)
                    val += pc * self.q_value(t, ctx, w, buf, b, q)
                    continue
                values = [self.q_value(t, ctx, w, buf, b, q) for q in inst.grid]
                best = max(values)
                argmax = tuple(q for q, v in zip(inst.grid, values, strict=True) if v >= best - 1e-9)
                self.groups.setdefault((t, ctx, b, buf), []).append((w, argmax))
                val += pc * best
        self._post[key] = val
        return val

    def act(self, t: int, ctx: int, w: float, buf: tuple, b: int) -> float:
        """Optimal grid propensity for this evaluator's ``p_z`` (smallest on ties)."""
        values = [self.q_value(t, ctx, w, buf, b, q) for q in self.inst.grid]
        best = max(values)
        return next(q for q, v in zip(self.inst.grid, values, strict=True) if v >= best - 1e-9)

    def value(self) -> float:
        return self.start_value(0, 1.0, (), self.budget)


def constant_table(table: dict[int, float]) -> Policy:
    return lambda t, ctx, w, buf, b: table[ctx]


def neyman_table(inst: Instance) -> dict[int, float]:
    """Propensity proportional to sqrt(E[(Z-H)^2 | x]) under the alternative, max scaled to 1."""
    scores = []
    for ctx, p in enumerate(inst.p_alt):
        h = inst.proxy[ctx]
        scores.append((p * (1 - h) ** 2 + (1 - p) * (-1 - h) ** 2) ** 0.5)
    top = max(scores)
    return {
        ctx: min(inst.grid, key=lambda g, s=s: abs(g - s / top)) for ctx, s in enumerate(scores)
    }


def _selection_exists(sets: list[tuple[float, ...]]) -> bool:
    lo = float("-inf")
    for s in sets:
        feasible = [v for v in s if v >= lo]
        if not feasible:
            return False
        lo = min(feasible)
    return True


def monotone_in_wealth(argmax_by_wealth: list[tuple[float, tuple[float, ...]]]) -> bool:
    ordered = [s for _, s in sorted(argmax_by_wealth, key=lambda item: item[0])]
    if _selection_exists(ordered):
        return True
    return _nonincreasing(ordered)


def _nonincreasing(sets: list[tuple[float, ...]]) -> bool:
    hi = float("inf")
    for s in sets:
        feasible = [v for v in s if v <= hi]
        if not feasible:
            return False
        hi = max(feasible)
    return True


def structure_report(ev: Evaluator) -> dict:
    tested = passed = 0
    failing = []
    for key, rows in ev.groups.items():
        by_w: dict[float, tuple[float, ...]] = {}
        for w, s in rows:
            by_w[w] = s
        if len(by_w) < 3:
            continue
        tested += 1
        if monotone_in_wealth(list(by_w.items())):
            passed += 1
        elif len(failing) < 10:
            failing.append({"t": key[0], "context": key[1], "budget": key[2], "n_wealth": len(by_w)})
    return {
        "groups_tested": tested,
        "groups_monotone": passed,
        "fraction_monotone": passed / tested if tested else None,
        "example_failures": failing,
    }


def run_budget(inst: Instance) -> dict:
    t0 = time.time()
    alt = Evaluator(inst, inst.p_alt, inst.budget)
    v_opt = alt.value()
    null_opt = Evaluator(inst, inst.p_null, inst.budget, policy=alt.act).value()
    structure = structure_report(alt)

    table_rows = []
    for qa, qb in itertools.product(inst.grid, repeat=2):
        pol = constant_table({0: qa, 1: qb})
        v_alt = Evaluator(inst, inst.p_alt, inst.budget, policy=pol).value()
        v_null = Evaluator(inst, inst.p_null, inst.budget, policy=pol).value()
        table_rows.append({"q_A": qa, "q_B": qb, "power": v_alt, "null_alarm": v_null})
    best_const = max(table_rows, key=lambda r: r["power"])

    ney = neyman_table(inst)
    ney_pol = constant_table(ney)
    always1 = constant_table({0: 1.0, 1: 1.0})
    return {
        "budget": inst.budget,
        "power_optimal": v_opt,
        "null_alarm_optimal": null_opt,
        "best_constant_table": best_const,
        "gap_vs_best_constant": v_opt - best_const["power"],
        "neyman_table": {str(k): v for k, v in ney.items()},
        "power_neyman": Evaluator(inst, inst.p_alt, inst.budget, policy=ney_pol).value(),
        "null_alarm_neyman": Evaluator(inst, inst.p_null, inst.budget, policy=ney_pol).value(),
        "power_always_q1": Evaluator(inst, inst.p_alt, inst.budget, policy=always1).value(),
        "max_null_alarm_constants": max(r["null_alarm"] for r in table_rows),
        "structure": structure,
        "n_states": len(alt._post),
        "seconds": time.time() - t0,
        "constant_tables": table_rows,
    }


def main(argv: list[str] | None = None) -> None:
    args = argv if argv is not None else sys.argv[1:]
    budgets = [int(a) for a in args] or [2, 3, 4, 6]
    sys.setrecursionlimit(10000)
    results = []
    for b in budgets:
        res = run_budget(Instance(budget=b))
        results.append(res)
        print(
            f"B={b} power_opt={res['power_optimal']:.4f} "
            f"best_const={res['best_constant_table']['power']:.4f} "
            f"neyman={res['power_neyman']:.4f} q1={res['power_always_q1']:.4f} "
            f"null_opt={res['null_alarm_optimal']:.4f} "
            f"mono={res['structure']['fraction_monotone']} states={res['n_states']} "
            f"{res['seconds']:.1f}s",
            flush=True,
        )
    out = Path("outputs/rpoq_s3_structure_v1")
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps({"instance": Instance().__dict__, "results": results}, indent=2, default=str))


if __name__ == "__main__":
    main()
