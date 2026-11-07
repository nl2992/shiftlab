"""Family D (SOTA sprint): transferable deploy-or-abstain safety architecture over fast selectors.

One module, ``DeployGate``, wraps an independently developed ranking host (Model Picker, CAMS,
Model Selector ports in ``scripts/promising_directions/sota/competitors``). The host keeps its own
query rule, its own randomness and its own learning; the gate decides *deployment*:

* the incumbent (model 0) stays deployed ("abstain") until an anytime sequential certificate
  rejects the promotion null AND the host currently ranks the challenger first;
* optionally the gate adds its own queries (front-loads disagreements while undecided, only when
  the host prefers the challenger by default), keeps a rollback reserve and runs a mirrored
  rollback test after promotion.

Evidence and validity (stated precisely, not claimed beyond this):

* Evidence is query-conditional: ``z_k = 1[challenger correct]`` on the k-th *queried*
  disagreement in request order (release order equals request order because delay is constant).
  No importance weights are used by the certificate.
* Every query decision is predictable: the host's Bernoulli(u_t) uses the host's private generator
  and u_t is a function of the host posterior (built from labels released strictly before t) and of
  the current event's *predictions*; the gate's own decision is a function of the host's current
  ranking, the gate's own past evidence and the remaining budget. None reads the label of event t.
  A rule that depends on a posterior that depends on past labels is still predictable.
* Under the conditional promotion null ``H+: P(z_t = 1 | F_{t-}, event t queried and a
  disagreement) <= 1/2`` for every t ("challenger never better on a disagreement, given the
  query-time information"), each started-mixture factor has conditional mean <= 1, so Ville's
  inequality bounds the probability that the promotion test *ever* crosses 2^j/alpha in cycle j.
  Requiring host agreement in addition only removes promotions. Summed over cycles this gives
  false promotion <= alpha under H+. In the synthetic regimes the host's query rule is symmetric
  in the two disagreement orientations, so query-conditional and marginal p coincide.
* This does NOT cover Markov-persistent signs (F5 rho>0): there P(z=1 | past) > 1/2 after a
  favourable outcome even when the stationary p = 1/2, so the plain mixture's null is violated.
  D5 swaps in a gap-aware dependence envelope certificate for that case (valid only under the
  declared persistence bound rho_bar).

The certificate is pluggable: any object with ``update(z, event_t) -> e-value`` (see ``_Cert``).
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOTA = ROOT / "scripts/promising_directions/sota"
for _p in (SOTA, SOTA / "competitors", ROOT / "scripts/failure_atlas_v2_flq"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from cams import CAMSDeploymentAdapter, stack_advice
from controls import PacedDisagreementAcquisition
from model_picker import ModelPickerDeploymentAdapter
from model_selector import ModelSelectorCausalAdapter
from qsg import EnvelopeMixture, StartedMixture
from simulator import QueryRequest, ReleasedFeedback


# ------------------------------------------------------------------------------------------------
# Pluggable certificates: update(z, event_t) -> current e-value for one side.
# ------------------------------------------------------------------------------------------------
class _Cert:
    """Started mixture (QSG) e-process; ``side=+1`` tests H+: p<=1/2, ``-1`` tests H-: p>=1/2."""

    def __init__(self, side: int):
        self.m = StartedMixture(side)

    def update(self, z: int, event_t: int, last=None) -> float:
        return self.m.update(z)


class _EnvCert:
    """Gap-aware Markov-envelope started mixture (qsg.EnvelopeMixture, declared rho_bar)."""

    def __init__(self, side: int, rho_bar: float = 0.8):
        self.m = EnvelopeMixture(side, rho_bar)

    def update(self, z: int, event_t: int, last=None) -> float:
        return self.m.update_at(z, event_t)


class _A1Cert:
    """Family A's A1 evidence (fam_a.MarkovSUI: gap-aware Markov sequential universal inference,
    no declared rho bound). ``last`` is the immediately preceding queried outcome of the WHOLE
    stream (z, issue event), which the Markov null conditions on even for a test started later."""

    def __init__(self, side: int, sui_cls, **kw):
        self.side, self.m = side, sui_cls(**kw)

    def update(self, z: int, event_t: int, last=None) -> float:
        hit = z if self.side > 0 else 1 - z
        prev, gap = None, 0
        if last is not None:
            prev = last[0] if self.side > 0 else 1 - last[0]
            gap = event_t - last[1]
        return self.m.update(hit, gap, prev)


def started_mixture(side):
    return _Cert(side)


def envelope(rho_bar):
    return lambda side: _EnvCert(side, rho_bar)


def _a1_or_standin(rho_bar=0.8):
    """Use Family A's A1 evidence (fam_a.MarkovSUI) if importable; else the envelope stand-in.

    Returns (factory, label). The label is recorded in the ledger.
    """
    try:
        import fam_a

        sui = fam_a.MarkovSUI
        return (lambda side: _A1Cert(side, sui)), "fam_a.MarkovSUI (A1 evidence, default kwargs)"
    except Exception:  # pragma: no cover - fam_a absent or broken: stand-in  # noqa: BLE001, S110
        pass
    return envelope(rho_bar), f"A1 stand-in: qsg.EnvelopeMixture(rho_bar={rho_bar})"


# ------------------------------------------------------------------------------------------------
# Host adapters: the only per-host shim is how a gate-acquired label is handed to the host.
# ------------------------------------------------------------------------------------------------
def _host_extra(host, event) -> dict:
    """Issue-time extras the host's update needs for a label it did not draw itself."""
    if isinstance(host, CAMSDeploymentAdapter):
        return {"E": host.core._prepare(event)["e"].copy()}
    return {}


