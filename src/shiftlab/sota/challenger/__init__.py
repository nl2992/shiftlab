"""The Challenger (arXiv 2512.18390) GSE / OSE / LSE: PAPER_RECONSTRUCTION.

No author code was found (the arXiv HTML lists none). Everything here is rebuilt from the paper text;
items the text did not pin down are flagged UNVERIFIED in the docstrings and in
docs/d2a_rar/BASELINE_REPRODUCTION.md.
"""

from shiftlab.sota.challenger.algorithms import (
    CONTINUE,
    DISCARD,
    SWITCH,
    Outcome,
    gse_decide,
    lse_decide,
    ose_decide,
    run_gse,
    run_lse,
    run_ose,
)
from shiftlab.sota.challenger.values import (
    Economics,
    integer_oracle_epoch,
    oracle_value,
    stopping_epoch_thm31,
    t_dagger_asymptotic,
)

__all__ = [
    "CONTINUE",
    "DISCARD",
    "SWITCH",
    "Economics",
    "Outcome",
    "gse_decide",
    "integer_oracle_epoch",
    "lse_decide",
    "oracle_value",
    "ose_decide",
    "run_gse",
    "run_lse",
    "run_ose",
    "stopping_epoch_thm31",
    "t_dagger_asymptotic",
]  # fmt: skip
