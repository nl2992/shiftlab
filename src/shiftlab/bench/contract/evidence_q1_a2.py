"""Amendment A2 Q1 evidence: ``restart_min_certificate`` (A2-Q1-R1). NEW module; ``evidence_q1.py`` is untouched.

Mechanism (docs/d2a_rar/drafts/A2_DRAFT.md section 1.4, registered in AUTORESEARCH_PROGRAM.md section 3b):

    log e = min( log sum_j w_j E_cond^(j) , log sum_j w_j E_marg^(j) )

Each component is a restart (onset) mixture over per-start exact-gap processes with ONE shared, fixed start-time prior:
starts at accepted-label indices ``s_j = 2^j - 1`` (0, 1, 3, 7, 15, ...) that are ``< B`` (label cap) and weights
``w_j proportional to 1/((j+1)(j+2))`` normalised to sum 1 (so the prior is summable and fixed before data).

Filtration G_i (in-order identified released outcomes, gaps, selection records). Validity (argument, unit-tested for the
weight property, NOT a proof): each mixture of per-start e-processes with a probability prior is a nonnegative
supermartingale under its own null whenever each per-start process is; the minimum is dominated by each component, so it
inherits H0cond-or-H0marg validity exactly as ``MinCore`` does. Min is taken OUTSIDE the mixtures. An unweighted
Shiryaev-Roberts sum would give only an ARL bound; summable weights are what make the time-uniform bound hold.
Stopping: any. Parameter uncertainty: inherited from the per-start process (certified supremum / predictable bets).
Target null: ``cond`` (also valid under ``marg`` within the declared class); scored on ``cond`` validity cells.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

import numpy as np

from . import evidence_q1 as q1
from .evidence_q1 import COMMON_FILT, SEL_REQ, Ctx, GapEvidence, MinCore, Q1Spec, StartMixture

FAMILY, VARIANT = "conditional_marginal_objective_selection", "restart_min_certificate"


def start_grid(B: int) -> list[int]:
    """Accepted-label indices of the restart starts: 2^j - 1 < B (at least the start at label 0)."""
    out, j = [], 0
    while (1 << j) - 1 < max(1, B):
        out.append((1 << j) - 1)
        j += 1
    return out


def start_prior(n: int) -> np.ndarray:
    """Fixed summable prior over ``n`` starts: w_j ~ 1/((j+1)(j+2)), normalised to sum 1."""
    w = np.array([1.0 / ((j + 1) * (j + 2)) for j in range(n)])
    return w / w.sum()


COARSE_CELL_WIDTH = 0.02  # as evidence_q1's ``coarse`` for >16 starts: still certified (looser) and keeps a run inside the CPU cap


def _restart_mixture(ctx: Ctx, null: str, cfg: dict) -> StartMixture:
    ctx = replace(ctx, cell_width=max(ctx.cell_width, COARSE_CELL_WIDTH))
    starts = start_grid(ctx.B)
    trig = [("idx", float(s)) for s in starts]
    # per-start process: cond -> altgrid bet (as MinCore's cond core); marg -> the envelope bet ``evidence_q1._cheap_start``
    # (valid under marg within the declared class). DEVIATION from min_of_both (certified-sup LR marg start): the certified
    # sup cost ~420 CPU-s for 20 seeds x 16 cells with >= 5 starts, above the 300 CPU-s A2 cap.
    make = (
        q1._per_start("cond", "altgrid", ctx, cfg)
        if null == "cond"
        else q1._cheap_start("marg", ctx, cfg)
    )
    return StartMixture(make, trig, start_prior(len(starts)))


class RestartMinCore(MinCore):
    """``min`` of a cond-null and a marg-null restart mixture (shared start grid and prior)."""

    def __init__(self, ctx: Ctx, cfg: dict) -> None:
        super().__init__(
            _restart_mixture(ctx, "cond", cfg), _restart_mixture(ctx, "marg", cfg), "cond"
        )


def restart_min_spec() -> Q1Spec:
    return Q1Spec(
        FAMILY, VARIANT, "cond", "min", "DOMINATED_BY_VALID", COMMON_FILT,
        "cond core: none; marg core: stationary two-state chain with P^{g_i}",
        "any stopping time of the released-order filtration (Ville)",
        "see the two cores; start prior fixed and summable (2^j-1 label-index starts, w ~ 1/((j+1)(j+2)))",
        SEL_REQ,
        "A2: restart/onset mixture inside both components (shared prior), min outside; marg start = envelope bet (not certified-sup LR) for CPU; certificate level = selector_alpha as REP1",
    )  # fmt: skip


def build_evidence_a2(identity: dict, **kw) -> GapEvidence:
    """A2 identities: ``restart_min_certificate`` here, everything else delegated to ``evidence_q1.build_evidence``."""
    if identity["variant"] != VARIANT:
        return q1.build_evidence(identity, **kw)
    cfg = dict(identity["configuration"])
    build: Callable[[Ctx], object] = lambda c: RestartMinCore(c, cfg)
    return GapEvidence(
        restart_min_spec(), build, rho_bar=cfg.get("declared_rho_bar", q1.DEFAULT_RHO_BAR),
        alpha_level=kw.get("alpha_level") or cfg.get("selector_alpha"),
        cell_width=kw.get("cell_width", q1.CELL_WIDTH), selection=kw.get("selection", "undeclared"),
    )  # fmt: skip


def promoter_adapter_a2(identity: dict, *, alpha: float = 0.1, schedule: str = "calendar", **kw):
    from .adapters_evidence import _EvidencePromoterAdapter

    return _EvidencePromoterAdapter(
        f"promoter[{identity['family']}.{identity['variant']}|{identity['target_null']}]",
        lambda: build_evidence_a2(identity),
        identity["target_null"],
        alpha=alpha,
        schedule=schedule,
        **kw,
    )


__all__ = [
    "RestartMinCore",
    "build_evidence_a2",
    "promoter_adapter_a2",
    "start_grid",
    "start_prior",
]
