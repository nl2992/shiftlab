# Final publication decision (status at 2026-11-07, end of the next-method cycle)

**Programme verdict: INCOMPLETE. C2 (a new algorithm beyond tuned Wald-LCB) is not achieved on
the evidence so far.** This is not a terminal success. Two routes remain feasible (§4), and
choosing between them is the user's call.

## 1. Contribution status

| | Status | Evidence |
|---|---|---|
| **C1 Failure Atlas** | **PASS (scoped), extended** | M1–M4 as recorded (Atlas v2, D0). New this cycle: (i) the tuned fixed-discount Wald frontier is efficient against 12 adaptive mechanisms; (ii) oracle change-time information is worth 11.7 units, but label-only online detection cannot capture it (information-limited); (iii) **M5 hyperparameter-transfer failure**: the evidence memory optimal on change-heavy synthetic streams is 6–9 units wrong on serially dependent real streams, and change detectors mistake dependence for change. |
| **C2 Algorithm** | **NOT ACHIEVED** (new method); base rule = NOVEL-INTEGRATION | 12 candidates screened (ledger). Best robust option: ESS-adjusted Wald (≈1 unit minimax gain; a classical correction). |
| **C3 Synthetic** | historical PASS for EQSDp vs adapters (unchanged); **next-method C3 NOT RUN** (no finalist) | NM-C3 seeds unopened |
| **C4 Real data** | **BLOCKED** for a new method; EQSDp C4 infrastructure ready (sealed builds, amendment A1) | exposed evidence: EQSDp-B beats tuned Gong–Zhang-style on 13/14 streams (−5.7) |

## 2. Completion checklist (honest marks)

C1:
- [x] M1–M4 evidence consolidated.
- [x] target failure identified (M2/M3 → the information bound; M5 new).
- [x] strongest baseline confirmed (tuned fixed-discount Wald).
- [x] causal mechanism documented.
- [ ] mechanistic figure: **blocked**, PaperBanana not installed in this environment (no substitute used).

C2:
- [x] adaptive discounting (A1, A3, A4, A5, A5b, A6).
- [x] asymmetric hysteresis (B1).
- [x] pending/decision-value acquisition (D1, S).
- [x] dependence (E), Bayes-myopic benchmark (F), OPE selection (G).
- [x] compared against tuned Wald.
- [ ] finalist selected: **none passed**.
- [ ] pseudocode/proof of a finalist: n/a.

C3:
- [x] historical result preserved.
- [x] development screens.
- [x] ablations.
- [x] tuned matched baselines.
- [ ] coherent target family with a gain: **not found**.
- [ ] freeze + independent confirmation: **not run**.

C4:
- [x] data audit.
- [x] exposed-stream development.
- [ ] frozen protocol for a new method.
- [ ] eight supporting datasets: **not started for a new method**.

Paper-readiness:
- [x] candidate ledger.
- [x] negative-result records.
- [x] reproduction commands.
- [ ] final novelty audit of a finalist.
- [ ] comparator fidelity table refresh.
- [ ] figures.
- [ ] manuscript outline.

## 3. Why the search stopped here

Each mechanism was given a fair, simple implementation and a grid at least as wide as the
comparator's. The failure pattern is consistent and explained:

- On this contract the information rate (≈0.1 labels/event, delay 100) sets the reaction time.
- Every memory or hurdle change only moves along the change-vs-guard frontier that (λ, γ)
  already spans.
- Free prediction-only information (the sentinel) is too slow at realistic shift sizes.
- Online cost-based selection (G) is too noisy within a 2,000-event episode.

More variants of the same families are not justified by the evidence.

## 4. Feasible routes (user decision)

1. **Narrow methods paper on the existing integration (recommended if the deadline binds).**
   - Method: confidence-bound reversible payback switching under hard, delayed,
     disagreement-only label budgets (EQSDp ≡ Wald).
   - Evidence: historical C3 vs the published-method adapters; the new frontier-efficiency
     and information-bound results as the analysis section; M5 as a practical finding.
   - C4: run the registered EQSDp C4 (vs tuned Gong–Zhang-style). Optionally amend the arm,
     before any opening, to the cross-domain minimax memory (λ=.95 or ESS-Wald).
   - Novelty stays NOVEL-INTEGRATION. It needs a full read of Regol 2025 and *The
     Challenger* (2512.18390).
2. **Continue the method search on a different lever.** The evidence says gains must come from
   information, not processing. Candidates, untested so far:
   - long-delay and congested-pending regimes (F6), where delay rather than label rate binds;
   - richer label-free signals on real streams (model confidence/margins, feature-drift
     scores), with real disagreement-rate dynamics rather than synthetic ones;
   - pooling evidence across episodes or streams (a hierarchical prior on memory length) to
     fix M5 without within-episode selection noise.

   Each needs its own development cycle; none has evidence yet.

Not recommended: tuning the Beta/Wald hurdle further, or re-screening adaptive-memory variants.
