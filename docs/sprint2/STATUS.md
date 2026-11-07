# Sprint 2 status and remaining work

Updated 2026-11-05 from the integrated checkout at `/Users/nigelli/Desktop/ICML/Shift-lab`, branch `main`. The sprint and its follow-up audits are committed and pushed to `origin/main`; verify the current remote tip with `git ls-remote origin refs/heads/main`. Registered raw runs and historical analyses are preserved.

## Completed and evidenced

- R5 completed its registered all-14-source real-stream replay: 4,600 jobs, 32,200 rows, 230 episodes and 20 policy seeds per episode (seed base 2026110903). Equal-source mean J was 404.22 for R5, 404.91 for D2, 412.39 for economic replacement, 406.55 for CAMS, and 414.14 for gated adaptive-range. The R5−D2 mean of source means was −0.68; source-level effects were mixed. This is post-development cost evidence on exposed streams, not independent confirmation or causal utility. See `family_r/R5_all14_real_protocol.md` and `family_r/R5_all14_real_results.md` and the manifest under `outputs/sprint2/round5/R5_all14_real20/`.

- P6 received a post-development 20-seed-per-episode cost replay across all 14 registered real-stream sources. Equal-source mean cost was 24.41 higher than M_LRMD_SUI and 111.10 higher than gated adaptive-range; outcomes are retrospective, with no causal late-change labels. See `family_p/P6_all14_real_protocol.md` and `family_p/P6_all14_real_results.md`.
- T3's previously missing held-out Track-R panel is complete on the registered eight-alpha grid for two A5b mechanisms, matched DISCERN hosts, A5b and D2, with separate development/evaluation seed blocks. Its risk/cost values are in `family_t/T3_trackR_followup.md`; per-run manifests and raw-record checksums are in `family_t/T3_trackR_manifests.json`. It is post-development, descriptive evidence.
- The remaining primary T1/T2/T5 Track-R panels are now complete: 17 policies × eight alpha values on 20 development and 20 separate evaluation seeds per each of four null and six alternative regimes (3,200 jobs, 54,400 rows). The 86 operating points and per-run checksums are in `family_t/T1_T2_T5_trackR_followup.md/json` and `family_t/T1_T2_T5_trackR_manifests.json`; outcomes are post-development simulator evidence.
- Family R's held-out coverage follow-up is complete: 26 development-feasible policies on one common evaluation seed block, eight alpha values, four null and six alternative regimes (1,600 jobs, 41,600 records). It adds points for nine eligible policies omitted from the earlier evaluation screens. The frozen calibration map matched the original development map; the local frontier has 28 displayed points. See `family_r/R_trackR_coverage_followup_report.md`, its curve table and manifest index. This is reused-regime simulator evidence, not independent real-data confirmation or a guarantee.
- R5 received a frozen-alpha, 100-seed-per-regime post-development simulator follow-up against D2, A5b, the adaptive-range certificate, and the economic stop. Results are mixed: mean alternative net cost is lower than D2 over six regimes, but promotion rates were 15/100 on F0 null and 24–26/100 on dependent nulls, and R5 loses to D2 on late and strong-persistence alternatives. See `family_r/R5_round5_protocol.md` and `family_r/R5_round5_results.md`.
- The prior SOTA validation queue and committed-code gate re-screen completed; see
  `outputs/sota_sprint/validation.log` and `gate.log`.
- All 24 brief IDs H1–H6, R1–R6, T1–T6 and P1–P6 have recorded development outcomes; 23 are algorithm candidates and P2 is analysis-only, with
  family ledgers under `docs/sprint2/family_{h,r,t,p}/`. Negative findings are retained.
- T1's required comparisons to Model Picker, D1 and D6 are present and negative economically.
- WP1 real late-improvement result is **NOT_SUPPORTED** (10 episodes, 5 clusters, criterion unmet).
  The original WP1 real data and analyses are under `outputs/sprint2/WP1/`.
- WP2 decision flags were audited against the saved records and frozen definitions: zero mismatches
  in Run 1/3/4 records, and the separate Run-2 audit found zero mismatches in 141,360 records and
  129,580 paired harm checks; boundary test added. Current suite: `uv run pytest -q tests/sota_sprint
  tests/sprint2` -> **381 passed in 142.84 seconds** (2026-11-05 latest full-suite run). The raw-to-report audit now passes 57/57 checks, including T3, T1/T2/T5 and Family-R follow-up regenerations.
