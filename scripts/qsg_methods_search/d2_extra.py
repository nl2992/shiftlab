"""D2 registry: EQS-D grid plus the declared comparators."""

from eqs import EXTRA as _EQS
from eqs_d import EXTRA as _EQSD
from qsg import EXTRA as _QSG
from r6_policies import EXTRA as _R6

EXTRA = {**_EQSD, **_R6, "QSG": _QSG["QSG"], "econF_mo5_m5": _EQS["econF_mo5_m5"]}
NAMES = list(EXTRA) + ["model_selector_causal", "economic_replacement", "CONTROL_never_switch"]
