"""C3 frozen confirmation registry (see docs/qsg_methods_search/synthetic_confirmation_protocol.md)."""

from d3_extra import CONFIRM
from qsg import EXTRA as _QSG

EXTRA = {**CONFIRM, "QSG": _QSG["QSG"]}
NAMES = list(EXTRA) + ["model_selector_causal", "CONTROL_never_switch"]
