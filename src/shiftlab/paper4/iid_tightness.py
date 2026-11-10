"""IID-tightness check: is the IID-relaxed optimum's safety explained by monotone promotion events?

Implements `docs/paper4/experiments/protocols/IID_TIGHTNESS_CHECK_V1.md` (steps 1-5).
Tapes are indexed MSB-first: tape ``y`` has index ``sum_t y_t * 2**(T - t)``, so setting
``y_t = 1`` adds ``2**(T - t)`` to the index.
"""

from __future__ import annotations

import time
from fractions import Fraction as F
from itertools import product

import numpy as np
from scipy.optimize import linprog

from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.paper4.frontier_cuts_fast import FastGame, float_risk_row

TOL = 1e-9
PLAN_CAP = 200_000
MAX_RANDOMIZED_FOR_ENUMERATION = 12
MAX_NODES = 200_000

# id -> (horizon, budget, delay, transition, emissions)
CELL_TABLE = {
    "C1": (5, 2, 1, F(1, 4), (F(1, 20), F(19, 20))),
    "C2": (5, 2, 1, F(9, 10), (F(1, 10), F(9, 10))),
    "C3": (6, 3, 1, F(3, 4), (F(1, 20), F(19, 20))),
    "C4": (6, 3, 1, F(1, 4), (F(1, 20), F(19, 20))),
    "C5": (8, 3, 1, F(1, 4), (F(1, 20), F(19, 20))),
    "C6": (8, 3, 1, F(3, 4), (F(1, 20), F(19, 20))),
    "S1": (10, 4, 2, F(1, 10), (F(1, 50), F(49, 50))),
    "S2": (10, 4, 2, F(3, 4), (F(1, 50), F(49, 50))),
    "S3": (10, 4, 2, F(3, 4), (F(1, 20), F(19, 20))),
}


def make_cell(name: str) -> tuple[GameConfig, RegimeModel]:
    horizon, budget, delay, trans, emis = CELL_TABLE[name]
    config = GameConfig(
        horizon=horizon,
        budget=budget,
        delay=delay,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
        max_nodes=MAX_NODES,
    )
    model = RegimeModel(
        transition01=trans,
        transition10=trans,
        emission0=emis[0],
        emission1=emis[1],
        prior1=F(1, 2),
    )
    return config, model


# ---------------------------------------------------------------- monotonicity on tapes


def tape_masks(horizon: int) -> tuple[list[int], list[int]]:
    """Bitsets over tape indices: ``m1[t]`` = tapes with y_t = 1, ``m0[t]`` = with y_t = 0 (t 1-based)."""
    n = 1 << horizon
    full = (1 << n) - 1
    m1 = [0] * (horizon + 1)
    for t in range(1, horizon + 1):
        shift = horizon - t
        bits = 0
        for idx in range(n):
            if (idx >> shift) & 1:
                bits |= 1 << idx
        m1[t] = bits
    m0 = [full ^ m1[t] if t else 0 for t in range(horizon + 1)]
    return m0, m1


def cover_violations(values: np.ndarray, horizon: int, tol: float = TOL) -> dict:
    """Monotonicity of ``G`` on the hypercube: violations of ``G(y) <= G(y + e_t)`` over covers."""
    g = np.asarray(values, dtype=float)
    if g.shape != (1 << horizon,):
        raise ValueError("values must have length 2**horizon")
    idx = np.arange(1 << horizon)
    max_viol = 0.0
    count = 0
    examples: list[tuple[float, int, int]] = []
    for t in range(1, horizon + 1):
        step = 1 << (horizon - t)
        lower = idx[((idx >> (horizon - t)) & 1) == 0]
        viol = g[lower] - g[lower + step]
        max_viol = max(max_viol, float(viol.max()))
        bad = np.nonzero(viol > tol)[0]
        count += int(bad.size)
        for j in bad:
            examples.append((float(viol[j]), int(lower[j]), t))
    examples.sort(key=lambda e: -e[0])
    witnesses = []
    for _v, y, t in examples[:3]:
        step = 1 << (horizon - t)
        witnesses.append(
            {
                "y": format(y, f"0{horizon}b"),
                "t": t,
                "G_y": float(g[y]),
                "G_y_with_t_set_to_1": float(g[y + step]),
            }
        )
    return {
        "max_violation": max_viol,
        "n_violating_covers": count,
        "n_covers": horizon * (1 << (horizon - 1)),
        "monotone": count == 0,
        "witnesses": witnesses,
    }


def bitset_violations(
    event: int, horizon: int, m0: list[int]
) -> tuple[int, tuple[int, int] | None]:
    """Number of covers with event(y)=1, event(y+e_t)=0; plus one witness (tape index, t)."""
    count = 0
    witness = None
    for t in range(1, horizon + 1):
        step = 1 << (horizon - t)
        bad = ((event & m0[t]) << step) & ~event
        if bad:
            count += bad.bit_count()
            if witness is None:
                low = (bad & -bad).bit_length() - 1
                witness = (low - step, t)
    return count, witness


