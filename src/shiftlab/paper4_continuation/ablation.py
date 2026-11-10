"""A3/A4 factorial runtime ablation: R0, R1, R2, I0, F0 (A3_A4_ABLATION_PROTOCOL_V1).

What FCG-fast (``shiftlab.paper4.frontier_cuts_fast``) represents as float vs Fraction
-----------------------------------------------------------------------------------
FLOAT:
  * ``objective`` (cost vector): ``FastGame._alternative`` is the decomposed game's own tree
    build.  Along a path ``weight``, ``posterior``, ``total_cost`` are Fractions; the leaf does
    ``cost[seq] += float(weight * total_cost)``, and the promotion branch does
    ``cost[child] += float(weight * (total_cost + continuation))``.  So each *summand* is the
    float rounding of an exact rational, accumulated in float.  ``FirstPromotionDecomposedGame``
    (R0) runs literally the same ``_alternative`` code, so R0's LP cost vector is the same floats.
  * the master LP (HiGHS, tolerances 1e-9): flow matrix, risk rows, ``alpha`` as float.
  * risk rows: ``float_risk_row`` (dyadic coefficients, exact in float).
  * the LP solution ``x``.
EXACT (Fraction):
  * the continuation DP (``_value_at``, ``_decision_value``, ``_promote_value``) and every belief
    (``_belief_from_history``, ``_transition_belief``, ``_release_due``).
  * policy recovery: ``recover`` rationalises ``x`` with ``limit_denominator(10**9)``.
  * separation: ``best_response_null`` (exact causal-null best response, exact robust risk).
  * dual multipliers (``limit_denominator(10**9)``) and the final certificate: ``exact_costs``,
    exact rows (nonzero duals only), exact weak-duality lower bound ``L``, root repair
    ``_repair`` (realization-space mixing with never-promote), exact ``U`` and repaired risk.

Conclusion for R2.  R0's own pipeline already uses the *same* float objects as FCG-fast: float
cost vector built by the identical ``_alternative``, float LP.  Its exact parts are the identical
Fraction beliefs/DP, recovery, ``expected_metrics`` and ``null_risk`` (final certified cost).  The
only structural differences are (a) R0's LP contains the opponent (null) sequence-form tree and its
float ``risk`` payoff, which *is* the problem R0 solves (replacing it by cut rows is the FCG
contribution, not a numeric-representation choice), and (b) the belief cache (R1).  There is no
numerically legitimate change beyond R1, so **R2 == R1** (alias, ``R2_NOTE``).  In particular, no
quantity in R0 can be turned into float without changing the certified cost: the final cost of
every method here is an exact Fraction.

Belief cache soundness (R1).  ``_belief_from_history(history, outcomes)`` reads only
``time = len(history) + 1``, ``history`` (the ``[1]`` query flags and length), ``self.config``,
``self.model`` and ``visible = dict(self.information(history, outcomes)[1])`` -- never the raw
``outcomes`` otherwise (pending, unreleased outcomes are only consulted through ``visible``).
Hence it is a pure function of ``(history, information(history, outcomes)[1])``, the learner
information key, and memoising on that key is exact.
"""

from __future__ import annotations

import time
from collections import defaultdict
from fractions import Fraction as F

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import vstack

import shiftlab.dive.causal_switching_game as csg
from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame
from shiftlab.paper4 import frontier_cuts_fast as ffast
from shiftlab.paper4.frontier_cuts import (
    best_response_null,
    exact_costs,
    exact_dual_lower_bound_multi,
    risk_row_for_null,
)

METHODS = ("R0", "R1", "R2", "I0", "F0")
R2_NOTE = (
    "R2 == R1: R0 already builds the same float cost vector (identical _alternative) and uses "
    "the same float LP and exact Fraction DP/beliefs/certificate as FCG-fast; no numerically "
    "legitimate change exists beyond the belief cache."
)
MAX_NODES = 200_000

_T = {"horizon": 8, "budget": 3, "delay": 1, "trans": F(3, 4), "emis": (F(1, 20), F(19, 20))}
CELLS = {
    "C6": dict(_T),
    "S1": dict(horizon=10, budget=4, delay=2, trans=F(1, 10), emis=(F(1, 50), F(49, 50))),
    "T10D1": dict(_T, horizon=10),
    "T9D1": dict(_T, horizon=9),
}


def make(cell: str, max_nodes: int = MAX_NODES):
    c = CELLS[cell]
    config = GameConfig(
        horizon=c["horizon"],
        budget=c["budget"],
        delay=c["delay"],
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
        max_nodes=max_nodes,
    )
    model = RegimeModel(
        transition01=c["trans"],
        transition10=c["trans"],
        emission0=c["emis"][0],
        emission1=c["emis"][1],
        prior1=F(1, 2),
    )
    return config, model


