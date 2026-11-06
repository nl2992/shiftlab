# Sprint 2 reproduction index

Run commands from the repository/worktree root using `uv run`. The run environment is the
`research/sprint2-a5b-d2-rmm` worktree at base revision
`1e46378132c8c090f67b39e9bd10b91a75cb4919`; experiment-specific exact seed bases and commands are
in family ledgers and manifests. Raw outputs are under gitignored `outputs/`; do not add licensed or
large artifacts to Git.

## Raw-to-report numerical reproduction

Recompute and compare the amended analyses and the family H/R/T/P Track-R outputs to their saved
reports with:

```sh
uv run python scripts/sota_sprint/audit_raw_to_reports.py --out docs/sprint2/raw_report_audit.json
```

The audit runs from saved raw records and requires exact JSON equivalence (numeric tolerance 1e-12)
and byte-identical Markdown. It covers amended validation, WP1 and WP2; WP1 rollback event traces;
P6 twin and selection-adjusted summaries; H and T development summaries; both WP2 Xu-excluded
sensitivities; all four H/R/T/P Track-R reports; and the post hoc WP1 E_swcert Track-R curve and Giacomini–Rossi diagnostic. It also recomputes the reported Family R Track
E/V cells (315 metric cells) from its dev and evaluation runs. It does not reconcile every P-family
development claim or every narrative claim in the 24-candidate registry. The T3 matched-host
follow-up is regenerated separately from its eight development and eight evaluation runs.

The post hoc E_swcert Track-R runs use eight alphas and are stored separately at
`outputs/sprint2/WP1/trackR_E_swcert_{dev,eval}_a*`. The exact per-alpha screen command is:

```sh
uv run python scripts/sota_sprint/screen.py --regimes F0_null,F0_worse,F5_dep_null_r8,F5_dep_null_r95,F0_better,F7_near_better,F9_bursty_better,F1_late_800,F5_dep_better_r8,S_dep_better_r95 --policies E_swcert --seeds 20 --seed-base 2026110701 --workers 2 --alpha 0.005 --out outputs/sprint2/WP1/trackR_E_swcert_dev_a0.005
uv run python scripts/sota_sprint/risk_curves.py --dev outputs/sprint2/WP1/trackR_E_swcert_dev_a* --eval outputs/sprint2/WP1/trackR_E_swcert_eval_a* --out docs/sprint2/wp1/trackR_E_swcert.json
```

Repeat the screen command for alpha `0.01 0.02 0.05 0.1 0.2 0.3 0.5`, and for evaluation seed
base `2026110711` with `eval` in the output directory name.

The post-development T3 matched-host Track-R follow-up is registered separately in
`family_t/T3_trackR_followup_protocol.md`; its raw development and evaluation screens use the
registered Track-R seed bases and alpha grid under `outputs/sprint2/T/T3_trackR/`.

Reproduce the post hoc Giacomini–Rossi WP1 diagnostic with:

```sh
uv run python scripts/sota_sprint/wp1_giacomini_rossi.py --alpha 0.05 --out docs/sprint2/wp1/gr_one_time_reversal.json
```

## WP2 stored-flag audit

Recheck the Run-2 re-windowing records with:

```sh
uv run python scripts/sota_sprint/audit_wp2_run2.py --out docs/sprint2/wp2/run2_decision_flag_audit.json
```

This checks stored promotion metadata, per-promotion EI arithmetic, net cost identities, and paired
all-in excess economic cost against never-switch. The legacy raw `harm` field is a cost difference,
not application-level decision harm. This is not trajectory reproduction or a validity test.

Regenerate the retrospective WP2 cost decomposition from all saved primary and Run-2 records:

```sh
uv run python scripts/sota_sprint/analyze_wp2_realized_harm.py
```

This reports prediction-loss change, label expenditure, switch expenditure, and all-in excess
economic cost with cluster-bootstrap intervals. The script checks the per-record accounting identity
before summarizing; it does not estimate causal application utility or establish a prospective
promotion guarantee.

## Registry audit

