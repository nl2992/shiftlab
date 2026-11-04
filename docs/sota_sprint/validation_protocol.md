# SOTA sprint: locked validation protocol

Locked 2026-11-03, after the 24-candidate development screen and before any validation run. The
validation regimes and seeds were registered earlier in `scripts/sota_sprint/validation_spec.py`
(commit 39d25ce, before any family reported). Nothing below may be changed after the first
validation row is written; deviations are reported as deviations.

## Seeds and data
* Synthetic: seed base 2026110601, 100 paired seeds per regime, regimes `VAL_REGIMES` (13 Atlas v2
  V_* instances, which had only been run with base 2026110399, plus 8 new W_* instances).
* Null safety: seed base 2026110602, 1000 seeds on each regime in `NULL_REGIMES`
  (V_null, V_worse, V_null_dep_r5, V_null_dep_r8, W_null_dep_r9, W_null_dep_r95, W_worse_dep_r8).
* Real data (secondary, descriptive): the nine cached streams with episode-level inference and 20
  policy seeds at base 2026110603. These streams were exposed in Atlas v2 development; no real-data
  SOTA claim can be made from them.

## Advanced candidates (at most two per family, chosen from development evidence)
| family | candidates | host / control |
|---|---|---|
| A | A5b, A1b | QSG; A1b is A5b without adaptive density |
| B | B2 | rmm:gated_deployment+RMM |
| C | C2, C6 | gated_adaptive_range+front, gated_adaptive_range+pace_tuned |
| D | D1, D2 | model_picker_adapter, cams_adapter |
| combinations | chosen from the combination screen by the rule in H4 | as in the combination ledger |

## Comparators
* Certified published (`bench.CERTIFIED_PUBLISHED`): gated_deployment, gated_adaptive_range,
  gated_adaptive_range+front, discern_style (corrected), discern_design_floor,
  SMCS+retain-incumbent, xu_acquisition_only. Also the Choe-Ramdas-style EB comparators
  choe_ramdas_eb and choe_ramdas_eb+front, which are added to the certified class for every
  validation contrast.
* Uncertified published: model_picker_adapter, model_selector_causal, online_llm_picker,
  cams_adapter, variance_min_ipw, gong_zhang_paid_obs, qiu_delayed_movement, ryabchenko_capacity.
* Internal (never "SOTA"): QSG, QSG-env8, gated_deployment+QCE+front, RMM, LRMD, P7s. Control:
  never-switch, economic_replacement.
* "Strongest applicable comparator" = the comparator in the stated class with the lowest mean cost
  on that regime on the same seeds (selected after the fact, conservative for the candidate).

## Hypotheses
**H1, primary (reliability at matched cost; A5b).** All three parts must hold:
1. (Safety) A5b's promotion rate is <= .0936 on every NULL_REGIMES regime over 1000 seeds.
2. (Comparator failure) Every certified published comparator, including both Choe-Ramdas-style
   ports, has a promotion rate above .0936 with Wilson 95% lower bound above .05 on at least one
   NULL_REGIMES regime. Otherwise H1 is restated against the comparators that pass.
3. (Non-inferior cost) On the iid stationary alternatives {V_better_a, V_better_b, V_better_c,
   V_near, W_delay600_better}, the upper 95% bound of J(A5b) - J(strongest certified published)
   is <= +5 on at least 4 of 5 regimes. The margin is 5 cost units per 2000 events, about 1.3% of
   cost.
   
   Known dev losses are declared and reported but are not part of H1: V_bursty; dependent
   alternatives V_dep_better_r5, W_better_dep_r7, W_better_dep_r9; change regimes V_late_600,
   W_late_1000, V_reversal_1000, W_reversal_700, V_recurrent.

   If H1 holds, the claim is: "the only method in the comparison whose false-promotion rate stays
   within the registered bound under persistence up to rho = .95, at cost non-inferior to the
   strongest certified published method on iid stationary alternatives."