class CachedReferenceGame(FirstPromotionDecomposedGame):
    """R1: the reference game with ``_belief_from_history`` memoised by learner information."""

    def __init__(self, config, model) -> None:
        super().__init__(config, model)
        self._belief_cache: dict = {}
        self.belief_hits = 0
        self.belief_misses = 0

    def _belief_from_history(self, history, outcomes):
        key = (history, self.information(history, outcomes)[1])
        belief = self._belief_cache.get(key)
        if belief is None:
            self.belief_misses += 1
            belief = super()._belief_from_history(history, outcomes)
            self._belief_cache[key] = belief
        else:
            self.belief_hits += 1
        return belief


class TimingMixin:
    """Times phases of an R-configuration without changing any computation."""

    def __init__(self, config, model) -> None:
        super().__init__(config, model)
        self.t: dict[str, float] = defaultdict(float)
        self.n_belief_calls = 0
        self._phase = "other"

    def build(self):
        if self.built:
            return
        self._phase = "build"
        t0 = time.perf_counter()
        self._alternative((), (), 0, F(1), self.model.prior1, F(0))
        t1 = time.perf_counter()
        self._null((), (), 0, 0, F(1))
        t2 = time.perf_counter()
        self.built = True
        self.t["build_learner_tree"] += t1 - t0
        self.t["build_null_tree"] += t2 - t1
        self._phase = "other"

    def _belief_from_history(self, history, outcomes):
        t0 = time.perf_counter()
        out = super()._belief_from_history(history, outcomes)
        self.t["belief_in_" + self._phase] += time.perf_counter() - t0
        self.n_belief_calls += 1
        return out

    def _timed_phase(self, phase, fn, *args, **kwargs):
        previous, self._phase = self._phase, phase
        t0 = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            self.t[phase] += time.perf_counter() - t0
            self._phase = previous

    def recover(self, realization):
        return self._timed_phase("policy_recovery", super().recover, realization)

    def expected_metrics(self, policy):
        return self._timed_phase("certificate_expected_metrics", super().expected_metrics, policy)

    def null_risk(self, policy, **kwargs):
        return self._timed_phase("certificate_null_risk", super().null_risk, policy, **kwargs)


class TimedR0(TimingMixin, FirstPromotionDecomposedGame):
    pass


class TimedR1(TimingMixin, CachedReferenceGame):
    pass


