# Candidate ranking and decision record (2026-10-30)

Scores are triage aids, not evidence of paper quality. Weights: novelty delta 30, potential improvement 25, theory feasibility 20, compute feasibility 15, generalization 10.

| Candidate | Novelty (30) | Improvement (25) | Theory (20) | Compute (15) | Generalization (10) | Total | Basis |
|---|---|---|---|---|---|---|---|
| A: growth/signal-aware allocation with per-context bets | 12 | 14 | 13 | 14 | 5 | **58** | Repo already has a myopic growth rule (negative result), so novelty is limited to the per-context bet/SNR/bet-cap delta. Cheap, falsifiable screen (P1) |
| B: robust hybrid (uniform / variance / growth) | 8 | 6 | 10 | 14 | 6 | 44 | Robust ASI already publishes the active-to-uniform path (code read). S6c showed no gain over uniform on CRSP |
| C: delay/budget-aware policy approximation | 12 | 8 | 12 | 10 | 4 | 46 | Exact-oracle gap to the best constant table is only +0.002 to +0.03 power (S3, S3b), capping the possible gain; nonmonotone policy needs a flexible class |

**Decision.** Primary: **A** (narrowed to the per-context-bet, SNR-aware form above). Fallback: **C**. Deferred: **B**, until Pro-Active Inference and Active MPPI can be read, since they may already contain the robust hybrid.

**Why not simply "growth-aware"?** Because the derivation says it is equivalent to Neyman under a common bet, and the repo's myopic growth rule failed. The candidate is only worth screening because the per-context bet changes the objective, and because that is cheap to falsify.

**Source-access caveat.** The SOTA gate is *not* fully satisfied: the mandatory primary papers could not be fetched this session (hosts blocked). Any novelty statement is therefore provisional, and nothing may be claimed beyond "no known published result found *in the sources available*".