**H2 (cost superiority; secondary).** Holm-adjusted paired Delta J < 0 against the strongest
certified published comparator, over the 5 iid stationary regimes above, for A5b, D1, D2, C2 and
C6 (one Holm family per candidate). A cost superiority claim for a candidate is admissible only if
that candidate also meets H1-part-1 safety; otherwise it is reported as "cheaper but unsafe".

**H3 (mechanism attribution).** For each of A5b vs A1b (adaptive density), B2 vs its host on
V_reversal_1000 and W_reversal_700 (rollback), and D1 vs model_picker_adapter on nulls, report the
paired difference; this is descriptive.

**H4 (combinations).** A combination advances to validation only if, on the 20-seed combination
screen, its 95% CI vs its parent is below 0 on at least one targeted regime, with no null regime
promotion above 2/20. Advanced combinations are tested under H1/H2 exactly as A5b.

## Verdict rule
`SOTA_MET` requires H1 (or H2 with safety) for at least one candidate on fresh synthetic seeds,
plus a successful independent result-to-claim review of that exact claim. Real-data evidence on
exposed streams is descriptive. The task's success gate requires independent real-data validation
for a real-data claim, so any SOTA verdict is scoped "synthetic, under the declared Markov
dependence class".

## Amendment 1 (2026-11-03, before any validation row was read)
A strict re-read of the brief (Phase 6: "at least the strongest two candidates per family should advance
where functioning candidates exist") found Family B had only one advanced candidate. B5 (largest
reversal gain vs host in development) is added as B's second candidate. It runs in a supplemental job on
the same validation seed bases and regimes (streams are keyed by seed base, regime and seed, so rows pair
with the main run by seed). It is evaluated under H3 (vs host on change regimes) and the H1-part-1 safety
check. The two other changes are bookkeeping: the gate re-screen of all 24 at the committed revision
(Phase 5 traceability) and the fresh real-data protocol (`fresh_real_protocol.md`, external validation).

## Amendment 2 (2026-11-03, before any validation row was read)
This amendment responds to the milestone 1-2 review (`review_milestone12.md`). The lead confirms that no
validation record, log line or summary had been opened when it was committed. It supersedes H1 and H2
where they conflict. Every original metric is still reported.

* **O1 (stop rule carried over; claim wording).**
  * **H0 restores the Atlas v2 registered stop rule verbatim** (Atlas v2 report section 9):
    * Test a persistence-robust certified variant (A5b; A1b as its density-off control) against
      xu_acquisition_only and tuned non-uniform pacing (gated_adaptive_range+pace_tuned).
    * Success requires promotion <= .094 at rho=.8 and rho=.95, and paired CI < 0 against the stronger
      of the two baselines on >= 4 of the 6 stationary alternatives {V_better_a, V_better_b, V_better_c,
      V_dep_better_r5, V_near, V_bursty}. **If H0 fails, no cost-SOTA claim is made for A5b.**
  * The H1 claim no longer says "only".
  * H1 part 2 is replaced by a Pareto statement. Every certified published comparator must either
    (a) fail a NULL_REGIMES null, meaning point rate > .0936 and Wilson 95% lower bound > .05, or
    (b) be cost-dominated by A5b, meaning the 95% upper bound of J(A5b) - J(comparator) is < 0 on
    >= 3 of the 6 stationary alternatives above.
  * Every comparator is listed with its status.
* **O2 (class dependence).**
  * Any safety claim names the class: a stationary first-order homogeneous Markov sign in event time,
    with p <= 1/2 and any rho, independent of disagreement arrivals, under constant delay.
  * Two out-of-class nulls (`ooc_regimes.py`) run descriptively at 1000 seeds, base 2026110605, for
    every candidate and certified comparator. They are reported next to the in-class nulls; they are
    not part of H1.
