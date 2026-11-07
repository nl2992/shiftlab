"""RAR configuration. Every field records whether the value is stated in the paper.

Source: Retrain, Alert, or Rollback? (arXiv:2611.02251v1). ``STATED`` values are quoted from the
paper text read on 2026-11-07; ``CHOICE`` values are unspecified in the readable text and are
reconstruction choices of this repository (NOT the authors' values).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

STATED, CHOICE = "STATED", "CHOICE"


@dataclass
class RARConfig:
    # --- label / horizon ---
    tau: int = 800  # label delay (frozen example, Sec 4.3 / Fig 3) STATED
    warmup: int = 1000  # M_old warm-up prefix length; CHOICE
    # --- gates ---
    theta_L: float = 0.7  # Gate 2 label fraction; STATED (Glossary default)
    theta_R: float = 0.05  # Gate 3 degradation; STATED (Sec 6.9)
    W_train: int = 2700  # frozen example; STATED
    W_ref: int = 1000  # reference window for A_pre; STATED (Fig 3)
    W_cur: int = 500  # recent window for A_cur; CHOICE
    g: int = 200  # guard gap; STATED
    flag_ttl: int | None = None  # detector-flag lifetime from t_hat_d; CHOICE (default tau+W_train)
    detector_warmup: int = 30  # detector min reference after birth; CHOICE (ablation {30,500})
    # --- canary ---
    p1: float = 0.2  # STATED
    W1: int = 300  # STATED (Sec 13, via W1/p1+W2=2100)
    W2: int = 600  # STATED
    delta: float = 0.03  # canary margin; CHOICE (ablation {0.01,0.03,0.05})
    z_commit: float = 1.0  # STATED
    interim_fracs: tuple = (0.5,)  # interim R1 checkpoints; CHOICE
    interim_margin_mult: float = 2.0  # CHOICE
    kappa_canary_mult: float = 2.0  # timeout = mult * nominal stage duration; CHOICE
    # --- holds ---
    kappa_short: int = 1500  # CHOICE (1,500 appears in paper as two-tier hold length)
    kappa_long: int = 5000  # CHOICE (ablation {2500,5000,10000})
    kappa_min: int = 500  # CHOICE
    delta_crit_mult: float = 2.0  # Delta_crit = mult*theta_R; STATED ablation {2,3}
    m_clear: int = 200  # STATED
    W_mon: int = 1000  # alert monitoring clock / A3 rate limit; CHOICE
    soft_thr: float = 0.03  # A3 soft anomaly threshold; CHOICE
    # --- corruption pre-filter (q_t) ---
    q_window: int = 30  # CHOICE
    q_ratio: float = 3.0  # CHOICE
    r2_run: int = 100  # consecutive corrupt assessments for R2; CHOICE
    r2_hold_in_serving: bool = True  # R2 while Serving -> Alert-Hold-Hard; CHOICE
    min_train: int = 20  # skip retrain with fewer labelled rows; CHOICE
    alert_on_timeout: bool = True  # canary timeout = rollback plus alert (Sec 4.4); STATED
    # --- costs: C_e = 1, rho = C_r ---
    rho: float = 1.0  # STATED grid {0.1,0.5,1,5} (+ {1,10,100,1000})
    Ca_frac: float = 0.05  # STATED
    Cb_frac: float = 0.2  # STATED
    c_query: float = 0.0  # label cost; NOT in RAR's U (extension, default 0)
    seed: int = 0
    # --- policy switches (see baselines.py) ---
    mode: str = "full_rar"

    def __post_init__(self):
        if self.flag_ttl is None:
            self.flag_ttl = self.tau + self.W_train
        if not (0 < self.theta_L <= 1 and 0 < self.p1 <= 1):
            raise ValueError("theta_L, p1 must be in (0,1]")

    # cost helpers
    @property
    def C_r(self):
        return self.rho

    @property
    def C_a(self):
        return self.Ca_frac * self.rho

    @property
    def C_b(self):
        return self.Cb_frac * self.rho

    def as_dict(self):
        return asdict(self)


def earliest_retrain_time(t_d: int, tau: int, theta_L: float, W_train: int) -> int:
    """Paper Sec 4.3: t* = t_d + tau + ceil(theta_L*W_train) - 1."""
    return t_d + tau + math.ceil(theta_L * W_train - 1e-12) - 1


def latency_estimate(
    L_D: float, tau: int, theta_L: float, W_train: int, W1: int, p1: float, W2: int
) -> float:
    """Paper Eq. 5: L ~ max(L_D, tau+theta_L W_train) + (tau + W1/p1) + (tau + W2)."""
    return max(L_D, tau + theta_L * W_train) + (tau + W1 / p1) + (tau + W2)


def feasible_W_train(tau: int, theta_L: float) -> float:
    """Feasibility: W_train >= tau/(1-theta_L)."""
    return tau / (1 - theta_L)


# Mode switches for the seven policies of Sec 5
MODES = {
    # name: dict(retrain, gates, canary, alert, holds, cost_gate, periodic)
    "no_response": {
        "retrain": False,
        "gates": False,
        "canary": False,
        "alert": False,
        "holds": False,
        "cost_gate": False,
        "periodic": False,
    },
    "always_retrain": {
        "retrain": True,
        "gates": False,
        "canary": False,
        "alert": False,
        "holds": False,
        "cost_gate": False,
        "periodic": True,
    },
    "binary": {
        "retrain": True,
        "gates": False,
        "canary": False,
        "alert": False,
        "holds": False,
        "cost_gate": False,
        "periodic": False,
    },
    "alert_only": {
        "retrain": False,
        "gates": True,
        "canary": False,
        "alert": True,
        "holds": False,
        "cost_gate": False,
        "periodic": False,
    },
    "rollback_only": {
        "retrain": True,
        "gates": False,
        "canary": True,
        "alert": False,
        "holds": True,
        "cost_gate": False,
        "periodic": False,
    },
    "full_rar": {
        "retrain": True,
        "gates": True,
        "canary": True,
        "alert": True,
        "holds": True,
        "cost_gate": False,
        "periodic": False,
    },
    "cost_aware_binary": {
        "retrain": True,
        "gates": False,
        "canary": False,
        "alert": False,
        "holds": False,
        "cost_gate": True,
        "periodic": False,
    },
}