Run the structural candidate/evidence-path audit with:

```sh
uv run python scripts/sota_sprint/audit_sprint2_registry.py --out docs/sprint2/registry_audit.json
```

This verifies the 24 registry IDs, nonblank Track E/R/V cells, family-ledger IDs, and existence of
listed artifacts. It does not re-compute values or establish inference validity.

## Report claim audits

Regenerate the metric-specific WP1 late-improvement leaderboard from the saved primary records:

```sh
uv run python scripts/sota_sprint/build_wp1_late_metric_leaderboard.py
```

This reports J, retrospective hindsight regret, promotion-conditional delay, label expenditure,
switching expenditure, and paired net-cost differences against the strongest certified comparator
selected on the same episodes. It uses the 10 retrospective late episodes in five source clusters;
the comparator and episode class selection are development-exposed, so these are descriptive
within-stratum ranks rather than confirmatory or cross-track rankings.

```sh
uv run python scripts/sota_sprint/audit_raw_to_reports.py --out docs/sprint2/raw_report_audit.json
uv run python scripts/sota_sprint/audit_p_family_development.py --out docs/sprint2/family_p/development_audit.json
uv run python scripts/sota_sprint/audit_cost_risk_pareto.py --out docs/sprint2/cost_risk_audit.json
uv run python scripts/sota_sprint/analyze_p3_cost_sweep.py --out docs/sprint2/family_p/P3_cost_sweep.json
uv run python scripts/sota_sprint/wp2_analyze.py --amendment-dir docs/sprint2/wp2/amended_no_xu_pool --exclude-xu-pool
uv run python scripts/sota_sprint/wp1_false_rollback.py --workers 4
```

The first command recomputes amended reports, selected Track E/V cells, P1/P2 summaries, and
family Track-R tables from saved records, including the separate T3 and T1/T2/T5 held-out panels.
The second checks the specified P-family development tables. The third checks every displayed
cost-risk point (316 rows) against its family Track-R JSON. All three are numerical lineage checks; none establishes the appropriateness of the
estimands, thresholds, selection procedure, causal interpretation, or theorem assumptions. Manual
claim corrections and remaining coverage limits are recorded in `CLAIM_RECONCILIATION.md`.

## Existing core runs

- Main validation and 1,000-seed null suite: `outputs/sota_sprint/validation/`; command/seed
  manifests in `outputs/sota_sprint/validation.log` and `outputs/sota_sprint/manifest.json`.
- Gate A–D committed-code re-screen: `outputs/sota_sprint/gate.log` and run manifests.
- Candidate families H/R/T/P: exact development, real-data and Track R commands/seed manifests are
  recorded in `docs/sprint2/family_{h,r,t,p}/ledger.json` and the adjacent family run guides.
- WP1 primary/twin/sensitivity analyses: commands and seed bases in `docs/sprint2/wp1/protocol.md`;
  frozen raw runs in `outputs/sprint2/WP1/`.
- WP2 runs: frozen commands/protocol in `docs/sprint2/wp2/BENCHMARK.md` and `protocol.md`; raw
  manifests under `outputs/sprint2/WP2/`.
- Adaptive-range correction impact inventory across the SOTA sprint and Sprint 2: regenerate the manifest schedule with
  `uv run python scripts/sota_sprint/audit_adaptive_gate_impact.py`; its source manifests are under
  `outputs/`, its human-readable schedule is `docs/sprint2/adaptive_gate_impact.md`, and
  machine-readable output is `outputs/sprint2/adaptive_gate_impact.json` (gitignored). Affected old
  rows are historical; corrected same-seed replays and downstream report regeneration are pending.
  Generate replay commands with `uv run python scripts/sota_sprint/replay_adaptive_gate_runs.py`;
  execute the complete schedule with `uv run python scripts/sota_sprint/replay_adaptive_gate_runs.py --execute`.
  To run one registered suite first, pass `--run-dir outputs/sota_sprint/validation/null1000
  --workers 9 --execute`. Replays write to sibling directories tagged
  `_wmaxfix_20261105` and refuse to overwrite existing outputs.
  After corrected suites finish, compare old and new rows with
  `uv run python scripts/sota_sprint/analyze_adaptive_gate_replays.py`; it checks exact key and
  contract matches and records manifest hashes alongside paired outcome deltas.

