# Sprint 2 exit-condition audit

Updated 2026-11-05 against the full user-pasted Sprint brief, current worktree, family ledgers, saved
runs and reproduction audits. “Complete” means the requested screen/report exists; it does not mean a
hypothesis passed, a guarantee is valid, or independent confirmation was achieved.

## Gate A — mandatory experiments and workstreams

| Requirement | Status | Evidence and scope |
|---|---|---|
| All 24 H/R/T/P named configurations screened; P2 is analysis-only | **Complete as development screens** | `candidates.json` plus all four family ledgers; 23 algorithm candidates have implementation/development screens, while P2 records an analysis workstream. The structural audit requires 24 brief IDs, linked artifacts and populated Track E/R/V cells. Negative and partial tracks remain explicit. |
| H1–H6, R1–R6, T1–T6, P1–P6 coverage | **Complete as recorded family screens** | Family ledgers and exact artifacts; not all candidates advanced and some Track R cells are explicitly n/a. |
| WP1: chronological incumbent–challenger schedules, outcome-blind classification, matched policy comparisons | **Complete as retrospective development analysis** | `wp1/protocol.md`, `wp1/RESULTS.md`; 348 episodes across 14 source clusters, with 10 classified late improvements. Raw streams are development-exposed and classes are not causal change labels. |
| WP1: late improvement test | **Complete; registered criterion NOT_SUPPORTED** | 10 late episodes / 5 clusters; none of four RMM hosts meets the registered CI rule against the selected best certified comparator. See `wp1/results_amended_no_xu.json`. |
| WP1: rollback, reversal and sensitivity | **Complete within registered compute amendments** | Real reversal screen, B2-style E_rb, six-policy strict-pool delay/budget/switch-cost sensitivities (six altered settings on 26 frozen late/reversal episodes) and post-development 100-seed synthetic follow-up are reported. Sensitivity uses outcome-blind selected classes, is retrospective, and has only 10 late episodes / 5 source clusters. |
| WP1: rollback-event diagnostics | **Complete as evaluator-side descriptive analysis** | `wp1/false_rollback_audit.json` replays all 1,044 primary episode-seed combinations for four E_rb hosts (4,176 policy rows) and classifies events against frozen segment means. Not a conditional-expectation or validity test. |
| WP1: every proposed secondary diagnostic | **Partial / explicitly scoped** | E_swcert Track R (A4), Giacomini–Rossi one-time-reversal diagnostic (A5), and a post hoc elapsed-timestamp start-grid replay across five timestamped fresh UCI streams are recorded. Nine cached loss-only streams lack elapsed/publication timestamps; the replay does not cover them or model publication-time feedback delay. GR findings are retrospective, reuse outcomes that defined WP1 classes, and do not establish its asymptotic assumptions. |
| WP2: five registered twin datasets, new split randomizations, episode horizons, feedback delays, dependence classes | **Complete as development analyses** | `wp2/protocol.md`, `wp2/tables.md`, `wp2/amended_no_xu_pool/`; runs cover 20 new splits per dataset, T={1000,2000,4000}, delay multipliers {.5,1,2}, synthetic dependence classes and five fresh real streams. |
| WP2: conditional/marginal/economic objectives, harm, robustness cost | **Complete as specified analyses; criteria have mixed/negative outcomes** | V1/V2/V3 flags and harm definitions in `wp2/BENCHMARK.md`; H2/H4/H5 and class tables in generated WP2 reports. H1b, H4 and H6b fail their registered criteria. H5 now has a separate historical cached-real sensitivity over nine previously exposed sources; it remains retrospective and fixed-cost. |
| WP2: all-in realized excess economic cost across saved primary and Run-2 records | **Complete as retrospective descriptive supplement** | `wp2/REALIZED_HARM.md` and `wp2/realized_harm.json`: 200,760 records, 1,205 cells, 2,000 cluster-bootstrap replicates per cell. Decomposes prediction-loss change, label expenditure, and switch expenditure versus never-switch; also reports the positive all-in-cost rate per policy/regime cell. Application-level decision harm is not identified; the registered first-promotion EI is a proxy, and neither is a prospective promotion guarantee. Run-2 variants re-window the same event streams. |
| Xu classification sensitivity for pooled WP2 claims | **Complete** | `wp2/NO_XU_POOLED_SENSITIVITY.md` and `amended_no_xu_pool/`; H2 stays positive, H4 does not satisfy its conjunctive rule. Historical outputs remain preserved. |

