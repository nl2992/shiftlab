# Stratified decision-harm phase: checkpoint B (evidenced NO-GO)

**Final status, 2026-10-27: checkpoint B.** The phase ends with an evidenced NO-GO
for a new Paper 1 monitoring algorithm. No confirmation study is authorised. The
stratified (WP2) and data-efficient (WP3) branches stopped at their registered
prescreens; the ADG anchor stopped at its analytic screen; WP1 S3 passed both
co-primary endpoints but its gains come from published mechanisms (DISCERN-style
gating plus published betting engines); and WP4 met the real-data validity
minimum. All three conditions of the
[algorithm-search exit ledger](algorithm_search_exit_ledger.md) are met. The
findings go to the benchmark manuscript, not to a method claim.

| Work package / gate | Current result | Evidence |
|---|---|---|
| WP0 protocol/panel housekeeping | Complete | [Execution record](stratified_monitor_phase_execution.md), committed protocols and paper-to-code audits |
| WP1 S0 implementation | Passed | [Implementation checks](gated_monitor_implementation_results.md) |
| WP1 S1 fidelity | Passed: 6/60 at 96.9; 47/60 at 45.9 | [Fidelity receipt](gated_monitor_fidelity_results.md) |
| WP1 smoke | Passed integrity, excluded from inference | [Smoke and runtime receipt](gated_monitor_smoke_results.md) |
| WP1 S2 calibration | Passed: primary and all panel arms below 5% simultaneous upper bound | [Null calibration](gated_monitor_null_calibration_results.md) |
| WP1 S3 comparison | Passed both co-primary endpoints: P1 growth ratio 7.20 (95% 6.88–7.55; rule ≥ 2); P2 100 wins / 0 losses (McNemar p = 7.9e-31). G1 prediction confirmed at all four budgets. No method claim | [S3 results](gated_monitor_comparison_results.md), [numerical amendment](gated_monitor_s3_numerical_amendment.md), [frozen WP1 protocol](gated_vs_ungated_monitor_comparison_protocol.md) |
| WP2 G0/theory | Standard subgroup composition identified; no priority claim | [Novelty audit](../papers/shiftguard_unified/novelty_audit.md), [theory](../papers/paper1_decision_drift/theory_notes.md) |
| WP2 G1 | Failed; stop before development/calibration | [Analytic results](stratified_growth_prescreen_results.md) |
| WP3 G0/theory | Complete with scoped independent algebra check | Novelty audit and theory note above |
| WP3 prescreen | Failed; stop before development/calibration | [Frozen WP3 protocol](data_efficient_edetector_prescreen_protocol.md), [prescreen results](data_efficient_edetector_prescreen_results.md) |
| WP4 local inventory | Complete | [Local source inventory](live_data_inventory_stratified_phase.md) |
| WP4 real-data validity minimum | Passed: 68/68 registered EIA null cells, 0/1,000 alarms each (largest exact upper bound 0.0030). Injected harm descriptive: fixed gating matches full-feedback delay from `r = 0.05` | [Frozen WP4 protocol](eia_real_data_validity_protocol.md), [freeze record](eia_real_data_validity_freeze.json), [WP4 results](eia_real_data_validity_results.md) |
| Algorithm-search exit | All three exit conditions met; checkpoint B | [Exit ledger](algorithm_search_exit_ledger.md) |

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

## What the WP1 S3 result means

S3 ran on the disjoint registered block 58400000–58400099 (100 streams per
scenario × budget) under the frozen protocol. One amendment applied before any
outcome was seen: a floating-point snap for a PPI increment that lies exactly on
its support bound; it changes no estimand, arm, threshold or seed.

- **Co-primary endpoints (`boundary_local_harm`).** P1: paced gated HT grows
  evidence 7.20× faster than correctly bounded uniform PPI at `r = 0.20`
  (one-sided 97.5% lower bound 6.88, rule ≥ 2). P2: at `r = 0.05` gated detects in
  100 discordant streams where uniform misses, with 0 losses.
- **Analytic prediction.** Measured growth ratios 17.5 / 20.6 / 14.7 / 7.2 at
  `r = 0.02 / 0.05 / 0.10 / 0.20` against G1's predicted 18 / 18 / 15 / 7.5, all
  within the registered factor of two.
- **Panel.** At `r ≤ 0.05`, gated arms detect 0.82–1.00 and ungated arms
  0.00–0.01. The best selective-label arms are published compositions: gated HT
  or PPI with Timans GRAPA (mean detection 0.99) and the PPE gated alias (0.99).
  The PPI proxy adds nothing over gated HT and hurts under harmful adaptation
  (0.36–0.39 against 0.50–0.59).
