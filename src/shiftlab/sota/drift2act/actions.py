"""Action set, gain table (paper App. E.6, H=150, sigma_R=0.10), costs (Table 2) and configuration."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

ACTIONS = (
    "A0_noop",
    "A1_recalibrate",
    "A2_tta",
    "A3_query",
    "A4_retrain",
    "A5_rollback",
    "A6_abstain",
)
COST = np.array(
    [0.0, 0.2, 1.0, 0.0, 12.0, 1.5, 0.3]
)  # A3 = 0.05*k_t is charged per label (LABEL_COST), see doc
LABEL_COST = 0.05
GAIN = np.array(
    [  # rows: none, covariate, concept, subgroup; cols A0..A6  (verbatim from paper App. E)
        [0.00, 0.10, 0.05, 0.08, 0.12, 0.10, 0.15],
        [0.00, 0.35, 0.70, 0.25, 0.85, 0.40, 0.55],
        [0.00, 0.20, 0.30, 0.75, 1.05, 0.60, 0.65],
        [0.00, 0.25, 0.35, 0.85, 0.95, 0.55, 0.80],
    ]
)


@dataclass
class Config:
    # paper-stated
    tau: float = 0.20
    delta: float = 0.05
    delay: int = 50
    label_budget: int = 3000
    gamma: float = 50.0
    sigma_U: float = 0.10
    N: int = 1024
    cooldown_retrain: int = 800
    cooldown_rollback: int = 400
    k_max: int = 64
    k_high: int = 32
    k_low: int = 8
    m_low: float = 0.02
    theta_sel: float = 0.6
    # NOT given in the paper -- our reconstruction choices (documented)
    lam: float = 0.5  # lambda value unstated; applied to c(a)/max(c)
    cost_norm: float = 12.0
    eps_noop: float = 0.15  # act only if best utility >= eps (otherwise Table-2 gains > 0 under 'none' force constant acting)
    audit_every: int = 4
    evidence_beta: float = 0.3  # tempering of the diagonal-Gaussian likelihood (paper: beta=1 for its discriminative model)
    a3_cooldown: int = 50
    min_retrain_labels: int = 30
    window_mode: str = "delayed"  # Alg.1 (delay-adjusted); 'current' = Sec 4.1
    pool: str = "window"  # 'round' = Alg.1 literal (|Q_t|), 'window' = all released labelled items in window
    delta_mode: str = (
        "mandate"  # "alg1" = delta_t=6delta/(pi^2 t^2) on top of rad(n,.) (literal Alg.1)
    )
    use_certificate: bool = True
    fail_schedule: str = "belief_or_risk"  # on U>tau: 'literal' (always schedule rollback/retrain), 'risk_evidence' (R^>tau), 'belief_or_risk'
