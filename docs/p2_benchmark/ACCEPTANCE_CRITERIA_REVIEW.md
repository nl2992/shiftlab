# Review of ShiftLab acceptance criteria (2026-11-06)

**Status:** interpretive review. It changes no registered outcome. Every number is quoted from the
artifact named beside it; nothing was re-run. Revising a criterion after seeing results cannot make
an old result confirmatory. A revised criterion must be frozen first, then tested on fresh seeds and
untouched data.

## Summary

Most of the programme's safeguards were sound: paired designs, pre-registration, source-cluster
inference, holding methods to the null they claim, and keeping confirmation data untouched. Six of
the criteria that ended method lines were stricter than the field's norm, or measured the wrong thing:

1. **Mis-specified.** A ≤ .0936 promotion bound on dependent Markov nulls was applied to methods
   that claim only the conditional (V1) null. This bound alone rejected FLQ, even though FLQ's cost on that null
   matched its host.
2. **Unachievable as written.** Untouched real sources with *authentic* label-release clocks. Almost
   no public dataset records them.
3. **Underpowered.** Interval rules were applied with 5–20 clusters, where a method at exactly α fails
   about half the time.
4. **Binary effect bars.** A 10% gate discarded meaningful effects of 7.7–10.2% whose CIs excluded 0
   (already conceded in `promising_directions/14_FAIR_REEVALUATION.md`).
5. **Comparator selection.** The strongest comparator was chosen per regime on the same seeds. This
   biases the comparison toward the comparator.
6. **No-loss-anywhere and composition-means-stop rules.** These rule out any scoped trade-off and any
   diagnosis-plus-simple-repair paper.

Some lines failed on substance, and no criterion change rescues them: E_rb, P6 on real data, H2, the
T family, and B3+/P7s. Two lines were worth re-testing under revised, pre-frozen criteria: **FLQ (front-loaded acquisition)**, re-tested
2026-11-06 with result NOT_SUPPORTED on efficacy while passing both validity tiers, and **P3b's insurance profile** (not yet re-tested).

## Criterion-by-criterion