## Corrected sensitivity analyses

```sh
uv run python scripts/sota_sprint/analyze_validation.py --amendment-dir docs/sprint2/validation_amendment_20261104
uv run python scripts/sota_sprint/analyze_validation.py --strict-published-dir docs/sprint2/validation_strict_published_20261104
uv run python scripts/sota_sprint/late_real.py report --primary outputs/sprint2/WP1/primary --twin outputs/sprint2/WP1/twin --sens outputs/sprint2/WP1/sens_* --classes outputs/sprint2/WP1/classes.json --amended-no-xu --out docs/sprint2/wp1/results_amended_no_xu.json
uv run python scripts/sota_sprint/late_real.py run --streams all --policies discern_design_floor --seeds 3 --seed-base 2026110803 --workers 2 --out outputs/sprint2/WP1/strict_extra_discern_design_floor
uv run python scripts/sota_sprint/late_real.py report --primary outputs/sprint2/WP1/primary --twin outputs/sprint2/WP1/twin --sens outputs/sprint2/WP1/sens_* --supplemental outputs/sprint2/WP1/strict_extra_discern_design_floor --classes outputs/sprint2/WP1/classes.json --strict-published-subset --out docs/sprint2/wp1/strict_published_subset_20261104.json
uv run python scripts/sota_sprint/wp2_analyze.py --amendment-dir docs/sprint2/wp2/amended_no_xu
uv run python scripts/sota_sprint/wp2_analyze.py --strict-published-dir docs/sprint2/wp2/strict_published_20261104
uv run python scripts/sota_sprint/screen.py --kind real --regimes metro,beijing_pm25,bike_hour,appliances,household_power --policies H1,H2,H3,H4,H5,H6-r10,D2,A5b,gated_deployment,gated_adaptive_range,gated_adaptive_range+front,discern_style,discern_design_floor,SMCS+retain-incumbent,xu_acquisition_only,choe_ramdas_eb+front,CONTROL_never_switch --seeds 20 --seed-base 2026110701 --workers 4 --alpha 0.05 --out outputs/sprint2/round5/H_corrected_real_20
uv run python scripts/sota_sprint/analyze_h_corrected_real.py outputs/sprint2/round5/H_corrected_real_20/records.jsonl --json docs/sprint2/family_h/corrected_real_20.json --markdown docs/sprint2/family_h/corrected_real_20.md
```

These analyses preserve original registered outputs. The first validation sensitivity excludes Xu
but retains Choe–Ramdas and QCE ports in its historical adapter pool. The strict validation output
ranks only the six ports in `bench.CERTIFIED_PUBLISHED`. Neither analysis adjusts same-sample
comparator selection; all common-contract method ports remain distinct from author-native full
deployments.

The corrected Family-H replay contains 1,240 jobs and 21,080 rows (62 episodes × 20 seeds × 17
policies). Its raw-record SHA-256 is
`61c60387a9ff001a10c62d4a60e22607dc8a16575189af174bdfd60b59a0a93c`; `manifest.json` records
the run arguments, runtime, code hashes and five input-cache hashes. Analysis verifies complete
episode × seed × policy coverage against each source cache. The report is post-development and
descriptive; the streams have prior exposure.

## T1/T2/T5 held-out Track-R follow-up

The additional Model Picker, Gated Deployment and shared-wrapper curves use the registered
protocol and runner:

