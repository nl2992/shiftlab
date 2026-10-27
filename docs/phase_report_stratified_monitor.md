# Stratified decision-harm phase: checkpoint pending

This report is in progress. No checkpoint has been reached and no confirmation
study is authorised. The stratified and data-efficient algorithm branches both
stopped at their prescreens; WP1 must finish before checkpoint B can be declared.

| Work package / gate | Current result | Evidence |
|---|---|---|
| WP0 protocol/panel housekeeping | Complete | [Execution record](stratified_monitor_phase_execution.md), committed protocols and paper-to-code audits |
| WP1 S0 implementation | Passed | [Implementation checks](gated_monitor_implementation_results.md) |
| WP1 S1 fidelity | Passed: 6/60 at 96.9; 47/60 at 45.9 | [Fidelity receipt](gated_monitor_fidelity_results.md) |
| WP1 smoke | Passed integrity, excluded from inference | [Smoke and runtime receipt](gated_monitor_smoke_results.md) |
| WP1 S2 calibration | Passed: primary and all panel arms below 5% simultaneous upper bound | [Null calibration](gated_monitor_null_calibration_results.md) |
| WP1 S3 comparison | Running on the disjoint registered block | [Frozen WP1 protocol](gated_vs_ungated_monitor_comparison_protocol.md), `outputs/gated_monitor_compare/launch.json` |
| WP2 G0/theory | Standard subgroup composition identified; no priority claim | [Novelty audit](../papers/shiftguard_unified/novelty_audit.md), [theory](../papers/paper1_decision_drift/theory_notes.md) |
| WP2 G1 | Failed; stop before development/calibration | [Analytic results](stratified_growth_prescreen_results.md) |
| WP3 G0/theory | Complete with scoped independent algebra check | Novelty audit and theory note above |
| WP3 prescreen | Failed; stop before development/calibration | [Frozen WP3 protocol](data_efficient_edetector_prescreen_protocol.md), [prescreen results](data_efficient_edetector_prescreen_results.md) |
| WP4 local inventory | Complete; real-data validity experiments not run | [Local source inventory](live_data_inventory_stratified_phase.md) |

## What the negative stratified result means

Across 20 learner slices and the full registered analytic grid, the candidate and
equally equipped subgroup composition agree to 4.4409e-16. The largest growth ratio
against the strongest applicable incumbent is 1.0000, below 1.5. Gains over a pooled
monitor cannot establish a method contribution when the subgroup monitor tests a
stronger intersection null. This phase will preserve the estimand distinction and
allocation formulas as benchmark findings rather than claim a new subgroup test.

No stratified detection probability, simulated delay, intersection-null calibration
or real-data result is available: the registered gate deliberately stopped those
runs. The analytic table is not a measured detection leaderboard. No 588/589 or
reserved 591 block was used.

## What the negative data-efficient result means

The registered 20-seed late-onset screen retained all 39,200 rows in the composed
panel. At the primary 75%-onset, 5%-budget cell, the canonical adaptive controller
with fixed-stake SR detected 11/20 streams (55%; Wilson 95% interval 34.2%–74.2%),
with mean censored delay 488.35, 48.05 labels and $71.50. The strongest simple
registered temporal policy configurations detected 20/20; fixed-stake started
evidence had mean delay 172.20, 110.40 labels and $165.59. The candidate conserved
resources but missed both the +10-point and 1.5x-delay primary margins against
those incumbents. It also failed the registered comparison rule in all seven
secondary cells. WP3 therefore stops before development, null calibration or
confirmation. These alternative-only results establish neither false-alarm
control nor a confirmed power difference.

## Comparator and reporting contract

The final WP1 and WP3 reports must list every registered arm/cell with its null,
information budget, betting engine, detection interval, censored delay, labels,
dollars, validity status and source fidelity. All registered tables, including ties,
losses and failed-calibration arms, must remain available. A primary endpoint
against uniform PPI in WP1 verifies the published gating mechanism; it does not
establish superiority over the complete composed panel.

PPE and Xu source-factor aliases retain their published-factor checks; shared
gating/betting compositions are adaptations. Timans engines are affine paired-cost
adaptations. Full feedback is label unmatched. Feature ADWIN tests feature change,
not harm. Same-null subgroup composition belongs to the intersection panel;
Comparecast's weak null, PPRM's predictive-risk target and Q2 promotion methods
are excluded from pooled-harm ranking for the stated target mismatch. These
exclusions cannot be converted into claims that the methods are generally weak.

## Live status and confirmation boundary

The local EIA demand snapshot ends 2026-10-19T18:00Z; its receipt/hash is verified.
No frozen real-data policy/model-weight bundle exists, so no prospective clock
has started and no prospective observations, per-path null pass, injected-harm
result or confirmation-window completion date is claimed. The local inventory
and its limits are linked above. Checkpoint A's real-data minimum is unsatisfied.

Any future confirmation would first need a justified candidate, separate development
and null calibration, a frozen full panel and primary cell, exact matched-resource
rules, simultaneous null accounting, per-path real-data orientation checks and
untouched data. Only then could a new protocol allocate the reserved 59100000–59100999
block. The final decision must apply the +10-point or 1.5x delay primary margin,
the -3-point secondary margin, and the required paired uncertainty. No such run
is part of this phase.

## Remaining limits

Twenty alternative seeds in WP3 can screen a policy but cannot confirm efficiency
or null validity. Exact working-law growth in WP2 is conditional on imposed laws
and fitted pilot slices. Prior-art searches are bounded and establish no priority.
Synthetic conditional-null arguments do not establish real-data causal utility
or historical publication availability. The complete regression suite and run
artifact audits remain required before final results are committed.

Ponytail's source skill was applied without global installation. PaperBanana's
author/community repositories were inspected; the pinned environment has no
working PaperBanana/API configuration. No research figure was generated and no
alternative visual generator was substituted. Tables carry the current evidence.
