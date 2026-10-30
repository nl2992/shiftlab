# Append-only execution ledger

## 2026-10-30: initial progress

- Isolated branch `research/exhaustive-candidate-evaluation-2026-10-30`, base `71ad2b3`.
- Copied Candidate J originals without modifying their source worktree. Five existing correctness tests passed. Registered J benchmark completed: exact risk `809/2048` on both; 235 versus 170975 states; 0.00964 versus 41.01 seconds; Python-traced peaks 119951 versus 159387567 bytes. Fixed-controller result only, not optimizer novelty or safe policy synthesis. The benchmark controller's risk exceeds 0.05.
- First 540-combination development screen completed all eight cases, 64 independent paths per case, horizon 1200. Its artifact hashes and executed engine/runner snapshots are retained. No faithful SOTA reproduction, real-data win or novelty claim follows.

## 2026-10-30: evaluator correction before ranking

The initial `harm_to_alarm` used the positive part of expected context loss minus population source mean. That assigns positive harm to ordinary context variation under a stationary null. It is not shift-attributable harm. Preserve v1 metrics unchanged; withdraw that column's interpretation. Alarm probabilities, query counts and trajectories are unaffected by this evaluator-only correction.

Version 2 subtracts source conditional loss on the SAME realized context before taking the positive part. Under null/nuisance this is exactly zero. This is evaluator-only synthetic information and never enters the learner. New regression check verifies zero null harm and localization after onset. The corrected rerun has separate registration/output/status paths and identical algorithm grid, world/query seeds and sample sizes. It does not add 540 new distinct algorithms to the count.

Analysis must use `pd.read_csv(..., keep_default_na=False)` because pandas otherwise parses the literal case name `null` as missing. This was discovered in an ad hoc diagnostic, not the execution loop; do not omit null cells from ranking.

## 2026-10-30: author-code compatibility check

Cloned the active-RCPS author repository at `a67f85d603df2bb3e32ef007f445191923ebd990`. First fixed-target parity execution failed at the original author's NumPy-array >= Torch-tensor assertion under current packages. A local subclass converts only the bound return type to NumPy; it does not change the original increment or FTL update. The parity path uses budget=T to isolate the author's expected-budget component from the separately unproved hard-cap extension. Full grid inversion and learned query policy remain unverified.

The first numerical comparison (and a float64 diagnostic) then failed with max logwealth error 0.374166: it compared the author's immediate-observation bet update with an issuance-delayed adapter at delay 5. Those filtrations differ. The correct component parity setting is delay 1, where each preceding event is observed before the next bet is issued. Larger-delay wrappers are explicitly adaptations, not original-code parity. The diagnostic failure arrays are retained in `rcps_parity_failure.json`. No successful reproduction claim is made for those failed settings.

## 2026-10-30: validated development checkpoint

- Corrected screen completed 540 unique configurations across eight cases. Initial and corrected runs are the same 540 algorithms, not 1080. Corrected metrics and raw per-path arrays are retained.
- Author RCPS fixed-target component parity passed at delay1: max logwealth difference `1.3322676295501878e-15`. Delayed hard-cap adapter was compared on the same eight development cases; full learned querying and other published baseline obligations remain open.
- Agent downloaded and checksum-verified both public data sources into this isolated worktree; 8645 Bike and 17520 Beijing pre-final development rows, no duplicate timestamps. Final outcomes were not analysed. No real-data efficacy claim.
- Fourteen targeted tests passed. Host Ruff 0.15.18 initially passed, but commit hooks use Ruff 0.17.1 and required additional import/style checks. Hooks formatted source. Executed pre-format sources are archived; a separate replay verified that all first-alarm, query-count and maximum-logwealth arrays are exactly identical for all 540 configurations on all eight cases after formatting/lint fixes. This replay is not independent confirmation.
- Byte-preserving Git attributes protect registrations/results and archived executed-source hashes across Windows/Linux checkout. Historical source hashes refer to archived executed bytes, not necessarily the subsequently formatted working source.
- Full objective remains ACTIVE: faithful PR/PPRM and active-query baselines, compact-controller synthesis/value-gap comparison, second bottleneck-targeted round, realistic calibration/dependence, real-data efficacy, fresh confirmation and final adversarial review are not complete.

## 2026-10-30: second goal turn — progress

- Added PR Appendix E PM-EB and PPRM equations 19/22/27 formula adapters. Both ran alongside RCPS and old anchors on 12 round2 cases. Full author reproduction is not claimed.
- Executed 756 registered tuples, 96 paths, horizon 2000, including independent source calibration. Activity audit found 108 inactive cost-floor aliases: a .25-guidance blend already retains .75 of cost, exceeding its .5 floor. All alias arrays are exactly equal on all 12 cases. **648 effective round2 configurations; 1188 across rounds**, not 1296. Original registration/status are preserved. The initial report's count is withdrawn and separately archived.
- Best round2 mean harm reduction: 4.068%, below the practical gate, development-selected and cost-only. No guidance novelty conclusion.
- Registered/ran two real development tasks with frozen training-only predictors/calendar features. At query cost .001/switch cost 1, Bike only adds monitoring cost; Beijing blended-monitor switching adds ~213.57 normalized cost because its challenger is worse. This falsifies the tested alarm-triggered controller, not all candidates. Final outcomes remain unopened. Query seeds are not independent real datasets.
- Historical H2c anchor reproduced exactly on 600 per-path outcomes, three methods, both label rates.
- Revised engine preserves all stored round1 arrays. Original post-lint record restored byte-for-byte; new legacy replay stored separately. Real-run lint required binding two immediate-use helper defaults; archived executed bytes remain in registration. No outcome-driven model/metric changes.
- Next bottleneck: separate paired-benefit certification/action-set tests and remaining learned/published baseline comparisons. No candidate is eligible for fresh final confirmation yet. Goal remains active.
