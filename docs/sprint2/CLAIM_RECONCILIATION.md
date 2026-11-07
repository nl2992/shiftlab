# Sprint 2 claim reconciliation

Updated 2026-11-05. This is an internal source-to-claim review. It is not an external audit,
independent replication, or proof of statistical validity.

## Corrected claims

| Candidate / claim | Correction | Source evidence |
|---|---|---|
| Family H, fresh-real comparator class | The original 3-seed H screen's `best_cert` pool included Xu acquisition and Choe–Ramdas adapters, omitted registered certificate ports, and therefore did not identify the best published certificate port. H1's +68..+189 and the H2 +60..+203 selected-port ranges are withdrawn for published-comparator claims. A corrected 20-seed replay found each H candidate costlier than gated adaptive-range (+34.2 to +56.4 J) and its front variant (+85.7 to +107.8 J), but cheaper than the simpler gated-deployment port for H1–H6 (point differences -11.5 to -33.7 J; only H1–H4 intervals exclude zero). Every H candidate cost more than D2 (+100.9 to +123.0 J). These are equal-weight summaries over five exposed datasets with episode-bootstrap intervals; selected per-dataset winners are descriptive, and bootstrap treats episodes as exchangeable. | `scripts/sota_sprint/fam_h.py:LEGACY_SUMMARY_COMPARATOR_POOL`, `docs/sprint2/family_h/screen_real_fresh.json`, `docs/sprint2/family_h/corrected_real_20.md/json`, `outputs/sprint2/round5/H_corrected_real_20/manifest.json`; H1–H6 registry and ledger entries synchronized. |
| Validation H1/H2 published-comparator pool | The first amended validation excluded Xu but retained Choe–Ramdas and ShiftLab QCE ports in its selected pool. Its selected-comparator claims are therefore an adapter-pool sensitivity, not a strict published-comparator result. A separately regenerated strict analysis ranks only the six `bench.CERTIFIED_PUBLISHED` ports: A5b/A1b are null-safe but fail the full H1 rule (2/5 iid non-inferiority checks); no H2 candidate passes its combined safety and four-of-five significance rule. Same-seed comparator selection remains unadjusted. | `scripts/sota_sprint/analyze_validation.py --strict-published-dir`, `docs/sprint2/validation_strict_published_20261104/validation_results.md/json`; `audit_raw_to_reports.py` now regenerates both amended analyses. |
| WP1 comparator pool | The registered seven-member “best certified” pool was a mixed adapter panel: it included Xu's composite and the Choe–Ramdas port and omitted `discern_design_floor`. A supplemental replay evaluates that sixth port on all 348 real WP1 episode-seed combinations (1,044 jobs). The complete strict six-port panel still selects `gated_adaptive_range+front` on the 10 late-improvement episodes, and the registered NOT_SUPPORTED verdict remains. Same-episode selection is unadjusted. | `outputs/sprint2/WP1/strict_extra_discern_design_floor/manifest.json`, `docs/sprint2/wp1/strict_published_subset_20261104.json`, `wp1/COMPARATOR_CLASS_AUDIT.md`, and A7 in `wp1/protocol.md`. |
| WP2 pooled V1 “published ports” | The historical 11-member V1 port set contained six strict-pool ports plus Xu, Choe–Ramdas and QCE adapters. A six-port reanalysis keeps H2 positive, H4 false, and 4/6 H1a methods meeting the twin criterion; results remain exposed-data and post-development. | `docs/sprint2/wp2/COMPARATOR_CLASS_AUDIT.md`, `wp2/strict_published_20261104/`, A7 in `wp2/protocol.md`. |
| H2, post-development registry coverage | The candidate registry's Track E/V text had not incorporated the frozen 100-seed synthetic, 1,000-seed Markov-null and 14-source real follow-ups. It is now synchronized to the family ledger, including the equal-source cost contrasts and four null-rate estimates; the existing 3-seed fresh-real screen remains a separate result. | `docs/sprint2/family_h/ROUND5_H2_AMENDMENT_20261104.md`, `family_h/round5_h2.md/json`, and `audit_sprint2_registry.py`; structural audit passes with 24/24 entries and no mismatches. |
| H2, iid alternatives | “Identical to H1” now explicitly refers to the promotion rates. Other metrics differ. | `docs/sprint2/family_h/screen_synthetic.json`; H1/H2 ledger wording corrected. |
| H2, Track R | H2 is Pareto at R5; H4 is Pareto at R10–R20 on the selected grid. | `docs/sprint2/family_h/track_R.json`; ledger and candidate disposition corrected. |
| H3, fresh metro contrast | H3−H2 is +0.4, not −0.4 (H3 cost 183.16 vs H2 182.78). | `docs/sprint2/family_h/screen_real_fresh.json`; registry and ledger corrected. |
| H6, runtime | The 16.3 s maximum is specifically H6-r25. | `docs/sprint2/family_h/screen_synthetic.json`; registry variant label clarified. |
| R4, development alternative cost | R4-both mean J 399.351 (+36.6 paired vs D2); R4-comb mean J 375.595 (+12.8 paired vs D2). R4-comb is not 625.4; that number is its fresh-real appliances cost. | `outputs/sprint2/R/analysis/trackE_V_a05.json` (`dev`, `paired_vs_D2_dev`); `outputs/sprint2/R/analysis/real_a05.json`; registry, ledger and results report corrected. R4-comb has 0/20 promotions on F0/rho=.8 and 5/20 on rho=.95. |
| T1, Model Picker cost gap | Using full-precision means, the gap vs Model Picker is about +43.4 (not +43.3); +28.2 vs D1 and +20.5 vs D6:mp remain. The Model Picker-host contrast and interval are in `dev_summary.md` and the devA records; `contrasts.json` contains only the D1 and D6:mp contrasts. | `outputs/sprint2/T/dev_summary.json`, `dev_summary.md`, `devA/records.jsonl`, and `contrasts.json`; ledger and results report now distinguish which artifact contains each comparison. |
| T2, rho=.95 false promotions | The 0.35 rate belongs to `gated_adaptive_range+front` and `gated_deployment+QCE+front`; `T2:gated/a5b+front` is 0/20 in that screen. | `outputs/sprint2/T/dev_summary.json` and `dev_summary.md`; registry and ledger corrected. |
| P4, out-of-class A5b behavior | The 0/20 observations on tested non-HMM nulls are descriptive, not a guarantee outside A5b's declared first-order Markov null. A 1,000-seed HMM replay observed A5b promotions 176/1,000 (Wilson 95% CI [.154,.201]); this remains an out-of-class stress result. | `outputs/sprint2/round5/P4_hmm_null1000/records.jsonl`, `docs/sprint2/family_p/P4_hmm_round5.json`; `audit_raw_to_reports.py` regenerates the summary. |
| P2, real twins and target correlation | Selected-promotion positive A500 averages do not estimate persistence duration or establish transfer. At rho=.95, delay=100, M/Cpol are both .52 and Cstate is .53; these close descriptive correlations do not make targets equivalent. | `outputs/sprint2/P/p2p3/p2p3.json`; report and registry wording corrected. |
| P2, realised A_H window | The report's summation endpoint was corrected from inclusive τ+H to the implemented H-event half-open window [τ, τ+H), truncated at the episode end. A_H is a realised sum and is distinct from conditional-mean targets. | `scripts/sota_sprint/fam_p.py:_paths_eval` slices `d[tau:tau+H]`; `docs/sprint2/wp2/protocol.md` uses the same half-open convention. |
| P3, cost sweep and harm ranges | P3_follow has an additional best-other win at p=.50, rho=.80, delay=1, cs=.5 (margin -1.8). At delay=100 its loss margin ranges +14.0 to +669.5 over tested p/rho and reweighted cs; across the full reweighted grid the maximum loss is +738.4 at p=.50, rho=0, delay=1, cs=20. Certified-method harm at rho=.95, delay=1 ranges -12.6 to +21.0. Cost sweep reweights fixed cs=5 trajectories; policies were not rerun at each cost. | `outputs/sprint2/P/p2p3/p2p3.json`, `outputs/sprint2/P/final_summary.txt`, `docs/sprint2/family_p/P3_cost_sweep.json`; report and registry wording corrected. |
| P3, development-screen contrast vs A5b | The registry/ledger range +40 to +130 was not supported by the full 23-regime screen. Recomputed paired mean J differences over 20 seeds range +37.2 to +163.0; the candidate and ledger now state this scope and range. | `outputs/sprint2/P/dev_syn/records.jsonl`; recomputed by `audit_p_family_development.py`. |
| P5, pairwise certificate updates | A pairwise certificate advances on queried disagreements (`li != lj`), not every queried event. | `scripts/sota_sprint/fam_p.py:KGate.observe`; P5 report corrected. |
| P5, pairwise selection-conditional null | A shared label can be requested because another challenger is host-preferred and then updates every pairwise gate. The required null must hold for each tested pair conditional on the full pre-label query selection, including cross-pair triggers. The Track V and report wording now state this stronger condition. | `scripts/sota_sprint/fam_p.py:KGate.request_labels/observe`, `docs/sprint2/family_p/P5_multimodel.md`, and `THEOREM_SCOPE_AUDIT.md`. |
| P6, start-prior mechanism and Track R | The uniform-start-prior effect is scoped to the tested no-host synthetic paired ablation. P6_RRD has risk .050 and cost 383.8; A5b has risk .025 and cost 384.0, so these points are near-equal in cost at different observed risk. | `outputs/sprint2/P/trackR2`, `docs/sprint2/family_p/P6_late_reversal.md`; ledger and candidate interpretation corrected. |
| P4, HMM marginal gain | The marginal mean gain is `E[G_t] = dis(2p−1)`; HMM conditional `p_t` varies by hidden state, so the former pathwise/conditional statement was too strong. The “only powered method” phrase was also narrowed because other methods have zero observed promotions on some out-of-class null cells. | `scripts/sota_sprint/fam_p.py:PRegime`, `docs/sprint2/family_p/P4_misspecification.md`; interpretation corrected. |
| P4, HMM validity wording | The family ledger and registry now use matching scope: the development HMM cell and 1,000-seed follow-up are explicitly out of the declared first-order Markov null and do not test in-class validity. | `docs/sprint2/family_p/ledger.json`, `candidates.json`, `family_p/P4_hmm_round5.md`; `audit_sprint2_registry.py` passes. |
| P5, multi-model transfer | “Gate transfers to K=3–4” is narrowed to evidence in the tested development settings; it does not establish general transfer. | `docs/sprint2/family_p/P5_multimodel.md`, candidate registry and family ledger corrected. |
| P6, Amendment-6 retained fractions and reserve | Initial summary ranges applied only to two Amendment-6 regimes; later P6 runs show regime-dependent retained fractions. The reserve ablation is “similar, not identical,” and did not recover late performance in the tested configuration; no causal attribution to host front-loading is made. | `docs/sota_sprint/merge/merge_results.md`, `outputs/sprint2/P/final_summary.txt`, `docs/sprint2/family_p/P6_late_reversal.md`; claims scoped to exact regimes and runs. |
| P1, hazard parameterization boundary | The hazard map's one-to-one claim now states its necessary domain `a < 1`; at `a = 1` both exit hazards are zero and `p` is not identifiable. | `docs/sprint2/family_p/P1_power.md`; checked algebraically from `h1=(1-a)(1-p)` and `h0=(1-a)p`. |
| P1, oracle-to-SUI gap | The narrative now scopes the 2.3–2.8 nat residual to spaced rho=.8 settings (G=7,12), and states the tighter G=1 residual is 4.4 nats. | `outputs/sprint2/P/p1diag/p1diag.json`; reconciled to the displayed simulation table by the P-family audit. |
| Leaderboard, 1,000-seed null-rate attribution | The six-regime null counts previously labeled A5b were P6_LRMD_U counts. In the P6 1,000-seed null follow-up's A5b comparator arm, rates are 1/2/3/16/60/176 across F0, rho=.8, rho=.95, order-2, semi-Markov and HMM; P6 has 10/2/6/13/79/139. | Recounted `ever_promote` per policy/regime from `outputs/sprint2/round5/P6_LRMD_U_null1000/records.jsonl`. This is not the separate P4 HMM follow-up, whose A5b HMM count is documented in `family_p/P4_hmm_round5.md`. |
| WP2 H5 paired contrasts | The registered H5 paired A5b−QSG and D5−D2 comparisons were computed in JSON but omitted from all generated tables. Added the real positive-advantage subset contrasts and all six synthetic-alternative contrasts, with paired intervals and selection/cluster caveats. | `docs/sprint2/wp2/results.json` (`H5`); `scripts/sota_sprint/wp2_analyze.py`; tables regenerated for registered, amended no-Xu and amended no-Xu-pooled outputs. |
| H2/P6 comparator labels and R-family artifact paths | The H2 14-source +71.7 contrast is against `gated_adaptive_range+front`, not the no-front port. P6's “vs Xu” shorthand refers to `xu_acquisition_only` (Xu acquisition plus ShiftLab's paired V1 certificate), not Xu's published certificate. R1–R6 result paths were missing the `outputs/sprint2/R/` root; paths now resolve from the repository root. | `family_h/round5_h2.md`, `family_p/P6_late_reversal.md`, `candidates.json`, and `registry_audit.json`. |
| WP2 benchmark novelty phrasing | “What is new here” was changed to “Benchmark features” and explicitly identifies the text as a description of the contract, not a resolved novelty claim. | `docs/sprint2/wp2/BENCHMARK.md`; the SOTA audit leaves prior-art scope for review. |
| WP1 amendment chronology | The results report now attributes the pre-results chronology to the protocol's record and states that result artifacts cannot independently verify when the relevant outputs were first viewed. | `docs/sprint2/wp1/protocol.md`, `docs/sprint2/wp1/RESULTS.md`; this is a provenance limitation, not a numerical discrepancy. |
| H diagnosis C4, Markov evidence limit | The diagnosis and README now describe a tested evidence-information trade-off on the finite S-dep-r95 run. They no longer claim that every method valid for the stationary-Markov null must fail to recover D2's promotion rate; no general impossibility proof was established. | `docs/sprint2/family_h/diagnosis.md` lines 86–95 and 125–129; `family_h/README.md`; the saved diagnostic supports only the listed methods, generator and 2,000-event horizon. |
| WP1 dataset class-count labels | The per-dataset entries are episode counts, not distinct source-cluster counts. The headings now say “episodes by dataset,” consistent with the 10 late episodes in 5 clusters and 16 reversal episodes in 7 clusters. | `docs/sprint2/wp1/RESULTS.md` lines 45–50; `wp1/results.json` and `wp1/results_amended_no_xu.json`. |
| WP2 protocol chronology | The protocol now distinguishes its dated registration record from independently verified preregistration. Existing files do not establish whether the protocol preceded all policy runs or v2 twin-split construction; those chronology statements are attributed to the protocol record. | `docs/sprint2/wp2/protocol.md` opening and Amendment 0; no immutable timestamp/signature or run manifest verifies chronology. |
| P1 null-promotion scope | The prose now separates the 10 designated null regimes from the additional out-of-class HMM stress. The first four P1 variants are 0/20 on the designated set; on HMM, the first three remain 0/20 and P1_A5b_c10 matches A5b at 3/20. | Recomputed from `outputs/sprint2/P/dev_syn/records.jsonl`; `docs/sprint2/family_p/P4_hmm_round5.md` separately reports the larger 1,000-seed HMM follow-up. |
| WP1, Giacomini–Rossi implementation | The Proposition 3 implementation was checked against the paper's joint statistic, 15–85% trim and tabulated critical values; its HAC uses the paper's raw cross-products under the zero-mean null. The earlier centered-HAC draft was corrected before reporting. | `scripts/sota_sprint/wp1_giacomini_rossi.py`, `tests/sprint2/test_wp1_giacomini_rossi.py`, primary source [Giacomini & Rossi (2010)](https://doi.org/10.1002/jae.1177). Its assumptions and same-data class selection remain limitations. |
| P1, information and hazard wording | The free-persistence null restriction is stated as h0 <= h1 for a < 1, with evidence from observed transitions and run exits; the prose no longer says completed runs are the only information or that no valid test can recover information loss. The limitation is now explicitly at fixed query budget/gap, with more queries or wider gaps noted as possible offsets. | `docs/sprint2/family_p/P1_power.md`; Fisher values are reconciled by `audit_p_family_development.py`. |
| P4, dependence mechanism interpretation | Elevated promotion across the listed misspecified nulls is retained as descriptive evidence. The report no longer attributes the pattern specifically to sign-run length or treats co-occurrence as causal identification. | `docs/sprint2/family_p/P4_misspecification.md`; rates are covered by the family P audit and 1,000-seed HMM follow-up audit. |
| P6, real-cost mechanism interpretation | The real-data cost gap and twin-null promotion rates are described as directionally consistent with extra looks from a cheaper start prior, without attributing the real cost difference causally to those extra looks. | `docs/sprint2/family_p/P6_late_reversal.md`; costs and twin rates are reconciled to the corrected comparator and twin-bike analyses. |
| P5, real-stream interval scope | “Only household_power and metro have CIs that exclude 0” is explicitly limited to the real-stream comparisons; the synthetic K3/K4 null rows also have paired-cost intervals that exclude 0. All 20 real paired mean and half-width cells were recomputed from episode-level K-screen records and matched. | `docs/sprint2/family_p/P5_multimodel.md`, `outputs/sprint2/P/kscreen/kscreen.json`; reproducible calculation uses paired episode differences and 1.96·SD/√n. |
| P5, multi-model cache fidelity | The stated exact match of the first two K=4 model-loss columns to the committed two-model cache was checked directly on all five datasets; all 5 arrays match. | `scripts/sota_sprint/fam_p.py:kbuild`, `outputs/sprint2/P/kstreams/*.npz`, `data/sprint_fresh_losses/*.npz`. |
| P5, comparative-cost and null-switching narrative | The “4/6 synthetic, 5/5 real cheaper than native CAMS,” real-stream confidence-interval attribution, and K3/K4 null switch rates (.05 vs .95–1.00) are checked from paired records. | `scripts/sota_sprint/audit_p_family_development.py`, check `P5 cost, confidence-interval and null-switch prose`. |
| P5, separate K-model Track R | The former “not run” cell was a scope gap, not an inapplicable track: K3/K4 null and alternative regimes support a separate empirical alpha grid. Selection uses development null risk and alternative cost; separate evaluation uses 20 seed blocks. The intervals are descriptive and the full-selection conditional null remains unverified. | `scripts/sota_sprint/p5_trackr.py`, `outputs/sprint2/P/trackR_K/`, `audit_cost_risk_pareto.py` (six P5 table rows). |

## Candidate-registry synchronization (2026-11-04)

A field-by-field comparison of all shared candidate-registry and family-ledger fields found stale
claims in H1/H3 result-artifact paths; H2 result-artifact paths, disposition and next action; H5/H6
runtime-disposition wording; and P2/P3/P4 result-artifact or disposition text. These were synchronized
to their family ledgers. No shared status, implementation, result-artifact, Track E/R/V, disposition,
or next-action field now differs across the 24 entries. H5/H6 `run_config` is deliberately not mirrored:
the registry records the later Track-R completion command, while the ledger retains its full original
screen commands. The expanded `audit_sprint2_registry.py` checks all shared fields, exact candidate
coverage, and artifact existence; `registry_audit.json` passes with zero mismatches.

This synchronization check proves registry-to-ledger consistency, not the truth of the mirrored
claims. The numerical and interpretation review remains the source review recorded above: H/R/T
primary metrics were compared with their cited summaries; P-family report claims have explicit
numeric audit coverage; free text outside those cited/recomputed claims still requires human review.

## Additional report-cell checks

- The WP1 report check verifies episode/class and named cluster counts, classifier rule-sensitivity
  claims, the primary paired-contrast table, selected late-class mean-cost/verdict statements, and
  the sensitivity table against its correctly scoped historical analysis, and false-rollback
  numerator/denominator claims against trace summaries, the reversal operating table, twin-null
  promotion rates, and the E_swcert/Xu Track-R operating-point wording (293 checks). It does not
  cover every WP1 table or secondary diagnostic; both result JSON files are regenerated from raw
  records by the separate raw-to-report audit.
- The P-family development check now covers 7,139 numeric cells across 17 groups, including P1's
  selected power-repair contrast table and null-promotion narrative, plus P2
  target/harm statements, P3 cost-grid / development-cost range claims, P5 real paired cost
  means/intervals, cache identity of the first two K=4 columns on five datasets, and selected P5
  comparative-cost and null-switch claims. See
  `family_p/development_audit.json`.

## Claim checks performed

- **H1–H6:** Read-only review compared candidate/ledger claims with the family synthetic, fresh-real,
  twin, and Track R summaries. Aside from the corrections above and the stated precision clarifications,
  the reviewed primary numeric claims matched those source summaries. The evidence is development or
  reused-stream evidence as labeled in those reports.
- **R1–R6:** Read-only review compared Track E/V claims with
  `outputs/sprint2/R/analysis/trackE_V_a05.json`, Track R claims with `risk_curves.json`, and R6's
  joint selector claims with `r6_joint.json`. The R4 figures above were the identified mismatch;
  remaining claims checked in that review matched their cited outputs.
- **T1–T6:** Read-only review compared the candidate/ledger claims with the development summaries,
  contrasts, Track R and real-twin summaries. The T1 rounding and T2 attribution corrections above
  were identified; remaining numeric claims checked in that review matched those sources.
- **P1–P6:** `audit_p_family_development.py` recomputes seventeen report groups (including 5,980
  P1 summary fields, the displayed P1 Fisher/simulation tables, P2 V1/V2 and twin outcomes, selected
  P3 harm and all 768 switch-cost reweighting cells, P4 tables, P5 synthetic/real cost tables, and
  P6 development contrasts/fresh-real means). The P1 diagnostic is also regenerated
  by `audit_raw_to_reports.py`. P-family interpretation changes above correct scope, attribution, and
  interpretation errors; they do not establish statistical validity. A sentence-level reading pass
  also covered the six narrative reports (`P1_power.md`, `P2P3_objectives_harm.md`,
  `P4_misspecification.md`, `P4_hmm_round5.md`, `P5_multimodel.md`, and `P6_late_reversal.md`).
  It found the previously listed scope and attribution issues; no additional factual contradiction
  was identified in this pass. This was a manual consistency review against cited local analyses,
  not independent reproduction of every sentence or proof verification of theorem claims. Candidate
  registry prose and source-level proof assumptions remain outside that pass.

## Visual artifact inventory

The current Sprint 2 family, WP1 and WP2 reports contain no embedded Markdown figures, and there are
no image/PDF/SVG artifacts under `docs/sprint2` or `outputs/sprint2`. Legacy plots elsewhere under
`outputs/` are not referenced by these current reports and are outside this sprint's displayed-claim
set. No new empirical figure was produced for this sprint; therefore there is no exported sprint
figure to reconcile against source values.

## Still not established

This reconciliation does not verify every numeric prose claim in every report, establish the
validity assumptions of every method, verify causal interpretation of real-data labels, or provide
external independent review. Remaining work includes registry prose review, theorem-assumption
verification, untouched-data confirmation if confirmatory claims are desired, and review of any
future figures. Internal read-only reviews are not a substitute for the requested human/external
ARIS/HKUSTDial audit.

The Sprint 2 Markov SUI cumulative log-floor concern has a new bounded check: all 214 saved run
manifests with a recorded horizon specify T=2000, and the implemented per-event factor grid yields
log lower bounds well above `LOG0=-1e9`; the bound is reproducible with
`scripts/sota_sprint/audit_sui_clamp_bound.py` and saved in `sui_clamp_bound.json`. This resolves
floor non-attainment for these saved-run horizons, but not larger horizons or independent proof
review.

## R5 post-development follow-up (2026-11-05)

The frozen-alpha R5 run now has a protocol, manifest, raw records, and analyzed results at
`family_r/R5_round5_protocol.md`, `outputs/sprint2/round5/R5_eval100_a002/manifest.json`, and
`family_r/R5_round5_results.json`. The family ledger, candidate registry, leaderboard, and Track-R
summary now all distinguish the earlier 20-seed development-selected frontier from this 100-seed
per-regime fixed-alpha sensitivity. The result is mixed: pooled alternative net cost is lower than
D2, but promotions are elevated in three tested null regimes and R5 loses on late and
strong-persistence alternatives. The registry audit passes with no field or source-path mismatches.
This new seed block is still post-development simulator evidence, not unseen-data confirmation.