- **R7 prediction falsified.** Fixed gating is equal to or better than past-paced
  gating under `harmful_adaptation` at every budget (0.86 against 0.76 at
  `r = 0.10`; censored delay 370 against 1,028 under GRAPA). At `r ≤ 0.05` every
  selective arm detects at most 0.33 there, because disagreement rises from about
  9% to 42% and the reserve is exhausted.
- **Null cells in S3.** At most 2/100 false alarms in `stationary` and
  `benign_nuisance` for every arm, engine and budget. S2 remains the registered
  calibration.

The primary endpoint against uniform PPI verifies DISCERN's gating mechanism; it
does not establish superiority over the complete composed panel, and no new
mechanism appears in it.

## What the WP4 real-data result means

WP4 froze an EIA paired reserve-procurement task (frozen versus weekly-refit Ridge,
imposed shortfall/idle costs 5/1 at the 90th demand percentile, 2024 rehearsal)
before its first registered run (freeze 2026-10-27T20:58:55Z). All four paths
(CISO and ERCO, 2025 and 2026) are previously examined development windows.

- **Random-orientation null (registered).** 68/68 primary cells passed with
  0/1,000 alarms at `epsilon = 0.1`; largest exact one-sided upper bound 0.0030.
  The descriptive `epsilon = 0` boundary check peaked at 28/1,000 (bound 0.0382)
  on CISO-2026, the only path with many disagreements (150). The other three paths
  have 1–7 disagreements, so their passes carry little information.
- **Unmodified streams (descriptive).** No alarm from full feedback or any
  selective arm except `ungated_ht` at `r = 0.20` on CISO-2026 (2 of 200
  replicates). This says nothing about real operational harm; costs are imposed.
- **Injected under-procurement (descriptive positive control).** No arm alarmed
  before onset. Fixed gating matched the full-feedback median delay in all 10
  detectable cells from `r = 0.05`, with 338–701 labels per path; ungated HT was
  slower or missed. Past-paced gating degraded when injected harm created
  disagreement bursts (about 0.1% rising to 6–15%), which independently
  replicates the S3 R7 finding.

## Registered regime ledger

This ledger preserves regimes that stopped before a measured comparison instead
of replacing them with results from a different estimand or weaker comparator.

| Regime | Strongest applicable incumbent | Phase evidence | Outcome label |
|---|---|---|---|
| R1 full feedback, pooled eventwise null | Timans official GRAPA | Earlier matched benchmark found no adjusted advantage over Timans; WP1 retains full feedback only as an unmatched reference | Tie / no method claim |
| R2 selective labels, budget at least disagreement rate | Gated HT with shared adaptive engines | WP1 S3: gated arms dominate ungated; best arms are gated HT/PPI with Timans GRAPA and the PPE gated alias | Tie / no method claim (gain credited to DISCERN and published engines) |
| R3 scarce selective labels | Gated HT with adaptive engines, Xu and PPE | WP1 S3: P1 7.20x, P2 100/0 against uniform PPI; Xu active 0.00 at `r = 0.05`; ADG anchor screen added at most 1.23x over gating | Tie / no method claim; ADG stopped |
| R4 localised pooled harm | Chugg-style subgroup composition plus gating; pooled gated HT | WP2 exact growth screen: candidate/composition ratio at most 1.000 | Loss; stopped before simulated detection |
| R5 mixed-sign harm, intersection null | Chugg-style subgroup composition | Candidate and incumbent agree to 4.44e-16 | Tie; no candidate contribution |
| R6 late onset under hard budget | Horizon SR/CUSUM on gated increments and started mixtures | Candidate 55% versus temporal fixed1/started 100% in the primary screen | Loss; stopped before calibration |
| R7 harmful policy adaptation | Paced gated monitor; Timans full-feedback reference | WP1 S3: fixed gating ≥ paced at every budget (0.86 vs 0.76 at `r = 0.10`); all selective arms ≤ 0.33 at `r ≤ 0.05` | Paced incumbent beaten by fixed gating; benchmark finding, not a method (both DISCERN-style) |
| R8 live data | Same matched panel on the same paths and coins | WP4: 68/68 per-path orientation null cells pass; injected harm descriptive; retrospective development windows only | Validity minimum met; no prospective or confirmatory evidence |

## Complete leaderboards and comparator scope

The complete machine-readable tables are committed under
[`phase_tables_stratified_monitor`](phase_tables_stratified_monitor/README.md).
They retain every registered WP1 null cell, all 19,440 WP2 analytic-arm rows,
all 1,960 WP3 arm/engine/detector summaries, and every WP3 candidate-incumbent
paired comparison. Raw seed/path records remain in checksummed ignored output
directories. The WP1 S3 comparison summary (every scenario/budget/arm/engine cell)
and the three WP4 EIA tables (null cells, unmodified streams, injected harm) are
included.

