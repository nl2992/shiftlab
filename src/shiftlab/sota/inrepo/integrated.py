# PORTED UNCHANGED (COMMON_CONTRACT_PORT tier component) -- WP1e, d2a_rar branch.
# Source: origin/research/gave-r-2026-11-06@03289d1d (file last changed in 8fe567a7), path: src/shiftlab/gaver/integrated.py
# Only edit vs source: 'shiftlab.gaver' import paths -> 'shiftlab.sota.inrepo'. See tests/d2a_rar/test_inrepo_ports.py
# (test_port_source_identical) which re-extracts the source with git show and diffs it.
"""GAVE-R WP5: evidence x acquisition factorial on the frozen DSS shell.

``GaverMethod`` is the frozen cycle-7 DSS candidate (spec ``5b5c77b635e5``, ``ComposedMethod``)
with two independent switches:

* ``evidence``: ``"dss"`` (the spec's own started-mixture e-process), ``"gapmix"`` (WP1 exact-gap
  Markov LR, declared ``rho_bar``, 4-start restart mixture) or ``"env"`` (WP1 envelope variant).
* ``acq``: ``"dss"`` (frozen DSS acquisition incl. its delay switch, i.e. uniform when
  ``d >= 2T/(B+2)``) or ``"pave"`` (delay-gated PAVE: the WP2 governor, reserve off, active
  exactly when DSS would fall back to uniform; the straddle DSS rule otherwise).

Everything else (promotion rule, econ check, Page-CUSUM rollback, alpha spending
``alpha*2^-(j+1)`` over rollback episodes, hard budget clamp) is inherited unchanged, so the 2x2
is a clean factorial. Gap-Mix evidence receives each label's event round; gaps are irregular here
(adaptive calendar), which WP1 never exercised.

Gap-Mix restart starts in episode ``j``: ``ep_start + f*(T-ep_start)``, ``f in {0,.25,.5,.75}``
(``ep_start=0`` reproduces WP1's ``f*T``). ``ep_start`` is a past decision time, so the starts are
predictable.

Post-switch hook (for a later FreshCheck / E_rb factor): pass ``rollback_hook(method, t, released)
-> bool``. When given, it replaces the Page-CUSUM rollback test while deployed. ``None`` keeps
the baseline CUSUM. No hook is registered by default.

Nothing here claims validity beyond the components' own status (docs/gaver/10_GAPMIX_RESULTS.md);
closed-loop validity of Gap-Mix under adaptive acquisition is exactly what the WP5 null grid probes.
"""

from __future__ import annotations

import math
from collections import deque

from shiftlab.dive import atlas_components as comp
from shiftlab.dive.atlas_dependence_baselines import MarkovLREProcess
from shiftlab.sota.inrepo import gapmix as gm
from shiftlab.sota.inrepo.pave import PaveMethod, PaveParams

EVIDENCES = ("dss", "gapmix", "env", "mlr")  # mlr: post-hoc valid reference (WP5 amendment)
ACQS = ("dss", "pave")
RHO_BAR = 0.8
PAVE_TUNED = PaveParams(pending=True, deadline=True, reserve=False, kappa=0.1, q=0.03)
FRACS = (0.0, 0.25, 0.5, 0.75)


def pave_active(cfg) -> bool:
    """Delay gate: exactly the DSS delay-switch condition ``d >= 2T/(B+2)``."""
    return cfg.d >= 2 * cfg.T / (cfg.B + 2)


class GapEvidence:
    """``_Evidence``-compatible adapter feeding event rounds to a Gap-Mix restart mixture."""

    def __init__(self, method: GaverMethod, alpha: float, ep_start: int):
        cfg = method.cfg
        self.method = method
        thr = tuple(int(ep_start + f * (cfg.T - ep_start)) for f in FRACS)
        q0 = (1.0 + cfg.h) / 2.0
        mk = gm.ExactGapStart if method.evidence == "gapmix" else gm.EnvelopeStart
        self.inner = gm.RestartMixture(lambda: mk(q0, method.rho_bar), thr, alpha)
        self.xs: list[float] = []

    def update(self, x: float) -> None:
        ev = self.method._evq.popleft()
        self.xs.append(x)
        self.inner.update(ev, x)

    @property
    def proc(self):  # PAVE reads proc.log_e_value for reachability
        return self.inner

    @property
    def alarm(self) -> bool:
        return bool(self.inner.alarm)


class MLREvidence:
    """Existing Atlas Markov-LR e-process (``markov_lr_gate``'s evidence) inside the DSS shell."""

    def __init__(self, method: GaverMethod, alpha: float):
        cfg = method.cfg
        self.method = method
        self.inner = MarkovLREProcess((1.0 + cfg.h) / 2.0, alpha, cfg.B)
        self.xs: list[float] = []

    def update(self, x: float) -> None:
        self.method._evq.popleft()
        self.xs.append(x)
        self.inner.update_z(1 if x < 0 else 0)

    @property
    def proc(self):
        return self.inner

    @property
    def alarm(self) -> bool:
        return bool(self.inner.alarm)


class GaverMethod(PaveMethod):
    def __init__(
        self,
        evidence: str = "dss",
        acq: str = "dss",
        rho_bar: float = RHO_BAR,
        pave: PaveParams = PAVE_TUNED,
        rollback_hook=None,
    ):
        if evidence not in EVIDENCES or acq not in ACQS:
            raise ValueError((evidence, acq))
        super().__init__(pave)
        self.evidence, self.acq, self.rho_bar = evidence, acq, rho_bar
        self.rollback_hook = rollback_hook
        self.name = f"gaver:{evidence}:{acq}" + (":hook" if rollback_hook else "")
        self._evq: deque[int] = deque()

    def _init(self) -> None:
        comp.ComposedMethod._init(self)  # not PaveMethod._init: keep DSS delay switch
        self.reserve_n = 0
        self.pave_on = self.acq == "pave" and pave_active(self.cfg)
        if self.pave_on:  # governor owns the request rule
            self.dss_uniform = False
            self.cal = frozenset()

    def _new_episode(self, j: int, start: int) -> None:
        super()._new_episode(j, start)
        if self.evidence == "mlr":
            self.ep = MLREvidence(self, self._alpha_j(j))
        elif self.evidence != "dss":
            self.ep = GapEvidence(self, self._alpha_j(j), start)

    def _p(self, slot: str, name: str):
        if self.rollback_hook is not None and (slot, name) == ("decision", "kappa"):
            return math.inf  # CUSUM disabled; the hook owns rollback
        return super()._p(slot, name)

    def decide(self, t: int, released):
        gap_ev = self.evidence != "dss"
        self._evq = deque(
            ev for ev, _ in released if gap_ev and self.act == 0 and ev >= self.ep_start
        )
        if (
            self.rollback_hook is not None
            and self.act == 1
            and self.rollback_hook(self, t, released)
        ):
            self.cus = math.inf
        out = super().decide(t, released)
        assert not self._evq, "evidence queue not consumed"
        return out

    def _query(self, t: int) -> bool:
        if self.pave_on:
            return PaveMethod._query(self, t)
        return comp.ComposedMethod._query(self, t)


def build(name: str) -> GaverMethod:
    """``gaver:<evidence>:<acq>`` -> method (also accepts ``dss`` / ``uniform`` shorthands elsewhere)."""
    _, ev, aq = name.split(":")
    return GaverMethod(ev, aq)
