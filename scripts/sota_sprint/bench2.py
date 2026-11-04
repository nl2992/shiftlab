"""Sprint 2 (A5b x D2 x RMM) frozen specification. Registered 2026-11-04 before any sprint-2 run.

Three independent evaluation tracks (sprint-2 brief section 3; historical verdicts are NOT changed):

* Track E (economic): minimise J = loss + .05 labels + 5 switches; no false-promotion ceiling.
* Track R (risk-constrained): empirical cost-risk curves at targets R5..R30. Each policy's nominal alpha
  is calibrated on DEVELOPMENT null runs (`calibrate`, `risk_curves.py`) and then evaluated on separate
  seeds. An empirical risk target is NOT an anytime-valid guarantee.
* Track V (validity): each method is scored only against the null it actually tests (NULL_TESTED):
  V1 conditional-advantage null, V2 marginal stationary-Markov null, V3 economic non-improvement.
"""

from __future__ import annotations

from bench import DEV_ENVS, SPRINT_REGIMES  # noqa: F401  (re-exported for agents)

DEV_SEED_BASE = 2026110701  # sprint-2 development (20 seeds per environment)
EVAL_SEED_BASE = 2026110801  # sprint-2 Round-5 evaluation (registered before use; >= 100 seeds)
NULL_SEED_BASE = 2026110802  # Round-5 nulls (>= 1000 seeds)
REAL_SEED_BASE = 2026110803  # Round-5 real replays

RISK_TARGETS = {"R5": 0.05, "R10": 0.10, "R15": 0.15, "R20": 0.20, "R25": 0.25, "R30": 0.30}
ALPHA_GRID = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5]

# Development environments for Track R calibration: the null mix a risk target refers to. The mix is
# fixed here so that "risk" means the same thing for every method: iid, moderate and strong persistence.
RISK_NULLS = ["F0_null", "F0_worse", "F5_dep_null_r8", "F5_dep_null_r95"]
RISK_ALTS = ["F0_better", "F7_near_better", "F9_bursty_better", "F1_late_800", "F5_dep_better_r8",
             "S_dep_better_r95"]

# Track V: which null each method's guarantee actually concerns (sprint-1 code; new families add theirs).
#   V1 = conditional advantage: E[challenger advantage | F_{t-1}] <= 0 on the evidence it uses
#        (betting / empirical-Bernstein / likelihood-ratio e-processes on query-conditional or IPW outcomes)
#   V2 = marginal stationary first-order Markov null (p <= 1/2, any rho)
#   V3 = economic non-improvement (expected value of switching <= 0 after costs); no anytime guarantee
#   none = no false-promotion guarantee
NULL_TESTED = {
    "gated_deployment": "V1", "gated_adaptive_range": "V1", "gated_adaptive_range+front": "V1",
    "discern_style": "V1", "discern_design_floor": "V1", "SMCS+retain-incumbent": "V1",
    "xu_acquisition_only": "V1", "choe_ramdas_eb": "V1", "choe_ramdas_eb+front": "V1",
    "gated_deployment+QCE": "V1", "gated_deployment+QCE+front": "V1", "QSG": "V1",
    "D1": "V1", "D2": "V1", "rmm:gated_deployment+RMM": "V1", "rmm:LRMD": "V1",
    "A5b": "V2", "A1b": "V2", "D5": "V2", "M_LRMD_SUI": "V2", "M_RMMSUI_A5b": "V2",
    "economic_replacement": "V3", "P7s_settled": "V1",
    "model_picker_adapter": "none", "cams_adapter": "none", "model_selector_causal": "none",
    "online_llm_picker": "none", "variance_min_ipw": "none", "gong_zhang_paid_obs": "none",
    "qiu_delayed_movement": "none", "ryabchenko_capacity": "none", "CONTROL_never_switch": "none",
}

# The 24 mandatory sprint-2 configurations (status tracked in docs/sprint2/candidates.json).
MANDATORY = [f"H{i}" for i in range(1, 7)] + [f"R{i}" for i in range(1, 7)] + \
            [f"T{i}" for i in range(1, 7)] + [f"P{i}" for i in range(1, 7)]