```sh
scripts/sota_sprint/run_t125_trackr_followup.sh
uv run python scripts/sota_sprint/risk_curves.py \
  --dev outputs/sprint2/T/T125_trackR/dev_a0.005 outputs/sprint2/T/T125_trackR/dev_a0.01 outputs/sprint2/T/T125_trackR/dev_a0.02 outputs/sprint2/T/T125_trackR/dev_a0.05 outputs/sprint2/T/T125_trackR/dev_a0.1 outputs/sprint2/T/T125_trackR/dev_a0.2 outputs/sprint2/T/T125_trackR/dev_a0.3 outputs/sprint2/T/T125_trackR/dev_a0.5 \
  --eval outputs/sprint2/T/T125_trackR/eval_a0.005 outputs/sprint2/T/T125_trackR/eval_a0.01 outputs/sprint2/T/T125_trackR/eval_a0.02 outputs/sprint2/T/T125_trackR/eval_a0.05 outputs/sprint2/T/T125_trackR/eval_a0.1 outputs/sprint2/T/T125_trackR/eval_a0.2 outputs/sprint2/T/T125_trackR/eval_a0.3 outputs/sprint2/T/T125_trackR/eval_a0.5 \
  --out docs/sprint2/family_t/T1_T2_T5_trackR_followup.json
uv run python scripts/sota_sprint/finalize_t125_trackr_followup.py
```

The protocol, run commands, per-run manifests and SHA-256 checksums are recorded in
`family_t/T1_T2_T5_trackR_followup_protocol.md` and
`family_t/T1_T2_T5_trackR_manifests.json`. The panel has 3,200 episode jobs and 54,400 records.
The report-lineage audit checks its JSON and Markdown, and the cost-risk audit checks its displayed
rows. These checks do not establish validity beyond the registered empirical nulls.

## P-family development-table audit

Recompute selected P-family development summaries from saved runs:

```sh
uv run python scripts/sota_sprint/audit_p_family_development.py --out docs/sprint2/family_p/development_audit.json
```

This checks 5,980 P1 summary fields; P2 episode-level V1/V2, twin A500, narrative correlations and
conditional-harm values; selected P3 harm;
106 P4 null/power cells; all 24 synthetic and 20 real P5 paired-cost means/intervals, the first two
K=4 model columns against all five frozen 2-model caches, P5 comparative-cost and null-switching
claims; and 21 P6 synthetic
contrasts plus 25 fresh-real mean-cost cells. It also reconciles all 40 displayed P1 Fisher/simulation
cells, all 768 P3 switch-cost reweighting values, and P3's scoped narrative/registry cost-grid claims
to the saved source trajectories. The audit currently has 17 passing groups and 7,139 checked
cells, including P1's selected paired contrasts and null-promotion narrative reconciled to raw seed
records.
It does not
establish causal truth or theorem validity.

## WP1 headline report-claim audit

Reconcile the WP1 class-count and named cluster summaries, classifier rule-sensitivity counts,
primary paired-contrast table, late-class mean-cost/verdict claims, sensitivity contrast table,
false-rollback narrative counts, and the reversal operating table.
The primary table uses the no-Xu amended analysis; the
sensitivity table is checked against the historical registered analysis, which retains the Xu
acquisition adapter in its explicitly labeled comparator panel:

```sh
uv run python scripts/sota_sprint/audit_wp1_report_claims.py --out docs/sprint2/wp1/report_claim_audit.json
uv run python scripts/sota_sprint/audit_leaderboard_null_counts.py --out docs/sprint2/leaderboard_claim_audit.json
```

The current audit passes 9 groups / 293 numeric or verdict checks, including twin-null promotion
rates and the E_swcert/Xu Track-R wording. Both result JSON files are separately regenerated from
raw records by `audit_raw_to_reports.py`; this check does not validate classifier assumptions,
causal labels, or every WP1 diagnostic. The leaderboard null-rate audit recounts A5b and P6 promotions
from the six-regime, 1,000-seed saved run and checks the displayed attribution; it does not establish
validity outside the methods' declared nulls.

## Fresh-seed post-development follow-up

The WP1 reversal sensitivity is specified in `docs/sprint2/wp1/AMENDMENT_20261104_E_RB.md`.
After its runner completes, reproduce its summary with:

```sh
uv run python scripts/sota_sprint/analyze_wp1_erb_postdev.py outputs/sprint2/round5/wp1_erb_reversal_postdev100 --out docs/sprint2/wp1/erb_reversal_postdev100.json
```