- Paper-to-code SOTA review checked primary papers and source implementations. The comparison is a
  common-contract port/adapter study, not author-native reproduction. Xu uses its acquisition
  component plus ShiftLab's certificate; it is not Xu's published certificate.
- Separate amended comparator-class sensitivities regenerated for validation, WP1 and WP2. Xu is
  excluded from the designated amended pools and retained in WP2 descriptive pooled V1 tables as a
  ShiftLab certificate + Xu acquisition composite. Historical outputs remain unchanged. The first
  validation amendment still included Choe–Ramdas and QCE ports; the strict six-port validation
  result is recorded separately below. Same-sample comparator selection remains unadjusted in the
  broader amended outputs; P6 now also
  has a post-development max-statistic sensitivity across five ports per regime, but not across
  candidates/regimes and not as independent confirmation.
- A stricter validation replay now ranks only the six `bench.CERTIFIED_PUBLISHED` ports. It preserves
  the earlier Xu-excluded adapter-pool sensitivity as historical, clearly labeled analysis. In the
  strict pool, A5b/A1b are null-safe but meet only 2/5 iid non-inferiority checks; no H2 candidate
  passes the joint rule. Comparator selection still uses these evaluation seeds, so results are
  descriptive. `audit_raw_to_reports.py` now regenerates both outputs.
- WP1 and WP2 now have separate strict-pool sensitivities. WP1's supplemental 1,044-job replay fills
  the missing `discern_design_floor` comparator; its complete 6/6 strict panel retains the same
  selected late-class port and NOT_SUPPORTED verdict. WP2's six-port pool retains positive H2, H4 remains false, and 4/6 ports
  meet the H1a twin condition. The original mixed adapter panels remain preserved and explicitly
  labeled; all these analyses reuse exposed data and do not adjust same-sample selection.
- WP1's altered-setting sensitivities now have all six published-certificate ports at B={100,400},
  delay multipliers={0.5,2} and c_s={2,10}, over the registered 26 late/reversal episodes. The
  late-class selected comparator changes only at B=400; every RMM-gated interval still includes zero.
  This closes the earlier reduced-pool gap but remains same-sample descriptive analysis.
- CAMS-MAX's source-checked core is now exposed as `cams_max_adapter` under the context-free
  constant-policy specialization supported by the loss streams. Its three-seed replay over all 348
  WP1 real episodes gives mean J 3.73 [1.30,5.60] above CAMS, with no clear improvement on late or
  reversal episodes. The exact comparison and its deployment-adapter limits are documented in
  `SOTA_BENCHMARK_AUDIT.md` and `wp1/cams_max_comparison.json`; the focused CAMS source tests pass
  (10 passed, 6 skipped). Matched validation now also covers 21 synthetic regimes × 100 seeds,
  seven in-class null/adverse regimes × 1,000 seeds, two out-of-class nulls × 1,000 seeds, nine
  cached real sources × 10 seeds and five fresh real sources × 20 seeds, with same-seed CAMS
  controls for the null panels. The JSON report shows CAMS-MAX has higher mean synthetic cost in
  20/21 regime means; its equal-source real-data ΔJ is +4.24 [1.95, 6.92] on cached sources and
  +1.99 [−0.51, +4.41] on fresh sources. These remain descriptive post-development comparisons,
  not independent confirmation or guarantee tests. Full method scope, per-panel results and exact
  commands are in `CAMS_MAX_VALIDATION.md` and `CAMS_MAX_VALIDATION.json`.
- WP2's fixed-cost H5 comparison now has an additional historical sensitivity on nine previously
  exposed Atlas v2 sources: 126 realized-positive episodes across nine source clusters. Paired
  A5b−QSG and D5−D2 contrasts show higher net costs for the first policy, with retrospective episode
  selection and fixed-cost limitations recorded in `wp2/CACHED_REAL_H5_SENSITIVITY.md`.
- A dated post-development WP1 reversal protocol was frozen and run on 100 paired seeds across three
  synthetic reversal regimes and four matched hosts. E_rb minus matched RMM mean net cost: **-6.65**,
  95% t CI **[-7.31,-6.00]**. This is scoped simulator evidence, not real-data transfer or a
  confirmatory theorem test. See `wp1/AMENDMENT_20261104_E_RB.md`, `wp1/RESULTS.md`, and
  `wp1/erb_reversal_postdev100.json`.