# ---------------------------------------------------------------- the IID LP optimum


def solve_iid_lp(config: GameConfig, model: RegimeModel):
    """FCG-fast iteration 0: learner tree, float costs, single IID risk row, HiGHS."""
    game = FastGame(config, model)
    game._alternative((), (), 0, F(1), model.prior1, F(0))
    game.built = True
    n = game.learner.count
    flow, flow_rhs = game.learner.matrix()
    objective = np.zeros(n)
    for key, value in game.cost.items():
        objective[key] = value
    row = float_risk_row(game, {}, n)
    result = linprog(
        objective,
        A_ub=row,
        b_ub=np.array([float(config.alpha)]),
        A_eq=flow,
        b_eq=flow_rhs,
        bounds=[(0, None)] * n,
        method="highs",
        options={
            "time_limit": 600.0,
            "primal_feasibility_tolerance": 1e-9,
            "dual_feasibility_tolerance": 1e-9,
        },
    )
    if not result.success:
        raise RuntimeError(f"IID LP failed: {result.message}")
    return game, result


# ---------------------------------------------------------------- tape traversal


class PolicyTree:
    """Learner tree restricted to positive-probability choices of a behavioural policy."""

    def __init__(self, game: FastGame, policy) -> None:
        self.game, self.policy = game, policy
        self.horizon = game.config.horizon
        self.m0, self.m1 = tape_masks(self.horizon)
        self.n_tapes = 1 << self.horizon
        self.full = (1 << self.n_tapes) - 1
        self._nodes: dict = {}
        self.randomized_reached: dict = {}  # key -> list of (choice, prob) with prob > TOL
        self.max_dropped_mass = 0.0

    def node(self, history, outcomes):
        """(info key, [(choice, float prob)]) for positive-probability choices (prob > TOL)."""
        state = (history, outcomes)
        hit = self._nodes.get(state)
        if hit is None:
            key = self.game.information(history, outcomes)
            probs = self.policy(history, outcomes)
            kept = [
                (choice, float(p))
                for choice, p in zip(self.game.choices(history), probs, strict=True)
                if p > TOL
            ]
            dropped = float(sum(p for p in probs if 0 < p <= TOL))
            self.max_dropped_mass = max(self.max_dropped_mass, dropped)
            hit = (key, kept)
            self._nodes[state] = hit
        return hit

    def promotion_function(self) -> np.ndarray:
        """G(y) for all tapes: exact behavioural promotion probability along the tape (float)."""
        horizon, m1_bool = self.horizon, {}
        idx = np.arange(self.n_tapes)
        for t in range(1, horizon + 1):
            m1_bool[t] = ((idx >> (horizon - t)) & 1) == 1
        memo: dict = {}
        ones = np.ones(self.n_tapes)

        def visit(history, outcomes):
            time_ = len(history) + 1
            if time_ > horizon:
                return np.zeros(self.n_tapes)
            state = (history, outcomes)
            if state in memo:
                return memo[state]
            key, kept = self.node(history, outcomes)
            if len(kept) > 1:
                self.randomized_reached[key] = kept
            total = np.zeros(self.n_tapes)
            for (action, query), prob in kept:
                if action:
                    total += prob * ones
                    continue
                following = history + ((action, query),)
                if query:
                    zero = visit(following, outcomes + ((time_, 0),))
                    one = visit(following, outcomes + ((time_, 1),))
                    total += prob * np.where(m1_bool[time_], one, zero)
                else:
                    total += prob * visit(following, outcomes)
            memo[state] = total
            return total

        return visit((), ())

    def plan_event(self, plan: dict) -> int:
        """Promotion event (bitset over tapes) of the pure plan ``plan``: key -> choice."""
        horizon = self.horizon

        def visit(history, outcomes):
            time_ = len(history) + 1
            if time_ > horizon:
                return 0
            key, kept = self.node(history, outcomes)
            action, query = plan[key] if key in plan else kept[0][0]
            if action:
                return self.full
            following = history + ((action, query),)
            if query:
                zero = visit(following, outcomes + ((time_, 0),))
                one = visit(following, outcomes + ((time_, 1),))
                return (zero & self.m0[time_]) | (one & self.m1[time_])
            return visit(following, outcomes)

        return visit((), ())


