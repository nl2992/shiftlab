# Final publication decision (2026-11-08)

## New-algorithm programme: **INCOMPLETE**

| Track | Verdict | Deciding evidence |
|---|---|---|
| A: BCR | STOP at feasibility | ties tuned K-Wald (+1.15 [−1.37, +3.66]); on the K-Wald frontier, never inside it |
| B: Gap-Mix+ | FAIL (registered C3 development rule) | 3.97% worse than the strongest valid comparator; gap-10 thinning is cheaper |
| C: PAVE+ | STOP at feasibility | delay-gated PAVE ties `episode_front`; simple rules capture part of the rest |

No track passed C2. No new-method C3 or C4 was frozen. Per directive §16, no fourth broad search is
started automatically.

## Existing EQSDp / Failure Atlas asset

| | Status |
|---|---|
| C1 | PASS (M1–M5; M5 reproduced on sealed data) |
| C2 | NOVEL-INTEGRATION (confidence-bound payback ≡ Wald); not a new primitive |
| C3 | PASS (historical frozen confirmation vs adapters) |
| C4 | **target reached under Amendment A2: 9/16 supporting**, 16/16 favourable, count bound 1.6 × 10⁻⁸; effect −0.75% of cost |

## Recommendation

- **Venue.** Submit as a **methods-and-analysis paper** to TMLR (preferred) or a
  deployment/MLOps-focused workshop. Main message: a simple confidence-bound payback switcher is
  consistently but modestly better than tuned point-estimate economic switchers on real data. It
  sits at the empirical frontier of evidence-processing variants, and the remaining headroom is
  informational.
- **Why not ICML.** ICML main track is not recommended: the algorithmic novelty is integration,
  and the real effect is below 1%.

## Required before submission

1. Full-text novelty reads: *The Challenger*, Regol et al. appendix, Gong–Zhang, Qiu et al., Sethi
   et al.
2. Figures. PaperBanana is not installed in this environment, so the dependency must be resolved
   (per AGENTS.md, no substitute generator).
3. Push the local branches. Every commit since `6ce1a3f7` on all three branches is local-only.
4. A reviewer-style kill-argument pass on the A2 sequential design and the batch-2 selection
   disclosure.