def _host_u(host, event, hreq) -> float:
    """The host's own issue-time query probability u_t for this event (whether or not it drew).

    Model Picker reports u_t on every disagreement; CAMS reports it only when drawn, so it is
    recomputed without a draw (no generator use); Model Selector's record gate is deterministic.
    """
    if hreq.requested:
        return float(hreq.probability)
    if isinstance(host, ModelPickerDeploymentAdapter):
        return float(hreq.probability)
    if isinstance(host, CAMSDeploymentAdapter):
        return float(host.core.decide(event, draw=False)[0])
    return 0.0


def make_host(kind: str, r):
    """Hosts use the SAME private generator names as the native registry entries, so a gated
    host replays the native host's randomness exactly until gate-acquired labels change it."""
    if kind == "mp":
        return ModelPickerDeploymentAdapter(2, 2, r("model_picker"))
    if kind == "cams":
        return CAMSDeploymentAdapter(
            n_models=2, n_classes=2, advice_fn=stack_advice(2, []), rng=r("cams")
        )
    if kind == "ms":
        return ModelSelectorCausalAdapter(2, 2, r("model_selector"))
    raise ValueError(kind)


# ------------------------------------------------------------------------------------------------
# The shared deploy-or-abstain wrapper (D1, D2, D4, D5, D6).
# ------------------------------------------------------------------------------------------------
class DeployGate:
    """Host ranks and queries; an anytime certificate gates promotion of the challenger.

    Parameters
    ----------
    acq : "host_pref" (default) the gate front-loads every disagreement (q=1) while undecided and
          the host ranks the challenger first; "always" front-loads while undecided regardless of
          the host (QSG-like); "host_only" adds no queries (pure veto on the host's own labels).
    and_host : promotion also requires the host to rank the challenger first.
    rollback : after promotion a mirrored test (H-: p>=1/2 on outcomes issued after promotion)
               at level alpha_r rolls back; the next promotion cycle runs at alpha/2^cycle.
    reserve : fraction of the budget withheld from all pre-promotion queries (host and gate),
              usable only after promotion for the rollback test.
    share : gate-acquired labels are also given to the host (with the combined frozen issue-time
            propensity u + (1-u) q_gate, so the host's IPW stays unbiased).
    stop_when_final : once promoted with no rollback, deployment is absorbing, so all queries stop.
    """

    def __init__(
        self,
        host,
        T,
        B,
        alpha,
        *,
        rng,
        cert=started_mixture,
        acq="host_pref",
        and_host=True,
        rollback=False,
        reserve=0.0,
        alpha_r=0.05,
        share=True,
        stop_when_final=True,
        monitor=True,
        name="DeployGate",
    ):
        self.host, self.name = host, name
        self.T, self.B, self.alpha, self.alpha_r = T, B, alpha, alpha_r
        self.rng, self.cert, self.acq = rng, cert, acq
        self.and_host, self.rollback, self.share = and_host, rollback, share
        self.stop_when_final, self.monitor = stop_when_final, monitor
        self.reserve = round(reserve * B)
        self.pacer = PacedDisagreementAcquisition(T, B)
        self.deployed, self.cycle, self.decided, self.cert_ok = 0, 1, False, False
        self.seg = 0
        self.host_pref = 0
        self.n_promotions = 0
        self.last = None  # last queried disagreement outcome of the stream: (z, issue event)
        self._req: dict[int, tuple[bool, float, float]] = {}  # t -> (host drew, u_host, q_comb)
        self._new_tests()

    def _new_tests(self):
        if self.deployed == 0:
            self.e_up, self.e_dn = self.cert(+1), self.cert(-1)
        else:
            self.e_up, self.e_dn = None, self.cert(-1)
        self.cert_ok = False

    # -- deployment ---------------------------------------------------------------------------
    def predict(self, event):
        self.host_pref = int(self.host.predict(event))
        if self.deployed == 0 and self.cert_ok and (self.host_pref == 1 or not self.and_host):
            self.deployed, self.decided, self.seg = 1, True, event.t
            self.n_promotions += 1
            self._new_tests()
        return self.deployed

    # -- acquisition --------------------------------------------------------------------------
    def request_labels(self, event, remaining_budget):
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q_pace = self.pacer.propensity(event.t, remaining_budget, dis)
        self.pacer.note_event(dis)
        final = self.deployed == 1 and not self.rollback and self.stop_when_final
        hreq = self.host.request_labels(event, remaining_budget)  # host keeps its own draw
        if final or not dis or remaining_budget <= 0:
            return QueryRequest(requested=False)
        pre = self.deployed == 0
        if pre and remaining_budget <= self.reserve:
            return QueryRequest(requested=False)  # reserve is for post-promotion monitoring only
        u = _host_u(self.host, event, hreq)
        if (
            pre
            and not self.decided
            and (self.acq == "always" or (self.acq == "host_pref" and self.host_pref == 1))
        ):
            q_g = 1.0
        elif self.deployed == 1 and self.rollback and self.monitor:
            q_g = q_pace  # paced rollback monitoring from the remaining (reserved) budget
        else:
            q_g = 0.0
        take = bool(hreq.requested) or (q_g > 0 and bool(self.rng.random() < q_g))
        if not take:
            return QueryRequest(requested=False)
        # issue-time propensity of the union of two independent draws, frozen here
        q_comb = u + (1.0 - u) * q_g
        extra = dict(hreq.extra) if hreq.requested else _host_extra(self.host, event)
        self._req[event.t] = (bool(hreq.requested), u, q_comb)
        return QueryRequest(requested=True, probability=q_comb, extra=extra)

    # -- feedback ------------------------------------------------------------------------------
    def observe(self, feedback):
        fbs = sorted(feedback, key=lambda f: f.event_id)
        host_fb = []
        for fb in fbs:
            drew, u, q_comb = self._req.pop(
                fb.event_id, (True, fb.query_probability, fb.query_probability)
            )
            if self.share or drew:
                p = q_comb if self.share else u
                host_fb.append(
                    ReleasedFeedback(
                        fb.event_id,
                        fb.t_requested,
                        fb.t_released,
                        fb.label,
                        fb.model_losses,
                        float(p),
                        fb.extra,
                    )
                )
        if host_fb:
            self.host.observe(host_fb)
        for fb in fbs:
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue
            z, last = int(d > 0), self.last
            self.last = (z, fb.event_id)
            if fb.event_id < self.seg:
                continue
            if self.deployed == 0:
                up = self.e_up.update(z, fb.event_id, last)
                dn = self.e_dn.update(z, fb.event_id, last)
                if up >= 2.0**self.cycle / self.alpha:
                    # latched: Ville bounds the event "ever crossed"; stop front-loading and
                    # wait for the host to rank the challenger first
                    self.cert_ok, self.decided = True, True
                elif dn >= 1.0 / self.alpha and not self.cert_ok:
                    self.decided = True  # discard: stop gate front-loading, host continues
            elif self.rollback:
                if self.e_dn.update(z, fb.event_id, last) >= 1.0 / self.alpha_r:
                    self.deployed, self.decided, self.seg = 0, False, fb.t_released
                    self.cycle += 1
                    self._new_tests()

    def decision_state(self):
        return (
            f"dep={self.deployed};cycle={self.cycle};cert={int(self.cert_ok)};pref={self.host_pref}"
        )

    def state_dict(self):
        return {}

    def load_state_dict(self, s):
        pass


