"""Stage-B candidate implementations: minimal, a-priori-parameterised mechanisms behind the host hooks (WP6).

Every mechanism here is a *reconstruction of the identity's mechanism sentence* with constants fixed before any run
(none tuned); where the identity leaves a quantity unspecified the choice is stated in the class docstring and is
carried into the ledger as ``implementation_notes``. The host is otherwise unchanged:

* Drift2Act ``d2a.request_size``: ``FeedDrift2Act`` is ``Drift2ActContractPolicy`` plus a read-only ``ObsFeed`` (released
  delays and pending ages taken from ``ObservableState``). The hook wraps the host's OWN default
  ``HeuristicQueryPolicy`` and may only gate/scale the size it proposes (host cadence preserved); with no hook
  the wrapper is behaviourally identical to the host (tested).
* RAR ``rar.label_request`` / ``rar.gate2`` / ``rar.gate3`` / ``rar.config``: ``FeedRAR`` is ``RARPolicy`` plus the same feed.
* Cost-Aware Binary ``cab.gate``: ``GatedBinary`` replaces only the economic test of ``BinaryPolicy._evaluate_flag``.
* contract-native hooks (``contract.query``, ``contract.switch_policy``): ``RuleSwitchPolicy`` (host =
  ``UniformQueryNaiveSwitch`` behaviour) with the single rule slot replaced.

Mechanisms that cannot be expressed faithfully on the available hook are NOT implemented (``resolve`` returns
``None`` with a reason in ``SKIP_REASONS``); nothing is approximated silently.
"""

from __future__ import annotations

import math
from contextlib import contextmanager
from dataclasses import dataclass, field

import numpy as np

from shiftlab.bench.contract.adapters_controls import (
    CalendarRule,
    GainSwitchRule,
    RuleSwitchPolicy,
)
from shiftlab.bench.contract.adapters_drift2act import Drift2ActContractPolicy
from shiftlab.bench.contract.adapters_rar import BinaryPolicy, RARPolicy, canary_clocks
from shiftlab.bench.contract.types import INCUMBENT, ClockSpec, EnvSpec

# ------------------------------------------------------------------------------------------ host profile
_HOST_PROFILE = "native_v0"


@contextmanager
def host_profile(profile: str):
    """Set the host-port profile for every Feed*/Gated* host built inside the block (Amendment A1 uses ``calibrated_v1``).

    ``native_v0`` (the default) injects nothing, so suite-v1 behaviour is bit-identical. Single-threaded by design
    (one experiment per worker process)."""
    global _HOST_PROFILE
    prev, _HOST_PROFILE = _HOST_PROFILE, profile
    try:
        yield
    finally:
        _HOST_PROFILE = prev


def _with_profile(kw: dict) -> dict:
    if _HOST_PROFILE != "native_v0":
        kw.setdefault("profile", _HOST_PROFILE)
    return kw


# ------------------------------------------------------------------------------------------ observation feed
class ObsFeed:
    """Read-only summary of ``ObservableState`` for hook objects (released delays, pending ages, budget use)."""

    def __init__(self, env: EnvSpec, window: int = 1024) -> None:
        self.T, self.B, self.c_q, self.h = env.T, env.budget.label_cap, env.costs.c_q, env.hurdle
        self.N = window
        self.t = 0
        self.delays: list[int] = []
        self._seen = 0
        self.pending_ages: list[int] = []
        self.label_used = 0
        self.pending = 0
        self.n_released = 0

    def update(self, state) -> None:
        self.t = state.t
        for lab in state.H[self._seen :]:
            self.delays.append(lab.release_t - lab.request_t)
        self._seen = len(state.H)
        self.pending_ages = [state.t - q.request_t for q in state.Q]
        self.label_used = state.b.label_used
        self.pending = state.b.pending
        self.n_released = len(state.H)

    def median_delay(self, default: int = 10) -> float:
        return float(np.median(self.delays)) if len(self.delays) >= 5 else float(default)

    def p_within(self, slack: float, age: int = 0) -> float:
        """Empirical P(delay <= slack + age | delay > age); optimistic 1.0 until 5 delays are observed."""
        if len(self.delays) < 5:
            return 1.0
        arr = np.asarray(self.delays)
        tail = arr[arr > age]
        if tail.size == 0:
            return 0.0
        return float((tail <= slack + age).mean())


# ------------------------------------------------------------------------------------------ query rules
class Rule:
    """size(feed, n0, info) -> number of labels to request now (n0 = what the host would request)."""

    notes = ""

    def size(self, f: ObsFeed, n0: int, info: dict) -> int:  # pragma: no cover
        raise NotImplementedError


class FeasibleRule(Rule):
    """Request only if P(label released before the deadline) >= q (empirical delay law; in-flight inclusive via the
    host's pending cap). deadline: 'promotion_horizon' = T; 'certificate_window' = min(T, t + N - 1) (N = host window,
    1024 >= T=1000 so the two sources coincide on the frozen suite)."""

    notes = "deadline sources coincide when N>=T (dev suite T=1000, N=1024)"

    def __init__(self, deadline_source: str, q: float) -> None:
        self.src, self.q = deadline_source, q

    def size(self, f, n0, info):
        if n0 <= 0:
            return 0
        d = f.T if self.src == "promotion_horizon" else min(f.T, f.t + f.N - 1)
        return n0 if f.p_within(d - f.t) >= self.q else 0


class InventoryCapRule(Rule):
    """Cap on expected-valid pending mass sum_i P(release before T | age_i) (survival_model='hazard') versus the raw
    pending count (survival_model='none'); cap = max(1, frac * label_cap)."""

    def __init__(self, frac: float, survival: str) -> None:
        self.frac, self.survival = frac, survival

    def size(self, f, n0, info):
        if n0 <= 0:
            return 0
        cap = max(1.0, self.frac * f.B)
        if self.survival == "none":
            mass = float(f.pending)
        else:
            mass = sum(f.p_within(f.T - f.t, a) for a in f.pending_ages)
        return n0 if mass < cap else 0


class UtilisationRule(Rule):
    """Hold pending inventory at target = max(1, frac * B). shadow_price 'off': hard cap at the target. 'static': the
    cap plus budget pacing (label_used <= B t/T + 1) = a static shadow price on spending ahead of the calendar."""

    def __init__(self, frac: float, shadow: str) -> None:
        self.frac, self.shadow = frac, shadow

    def size(self, f, n0, info):
        if n0 <= 0:
            return 0
        target = max(1, round(self.frac * f.B))
        if f.pending >= target:
            return 0
        if self.shadow == "static" and f.label_used > f.B * f.t / f.T + 1:
            return 0
        return n0


class DeadlinePriorityRule(Rule):
    """Credit pacing with weights w_s = 1/(D - s + 1 + d_med) rising toward the deadline D (= T on the frozen suite for
    both deadline sources / pricings): rate_t = remaining_budget * w_t / sum_{s>=t} w_s; request when credit >= 1."""

    notes = "D = T for every deadline_source/horizon_pricing at T=1000<N=1024: configs are behaviourally identical"

    def __init__(self, deadline_source: str, pricing: str) -> None:
        self.src, self.pricing = deadline_source, pricing
        self.credit, self.last_t = 0.0, 0

    def size(self, f, n0, info):
        dt = max(1, f.t - self.last_t) if self.last_t else 1
        self.last_t = f.t
        D = f.T
        if f.t > D:
            return 0
        w = 1.0 / (D - np.arange(f.t, D + 1) + 1 + f.median_delay())
        self.credit += (f.B - f.label_used) * (w[0] / w.sum()) * dt
        k = min(n0, int(self.credit))
        self.credit -= k
        return k


class WindowCloseValueRule(Rule):
    """Host size scaled by P(window still open at release) = P(delay <= T - t); zero below feasibility_q."""

    def __init__(self, q: float) -> None:
        self.q = q

    def size(self, f, n0, info):
        if n0 <= 0:
            return 0
        p = f.p_within(f.T - f.t)
        return int(n0 * p) if p >= self.q else 0


class VOQRule(Rule):
    """VOQ_t = S * P_flip * (T - t) * h - c_q * m_t > 0 -> query. h = public hurdle (benefit per round of a correct
    decision); P_flip: 'certificate' = exp(-|tau-U|/rad) (1 if no certificate yet), 'drift' = 4 b (1-b) with b the
    belief drift mass, 'none' = 1; S = exp(-hazard * d_med) ('hazard') or 1; m_t: 1 ('off'/'static') or
    1 + 20 max(0, used/B - t/T) ('dual', price of spending ahead of the calendar). Constants fixed a priori."""

    def __init__(self, flip: str, shadow: str, survival: str = "none", hazard: float | None = None):
        self.flip, self.shadow, self.survival, self.hazard = flip, shadow, survival, hazard

    def size(self, f, n0, info):
        if n0 <= 0:
            return 0
        if self.flip == "certificate" and np.isfinite(info.get("U", np.inf)):
            p = math.exp(-abs(info["tau"] - info["U"]) / max(info["rad"], 1e-3))
        elif self.flip == "drift" and "drift_mass" in info:
            b = info["drift_mass"]
            p = 4.0 * b * (1.0 - b)
        else:
            p = 1.0
        s = 1.0
        if self.survival == "hazard":
            hz = self.hazard if self.hazard is not None else 3.0 / f.T
            s = math.exp(-hz * f.median_delay())
        mult = 1.0 + (
            20.0 * max(0.0, f.label_used / f.B - f.t / f.T) if self.shadow == "dual" else 0.0
        )
        voq = s * p * (f.T - f.t) * f.h - f.c_q * mult
        return n0 if voq > 0 else 0


class BeliefTriggeredRule(Rule):
    """Certificate refresh (label request) only when belief drift mass > 0.5; otherwise a heartbeat with credit
    min_propensity per host audit tick."""

    def __init__(self, min_rate: float) -> None:
        self.rate, self.credit = min_rate, 0.0

    def size(self, f, n0, info):
        if n0 <= 0:
            return 0
        if info.get("drift_mass", 0.0) > 0.5:
            return n0
        self.credit += self.rate
        if self.credit >= 1.0:
            self.credit -= 1.0
            return n0
        return 0


class RegimeAgeRule(Rule):
    """Query rate a function of time since the last detected regime change: rate(age) = max(floor, exp(-age/100)),
    realised by credit pacing; age resets when the detector flag (t_hat_d) changes."""

    def __init__(self, floor: float) -> None:
        self.floor, self.credit, self.last_t, self.last_flag, self.event_t = floor, 0.0, 0, None, 0

    def size(self, f, n0, info):
        flag = info.get("t_hat_d")
        if flag is not None and flag != self.last_flag:
            self.last_flag, self.event_t = flag, f.t
        dt = max(1, f.t - self.last_t) if self.last_t else 1
        self.last_t = f.t
        self.credit += max(self.floor, math.exp(-(f.t - self.event_t) / 100.0)) * dt
        k = min(max(n0, 1), int(self.credit))
        self.credit -= k
        return k


# ------------------------------------------------------------------------------------------ Drift2Act host
class _D2AHook:
    """request_size hook wrapper: base = host default policy; rule gates/scales the size, never the indices."""

    def __init__(self, feed: ObsFeed, base, rule: Rule) -> None:
        self.feed, self.base, self.rule = feed, base, rule

    def __getattr__(self, name):  # k_high etc. of the host default
        return getattr(self.base, name)

    def request_size(self, ctx) -> int:
        n0 = int(self.base.request_size(ctx))
        info = {
            "drift_mass": 1.0 - float(ctx.belief[0]),
            "U": ctx.prev_U,
            "tau": ctx.tau,
            "rad": ctx.prev_rad,
        }
        return int(self.rule.size(self.feed, n0, info))


class FeedDrift2Act(Drift2ActContractPolicy):
    def __init__(self, rule: Rule | None = None, **kw) -> None:
        super().__init__(**_with_profile(kw))
        self.rule = rule

    def reset(self, env: EnvSpec) -> None:
        super().reset(env)  # builds the host's own default HeuristicQueryPolicy
        self.feed = ObsFeed(env, self.N)
        if self.rule is not None:
            self.policy = _D2AHook(self.feed, self.policy, self.rule)

    def act(self, state):
        self.feed.update(state)
        return super().act(state)


# ------------------------------------------------------------------------------------------ RAR host
class _RARRequest:
    def __init__(self, feed: ObsFeed, rule: Rule) -> None:
        self.feed, self.rule = feed, rule

    def request(self, ctx) -> bool:
        return self.rule.size(self.feed, 1, {"t_hat_d": ctx.t_hat_d}) > 0


class FeedRAR(RARPolicy):
    def __init__(self, rule: Rule | None = None, **kw) -> None:
        super().__init__(**_with_profile(kw))
        self.rule = rule

    def reset(self, env: EnvSpec) -> None:
        super().reset(env)
        self.feed = ObsFeed(env)
        if self.rule is not None:
            self.label_policy = _RARRequest(self.feed, self.rule)
        for g in (self.gate2, self.gate3):
            if hasattr(g, "bind"):
                g.bind(env)

    def act(self, state):
        self.feed.update(state)
        return super().act(state)


def _range(s: str) -> tuple[float, float]:
    lo, hi = s.split("-")
    return float(lo), float(hi)


class Gate2Deadline:
    """Gate-2 label-fraction threshold relaxes linearly from hi to lo as the horizon is consumed."""

    def __init__(self, theta_range: str) -> None:
        self.lo, self.hi = _range(theta_range)

    def bind(self, env):
        self.T = env.T

    def passes(self, ctx) -> bool:
        th = self.hi - (self.hi - self.lo) * min(1.0, ctx.t / self.T)
        return ctx.labeled_in_window >= th * ctx.cfg.W_train - 1e-9


class Gate2RecoveryAware:
    """Required label fraction falls from hi to lo as the estimated recovery rec = A_pre - A_cur grows
    (full relaxation at rec >= 4 theta_R); no estimate -> hi."""

    def __init__(self, theta_range: str) -> None:
        self.lo, self.hi = _range(theta_range)

    def bind(self, env):
        pass

    def passes(self, ctx) -> bool:
        if ctx.acc_pre is None or ctx.acc_cur is None:
            th = self.hi
        else:
            rec = max(0.0, ctx.acc_pre - ctx.acc_cur)
            th = self.hi - (self.hi - self.lo) * min(1.0, rec / (4.0 * ctx.cfg.theta_R))
        return ctx.labeled_in_window >= th * ctx.cfg.W_train - 1e-9


class Gate2ValueOfWaiting:
    """Pass if frac >= hi; fail if frac < lo; between, pass iff the loss of waiting for the missing labels
    (deg * wait_rounds, deg = max(0, A_pre - A_cur); wait_rounds = missing labels / observed label rate;
    'hazard' discounts by P(regime persists) = exp(-wait/(T/3))) exceeds rho * (hi - frac), the retrain cost at
    risk from an under-labelled window."""

    def __init__(self, theta_range: str, model: str) -> None:
        self.lo, self.hi = _range(theta_range)
        self.model = model

    def bind(self, env):
        self.T = env.T

    def passes(self, ctx) -> bool:
        frac = ctx.labeled_in_window / ctx.cfg.W_train
        if frac >= self.hi - 1e-9:
            return True
        if frac < self.lo or ctx.acc_pre is None or ctx.acc_cur is None:
            return False
        rate = max(ctx.n_labels_released / max(ctx.t, 1), 1e-3)
        wait = (self.hi - frac) * ctx.cfg.W_train / rate
        deg = max(0.0, ctx.acc_pre - ctx.acc_cur)
        cost = deg * wait * (math.exp(-wait / (self.T / 3.0)) if self.model == "hazard" else 1.0)
        return cost >= ctx.rho * (self.hi - frac)


class Gate3RecoveryGain:
    """Gate 3: estimated recovery (A_pre - A_cur) x remaining horizon >= rho_scale * rho (c_r): the economic test of
    Cost-Aware Binary, with the remaining deployment horizon instead of the mean inter-detection interval."""

    def __init__(self, rho_scale: float) -> None:
        self.k = rho_scale

    def bind(self, env):
        self.T = env.T

    def passes(self, ctx) -> bool:
        if ctx.acc_pre is None or ctx.acc_cur is None:
            return False
        return max(0.0, ctx.acc_pre - ctx.acc_cur) * max(0, self.T - ctx.t) >= self.k * ctx.rho


# ------------------------------------------------------------------------------------------ Cost-Aware Binary host
class GatedBinary(BinaryPolicy):
    """BinaryPolicy with a replaceable economic test. ``cost_test(policy, d_hat, H, cost, state, a_pre, a_cur) -> bool``;
    default reproduces ``BinaryPolicy._evaluate_flag`` exactly (tested)."""

    def __init__(self, cost_test=None, **kw) -> None:
        super().__init__(cost_aware=True, **_with_profile(kw))
        self.cost_test = cost_test

    def _evaluate_flag(self, state, acts) -> None:
        if self.cost_test is None:
            return super()._evaluate_flag(state, acts)
        from shiftlab.bench.contract.adapters_rar import RETRAINING
        from shiftlab.bench.contract.types import Action

        t, cfg, env = state.t, self.cfg, self.env
        if not self._can_retrain(state):
            return
        self.flag["evaluated"] = True
        a_pre, a_cur = self._acc_pre(self.flag["t_d"]), self._acc_cur(t)
        d_hat = 0.0 if (a_pre is None or a_cur is None) else max(0.0, a_pre - a_cur)
        H = float(np.mean(np.diff(self.detections))) if len(self.detections) >= 2 else 0.0
        H = max(H, float(cfg.W_train))
        cost = float(env.costs.c_r) + (
            0.0 if env.clocks.deploy_on_complete else float(env.costs.c_s)
        )
        ok = bool(self.cost_test(self, d_hat, H, cost, state, a_pre, a_cur))
        self._log(t, "cost_gate", d_hat=d_hat, H=H, cost=cost, passes=ok)
        if not ok:
            self.flag = None
            return
        self._retrain_used0 = state.b.retrain_used
        acts.append(Action("retrain"))
        self.flag = None
        self.st = RETRAINING
        self._log(t, "retrain_issued", reason="binary_flag")


def _z(conf: float) -> float:
    return {0.8: 0.8416, 0.95: 1.6449}[conf]


def cab_test(rule: str, cfg: dict):
    """Economic-test variants for Cost-Aware Binary (hook ``cab.gate``)."""
    z = _z(cfg["promo_conf"]) if "promo_conf" in cfg else 0.0
    margin = {"break_even": 0.0, "margin_1sd": 1.0, "margin_2sd": 2.0}[
        cfg.get("threshold_rule", "break_even")
    ]

    def se(p, a_pre, a_cur):  # binomial s.e. of the accuracy drop from the windows
        n1, n2 = max(p.cfg.W_ref, 1), max(p.cfg.W_cur, 1)
        return math.sqrt(0.25 / n1 + 0.25 / n2)

    def lcb(p, d, H, cost, s, a_pre, a_cur):
        return (max(0.0, d - z * se(p, a_pre, a_cur)) * H) >= cost + margin * se(
            p, a_pre, a_cur
        ) * H

    def label_net(p, d, H, cost, s, a_pre, a_cur):
        net = cost + p.env.costs.c_q * min(s.b.label_remaining, p.cfg.W_cur)
        return (max(0.0, d - z * se(p, a_pre, a_cur)) * H) >= net

    def amortised(p, d, H, cost, s, a_pre, a_cur):
        eff = cfg.get("rho_scale", 1.0) * cost * p.cfg.W_train / max(H, p.cfg.W_train)
        return d * H >= eff + margin * se(p, a_pre, a_cur) * H

    return {"lcb": lcb, "label_net": label_net, "amortised": amortised}[rule]


# ------------------------------------------------------------------------------------------ contract-native rules
class PendingUtilQueryRule:
    """contract.query: hold pending inventory at max(1, frac*B); 'static' adds calendar pacing (see UtilisationRule)."""

    def __init__(self, frac: float, shadow: str) -> None:
        self.rule = UtilisationRule(frac, shadow)

    def reset(self, env):
        self.feed = ObsFeed(env)

    def query(self, state):
        from shiftlab.bench.contract.types import Action

        self.feed.update(state)
        if state.b.label_remaining > 0 and self.rule.size(self.feed, 1, {}) > 0:
            return Action("query")
        return None


class LCBSwitchRule(GainSwitchRule):
    """Promote iff (LB(gain) - h) * (T - t) > c_s + netted label cost, over the last ``window`` released labels.
    LB = mean - z sd/sqrt(n) ('lcb'), the CVaR_alpha lower tail mean of the gains ('cvar'), or mean - margin*se for
    the OSE-style threshold ('ose', margin in {0,1} sd). ``net``: 'pending' = c_q * pending; 'remaining' = c_q *
    min(label_remaining, 20); 'none'."""

    def __init__(self, kind="lcb", conf=0.8, net="pending", margin=0.0, window=20, min_labels=5):
        super().__init__(window, min_labels)
        self.kind, self.conf, self.net, self.margin = kind, conf, net, margin

    def promote(self, state) -> bool:
        if state.m != INCUMBENT or state.available_labels < self.min_labels:
            return False
        g = np.array([x for x in (lab.gain() for lab in state.H[-self.window :]) if x is not None])
        if g.size < self.min_labels:
            return False
        n, mu = g.size, float(g.mean())
        sd = float(g.std(ddof=1)) if n > 1 else 0.5
        if self.kind == "cvar":
            k = max(1, math.ceil((1.0 - self.conf) * n))
            lb = float(np.sort(g)[:k].mean())
        elif self.kind == "ose":
            lb = mu - self.margin * sd / math.sqrt(n)
        else:
            lb = mu - _z(self.conf) * sd / math.sqrt(n)
        c = self.env.costs
        net = {
            "pending": c.c_q * state.b.pending,
            "remaining": c.c_q * min(state.b.label_remaining, 20),
            "none": 0.0,
        }[self.net]
        return (lb - self.env.hurdle) * (self.env.T - state.t) > c.c_s + net