* **O3 (bursty).**
  * Part 3 is also reported as k/6 including V_bursty.
  * If A5b is not non-inferior on V_bursty, the claim is restricted to Bernoulli (non-bursty)
    disagreement arrivals.
  * The claim states that A5b has near-zero power against persistent alternatives.
* **O4 (harm).** Every null reports harm: mean J minus never-switch J. Promotion rate alone is not
  treated as harm.
* **O5 (comparators).**
  * choe_ramdas_eb is documented as the query-conditional PrPl-EB port (= DiscernQCE); it is not
    author code.
  * The betting-CS query-conditional ports gated_deployment+QCE and gated_deployment+QCE+front join the
    certified comparator class as a supplemental run on the same seeds.
  * The IPW betting form is discern_style/gated_adaptive_range (already in the class).
  * Waudby-Smith et al. 2022 is NOT implemented, a recorded gap.
  * RESULTS.md's statement about rho=.95 is corrected.
* **O6 (X_A5C).** X_A5C may be claimed only if it beats A5b (paired CI < 0) on its targeted regimes
  V_late_600 and W_late_1000.
* **O8.** H1 part 1 uses the Wilson 95% upper bound <= .0936, not the point estimate.
* **O9.**
  * H1 parts 1/3 and H2 are evaluated for X_A5C and B5 as well.
  * H2 success for a candidate = Holm-adjusted p < .05 on >= 4 of 5 iid alternatives AND H1 part 1
    safety.
* **O10, O12, O13, O14 (recorded caveats).**
  * O10: the Family C held-out seeds share the null-check base and were used to pick C6.
  * O12: four of the five part-3 regimes were exposed in Atlas v2, although with other seeds.
  * O13: B2 and Family C constants come from generator design knowledge.
  * O14: D's host-AND is inert.
* **O11.** B5 is advanced only to satisfy Phase 6's two-per-family requirement; Family B recommended
  stopping it.

## Amendment 3 (2026-11-03): RMM transferable-extension test (publishability addendum)

Registered before any sprint validation row was read. The test uses fresh seeds, so it is independent
of the sprint validation rows. Every earlier RMM result predates the DISCERN PrPl-EB `/4` fix. The
`rmm:discern_style+RMM` factory now wraps the corrected `DiscernStyleStop`.

**HR (transfer).**
* Hosts: gated_deployment, discern_style (corrected), SMCS+retain-incumbent, model_picker_adapter and
  cams_adapter, each also run with RMM attached.
* Primary family, the change-and-stationary-improvement regimes the RMM claim was made on:
  {V_late_600, W_late_1000, V_better_a, V_better_b, V_better_c, V_near}.
* Statistic: the per-seed family mean of J(h+RMM) - J(h).
* Seeds: 100 fresh synthetic seeds, base 2026110606.
* HR passes if the 95% CI is below 0 for at least 4 of the 5 hosts, and first-promotion safety holds
  under the iid conditional null. Safety means the Wilson upper bound is at most .0936 on V_null and
  V_worse over 1000 seeds (base 2026110607).
* The ρ=.8/.95 Markov nulls are reported as known out-of-scope failures. RMM's validity is stated
  under the iid conditional null only.

**HR2 (versus strong baselines, descriptive plus one test).** The same family mean is reported for the
best host+RMM against:
* gated_adaptive_range+front
* gated_deployment+QCE+front
* xu_acquisition_only
* discern_design_floor
* P7s_settled
* A5b
* the best certified published comparator, chosen per regime

The one test asks whether the best host+RMM is significantly cheaper than the best certified published
comparator on {V_late_600, W_late_1000}. Holm correction is applied over the two regimes.

**Attribution.**
* +RMM_single, which drops the restart mixture.
* +RMM_noacq, which drops continued acquisition.

## Publication track
The publishability addendum (2026-11-03) keeps two separate assessments, main-track contribution
potential and SOTA performance. They are recorded in `publication_register.md` and in the leaderboard.
They do not change any registered hypothesis above.