# ------------------------------------------------------------------------------------------------
# D3: Model Selector + post-decision monitoring.
# ------------------------------------------------------------------------------------------------
class SelectThenMonitor:
    """Model Selector picks once, then a sequential monitor replaces the model on evidence.

    Phase 1: the Model Selector causal adapter runs natively (its own paced record-gate queries
    and labeled-accuracy rule, deploying what it selects) until ``n_select`` labels have been
    released; its choice is then frozen (the published method is a one-shot selection).
    Phase 2: the remaining budget is paced over disagreements; a started-mixture test of
    "the deployed model is never worse on a disagreement" runs on outcomes issued after the
    selection. Rejection replaces the model. A replacement *to the challenger* is a promotion and
    uses threshold 2^cycle/alpha; a replacement back to the incumbent uses 1/alpha_r.
    The initial selection is uncertified (that is the host's behaviour); ``gate_initial=True``
    holds the incumbent at selection time unless the phase-1 evidence certifies the challenger.
    """

    def __init__(
        self,
        T,
        B,
        alpha,
        *,
        r,
        rng,
        n_select=100,
        alpha_r=0.05,
        cert=started_mixture,
        gate_initial=False,
        name="D3",
    ):
        self.host = make_host("ms", r)
        self.name, self.T, self.B, self.alpha, self.alpha_r = name, T, B, alpha, alpha_r
        self.rng, self.cert, self.n_select, self.gate_initial = rng, cert, n_select, gate_initial
        self.pacer = PacedDisagreementAcquisition(T, B)
        self.phase, self.deployed, self.cycle, self.seg, self.n_obs = 1, 0, 1, 0, 0
        self.pre_up = cert(+1)  # phase-1 evidence (for gate_initial only)
        self.pre_ok = False
        self.mon = None

    def predict(self, event):
        if self.phase == 1:
            self.deployed = int(self.host.predict(event))
            if self.gate_initial and not self.pre_ok:
                self.deployed = 0
        return self.deployed

    def request_labels(self, event, remaining_budget):
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.pacer.propensity(event.t, remaining_budget, dis)
        self.pacer.note_event(dis)
        if self.phase == 1:
            return self.host.request_labels(event, remaining_budget)
        if not dis or remaining_budget <= 0:
            return QueryRequest(requested=False)
        take = bool(self.rng.random() < q)
        return QueryRequest(requested=take, probability=q if take else 0.0)

    def _start_monitor(self, t):
        self.phase, self.seg = 2, t
        # test "deployed never worse": deployed=0 -> H+ (z favours challenger), deployed=1 -> H-
        self.mon = self.cert(+1 if self.deployed == 0 else -1)

    def observe(self, feedback):
        for fb in sorted(feedback, key=lambda f: f.event_id):
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if self.phase == 1:
                self.host.observe([fb])
                self.n_obs += 1
                if d != 0 and self.gate_initial and not self.pre_ok:  # noqa: SIM102
                    if self.pre_up.update(int(d > 0), fb.event_id) >= 2.0 / self.alpha:
                        self.pre_ok = True
                if self.n_obs >= self.n_select:
                    c0, c1 = self.host.correct
                    pref = 1 if c1 > c0 else 0 if c0 > c1 else self.deployed
                    if self.gate_initial and not self.pre_ok:
                        pref = 0
                        self.cycle = 2  # phase-1 test spent alpha/2; next promotion test alpha/4
                    self.deployed = pref
                    self._start_monitor(fb.t_released)
                continue
            if d == 0 or fb.event_id < self.seg:
                continue
            e = self.mon.update(int(d > 0), fb.event_id)
            thr = (2.0**self.cycle / self.alpha) if self.deployed == 0 else 1.0 / self.alpha_r
            if e >= thr:
                self.deployed = 1 - self.deployed
                if self.deployed == 0:
                    self.cycle += 1
                self._start_monitor(fb.t_released)

    def decision_state(self):
        return f"phase={self.phase};dep={self.deployed}"

    def state_dict(self):
        return {}

    def load_state_dict(self, s):
        pass


