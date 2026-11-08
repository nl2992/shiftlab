# C1: Failure Atlas (consolidated)

Each mechanism is an empirical finding for the stated implementations and contract. None is
claimed universal.

| ID | Mechanism | Evidence | Contract | Source |
|---|---|---|---|---|
| M1 | Certification latency: certified hosts deploy a better challenger late under binding budgets | +8 to +120 cost vs best uncertified on stationary-advantage cells; reproduced on 4 real streams; α=.05 certification costs 20–100 units | T=2000, B=200, c_q=.05, c_s=5 | `failure_atlas_v2_flq/results/REPORT.md`, `selected_mechanism.md`; `qsg_methods_search/publication_decision.md` (D0) |
| M2 | Switching churn of fast uncertified selectors | +12 to +64 vs never-switch on null/dependence cells, 5–11 switches. Multi-model: Model Picker adapter 6.9 switches (+28 vs K-Wald); null churn grows K=3→5 | same; K=3/5 pilot | Atlas v2; BCR `03_PILOT_RESULTS.md` |
| M3 | Late improvement / reversal recovery | Certified hosts terminal; oracle-restart ceiling 11.7 units shows the cost of slow online change detection; candidate elimination delays recovery (BCR E3 +20.5) | same | Atlas v2; `NEXT_METHOD_LEDGER.md`; BCR pilot |
| M4 | Serial-dependence miscalibration | Frozen iid DSS evidence null UCB .27–.40 at ρ=.8, .98 at ρ=.95; betting methods .24–.63 at ρ=.95 | GAVE-R harness, Atlas v2 | `docs/gaver/90_SUMMARY.md` §3; Atlas v2 |
| M5 | Evidence-memory transfer failure | λ=.85–.9 tuned on synthetic is 6–9 units worse than λ=.97 on 14 exposed real streams; real disagreement outcomes have lag-1 autocorrelation .3–.95; on 16 sealed C4 datasets arm A (λ=.95) beats arm B (λ=.9) on 16/16 | exposed + sealed real streams | `NEXT_METHOD_LEDGER.md`; `c4_results.md` |

**Information-limit finding (supporting analysis).**
- Twelve label-only mechanisms and the BCR prototype stay within ≈1.6 units of the tuned
  fixed-discount Wald frontier.
- +100% free labels is worth 5.3 units.
- Observable unlabeled signals carry ≤ 1.13× labels of information (SAES Phase 1).

**Counterexamples and limits.**
- M2 is solved by certification, at the M1 price.
- M4 is avoided by Gap-Mix within its declared ρ̄=.8 and fails beyond it.
- Arm B loses to never-switching on 3 of 16 real datasets where the challenger is not better.
