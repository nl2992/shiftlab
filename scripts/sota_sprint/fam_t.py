"""Sprint 2 Family T: transfer of evidence mechanisms to published hosts (candidates T1-T6).

One PLUGGABLE evidence interface (fam_d's ``cert(side)``: an object with
``update(z, event_t, last) -> e-value``) is attached to five published hosts:

* fast selectors (Model Picker, CAMS, Model Selector) through ``TGate`` (fam_d.DeployGate plus an
  optional A5b-style adaptive-density rule on the gate's own front-loaded queries);
* certificate stops (Gated Deployment / MOPE off-policy CS in its strong adaptive-range re-port, and
  corrected DISCERN PrPl-EB with design floor) through ``_DepMixin``, which feeds the host's queried
  disagreements, in event order, to the evidence module and either REPLACES the host's verdict rule
  or AUGMENTS it (promotion needs host CS AND module; discard if either discards).

Evidence modules (``EVIDENCE``) and the null each one tests (Track V, ``EVIDENCE_NULL``)
------------------------------------------------------------------------------------------
``qsg``    QSG StartedMixture on query-conditional outcomes: V1 (conditional advantage <= 0 on
           every queried disagreement, given the query-time past).
``a5b``    fam_a.MarkovSUI with fam_a._B (A5b's evidence): V2 (stationary first-order Markov sign
           process, p <= 1/2, ANY rho; gap-aware).
``env8``   qsg.EnvelopeMixture(rho_bar=.8): Markov null with a DECLARED persistence bound
           rho <= .8 (a sub-class of V2; reported as "V2(rho<=.8)"). Invalid at rho=.95 by design.
``cmean``  ``CondMeanEB`` (below; Family T's own, because fam_r.py did not exist when this module
           was written): predictable-plug-in empirical-Bernstein e-process on query-conditional
           ``W = z`` in [0,1] for the lambda-weighted RUNNING AVERAGE of conditional means
           (Choe & Ramdas 2024 / Waudby-Smith & Ramdas 2024 Thm 2 with time-varying conditional
           means). It tests the composite null ``sum_i lam_i (m_i - 1/2) <= 0`` with
           ``m_i = P(z_i = 1 | F_{i-1})``; this CONTAINS the pointwise V1 null, so it is V1-valid,
           and additionally valid when the challenger is better on some stretches and worse on
           others as long as the lambda-weighted average is <= 0 ("V1-avg"). It is NOT valid under
           Markov persistence (rho > 0 makes m_i > 1/2 after a favourable outcome).
``cmean_s`` the started version (mixture over start indices, w_j = 1/(j(j+1))): V1.
``fam_r:*`` any evidence factory fam_r exposes as ``fam_r.EVIDENCE`` (looked up lazily).

On +-1 outcomes a betting e-process prod(1 + lam x) and QSG's Bernoulli LR mixture are the same
family (sprint-1 fact); ``cmean`` differs from ``qsg`` only by plug-in vs mixture bets, the
empirical-Bernstein variance penalty and the time-averaged target. Expect small differences.

Every query decision is predictable (no label of the current event is read); validity of a
module's verdict is exactly the validity of that module under its stated null; host agreement or
an AND with a second certificate only removes promotions. Common-contract ADAPTATIONS are marked
``ADAPTATION`` below.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (
    ROOT / "scripts/failure_atlas_v2_flq",
    ROOT / "scripts/promising_directions/sota",
    ROOT / "scripts/promising_directions/sota/competitors",
    HERE,
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import fam_a
import fam_c
import fam_d
from fam_d import DeployGate, _host_extra, _host_u, make_host
from simulator import QueryRequest
from strong_hosts import DiscernDesignFloor, GatedAdaptiveRange


# =============================================================================== evidence
class CondMeanEB:
    """One-sided predictable-plug-in empirical-Bernstein e-process (see module docstring).

    ``side=+1`` tests H+: lambda-weighted average of P(z=1|past) <= 1/2 using W = z;
    ``side=-1`` the mirror with W = 1 - z. log E_k = sum lam_i (W_i - 1/2) - sum v_i psi(lam_i),
    v_i = 4 (W_i - mu_{i-1})^2, psi(l) = (-log(1-l) - l)/4 (WSR eq. 14). Bet (predictable):
    lam_k = clip((mu_{k-1} - 1/2) / max(s2_{k-1}, .05), 0, lam_max): the growth-optimal plug-in for
    the EB lower bound, with prior pseudo-counts ``n0`` at mu = 1/2 (s2 prior 1/4).
    ``started=True``: E_k = sum_j w_j E_{j,k} over all start indices j (w_j = 1/(j(j+1))); each
    component keeps its own plug-ins from j. Ville applies to E_k + sum_{j>k} w_j.
    """

    def __init__(
        self, side: int = 1, *, started: bool = False, n0: float = 4.0, lam_max: float = 0.75
    ):
        self.side, self.started, self.n0, self.lam_max = side, started, n0, lam_max
        # per-start state columns: [log_e, sum_w, sum_sq, n]
        self.st = np.zeros((0, 4))
        self.k = 0
        self.value = 0.0 if started else 1.0

    def update(self, z: int, event_t: int = 0, last=None) -> float:
        w = float(z if self.side > 0 else 1 - z)
        self.k += 1
        if self.started or self.k == 1:
            self.st = np.vstack([self.st, np.zeros(4)])
        s = self.st
        n = s[:, 3]
        mu = (0.5 * self.n0 + s[:, 1]) / (self.n0 + n)
        s2 = (0.25 * self.n0 + s[:, 2]) / (self.n0 + n)
        lam = np.clip((mu - 0.5) / np.maximum(s2, 0.05), 0.0, self.lam_max)
        psi = (-np.log1p(-lam) - lam) / 4.0
        s[:, 0] += lam * (w - 0.5) - 4.0 * (w - mu) ** 2 * psi
        s[:, 1] += w
        s[:, 3] += 1.0
        mu_new = (0.5 * self.n0 + s[:, 1]) / (self.n0 + s[:, 3])
        s[:, 2] += (w - mu_new) ** 2
        if self.started:
            j = np.arange(1, len(s) + 1)
            self.value = float(np.sum(np.exp(np.minimum(s[:, 0], 700.0)) / (j * (j + 1.0))))
        else:
            self.value = float(math.exp(min(s[0, 0], 700.0)))
        return self.value


def _cmean(side):
    return CondMeanEB(side)


def _cmean_s(side):
    return CondMeanEB(side, started=True)


def _a5b(side):
    return fam_d._A1Cert(side, fam_a.MarkovSUI, **fam_a._B)


EVIDENCE = {
    "qsg": fam_d.started_mixture,
    "a5b": _a5b,
    "env8": fam_d.envelope(0.8),
    "env95": fam_d.envelope(0.95),
    "cmean": _cmean,
    "cmean_s": _cmean_s,
}
EVIDENCE_NULL = {
    "qsg": "V1",
    "a5b": "V2",
    "env8": "V2(rho<=.8 declared)",
    "env95": "V2(rho<=.95 declared)",
    "cmean": "V1-avg (contains V1)",
    "cmean_s": "V1",
}


def fam_r_evidence() -> dict:
    """Evidence factories exposed by fam_r (``fam_r.EVIDENCE: {name: cert(side)}``), if any."""
    try:
        import fam_r

        return {f"fam_r:{k}": v for k, v in getattr(fam_r, "EVIDENCE", {}).items()}
    except ImportError:
        return {}


def get_evidence(name: str):
    if name in EVIDENCE:
        return EVIDENCE[name]
    ext = fam_r_evidence()
    if name in ext:
        return ext[name]
    raise KeyError(name)


# =============================================================================== fast-selector hosts
class TGate(DeployGate):
    """fam_d.DeployGate with a pluggable evidence module and optional adaptive evidence density.

    ``density="adaptive"``: the gate's OWN front-loaded queries (q_g = 1) are issued only if the
    event gap since the last issued disagreement query (host or gate) is >= g* = ceil(log c / log rho_hat), rho_hat the
    shrunk (sig = 2 nats) gap-indexed Markov MLE from released outcomes (fam_a.rho_mle, A5b's rule).
    Predictable: reads only released labels and issue times. Host queries are untouched.
    """

    def __init__(
        self,
        host,
        T,
        B,
        alpha,
        *,
        rng,
        density="front",
        c_corr=0.25,
        min_pairs=8,
        rho_sig=2.0,
        single_cycle=False,
        **kw,
    ):
        self.density, self.c_corr, self.min_pairs, self.rho_sig = (
            density,
            c_corr,
            min_pairs,
            rho_sig,
        )
        self.rel_z: list[int] = []
        self.rel_t: list[int] = []
        self.rho_hat = None
        self.last_gate_issue = -(10**9)
        self.n_gap_skips = 0
        super().__init__(host, T, B, alpha, rng=rng, **kw)
        # Family H's threshold correction: with no rollback, promotion is absorbing, so only one
        # promotion cycle can run and threshold 2^0/alpha = 1/alpha suffices (Ville, level alpha).
        # cycle only increments on rollback, so cycle = 0 gives 1/alpha exactly.
        if single_cycle and not self.rollback:
            self.cycle = 0

    def _gmin(self):
        if self.density != "adaptive" or self.rho_hat is None or self.rho_hat <= 0:
            return 0
        if self.rho_hat >= 1:
            return 10**9
        return math.ceil(math.log(self.c_corr) / math.log(self.rho_hat))

    def request_labels(self, event, remaining_budget):
        # identical to DeployGate.request_labels except for the gap rule on the gate's own draw
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q_pace = self.pacer.propensity(event.t, remaining_budget, dis)
        self.pacer.note_event(dis)
        final = self.deployed == 1 and not self.rollback and self.stop_when_final
        hreq = self.host.request_labels(event, remaining_budget)
        if final or not dis or remaining_budget <= 0:
            return QueryRequest(requested=False)
        pre = self.deployed == 0
        if pre and remaining_budget <= self.reserve:
            return QueryRequest(requested=False)
        u = _host_u(self.host, event, hreq)
        if (
            pre
            and not self.decided
            and (self.acq == "always" or (self.acq == "host_pref" and self.host_pref == 1))
        ):
            q_g = 1.0
            if event.t - self.last_gate_issue < self._gmin():
                q_g = 0.0
                self.n_gap_skips += 1
        elif self.deployed == 1 and self.rollback and self.monitor:
            q_g = q_pace
        else:
            q_g = 0.0
        gate_draw = q_g > 0 and bool(self.rng.random() < q_g)
        take = bool(hreq.requested) or gate_draw
        if not take:
            return QueryRequest(requested=False)
        self.last_gate_issue = event.t  # any issued disagreement query (A5b: gap since last issue)
        q_comb = u + (1.0 - u) * q_g
        extra = dict(hreq.extra) if hreq.requested else _host_extra(self.host, event)
        self._req[event.t] = (bool(hreq.requested), u, q_comb)
        return QueryRequest(requested=True, probability=q_comb, extra=extra)

    def observe(self, feedback):
        for fb in sorted(feedback, key=lambda f: f.event_id):
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d != 0:
                self.rel_z.append(int(d > 0))
                self.rel_t.append(fb.event_id)
        super().observe(feedback)
        if self.density == "adaptive" and len(self.rel_z) >= self.min_pairs + 1:
            self.rho_hat = fam_a.rho_mle(
                np.array(self.rel_z[-150:]), np.array(self.rel_t[-150:]), sig=self.rho_sig
            )


def _tg(kind, name, ev="qsg", **kw):
    def f(T, B, cs, cq, a, d, r):
        return TGate(
            make_host(kind, r), T, B, a, rng=r("D_gate"), name=name, cert=get_evidence(ev), **kw
        )

    return f


# =============================================================================== certificate hosts
class _DepMixin:
    """Dependence-aware evidence on a _CertificateStop host (Gated / DISCERN).

    The host's ordered, delay-safe increment stream is kept; every RESOLVED, QUERIED disagreement
    (w > 0, d != 0) is passed, in event order, to the evidence pair (up = promotion test, dn =
    discard test). The host CS keeps running (its bounds also drive fam_c controllers).
    mode "replace": deploy iff up >= 1/alpha; discard iff dn >= 1/alpha.
    mode "and":     deploy iff host CS deploys AND up >= 1/alpha; discard iff host discards OR
                    dn >= 1/alpha. Valid under the union of the host's null and the module's null.
    ADAPTATION: the host is one-shot (a verdict stops acquisition for good), as in the published
    ports, so a single promotion test at level alpha is used (no rollback cycles).
    """

    def _dep_init(self, ev, mode):
        self.dep_up, self.dep_dn = ev(+1), ev(-1)
        self.dep_mode = mode
        self.dep_last = None
        self.dep_vals = (0.0, 0.0)
        self.dep_n = 0

    def _ingest(self, w, d, event_ref):
        super()._ingest(w, d, event_ref)
        if d != 0 and w > 0:
            z = int(d > 0)
            up = self.dep_up.update(z, event_ref, self.dep_last)
            dn = self.dep_dn.update(z, event_ref, self.dep_last)
            self.dep_last = (z, event_ref)
            self.dep_vals = (up, dn)
            self.dep_n += 1

    def _check(self):
        base = super()._check()
        dep_v, dis_v = self.deploy_verdicts[0], self._discard_verdict
        up_ok = self.dep_vals[0] >= 1.0 / self.alpha
        dn_ok = self.dep_vals[1] >= 1.0 / self.alpha
        if self.dep_mode == "replace":
            return dep_v if up_ok else (dis_v if dn_ok else "")
        if base == dis_v or dn_ok:
            return dis_v
        return dep_v if (base == dep_v and up_ok) else ""


class GatedDep(_DepMixin, GatedAdaptiveRange):
    _discard_verdict = "discard"

    def __init__(self, T, B, alpha, *, rng, ev, mode="replace", front=False, name):
        GatedAdaptiveRange.__init__(self, T, B, alpha, rng=rng, front=front, name=name)
        self._dep_init(ev, mode)


class DiscernDep(_DepMixin, DiscernDesignFloor):
    _discard_verdict = "regression"

    def __init__(self, T, B, alpha, *, rng, ev, mode="replace", front=False, name):
        DiscernDesignFloor.__init__(self, T, B, alpha, rng=rng, front=front, name=name)
        self._dep_init(ev, mode)


class GatedCDep(_DepMixin, fam_c.GatedC):
    """T6: fam_c acquisition controller (C2 shadow price / C6) x evidence module on the gated host.
    The controller's value projection still reads the host MOPE CS (declared: the controller is
    used exactly as published in fam_c; only the verdict evidence changes)."""

    _discard_verdict = "discard"

    def __init__(self, T, B, alpha, cs, cq, delay, ctl, *, rng, ev, mode="replace", name):
        fam_c.GatedC.__init__(self, T, B, alpha, cs, cq, delay, ctl, rng=rng, name=name)
        self._dep_init(ev, mode)


def _gd(name, ev, mode="replace", front=False):
    return lambda T, B, cs, cq, a, d, r: GatedDep(
        T, B, a, rng=r("gated_deployment"), ev=get_evidence(ev), mode=mode, front=front, name=name
    )


def _dd(name, ev, mode="replace", front=False):
    return lambda T, B, cs, cq, a, d, r: DiscernDep(
        T, B, a, rng=r("discern_style"), ev=get_evidence(ev), mode=mode, front=front, name=name
    )


_C2 = {"base": "front", "shadow": True, "gamma": fam_c._gam, "zeta": fam_c._zet}
_C6 = dict(fam_c._c6)


def _gc(name, ev, ctl_kw, mode="replace"):
    return lambda T, B, cs, cq, a, d, r: GatedCDep(
        T,
        B,
        a,
        cs,
        cq,
        d,
        fam_c.Controller(**ctl_kw),
        rng=r("gated_deployment"),
        ev=get_evidence(ev),
        mode=mode,
        name=name,
    )


# =============================================================================== registry
EXTRA: dict = {}
# T1 (Model Picker), T4 (CAMS), T5 (shared wrapper incl. Model Selector): host x evidence x density
for _h in ("mp", "cams", "ms"):
    for _e in ("qsg", "a5b", "env8", "cmean"):
        EXTRA[f"T:{_h}/{_e}"] = _tg(_h, f"T:{_h}/{_e}", _e)
    EXTRA[f"T:{_h}/a5b+ad"] = _tg(_h, f"T:{_h}/a5b+ad", "a5b", density="adaptive")
    EXTRA[f"T:{_h}/qsg+ad"] = _tg(_h, f"T:{_h}/qsg+ad", "qsg", density="adaptive")
EXTRA["T:cams/env95"] = _tg("cams", "T:cams/env95", "env95")
EXTRA["T:cams/cmean_s"] = _tg("cams", "T:cams/cmean_s", "cmean_s")
EXTRA["T:cams/a5b-host_only"] = _tg("cams", "T:cams/a5b-host_only", "a5b", acq="host_only")
EXTRA["T:mp/a5b+ad+rb"] = _tg(
    "mp", "T:mp/a5b+ad+rb", "a5b", density="adaptive", rollback=True, reserve=0.10, alpha_r=0.05
)
# Family H threshold correction (1/alpha when promotion is absorbing) on every fast-selector host
for _h in ("mp", "cams", "ms"):
    for _e in ("qsg", "a5b"):
        EXTRA[f"T:{_h}/{_e}1"] = _tg(_h, f"T:{_h}/{_e}1", _e, single_cycle=True)


def _hg(kind, name, **kw):
    """fam_h.HGate (H2 = SUI + 1/alpha + A5b spacing; H4 = H2 + dual clock; H3 = H2 + C2 shadow
    price) on another published host. ADAPTATION: fam_h was built on CAMS; the same gate is
    wrapped around Model Picker / Model Selector with their native generator names."""

    def f(T, B, cs, cq, a, d, r):
        import fam_h

        return fam_h.HGate(
            make_host(kind, r), T, B, a, rng=r("D_gate"), delay=d, cs=cs, cq=cq, name=name, **kw
        )

    return f


_H2 = {"evidence": "sui", "single_cycle": True, "spacing": True}
for _h in ("mp", "ms"):
    EXTRA[f"T:{_h}/H2"] = _hg(_h, f"T:{_h}/H2", **_H2)
    EXTRA[f"T:{_h}/H4"] = _hg(_h, f"T:{_h}/H4", **_H2, dualclock=True)
# T6 on CAMS (fam_h host): evidence {iid, sui} x acquisition {front, spacing, C2 shadow}; the
# fam_h registry supplies H1-iid1, H2-iid_space, H1, H2, H3; this is the missing (iid, shadow) cell
EXTRA["T6:iidxshadow"] = _hg(
    "cams", "T6:iidxshadow", evidence="iid", single_cycle=True, spacing=True, shadow=True
)
EXTRA["T6:iidxshadow_nospace"] = _hg(
    "cams", "T6:iidxshadow_nospace", evidence="iid", single_cycle=True, shadow=True
)

# T2 (Gated Deployment, strong adaptive-range re-port) and T3 (corrected DISCERN, design floor)
for _e in ("a5b", "env8"):
    for _m, _tag in (("replace", "/"), ("and", "AND/")):
        for _fr in (False, True):
            _s = "+front" if _fr else ""
            EXTRA[f"T2:gated{_tag}{_e}{_s}"] = _gd(f"T2:gated{_tag}{_e}{_s}", _e, _m, _fr)
            EXTRA[f"T3:discern{_tag}{_e}{_s}"] = _dd(f"T3:discern{_tag}{_e}{_s}", _e, _m, _fr)
EXTRA["T2:gated/qsg+front"] = _gd("T2:gated/qsg+front", "qsg", "replace", True)  # mechanism check
# T6: evidence {MOPE (host), module} x acquisition {front, C2 / C6} on the gated host
for _e in ("a5b", "env8", "qsg"):
    EXTRA[f"T6:{_e}xC2"] = _gc(f"T6:{_e}xC2", _e, _C2)
    EXTRA[f"T6:{_e}xC6"] = _gc(f"T6:{_e}xC6", _e, _C6)

# Track V: the null each candidate's verdict actually tests (host CS null in "and" mode: V1 IPW
# all-event conditional mean for gated / DISCERN; union with the module's null)
NULL_TESTED = {}
for _k in EXTRA:
    _e = next((e for e in ("cmean_s", "cmean", "env95", "env8", "a5b", "qsg") if e in _k), None)
    _n = EVIDENCE_NULL[_e] if _e else ("V1" if "iid" in _k else "V2")
    NULL_TESTED[_k] = f"union(V1-host-CS, {_n})" if "AND/" in _k else _n


# =============================================================================== analysis CLI
def host_of(name: str) -> list[str]:
    """Declared hosts / sprint-1 variants each candidate is compared with (first = native host)."""
    if name.startswith("T:mp/"):
        return ["model_picker_adapter", "D1", "D6:mp"]
    if name.startswith("T:cams/"):
        return ["cams_adapter", "D2", "D5"]
    if name.startswith("T:ms/"):
        return ["model_selector_causal", "D6-D1params:ms", "D6:ms"]
    if name.startswith("T2:"):
        return (
            ["gated_adaptive_range+front"] if name.endswith("+front") else ["gated_adaptive_range"]
        ) + ["gated_deployment"]
    if name.startswith("T3:"):
        return (
            ["discern_design_floor+front"] if name.endswith("+front") else ["discern_design_floor"]
        ) + ["discern_style"]
    if name.startswith("T6:"):
        return ["C2" if name.endswith("C2") else "C6", "gated_adaptive_range+front"]
    return []


def summarise(dirs, nulls=None, alts=None, extra_regimes=()):
    """Null promotion (RISK_NULLS), alternative mean J (RISK_ALTS) and paired contrasts."""
    import pandas as pd
    from bench import CERTIFIED_PUBLISHED, UNCERTIFIED_PUBLISHED
    from bench2 import RISK_ALTS, RISK_NULLS

    nulls, alts = nulls or RISK_NULLS, alts or RISK_ALTS
    df = pd.concat([pd.read_json(Path(d) / "records.jsonl", lines=True) for d in dirs])
    pols = sorted(df.policy.unique())
    prom = df[df.regime.isin(nulls)].pivot_table(
        index="policy", columns="regime", values="ever_promote", aggfunc="mean"
    )
    piv = df.pivot_table(index=["regime", "ep", "seed"], columns="policy", values="net")
    alt = piv.loc[piv.index.get_level_values(0).isin(alts)]
    alt_seed = alt.groupby(level=["seed", "ep"]).mean()  # per-seed mean over alternatives
    cert = [
        p for p in CERTIFIED_PUBLISHED + ["choe_ramdas_eb", "choe_ramdas_eb+front"] if p in pols
    ]
    unc = [p for p in UNCERTIFIED_PUBLISHED if p in pols]
    best_cert = alt_seed[cert].mean().idxmin() if cert else None
    best_unc = alt_seed[unc].mean().idxmin() if unc else None

    def pd_(a, b, frame):
        d = (frame[a] - frame[b]).dropna().to_numpy()
        se = d.std(ddof=1) / np.sqrt(len(d))
        return {
            "vs": b,
            "mean": round(float(d.mean()), 2),
            "lo": round(float(d.mean() - 1.96 * se), 2),
            "hi": round(float(d.mean() + 1.96 * se), 2),
            "n": len(d),
        }

    out = {"best_certified_alt": best_cert, "best_uncertified_alt": best_unc, "policies": {}}
    for p in pols:
        rec = {
            "null_promotion": {k: round(float(v), 3) for k, v in prom.loc[p].items()}
            if p in prom.index
            else {},
            "alt_J": round(float(alt_seed[p].mean()), 2),
            "per_regime_J": {r: round(float(g[p].mean()), 2) for r, g in piv.groupby(level=0)},
            "contrasts_alt": {},
        }
        for h in host_of(p) + [best_cert, best_unc]:
            if h and h in alt_seed and h != p:
                rec["contrasts_alt"][h] = pd_(p, h, alt_seed)
        out["policies"][p] = rec
    return out


def _md(s, cands):
    from bench2 import RISK_NULLS

    L = [
        (
            f"best certified (alt mean): {s['best_certified_alt']}; best uncertified: "
            f"{s['best_uncertified_alt']}"
        ),
        "",
        "| policy | null V | " + " | ".join(RISK_NULLS) + " | alt J | vs host | vs best cert |",
        "|---|---|" + "---|" * len(RISK_NULLS) + "---|---|---|",
    ]
    for p in cands:
        if p not in s["policies"]:
            continue
        r = s["policies"][p]
        np_ = [f"{r['null_promotion'].get(k, float('nan')):.3f}" for k in RISK_NULLS]
        hs = host_of(p)
        c = r["contrasts_alt"]

        def f(k, c=c):
            x = c.get(k)
            return "" if not x else f"{x['mean']:+.1f} [{x['lo']:+.1f},{x['hi']:+.1f}] ({k})"

        L.append(
            f"| {p} | {NULL_TESTED.get(p, '')} | "
            + " | ".join(np_)
            + f" | {r['alt_J']:.1f} | {f(hs[0]) if hs else ''} | {f(s['best_certified_alt'])} |"
        )
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Family T screen summary")
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    s = summarise(a.dirs)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(s, indent=1) + "\n")
    md = _md(s, sorted(s["policies"]))
    Path(a.out).with_suffix(".md").write_text(md)
    print(md)