# ------------------------------------------------------------------------------------------------
# Registry entries.
# ------------------------------------------------------------------------------------------------
# D6 frozen parameter set (one module, one setting, every host). Fixed a priori, not tuned.
D6_PARAMS = {
    "cert": started_mixture,
    "acq": "host_pref",
    "and_host": True,
    "rollback": True,
    "reserve": 0.25,
    "alpha_r": 0.05,
    "share": True,
}
A1_FACTORY, A1_SOURCE = _a1_or_standin(0.8)


def _gate(kind, name, **kw):
    def f(T, B, cs, cq, a, d, r):
        return DeployGate(make_host(kind, r), T, B, a, rng=r("D_gate"), name=name, **kw)

    return f


EXTRA = {
    # D1: Model Picker + anytime deploy gate (no rollback; promotion absorbing)
    "D1": _gate("mp", "D1"),
    "D1-host_only": _gate("mp", "D1-host_only", acq="host_only"),
    "D1-always": _gate("mp", "D1-always", acq="always"),
    "D1-no_and": _gate("mp", "D1-no_and", and_host=False),
    "D1-no_share": _gate("mp", "D1-no_share", share=False),
    # D2: CAMS (constant policies, the only information the loss-only stream supports) + gate
    "D2": _gate("cams", "D2"),
    # NeurIPS 2024 Appendix G.7 ablation: native stochastic CAMS-MAX recommendation core
    # under the same context-free constant-policy advice as cams_adapter. Prediction deployment,
    # hard cap, delayed feedback and switching costs remain benchmark adapters.
    "cams_max_adapter": lambda T, B, cs, cq, a, d, r: CAMSDeploymentAdapter(
        n_models=2,
        n_classes=2,
        advice_fn=stack_advice(2, []),
        rng=r("cams"),
        variant="CAMS-MAX",
        name="cams_max_adapter",
    ),
    "D2-host_only": _gate("cams", "D2-host_only", acq="host_only"),
    # D3: Model Selector + post-decision monitoring
    "D3": lambda T, B, cs, cq, a, d, r: SelectThenMonitor(T, B, a, r=r, rng=r("D_gate"), name="D3"),
    "D3-gated": lambda T, B, cs, cq, a, d, r: SelectThenMonitor(
        T, B, a, r=r, rng=r("D_gate"), gate_initial=True, name="D3-gated"
    ),
    # D4: D1 + rollback reserve + rollback rule
    "D4": _gate("mp", "D4", rollback=True, reserve=0.25),
    "D4-no_reserve": _gate("mp", "D4-no_reserve", rollback=True, reserve=0.0),
    "D4-r10": _gate("mp", "D4-r10", rollback=True, reserve=0.10),
    # D5: D2 + gap-aware dependence-corrected certificate (A1, or the declared stand-in)
    "D5": _gate("cams", "D5", cert=A1_FACTORY),
    "D5-standin_env8": _gate("cams", "D5-standin_env8", cert=envelope(0.8)),
    # D6: the shared wrapper, same module and parameters on three independent hosts
    "D6:mp": _gate("mp", "D6:mp", **D6_PARAMS),
    "D6:cams": _gate("cams", "D6:cams", **D6_PARAMS),
    "D6:ms": _gate("ms", "D6:ms", **D6_PARAMS),
    # post-screen addition (2026-11-03, after screen1): D1's default parameter set on the Model
    # Selector host, to complete the D1-params transfer row (D2 is already D1-params on CAMS)
    "D6-D1params:ms": _gate("ms", "D6-D1params:ms"),
}