## Experimental rounds and comparator scope

| Brief requirement | Status | Evidence and limit |
|---|---|---|
| Round 1–3, all 24 development screens | **Complete** | The candidate registry and family ledgers. These are development evidence. |
| Round 4, P1/P2 workstreams | **Complete as reports** | `wp1/RESULTS.md` and `wp2/BENCHMARK.md` / `wp2/tables.md`; negative and inconclusive findings are preserved. |
| Round 5, stronger candidate evaluation | **Partial, targeted** | P6 has 100-seed paired synthetic follow-up, 1,000-seed reused twin-bike replay, corrected five-port sensitivity, and a 20-policy-seed-per-episode cost replay across all 14 real-stream sources; the latter shows no average advantage over its parent or deployment comparators and provides no late-change truth. R5 now has a 100-seed-per-regime frozen-alpha follow-up; it shows a mean alternative-cost advantage against D2 but elevated promotion rates on three tested nulls and losses on two alternatives. Its additional all-14-source real-stream replay is complete (20 policy seeds per episode, 230 episodes); equal-source mean cost is 404.22 for R5 vs 404.91 for D2, with mixed per-source effects. This uses previously exposed streams and is descriptive only. E_rb has a post-development 100-seed reversal run. H2 has 100-seed synthetic, 1,000-seed first-order Markov-null, and all-14-source real replays; P4 has a 1,000-seed HMM misspecification stress run. These are post-development/reused-data results; no fresh independent real source was added and other candidates were not advanced to the same depth. |
| Round 6, focused combinations | **Complete as a decision/report; no new hybrid advanced** | `ROUND6_FOCUSED_COMBINATIONS.md`; combinations are documented as prior development evidence and the failed RMM/SUI merge is not repeated without a new mechanism. |
| Round 7, independent review | **Open; handoff prepared** | `EXTERNAL_REVIEW_PACKET.md` now gives reviewer scope, claim questions, evidence map, reproduction commands, and a findings template. Internal reviews and numerical audits exist. ARIS/HKUSTDial integrations are not available in this environment; no human/external reviewer has approved the claims. |
| Published-method comparisons | **Complete as common-contract ports/adapters where implementable** | `SOTA_BENCHMARK_AUDIT.md`, family reports, strict-pool sensitivities for validation, WP1 (6/6 default and six altered settings) and WP2 (six ports), plus CAMS-MAX context-free matched validation. Full CAMS-MAX validation panels and limits are in `CAMS_MAX_VALIDATION.md`. No author-native full-system claim: Xu is an acquisition adapter with ShiftLab's certificate, not Xu's published certificate; CAMS-MAX preserves its constant-policy selection core but uses the benchmark deployment, delay, budget and switching-cost adapters; other ports have their documented limits. Missing author code and incompatible protocols are noted. |
| Track R at R5–R30, uncertainty and Pareto points | **Complete for registered eligible panels; partial across all candidate configurations** | `COST_RISK_PARETO.md`; 344 displayed rows reproduce from source Track-R JSON. Separate held-out panels cover T3, primary T1/T2/T5 transfer policies, and the 26-policy Family-R coverage follow-up; P5 has a K3/K4 panel. P2 is analysis-only, P3 has no tunable risk threshold and fails its null screen, and P4 is a generator family, so these have no policy curve. Other family panels remain bounded to registered policies, not every variant. The audit checks row lineage, not target calibration or guarantee validity. |

## Gates B–E and final deliverables

