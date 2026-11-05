# Sprint 2 independent review packet

Updated 2026-11-05 after the R5 100-seed simulator follow-up and its all-14-source real-stream cost replay. This packet is a reviewer handoff, not a review result. Reviewer identity, model/tool, date, findings, and dispositions must be added after an independent reviewer completes the work. No external review is represented as having occurred.

## Review objective

Assess whether the reported Sprint 2 conclusions are supported by the implementations, frozen protocols, raw records, and cited literature. Review claims at their stated scope. In particular, distinguish descriptive reanalysis from untouched confirmation, and distinguish conditional, marginal Markov, empirical risk, and economic objectives.

## Requested review sections

### 1. Comparator fidelity and prior art

Review `SOTA_BENCHMARK_AUDIT.md`, the relevant primary papers and source code, plus the method-specific implementation and adapters. Verify each publication-facing comparator claim, including the implementation details and any common-contract adaptation. Pay particular attention to:

- Xu: current comparisons combine its acquisition component with ShiftLab's certificate; they are not Xu's published certificate.
- CAMS-MAX: its context-free constant-policy selection core is used with ShiftLab deployment, delay, budget, and switching-cost adapters; this is not a native full-system deployment.
- Choe–Ramdas, QCE, and other certificate ports: verify the source implementation, the distinction between a published method and the local port, and the corrected comparator pools.
- The corrected DISCERN variance and design-floor variants, Gated Deployment variants, SMCS, Model Picker, CAMS, and other applicable published methods.

**Reviewer questions:** Are any methods mislabeled as author-native? Are any required strong comparators missing from a claim's comparison set? Are the information, label, delay, and economic-cost contracts actually matched? Do corrected/amended panels support the exact relative claims made?

### 2. Statistical objectives and theorem scope

Review `THEOREM_SCOPE_AUDIT.md`, `family_r/conditional_mean_verification.md`, the implementation of each evidence process, and the relevant protocol sections. For each validity statement, check the tested null, filtration, event clock, predictability of acquisition/policy selection, feedback availability, dependence assumptions, stopping rule, and multiplicity/error allocation.

Specific checks:

- Conditional-mean evidence uses an ordered issue/disagreement clock; assess the claimed time-averaged conditional null and the conditions for delayed labels and inverse-propensity outcomes.
- A5b/H2's V2 claim is restricted to its stated stationary first-order Markov null and implementation assumptions. Empirical null rates do not prove those assumptions.
- The K-model pairwise gate uses shared queries and cross-pair selection; assess whether its stated full pre-label conditional null covers the actual label-selection mechanism.
- Track R intervals are empirical operating characteristics, not anytime-valid guarantees. The R5 fixed-alpha follow-up is a single post-development simulator sensitivity, not a replacement for or confirmation of the full selected frontier.
- The SUI log-floor audit bounds recorded T=2000 arithmetic; it does not establish statistical validity or cover longer horizons.

**Reviewer questions:** Does any theorem or guarantee claim exceed the implemented process or stated assumptions? Are there filtration, optional-stopping, delayed-feedback, selection, or multiplicity gaps? Which claims should be removed or narrowed?

### 3. Experimental design, statistics, and selection

Review the frozen protocols and raw-to-report audit. Check independent units and uncertainty calculations, paired contrasts, split/seed construction, episode/window selection, comparator selection, post-development amendments, and the limits of reuse.

Key evidence and caveats:

- `raw_report_audit.json`: raw-to-derived reproduction audit; latest run passed all 50 checks.
- `wp1/report_claim_audit.json`: 293 checks across the WP1 headline report.
- `family_p/development_audit.json`: 7,139 checked cells in 17 audit groups.
- `cost_risk_audit.json`: reported cost-risk table lineage; it does not verify calibration or guarantee validity.
- `wp2/realized_harm.json`: 200,760 saved rows summarized into 1,205 cells; 2,000 cluster-bootstrap draws per cell. Reports prediction-loss change, label expenditure, switch expenditure, mean all-in excess economic cost, and the per-policy/per-regime rate of positive realized all-in excess cost. Run-2 horizon/delay variants re-window the same event streams. These are retrospective; application-level decision harm is not identified, and this is not a prospective promotion test.
- R5's fixed-alpha follow-up (`family_r/R5_round5_protocol.md`, `family_r/R5_round5_results.md`) uses 100 new simulator seeds per regime at α=.02. It found elevated promotions on F0 and dependent nulls, lower average alternative cost than D2, and higher R5 costs on the late and strong-persistence alternatives. This does not validate the earlier selected risk frontier.
- P6's all-14-source real cost replay (`family_p/P6_all14_real_protocol.md`, `family_p/P6_all14_real_results.md`) uses 20 policy seeds per stored episode. It finds higher equal-source mean cost than M_LRMD_SUI, A5b, D2, RMM and gated adaptive-range, but lower cost than never-switch. These are reused streams and do not identify late changes.
- P6's max-statistic analysis adjusts over five ports within each regime; it does not adjust across regimes or candidates.
- Comparator selection and multiple amended sensitivities still reuse exposed evaluation data. New seeds on reused datasets are not unseen datasets.