class PostSwitchRollbackRule:
    """Rollback if the mean released paired gain on labels with label_round >= switch time (post-switch window of
    ``window`` labels, >= 10) is below -thr_eff. ``paired``: use shadow incumbent loss (gain); thr_eff =
    thr * (1 - hazard_adj) where hazard_adj = est. reversal hazard (hazard_floor with no observed reversals)."""

    def __init__(self, thr: float, window: int, hazard_floor: float = 0.0):
        self.thr, self.window, self.hz = thr, window, hazard_floor

    def reset(self, env):
        self.switch_t = None

    def rollback(self, state) -> bool:
        if self.switch_t is None:
            self.switch_t = state.t
        g = [
            x
            for lab in state.H
            if lab.label_round >= self.switch_t and (x := lab.gain()) is not None
        ]
        g = g[-self.window :]
        if len(g) < 10:
            return False
        return float(np.mean(g)) < -self.thr * (1.0 - self.hz)


# ------------------------------------------------------------------------------------------ registry
@dataclass
class Impl:
    kind: str  # d2a | rar | cab | naive
    host_kwargs: dict = field(default_factory=dict)
    build_cand: object = None  # (env) -> policy
    clocks: str = "default"  # default | canary
    notes: str = ""
    absent_family: str | None = (
        None  # dev-suite family the mechanism needs but the suite lacks -> UNVERIFIED
    )
    rollback_family: bool = False  # validity = false rollback under the keep-null


def host_policy(kind: str, kwargs: dict | None = None):
    kw = dict(kwargs or {})
    if kind == "d2a":
        return FeedDrift2Act(None, **kw)
    if kind == "rar":
        return FeedRAR(None, **kw)
    if kind == "cab":
        return GatedBinary(None, **kw)
    if kind == "naive":
        return RuleSwitchPolicy(CalendarRule(), name="naive_host")
    raise KeyError(kind)


def make_clocks(kind: str) -> ClockSpec:
    return (
        canary_clocks(retrain_duration=20) if kind == "canary" else ClockSpec(retrain_duration=20)
    )


SKIP_REASONS: dict[str, str] = {
    "evidence_hook": "d2a.evidence_log_lik consumes standardised monitor proxies z=[MMD,dH,dECE]-proxies, not the label chain; "
    "kernel/envelope/gap/restart/hazard-prior mechanisms need binary released outcomes, so no faithful implementation on this hook",
    "propensity": "hook cannot declare/log propensities (rar.label_request returns bool; d2a request_size picks uniform indices), "
    "so IPW-valid adaptive propensities are not representable",
    "proxy": "needs proxy/surrogate predictions (WP2c open)",
    "dynamic_config": "mechanism is dynamic (per-round state), but the hook is a static config dataclass",
    "port_noop": "audit_every/delta_mode: audit_every equals the host default and the port has no delta_mode; behaviourally identical to the host",
    "unspecified": "mechanism under-specified for a faithful minimal implementation (see note)",
    "stake": "predictable-stake e-process absent from the contract-native host (no e-process to size)",
    "lookback": "needs ClockSpec.max_lookback>0 (retrospective query), which differs from the frozen workload clock",
    "ramp": "geometric ramp / uncertainty-triggered canary are dynamic RAR stage logic, not config fields",
}


