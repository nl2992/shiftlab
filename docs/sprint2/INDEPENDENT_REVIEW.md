# Independent review record — Sprint 2 (2026-11-04)

## Review status

Two read-only research/code reviews were completed using independent agents in this Codex task tree:

- Comparator-method audit: checked the amended validation, WP1 and WP2 classifications and claim
  implications. Findings are incorporated in `SOTA_BENCHMARK_AUDIT.md`, the amended outputs, and
  `wp2/DECISION_FLAG_AUDIT.md`.
- Completion audit: reconciled the frozen brief, candidate registry, ledgers and run artifacts. Its
  findings are summarized in `STATUS.md` and below.

These are internal agent reviews, not external peer review, not a rerun of the full benchmark, and
not an ARIS/HKUSTDial execution. No ARIS or HKUSTDial interface is available in the active tool
catalog. An independent reviewer agent was used for a separate read-only audit, but this does not
satisfy any institutional review requirement associated with those systems.

## Findings to preserve

1. Xu is an acquisition adapter paired with ShiftLab's V1 certificate in the existing comparisons;
   it is not Xu et al.'s published certificate. Amended outputs exclude it from published-method
   ranking and powered sets. WP2 retains the descriptive V1 composite under an explicit label.
2. Choe-Ramdas, QCE and related entries are ports/adapters under a common benchmark contract, not
   author-native deployments. The paper-to-code audit limits all related claims accordingly.
3. Same-evaluation-sample selection of the lowest-cost certified comparator remains unadjusted.
   Amended comparisons are descriptive sensitivity analyses, not selection-adjusted inference.
4. WP1 real late-improvement criterion is `NOT_SUPPORTED`; the reversal finding is not independently
   validated by the original registered run. A prospective-style amendment dated 2026-11-04 defines
   a post-development, fresh-seed E_rb follow-up; its status and interpretation are reported in
   `AMENDMENT_20261104_E_RB.md`.
5. Candidate-level Track R/V completeness, additional Round 5/6 work, and final external review are
   not fully satisfied. See `STATUS.md` for the exact open items.

## Required before paper claims

A human reviewer should verify the final candidate matrix and raw-to-report lineage, assess the
selected-comparator inference plan, and approve any publication-facing claim. This review record
must not be cited as external validation.

## Follow-up internal completion audit (2026-11-04)

A separate read-only audit checked the full frozen brief against the family ledgers, registry and
linked artifacts. It confirmed structural coverage of all 24 candidate IDs and no missing registry
artifact paths, but did not recalculate all metrics. Subsequent numeric audits now reproduce the
principal derived reports and the consolidated 197-row cost-risk table; they do not cover every
narrative claim. The 1000-seed P6 twin-bike replay does not establish transfer.
The audit also noted the prior WP2 flag audit had omitted Run 2. That gap is now addressed by
`audit_wp2_run2.py`, which found zero mismatches across 141,360 stored Run-2 rows and 129,580 paired
harm checks. The audit outputs are internal review evidence only; they are not external peer review.

A post-development P6 max-statistic bootstrap now adjusts comparison over the five certificate ports
available in that run, regime by regime (`family_p/P6_selection_adjusted.json`). It does not adjust
across regimes, candidate development or other analyses, so it does not provide confirmatory
superiority evidence.


## Raw-to-report reproduction follow-up (2026-11-04)

The lead reran the amended validation, WP1 and WP2 analyses and H/R/T/P Track-R analyses from saved
raw records. Exact JSON comparison (1e-12 numeric tolerance) and byte comparison of Markdown pass
for the amended reports; H and T development summaries also regenerate exactly, and 315 Family R
Track-E/V cells match after applying the report's rounding convention. A separate P-family audit
passes seventeen checks covering the P1 summary, the selected P1 power-repair contrasts and displayed diagnostic tables, P2 summaries and
narrative correlation/conditional-harm claims, P3 harm
and all switch-cost reweighting values plus narrative/registry cost-grid ranges and the paired P3 development-cost range, P4/P5 tables and claims, and P6 synthetic/fresh-real results (7,139 checked cells). The WP1 E_rb, P6 twin-bike
and P6 within-regime selection-adjusted summaries also reproduce exactly. The current machine-
readable result is `raw_report_audit.json` (48 checks after the H1/H3 and H5/H6 Track-R follow-ups and
the WP1 six-port supplemental replay); the runner is
`scripts/sota_sprint/audit_raw_to_reports.py`; P-family details are recorded in
`family_p/development_audit.json`. The unstructured candidate prose and remaining P-family narrative
claims are not fully reconciled, and this work is neither a validity nor an external review.

## Candidate claim corrections (2026-11-04)

Read-only family audits of H1–H6, R1–R6 and T1–T6 were compared with saved family reports and source
summaries. Corrections include H2 real-data ranges and Track-R disposition, H3's metro contrast
sign, R4's development costs, and T2's null-rate attribution; T1's rounding was clarified. P4 out-of-class validity wording, P2 twin/correlation interpretation, P3 cost-sweep coverage and
harm ranges, P5 pairwise update semantics, and P6 mechanism/Track-R wording were also corrected. Exact
corrections and evidence paths are in `CLAIM_RECONCILIATION.md`. Targeted P1, P4 and P6 interpretation
claims, P5 real intervals, cache identity and null-switching statements have since been checked.
Residual candidate-registry narrative and source-level theorem assumptions remain outside the
numeric raw-to-report audit. The registry-to-ledger shared-field audit passes all 24 entries, but
does not prove the scientific prose. These internal reads do not
satisfy external/human review.

