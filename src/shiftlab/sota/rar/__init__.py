"""RAR (Retrain / Alert / Rollback) - PAPER_RECONSTRUCTION of arXiv:2611.02251v1.

No author artifact is obtainable (Zenodo DOI reserved, 'on request'); see docs/d2a_rar/baselines/RAR.md.
"""

from .components import (
    ADWINDetector,
    AllLabelsPolicy,
    FractionLabelPolicy,
    HookContext,
    Learner,
    MajorityFactory,
    RiverHoeffdingTreeFactory,
    ScriptedDetector,
    StepSizeQuality,
    StumpFactory,
    ThetaLGate,
    ThetaRGate,
)
from .config import MODES, RARConfig, earliest_retrain_time, feasible_W_train, latency_estimate
from .controller import (
    CANARY1,
    CANARY2,
    HOLD_HARD,
    HOLD_SOFT,
    SERVING,
    STATES,
    LeakageError,
    RARController,
    StepOutput,
)
from .harness import run_stream, utility_at_rho

FIDELITY_TIER = "PAPER_RECONSTRUCTION"

__all__ = [
    "CANARY1",
    "CANARY2",
    "FIDELITY_TIER",
    "HOLD_HARD",
    "HOLD_SOFT",
    "MODES",
    "SERVING",
    "STATES",
    "ADWINDetector",
    "AllLabelsPolicy",
    "FractionLabelPolicy",
    "HookContext",
    "LeakageError",
    "Learner",
    "MajorityFactory",
    "RARConfig",
    "RARController",
    "RiverHoeffdingTreeFactory",
    "ScriptedDetector",
    "StepOutput",
    "StepSizeQuality",
    "StumpFactory",
    "ThetaLGate",
    "ThetaRGate",
    "earliest_retrain_time",
    "feasible_W_train",
    "latency_estimate",
    "run_stream",
    "utility_at_rho",
]
