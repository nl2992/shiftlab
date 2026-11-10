"""Shared potential-outcome tapes, regime generator, policy loop and evaluator.

Tapes hold both potential losses ell_t(0), ell_t(1) per round and are generated once per
(regime, seed); every policy is run on the identical tape. Evaluator-only truth (``Truth``) is a
separate object that ``run_policy`` never sees. Seeds are SeedSequence entropy integers; stages
are registered in configs/paper3/seed_registry_v1.json.

Generator (all vectorised): latent p_t = P(challenger correct | disagreement) from a path spec;
disagreement ~ Bernoulli(r); on disagreement exactly one model errs, the challenger is correct
iff Phi(u_t) < p_t with u an AR(1) Gaussian copula (marginals exact, serial dependence rho);
without disagreement both models share one error draw (prob e_both). So Z_t in {-1, 0, 1}.
"""

from __future__ import annotations

import json
import zlib
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import numpy as np
from scipy.signal import lfilter
from scipy.special import ndtr

from .budgets import BudgetLedger
from .contracts import (
    Costs,
    Paper3Decision,
    Paper3Event,
    PolicyAdapter,
    PolicyView,
    ProblemSpec,
    ReleasedLabel,
    RunRecord,
)
from .feedback_queue import PendingFeedbackQueue

CONFIG_DIR = Path(__file__).resolve().parents[3] / "configs" / "paper3"


# --------------------------------------------------------------------------------------------
# data objects
# --------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Tape:
    """Policy-independent realisation: potential losses, observables, pre-drawn label delays."""

    ell: np.ndarray  # (T, 2) losses of action 0 / 1
    disagree: np.ndarray  # (T,) bool, observable before the label
    x: np.ndarray  # (T, dx) observable features
    delay: np.ndarray  # (T,) delay applied if a label is requested at t
    meta: dict = field(default_factory=dict)

    def __post_init__(self):
        for arr in (self.ell, self.disagree, self.x, self.delay):
            arr.flags.writeable = False

    @property
    def T(self) -> int:
        return len(self.ell)


@dataclass(frozen=True)
class Truth:
    """Evaluator-only. Never passed to policies, monitors or adaptation code."""

    regime_id: str
    p: np.ndarray  # P(challenger correct | disagreement)
    r: float
    mu: np.ndarray  # E[Z_t] = r (2p - 1)
    change_points: tuple[int, ...]
    global_null: bool  # mu_t <= 0 for all t


@dataclass(frozen=True)
class Regime:
    id: str
    params: dict
    costs: Costs
    B: int


# --------------------------------------------------------------------------------------------
# registry / config
# --------------------------------------------------------------------------------------------
@cache
def _load(name: str) -> dict:
    return json.loads((CONFIG_DIR / name).read_text(encoding="utf-8"))


def seed_blocks() -> dict[str, tuple[int, int]]:
    return {k: tuple(v) for k, v in _load("seed_registry_v1.json")["blocks"].items()}


def seeds_for(stage: str, n: int, start: int = 0) -> list[int]:
    lo, hi = seed_blocks()[stage]
    if lo + start + n - 1 > hi:
        raise ValueError(f"seed request leaves the registered {stage} block")
    return list(range(lo + start, lo + start + n))


def load_regimes(path: str | None = None) -> dict[str, Regime]:
    cfg = json.loads(Path(path).read_text(encoding="utf-8")) if path else _load("regimes_v1.json")
    d = cfg["defaults"]
    out = {}
    for g in cfg["regimes"]:
        p = {**d, **{k: v for k, v in g.items() if k not in ("costs", "B")}}
        costs = Costs(**{**d["costs"], **g.get("costs", {})})
        out[g["id"]] = Regime(g["id"], p, costs, int(g.get("B", d["B"])))
    return out


def make_spec(regime: Regime, T: int) -> ProblemSpec:
    dl = regime.params["delay"]
    known = int(dl["d"]) if dl["kind"] == "fixed" else None
    return ProblemSpec(
        T=T, B=regime.B, costs=regime.costs, delay_known=known, delay_kind=dl["kind"]
    )


