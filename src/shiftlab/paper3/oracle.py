"""Exact finite-horizon economic-belief DP over a known 2-state hidden-Markov regime model.

SCOPE. This is the Bayes-optimal controller for J(A,Q) = E[sum ell_t(A_t) + c_q sum Q_t
+ k sum 1{A_t != A_{t-1}}] when the learner KNOWS the regime model (transition matrix, prior,
per-regime Bernoulli loss rates), the delay d is a known constant, and at most B labels can be
requested (pending included). It is an economic-belief benchmark, NOT a robust global-null-risk
oracle: it can promote on weak evidence if the known prior makes that profitable. The
risk-constrained counterpart (alpha-safe under the full causal null) is ``oracle_risk``, which
wires the existing sequence-form LP in ``shiftlab.dive.causal_switching_game``
(research/risk-preserving-switching-approx-2026-10-29@2bd2e8e; same file is on main at ce1f98ad).

Information state at the start of round t (after release): (t, a_prev, remaining, obs, pend),
obs = released (request_time, (ell0, ell1)) pairs, pend = request times of unreleased labels
that can still arrive. Exact arithmetic with ``fractions.Fraction`` (or floats via ``num``).
Hidden regime and unreleased outcomes are never in the state.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from functools import cache, lru_cache
from itertools import product

import numpy as np

from .contracts import Paper3Decision, PolicyAdapter, PolicyView, ProblemSpec

OUTCOMES = ((0, 0), (0, 1), (1, 0), (1, 1))  # (ell0, ell1)


@dataclass(frozen=True)
class HMMModel:
    """s_t in {0,1}; P(s_1=1)=prior1; trans[i][j]=P(s_{t+1}=j|s_t=i);
    m0[s]=P(ell0=1|s), m1[s]=P(ell1=1|s) independent given the regime (so Z in {-1,0,1})."""

    trans: tuple[tuple[F, F], tuple[F, F]] = ((F(9, 10), F(1, 10)), (F(1, 10), F(9, 10)))
    prior1: F = F(1, 2)
    m0: tuple[F, F] = (F(1, 2), F(1, 2))
    m1: tuple[F, F] = (F(1, 2), F(1, 5))

    def emit(self, s: int, o: tuple[int, int]):
        a = self.m0[s] if o[0] else 1 - self.m0[s]
        b = self.m1[s] if o[1] else 1 - self.m1[s]
        return a * b

    def sample_tape(self, T: int, rng: np.random.Generator) -> np.ndarray:
        s = int(rng.random() < float(self.prior1))
        ell = np.zeros((T, 2))
        for t in range(T):
            if t:
                s = int(rng.random() < float(self.trans[s][1]))
            ell[t] = [rng.random() < float(self.m0[s]), rng.random() < float(self.m1[s])]
        return ell


@dataclass(frozen=True)
class OracleResult:
    value: object
    policy: dict  # info-state -> (action, query)
    n_states: int


class EconomicOracle:
    def __init__(self, model: HMMModel, T: int, B: int, d: int, c_q, k, num=F):
        if d < 1 or T < 1 or B < 0:
            raise ValueError("need T >= 1, B >= 0, d >= 1")
        self.T, self.B, self.d = T, B, d
        self.c_q, self.k = num(c_q), num(k)
        self.model = HMMModel(
            tuple(tuple(num(x) for x in row) for row in model.trans),
            num(model.prior1),
            tuple(num(x) for x in model.m0),
            tuple(num(x) for x in model.m1),
        )
        self.one = num(1)
        self._alpha = lru_cache(maxsize=None)(self._alpha_raw)
        self.solve_state = lru_cache(maxsize=None)(self._solve_state)

    # ---- exact filtering --------------------------------------------------------------
    def _alpha_raw(self, obs: tuple, t: int):
        """Unnormalised P(s_t = s, obs) for obs = ((tau, o), ...) with tau <= t."""
        m = self.model
        al = [self.one - m.prior1, m.prior1]
        od = dict(obs)
        for tau in range(1, t + 1):
            if tau > 1:
                al = [al[0] * m.trans[0][j] + al[1] * m.trans[1][j] for j in (0, 1)]
            if tau in od:
                al = [al[s] * m.emit(s, od[tau]) for s in (0, 1)]
        return al

    def joint(self, obs: tuple):
        """P(all outcomes in obs) (exact forward probability)."""
        if not obs:
            return self.one
        return sum(self._alpha(obs, obs[-1][0]))

    def expected_loss(self, obs: tuple, t: int, a: int):
        al = self._alpha(obs, t)
        rates = self.model.m0 if a == 0 else self.model.m1
        return (al[0] * rates[0] + al[1] * rates[1]) / (al[0] + al[1])

    # ---- DP ---------------------------------------------------------------------------
    def _choices(self, rem: int):
        return [(a, q) for q in ((0, 1) if rem > 0 else (0,)) for a in (0, 1)]

    def _step(self, state, a, q, value_fn):
        """Immediate cost plus expected continuation of choice (a, q) in ``state``."""
        t, a_prev, rem, obs, pend = state
        cost = self.expected_loss(obs, t, a) + self.k * (a != a_prev) + self.c_q * q
        if t == self.T:
            return cost
        pend2 = pend + ((t,) if (q and t + self.d <= self.T) else ())
        tau = t + 1 - self.d
        if tau in pend2:
            rest = tuple(x for x in pend2 if x != tau)
            den = self.joint(obs)
            for o in OUTCOMES:
                nobs = obs + ((tau, o),)
                p = self.joint(nobs) / den
                if p:
                    cost += p * value_fn((t + 1, a, rem - q, nobs, rest))
        else:
            cost += value_fn((t + 1, a, rem - q, obs, pend2))
        return cost

    def _solve_state(self, state):
        best = None
        for a, q in self._choices(state[2]):
            c = self._step(state, a, q, lambda s: self.solve_state(s)[0])
            if best is None or c < best[0]:
                best = (c, (a, q))
        return best

    def root(self):
        return (1, 0, self.B, (), ())

    def solve(self) -> OracleResult:
        val = self.solve_state(self.root())[0]
        pol = {}
        stack = [self.root()]
        while stack:  # reachable states under the optimal policy
            s = stack.pop()
            if s in pol or s[0] > self.T:
                continue
            _, (a, q) = self.solve_state(s)
            pol[s] = (a, q)
            t, _, rem, obs, pend = s
            if t == self.T:
                continue
            pend2 = pend + ((t,) if (q and t + self.d <= self.T) else ())
            tau = t + 1 - self.d
            if tau in pend2:
                rest = tuple(x for x in pend2 if x != tau)
                den = self.joint(obs)
                stack += [
                    (t + 1, a, rem - q, obs + ((tau, o),), rest)
                    for o in OUTCOMES
                    if self.joint(obs + ((tau, o),)) / den
                ]
            else:
                stack.append((t + 1, a, rem - q, obs, pend2))
        return OracleResult(val, pol, len(pol))

    def policy_value(self, fn):
        """Exact J of an information-state policy ``fn(state) -> (a, q)`` (q only if budget)."""

        @cache
        def v(state):
            a, q = fn(state)
            if q and state[2] <= 0:
                raise ValueError("policy exceeds budget")
            return self._step(state, a, q, v)

        return v(self.root())


def solve_economic(model: HMMModel, T: int, B: int, d: int, c_q, k, num=F) -> OracleResult:
    return EconomicOracle(model, T, B, d, c_q, k, num).solve()


# ------------------------------------------------------------------------------------------
# brute force over ALL deterministic (full-history) policies, tapes enumerated independently
# ------------------------------------------------------------------------------------------
def _tape_probabilities(model: HMMModel, T: int) -> dict:
    out = {}
    for tape in product(OUTCOMES, repeat=T):
        tot = F(0)
        for path in product((0, 1), repeat=T):
            pr = model.prior1 if path[0] else 1 - model.prior1
            for t in range(1, T):
                pr *= model.trans[path[t - 1]][path[t]]
            for t in range(T):
                pr *= model.emit(path[t], tape[t])
            tot += pr
        out[tape] = tot
    return out


def brute_force_optimum(model: HMMModel, T: int, B: int, d: int, c_q, k):
    """Enumerate every deterministic policy tree and score it on every outcome tape.

    Independent of the filtering recursion: probabilities come from summing over all hidden
    paths; costs use realised losses along each tape. Returns (optimal value, #policies).
    Only for tiny instances (T <= 4).
    """
    c_q, k = F(c_q), F(k)
    probs = _tape_probabilities(model, T)

    def strategies(t, rem, reqs):
        # a strategy is (choice, {key: substrategy}); key = released outcome or None
        outs = []
        for q in (0, 1) if rem > 0 else (0,):
            for a in (0, 1):
                reqs2 = reqs + ((t,) if (q and t + d <= T) else ())
                if t == T:
                    outs.append(((a, q), {}))
                    continue
                tau = t + 1 - d
                if tau in reqs2:
                    rest = tuple(x for x in reqs2 if x != tau)
                    sub = strategies(t + 1, rem - q, rest)
                    for combo in product(sub, repeat=len(OUTCOMES)):
                        outs.append(((a, q), dict(zip(OUTCOMES, combo, strict=True))))
                else:
                    for sub in strategies(t + 1, rem - q, reqs2):
                        outs.append(((a, q), {None: sub}))
        return outs

    # exact integer scoring: scale probabilities and costs to a common denominator
    from math import lcm

    den_p = lcm(*(pr.denominator for pr in probs.values()))
    den_c = lcm(c_q.denominator, k.denominator)
    pint = {tp: int(pr * den_p) for tp, pr in probs.items()}
    cq_i, k_i = int(c_q * den_c), int(k * den_c)

    def walk_cost(strategy, tape):  # realised cost along one tape, scaled by den_c
        node, t, prev, total, reqs = strategy, 1, 0, 0, set()
        while True:
            (a, q), kids = node
            total += tape[t - 1][a] * den_c + k_i * (a != prev) + cq_i * q
            if q and t + d <= T:
                reqs.add(t)
            if t == T:
                return total
            prev, t = a, t + 1
            tau = t - d
            node = kids[tape[tau - 1]] if tau in reqs else kids[None]

    best, n = None, 0
    for st in strategies(1, B, ()):
        n += 1
        ev = sum(p * walk_cost(st, tape) for tape, p in pint.items())
        if best is None or ev < best:
            best = ev
    return F(best, den_p * den_c), n


# ------------------------------------------------------------------------------------------
# policy adapter: run the DP policy inside the shared simulator loop (end-to-end check)
# ------------------------------------------------------------------------------------------
class OraclePolicy(PolicyAdapter):
    name = "economic_oracle"

    def __init__(self, oracle: EconomicOracle):
        self.o = oracle

    def reset(self, spec: ProblemSpec, rng) -> None:
        self.obs, self.pend = (), ()

    def act(self, view: PolicyView) -> Paper3Decision:
        for lab in sorted(view.released, key=lambda x: x.t_request):
            self.obs += ((lab.t_request, (int(lab.ell0), int(lab.ell1))),)
            self.pend = tuple(x for x in self.pend if x != lab.t_request)
        t = view.t
        state = (t, view.prev_action, view.labels_remaining, self.obs, self.pend)
        _, (a, q) = self.o.solve_state(state)
        if q and t + self.o.d <= self.o.T:
            self.pend += (t,)
        return Paper3Decision(a, q)


# ------------------------------------------------------------------------------------------
# risk-constrained oracle: wires the existing exact sequence-form LP (no reimplementation)
# ------------------------------------------------------------------------------------------
def oracle_risk(
    horizon, budget, delay, alpha=F(1, 10), query_cost=F(1, 100), switch_cost=F(1, 10), model=None
) -> dict:
    """Exact alpha-safe (full causal null) optimum for the classical single-outcome game.

    Source: research/risk-preserving-switching-approx-2026-10-29@2bd2e8e,
    src/shiftlab/dive/causal_switching_game.py (also on main). Its model is a binary common
    outcome with promotion absorbing; it is not the paired-loss HMM of ``EconomicOracle`` and
    the two values are not directly comparable. alpha=1 gives its unconstrained economic cost.
    """
    from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
    from shiftlab.dive.delayed_regime_information import RegimeModel

    cfg = GameConfig(
        horizon=horizon,
        budget=budget,
        delay=delay,
        alpha=F(alpha),
        query_cost=F(query_cost),
        switch_cost=F(switch_cost),
    )
    report, _policy, _records = CausalSwitchingGame(cfg, model or RegimeModel()).solve()
    return report