| Comparator | Treatment in this phase | Reason / fidelity boundary |
|---|---|---|
| Timans official approximate GRAPA / GRAPA | Full-feedback source replay and shared paired-cost adaptations | Official factors are replay-verified; HT/gated transfers are adaptations |
| PPE | Source-factor aliases plus shared-engine compositions | Paired decision-cost use is an endpoint adaptation |
| Xu active betting | Implemented source construction and shared-engine compositions | Transferred to paired costs with its propensity/bound requirements |
| DISCERN | Gated HT and empirical-Bernstein-style adaptation | Disagreement gating is credited to DISCERN; there is no official code reproduction here |
| Horizon SR/CUSUM | Fixed-start, registered starts, SR and CUSUM variants | Standard e-detector composition; supplied to candidate and incumbents |
| Chugg-style group audit | Independent exact subgroup composition in WP2 | Same intersection-type null; analytically ties the candidate |
| Full feedback | Reported as an unmatched upper reference | Uses more information than selective-label arms |
| Feature ADWIN | Reported as a label-free feature sentinel | Tests feature change rather than decision harm |
| Comparecast | Excluded from same-null ranking | Weak running-average forecasting null differs from the eventwise harm null |
| PPRM | Excluded from same-null ranking | Predictive-risk estimand differs from paired decision harm |
| MOPE, OPI and Wang certification | Out of scope | Q2 candidate-certification target, not incumbent-harm monitoring |

No exclusion is evidence that a method is generally weak. Every composition uses
the same registered path, acquisition budget and applicable engine family; the
candidate is never given a stronger engine solely for its own row.

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
The WP4 task, policies and arms were frozen by hash at 2026-10-27T20:58:55Z, which
starts the prospective clock for that bundle. No post-freeze EIA data has been
pulled, so no prospective observation is claimed. The earliest useful prospective
smoke check is around 2026-12-08 (about 1,000 hours per respondent) and needs an
API key or a fresh bulk snapshot (about 700 MB), which awaits the user's
go-ahead. The retrospective per-path null passes and injected-harm results are
recorded above; checkpoint A is moot because the phase ends at checkpoint B.

Any future confirmation would first need a justified candidate, separate development
and null calibration, a frozen full panel and primary cell, exact matched-resource
rules, simultaneous null accounting, per-path real-data orientation checks and
untouched data. Only then could a new protocol allocate the reserved 59100000–59100999
block. The final decision must apply the +10-point or 1.5x delay primary margin,
the -3-point secondary margin, and the required paired uncertainty. No such run
is part of this phase.

## Remaining limits

Twenty alternative seeds in WP3 can screen a policy but cannot confirm efficiency
or null validity. WP1 S3 is a development comparison, not confirmation; its
gains are attributable to published mechanisms. WP4 uses previously examined
windows, imposed costs and monitor label delay 0, and its real policy pair rarely
disagrees. Git stores the WP4 frozen sources with LF line endings, so hashes taken
on a CRLF checkout differ from the freeze record. Exact working-law growth in WP2
is conditional on imposed laws
and fitted pilot slices. Prior-art searches are bounded and establish no priority.
Synthetic conditional-null arguments do not establish real-data causal utility
or historical publication availability. The WP1 and WP4 test files pass
(52 tests in `tests/test_gated_monitor_comparison.py`; 74 across the four WP4
test files).

## Continue / pivot / stop

**Stop** the Paper 1 algorithm search (checkpoint B). Every claimable mechanism
(M1–M4, M7) failed its registered screen; S3 exposed no uncredited advantage; and
no new derivable candidate fits Paper 1 (see the
[exit ledger](algorithm_search_exit_ledger.md)). This is not a claim that no
better monitor exists.

**Continue** the benchmark manuscript with these findings: ungated sparse-label
conclusions in the repository are mostly label waste (about 91% of labels on
events with known zero paired cost); the G1 growth calculation predicts realised
growth within about 15%; under bursty disagreement, fixed gating should be
preferred to past-paced gating (synthetic R7 and EIA injected harm); the
estimand distinction between pooled and intersection nulls; the real-data
validity table; and the negative screens with their registered margins.

**Pivot options (each needs user approval and its own protocol):** Paper 3,
burst-robust allocation of a finite label budget over time (M8), against WP3's
temporal schedule and DE-CuSum-style rules; or Paper 2, candidate promotion,
whose estimand and incumbents are unaffected by these failures. The prospective
EIA smoke check can proceed independently once data access is approved.

Ponytail's source skill was applied without global installation. PaperBanana's
author/community repositories were inspected; the pinned environment has no
working PaperBanana/API configuration. No research figure was generated and no
alternative visual generator was substituted. Tables carry the current evidence.
