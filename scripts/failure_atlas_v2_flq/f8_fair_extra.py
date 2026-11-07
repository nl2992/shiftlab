"""Previously registered F8 controls plus the in-horizon validation-gate baseline."""

from f8_synthetic_extra import EXTRA as PREVIOUS
from fair_validation_gate import EXTRA as GATE

EXTRA = {**PREVIOUS, **GATE}
