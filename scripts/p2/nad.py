"""P2 null-aware deployment (NAD): envelope-certified promotion with dependence-priced spacing.

Declared null classes (side +1 = promotion test; side -1 mirrors it for discard / rollback).
Queried disagreement outcomes z_k = 1[challenger correct] are processed in issue order; t_k is the
issue event, g_k = t_k - t_{k-1}. Query times are predictable (they use released labels, the
disagreement indicators and private randomness only), so conditioning on t_k is harmless.

* ``markov``  M(rho_bar): the event-time sign is a stationary 2-state Markov chain with
  P(s=1) = p <= 1/2 and persistence rho <= rho_bar. Then
  P(z_k=1 | F_{k-1}) = rho^g z_{k-1} + (1 - rho^g) p <= u_k := 1/2 + (rho_bar^g / 2) z_{k-1}.
* ``phi``     Phi(beta): any stationary sign process with P(s=1) <= 1/2 whose phi-mixing
  coefficient satisfies phi(g) <= beta(g) = rho_bar^g. Then
  P(z_k=1 | F_{k-1}) <= 1/2 + beta(g_k) =: u_k. This covers higher-order chains and mixing hidden
  state models with a geometric envelope; it does not cover heavy-tailed run lengths.

Evidence. For a relative edge c in (0,1), set p'_k = u_k + c (1 - u_k) and
LR_k = (p'_k/u_k)^h (1-p'_k)/(1-u_k))^(1-h), h the outcome in the tested direction. For any
conditional success probability v <= u_k, E[LR_k | F_{k-1}] = 1 + (v - u_k)(p'_k - u_k)/(u_k(1-u_k))
<= 1. A started mixture over c (QSG's construction, w_j = 1/(j(j+1))) plus 1/(k+1) is therefore a
test supermartingale under every member of the class, and Ville bounds false promotion by alpha.
The previous queried outcome z_{k-1} is tracked over the whole stream, including outcomes a test
restart discards; resetting it (as QSG-env8 does) would leave the first post-restart factor
unbounded by u_k under the class.

Acquisition (the dependence-priced spacing). While undecided, a disagreement is queried only if at
least g events have passed since the last issued query. ``gap='fixed'`` uses a constant g;
``gap='rate'`` picks g to maximise the planned information rate
I(g) / (g + 1/dis_rate), where I(g) is the expected per-label KL against the envelope under a
plug-in alternative p_a (released labels only, so predictable). Validity does not depend on g.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
FLQ = HERE.parents[0] / "failure_atlas_v2_flq"
for _p in (FLQ, HERE.parents[0] / "promising_directions/sota"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from qsg import QSG
from simulator import QueryRequest

sys.path.insert(0, str(HERE.parents[0] / "sota_sprint"))
from fam_a import _B, FamA, MarkovSUI, rho_mle

HGRID = np.array([0.0, 0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12, 0.2, 0.3])
CGRID = np.array([0.05, 0.1, 0.2, 0.3, 0.45, 0.6, 0.8])


def envelope_u(kind: str, rho_bar: float, gap: int | None, prev_hit: int | None) -> float:
    """Worst-case conditional success probability of the next outcome under the declared class."""
    if prev_hit is None or gap is None or rho_bar <= 0:
        return 0.5
    b = rho_bar ** max(int(gap), 1)
    if kind == "markov":
        return 0.5 + 0.5 * b * prev_hit
    if kind == "phi":
        return min(0.5 + b, 1.0)
    if kind == "iid":
        return 0.5
    raise ValueError(kind)


class EnvelopeStarted:
    """Started mixture over relative edges against a per-step envelope u_k."""

    def __init__(self, side: int, cgrid=CGRID):
        self.side = side
        self.c = np.asarray(cgrid, float)
        self.pi = np.full(len(self.c), 1.0 / len(self.c))
        self.S = np.zeros(len(self.c))
        self.k = 0

    def update(self, hit: int, u: float) -> float:
        self.k += 1
        w = 1.0 / (self.k * (self.k + 1))
        if u >= 1.0:  # the class allows a sure success: no admissible bet
            lr = np.ones_like(self.c)
        else:
            pp = u + self.c * (1.0 - u)
            lr = pp / u if hit else (1.0 - pp) / (1.0 - u)
        self.S = (self.S + w) * lr
        return self.value

    @property
    def value(self) -> float:
        return float(self.pi @ self.S)


def _kl(a: float, b: float) -> float:
    a = min(max(a, 1e-9), 1 - 1e-9)
    b = min(max(b, 1e-9), 1 - 1e-9)
    return a * math.log(a / b) + (1 - a) * math.log((1 - a) / (1 - b))


RV_GRID = (0.0, 0.5, 0.7, 0.8, 0.85, 0.9, 0.93, 0.95, 0.97, 0.99)


class RobustnessValue:
    """Anytime dependence-robustness value (05_VALIDITY_AUDIT P4).

    One started envelope e-process per rho_bar in RV_GRID on every queried outcome of the stream
    (one test from the first outcome, side +1, threshold 1/alpha). rv(t) = largest grid rho_bar whose
    e-process has crossed by t. Pathwise monotone in rho_bar, so P(rv ever >= rho_0) <= alpha under
    any null in the relaxed class with persistence <= rho_0.
    """

    def __init__(self, alpha, kind="markov"):
        self.alpha, self.kind = alpha, kind
        self.e = [EnvelopeStarted(+1) for _ in RV_GRID]
        self.crossed = [False] * len(RV_GRID)

    def update(self, z, gap, prev_z):
        for i, rb in enumerate(RV_GRID):
            u = envelope_u(self.kind, rb, gap, prev_z) if prev_z is not None else 0.5
            if self.e[i].update(z, u) >= 1.0 / self.alpha:
                self.crossed[i] = True

    @property
    def value(self):
        ok = [rb for rb, c in zip(RV_GRID, self.crossed) if c]
        return max(ok) if ok else -1.0


class NAD(QSG):
    def __init__(self, horizon, budget, alpha=0.05, *, rng, env="markov", rho_bar=0.8,
                 gap="fixed", g=10, g_max=80, p_floor=0.6, budget_guard=True, rho_prior=0.5, evidence="env", hurdle=False, kappa=True, cs=5.0, name="NAD",
                 **kw):  # fmt: skip
        self.env, self.rho_bar = env, rho_bar
        self.gap_mode, self.g_fixed, self.g_max = gap, g, g_max
        self.p_floor, self.budget_guard = p_floor, budget_guard
        self.rho_prior, self.rho_sig = rho_prior, 2.0
        self.evidence, self.hurdle, self.kappa, self.cs = evidence, hurdle, kappa, cs
        self.rho_hat = None
        self.rel_z: list[int] = []
        self.rel_t: list[int] = []
        self.prev = None  # (z, issue event) of the last processed outcome, whole stream
        self.rv = RobustnessValue(alpha)
        self.extra_record = {"rv_end": -1.0, "rv_at_promo": []}
        self.last_issue = -(10**9)
        self.n_rel = 0
        self.n_hit = 0
        self.n_ev = 0
        self.n_dis = 0
        super().__init__(horizon, budget, alpha, rng=rng, name=name, **kw)

    def _new_tests(self):
        def mk(side, grid=False):
            env = [EnvelopeStarted(side) for _ in (HGRID if grid else (0.0,))]
            ui = None
            if self.evidence == "mix":  # bounded-rho UI: valid on M(rho_bar), brittle outside
                ui = MarkovSUI(rho_max=self.rho_bar, **_B)
            elif self.evidence == "mixa":  # A5b's unbounded-rho UI: valid on M(any rho)
                ui = MarkovSUI(**_B)
            return {"env": env, "ui": ui, "side": side}

        if self.deployed == 0:
            self.e_up, self.e_dn = mk(+1, grid=self.hurdle), mk(-1)
        else:
            self.e_up, self.e_dn = None, mk(-1)

    def _hurdle_index(self, t: int) -> int:
        """Smallest grid hurdle h_j >= payback hurdle at release time t (0 if hurdles are off)."""
        if not self.hurdle:
            return 0
        dis = (self.n_dis + 5.0) / (self.n_ev + 20.0)
        rest = max(self.T - t, 1)
        kap = dis * self.rho_bar / (1.0 - self.rho_bar) if self.kappa else 0.0
        h = (self.cs + kap) / (2.0 * dis * rest)
        for j, hj in enumerate(HGRID):
            if hj >= h:
                return j
        return -1  # hurdle above every grid point: promotion cannot pay back

    def _upd(self, test, z: int, e: int, t: int) -> float:
        """Update a test with outcome z issued at e; return its decision e-value at release t."""
        side = test["side"]
        hit = z if side > 0 else 1 - z
        vals = []
        for j, ev in enumerate(test["env"]):
            b = 0.5 + (HGRID[j] if len(test["env"]) > 1 else 0.0)
            vals.append(ev.update(hit, self._u(side, e, b)))
        if test["ui"] is not None:
            prev = gap = None
            if self.prev is not None:
                prev = self.prev[0] if side > 0 else 1 - self.prev[0]
                gap = e - self.prev[1]
            ui = test["ui"].update(hit, gap if gap is not None else 0, prev)
            return 0.5 * vals[0] + 0.5 * ui
        if len(vals) == 1:
            return vals[0]
        j = self._hurdle_index(t)
        return 0.0 if j < 0 else vals[j]

    # ---------------------------------------------------------------- acquisition
    def _info(self, g: int, pa: float, rho: float = 0.0) -> float:
        """Planned per-label KL growth of the promotion test at gap g.

        Plug-in alternative: Markov sign with stationary success pa and persistence rho (both
        estimated from released labels only). The envelope bet is growth-optimal against the
        per-step relaxation of the class, so KL(q || u) is its exact expected log-growth.
        """
        a = rho**g
        q1 = a + (1 - a) * pa  # success prob after a favourable outcome
        q0 = (1 - a) * pa  # after an unfavourable one
        if self.env == "markov":
            u1 = envelope_u("markov", self.rho_bar, g, 1)
            return pa * (_kl(q1, u1) if q1 > u1 else 0.0) + (1 - pa) * (
                _kl(q0, 0.5) if q0 > 0.5 else 0.0
            )
        u = envelope_u(self.env, self.rho_bar, g, 1)
        return pa * (_kl(q1, u) if q1 > u else 0.0) + (1 - pa) * (_kl(q0, u) if q0 > u else 0.0)

    def _gmin(self, t: int, remaining_budget: int) -> int:
        if self.gap_mode == "none":
            return 0
        if self.gap_mode == "fixed":
            g = self.g_fixed
        elif self.gap_mode == "a5b":  # A5b's density rule: min{g : rho_hat^g <= .25}
            r = self.rho_hat
            g = (
                0
                if (r is None or r <= 0)
                else (10**9 if r >= 1 else math.ceil(math.log(0.25) / math.log(r)))
            )
        else:
            dis = (self.n_dis + 5.0) / (self.n_ev + 20.0)
            phat = (self.n_hit + 1.0) / (self.n_rel + 2.0)
            pa = max(abs(phat - 0.5) + 0.5, self.p_floor)
            rho = 0.0
            if self.gap_mode == "rate2":
                rho = self.rho_hat if self.rho_hat is not None else self.rho_prior
            # events per label cannot beat the budget-sustainable spacing
            span = max(self.T - t - 1, 1)
            g_bud = span / max(remaining_budget, 1)
            best, g = -1.0, 1
            for gg in range(1, self.g_max + 1):
                r = self._info(gg, pa, rho) / max(
                    gg + 1.0 / dis, g_bud if self.gap_mode == "rate2" else 0.0
                )
                if r > best + 1e-15:
                    best, g = r, gg
        if self.budget_guard and remaining_budget > 0:
            # never spend faster than the budget can sustain to the last informative event
            span = max(self.T - t - 1, 1)
            dis = (self.n_dis + 5.0) / (self.n_ev + 20.0)
            g = max(g, int(span / remaining_budget - 1.0 / dis))
        return g

    def request_labels(self, event, remaining_budget):
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        self.n_ev += 1
        self.n_dis += int(dis)
        if not dis or remaining_budget <= 0:
            return QueryRequest(requested=False)
        if not self.decided and self.front and remaining_budget > self.reserve:
            if event.t - self.last_issue < self._gmin(event.t, remaining_budget):
                return QueryRequest(requested=False)
            q = 1.0
        elif self.decided and not self.monitor:
            return QueryRequest(requested=False)
        take = bool(self.rng.random() < q)
        if take:
            self.last_issue = event.t
        return QueryRequest(requested=take, probability=q if take else 0.0)

    # ---------------------------------------------------------------- evidence
    def _u(self, side: int, e: int, b: float = 0.5) -> float:
        """Envelope for the null 'marginal success <= b' (b = 1/2 is the plain null)."""
        if self.prev is None:
            return b
        z0, t0 = self.prev
        prev_hit = z0 if side > 0 else 1 - z0
        u = envelope_u(self.env, self.rho_bar, e - t0, prev_hit)  # 1/2 + slack
        if self.env == "phi":  # P(z=1|past) <= p + phi(g) <= b + beta(g)
            return min(b + (u - 0.5), 1.0)
        # markov: rho^g z + (1 - rho^g) p <= b + rho_bar^g (1 - b) z for p <= b, rho <= rho_bar
        return min(b + (u - 0.5) * (1.0 - b) / 0.5, 1.0)

    def observe(self, feedback):
        for fb in sorted(feedback, key=lambda f: f.event_id):
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue
            z, e, t = int(d > 0), fb.event_id, fb.t_released
            self.rv.update(z, None if self.prev is None else e - self.prev[1],
                           None if self.prev is None else self.prev[0])  # fmt: skip
            self.extra_record["rv_end"] = self.rv.value
            self.n_rel += 1
            self.n_hit += z
            if e >= self.seg:
                if self.deployed == 0:
                    up = self._upd(self.e_up, z, e, t)
                    dn = self._upd(self.e_dn, z, e, t)
                    if up >= 2.0**self.cycle / self.alpha:
                        self.extra_record["rv_at_promo"].append(self.rv.value)
                        self.deployed, self.decided, self.seg = 1, True, t
                        self._new_tests()
                    elif dn >= 1.0 / self.alpha:
                        self.decided = True
                elif self.rollback and self._upd(self.e_dn, z, e, t) >= 1.0 / self.alpha_r:
                    self.deployed, self.decided, self.seg = 0, False, t
                    self.cycle += 1
                    self._new_tests()
            self.prev = (z, e)
            self.rel_z.append(z)
            self.rel_t.append(e)
        if self.gap_mode in ("rate2", "a5b") and len(self.rel_z) >= 9:
            self.rho_hat = rho_mle(
                np.array(self.rel_z[-150:]), np.array(self.rel_t[-150:]), sig=self.rho_sig
            )

    def decision_state(self):
        return f"dep={self.deployed};cycle={self.cycle};decided={self.decided}"


def _f(name, **kw):
    return lambda T, B, cs, cq, a, d, r: NAD(T, B, a, rng=r("QSG"), name=name, cs=cs, **kw)


EXTRA: dict = {}
for _env in ("markov", "phi"):
    for _rb in (0.8, 0.9, 0.95):
        _tag = f"{_env[0]}{round(_rb * 100)}"
        EXTRA[f"NAD-{_tag}-g0"] = _f(f"NAD-{_tag}-g0", env=_env, rho_bar=_rb, gap="none")
        EXTRA[f"NAD-{_tag}-rate"] = _f(f"NAD-{_tag}-rate", env=_env, rho_bar=_rb, gap="rate")
        EXTRA[f"NAD-{_tag}-rate2"] = _f(f"NAD-{_tag}-rate2", env=_env, rho_bar=_rb, gap="rate2")
        for _g in (5, 10, 15, 20, 40):
            EXTRA[f"NAD-{_tag}-g{_g}"] = _f(f"NAD-{_tag}-g{_g}", env=_env, rho_bar=_rb, g=_g)
EXTRA["NAD-iid-g0"] = _f("NAD-iid-g0", env="iid", rho_bar=0.0, gap="none")

# round 2 (2026-11-09): bounded-rho universal inference with spacing, envelope+UI mixture, payback


def _ui(name, rb, g=0, adaptive=False):
    def make(T, B, cs, cq, a, d, r):
        return FamA(
            T, B, a, rng=r("QSG"), name=name, evidence="sui",
            density="adaptive" if adaptive else ("fixedgap" if g else "front"),
            fixed_gap=g, rho_sig=2.0 if adaptive else 0.0, sui_kw=dict(_B, rho_max=rb),
        )  # fmt: skip

    return make


for _rb in (0.8, 0.9):
    _t = round(_rb * 100)
    for _g in (0, 5, 10):
        EXTRA[f"UI{_t}-g{_g}"] = _ui(f"UI{_t}-g{_g}", _rb, _g)
    EXTRA[f"UI{_t}-ad"] = _ui(f"UI{_t}-ad", _rb, adaptive=True)
    for _g in (5, 10):
        EXTRA[f"MIX{_t}-g{_g}"] = _f(
            f"MIX{_t}-g{_g}", env="markov", rho_bar=_rb, g=_g, evidence="mix"
        )
        EXTRA[f"PB{_t}-g{_g}"] = _f(f"PB{_t}-g{_g}", env="markov", rho_bar=_rb, g=_g, hurdle=True)
    EXTRA[f"MIX{_t}-rate2"] = _f(
        f"MIX{_t}-rate2", env="markov", rho_bar=_rb, gap="rate2", evidence="mix"
    )

# round 3: envelope + unbounded-rho UI mixture (valid on M(rho_bar) as an average of two e-processes)
for _g in (5, 10):
    EXTRA[f"MIXA80-g{_g}"] = _f(f"MIXA80-g{_g}", env="markov", rho_bar=0.8, g=_g, evidence="mixa")

# round 4: A5b's adaptive density rule
for _ev in ("env", "mixa"):
    _n = {"env": "NAD", "mixa": "MIXA"}[_ev]
    EXTRA[f"{_n}80-ad"] = _f(
        f"{_n}80-ad", env="markov", rho_bar=0.8, gap="a5b", evidence=_ev, budget_guard=False
    )


class TwoStream(FamA):
    """NAD-2S: envelope e-process on a sign-independent flagged subsequence + A5b UI on all outcomes.

    Validity (05_VALIDITY_AUDIT P5). Flagged queries are the first disagreement at least g_env
    events after the previous flagged issue, drawn from a reserved budget B_env and issued with
    probability 1. Their times depend on the disagreement process only, so under M(rho_bar) the
    flagged outcomes have P(z=1 | flagged past) <= 1/2 + rho_bar^G/2 z_prev in their own filtration.
    The envelope process ENV never restarts and may trigger only the cycle-1 promotion before any
    verdict (a coupling with a hypothetical never-closed flag stream covers the closure). The UI
    tests run at alpha/2 inside FamA (thresholds 2^c/(alpha/2)). ENV promotes at 4/alpha. Union
    bound: P(false promotion) <= alpha/2 + alpha/4 < alpha. No averaging across filtrations.
    """

    def __init__(self, T, B, alpha, *, rng, rho_bar=0.8, g_env=10, env_frac=0.6, name="NAD2S"):
        self.rho_bar_env, self.g_env = rho_bar, g_env
        self.B_env = round(env_frac * B)
        self.env_used, self.last_flag, self.env_open = 0, -(10**9), True
        self.flagged: set[int] = set()
        self.env = EnvelopeStarted(+1)
        self.env_prev = None
        self.alpha_full = alpha
        super().__init__(T, B, alpha / 2.0, rng=rng, evidence="sui", density="adaptive",
                         rho_sig=2.0, sui_kw=_B, name=name)  # fmt: skip

    def request_labels(self, event, remaining_budget):
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        if not dis or remaining_budget <= 0:
            return QueryRequest(requested=False)
        if self.env_open and self.decided:
            self.env_open = False
        if self.env_open and event.t - self.last_flag >= self.g_env and self.env_used < self.B_env:
            self.flagged.add(event.t)
            self.last_flag, self.last_issue = event.t, event.t
            self.env_used += 1
            self.n_issued += 1
            return QueryRequest(requested=True, probability=1.0)
        reserve = (self.B_env - self.env_used) if self.env_open else 0
        if remaining_budget - reserve <= 0:
            return QueryRequest(requested=False)
        if not self.decided and self.front:
            if event.t - self.last_issue < self._gmin():
                return QueryRequest(requested=False)
            q = 1.0
        elif self.decided and not self.monitor:
            return QueryRequest(requested=False)
        take = bool(self.rng.random() < q)
        if take:
            self.last_issue = event.t
            self.n_issued += 1
        return QueryRequest(requested=take, probability=q if take else 0.0)

    def observe(self, feedback):
        for fb in sorted(feedback, key=lambda f: f.event_id):
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d != 0 and fb.event_id in self.flagged:
                z, e = int(d > 0), fb.event_id
                u = 0.5
                if self.env_prev is not None:
                    u = envelope_u(
                        "markov", self.rho_bar_env, e - self.env_prev[1], self.env_prev[0]
                    )
                v = self.env.update(z, u)
                self.env_prev = (z, e)
                if (self.env_open and self.deployed == 0 and self.cycle == 1 and not self.decided
                        and v >= 4.0 / self.alpha_full):  # fmt: skip
                    self.deployed, self.decided, self.seg = 1, True, fb.t_released
                    self.env_open = False
                    self._new_tests()
            super().observe([fb])


def _2s(name, **kw):
    return lambda T, B, cs, cq, a, d, r: TwoStream(T, B, a, rng=r("QSG"), name=name, **kw)


for _g in (10, 15):
    for _fr in (0.4, 0.6):
        EXTRA[f"NAD2S-g{_g}-f{round(_fr * 10)}"] = _2s(
            f"NAD2S-g{_g}-f{round(_fr * 10)}", g_env=_g, env_frac=_fr
        )
