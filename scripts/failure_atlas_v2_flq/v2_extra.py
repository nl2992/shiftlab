"""All Atlas v2 additions in one registry: R6 ports, QCE-repaired hosts, QSG and its ablations."""

from qce import EXTRA as _QCE
from qsg import EXTRA as _QSG
from r6_policies import EXTRA as _R6
from strong_hosts import EXTRA as _STRONG

EXTRA = {**_R6, **_QCE, **_QSG, **_STRONG}
