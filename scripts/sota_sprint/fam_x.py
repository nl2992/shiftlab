"""Comparators added after the Agent F prior-art audit (2026-11-03).

Choe & Ramdas, "Comparing sequential forecasters" (Oper. Res. 2024, arXiv:2110.00115) and Henzi &
Ziegel (Biometrika 2022, arXiv:2103.08402) give anytime-valid comparisons of two forecasters under
ARBITRARY dependence, for the null that the running average of conditional mean loss differences is
<= 0. Their constructions are empirical-Bernstein / betting confidence sequences on paired loss
differences with full observation. Under a hard label budget no author rule exists for which events
to label; the common-contract port below runs the Waudby-Smith-Ramdas predictable-plug-in EB CS
(the same EB family Choe-Ramdas use) on query-conditional paired differences Y in [-1, 1], with
uniform paced acquisition ("choe_ramdas_eb") or every disagreement queried while undecided
("+front"). This is an adapter, not author code; it reuses DiscernQCE's fidelity-checked PrPl-EB CS.

Note on nulls: these methods control the time-averaged CONDITIONAL mean. Under a persistent Markov
null with marginal p = 1/2 that average is positive during runs, so a promotion there is correct
for their null and a false promotion for the marginal null the ShiftLab bound targets.
"""

from __future__ import annotations

import sys
from pathlib import Path

_FLQ = Path(__file__).resolve().parents[1] / "failure_atlas_v2_flq"
if str(_FLQ) not in sys.path:
    sys.path.insert(0, str(_FLQ))

from qce import DiscernQCE  # noqa: E402

EXTRA = {
    "choe_ramdas_eb": lambda T, B, cs, cq, a, d, r: DiscernQCE(
        T, B, a, rng=r("choe_ramdas"), name="choe_ramdas_eb"),
    "choe_ramdas_eb+front": lambda T, B, cs, cq, a, d, r: DiscernQCE(
        T, B, a, rng=r("choe_ramdas"), front=True, name="choe_ramdas_eb+front"),
}
