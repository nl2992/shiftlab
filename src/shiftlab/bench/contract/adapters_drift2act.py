"""COMMON_CONTRACT_PORT of the Drift2Act controller (Lamaakal et al., arXiv:2603.08578; PAPER_RECONSTRUCTION in
``shiftlab.sota.drift2act``).

What runs: windowed uniform auditing (label requests charged through the contract), certificate
``U_t = R^_t + rad(n, delta)`` of the model in force on released labels inside the window, gate ``U_t <= tau``,
belief-weighted utility ``Delta_t(a) - lambda c(a) - gamma Viol_t(a)`` over the contract-available action subset,
cooldowns, abstain on gate failure, rollback to the last certified model else retrain.

Action map (Drift2Act -> contract):
  A0 no-op -> continue            A3 query labels -> ``query`` (audit boost to k_high for the next audit)
  A2 test-time adaptation -> switch(CANDIDATE) (candidate stands in for the cheap adapted model; the coordinator's map)
  A4 retrain -> retrain           A5 rollback -> rollback (only if prev_m is the last certified model)
  A6 abstain/handoff -> abstain   certificate-failure notice -> alert (rate limited)
  UNMAPPED: A1 recalibrate (the contract has no in-place model edit). ``route``, switch to RETRAINED are never used.

Deviations from the native controller (each is a closest-observable proxy or a contract-induced change):
* sensing z_t=[MMD2, dH, dECE] needs embeddings and predictive probabilities, which ObservableState lacks. Proxies on the
  scalar monitor ``state.x`` and released losses, standardised on a warm-up reference: z1 = mean-shift z-score (MMD proxy),
  z2 = log-scale-ratio z-score (entropy-shift proxy), z3 = recent-vs-reference released-loss z-score (dECE proxy).
* evidence p(z|d) is hand-specified (|z| half-normal under 'none', N(3, 2^2) under any drift) and untuned: the contract has
  no calibration episodes; the three drift types are indistinguishable here, so the belief separates none vs drift only.
  Transition matrix T is hand-set (stay 0.99). These are Q1-hook swappable (``evidence``).
* A6 is charged c_h per abstained ROUND by the contract (native: once on activation).
* gain table G(d,a) is the paper's (App. E.6, H=150); cost term uses contract prices normalised by the largest price.
* the window can only reach back ``ClockSpec.max_lookback`` rounds; with the default 0 the audit degenerates to labelling
  the current round (at most one query per round) and the certificate window is that of the labelled rounds released so far.
* certificate pools all released labels in the window (``pool='window'``, ``delta_mode='mandate'``): exact only for
  stationary within-window risk (heuristic otherwise, see docs/d2a_rar/baselines/DRIFT2ACT.md section 2).

Q1 outcome-evidence seam (opt-in): if ``evidence`` has ``bind_env``/``outcome_sink`` (``evidence_seam.OutcomeAugmentedEvidence``) the
host feeds it the RELEASED labelled outcomes each round before the belief update; the default ``ProxyEvidence`` has neither, so the
default path is byte-for-byte the pre-seam behaviour (golden test tests/d2a_rar/test_q1_evidence.py). The host's own label selection
(request size from belief/certificate state, which uses the current monitor x_t) is NOT predictable in the outcome filtration, and its
queries carry no declared propensity, so Q1 evidence run on this host is out-of-contract for validity claims (descriptive only).

Profiles: ``native_v0`` (default, unchanged since cc867f40) and ``calibrated_v1`` (WP6 host audit, docs/d2a_rar/status/wp6_host_audit.md):
C1 audit pacing ``audit_every = ceil(T/label_cap)`` with k_low=1 so that k_low/audit_every <= B/T (native_v0 rounds k_low up => 5x over budget at B/T=0.05);
C2 paper round constants (N, retrain/rollback cooldowns; L=1500) scaled by T/1500. Nothing else differs.

Claimed null: ``abs_risk`` (gate ``U_t <= tau`` bounds the windowed risk of the model in force under UNIFORM sampling from the
window). It is NOT valid under informative delay/missingness (released labels are then a loss-dependent subset), serial
dependence, or a request-size policy that selects *which* rounds to label non-uniformly. The Q2 hook
(``request_policy``, a ``LabelRequestPolicy``) replaces only the request SIZE; round choice stays uniform.
"""

from __future__ import annotations

import math

import numpy as np