- H2's previously outstanding Round-5 follow-up is now complete under a frozen post-development
  protocol: 100 paired synthetic seeds, 1,000 seeds on four first-order Markov nulls, and three
  paired seeds across all 14 available real loss sources. H2 stayed below .05 on each tested Markov
  null (1–8/1,000 promotions), while D2 reached .192/.660/.815 on the three persistent nulls.
  H2's equal-source real cost was +81.2 [38.1,136.1] vs D2 and +71.7 [30.1,126.4] vs
  `gated_adaptive_range+front`. This supports a scoped V2 robustness/economic trade-off, not an advantage;
  all data are reused and post-development. See `family_h/ROUND5_H2_AMENDMENT_20261104.md` and
  `family_h/round5_h2.md`.
- P4's ledger-requested HMM-null follow-up is complete: on the fixed out-of-class HMM generator,
  A5b promoted 176/1,000 (Wilson 95% CI [.154,.201]); P1_renew 54/1,000 and P1_union 44/1,000,
  both with intervals crossing .05. The HMM is outside their declared first-order Markov nulls;
  this is a misspecification stress result, not a guarantee test. See
  `family_p/P4_hmm_round5.md` and its frozen protocol in `P4_misspecification.md`.
- Three leaderboards, a reproduction index, and an internal independent-review record now exist:
  `LEADERBOARD.md`, `REPRODUCIBILITY.md`, `INDEPENDENT_REVIEW.md`.
- The old Sprint 1 ranked view is now visibly marked historical and points to the amended Sprint 2
  leaderboard; its archived JSON and rank values remain preserved as historical data.

## Current status

- The numeric audit now reproduces the principal amended analyses and H/R/T/P Track-R outputs exactly.
  The rerunnable audit (`scripts/sota_sprint/audit_raw_to_reports.py`) now runs inside the pinned `uv`
  environment and passes all 52 generated-vs-saved checks, including strict published-pool validation,
  WP1 and WP2, and the corrected Family H replay. The rerun also fixed two WP2 table-note generator
  mismatches and NaN comparison handling. In addition to the amended validation,
  WP1/WP2, P6 follow-ups, and family Track-R outputs, it exactly regenerates the Family H and T
  development JSON summaries (and T Markdown) from saved records, recomputes 315 Family R
  Track-E/V metric cells, regenerates the P1 diagnostic, and verifies the P2 episode-level V1/V2
  table from saved runs. Manual corrections are recorded in `CLAIM_RECONCILIATION.md`; that review is broad but does not cover every sentence in every candidate narrative.