P6's corrected certificate-port comparison, its within-regime simultaneous comparator bootstrap, and 1,000-seed replay on 120 episodes nested in 20 source
splits of the reused twin-bike dataset are preregistered in `family_p/P6_COMPARATOR_AMENDMENT_20261104.md` and the Twin Bike section
of `family_p/P6_late_reversal.md`. Their exact runner commands are frozen in those amendments.
The twin run is complete. The manifest was reconstructed after a manifest-only post-run error;
row coverage and hashes are recorded in the manifest, while runtime is unavailable. Reproduce the
manifest audit and cluster summaries with:

```sh
uv run python scripts/sota_sprint/analyze_p6_selection_adjusted.py outputs/sprint2/round5/P6_corrected_comparators_100/records.jsonl --out docs/sprint2/family_p/P6_selection_adjusted.json
uv run python scripts/sota_sprint/finalize_p6_twin_manifest.py
uv run python scripts/sota_sprint/analyze_p6_twin_bike.py outputs/sprint2/round5/p6_twin_bike_1000 --out docs/sprint2/family_p/p6_twin_bike_1000.json
```

## Checks previously recorded

The post hoc WP1 timestamp-start-grid replay and summary can be reproduced with:

```sh
uv run python scripts/sota_sprint/wp1_clock_ablation.py --seeds 3 --seed-base 2026110803 --out outputs/sprint2/WP1/clock_ablation_posthoc3
uv run python scripts/sota_sprint/analyze_wp1_clock_ablation.py outputs/sprint2/WP1/clock_ablation_posthoc3/records.jsonl --out docs/sprint2/wp1/clock_ablation_posthoc3.json
```

It covers only the five timestamp-retaining fresh UCI streams and is exploratory; see the limitations in the generated JSON.

The H2 Round-5 follow-up (protocol and seed bases are frozen in
`family_h/ROUND5_H2_AMENDMENT_20261104.md`) can be reproduced with:

```sh
uv run python scripts/sota_sprint/screen.py --seed-base 2026110801 --workers 4 --regimes F0_better,F9_bursty_better,F1_late_800,F3_reversal_800,F5_dep_better_r8,S_dep_better_r95,F0_null,F5_dep_null_r8,F5_dep_null_r95 --policies H2,D2,A5b,H1,H2-iid_space,H2-gateonly,gated_adaptive_range+front,CONTROL_never_switch --seeds 100 --out outputs/sprint2/round5/H2_followup100
uv run python scripts/sota_sprint/screen.py --seed-base 2026110802 --workers 4 --regimes F0_null,F5_dep_null_r8,F5_dep_null_r95,P_markov_null_r98 --policies H2,H2-iid_space,H2-gateonly,D2,A5b --seeds 1000 --out outputs/sprint2/round5/H2_markov_null1000
uv run python scripts/sota_sprint/screen.py --kind real --seed-base 2026110803 --workers 3 --regimes rialto,openml_ldpa,airlines,criteo,bank,elec2,weather,spam,uci_occupancy,metro,beijing_pm25,bike_hour,appliances,household_power --policies H2,D2,A5b,gated_adaptive_range+front,CONTROL_never_switch --seeds 3 --out outputs/sprint2/round5/H2_real14_3seed
uv run python scripts/sota_sprint/analyze_h2_round5.py --synthetic outputs/sprint2/round5/H2_followup100/records.jsonl --null outputs/sprint2/round5/H2_markov_null1000/records.jsonl --real outputs/sprint2/round5/H2_real14_3seed/records.jsonl --out docs/sprint2/family_h/round5_h2.json
uv run python scripts/sota_sprint/screen.py --seed-base 2026110802 --workers 4 --regimes P_hmm_null --policies A5b,P1_renew,P1_union,P1_A5b_c10,D2,rmm:gated_deployment+RMM,P6_LRMD_U --seeds 1000 --out outputs/sprint2/round5/P4_hmm_null1000
uv run python scripts/sota_sprint/analyze_p4_hmm_followup.py outputs/sprint2/round5/P4_hmm_null1000/records.jsonl --out docs/sprint2/family_p/P4_hmm_round5.json
```