from shiftlab.sota.drift2act.actions import GAIN
from shiftlab.sota.drift2act.audit import HeuristicQueryPolicy, LabelRequestPolicy, QueryContext
from shiftlab.sota.drift2act.belief import BeliefFilter
from shiftlab.sota.drift2act.certificate import rad

from .policies import BasePolicy
from .types import CANDIDATE, INCUMBENT, Action, EnvSpec, ObservableState

PAPER_L = 1500  # Drift2Act App. E episode length L; round-valued paper constants are scaled by T / PAPER_L in calibrated_v1
PROFILES = ("native_v0", "calibrated_v1")

# native action indices used in GAIN columns
A0, A2, A3, A4, A5, A6 = 0, 2, 3, 4, 5, 6
MAPPED = (A0, A2, A3, A4, A5, A6)
UNMAPPED = ("A1_recalibrate",)


class ProxyEvidence:
    """Hand-specified evidence over (none, covariate, concept, subgroup) from |z| of the three standardised proxies."""

    def __init__(self, m: float = 3.0, s: float = 2.0, beta: float = 1.0) -> None:
        self.m, self.s, self.beta = m, s, beta

    def log_lik(self, z, gap: int = 1) -> np.ndarray:
        a = np.abs(np.asarray(z, float))
        none = -0.5 * float(np.sum(a**2))
        drift = -0.5 * float(np.sum(((a - self.m) / self.s) ** 2)) - a.size * math.log(self.s)
        return self.beta * np.array([none, drift, drift, drift])


def _hand_T(stay: float = 0.99, smooth: float = 1e-3) -> np.ndarray:
    T = np.zeros((4, 4))
    T[0, 0], T[0, 1:] = stay, (1 - stay) / 3
    for d in (1, 2, 3):
        T[d, d], T[d, 0] = stay, 1 - stay
    return (1 - smooth) * T + smooth / 4