- A no-Xu pooled WP2 sensitivity now separately removes the Xu acquisition composite from H2/H4/H6 pooled V1 summaries. H2 remains positive (`adv_rest` .0122 [.0063,.0180]); the conjunctive H4 criterion remains unsupported, and registered H1b/H6b limits still fail. See `wp2/NO_XU_POOLED_SENSITIVITY.md`.
- The candidate registry now matches the family ledger on H2 and P4 Track E/V text, incorporating H2's Round-5 follow-ups and using consistent out-of-class HMM wording for P4. The expanded per-candidate schema and manifest path checks are summarized below.
- Registry/ledger coverage has the required per-candidate fields. The strengthened audit now checks all 24 entries, required schema, shared-field parity, artifact paths, and all referenced run-manifest paths. Its structural audit passes with no missing fields, paths or mismatches (`registry_audit.json`). The separate provenance result is explicitly **PARTIAL**: H1–H4 include F0/F7 evidence derived from the H/screen1 partial run, which has no original manifest, and custom P1/P2/P3/P5 analysis steps did not emit original manifests. `legacy_seed_provenance.json` captures output hashes where available, recovered seed rules, command sources and these limits; it is a retrospective reconstruction, not a replacement run-time manifest. T2/T3/T6 label the Choe–Ramdas port as historical exploratory evidence rather than an author-native SOTA comparator.
- A WP1 prose-to-results audit matches class counts, cluster distributions, classifier sensitivity counts, 106 primary-contrast cells, 63 sensitivity-table cells, late-class cost/verdict claims, reversal operating metrics, false-rollback narrative ratios, twin-null promotion rates, and Track-R target wording to the corresponding saved analyses: 9 groups, 293 checks, no discrepancies (`wp1/report_claim_audit.json`). The sensitivity table intentionally uses the historical comparator pool that retains Xu's acquisition adapter; the amended primary analysis excludes it. Other WP1 diagnostic prose remains only partially reconciled.
- A broader prose pass caught a leaderboard attribution error: six null-rate counts in the P6 1,000-seed follow-up were labeled A5b but came from P6_LRMD_U. The leaderboard now reports both policies' rates from the raw records, clearly labels A5b as the comparator arm, and distinguishes the separate P4 HMM follow-up. WP1's uncovered diagnostic prose was independently spot-checked against its saved sources with no further factual mismatches found; process-timing assertions remain unverified from result artifacts.
- WP2 H5's registered paired comparisons (A5b−QSG and D5−D2) were present in the result JSON but missing from the human-readable reports. The table generator now includes paired cost, delay, label and promotion-rate differences for the fresh-real positive-advantage subset and all six synthetic alternatives, with pairing and selection caveats. Registered and both amended table variants have been regenerated; exact reproduction passes in the raw-to-report audit.
- WP2 benchmark prose now describes its elements as benchmark features and explicitly avoids presenting them as settled novelty; the prior-art scope remains open for review.
- WP2 has a retrospective decomposition of all-in excess economic cost over its saved primary records and all eight Run-2 variants: 200,760 records in 1,205 policy/regime/run cells, with 2,000 cluster-bootstrap replicates per cell. It separates prediction-loss change, label expenditure, and switch expenditure, and reports positive-cost rates. These accounting and predictive quantities are not application-level decision harm because causal application utility is unavailable; they are also not a prospective promotion guarantee. Run-2 horizon/delay variants re-window the same event streams. See `wp2/REALIZED_HARM.md` and `wp2/realized_harm.json` (legacy filenames/schema naming).
- WP1's missing post-switch diagnostic is now computed by replaying 1,044 primary real episode-seed combinations for four E_rb hosts with event traces (4,176 rows). Evaluator-side false rollback classifications are reported by class and source cluster in `wp1/false_rollback_audit.json`; observed rates are 100% for the small late-improvement class, 8–15% for reversals, and 68–78% for stationary-better episodes. These are retrospective segment-mean diagnostics, not conditional-validity estimates.
- The A2-omitted E_swcert Track-R coverage gap was filled in a separate post hoc run: 20-seed development and evaluation across the registered ten regimes and eight-alpha grid. E_swcert has no selected R5 point. At R10, alpha .005 produced an evaluation point risk of .0625, below the .10 target, while the 95% Wilson interval upper bound (.138) crossed the target. See `wp1/protocol.md` Amendment A4 and `wp1/trackR_E_swcert.json`; this one-policy curve is not a cross-method Pareto comparison.
- The Giacomini–Rossi One-time Reversal statistic (2010, Proposition 3) was implemented and applied to all 348 registered non-twin WP1 episodes. Its raw-product HAC estimator and tabulated critical values are tested; the raw-to-report audit reproduces the JSON and Markdown exactly. Findings are retrospective and unadjusted, reuse the same losses that defined WP1's classes, and do not establish asymptotic assumptions. See `wp1/gr_one_time_reversal.json`.
- A post hoc WP1 label-clock vs elapsed-timestamp RMM replay is now complete for five timestamped fresh UCI datasets: 62 episodes, three paired policy seeds, 372 policy rows. Equal-dataset mean ΔJ (timestamp minus label-clock) is −0.61; five-dataset cluster-bootstrap 95% CI [−5.85, +2.41]. The interval is coarse and includes zero. Cached loss-only streams and publication-time feedback delays remain uncovered. See `wp1/clock_ablation_posthoc3.md/json`.
- A separate P-family development audit passes 17 groups / 7,139 cells: 5,980 P1 summary fields,
  all 27 selected paired-contrast values and interval bounds, plus null-promotion narrative counts
  in `P1_power.md`, and all 40
  displayed P1 diagnostic-table cells; P2 V1/V2 rates and twin A500; selected P3 harm contrasts;
  106 P4 table values; P5 synthetic/real paired-cost means and intervals, cache identity, comparative-cost and null-switching claims; P6 synthetic contrasts and fresh-real
  means; all 768 P3 switch-cost reweighting values; and P2 narrative correlations and conditional-harm
  claims, P3 narrative/registry cost-grid ranges, and the P3 paired development-cost range against
  source trajectories. It corrected P2's A_H endpoint notation to match the code's
  half-open [τ, τ+H) window. P2's grid has 16 settings (10 null and 6 alternatives), each with 12 seeds. See
  `family_p/development_audit.json`.
