"""SOTA sprint family B: nonstationary detection and recovery on top of Gated+RMM.

Host: ``rmm:gated_deployment+RMM`` (RestartMixtureMonitor around GatedDeploymentStop, base at
alpha/2, label-clock restart-mixture SR e-detector at alpha/2, continued paced acquisition).
``RecoveryMonitor`` subclasses the host and adds four switchable mechanisms:

* reserve (B1): before the first deployment decision (a promotion, by detector or base, or the
  base's own "discard" verdict) the base and the monitor pacer see ``remaining - ceil(rho B)``;
  the held ``rho B`` labels are released only after that decision, for monitoring.
* rollback (B2): after a promotion the rollback detector is a restart-mixture SR e-detector at
  ``alpha_rb = .10`` whose start grid covers the budget actually left at promotion (less prior
  dilution than the host's grid over all of B), with a horizon gate: no rollback when fewer than
  ``h_min = ceil(c_s / g_ref)`` events remain (it cannot repay its switch cost). After a rollback
  the base is restarted at ``alpha_base / 2^k`` and the promotion detector at ``alpha_det / 2^j``.
* multiscale (B3): the detector is a weighted mixture of three restart grids (one start at the
  first label; starts every 25 labels; starts every 5 labels) over a wider bet grid.
* deadline (B4): no label is bought (by base or monitor) whose release ``t + delay`` falls after
  ``T - h_min``; the monitor pacer spreads the remaining budget over the window that is still
  useful, and skips a label when even all outstanding plus all still-purchasable labels at the
  maximal bet could not push the detector over its threshold before the deadline.

Error accounting (iid conditional null: on queried disagreements the challenger is correct with
probability <= 1/2, independently of the past and of the predictable query rule).
* First promotion: base CS at alpha/2 plus detector at alpha/2 (Ville on the mixture), so
  P(any promotion) <= alpha. Reserve and deadline only change predictable propensities or stop
  querying, and the detector uses unweighted label-clock outcomes, so this is unchanged.
* After a promotion: a rollback is an alarm of a detector at level alpha_rb against the null
  "the deployed challenger is not worse"; a false rollback is a COST (two switches plus time on the
  incumbent), not a safety error, and we report its empirical rate. Re-promotions after a
  rollback spend (alpha_det + alpha_base)/2^k, so under a global null after the rollback the
  k-th re-promotion has probability <= alpha/2^k. NOT controlled: time on a model that became
  worse (detection delay), anything under serial dependence (rho > 0), the host's own rollback
  at alpha (B0/B1/B3/B4 keep the host's rollback detector at alpha=.05 over a grid on B).
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def _load_rmm():
    name = "atlas_v2_restart_monitor"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "scripts/failure_atlas_v2/restart_monitor.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    saved = list(sys.path)
    try:
        spec.loader.exec_module(mod)
    finally:  # RMM's directory has regimes.py/suite.py that would shadow the FLQ modules
        sys.path[:] = saved
    return mod


_rmm = _load_rmm()
RestartMixtureMonitor = _rmm.RestartMixtureMonitor
HorizonWeightedPacer = _rmm.HorizonWeightedPacer

from certificate_stops import GatedDeploymentStop
from simulator import Event, QueryRequest

HOST_LAMBDAS = (0.15, 0.3, 0.5)
WIDE_LAMBDAS = (0.1, 0.2, 0.35, 0.5, 0.7)
G_REF = 0.1  # registered upper reference for |G_t| per event (dis .2 * |2p-1| <= .1 in the atlas)


class GridMixtureDetector:
    """Weighted mixture of restart-grid SR e-detectors; total prior mass one.

    ``components`` = [(weight, gap, n_starts)]: component c opens a product with prior mass
    weight_c / n_starts_c before every gap_c-th label (the first n_starts_c of them). Each product
    is a nonnegative supermartingale under the conditional null E[X | past] <= 0 for any bet in
    [0, 1), so stat + (mass of starts not yet opened) is a nonnegative supermartingale started at
    one, and Ville gives P(sup stat >= 1/alpha) <= alpha. With one component (1, 10, ceil(B/10))
    and the host bets this is exactly the host's MixtureSRDetector.
    """

    def __init__(self, alpha: float, components, lambdas=HOST_LAMBDAS):
        self.alpha = float(alpha)
        tot = sum(w for w, _, _ in components)
        self.comps = [(w / tot, int(g), max(1, int(n))) for w, g, n in components]
        self.lams = np.asarray(lambdas, float)
        self.sr = np.zeros((len(self.comps), len(self.lams)))
        self.n = 0

    def update(self, x: int) -> bool:
        for i, (w, g, ns) in enumerate(self.comps):
            if self.n % g == 0 and self.n // g < ns:
                self.sr[i] += w / ns
        self.sr *= 1.0 + self.lams * x
        self.n += 1
        return self.stat >= 1.0 / self.alpha

    @property
    def stat(self) -> float:
        return float(self.sr.mean(axis=1).sum())

    def max_reachable(self, k: int) -> float:
        """Upper bound on stat after k more labels (every bet wins, every unopened start opens)."""
        if k <= 0:
            return self.stat
        unopened = sum(w * (ns - min(ns, -(-self.n // g))) / ns for w, g, ns in self.comps)
        grow = (1.0 + self.lams) ** k
        return float(((self.sr.sum(axis=0) + unopened) * grow).mean())


def host_detector(alpha, max_labels, gap=10):
    return GridMixtureDetector(alpha, [(1.0, gap, math.ceil(max_labels / gap))], HOST_LAMBDAS)


def multiscale_detector(alpha, max_labels):
    return GridMixtureDetector(
        alpha,
        [
            (0.3, max_labels + 1, 1),
            (0.35, 25, math.ceil(max_labels / 25)),
            (0.35, 5, math.ceil(max_labels / 5)),
        ],
        WIDE_LAMBDAS,
    )


class DeadlinePacer(HorizonWeightedPacer):
    """Uniform pacer over [t, t_dead): no spend after the deadline, all budget usable before it."""

    def __init__(self, horizon, budget, t_dead, p_min=0.05, k=1.0):
        super().__init__(horizon, budget, p_min=p_min, k=k)
        self.t_dead = int(t_dead)

    def propensity(self, t, remaining, disagree):
        if not disagree or remaining <= 0 or t >= self.t_dead:
            return 0.0
        rate = (self.n_disagree + self.prior_rate * self.prior_w) / (t + self.prior_w)
        expected_left = max(rate * (self.t_dead - t), 1e-9)
        return float(min(max(self.k * remaining / expected_left, self.p_min), 1.0))


class RecoveryMonitor(RestartMixtureMonitor):
    def __init__(
        self,
        make_base,
        horizon,
        budget,
        alpha,
        *,
        rng,
        name="",
        delay=100,
        cs=5.0,
        reserve=0.0,
        rollback=False,
        multiscale=False,
        deadline=False,
        alpha_rb_new=0.10,
        g_ref=G_REF,
    ):
        self.reserve_n = math.ceil(reserve * budget)
        self.rollback_on, self.multiscale, self.deadline = (
            bool(rollback),
            bool(multiscale),
            bool(deadline),
        )
        self.alpha_rb_new = float(alpha_rb_new)
        self.h_min = math.ceil(cs / g_ref)
        self.delay = int(delay)
        self.decided = False
        self.n_rollbacks = 0
        self.n_vetoed = 0
        self.n_skipped_potential = 0
        self._remaining_hint = int(budget)
        super().__init__(make_base, horizon, budget, alpha, rng=rng, name=name)
        self.t_dead = self.T - self.delay - self.h_min
        if self.deadline:
            self.acq = DeadlinePacer(horizon, budget, self.t_dead, p_min=0.05)

    # -- detectors
    def _new_detector(self):
        if self.deployed == 0:
            a = self.alpha_det / (2.0**self.n_promotions)
            m = self.B
        else:
            a = self.alpha_rb_new if self.rollback_on else self.alpha_rb
            m = max(int(self._remaining_hint), 20) if self.rollback_on else self.B
        return multiscale_detector(a, m) if self.multiscale else host_detector(a, m, self.gap)

    # -- budget view
    def _effective(self, t, remaining):
        eff = remaining
        if self.reserve_n and not self.decided:
            eff = max(0, remaining - self.reserve_n)
        if self.deadline and t >= self.t_dead:
            eff = 0
        return eff

    def _mark_decided(self):
        if not self.decided and (
            self.deployed == 1 or self.n_alarms > 0 or getattr(self.base, "stopped", False)
        ):
            self.decided = True

    # -- Policy protocol
    def predict(self, event: Event) -> int:
        self.t = event.t
        k = self.view.model(int(self.base.predict(self.view.event(event))))
        if k != self.deployed:  # the base switched under its own CS
            if self.rollback_on:  # B2 alpha accounting counts base switches too (host does not)
                if k == 1:
                    self.n_promotions += 1
                else:
                    self.n_rollbacks += 1
            self.deployed = k
            self.det = self._new_detector()
            self.order, self.queue = [], {}
        self._mark_decided()
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        self.remaining = remaining_budget
        self._remaining_hint = remaining_budget
        eff = self._effective(event.t, remaining_budget)
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        req = self.base.request_labels(self.view.event(event), eff)
        q_own = self.acq.propensity(event.t, eff, dis)
        self.acq.note_event(dis)
        if req.requested:
            self.base_owned.add(event.t)
            if dis:
                self.order.append(event.t)
            return req
        if self.keep and dis and q_own > 0.0:
            if self.deadline:  # can the detector still alarm before the deadline at all?
                rate = max(self.acq.n_disagree / max(event.t + 1, 1), 1e-3)
                k = len(self.order) + 1 + int(min(eff, rate * max(self.t_dead - event.t, 0)))
                if self.det.max_reachable(k) < 1.0 / self.det.alpha:
                    self.n_skipped_potential += 1
                    return QueryRequest(requested=False)
            if self.rng.random() < q_own:
                self.own.add(event.t)
                self.order.append(event.t)
                return QueryRequest(requested=True, probability=q_own)
        return QueryRequest(requested=False)

    def _switch(self) -> None:
        new = 1 - self.deployed
        if new == 0 and self.rollback_on and self.T - (self.t + 1) < self.h_min:
            self.n_vetoed += 1  # too late to repay c_s: keep the challenger, stop testing
            self.det = GridMixtureDetector(1e-12, [(1.0, 1, 1)])
            self.order, self.queue = [], {}
            return
        self.n_alarms += 1
        if new == 1:
            self.n_promotions += 1
        else:
            self.n_rollbacks += 1
        self.deployed = new
        h = max(self.T - (self.t + 1), 1)
        self.view = _rmm._View(self.t + 1, h, swap=(new == 1))
        a_base = self.alpha_base
        if new == 0 and self.rollback_on:  # re-promotion spends a halving share
            a_base = self.alpha_base / (2.0**self.n_rollbacks)
        self.base = self.make_base(h, max(self.remaining, 0), a_base, self.rng)
        self.base_owned = set()
        self.det = self._new_detector()
        self.order, self.queue = [], {}
        self.decided = True

    def decision_state(self) -> str:
        return f"dep={self.deployed};alarms={self.n_alarms};rb={self.n_rollbacks}"


def _gated(T, B, a, r):
    return GatedDeploymentStop(T, B, a, rng=r)


def _make(**kw):
    def f(T, B, cs, cq, alpha, delay, r):
        return RecoveryMonitor(
            _gated, T, B, alpha, rng=r("gated_deployment"), delay=delay, cs=cs, **kw
        )

    return f


RES = 0.15  # reserve level used inside the composites, fixed before any screen
EXTRA = {
    "B0_host": _make(),  # reimplementation check: must equal rmm:gated_deployment+RMM
    "B1_r10": _make(reserve=0.10),
    "B1_r15": _make(reserve=0.15),
    "B1_r25": _make(reserve=0.25),
    "B2": _make(rollback=True),
    "B3": _make(multiscale=True),
    "B4": _make(deadline=True),
    "B5": _make(reserve=RES, rollback=True, deadline=True),
    "B6": _make(reserve=RES, rollback=True, multiscale=True, deadline=True),
    # mechanism ablations of B5 (each removes one component)
    "B5-reserve": _make(rollback=True, deadline=True),
    "B5-rollback": _make(reserve=RES, deadline=True),
    "B5-deadline": _make(reserve=RES, rollback=True),
}


# --------------------------------------------------------------------------- path diagnostics
def diagnose(regimes, policies, seeds=20, seed_base=None, out=None):
    """Replay screen.py's paired streams and classify every switch against the evaluator truth.

    correct_rollback: a 1->0 switch while G_t < 0; false_rollback: a 1->0 switch while G_t >= 0;
    reversal_delay: events from the first sign change of G from + to - until the first 1->0 switch
    after it (only when the policy was on model 1 at that change). Evaluator-side only.
    """
    import json

    import screen
    from bench import CONTRACT, DEV_SEED_BASE, parse_regime
    from registry import EXTRA as REG
    from simulator import run_episode
    from suite import build_suite, stream_from_losses

    seed_base = DEV_SEED_BASE if seed_base is None else seed_base
    rows = []
    for name in regimes:
        R, b = parse_regime(name)
        budget = b or CONTRACT["budget"]
        gain = R.truth_gain()
        neg = np.flatnonzero((gain[1:] < 0) & (gain[:-1] > 0)) + 1
        for s in range(seeds):
            losses = R.sample(
                np.random.default_rng(np.random.SeedSequence([seed_base, screen._h(R.name), s]))
            )
            for pol in build_suite(
                losses.shape[0],
                budget,
                CONTRACT["cs"],
                CONTRACT["cq"],
                CONTRACT["alpha"],
                R.delay,
                s,
                seed_base + screen._h(name) % 1000,
                names=policies,
                extra=REG,
            ):
                preds, labels = stream_from_losses(
                    losses, np.random.default_rng([seed_base, screen._h(name), 0, s, 7])
                )
                res = run_episode(
                    pol,
                    model_predictions=preds,
                    labels=labels,
                    delay=R.delay,
                    budget=budget,
                    label_price=CONTRACT["cq"],
                    switch_cost=CONTRACT["cs"],
                    trace=True,
                )
                dep = np.array([r["deployed_model"] for r in res.records])
                tr = np.diff(np.r_[0, dep])
                down = np.flatnonzero(tr == -1)
                delays = []
                for c in neg:
                    if dep[c - 1] == 1:
                        after = down[down >= c]
                        delays.append(int(after[0] - c) if len(after) else int(len(dep) - c))
                rows.append(
                    {
                        "regime": name,
                        "seed": s,
                        "policy": pol.name,
                        "net": res.net_cost,
                        "correct_rollbacks": int((gain[down] < 0).sum()),
                        "false_rollbacks": int((gain[down] >= 0).sum()),
                        "on1_at_reversal": len(delays),
                        "reversal_delay_mean": float(np.mean(delays)) if delays else None,
                    }
                )
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in rows)
    return rows


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="family-B path diagnostics")
    ap.add_argument("--regimes", required=True)
    ap.add_argument("--policies", required=True)
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    for p in (ROOT / "scripts/failure_atlas_v2_flq", HERE):
        sys.path.insert(0, str(p))
    diagnose(a.regimes.split(","), a.policies.split(","), a.seeds, out=a.out)
    print("wrote", a.out)