def resolve(c: dict) -> tuple[Impl | None, str]:
    """(implementation, reason-if-skipped) for a candidate identity."""
    fam, var, host, cfg = c["family"], c["variant"], c["host"], c["configuration"]
    key = (fam, var, host)

    def d2a(mk, notes="", absent=None, **hk):
        return Impl(
            "d2a",
            dict(hk),
            lambda env: FeedDrift2Act(mk(), **hk),
            notes=notes,
            absent_family=absent,
        ), ""

    def rar_req(mk, notes="", absent=None):
        return Impl("rar", {}, lambda env: FeedRAR(mk()), notes=notes, absent_family=absent), ""

    if key == ("pending_aware_budgets", "release_feasible_requests", "drift2act"):
        return d2a(
            lambda: FeasibleRule(cfg["deadline_source"], cfg["feasibility_q"]), FeasibleRule.notes
        )
    if key == ("pending_aware_budgets", "release_weighted_inventory_cap", "drift2act"):
        return d2a(lambda: InventoryCapRule(cfg["pending_cap_frac"], cfg["survival_model"]))
    if key == ("pending_aware_budgets", "pending_utilisation_target", "drift2act"):
        return d2a(lambda: UtilisationRule(cfg["pending_cap_frac"], cfg["shadow_price"]))
    if key == ("pending_aware_budgets", "pending_utilisation_target", "contract_native"):
        return Impl(
            "naive",
            {},
            lambda env: RuleSwitchPolicy(
                PendingUtilQueryRule(cfg["pending_cap_frac"], cfg["shadow_price"]), name="util"
            ),
            notes="host = UniformQueryNaiveSwitch decision rule; only the query rule replaced",
        ), ""
    if fam == "deadline_aware_querying" and var == "certificate_deadline_priority":
        mk = lambda: DeadlinePriorityRule(cfg["deadline_source"], cfg["horizon_pricing"])
        if host == "drift2act":
            return d2a(mk, DeadlinePriorityRule.notes, absent="tight-deadline")
        if host == "rar":
            return rar_req(mk, DeadlinePriorityRule.notes, absent="tight-deadline")
    if key == ("deadline_aware_querying", "window_close_probability_value", "drift2act"):
        return d2a(lambda: WindowCloseValueRule(cfg["feasibility_q"]), absent="tight-deadline")
    if fam == "voi_acquisition" and var in (
        "voq_certificate_state",
        "voq_release_survival",
        "voq_wait_vs_query_generic",
    ):
        shadow = cfg.get("shadow_price", "off")
        if host == "drift2act":
            flip = {
                "voq_certificate_state": "certificate",
                "voq_release_survival": "certificate",
                "voq_wait_vs_query_generic": "drift",
            }[var]
            surv = cfg.get("survival_model", "none")
            return d2a(lambda: VOQRule(flip, shadow, surv))
        if host == "rar" and var == "voq_release_survival":
            return rar_req(
                lambda: VOQRule("none", shadow, cfg.get("survival_model", "none")),
                "RAR has no certificate: P_flip=1",
            )
        return None, SKIP_REASONS[
            "unspecified"
        ] + " (RAR host has no certificate/belief for P_flip)"
    if fam == "hazard_regime_duration" and var == "hazard_survival_for_voq":
        hz = cfg["hazard_floor"]
        if host == "drift2act":
            return d2a(
                lambda: VOQRule("certificate", "off", "hazard", hz), absent="hazard/semi-Markov"
            )
        return rar_req(lambda: VOQRule("none", "off", "hazard", hz), absent="hazard/semi-Markov")
    if key == ("hazard_regime_duration", "regime_age_dependent_query_rate", "rar"):
        return rar_req(lambda: RegimeAgeRule(cfg["hazard_floor"]), absent="hazard/semi-Markov")
    if key == ("drift2act_certification_scheduling", "belief_triggered_certification", "drift2act"):
        return d2a(
            lambda: BeliefTriggeredRule(cfg["min_propensity"]), audit_every=cfg["audit_every"]
        )
    # ---- RAR gates
    if fam == "cost_aware_rar_gate":
        if cfg.get("recovery_estimator") == "heldout_recovery":
            return (
                None,
                "heldout_recovery needs a held-out labelled recovery estimate absent from ObservableState",
            )
        if var == "gate2_deadline_label_fraction":
            g2, g3 = Gate2Deadline(cfg["theta_L_range"]), None
        elif var == "gate2_recovery_aware":
            g2, g3 = Gate2RecoveryAware(cfg["theta_L_range"]), None
        elif var == "gate2_value_of_waiting":
            g2, g3 = Gate2ValueOfWaiting(cfg["theta_L_range"], cfg["waiting_cost_model"]), None
        else:
            g2, g3 = None, Gate3RecoveryGain(cfg["rho_scale"])
        kw = {k: v for k, v in (("gate2", g2), ("gate3", g3)) if v is not None}
        return Impl("rar", {}, lambda env: FeedRAR(None, **kw)), ""
    # ---- RAR canary config
    if fam == "canary_exposure_verification" and host == "rar":
        if var == "economic_exposure_design":
            ov = {k: cfg[k] for k in ("p1", "W1", "W2")}
        elif var == "adaptive_ramp" and cfg.get("ramp") == "fixed":
            ov = {"p1": cfg["p1"]}
        else:
            return (
                None,
                SKIP_REASONS["ramp"]
                if var != "sequential_canary_stop"
                else "Lindon-style sequential test replaces the fixed-W decision (not a config field)",
            )
        return Impl(
            "rar",
            {"cfg_overrides": ov},
            lambda env: FeedRAR(None, cfg_overrides=ov),
            clocks="canary",
            notes="ran with ClockSpec(deploy_on_complete=False) so stage-1 canary exists; ALL methods of the record share it",
            absent_family="RAR-native persistent drift",
        ), ""
    # ---- cooldown (static config transform)
    if var == "cost_scaled_cooldown":
        s = cfg["hold_scale"] * cfg["price_slope"]
        if host == "drift2act":
            return Impl(
                "d2a",
                {},
                lambda env: FeedDrift2Act(
                    None,
                    cooldown_retrain=max(1, round(800 * s * env.costs.c_r / 30.0)),
                    cooldown_rollback=max(1, round(400 * s * env.costs.c_b / 5.0)),
                ),
                notes="cooldown = hold_scale*price_slope*(host default)*c/c_balanced: proportional to the cost of the intervention",
            ), ""
        if host == "rar":
            return Impl(
                "rar",
                {},
                lambda env: FeedRAR(
                    None,
                    cfg_overrides={"kappa_short": max(1, round(150 * s * env.costs.c_b / 5.0))},
                ),
                notes="kappa_short = 150*hold_scale*price_slope*c_b/5 (proportional to rollback cost)",
            ), ""
    # ---- Cost-Aware Binary economic-test variants
    if host == "cost_aware_binary":
        rule = {
            "lcb_break_even_promotion": "lcb",
            "label_cost_net_promotion": "label_net",
            "switch_cost_amortisation": "amortised",
        }.get(var)
        if cfg.get("promo_rule") == "cvar":
            return (
                None,
                "CVaR promotion needs a loss distribution; Cost-Aware Binary's test is a scalar accuracy drop",
            )
        if rule:
            return Impl("cab", {}, lambda env: GatedBinary(cab_test(rule, cfg))), ""
        return None, SKIP_REASONS[
            "unspecified"
        ] + " (pending-label credit adds no information to d_hat)"
    # ---- contract-native whole-policy variants (host = naive decision rule)
    if host == "contract_native":
        if fam == "risk_cost_aware_promotion":
            kind = "cvar" if cfg["promo_rule"] == "cvar" else "lcb"
            net = "remaining" if var == "label_cost_net_promotion" else "pending"
            return Impl(
                "naive",
                {},
                lambda env: RuleSwitchPolicy(
                    CalendarRule(), LCBSwitchRule(kind, cfg["promo_conf"], net), name="promo"
                ),
            ), ""
        if var == "label_cost_aware_ose":
            m = {"break_even": 0.0, "margin_1sd": 1.0}[cfg["threshold_rule"]]
            return Impl(
                "naive",
                {},
                lambda env: RuleSwitchPolicy(
                    CalendarRule(), LCBSwitchRule("ose", 0.8, "remaining", m), name="ose"
                ),
            ), ""
        if var == "reversal_hazard_rollback":
            return Impl(
                "naive",
                {},
                lambda env: RuleSwitchPolicy(
                    CalendarRule(),
                    None,
                    PostSwitchRollbackRule(cfg["rollback_threshold"], 50, cfg["hazard_floor"]),
                    name="rb",
                ),
                absent_family="reversal",
                rollback_family=True,
                notes="host promotion rule inherited; rollback if post-switch mean paired gain < -thr*(1-hazard_floor); no reversal in the dev suite",
            ), ""
        if var == "paired_pre_post_evidence":
            return Impl(
                "naive",
                {},
                lambda env: RuleSwitchPolicy(
                    CalendarRule(),
                    None,
                    PostSwitchRollbackRule(0.0, cfg["post_switch_window"]),
                    name="pp",
                ),
                absent_family="reversal",
                rollback_family=True,
                notes="rollback when the paired incumbent-shadow vs candidate mean gain over the last post_switch_window post-switch labels is < 0",
            ), ""
        if var == "retroactive_query_before_rollback":
            return None, SKIP_REASONS["lookback"]
        if fam in ("predictable_stake_sizing",):
            return None, SKIP_REASONS["stake"]
        return None, SKIP_REASONS["unspecified"]
    # ---- skip classes
    if c["hook"] == "d2a.evidence_log_lik":
        return None, SKIP_REASONS["evidence_hook"]
    if fam == "adaptive_query_propensities":
        return None, SKIP_REASONS["propensity"]
    if fam == "predictive_surrogates_control_variates":
        return None, SKIP_REASONS["proxy"]
    if fam in ("drift2act_certification_scheduling",):
        return None, SKIP_REASONS["port_noop"]
    if fam in ("cooldown_hold_release", "state_dependent_intervention_pricing"):
        return None, SKIP_REASONS["dynamic_config"]
    if var == "voq_reusable_uncertainty":
        return None, SKIP_REASONS[
            "unspecified"
        ] + " (how one label is credited to several pending decisions is not defined)"
    return None, SKIP_REASONS["unspecified"]


__all__ = [
    "SKIP_REASONS",
    "FeedDrift2Act",
    "FeedRAR",
    "GatedBinary",
    "Impl",
    "ObsFeed",
    "host_policy",
    "host_profile",
    "make_clocks",
    "resolve",
]