- The latest uncovered-prose audit found and corrected an overgeneralized H-diagnosis claim: finite
  S-dep-r95 results no longer imply impossibility for every V2-valid method. It also corrected WP1
  per-dataset labels from clusters to episodes and qualified WP2 preregistration chronology as a
  protocol-recorded claim that current artifacts cannot independently timestamp. WP1 secondary
  diagnostic values and the reviewed WP2 definitions/results matched their saved analyses. Exact
  corrections are in `CLAIM_RECONCILIATION.md`; the six P-family narrative reports have since had a
  sentence-level consistency pass. Sprint 2 reports have no embedded or locally generated figures.
- A comparator audit found that Family H's old `best_cert` summary pool included Xu's acquisition
  adapter and the non-native Choe–Ramdas port, while omitting registered certificate ports. Those
  selected-port claims are withdrawn for published-comparator purposes; historical runs remain
  preserved. `fam_h.summarize` now defaults to the shared `CERTIFIED_PUBLISHED` pool and retains an
  explicit legacy mode for reproducing old outputs. The matched 20-seed replay across the five
  reused streams is complete: all H candidates cost more than D2 (+100.9 to +123.0 J) and the two
  adaptive-range ports (+34.2 to +56.4 J and +85.7 to +107.8 J), while all have lower point cost
  than gated deployment (only H1–H4 intervals exclude zero). Source records and the run manifest
  are preserved; the analysis and H registry/ledger are updated. See `SOTA_BENCHMARK_AUDIT.md`,
  `family_h/corrected_real_20.md` and `family_h/README.md`.
- A source-to-claim review of the 18 H/R/T candidate entries found and corrected seven numeric or
  attribution errors/ambiguities (H2/H3/H6, R4, T1/T2); P4 wording was narrowed to avoid implying an out-of-class guarantee. Subsequent P-family review also corrected P2, P3, P4, P5 and P6 claims; see the reconciliation table. The claim-level corrections and source paths are
  recorded in `CLAIM_RECONCILIATION.md`. A targeted prose pass also narrowed P1 information, P4
  mechanism, and P6 causal interpretation claims. The Sprint 2 reports contain no embedded figures
  or figure artifacts; legacy plots outside those reports are not cited. A targeted sentence-level
  pass of the six P-family narrative reports is recorded in `CLAIM_RECONCILIATION.md`; it does not
  independently prove theorem claims or review every candidate-registry sentence.
- The consolidated cost-risk report now has its own audit: all 344 displayed operating points
  match the corresponding Track-R JSON (`cost_risk_audit.json`). This verifies report lineage, not
  calibration or the scientific validity of empirical risk targets.
- The omitted H1/H3 Track-R grids have now been completed as a post hoc follow-up: eight alpha values,
  20 development seeds per regime (2026110701) and 20 separate evaluation seeds per regime
  (2026110711), with D2/A5b controls. Merged Family-H curves cover H1-H6 and the two controls at all
  six targets. H1/H3 do not add a Pareto point: at R5 their costs are 376.8/378.1 versus H2's 374.7;
  at R10-R30 they cost 371.7/374.0 versus H4's 369.6, at the same point risk .062. H5/H6 now have
  Track-R curves: risk .0375 [.013,.105] at alpha .5; H5 costs 382.3, while H6 reserves cost
  382.9/384.3/385.3. A dedicated 15-episode timing recheck per candidate over three regimes was
  below .36s, but does not establish a worst-case bound. The expanded 344-row report audit passes.
  See `family_h/track_R_all.json` and `COST_RISK_PARETO.md`.
- External/human independent review remains open; internal reviews do not substitute for it.
  A reviewer handoff is now prepared in `EXTERNAL_REVIEW_PACKET.md`, with scoped questions, exact evidence paths, reproduction entry points and a findings template. It does not count as a review; the reviewer record remains blank pending an independent reviewer.
- The latest Sprint test command passes: `uv run pytest -q tests/sota_sprint tests/sprint2` —
  381 passed in 142.84 s on 2026-11-05. The raw-to-report audit passes
  57/57 checks after adding T3, T1/T2/T5 and Family-R follow-up regeneration; tests verify implementation checks, not research or
  theorem claims.


## Outstanding before the brief's exit conditions can be called complete

1. **P6 evidence is complete for this sprint; its open scientific limitation remains.** The corrected
   certificate-port comparison and twin-bike replay are complete, but both are post-development. The
   corrected P6 analysis adjusts over its five included ports within each regime; it does not adjust
   across regimes or candidates. Twin-bike results do not clear the .0936
   screening convention (P6 .076, split-cluster 95% CI [.036,.122]) and come from 20 splits of one
   reused dataset. No fresh independent real dataset has been added.
