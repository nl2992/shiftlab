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


---

# Update 2026-11-08: SAES pivot outcome and EQSDp viability

## SAES (signal-assisted economic switching): FAIL at Phase 1

See [SAES_PHASE1.md](SAES_PHASE1.md). On 11 feature-bearing development streams:
- **Per-event proxy information is too weak.** The confidence gap predicts the correct model
  on disagreements with AUC .50–.78, but it is worth only 1.00–1.13× labels (median 1.04).
- **Staleness signals do not anticipate advantage changes.** For drift, disagreement-rate and
  score-gap changes, pooled |r| ≤ .08.
- **The price of information is low.** +100% free labels is worth 5.3 units to tuned Wald, so
  the proxy channel is bounded at ≤0.7 units.

Phase 2–5 were not started, per the directive's stop rule and the user's 2026-11-08
instruction. No sealed seed or dataset was consumed.

## Is the original EQSDp paper still viable? Assessment

**What the evidence supports**
1. **Adapter gains.** Confidence-bound reversible payback switching under hard, delayed,
   disagreement-only label budgets (EQSDp ≡ Wald-LCB payback) beats the published-method
   adapters:
   - frozen C3, 100 fresh seeds, Holm: −8.8 vs tuned Gong–Zhang-style, −9.7 vs Qiu-style;
   - post-confirmation panel: −30 vs UPF-style.
2. **Real-stream transfer of the registered contrast.** On exposed real streams the C4
   contrast (vs tuned Gong–Zhang-style) holds on 13 of 14 streams (pooled −5.7). This is
   development evidence only.
3. **Analysis results (new, robust).**
   - The fixed-discount confidence-bound rule is frontier-efficient against 12 adaptive
     alternatives.
   - The problem is information-limited: change-time knowledge is worth 11.7 units, +100%
     labels 5.3, and observable unlabeled signals ≤0.7.
   - M5: memory tuned on change-heavy streams transfers badly to serially dependent real
     streams (EQSDp-B is +6 vs long-memory Wald on exposed streams).

**What it does not support**
- A new algorithmic primitive. The rule is a confidence-bound horizon-pays rule. Regol et al.
  2025 (UPF) and *The Challenger* (arXiv 2512.18390) constrain the novelty; both must be read
  in full.
- Superiority over native published algorithms. The comparators are common-contract adapters.
- Best real-data configuration. A differently tuned Wald (λ=.97) beats the frozen arm on
  exposed streams. Per the user's instruction the sealed C4 protocol is **not** amended to
  chase this.
- C4: only 2 sealed eligible sources exist (austin_animal, la_crime). Reaching ≥8 needs at
  least 6 more eligible builds from the registered candidate list.

**Viability verdict**
- As an ICML main-track *algorithmic* paper: **weak**. The method is a NOVEL-INTEGRATION of
  known parts with modest gains over the strongest simple baseline (tie with Wald).
- As a scoped contribution, the strongest honest paper is a **methods-plus-analysis** paper.
  Its message: "In budgeted, delayed model replacement, a simple confidence-bound payback
  switcher is (empirically) near the achievable frontier, and the remaining gap is
  informational: neither adaptive evidence processing nor observable unlabeled signals recover
  it."
  - Primary evidence: C3 (vs adapters) plus the registered C4 (vs tuned Gong–Zhang-style,
    arm B frozen).
  - Analysis section: the frontier and information-bound results, and M5.
  - Venue: TMLR or a workshop is more realistic than ICML main track. An ICML submission would
    rest on the analysis being judged a contribution.

**Programme status:** C1 PASS (M1–M5). C2 new-method NOT ACHIEVED (SAES and 12 label-only
mechanisms closed). C3 historical PASS only. C4 NOT STARTED (2/8 sealed eligible). **INCOMPLETE.**
The remaining executable work for the scoped paper is the C4 acquisition (≥6 more eligible
sources) and its single sealed opening under the existing registration.

---

# Update 2026-11-08 (late): BCR pivot and C4 opening

- **Multi-model BCR: feasibility FAIL.** BCR ties tuned K-Wald (+1.15 [−1.37, +3.66]). See branch
  `research/multimodel-bcr-2026-11-08`, `docs/multimodel_bcr/`.
- **C4 (registered, opened once): NOT PASS under the registered rule**, with 5 of 9 datasets
  supporting. Against the tuned Gong–Zhang-style adapter, arm B is cheaper on 9 of 9 datasets
  (sign test p = .002); pooled vs the Qiu-style adapter −8.1 (p = .0003). The effect is small:
  pooled −3.7 per episode (−0.8% of cost), driven by halved switching where the comparator
  churns. On 3 datasets never-switching is best. See [c4_results.md](c4_results.md).

**Programme status:**

| | Status |
|---|---|
| C1 | PASS (M1–M5, plus K-model observations) |
| C2 | new method NOT ACHIEVED; base rule = NOVEL-INTEGRATION |
| C3 | historical PASS vs adapters |
| C4 | NOT PASS (5/9; uniform direction, small effect) |

Overall: **INCOMPLETE.** The honest scoped paper is a methods-and-analysis paper. Its message:
a confidence-bound payback switcher is consistently, but only slightly, better than a tuned
point-estimate economic switcher on real streams, and the remaining headroom is informational.
Venue: TMLR or a workshop.