def _run_reference(game_cls, config, model) -> dict:
    started = time.perf_counter()
    lp_seconds = [0.0]
    original = csg.linprog

    def timed_linprog(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            lp_seconds[0] += time.perf_counter() - t0

    game = game_cls(config, model)
    csg.linprog = timed_linprog
    try:
        report, _policy, _records = game.solve()
    finally:
        csg.linprog = original
    total = time.perf_counter() - started
    t = game.t
    certificate = t["certificate_expected_metrics"] + t["certificate_null_risk"]
    build = t["build_learner_tree"] + t["build_null_tree"]
    belief = sum(v for k, v in t.items() if k.startswith("belief_in_"))
    accounted = build + lp_seconds[0] + t["policy_recovery"] + certificate
    out = {
        "final_cost": F(report["calibrated_total_cost"]),
        "U": F(report["calibrated_total_cost"]),
        "L": None,
        "exact_risk": F(report["calibrated_risk_bound"]),
        "raw_causal_null_risk": F(report["raw_causal_null_risk"]),
        "nodes": report["nodes"],
        "learner_sequences": report["learner_sequences"],
        "null_sequences": report["opponent_sequences"],
        "cuts": None,
        "iterations": 1,
        "solver_objective": report["solver_objective"],
        "n_belief_calls": game.n_belief_calls,
        "phases": {
            "build_learner_tree": t["build_learner_tree"],
            "build_null_tree": t["build_null_tree"],
            "belief_in_build_inclusive": t["belief_in_build"],
            "belief_total_inclusive": belief,
            "lp": lp_seconds[0],
            "separation_verification": None,
            "policy_recovery": t["policy_recovery"],
            "exact_certificate": certificate,
            "unaccounted_assembly_calibration": total - accounted,
            "total": total,
        },
    }
    if isinstance(game, CachedReferenceGame):
        out["belief_cache_hits"] = game.belief_hits
        out["belief_cache_misses"] = game.belief_misses
    return out


class _FastBeliefTimer:
    """Time ``FastGame._belief_from_history`` calls (inclusive of cache hits) in this process."""

    def __enter__(self):
        self.seconds = 0.0
        self.calls = 0
        self.original = ffast.FastGame._belief_from_history
        outer = self

        def timed(game, history, outcomes):
            t0 = time.perf_counter()
            try:
                return outer.original(game, history, outcomes)
            finally:
                outer.seconds += time.perf_counter() - t0
                outer.calls += 1

        ffast.FastGame._belief_from_history = timed
        return self

    def __exit__(self, *exc):
        ffast.FastGame._belief_from_history = self.original


def _run_f0(config, model) -> dict:
    with _FastBeliefTimer() as timer:
        r = ffast.frontier_cut_generation_fast(config, model)
    return {
        "final_cost": r["U"],
        "U": r["U"],
        "L": r["L"],
        "U0": r["U0"],
        "exact_risk": r["final_robust_risk"],
        "raw_causal_null_risk": r["final_raw_robust_risk"],
        "nodes": r["builder_nodes"],
        "learner_sequences": r["learner_variables"],
        "null_sequences": 0,
        "cuts": r["n_rows"] - 1,
        "iterations": r["n_iterations"],
        "n_belief_calls": timer.calls,
        "phases": {
            "build_learner_tree": r["build_seconds"],
            "belief_total_inclusive": timer.seconds,
            "lp": r["lp_seconds"],
            "separation_verification": r["verify_seconds"],
            "policy_recovery": None,  # inside separation_verification in committed F0
            "cut_rows_float": r["row_seconds"],
            "iteration0_u0_repair_extra": r["u0_seconds"],
            "exact_certificate": r["final_certificate_seconds"],
            "total": r["end_to_end_seconds"],
        },
    }


def _run_i0(config, model) -> dict:
    """FCG-fast iteration 0 only (IID row), then exact causal verification and exact repair.

    Replicates the first loop pass of ``frontier_cut_generation_fast`` using its own functions
    (``FastGame``, ``float_risk_row``, ``_repair``); no cuts are added.
    """
    started = time.perf_counter()
    alpha = config.alpha
    with _FastBeliefTimer() as timer:
        game = ffast.FastGame(config, model)
        game._alternative((), (), 0, F(1), model.prior1, F(0))
        game.built = True
        n = game.learner.count
        flow, flow_rhs = game.learner.matrix()
        objective = np.zeros(n)
        for key, value in game.cost.items():
            objective[key] = value
        iid_row = ffast.float_risk_row(game, {}, n)
        build = time.perf_counter() - started

        t0 = time.perf_counter()
        a_ub = vstack([iid_row], format="csr")
        result = linprog(
            objective,
            A_ub=a_ub,
            b_ub=np.full(1, float(alpha)),
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
        lp = time.perf_counter() - t0
        if not result.success:
            raise RuntimeError(f"IID master LP failed: {result.message}")

        t1 = time.perf_counter()
        raw_policy, _records = game.recover(result.x)
        recovery = time.perf_counter() - t1
        t2 = time.perf_counter()
        robust_risk, _strategy = best_response_null(game, raw_policy)
        separation = time.perf_counter() - t2

        tc = time.perf_counter()
        dual_ub = [F(float(v)).limit_denominator(10**9) for v in result.ineqlin.marginals]
        dual_eq = [F(float(v)).limit_denominator(10**9) for v in result.eqlin.marginals]
        costs = exact_costs(game)
        exact_row = risk_row_for_null(game, {})
        if not np.array_equal(np.array([float(v) for v in exact_row]), iid_row.toarray()[0]):
            raise AssertionError("float IID row differs from exact row")
        lower, _dv, _cm, _cs = exact_dual_lower_bound_multi(
            game, costs, [exact_row if dual_ub[0] else None], flow, flow_rhs, dual_ub, dual_eq
        )
        dual_bound = time.perf_counter() - tc
        tr = time.perf_counter()
        repaired, upper, activation = ffast._repair(game, raw_policy, robust_risk, alpha)
        repaired_risk = game.null_risk(repaired)
        if repaired_risk > alpha:
            raise AssertionError(f"repaired policy risk {repaired_risk} > alpha {alpha}")
        repair = time.perf_counter() - tr
    total = time.perf_counter() - started
    return {
        "final_cost": upper,
        "U": upper,
        "L": lower,
        "exact_risk": repaired_risk,
        "raw_causal_null_risk": robust_risk,
        "activation": activation,
        "nodes": game.nodes,
        "learner_sequences": n,
        "null_sequences": 0,
        "cuts": 0,
        "iterations": 1,
        "n_belief_calls": timer.calls,
        "phases": {
            "build_learner_tree": build,
            "belief_total_inclusive": timer.seconds,
            "lp": lp,
            "separation_verification": separation,
            "policy_recovery": recovery,
            "exact_certificate": dual_bound + repair,
            "exact_certificate_dual_lower_bound": dual_bound,
            "exact_certificate_repair": repair,
            "total": total,
        },
    }


def run_method(method: str, cell: str, max_nodes: int = MAX_NODES) -> dict:
    config, model = make(cell, max_nodes)
    if method == "R0":
        out = _run_reference(TimedR0, config, model)
    elif method in ("R1", "R2"):
        out = _run_reference(TimedR1, config, model)  # R2 == R1 (R2_NOTE)
        if method == "R2":
            out["note"] = R2_NOTE
    elif method == "I0":
        out = _run_i0(config, model)
    elif method == "F0":
        out = _run_f0(config, model)
    else:
        raise ValueError(method)
    out.update(method=method, cell=cell, max_nodes=max_nodes)
    return out