2. **Final source-to-claim reconciliation.** The reproducible audits cover the principal amended
   reports, WP1 false-rollback traces, WP2 no-Xu pooled sensitivity, H/T development summaries,
  315 R Track-E/V cells, seventeen P-family checks, and H/R/T/P Track-R outputs, including the H1-H6 Track-R completion. P5 has a separate K3/K4 Track-R panel; T3, T1/T2/T5 and Family R have held-out follow-ups, all included in the 344-row Pareto-table audit. The 57-check raw-to-report audit passes. The H/R/T/P candidate source review corrected numeric and interpretation errors documented in
   `CLAIM_RECONCILIATION.md`. Registry-to-ledger shared fields now match under the registry audit.
  A targeted final prose pass has now covered H/R family reports, P-family/WP1/WP2 narratives, and
  the SOTA/exit summaries; it corrected the economic interpretation of conditional predictive loss,
  retrospective WP1 class labels, and a stale Family-H completion sentence. The T-family and 24-entry registry consistency passes also corrected the Track-R alpha-grid description, T3 held-out-evaluation status, and stale T2/T3/T6 comparator wording in the canonical ledger. No material numeric contradiction was found in the registry spot checks; they did not rerun every analysis. Independent theorem-assumption review remains open;
   the internal source mapping is in `THEOREM_SCOPE_AUDIT.md`.
   The SUI log-floor caveat is now bounded for saved Sprint 2 runs: all 214 manifests with a
   recorded horizon specify T=2000, and the smallest implemented factors give cumulative log lower
   bounds −24,412.25 (null array) and −13,815.51 (alternative array), far above `LOG0=−1e9`.
   Reproduce with `scripts/sota_sprint/audit_sui_clamp_bound.py`; output is `sui_clamp_bound.json`.
   This finite-horizon arithmetic bound does not verify the method's statistical assumptions.
  No figures are embedded or stored under
  `docs/sprint2` or `outputs/sprint2`; PaperBanana is unavailable in this environment, so required
  research visuals remain open. See the inventory in `CLAIM_RECONCILIATION.md`.
3. **Round 5 for other advances.** Existing ≥100-seed synthetic and 1,000-seed null runs cover the
   screened mechanisms and all applicable reused real streams are represented in family analyses.
   The newly run E_rb reversal follow-up addresses one promising branch. P6 twin-bike is complete; it does not resolve the null concern.
   Avoid presenting reused streams or post-development seed changes as unseen-data validation.
4. **Round 6 focused combinations.** A consolidated report now records T6, P6_RRD, D2+A5b and
   the failed RMM/SUI interaction: `ROUND6_FOCUSED_COMBINATIONS.md`. These are earlier development
   combinations, not a new post-Round-5 experiment. The decision audit is complete; a fresh hybrid
   experiment is not justified by current evidence and is not claimed as completed. No hybrid earned further advancement; do not
   repeat the failed RMM/SUI merge without a different mechanism.
5. **Round 7/external independent review.** Internal read-only agent reviews are documented, but
   they do not satisfy ARIS/HKUSTDial review. Neither interface is available in this environment.
   Human/external review of fidelity, comparator correctness, statistical claims, novelty and
   result-to-claim alignment remains open.
6. **Independent confirmatory inference.** P6 now has a paired max-statistic bootstrap adjustment
   across the five certificate ports available in its corrected run, separately within each regime.
   The P6 follow-up remains post-development, and other amended sensitivities still select on their
   evaluation samples. Freeze choices on independent development data and evaluate on untouched data
   before making confirmatory claims; the current P6 adjustment does not cover across-regime or
   across-candidate selection.
7. **Git integration is complete.** The sprint and its follow-up audit corrections are on `main` and pushed to `origin/main`. Git-ignore checks confirm the newly added twin-v2 and late-loss data paths remain excluded; some older cached data files are already tracked in the base repository.

## Supported verdict

There is no universal SOTA claim. The clearest paper opportunity remains the empirical study of
conditional versus marginal validity, predictive outcomes, and excess economic cost under dependence
(P2), subject to explicit estimands and claims. Application-level decision harm is not identified by
the current data. WP1's real-late result is negative; E_rb has a scoped synthetic reversal result.
The corrected comparator analyses do not solve selection bias. Continue the bounded empirical
benchmark contribution, pivot away from broad real-world method superiority, and keep publication
claims contingent on independent review.

## Workflow instruction

The repo AGENTS.md asks for Codex with ChatGPT setup for coding work. The user explicitly requested
not to set that up this session; local execution proceeded without claiming a connection.