All evidence is post-development. The synthetic seeds are fresh Monte Carlo draws from fixed regimes;
the real data are unchanged previously exposed sources. The raw-to-report audit regenerates both
Round-5 summaries from their saved source records.

```sh
uv run pytest -q tests/sota_sprint tests/sprint2
```

Latest recorded run: 379 passed in 143.34 s after the P-family claim-audit updates, including three tests for the merged Family-H curve utility. Do not interpret
that test suite as validating research hypotheses or theorem assumptions.


## Family H Track-R completion

The post hoc H1/H3 Track-R grid is reproducible with:

```sh
scripts/sota_sprint/run_trackR_h_completion.sh
scripts/sota_sprint/run_trackR_h_rollback_completion.sh
uv run python scripts/sota_sprint/merge_h_trackr.py
uv run python scripts/sota_sprint/audit_cost_risk_pareto.py --out docs/sprint2/cost_risk_audit.json
```

The screens use the eight `bench2.ALPHA_GRID` values, 20 development seeds per regime at base
2026110701, and 20 evaluation seeds per regime at base 2026110711. The merged curves combine H1-H6
and D2/A5b. H5/H6 received a dedicated timing recheck after the earlier shared screen recorded high
outliers: 15 episodes per candidate over three regimes had maxima below 0.36s. This small sample is
not a worst-case runtime guarantee. The complete family-level curve table is
`family_h/track_R_all.json` and its report is included in `COST_RISK_PARETO.md`.

## Family P5 K-model Track R

The separate K=3/4 risk-cost panel uses the frozen 20-seed development/evaluation bases and saves
each regime/alpha batch under `outputs/sprint2/P/trackR_K/checkpoints/`, so completed batches can be
reused after interruption:

```sh
uv run python scripts/sota_sprint/p5_trackr.py --seeds 20 --workers 2 --out outputs/sprint2/P/trackR_K
uv run python scripts/sota_sprint/audit_cost_risk_pareto.py --out docs/sprint2/cost_risk_audit.json
```

Risk is pooled over K3_null/K4_null; alternative cost is pooled over K3_best1, K4_mixed, K3_near
and K4_late. Development null risk and development alternative cost select alpha; evaluation uses
separate seed blocks. This custom panel is not pooled with the shared two-model Track-R curves.

## Adaptive-gate correction sensitivity reports

The corrected outputs substitute affected policy rows only after one-to-one exact-key matching on
stream/regime, episode, seed, and policy. They are same-seed implementation-correction sensitivities;
they are not independent confirmation. Registered reports remain unchanged.

```sh
uv run python scripts/sota_sprint/analyze_validation.py \
  --strict-published-dir docs/sota_sprint/validation/adaptive_gate_fixed_strict_20261106 \
  --adaptive-gate-corrected
uv run python scripts/sota_sprint/analyze_real.py \
  --adaptive-gate-corrected-dir docs/sota_sprint/validation/real_adaptive_gate_fixed_20261106
uv run python scripts/sota_sprint/leaderboard_views.py --adaptive-gate-corrected \
  --out-dir docs/sota_sprint/validation/adaptive_gate_fixed_20261106
uv run python scripts/sota_sprint/late_real.py report \
  --primary outputs/sprint2/WP1/primary --twin outputs/sprint2/WP1/twin \
  --sens outputs/sprint2/WP1/sens_* --classes outputs/sprint2/WP1/classes.json \
  --amended-no-xu --adaptive-gate-corrected \
  --out docs/sprint2/wp1/adaptive_gate_fixed_20261106.json
uv run python scripts/sota_sprint/render_wp1_correction_report.py \
  --input docs/sprint2/wp1/adaptive_gate_fixed_20261106.json \
  --output docs/sprint2/wp1/adaptive_gate_fixed_20261106.md
uv run python scripts/sota_sprint/wp2_analyze.py \
  --adaptive-gate-corrected-dir docs/sprint2/wp2/adaptive_gate_fixed_20261106
```

