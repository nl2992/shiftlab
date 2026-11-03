"""Exact one-batch boundary-null check for the archived P6 rule."""

from __future__ import annotations

import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/promising_directions/results/adversarial_review/bl.py.txt"
DEST = ROOT / "docs/retrospective_audit_2026_11_01/P6_BOUNDARY_COUNTEREXAMPLE.json"


def one_batch_false_promotion(n: int, threshold: Fraction) -> Fraction:
    """D is iid +1/-1 with probability 1/2 under zero conditional mean."""
    if n < 1 or not 0 < threshold < 1:
        raise ValueError("invalid batch rule")
    positive_counts = [k for k in range(n + 1) if Fraction(2 * k - n, n) > threshold]
    return Fraction(sum(math.comb(n, k) for k in positive_counts), 2**n)


def run() -> dict[str, object]:
    source_text = SOURCE.read_text(encoding="utf-8")
    if (
        "s.sm/np.maximum(s.cnt,1)>s.thr" not in source_text
        or "s.cnt=np.where(full,0.0,s.cnt)" not in source_text
    ):
        raise ValueError("archived batch firing/reset rule has changed")
    p = one_batch_false_promotion(25, Fraction(3, 10))
    calibration = []
    for opportunities in (1, 8, 16):
        for min_positive in range(14, 26):
            candidate_threshold = Fraction(2 * (min_positive - 1) - 25, 25)
            one_batch = one_batch_false_promotion(25, candidate_threshold)
            familywise = 1 - (1 - one_batch) ** opportunities
            if familywise <= Fraction(1, 20):
                calibration.append(
                    {
                        "max_independent_batches": opportunities,
                        "minimum_positive_count_for_fire": min_positive,
                        "strict_threshold_fraction": str(candidate_threshold),
                        "one_batch_probability_fraction": str(one_batch),
                        "familywise_probability": float(familywise),
                        "hoeffding_union_threshold": math.sqrt(
                            2 * math.log(opportunities / 0.05) / 25
                        ),
                    }
                )
                break
    return {
        "status": "EXACT_MATHEMATICAL_COUNTEREXAMPLE_NOT_ARCHIVED_SIMULATION_RATE",
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "batch_size": 25,
        "strict_mean_threshold": "3/10",
        "conditional_null": "At each queried disagreement, D is independently +1 or -1 with equal probability; E[D_t | past]=0; first 25 labels are eventually released and eligible for one batch.",
        "one_batch_false_promotion_probability_fraction": str(p),
        "one_batch_false_promotion_probability": float(p),
        "exceeds_alpha_0_05": p > Fraction(1, 20),
        "two_independent_batch_opportunities_probability": float(1 - (1 - p) ** 2),
        "illustrative_fair_coin_calibration": calibration,
        "limitations": "Exact thresholds assume iid symmetric +/-1 eligible labels and a fixed maximum number of independent batch opportunities. They are not valid calibration for every conditional-null/selective-query/delay law. Hoeffding union thresholds require bounded conditionally mean-zero batch increments and predictable sampling; neither condition is established for archived P6. This is not the empirical false-promotion rate or a cost replay.",
    }


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["one_batch_false_promotion_probability_fraction"])