| Exit item | Status | Evidence |
|---|---|---|
| Gate B: identify a defensible research contribution | **Candidate identified, not established as a main-track contribution** | `LEADERBOARD.md` ranks the P2 dependence-aware deployment benchmark as the strongest paper opportunity, with remaining independent-review and confirmation needs. |
| Gate C: exact, scoped SOTA claim only | **No broad SOTA claim made** | `SOTA_BENCHMARK_AUDIT.md`, candidate reports and leaderboard delimit the actual methods/metrics/regimes. |
| Gate D: retain negative evidence and bounded search | **Complete for this sprint** | Negative results and failed criteria remain in ledgers; `ROUND6_FOCUSED_COMBINATIONS.md` records the bounded combination decision. |
| 1. Full 24-candidate matrix | **Complete** | `candidates.json`, `LEADERBOARD.md`. |
| 2–3. WP1 and WP2 reports | **Complete as scoped reports** | `wp1/RESULTS.md`; `wp2/BENCHMARK.md`, `wp2/tables.md`. |
| 4. A5b × D2 hybrid results | **Complete as development evidence** | Family H and R reports/ledgers; no broad economic superiority established. |
| 5. Published SOTA-method results | **Complete within implemented common-contract adapters** | `SOTA_BENCHMARK_AUDIT.md`; no author-native claim. |
| 6. Cost-risk Pareto curves | **Complete for the registered risk-operable panels, with documented non-policy exclusions** | `COST_RISK_PARETO.md`, `cost_risk_audit.json`; the T3, T1/T2/T5, 26-policy Family-R follow-up, and P5 K3/K4 panels are reported. P2/P3/P4 are excluded because they do not define an executable, risk-tunable policy. Family panels do not include every mechanism variant, so no all-24 joint frontier is claimed. |
| 7. Statistical-validity analysis | **Complete as empirical, null-specific assessment; theorem claims remain assumption-bound** | Track V cells, WP2 definitions, P4 misspecification tests, null audits. No empirical rate is treated as a guarantee. |
| 8. Real-data results | **Complete for available reused streams; no independent real confirmation** | Family reports and WP1/WP2 analyses; raw data and episodes are development-exposed. |
| 9. Independent reviewer findings | **Partial** | Internal read-only reviews are documented in `INDEPENDENT_REVIEW.md`; requested external/human review remains open. |
| 10. Ranked contribution opportunities | **Complete** | `LEADERBOARD.md`. |
| 11. Reproduction commands | **Complete for saved runs and audits** | `REPRODUCIBILITY.md`, protocols and manifests. |
| 12. Supported research verdicts | **Complete as bounded verdicts** | `LEADERBOARD.md` and `STATUS.md`. |

## Work remaining before “everything complete” is accurate

1. Obtain human/external review of comparator fidelity, statistical claims, novelty and result-to-claim
   alignment. The local tool catalog has no ARIS/HKUSTDial workflow.
2. If making independent-generalization or confirmatory claims, register and run on untouched data. A current worktree inventory found the nine previously-used Atlas loss caches and the five UCI sources designated fresh for this sprint (now used in the sprint), plus late-window/twin variants derived from those sources; no additional untouched paired-loss cache was present in the registered Sprint 2 data paths. A new source would need a frozen preprocessing, paired-policy, feedback-delay and evaluation protocol before use. Current evidence remains development-exposed, and the P6 adjustment is limited to five ports within each regime.
3. Obtain independent review of theorem assumptions and finish the sentence-level editorial pass on
   the candidate registry. Internal read-only reviews on 2026-11-05 covered H/R, P/WP, and SOTA/exit
   narratives; they corrected the conditional-predictive-loss economic interpretation, clarified
   retrospective WP1 class labels, and corrected a stale Family-H completion sentence. The T-family narrative and all 24 registry Track E/R/V summaries have now received an internal consistency pass. It corrected the alpha-grid description, T3 held-out-evaluation/status wording, and stale T2/T3/T6 comparator wording in the canonical ledger. These reviews did not rerun every analysis, are not exhaustive across all report prose, and are not external proof review. The internal source-level mapping is recorded in
   `THEOREM_SCOPE_AUDIT.md`; the T=2000 SUI clamp arithmetic is now verified in
   `sui_clamp_bound.json`, but this does not verify the proofs. Numeric reconciliation covers the
   reported H/R/T/P claims, but not every prose sentence or proof. Current Sprint 2 reports have no
   embedded figures or image/PDF/SVG artifacts under `docs/sprint2` or `outputs/sprint2`; legacy
   plots elsewhere are not cited by these reports. The required PaperBanana visual dependency is not
   available in this environment (no matching tool is installed), so validated research figures
   remain open. WP1 headline and structural registry audits pass.
## Integration record

The initial sprint implementation and subsequent audits were committed to `main` and pushed to `origin`. Registered follow-ups now cover held-out Track-R for T3 and primary T1/T2/T5 policies; source reports and lineage audits include those panels. Raw and large run outputs remain ignored and outside Git.

These open items do not invalidate completed screens or negative results. They prevent claiming the
entire brief's research and independent-review exit conditions are fully satisfied.