| # | Criterion and where it was used | Verdict | Evidence | Proposed revision |
|---|---|---|---|---|
| C1 | 10% net-cost reduction as a pass/fail gate (Oct 30 master prompt; `FINAL_RESEARCH_REPORT.md`) | **Too strict** (already conceded) | P3b: −7.7% to −10.2% vs best simple policy, CIs exclude 0; −36.7% to −40.5% vs never-switch when the challenger is useful (`14_FAIR_REEVALUATION.md`) | Graded rubric from doc 14, plus a practical margin stated in cost units before the run |
| C2 | Promotion ≤ .0936 on **every** null, including ρ=.8/.95 Markov nulls, for V1-claiming methods (Atlas v2 Amendment 2; `sota_sprint/benchmark_spec.md`) | **Mis-specified** | The protocol itself notes the pointwise conditional null is *false* on V_null_dep_r8. FLQ (gated+QCE+front) promoted .16 there and was declared uncertified. Its paired cost vs host on that same null was **−0.5 [−2.5, +1.8]**; for gated_adaptive_range+front it was −0.4 [−2.1, +1.5] (`failure_atlas_v2_flq/results/validation_synthetic.md`). WP2 H2: V1 promotions on real twin nulls are conditionally informed: mean remaining advantage .0122 [.0063, .018] (`sprint2/wp2/amended_no_xu_pool/results.json`) | **Two tiers.** (a) Hard gate: promotion ≤ bound on the null the method *claims*. (b) Reported, with a pre-declared tolerance: dependent-null promotion rate **and** all-in excess cost vs never-switch. Apply a hard V2 gate only to methods that claim V2. |
| C3 | "Strongest published comparator" = lowest cost per regime, chosen on the same seeds (Atlas v2 secondary; SOTA sprint) | **Strict and biased toward the comparator** | Takes the minimum over 5–6 ports per regime on the scored seeds (the report notes it "favours the comparator") | Pick the comparator on development seeds, or use a simultaneous max-statistic bootstrap over the port set (already done for P6) |
| C4 | No loss in late, reversal or recurrent regimes (counted against FLQ and RMM) | **Too strict** | Promoting earlier must cost something under reversal. FLQ: +35.6 [+29.5, +41.0] on V_reversal_1000, but −19.5 on V_recurrent and −6.6 to −123.9 on stationary improvements | Declare the region of applicability before confirmation and report losses outside it in the headline table. Reviewers will still ask whether that region is recognisable online, so answer that directly |
| C5 | Composition of known parts ⇒ stop (novelty audits; scoped research C3) | **Partly too strict** | Fair for a "new algorithm" claim; front-loading equals DISCERN with π=1. Too strict for a diagnosis paper: Atlas v2's diagnosis (published certified methods leave the hard-budget acquisition layer unspecified; uniform pacing costs 6–124 units) is a finding even though the fix is simple | Allow a "diagnosis + simple repair" framing: the novelty is the measured failure and its cause, with prior art cited |
| C6 | ≥ 2 untouched independent domains with **authentic** train/predict/label-release chronology (scoped research C4) | **Unachievable as written** | Wild-Time audit: benchmark releases give event clocks, not label-release clocks (`scoped_method_research_2026-11-06/WILDTIME_FEASIBILITY.md`, unmerged branch). No such source exists locally | Keep "untouched" (fair and achievable). Replace "authentic clocks" with imposed delays swept over a grid, plus one source with an external publication clock (OPSD/ENTSO-E) as a case study |
| C7 | Upper 95% bound ≤ .0936 with ~20 split clusters (H1b; P6 twin-bike screen) | **Bar fair, design underpowered** | P6 bike .076 [.036, .122]; A5b bike .125 [.058, .192]. The half-width at this cluster count (~.04–.07) matches or exceeds the .0436 slack, so a method whose true rate is exactly .05 fails roughly half the time | Keep the bar and power the study (≥ 60 splits per dataset), or test H0: rate ≥ .0936 with a stated power |
| C8 | WP1 late-improvement CI rule vs the selected best certified comparator | **Underpowered** | 10 late episodes across 5 source clusters (`sprint2/EXIT_AUDIT.md`) | Report as *inconclusive*, not "not supported"; require a power analysis before registering a cluster-level rule |
| C9 | Sprint success only when every brief item is done (user rule of 2026-11-03) | **Right for process, wrong as a science verdict** | External human review, two candidates per family and PaperBanana figures are process items | Keep it for "is the sprint complete", and report a separate science verdict |
| C10 | Anytime-valid conditional excess-cost null under general dependence (charter, Paper 1) | **Impossible in general** | Testing a mean over unrestricted dependent classes falls under known non-existence results (Bahadur–Savage; cited in `sprint2/wp2/BENCHMARK.md`) | Use a declared dependence class (mixing or Markov order) and state the guarantee within it |
| C11 | P3b stopped after tying an untuned fixed-sample batch test (Lane B) | **Unfair comparator** | The batch test's error control was not established (`14_FAIR_REEVALUATION.md`, F1 caveats) | Compare against a batch test calibrated to the same false-promotion level |

## What re-opens, and what does not

| Line | Re-open? | Why |
|---|---|---|
| **FLQ / front-loaded acquisition** (Atlas v2) | **Re-tested 2026-11-06: NOT_SUPPORTED** | Registered two-tier re-test ([results](results/FLQ_TWO_TIER_RESULTS.md)). It passes both validity tiers: on every dependent null its cost is at or below its host's, despite 2–4× more promotions. It fails efficacy, beating all six certified comparators in only 2 of 6 new instances; SMCS+retain-incumbent and the Xu composite block the rest. Stop the repair claim; keep it as benchmark evidence |
| **P3b insurance profile** (Lane B) | **Yes, cheaply** | Needs a calibrated batch-test comparator (C11); otherwise a benchmark row |
| E_rb rollback | No | Costs more than never-switch in all three pilot regimes and matches B2 exactly (scoped research, 2026-11-06) |
| P6 / LRMD | No | Loses to its parent on the 14-source real replay (+24.41) |
| H2, R5, T family | No | Losses on real cost or elevated null promotions, independent of the gates |
| B3+ / P7s | No | Loses to the published suite (`research/b3-generalisation-icml`) |

## Safeguards to keep unchanged

Hold each method to the null it claims. Use paired designs and source-cluster inference. Freeze
hypotheses before confirmatory runs. Use untouched data for confirmation. Never fabricate. Never
present empirical null rates as guarantees.
