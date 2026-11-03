"""Strongest-reading re-ports of gated deployment and DISCERN (review response, 2026-11-03).

The discovery ports fixed the importance-weight range at the declared worst case ``1/p_min = 20``.
The independent review (docs/failure_atlas_v2_flq/results/review_discovery_algorithm.md) pointed out that the
issue-time propensity ``q_t`` is predictable, so a tighter per-step range is legitimate:

* ``GatedAdaptiveRange``: MOPE (Karampatziakis et al., Alg. 2) with the bet set ``C`` of Section 4.4
  evaluated at ``wmax_t = 1/q_t`` for a disagreement record and ``wmax_t = 2`` for an agreement
  (where ``w = 1`` exactly). The bet is recomputed from the past sufficient statistics immediately
  before each increment is ingested, so it is predictable; every realised ``w <= wmax_t`` keeps the
  Lemma 1 condition ``x >= -1/2`` and wealth positive.
* ``DiscernDesignFloor``: DISCERN-style with a declared design floor ``pi_min = .25`` (``c = 4``)
  shared by its pacer, instead of ``.05``. A per-step ``c_t`` would change the [0,1] mapping of the
  mean step by step and is not covered by the PrPl-EB theorem, so the design floor is the
  strongest reading we can defend.

Front-loaded variants (q = 1 while undecided) are the attachable repair on these stronger hosts.
"""

from __future__ import annotations

from qce import DiscernFrontOnly, GatedDeploymentStop, DiscernStyleStop  # noqa: F401


class GatedAdaptiveRange(GatedDeploymentStop):
    def __init__(self, horizon, budget, alpha, *, rng, p_min=0.05, front=False,
                 name="gated_adaptive_range"):  # fmt: skip
        super().__init__(horizon, budget, alpha, rng=rng, p_min=p_min, name=name)
        self._wmax: dict[int, float] = {}
        self.front = front
        if front:
            base = self.acq.propensity
            self.acq.propensity = lambda t, rem, dis, _b=base: (
                1.0 if (dis and rem > 0) else _b(t, rem, dis))

    def request_labels(self, event, remaining_budget):
        req = super().request_labels(event, remaining_budget)
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        if dis and req.probability > 0:
            self._wmax[event.t] = max(1.0 / req.probability, 2.0)
        else:
            self._wmax[event.t] = 2.0  # agreement: w = 1 exactly
        return req

    def _ingest(self, w, d, event_ref):
        wm = self._wmax.pop(event_ref, 1.0 / self.p_min)
        for side in (self.cs.plus, self.cs.minus):
            side.wmax = wm
            side._bet()  # bet over C(wmax_t) from past statistics only
        super()._ingest(w, d, event_ref)


class DiscernDesignFloor(DiscernStyleStop):
    def __init__(self, horizon, budget, alpha, eps=0.0, *, rng, front=False,
                 name="discern_design_floor"):  # fmt: skip
        super().__init__(horizon, budget, alpha, eps, rng=rng, p_min=0.25, name=name)
        if front:
            base = self.acq.propensity
            self.acq.propensity = lambda t, rem, dis, _b=base: (
                1.0 if (dis and rem > 0) else _b(t, rem, dis))


EXTRA = {
    "gated_adaptive_range": lambda T, B, cs, cq, a, d, r: GatedAdaptiveRange(
        T, B, a, rng=r("gated_deployment")),
    "gated_adaptive_range+front": lambda T, B, cs, cq, a, d, r: GatedAdaptiveRange(
        T, B, a, rng=r("gated_deployment"), front=True, name="gated_adaptive_range+front"),
    "discern_design_floor": lambda T, B, cs, cq, a, d, r: DiscernDesignFloor(
        T, B, a, rng=r("discern_style")),
    "discern_design_floor+front": lambda T, B, cs, cq, a, d, r: DiscernDesignFloor(
        T, B, a, rng=r("discern_style"), front=True, name="discern_design_floor+front"),
}