# --------------------------------------------------------------------------------------------
# generator
# --------------------------------------------------------------------------------------------
def _p_path(spec: dict, T: int) -> tuple[np.ndarray, tuple[int, ...]]:
    t = (np.arange(T) + 0.5) / T
    kind = spec["type"]
    if kind == "steps":
        kn = np.array(spec["knots"], float)
        idx = np.searchsorted(kn[:, 0], t, side="right") - 1
        p = kn[np.clip(idx, 0, len(kn) - 1), 1]
    elif kind == "linear":
        kn = np.array(spec["knots"], float)
        p = np.interp(t, kn[:, 0], kn[:, 1])
    elif kind == "seasonal":
        ph = ((t - spec.get("phase", 0.0)) / spec["period_frac"]) % 1.0
        p = np.where(ph < spec["duty"], spec["hi"], spec["lo"])
    else:
        raise ValueError(f"unknown path type {kind}")
    cps = tuple(int(i) + 1 for i in np.flatnonzero(np.diff(p) != 0))
    return p, cps


def generate_tape(regime: Regime, seed: int, T: int) -> tuple[Tape, Truth]:
    prm = regime.params
    rng = np.random.default_rng([int(seed), zlib.crc32(regime.id.encode()), 7])
    p, cps = _p_path(prm["path"], T)
    r, rho = float(prm["r"]), float(prm["rho"])
    # AR(1) Gaussian copula: stationary N(0,1) marginals, lag-1 correlation rho
    e = rng.standard_normal(T)
    u0 = rng.standard_normal()
    u = lfilter([np.sqrt(1 - rho**2)], [1.0, -rho], e, zi=[rho * u0])[0]
    challenger_correct = ndtr(u) < p
    disagree = rng.random(T) < r
    shared_err = (rng.random(T) < float(prm["e_both"])).astype(float)
    # on disagreement exactly one model errs: model 0 errs iff the challenger is correct
    ell0 = np.where(disagree, challenger_correct.astype(float), shared_err)
    ell1 = np.where(disagree, 1.0 - ell0, shared_err)
    mu = r * (2 * p - 1)
    sent = float(prm["x_scale"]) * ((2 * p - 1) - (2 * p[0] - 1))
    x = np.column_stack([sent + rng.standard_normal(T), rng.standard_normal(T)])
    dl = prm["delay"]
    if dl["kind"] == "fixed":
        delay = np.full(T, int(dl["d"]))
    elif dl["kind"] == "random":
        delay = rng.choice(np.array(dl["values"]), size=T, p=np.array(dl["probs"]))
    elif dl["kind"] == "informative":
        favours = disagree & challenger_correct
        delay = int(dl["d"]) + int(dl["extra"]) * favours.astype(int)
    else:
        raise ValueError(f"unknown delay kind {dl['kind']}")
    tape = Tape(
        np.column_stack([ell0, ell1]),
        disagree,
        x,
        delay.astype(int),
        {"regime": regime.id, "seed": int(seed), "delay_kind": dl["kind"], "rho": rho},
    )
    truth = Truth(regime.id, p, r, mu, cps, bool(np.all(mu <= 0)))
    return tape, truth


# --------------------------------------------------------------------------------------------
# contract-enforcing loop
# --------------------------------------------------------------------------------------------
def run_policy(policy: PolicyAdapter, tape: Tape, spec: ProblemSpec, policy_seed: int) -> RunRecord:
    """Run one policy on one tape. The policy only ever receives ``PolicyView`` objects."""
    T = spec.T
    if tape.T != T:
        raise ValueError("tape horizon != spec.T")
    policy.reset(spec, np.random.default_rng([int(policy_seed), 11]))
    queue, led = PendingFeedbackQueue(), BudgetLedger(spec.B, spec.costs, spec.compute_budget)
    a, q, u, rt = (np.zeros(T, int) for _ in range(4))
    rtime = np.zeros(T, int)
    prev = 0
    for t in range(1, T + 1):
        released = tuple(
            ReleasedLabel(treq, t, pl[0], pl[1]) for avail, treq, pl in queue.release(t)
        )
        led.release(len(released))
        ev = Paper3Event(t, bool(tape.disagree[t - 1]), tuple(float(v) for v in tape.x[t - 1]))
        view = PolicyView(
            t, ev, released, prev, led.labels_remaining, led.pending, led.compute_remaining
        )
        dec = policy.act(view)
        if not isinstance(dec, Paper3Decision) or dec.action not in (0, 1):
            raise ValueError("policy must return Paper3Decision with action in {0,1}")
        if dec.query not in (0, 1) or dec.compute not in (0, 1) or dec.retrain not in (0, 1):
            raise ValueError("query/compute/retrain must be 0 or 1")
        if dec.query:
            led.request_query()
            rtime[t - 1] = queue.request(
                t, (float(tape.ell[t - 1, 0]), float(tape.ell[t - 1, 1])), int(tape.delay[t - 1])
            )
        if dec.compute:
            led.use_compute()
        led.retrains += dec.retrain
        led.switches += int(dec.action != prev)
        led.deploy_loss += float(tape.ell[t - 1, dec.action])
        a[t - 1], q[t - 1], u[t - 1], rt[t - 1] = dec.action, dec.query, dec.compute, dec.retrain
        prev = dec.action
    led.check(queue.n_pending)
    return RunRecord(a, q, u, rt, rtime, led.totals())


