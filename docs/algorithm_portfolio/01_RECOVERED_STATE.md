# Recovered state (2026-11-08)

## Repositories and branches (local; most are not on the remote)

| Location | Branch | Head | Contents |
|---|---|---|---|
| `ICML/shift-research-starter` (main checkout) | `research/qsg-methods-search-2026-11-07` | see `git log` | EQSDp methods search, next-method screens, SAES, EQSDp C4 (batches 1–2), this portfolio |
| `ICML/shiftlab-multimodel-bcr-2026-11-08` | `research/multimodel-bcr-2026-11-08` | `2f7002d1` | Track A (BCR) feasibility pilot and ledger |
| `ICML/shiftlab-methods-recovery-2026-11-07` | `research/methods-recovery-2026-11-07` | `b74a1fc3` and later | Tracks B/C: Gap-Mix+ prereg, tuning and eval; PAVE+ feasibility |
| `ICML/shiftlab-gave-r-2026-11-06` | `research/gave-r-2026-11-06` | `03289d1d` | GAVE-R (Gap-Mix, PAVE, FreshCheck) development results (`docs/gaver/`) |

The commits `2db4ddef`, `ca5d8522` and `810f3d56` exist locally on the main checkout's branch.
`git branch -r --contains 810f3d56` returns nothing, so they are not pushed.

## Verified findings carried forward

| Finding | Source | Status |
|---|---|---|
| EQSDp C3: arm B −8.8 / −9.7 vs tuned Gong–Zhang-style / Qiu-style adapters (100 seeds, Holm) | `qsg_methods_search/synthetic_confirmation.md` | frozen PASS (historical) |
| EQSDp-B ≡ tuned Wald LCB (−0.05 [−0.28, +0.19]) | `comparator_panel_results.md` | PARTIAL |
| Wider Wald grid optimum λ=.85, γ=.15 (354.69 on dev seeds 2026110901) | `NEXT_METHOD_LEDGER.md` | verified from records |
| 12 two-model mechanisms; none beats tuned Wald by >≈1.6 units; Wald frontier efficient | `NEXT_METHOD_RESULTS.md` | development |
| Oracle restart ceiling 11.7 units (evaluator-only) | `NEXT_METHOD_LEDGER.md` | diagnostic |
| M5: real streams prefer λ=.97; EQSDp-B +6 on exposed streams | `NEXT_METHOD_LEDGER.md` | development |
| SAES Phase 1 FAIL (proxy ≤1.13× labels; staleness \|r\| ≤ .08) | `SAES_PHASE1.md` | development |
| BCR feasibility FAIL (+1.15 [−1.37, +3.66] vs tuned K-Wald) | BCR branch `docs/multimodel_bcr/03_PILOT_RESULTS.md` | development |
| Gap-Mix valid at declared ρ̄=.8; 14.7% cheaper than valid Markov-LR (post-hoc arm); 5.1% worse than invalid iid DSS | `docs/gaver/90_SUMMARY.md` | development |
| Delay-gated PAVE 4.4% better than DSS/uniform in 9 gate-on cells (d=50) | `docs/gaver/90_SUMMARY.md` | development, niche |
| GAVE-R integration sub-additive (interaction −0.0064 [−.0106, −.0026]) | `docs/gaver/50_INTEGRATION_RESULTS.md` | development |

## In-progress work found and repaired

- **Gap-Mix+ C3 development eval crashed.** The alt stage hit `KeyError: 'b0.05_d50'` because
  Arm-5 pacing was frozen only for the target families. The null stage completed.
  - Fix: Amendment A1 (`docs/methods_recovery/01_AMENDMENT_A1.md`, commit `b74a1fc3`). Arm-5
    pacing for the neighbour families is selected on unused tuning seeds; the partial alt rows
    were not inspected.
  - Status: neighbour tuning running, then the alt stage resumes.
- **EQSDp C4.**
  - Batch 1 (K=9, registered `013775db`) opened: NOT PASS, 5/9 supporting.
  - Amendment A2 (`1247fd48`): sequential batches with a binomial count test.
  - Batch 2 (K=7, registered `0b034638`) is being opened.
  - A checkpoint commit `2046f874` (not made by this coordinator) added nine batch-2 builder
    modules and build records. They were audited before registration.

## Constraints

- Free RAM is about 2 GB (other applications), so runs are capped at 8–10 workers.
- About 13 GB of disk is free.
- Model usage limits interrupted two builder agents. Their sources are recorded as not built.
