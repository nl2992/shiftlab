# Publication Opportunity Register (SOTA sprint, 2026-11-03)

This register follows the publishability addendum. Main-track contribution potential (A) and SOTA performance (B) are assessed separately.

All numbers come from the sprint validation files in [validation/](validation/). Status uses three values: PROMISING, NEEDS EVIDENCE and NOT SUPPORTED. The result-to-claim review in [aris/](aris/) may revise these.

---

## P1. A restart-mixture label-clock monitor that transfers across certified deployment methods (RMM)

* **Research question.** Certified (anytime-valid) deployment gates stop measuring once they reach a verdict, and they dilute late evidence with early evidence. Can a single attachable module fix late-improvement latency for any certificate host?
* **Insight / mechanism.**
  * The module runs a Shiryaev-Roberts-style restart mixture of label-clock e-processes. It works on query-conditional, unweighted outcomes.
  * It keeps acquiring labels after the host's verdict.
  * When it alarms, it switches deployment and restarts the host. The alpha is split between host and detector.
* **Closest prior art.**
  * E-detectors (Shin, Ramdas and Rinaldo); Saha and Ramdas.
  * Data-efficient quickest change detection (Banerjee and Veeravalli).
  * The certified hosts: Karampatziakis et al. 2021, DISCERN, SMCS.
* **Exact difference.** The module attaches to an arbitrary certified deployment host, on the label clock, under a shared hard label budget. It continues acquiring after the verdict and restarts the host. No paper evaluates restart detectors as a deployment add-on across certificate families.
* **Evidence.** All results are on fresh seeds, after the DISCERN `/4` fix ([transfer_results.md](validation/transfer_results.md), [rmm_certified_hosts.txt](validation/rmm_certified_hosts.txt)).
  * Host+RMM minus host on the registered family:
    * gated −44.2 [−46.9, −41.4]
    * corrected DISCERN −47.3 [−49.8, −44.8]
    * SMCS −13.3 [−16.0, −10.6]
  * Independent-null first-promotion safety holds on all three hosts (Wilson upper bound ≤ .0936 at 1000 seeds).
  * Late improvement vs the best certified published method (Xu) is −15 to −27 per episode for every certified host, on V_late_600 and W_late_1000.
  * Family mean vs strong baselines (gated+front, QCE+front, P7s, A5b) is −2.4 to −7.3.
  * Ablations: the restart mixture contributes −2.4 to −5.5 and continued acquisition −8 to −11.
* **Adverse results.**
  * Registered HR fails at 3/5 hosts. Model Picker and CAMS have no certificate for RMM to improve: their null promotion is .94 to .95 with or without RMM.
  * Reversal and recurrence cost +20 to +37 vs the best certified method.
  * Strong stationary improvement costs +9 to +34 vs front-loaded EB.
  * The ρ=.8 Markov null gives .15 and ρ=.95 gives .66 to .70.
  * On fresh real data RMM is much better than its host (gated: −48 to −156) but mixed vs the best certified method (2 wins, 3 losses). The fresh streams contain no late-improvement episode.
* **Deviation to disclose.** Restricting the transfer claim to certificate hosts was decided after the registered 5-host HR failed. It is therefore a post-hoc scope, even though RMM's design rationale (adding monitoring to a certificate) predates it.
* **Necessary additional evidence.**
  1. A registered fresh test restricted to certificate hosts, adding a fourth certificate family (e.g. choe_ramdas_eb or gated_adaptive_range).
  2. Real streams with a genuine within-stream improvement, e.g. a challenger retrained on recent data that overtakes the incumbent.
  3. Fixing or bounding the reversal cost, with B2-style certified rollback.
  4. A formal statement of the joint error of promote then rollback.
* **Positioning.** A transferable extension (addendum type 1) and failure-guided design (type 4), with a scoped SOTA in the late-improvement regime (type 3).
* **(A) Main-track potential:** moderate. Novelty is incremental (composition of e-detectors). The transfer across three independent certificate families plus the latency diagnosis gives it a coherent story.
* **(B) SOTA:** scoped, synthetic only. Late improvement beats the strongest certified published method by 15 to 27; nothing broader.
* **Assessment: PROMISING (needs evidence items 1 and 2).**

## P2. Certified deployment under serial dependence: failure map and an impossibility-flavoured trade-off (Failure Atlas plus persistence study)

* **Research question.** Do anytime-valid deployment gates keep their false-promotion guarantee when label outcomes are serially dependent, as they are in real time-series streams? What does a dependence-robust certificate cost?
* **Main finding.**
  * Every certified published port that has power exceeds the .0936 bound on a persistent marginal null. Run at 1000 seeds each:
    * Xu: ρ=.9 .117, ρ=.95 .239
    * SMCS: ρ=.8 .097, ρ=.95 .350
    * gated_adaptive_range: ρ=.95 .112
    * DISCERN floor: ρ=.95 .110
    * Choe–Ramdas-style EB: ρ=.95 .213, front-loaded ρ=.8 .116
    * QCE-betting: ρ=.95 .232
  * The two that pass, original gated deployment and corrected DISCERN, almost never promote. A5b cost-dominates them on all 6 stationary alternatives.
  * A gap-indexed sequential-universal-inference certificate (A1b/A5b) holds the bound for every ρ ≤ .95. It also holds on two out-of-class nulls (.048, .018). Its stationary cost is within +7.4 of the cheapest unsafe certified method.
  * But it loses all power on real time-series streams. Fresh real data: +61 to +257 vs the best certified method. On metro it costs +99 with 0/16 episodes better, even though the challenger error is .047 vs .36.
  * The mechanism is measured persistence: ρ̂ of .4 to .8 on the fresh streams, and up to .98 on exposed streams.
  * This sits alongside the shared certification-latency diagnosis (M1, uniform pacing under a binding budget) and the churn of uncertified selectors (M2, 64 to 100% null promotion).
