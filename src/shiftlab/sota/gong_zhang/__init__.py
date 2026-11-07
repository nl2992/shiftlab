"""Gong & Zhang (ICML 2026) paid-observation contextual bandits, PAPER_RECONSTRUCTION; see docs/d2a_rar/baselines/GONG_ZHANG.md."""

from .core import (
    LinearPolicyGame,
    MetaController,
    OracleEfficientPaid,
    PaidExp4,
    eta_limited,
    eta_sufficient,
    eta_thm21,
    free_budget_threshold,
    obs_prob_paid,
    random_subset_budget,
    run_paid,
)
from .port import PaidLabelAcquirer

__all__ = [
    "LinearPolicyGame",
    "MetaController",
    "OracleEfficientPaid",
    "PaidExp4",
    "PaidLabelAcquirer",
    "eta_limited",
    "eta_sufficient",
    "eta_thm21",
    "free_budget_threshold",
    "obs_prob_paid",
    "random_subset_budget",
    "run_paid",
]
