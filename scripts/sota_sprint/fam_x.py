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

from qce import DiscernQCE

EXTRA = {
    "choe_ramdas_eb": lambda T, B, cs, cq, a, d, r: DiscernQCE(
        T, B, a, rng=r("choe_ramdas"), name="choe_ramdas_eb"
    ),
    "choe_ramdas_eb+front": lambda T, B, cs, cq, a, d, r: DiscernQCE(
        T, B, a, rng=r("choe_ramdas"), front=True, name="choe_ramdas_eb+front"
    ),
}


# ------------------------------------------------------------------------------------------------
# Phase 7 cross-family combinations (lead, 2026-11-03, after the 24-candidate screen). Parameters are
# the families' registered/dev-tuned values; nothing below was tuned.
# ------------------------------------------------------------------------------------------------
import fam_a
import fam_d
from simulator import QueryRequest


def _a5b(name, reserve=0.0, **kw):
    def f(T, B, cs, cq, a, d, r):
        pol = fam_a.FamA(
            T,
            B,
            a,
            rng=r("QSG"),
            name=name,
            evidence="sui",
            density="adaptive",
            rho_sig=2.0,
            sui_kw=fam_a._B,
            **kw,
        )
        pol.reserve = round(reserve * B)  # QSG semantics: kept back from front-loading
        return pol

    return f


class _SaveAfterDiscard(fam_a.FamA):
    """A5b + economic acquisition (C-family finding): no post-verdict labels after a DISCARD
    verdict (the incumbent is kept and only a late improvement could use them); monitoring after a
    promotion is kept for rollback. Acquisition only: validity is A5b's."""

    def request_labels(self, event, remaining_budget):
        if self.decided and self.deployed == 0:
            self.acq.note_event(bool(event.model_predictions[0] != event.model_predictions[1]))
            return QueryRequest(requested=False)
        return super().request_labels(event, remaining_budget)


def _a1b_cert(side):
    return fam_d._A1Cert(side, fam_a.MarkovSUI, **fam_a._B)


def _gate(kind, name, **kw):
    return lambda T, B, cs, cq, a, d, r: fam_d.DeployGate(
        fam_d.make_host(kind, r), T, B, a, rng=r("D_gate"), name=name, **kw
    )


EXTRA.update(
    {
        # A5 + B5: dependence-valid evidence + monitoring reserve (B's .15) + rollback (QSG's)
        "X_A5B5": _a5b("X_A5B5", reserve=0.15),
        # A6 + B5 (+ C5 components are acquisition-only and did not replicate; see ledger)
        "X_A6B5": _a5b("X_A6B5", reserve=0.15, dualclock=True, inflight=True),
        # A5 + C (label saving after a discard verdict)
        "X_A5C": lambda T, B, cs, cq, a, d, r: _SaveAfterDiscard(
            T,
            B,
            a,
            rng=r("QSG"),
            name="X_A5C",
            evidence="sui",
            density="adaptive",
            rho_sig=2.0,
            sui_kw=fam_a._B,
        ),
        # D4 + A1: certified fast selection under dependence (Model Picker host, A1b evidence)
        "X_D4A1": _gate("mp", "X_D4A1", cert=_a1b_cert, rollback=True, reserve=0.10),
        # D6 + A1: the shared wrapper with dependence-valid evidence, on two independent hosts
        "X_D6A1:mp": _gate("mp", "X_D6A1:mp", cert=_a1b_cert),
        "X_D6A1:cams": _gate("cams", "X_D6A1:cams", cert=_a1b_cert),
    }
)
