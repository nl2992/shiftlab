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