class Drift2ActContractPolicy(BasePolicy):
    name = "drift2act"

    def __init__(
        self,
        tau: float = 0.5,
        delta: float = 0.05,
        N: int = 1024,
        audit_every: int = 4,
        request_policy: LabelRequestPolicy | None = None,
        evidence=None,
        lam: float = 0.5,
        gamma: float = 50.0,
        sigma_U: float = 0.10,
        eps_noop: float = 0.15,
        cooldown_retrain: int = 800,
        cooldown_rollback: int = 400,
        a3_cooldown: int = 50,
        min_retrain_labels: int = 30,
        warmup: int | None = None,
        recent: int = 50,
        alert_spacing: int = 50,
        seed: int = 0,
        profile: str = "native_v0",
    ) -> None:
        if profile not in PROFILES:
            raise ValueError(f"profile must be one of {PROFILES}")
        self.profile = profile
        self._raw = {
            "N": N,
            "audit_every": audit_every,
            "cd_rt": cooldown_retrain,
            "cd_rb": cooldown_rollback,
        }
        self.tau, self.delta, self.N, self.audit_every = tau, delta, N, audit_every
        self.request_policy = request_policy
        self.evidence = evidence or ProxyEvidence()
        self.lam, self.gamma, self.sigma_U, self.eps_noop = lam, gamma, sigma_U, eps_noop
        self.cd_rt, self.cd_rb, self.a3_cd = cooldown_retrain, cooldown_rollback, a3_cooldown
        self.min_retrain_labels, self.warmup, self.recent = min_retrain_labels, warmup, recent
        self.alert_spacing, self.seed = alert_spacing, seed

    # ------------------------------------------------------------------ lifecycle
    def reset(self, env: EnvSpec) -> None:
        super().reset(env)
        c = env.costs
        prices = {"switch": c.c_s, "retrain": c.c_r, "rollback": c.c_b, "abstain": c.c_h}
        self.norm = max(max(prices.values()), 1e-9)
        self.price = {A2: prices["switch"], A4: prices["retrain"], A5: prices["rollback"]}
        self.price[A6], self.price[A0], self.price[A3] = prices["abstain"], 0.0, 0.0
        cap = env.budget.label_cap
        raw = self._raw
        self.N, self.audit_every = raw["N"], raw["audit_every"]
        self.cd_rt, self.cd_rb = raw["cd_rt"], raw["cd_rb"]
        if self.profile == "calibrated_v1":
            # C1: honour the stated pacing rule k_low/audit_every <= B/T (native_v0 rounds k_low UP to 1 => 5x over budget at B/T=0.05)
            self.audit_every = max(1, math.ceil(env.T / max(1, cap)))
            k_low = 1
            # C2: round-valued paper constants (L=1500) scaled to the contract horizon
            sc = env.T / PAPER_L
            self.N = max(1, round(raw["N"] * sc))
            self.cd_rt, self.cd_rb = round(raw["cd_rt"] * sc), round(raw["cd_rb"] * sc)
        else:
            k_low = max(
                1, round(cap / env.T * self.audit_every)
            )  # native pacing: k_low/audit_every = B/L
        self.policy = self.request_policy or HeuristicQueryPolicy(
            8 * k_low, 4 * k_low, k_low, 0.02, self.audit_every
        )
        self.rng = np.random.default_rng([self.seed, 0xD2A])
        self.W = self.warmup or max(20, env.T // 10)
        self.ref: tuple[float, float] | None = None  # (mean, sd) of x on warm-up rounds
        self.belief = BeliefFilter(_hand_T(), self.evidence)
        bind_env = getattr(
            self.evidence, "bind_env", None
        )  # Q1 outcome-evidence seam (opt-in; absent on ProxyEvidence)
        if bind_env is not None:
            bind_env(env)
        self.requested: set[int] = set()
        self.prev = {"U": math.inf, "risk": float("nan"), "rad": float("nan")}
        self.boost = 0
        self.last_a3 = self.last_rt = self.last_rb = self.last_alert = -(10**9)
        self.safe_m = INCUMBENT
        self.prev_gate_ok = False
        self.log: list[dict] = []

    # ------------------------------------------------------------------ sensing
    def _loss_pairs(self, state: ObservableState):
        m = state.m
        pairs = sorted((lab.label_round, v) for lab in state.H if (v := lab.loss(m)) is not None)
        return pairs

    def _sense(self, state: ObservableState, pairs) -> np.ndarray:
        t, k = state.t, self.recent
        if self.ref is None and t > self.W:
            warm = np.asarray(state.x_hist[: self.W - 1], float)
            self.ref = (float(warm.mean()), float(warm.std()) + 1e-6)
        z1 = z2 = z3 = 0.0
        if self.ref is not None:
            xs = np.append(np.asarray(state.x_hist[-(k - 1) :], float), state.x)
            n = len(xs)
            mu, sd = self.ref
            z1 = float((xs.mean() - mu) / (sd / math.sqrt(n)))
            z2 = float(math.log((xs.std() + 1e-6) / sd) * math.sqrt(n / 2.0))
        if len(pairs) >= 25:
            ref = np.array([v for _, v in pairs[:15]])
            rec = np.array([v for r, v in pairs if r > t - 2 * k])
            if len(rec) >= 10:
                se = math.sqrt(0.25 / len(rec) + 0.25 / len(ref))
                z3 = float((rec.mean() - ref.mean()) / se)
        return np.clip(np.array([z1, z2, z3]), -10.0, 10.0)

    # ------------------------------------------------------------------ decision
    def act(self, state: ObservableState):
        t, env = state.t, self.env
        pairs = self._loss_pairs(state)
        outcome_sink = getattr(
            self.evidence, "outcome_sink", None
        )  # Q1 seam: released outcomes only, opt-in
        if outcome_sink is not None:
            outcome_sink(state)
        z = self._sense(state, pairs)
        b = self.belief.update(z)
        # certificate of the model in force on released labels inside the window
        win = [v for r, v in pairs if t - self.N + 1 <= r <= t]
        n = len(win)
        if n:
            risk, radius = float(np.mean(win)), rad(n, self.delta)
        else:
            risk, radius = float("nan"), math.inf
        U = risk + radius if n else math.inf
        gate_ok = bool(n and U <= self.tau)
        if gate_ok:
            self.safe_m = state.m
        acts: list[Action] = []

        # ---- audit: how many window rounds to label (Q2 hook decides ONLY the size)
        lookback = env.clocks.max_lookback
        lo = max(1, t - min(lookback, self.N - 1))
        eligible = [s for s in range(lo, t + 1) if s not in self.requested]
        cap_left = state.b.label_remaining
        if env.budget.pending_cap is not None:
            cap_left = min(cap_left, env.budget.pending_cap - state.b.pending)
        ctx = QueryContext(
            t,
            b.copy(),
            self.prev["U"],
            self.prev["risk"],
            self.prev["rad"],
            self.tau,
            state.b.label_remaining,
            env.T,
            state.b.pending,
            t - lo + 1,
        )
        n_t = int(self.policy.request_size(ctx))
        if self.boost:
            n_t, self.boost = (
                max(n_t, self.policy.k_high if hasattr(self.policy, "k_high") else n_t),
                0,
            )
        n_t = max(0, min(n_t, cap_left, len(eligible)))
        if n_t:
            for s in self.rng.choice(np.array(eligible), size=n_t, replace=False):
                s = int(s)
                self.requested.add(s)
                acts.append(
                    Action("query", round=s)
                )  # uniform among eligible window rounds; no randomisation claim
        self.prev = {"U": U, "risk": risk, "rad": radius}

        # ---- action selection
        drift_mass = 1.0 - float(b[0])
        executed: list[str] = []
        if not gate_ok:  # U_t > tau (or no labels yet): abstain + scheduled rollback/retrain
            acts.append(Action("abstain"))
            executed.append("abstain")
            if self.prev_gate_ok and t - self.last_alert >= self.alert_spacing:
                acts.append(Action("alert"))
                self.last_alert = t
            risk_ev = bool(np.isfinite(risk) and risk > self.tau)
            if risk_ev or drift_mass > 0.5:
                if (
                    state.prev_m is not None
                    and state.prev_m == self.safe_m
                    and t - self.last_rb >= self.cd_rb
                ):
                    acts.append(Action("rollback"))
                    executed.append("rollback")
                    self.last_rb = t
                elif self._can_retrain(state):
                    acts.append(Action("retrain"))
                    executed.append("retrain")
                    self.last_rt = t
        else:
            delta_a = b @ GAIN
            feas = [A0, A6]
            if state.m == INCUMBENT and state.b.switch_cooldown_left == 0:
                feas.append(A2)
            if state.b.label_remaining > 0 and t - self.last_a3 >= self.a3_cd:
                feas.append(A3)
            if self._can_retrain(state):
                feas.append(A4)
            if (
                state.prev_m is not None
                and state.prev_m == self.safe_m
                and t - self.last_rb >= self.cd_rb
            ):
                feas.append(A5)
            util = {}
            for a in feas:
                viol = max(0.0, U - self.sigma_U * delta_a[a] - self.tau)
                util[a] = float(
                    delta_a[a] - self.lam * self.price[a] / self.norm - self.gamma * viol
                )
            best = max(feas, key=lambda a: util[a])
            if best != A0 and util[best] >= self.eps_noop:
                if best == A2:
                    acts.append(Action("switch", target=CANDIDATE))
                    executed.append("switch")
                elif best == A3:
                    self.boost, self.last_a3 = 1, t
                    executed.append("query_boost")
                elif best == A4:
                    acts.append(Action("retrain"))
                    executed.append("retrain")
                    self.last_rt = t
                elif best == A5:
                    acts.append(Action("rollback"))
                    executed.append("rollback")
                    self.last_rb = t
                elif best == A6:
                    acts.append(Action("abstain"))
                    executed.append("abstain")
        self.prev_gate_ok = gate_ok
        self.log.append(
            {"t": t, "n_cert": n, "U": U, "gate_ok": gate_ok, "belief": b.tolist(),
             "n_requested": n_t, "executed": executed}
        )  # fmt: skip
        return acts or Action("continue")

    def _can_retrain(self, state: ObservableState) -> bool:
        bud, b = self.env.budget, state.b
        return (
            b.retrain_busy_until is None
            and b.retrain_cooldown_left == 0
            and (bud.retrain_cap is None or b.retrain_used < bud.retrain_cap)
            and state.t - self.last_rt >= self.cd_rt
            and state.available_labels >= self.min_retrain_labels
        )


class _Drift2ActAdapter:
    name = "drift2act"
    vocabulary = ("query", "continue", "switch", "retrain", "alert", "rollback", "abstain")
    claimed_null = "abs_risk"
    port_status = "COMMON_CONTRACT_PORT"
    unmapped_native_actions = UNMAPPED

    def __init__(self, **kw) -> None:
        self.kw = kw

    def build(self, env: EnvSpec) -> BasePolicy:
        p = Drift2ActContractPolicy(**self.kw)
        p.reset(env)
        return p


Drift2ActAdapter = _Drift2ActAdapter()
Drift2ActCalibratedAdapter = _Drift2ActAdapter(profile="calibrated_v1")