The corrected WP1 analysis remains **NOT_SUPPORTED** for the retrospective real late-improvement
subset (0/4 RMM hosts); this does not establish absence of late-improvement value in other data.
WP2's original limitations remain: A5b does not meet the registered criterion on every tested
strong-dependence null, and the combined three-null precision criterion fails. WP1/WP2 corrected
artifacts are sensitivity reports, not replacements for their registered evidence.

## MOPE interval-intersection correction (2026-11-06)

Source review found that the local two-sided MOPE interval did not intersect its lower and reflected
upper confidence sequences after every update. This could leave a crossed interval and cause future
bets to use endpoints outside the joint interval. `MopeCS.update` now enforces the intersection and
recomputes both next bets at the intersected endpoints. Focused regression and policy tests cover
the invariant. The broader replay includes direct and wrapped consumers of `MopeCS`:

```sh
uv run python scripts/sota_sprint/replay_mope_interval_runs.py --workers 8 --execute
```

The current scheduler inventory contains 163 manifest-backed source runs. After it finishes, rerun
all MOPE-dependent validation, real-data, WP1/WP2 and leaderboard sensitivities with the sibling
outputs tagged `_mopeinterval_20261106`. The earlier `adaptive_gate_fixed_*` reports predate this fix
and are superseded for MOPE-dependent conclusions. The native author's `opebet.wealth_lb_2d`
thresholds exact log wealth on a finite grid; the local adapter instead implements the paper's
quadratic log-wealth lower bound. Numerical comparison therefore needs to check bet updates, bound
direction, and coverage as well as endpoint values; native-source parity review remains open.

## R5 focused Round-5 follow-up

The new-seed R5 alpha=.02 simulator follow-up has its frozen question and execution details in
`family_r/R5_round5_protocol.md`. Reproduce it with:

```sh
uv run python scripts/sota_sprint/screen.py \
  --regimes F0_null,F0_worse,F5_dep_null_r8,F5_dep_null_r95,F0_better,F7_near_better,F9_bursty_better,F1_late_800,F5_dep_better_r8,S_dep_better_r95 \
  --policies R5,D2,A5b,gated_adaptive_range+front,R:economic_stop \
  --seeds 100 --seed-base 2026110901 --workers 4 --alpha 0.02 \
  --out outputs/sprint2/round5/R5_eval100_a002
uv run python scripts/sota_sprint/analyze_r5_round5.py \
  --input outputs/sprint2/round5/R5_eval100_a002 \
  --out docs/sprint2/family_r/R5_round5_results.json
```

The alpha is frozen from the prior development curve; this follow-up estimates only that operating
point and does not regenerate R5's full R5–R30 frontier.

## P6 all-14-source real-stream cost replay

This post-development descriptive replay uses the nine Atlas and five UCI sources already in the
repository. Its protocol and interpretation limits are in `family_p/P6_all14_real_protocol.md`.
Reproduce the run and analysis with:

```sh
uv run python scripts/sota_sprint/screen.py --kind real \
  --regimes rialto,spam,weather,openml_ldpa,uci_occupancy,airlines,bank,elec2,criteo,metro,beijing_pm25,bike_hour,appliances,household_power \
  --policies P6_LRMD_U,M_LRMD_SUI,A5b,D2,rmm:gated_deployment+RMM,gated_adaptive_range+front,CONTROL_never_switch \
  --seeds 20 --seed-base 2026110902 --workers 6 --alpha 0.05 \
  --out outputs/sprint2/round5/p6_all14_real20
uv run python scripts/sota_sprint/analyze_p6_all14_real.py \
  --input outputs/sprint2/round5/p6_all14_real20 \
  --json docs/sprint2/family_p/P6_all14_real_results.json \
  --markdown docs/sprint2/family_p/P6_all14_real_results.md
```

Policy seeds are averaged within fixed episodes; they are Monte Carlo repetitions, not new data
units. Cached-stream comparisons are economic replays only and do not provide causal late-change
labels or independent dataset confirmation.