* **Closest prior art.**
  * Choe and Ramdas 2024; Henzi and Ziegel 2022. These control the time-averaged *conditional* mean, so a promotion in a persistent run is correct for their null.
  * Universal inference (Wasserman, Ramdas and Balakrishnan 2020).
  * Markov e-detectors.
* **Exact difference.**
  * The atlas measures marginal false promotion of deployment gates under controlled persistence, on one common budgeted, delayed simulator, against 13 published methods. It also shows the conditional-vs-marginal null distinction has decision consequences.
  * A gap-indexed Markov UI certificate for actively queried outcomes; the novelty audit found no prior use of it.
* **Necessary additional evidence.**
  1. A short formal argument that, under unknown persistence, any test valid for all ρ ≤ 1 needs evidence that grows with run changes rather than with labels. This would turn the trade-off into a lower bound.
  2. Real streams with a known null, e.g. two equally accurate retrained models, to measure real false-promotion rates.
  3. Author-code comparators where available.
* **Positioning.** A new evaluation methodology plus a substantive empirical finding (addendum types 5 and 6), possibly a datasets-and-benchmarks track.
* **(A) Main-track potential:** moderate to good as an empirical paper, if the lower-bound argument holds.
* **(B) SOTA:** A5b is the lowest-cost method among those that hold the bound at ρ ≤ .95 on synthetic data. It is not SOTA on real data.
* **Assessment: PROMISING (needs evidence item 1).**

## P3. A shared deploy-or-abstain gate for fast online model selectors (Family D)

* **Research question.** Can fast uncertified selectors (Model Picker, CAMS, Model Selector) keep most of their economy once an anytime certificate is required before deployment?
* **Mechanism.** The host ranks and queries. Promotion requires a started-mixture e-process on query-conditional outcomes. Gate queries are added only while the host is undecided.
* **Evidence.**
  * Native null promotion of 64 to 100% falls to .014 to .016 on V_null for all three hosts at 1000 seeds.
  * Fresh real data, D2 (CAMS) vs the best certified method:
    * beijing −33.2 (13/14 episodes)
    * bike −6.1 (5/6)
    * metro −2.7 (14/16)
    * household −2.8 (11/20)
    * appliances +1.4
* **Adverse results.**
  * Registered HD fails. Holm-significant wins vs the best certified method number 0, 2 and 2 of 5.
  * D2's first-validation 4/5 did not replicate on new seeds.
  * ρ=.8 null promotion is .20 to .23.
  * Real gains are consistent only on the CAMS host.
* **Closest prior art.** Composition of published gates (Karampatziakis et al. 2021) with published selectors. The novelty audit judged it composition.
* **(A) Main-track potential:** low as a method. It is useful as the M2 benchmark finding inside P2.
* **(B) SOTA:** not established.
* **Assessment: NEEDS EVIDENCE, leaning NOT SUPPORTED as a standalone paper.**

## P4. Certified rollback (B2/B5)

* **Evidence.** Reversal cost vs host: B2 −8.9 and −8.4; B5 −12.0 and −17.8 (fresh seeds).
* **Adverse results.**
  * One host only, in the RMM line, which fails ρ=.8.
  * Reversal is still +20 or more vs the best certified method (discern_style), because that method never promotes.
* **Assessment: NEEDS EVIDENCE.** Best used as P1's fix for reversal cost.

## P5. FLQ/QCE/QSG front-loading, adaptive density, shadow pricing (A2, A3, C1 to C6)

* **Evidence.** Earlier Atlas v2 work: stationary gains bought with dependence-safety failure (QSG at ρ=.95: .696). The C family gives no replicated gain; C2's development gain did not replicate.
* **Assessment: NOT SUPPORTED** as contributions. Kept as negative results within P2.

## P6. LRMD (standalone restart monitor)

* **Evidence.** Earlier registered null-safety failure. In the transfer run it is cheaper than gated+RMM on the family (+5.0 for gated+RMM vs LRMD), but its nulls were not re-tested here.
* **Assessment: NEEDS EVIDENCE.** One fresh 1000-seed null run would decide it.

---

## Ranked recommendation for paper development

1. **P2** as a benchmark/empirical paper: certified deployment under dependence. It has the broadest finding, every number is on fresh seeds, and its real-data relevance was measured.
2. **P1** as a method paper on transferable restart monitoring for certified deployment. Run its two missing experiments first.
3. Fold P3 to P5 into P2 as findings and negative results.
