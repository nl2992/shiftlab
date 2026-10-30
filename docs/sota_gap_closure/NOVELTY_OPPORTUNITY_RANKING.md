# Novelty opportunity ranking (judgement, grounded in the stored results)
Scores 1-5 (5 = best). "Statistical correctness" = whether the mechanism keeps an anytime-valid guarantee under its null. Novelty is **unassessed against the literature** (primary sources unreachable): scores reflect only what was not present in this repository's baselines.

| rank | opportunity | severity of the problem | methods affected | reproducibility | importance | fix feasibility | statistical correctness | potential novelty | status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Dependence-robust (conditional-null-safe) e-processes: long-run-variance-calibrated bets with a proof under mixing | 5 | 3+ | 5 | 5 | 2 (no proof; F2 is a heuristic that only partly works) | 1 now, could be 4 | 4 | OPEN: F2 partial |
| 2 | Allocation-aware validity caps (use the inclusion probability on the events where the increment is non-zero) | 4 | 7 families | 5 | 4 | 4 (Q2: 0.77 -> 0.92 for CAMS-style certification) | 5 | 3 | partially realised in Q2 (disagreement-event cap) |
| 3 | Disagreement-focused certification with exact zero increments (Q2/Q3) | 3 | 4 | 4 | 4 | 5 | 5 | 2 (CAMS-style) | realised; matches CAMS-style baseline |
| 4 | Decision-cost gate for Brier evidence (HG) | 3 | 1 parent tested | 3 | 4 | 5 | 5 | 2 (composition of known ideas) | realised; survives repair |
| 5 | Forgetting evidence for non-stationary certification / reversal | 2 | all Q2 | 2 | 4 | 1 (no anytime-valid forgetting form found) | 1 | 4 | open |
| 6 | Growth-aware acquisition | 1 (does not help) | - | 5 | 3 | - | 5 | 1 | falsified (equals variance to second order; loses under the validity tax) |
| 7 | Reliability-adaptive proxy weight | 1 (does not help) | - | 4 | 2 | - | 5 | 1 | falsified |
| 8 | Budget pacing | 1 | - | 4 | 2 | - | 5 | 1 | falsified (v2 pending in results) |
