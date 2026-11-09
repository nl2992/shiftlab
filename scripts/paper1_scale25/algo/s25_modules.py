# ruff: noqa
"""Workstream-B modules for the compositor (scripts/paper1_eqsdp/search60/compositor.py).

Label-matched acquisition controls (ablation, brief section 10). They sit on the frozen parent
(EQSDp or Wald + cutoff H=1100: same evidence, same switching rule, same cutoff); the parent's own
acquisition is switched off (``scale`` -> 0) and replaced:

  UNI  uniform calendar: ``n_target`` slots spread evenly over the open (pre-cutoff) period; the
       first disagreement event at or after each slot is bought.
  UNC  uncertainty (entropy) sampling: buy a disagreement event with probability
       min(1, c * H(mu)), H = binary entropy of the parent's posterior mean of
       P(challenger correct | disagreement).  c is calibrated per dataset so that the mean
       label count equals the label count of the matched arm (EQ+pair).

Both see only ctx (t, parent evidence on released labels, remaining budget).
"""

from __future__ import annotations

import math
import s25_common  # noqa: F401  (sys.path)
from compositor import Force, Module, register


@register
class UNI(Module):
    ID = "UNI"
    FAMILY = "F"
    DEFAULTS = {"n_target": 55.0}
    SETTINGS = [{"n_target": 55.0}, {"n_target": 55.0}]

    def __init__(self, *a):
        super().__init__(*a)
        self.bought = 0
        n = max(1, int(round(self.params["n_target"])))
        end = self.ctx.t_close if self.ctx.t_close else self.ctx.T - self.ctx.delay
        self.slots = [(j + 0.5) * end / n for j in range(n)]

    def scale(self, ctx):
        return 0.0

    def floor(self, ctx):
        if ctx.closed or not ctx.releasable:
            return None
        due = sum(1 for s in self.slots if s <= ctx.t)
        return Force("force", 1.0, "UNI") if due > self.bought else None

    def on_purchase(self, ctx, rec):
        if self.ID in rec["by"]:
            self.bought += 1


@register
class UNC(Module):
    ID = "UNC"
    FAMILY = "F"
    DEFAULTS = {"c": 0.3}
    SETTINGS = [{"c": 0.3}, {"c": 0.3}]

    def scale(self, ctx):
        return 0.0

    def floor(self, ctx):
        if ctx.closed or not ctx.releasable:
            return None
        mu = (ctx.k + 1.0) / (ctx.n + 2.0)
        mu = min(max(mu, 1e-9), 1 - 1e-9)
        h = -(mu * math.log2(mu) + (1 - mu) * math.log2(1 - mu))
        q = min(1.0, self.params["c"] * h)
        return Force("force", q, "UNC") if self.rng.random() < q else None


import s25_v2  # noqa: E402,F401  (register the v2 candidate modules)
