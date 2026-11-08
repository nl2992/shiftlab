# Method ranking

| Criterion | A: BCR | B: Gap-Mix+ | C: PAVE+ | EQSDp (fallback) |
|---|---|---|---|---|
| Gate outcome | feasibility FAIL | C3-development FAIL | feasibility STOP | C3 PASS (historical); C4 9/16 under A2 |
| Best comparison | +1.15 [−1.37, +3.66] vs tuned K-Wald | −3.97% vs strongest valid comparator | PAVE ties `episode_front` (+0.01%) | −0.75% vs tuned Gong–Zhang-style adapter (16/16 favourable) |
| Attributable mechanism | none beyond K-Wald | governor +1.2% vs ablation | deadline cutoff ≈41% of PAVE gain | confidence-bound hurdle (≡ Wald) halves switching |
| Novelty | — | — | — | NOVEL-INTEGRATION |
| Real-data feasibility | K≥3 streams not built | dependence-declared data needed | delay imposed, not authentic | done (16 datasets) |

**Ranking.** None of the three new tracks has defensible algorithmic headroom. The only asset with
complete C1/C3/C4 evidence is the EQSDp/Failure-Atlas methods-and-analysis package. Per directive
§16, no fourth broad search is launched.