## R5 all-14-source real-stream cost replay

This replay extends Family R's prior 3-seed, 7-source real run to all 14 paired-loss sources. It is
post-development descriptive evidence; see `family_r/R5_all14_real_protocol.md` for the frozen
question and interpretation limits.

```sh
uv run python scripts/sota_sprint/screen.py --kind real \
  --regimes rialto,spam,weather,openml_ldpa,uci_occupancy,airlines,bank,elec2,criteo,metro,beijing_pm25,bike_hour,appliances,household_power \
  --policies R5,D2,A5b,economic_replacement,R:economic_stop,cams_adapter,gated_adaptive_range+front \
  --seeds 20 --seed-base 2026110903 --workers 6 --alpha 0.05 \
  --out outputs/sprint2/round5/R5_all14_real20
uv run python scripts/sota_sprint/analyze_r5_all14_real.py \
  --input outputs/sprint2/round5/R5_all14_real20 \
  --json docs/sprint2/family_r/R5_all14_real_results.json \
  --markdown docs/sprint2/family_r/R5_all14_real_results.md
```

The 20 seeds are policy-randomness repetitions within fixed episodes. They do not increase the
number of independent datasets.

## Family R Track-R coverage follow-up

This run adds held-out points for the 26 policies with at least one development-feasible alpha,
using the existing development calibration map and one common evaluation seed block. Its protocol is
`family_r/R_trackR_coverage_followup_protocol.md`; it is a new simulator replicate on reused regimes,
not independent real-data confirmation.

```sh
scripts/sota_sprint/run_r_trackr_coverage_followup.sh
uv run python scripts/sota_sprint/risk_curves.py \
  --dev outputs/sprint2/R/dev_screen_a05 \
       outputs/sprint2/R/trackR/dev_a0.005 outputs/sprint2/R/trackR/dev_a0.01 \
       outputs/sprint2/R/trackR/dev_a0.02 outputs/sprint2/R/trackR/dev_a0.1 \
       outputs/sprint2/R/trackR/dev_a0.2 \
       outputs/sprint2/R/trackR/dev_a0.3 outputs/sprint2/R/trackR/dev_a0.5 \
       outputs/sprint2/R/trackR_H/dev_a0.005 outputs/sprint2/R/trackR_H/dev_a0.01 \
       outputs/sprint2/R/trackR_H/dev_a0.02 outputs/sprint2/R/trackR_H/dev_a0.05 \
       outputs/sprint2/R/trackR_H/dev_a0.1 outputs/sprint2/R/trackR_H/dev_a0.2 \
       outputs/sprint2/R/trackR_H/dev_a0.3 outputs/sprint2/R/trackR_H/dev_a0.5 \
  --eval outputs/sprint2/R/trackR_coverage_followup/eval_a0.005 \
         outputs/sprint2/R/trackR_coverage_followup/eval_a0.01 \
         outputs/sprint2/R/trackR_coverage_followup/eval_a0.02 \
         outputs/sprint2/R/trackR_coverage_followup/eval_a0.05 \
         outputs/sprint2/R/trackR_coverage_followup/eval_a0.1 \
         outputs/sprint2/R/trackR_coverage_followup/eval_a0.2 \
         outputs/sprint2/R/trackR_coverage_followup/eval_a0.3 \
         outputs/sprint2/R/trackR_coverage_followup/eval_a0.5 \
  --out docs/sprint2/family_r/R_trackR_coverage_followup.json
uv run python scripts/sota_sprint/analyze_r_trackr_coverage_followup.py
uv run python scripts/sota_sprint/finalize_r_trackr_coverage_followup.py
uv run python scripts/sota_sprint/audit_raw_to_reports.py
uv run python scripts/sota_sprint/audit_cost_risk_pareto.py
```

The finalizer checks all eight manifests, complete regime/seed/policy/alpha coverage, and stable
simulation source hashes. Git revisions and bookkeeping-source hashes are retained per run because
audit files may change without changing the experiment implementation.