The continued source review corrected P2's A_H window notation and P3's best-other cost-grid and
development-versus-A5b ranges. The P-family audit now has 17 passing checks covering 7,139 numerical
cells. H2 and P4 registry Track E/V fields were synchronized with their family
ledgers; the 24-entry registry audit passes. The registry audit enforces shared-field parity and
artifact links, not sentence-level proof of all registry claims.

The WP1 headline report was separately checked against its corresponding saved analyses: class
counts and cluster distributions, classifier sensitivity counts, the amended primary contrast table,
late-class means/verdict, historical sensitivity table, false-rollback counts, reversal operating
table, twin-null promotion rates, and Track-R operating-point wording all pass (293 checks). The
sensitivity table retains the Xu acquisition adapter as explicitly documented; the amended primary
excludes it. This does not cover every WP1 diagnostic, and the internal review remains distinct from
external peer review.

## Additional source review (2026-11-04)

A later report pass found and corrected one consolidated leaderboard attribution error: six null
promotion counts from the P6 1,000-seed follow-up were labeled A5b but were actually P6_LRMD_U counts.
The A5b values were recounted from that raw record file and kept distinct from the separate P4 HMM
follow-up. The same
pass found the registered WP2 H5 paired contrasts had been computed but omitted from its generated
tables. The WP2 table generator now renders those contrasts for registered and amended variants;
all 41 raw-to-report checks pass, including exact table regeneration and the H1/H3 Track-R outputs. A read-only WP1 narrative review found no
additional factual mismatches outside those already corrected, though process-timing statements
cannot be proven from result files alone. These findings are internal and do not satisfy external
review.


## Added Family-H Track-R and prose review follow-up (2026-11-04)

The H1/H3 and H5/H6 risk-calibration grids were run at all eight alpha values with 20 development
and 20 separate evaluation seeds per regime. H5/H6 dedicated timing recheck medians were 0.22–0.23s
and maxima 0.28–0.36s over 15 episodes per candidate in three targeted regimes; historical shared
screen outliers remain documented and are not explained by this small recheck. At alpha .5, H5/H6
held-out risk was .0375 [.013,.105] at every target, with costs 382.3, 382.9, 384.3 and 385.3 for
H5/H6-r10/r15/r25. The merged curve includes H1-H6 and D2/A5b. The 197-row cost-risk table audit
passes. The full raw-to-report audit passes 48/48 checks after the WP1 supplemental-path change.

The remaining prose audit corrected the finite-diagnostic overclaim in H diagnosis C4, WP1
per-dataset episode-count labels, and WP2 preregistration chronology wording. The WP1 headline audit
passes 9 groups / 293 checks after its parser was updated for the corrected headings. These checks
remain internal; they do not provide external review, theorem validity or untouched-data confirmation.

## Final internal prose pass (2026-11-05)

Three read-only internal reviews covered H/R, P-family/WP1/WP2 and SOTA/exit narratives. They found
and corrected: (1) language treating conditional predictive-loss advantage as application economic
value and an overly categorical delay/persistence statement in `family_p/P2P3_objectives_harm.md`;
(2) WP1's shorthand “late improvements,” clarified as episodes classified retrospectively as
`late_improvement`, not causal change labels; and (3) a stale Family-H sentence saying its corrected
rerun was still pending in `SOTA_BENCHMARK_AUDIT.md`. The SOTA audit now points to the completed
six-port result and marks the current Sprint 2 headline wording update complete. No other material
issues were found within those reviewed scopes. A subsequent T-family narrative review found and corrected the Track-R alpha-grid description and T3 status as of that review: T3 had development calibration but no held-out Track-R evaluation, and its cost evidence was mixed across contrasts. The later T3 follow-up below fills that specific Track-R gap. Spot-checks for T1/T2/T4/T5/T6 matched saved summaries. These internal reviews are not exhaustive, do not verify theorem proofs and do not constitute independent external review.

## Final candidate-registry audit (2026-11-05)

A separate read-only review checked the substantive Track E/R/V claims for all 24 registry entries
against the family ledgers, reports, and locally saved artifacts. It found no material numeric
contradiction in its spot checks. It identified stale comparator wording in the Family T ledger for
T2, T3, and T6; the canonical finding strings now use the registry's qualified comparator language.
The structural registry audit still passes all 24 IDs with no field or path mismatches.

This audit did not rerun every simulation or independently regenerate every interval. It is an
internal consistency review, not external validation, theorem review, or a substitute for resolving
the documented retrospective provenance gaps for H1-H4 and custom P-family analyses.

## Integrated-checkout follow-up (2026-11-05)

Three read-only internal passes rechecked H/R, T/P, and WP1/WP2/SOTA/exit evidence against the
integrated checkout. The H/R reviewer found no material mismatch in the registered numeric claims
it sampled. The T/P reviewer corrected the T1 artifact citation: the Model Picker-host contrast is
in the dev summary and devA records, while `contrasts.json` has only the D1 and D6:mp contrasts. It
also confirmed that the T-family held-out Track-R panel was partial at review time, the P-family historical
manifest gaps remain documented, and P6's all-14-source replay is negative versus its parent. The
WP1/WP2/SOTA reviewer confirmed the bounded result interpretations and identified stale statements
that the sprint had not been pushed and WP1's code was dirty; those status lines are now corrected.

The refreshed raw-to-report audit passes 52/52 checks after adding the T3 follow-up regeneration.
The cost-risk lineage audit passes for all 230 displayed points. These are internal consistency
and regeneration checks; they do not replace
the requested ARIS/HKUSTDial or human review, theorem-proof review, or untouched-data confirmation.