# --------------------------------------------------------------------------------------------
# evaluator
# --------------------------------------------------------------------------------------------
def hindsight_oracle_cost(ell: np.ndarray, k: float) -> float:
    """min over action paths of sum ell_t(a_t) + k * switches (a_0 = 0). UNATTAINABLE."""
    c0, c1 = 0.0, k  # cost of being at action 0 / 1 before round 1
    for t in range(len(ell)):
        n0 = min(c0, c1 + k) + ell[t, 0]
        n1 = min(c1, c0 + k) + ell[t, 1]
        c0, c1 = n0, n1
    return float(min(c0, c1))


class SimulationEvaluator:
    """Full decomposition of J plus the five separate error notions (evaluator side)."""

    def __init__(self, tape: Tape, truth: Truth, costs: Costs, horizon_h: int = 50):
        self.tape, self.truth, self.costs, self.h = tape, truth, costs, horizon_h
        self.J_never = float(tape.ell[:, 0].sum())
        self.J_oracle = hindsight_oracle_cost(tape.ell, costs.k)

    def evaluate(self, rec: RunRecord) -> dict:
        tp, tr, k = self.tape, self.truth, self.costs.k
        a = rec.a
        T = len(a)
        prev = np.r_[0, a[:-1]]
        promo = (prev == 0) & (a == 1)
        mu = tr.mu
        out = dict(rec.ledger)
        out["J_never"] = self.J_never
        out["delta_vs_never"] = out["J"] - self.J_never
        out["regret_hindsight_UNATTAINABLE"] = out["J"] - self.J_oracle
        # (1) global-null false promotion: any promotion when mu_t <= 0 for all t
        out["global_null"] = int(tr.global_null)
        out["global_null_false_promotion"] = int(tr.global_null and promo.any())
        # (2) current-regime value: expected-loss rate on the wrong side of the true mean
        out["frac_time_wrong_model"] = float(np.mean((mu > 0) != (a == 1))) if T else 0.0
        out["missed_improvement"] = float(np.sum(np.where(a == 0, np.maximum(mu, 0), 0)))
        out["excess_harm"] = float(np.sum(np.where(a == 1, np.maximum(-mu, 0), 0)))
        out["false_promotions"] = int(np.sum(promo & (mu <= 0)))
        # (3) future payback: promotions whose realised true-mean gain until the next change of
        #     action is below the switch fee (evaluator-side, uses truth)
        unpaid = 0
        for t in np.flatnonzero(promo):
            nxt = np.flatnonzero(a[t:] == 0)
            end = t + nxt[0] if len(nxt) else T
            unpaid += int(mu[t:end].sum() < k)
        out["unpaid_promotions"] = unpaid
        # (4) intervention safety: worst cumulative excess realised cost against never-switch
        step = tp.ell[np.arange(T), a] - tp.ell[:, 0]
        extra = np.cumsum(step) + np.cumsum(self.costs.c_q * rec.q + self.costs.c_compute * rec.u)
        extra = extra + k * np.cumsum(a != prev)
        out["max_drawdown_vs_never"] = float(max(0.0, extra.max())) if T else 0.0
        # (5) dynamic regret: hindsight oracle is unattainable; also gap to a known-mean oracle
        out["J_hindsight_oracle_UNATTAINABLE"] = self.J_oracle
        return out
