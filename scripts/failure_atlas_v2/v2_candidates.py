"""All non-baseline policies for Atlas v2 runs: registry adapters, label-clock and RMM variants."""

from label_clock import FACTORIES as _LC
from registry_additions import FACTORIES as _RA
from restart_monitor import FACTORIES as _RMM

FACTORIES = {**_RA, **_LC, **_RMM}