**Reviewer questions:** Are clusters/splits/episodes the right uncertainty units for each estimand? Are bootstrap intervals and paired analyses implemented correctly? Do the protocols justify the selection claims? Does any report imply independent confirmation where there is only post-development or reused-data evidence?

### 4. Result-to-claim and contribution assessment

Review `CLAIM_RECONCILIATION.md`, `LEADERBOARD.md`, `STATUS.md`, `EXIT_AUDIT.md`, the candidate registry, and the linked family reports. Assess the actual support for the proposed P2 empirical contribution and the narrower RMM/E_rb method opportunity.

Claims currently intended to remain bounded:

- No universal SOTA claim.
- WP1 real late-improvement criterion is NOT_SUPPORTED on the available episodes.
- E_rb has a post-development synthetic reversal result; no real-world transfer is established.
- P2 is a candidate empirical benchmark contribution about conditional versus marginal deployment validity, predictive outcomes, and excess economic cost under dependence; application-level decision harm is not identified, and novelty/main-track significance are not established.
- H2's dependence robustness is scoped to its declared V2 Markov conditions, and comes with substantial economic costs in persistent alternatives and reused real streams.
- Internal numeric and prose audits are not external validation.

**Reviewer questions:** Is each conclusion entailed by its cited evidence? Is the P2 question novel and significant enough for a main-track paper after comparison with prior work? What further experiment, if any, is decisive rather than incremental?

## Reproduction entry points

Run in the pinned project environment from the repository root:

```sh
uv run python scripts/sota_sprint/audit_raw_to_reports.py
uv run python scripts/sota_sprint/audit_sprint2_registry.py --out docs/sprint2/registry_audit.json
uv run python scripts/sota_sprint/audit_sui_clamp_bound.py --out docs/sprint2/sui_clamp_bound.json
uv run python scripts/sota_sprint/audit_wp1_report_claims.py
uv run python scripts/sota_sprint/audit_p_family_development.py
uv run python scripts/sota_sprint/audit_cost_risk_pareto.py
```

The scripts verify their documented scopes only. Consult `REPRODUCIBILITY.md` for full experiment commands, environment, manifests, and raw-record locations. Do not interpret successful reproduction as proof of a theorem or of data provenance beyond recorded metadata.

## Evidence map

- Overall status, scope, remaining work, and supported verdict: `STATUS.md`, `EXIT_AUDIT.md`, `LEADERBOARD.md`.
- Comparator source review: `SOTA_BENCHMARK_AUDIT.md`.
- Claim corrections and coverage limits: `CLAIM_RECONCILIATION.md`.
- Theorem assumptions and process mapping: `THEOREM_SCOPE_AUDIT.md`.
- Reproduction commands and data provenance: `REPRODUCIBILITY.md`.
- P1 real-world RMM evaluation: `wp1/RESULTS.md`, `wp1/protocol.md`, `wp1/false_rollback_audit.json`, `wp1/gr_one_time_reversal.json`, `wp1/clock_ablation_posthoc3.md`.
- P2 dependence, twins, decision flags, and all-in excess economic cost: `wp2/BENCHMARK.md`, `wp2/protocol.md`, `wp2/DECISION_FLAG_AUDIT.md`, `wp2/REALIZED_HARM.md`.
- Candidate execution evidence: `family_h/`, `family_r/`, `family_t/`, `family_p/`; seed-provenance exceptions and reconstructed evidence are in `legacy_seed_provenance.json`.
- R5 post-development evidence: `family_r/R5_round5_results.md` and `family_r/R5_all14_real_results.md`, with frozen protocols and raw-run manifests. The latter uses previously exposed sources and supports only descriptive retrospective cost comparisons.

## Reviewer record (to be completed by the independent reviewer)

- Reviewer / affiliation or review system:
- Model family or review method (if applicable):
- Date and code/data snapshot reviewed:
- Reproduction commands run and outcomes:
- Comparator fidelity findings:
- Statistical validity and theorem-scope findings:
- Experimental design and uncertainty findings:
- Result-to-claim corrections requested:
- Novelty/significance assessment:
- Required follow-up experiments:
- Disposition of each material objection:
- Overall recommendation and limits:
