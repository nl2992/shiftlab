"""Drift2Act (Lamaakal et al., arXiv:2603.08578) -- PAPER_RECONSTRUCTION.

No author code was found (checked 2026-11-07); every module below is reconstructed from the paper
text.  See docs/d2a_rar/baselines/DRIFT2ACT.md for the spec, deviations and validity conditions.
Hooks: ``EvidenceModel`` (Q1 evidence layer) and ``LabelRequestPolicy`` (Q2 label-request policy).
"""

from .actions import ACTIONS, COST, GAIN, Config
from .audit import (
    BudgetError,
    HeuristicQueryPolicy,
    LabelRequestPolicy,
    LabelStore,
    LeakageError,
    QueryContext,
    WindowedAuditor,
)
from .belief import DRIFTS, BeliefFilter, EvidenceModel, GaussianEvidence
from .certificate import Certificate, CertResult, rad, rad_fp
from .controller import Drift2ActController

__all__ = [
    "ACTIONS",
    "COST",
    "DRIFTS",
    "GAIN",
    "BeliefFilter",
    "BudgetError",
    "CertResult",
    "Certificate",
    "Config",
    "Drift2ActController",
    "EvidenceModel",
    "GaussianEvidence",
    "HeuristicQueryPolicy",
    "LabelRequestPolicy",
    "LabelStore",
    "LeakageError",
    "QueryContext",
    "WindowedAuditor",
    "rad",
    "rad_fp",
]