def enumerate_plans(tree: PolicyTree, randomized: dict) -> dict:
    keys = list(randomized)
    n_plans = 1
    for key in keys:
        n_plans *= len(randomized[key])
    out = {"n_randomized_reached": len(keys), "n_pure_plans": n_plans}
    if len(keys) > MAX_RANDOMIZED_FOR_ENUMERATION:
        return {**out, "enumerated": False, "reason": "more than 12 randomized information sets"}
    if n_plans > PLAN_CAP:
        return {**out, "enumerated": False, "reason": f"plan count exceeds cap {PLAN_CAP}"}
    horizon = tree.horizon
    n_bad = 0
    bad_weight = 0.0
    total_weight = 0.0
    witness = None
    for combo in product(*(randomized[k] for k in keys)):
        weight = 1.0
        plan = {}
        for key, (choice, prob) in zip(keys, combo, strict=True):
            plan[key] = choice
            weight *= prob
        total_weight += weight
        count, cover = bitset_violations(tree.plan_event(plan), horizon, tree.m0)
        if count:
            n_bad += 1
            bad_weight += weight
            if witness is None:
                y, t = cover
                witness = {
                    "y": format(y, f"0{horizon}b"),
                    "t": t,
                    "n_violating_covers": count,
                    "weight": weight,
                    "plan_choices": [
                        {"history": repr(k[0]), "released": repr(k[1]), "choice": list(plan[k])}
                        for k in keys
                    ],
                }
    return {
        **out,
        "enumerated": True,
        "n_non_monotone_plans": n_bad,
        "weight_on_non_monotone_plans": bad_weight,
        "total_weight": total_weight,
        "witness": witness,
    }


# ---------------------------------------------------------------- the cell check


def classify(safe: bool, g: dict, plans: dict) -> dict:
    if safe:
        if not g["monotone"]:
            label = "NOT EXPLAINED"
        elif plans["enumerated"] and plans["n_non_monotone_plans"] == 0:
            label = "EXPLAINED"
        else:
            label = "UNRESOLVED"
        return {"group": "IID-safe", "classification": label}
    if not g["monotone"] or (plans["enumerated"] and plans["n_non_monotone_plans"] > 0):
        contrast = "CONSISTENT (non-monotone G or non-monotone plans)"
    elif plans["enumerated"]:
        contrast = "CONTRADICTION (G monotone and all plans monotone): debug before concluding"
    else:
        contrast = "INCONCLUSIVE (G monotone, plans not enumerated)"
    return {"group": "IID-unsafe", "classification": None, "contrast_check": contrast}


def check_cell(config: GameConfig, model: RegimeModel) -> dict:
    started = time.perf_counter()
    game, lp = solve_iid_lp(config, model)
    policy, records = game.recover(lp.x)
    r_causal = game.null_risk(policy)
    r_iid = game.null_risk(policy, iid_boundary=True)

    n_random_all = sum(
        any(TOL < float(F(p)) < 1 - TOL for p in rec["probabilities"]) for rec in records
    )

    tree = PolicyTree(game, policy)
    g_values = tree.promotion_function()
    g_report = cover_violations(g_values, config.horizon)
    g_report["max_distance_to_0_1"] = float(np.minimum(g_values, 1 - g_values).max())
    g_report["values_within_1e-9_of_0_1"] = g_report["max_distance_to_0_1"] <= TOL
    g_report["min"], g_report["max"] = float(g_values.min()), float(g_values.max())
    g_report["promotion_prob_iid_boundary_mean"] = float(g_values.mean())

    randomized = tree.randomized_reached
    plans = enumerate_plans(tree, randomized)
    safe = r_causal == r_iid
    verdict = classify(safe, g_report, plans)
    consistency = []
    if plans.get("enumerated") and plans["n_non_monotone_plans"] == 0 and not g_report["monotone"]:
        consistency.append("all plans monotone but G not monotone: bug")
    if plans.get("enumerated") and plans["n_non_monotone_plans"] == 0 and r_causal != r_iid:
        consistency.append("all plans monotone but R_causal != R_IID: contradicts theorem or bug")
    if plans.get("enumerated") and abs(plans["total_weight"] - 1.0) > 1e-6:
        consistency.append(f"plan weights sum to {plans['total_weight']}")

    return {
        "cell_config": {
            "horizon": config.horizon,
            "budget": config.budget,
            "delay": config.delay,
            "alpha": str(config.alpha),
        },
        "learner_variables": game.learner.count,
        "lp_objective": float(lp.fun),
        "R_causal": str(r_causal),
        "R_IID": str(r_iid),
        "R_causal_float": float(r_causal),
        "R_IID_float": float(r_iid),
        "iid_safe_exact_equality": safe,
        "n_info_sets": len(records),
        "n_randomized_info_sets_all": n_random_all,
        "n_randomized_info_sets_reached": len(randomized),
        "max_dropped_mass_below_tol": tree.max_dropped_mass,
        "G": g_report,
        "plans": plans,
        **verdict,
        "consistency_flags": consistency,
        "seconds": time.perf_counter() - started,
    }
