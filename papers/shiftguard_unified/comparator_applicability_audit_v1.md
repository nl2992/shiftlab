# Finite comparator applicability audit — 2026-10-26

This audit records the source-discovery and task-eligibility pass for the
currently named high-priority Q2/Q3 comparators. It does **not** claim that all
eligible comparisons have been run. AnyRank has a corrected, source-pinned
six-stream development pilot, but that pilot neither evaluates its full
ranking procedure nor tests the project's mean decision-cost promotion
estimand. A larger AnyRank ranking benchmark is warranted only if the paper
scope includes distributional policy ranking as a separate target.

**Status update (2026-10-26):** the initial AnyRank implementation gap has
since received a limited, source-pinned synthetic pilot. The pilot is an
explicit candidate-versus-incumbent adaptation, not a reproduction of the
paper's complete all-pairs ranking or active trial allocation. See the results
and updated gate disposition at the end of this document.

## Q2: ranking, off-policy value, and safe improvement

### Newly surfaced comparator — Wang (2026), *The Certification Exponent*

The primary arXiv v1 (submitted 2026-10-17) studies sequential certification that a fixed target policy improves on a known, possibly history-dependent logging policy. Under its logged-tree environment class, bounded rewards and coverage conditions, it gives the instance-specific lower bound `E_P[tau_delta] >= log(1/delta)/K*` and a plug-in Kelly certifier matching the exponent asymptotically when `0 < K* < infinity`; its coverage trichotomy includes cases where certification is impossible. This is a direct Q2 policy-improvement comparator, separate from common-label classification certification and from Molitor's finite-class optimal-policy identification target.

The arXiv paper says code and raw outputs are in supplementary material, but the public source archive inspected for this audit contains only the manuscript, bibliography, style file and figures; no code or separate supplement was located. The theory was source-audited, but no implementation or ShiftLab head-to-head has been verified. A one-step contextual-bandit reduction may fit the frozen OBD item-41 question, but OBD's user/slate dependence, context-as-of semantics, reward availability, and i.i.d./episode assumptions remain unresolved. First map assumptions and obtain/inspect the supplementary implementation; then compare on a matched synthetic one-step logged-policy task if the method is implementable. Do not present the comparison as complete until that task-fit decision is recorded. Primary source: [arXiv:2610.24345](https://arxiv.org/abs/2610.24345).

| Comparator | Published target and necessary information | Fit to current ShiftLab evidence | Decision |
|---|---|---|---|
| **AnyRank** ([paper](https://arxiv.org/abs/2610.14603), [author code](https://github.com/irom-princeton/AnyRank)) | Anytime-valid multi-policy ranking with graphical familywise-error allocation and adaptive allocation of independent task/hardware trials. Requires a fixed policy set for the declared ranking family, bounded shared metric, and i.i.d. task instances; optional priors may improve allocation. | The source-pinned pilot adapts the ranking procedure to a star-shaped incumbent comparison. Its tie-aware reward-distribution ordering is stricter than the project's expected decision-cost improvement target. With common labels, one label scores all deterministic candidates, so AnyRank's adaptive trial-allocation efficiency does not translate into label savings. | **Scope comparator, not a required mean-cost promotion baseline.** The corrected six-stream pilot is only development evidence. A full AnyRank benchmark is needed only if distributional ranking is retained as a separate paper estimand; it must then use its declared ranking/FWER mode and an independent, adequately powered task family. Do not interpret it as label savings or evidence for mean-cost improvement. The author's repository is MIT, but two dependencies are CC BY-NC 4.0 and remain external. |
| **PACE** ([paper](https://arxiv.org/abs/2606.08106)) | One paired fixed-candidate commit gate from binary correctness discordances; its per-candidate guarantee does not itself supply run-level familywise control over an adaptive sequence. | A paper-rule adaptation has run on disjoint WILDS article-level scout/certification partitions. It retained the incumbent after 3,491 cert instances; fixed-N exact McNemar promoted (`p=0.02016`). The held-out test comparison is exploratory due to prior exposure. | **Limited adaptation complete.** It does not replace AnyRank's multi-candidate ranking baseline or provide a real-time intervention result. |
| **Off-Policy Confidence Sequences (OCS/MOPE)** ([ICML 2021 paper](https://proceedings.mlr.press/v139/karampatziakis21a.html), [author code](https://github.com/n17s/mope)) | Time-uniform contextual-bandit policy-value and gated candidate-vs-logger confidence sequences from logged actions, rewards and propensities; the paper's main OCS theorem assumes IID contextual-bandit data and requires the stated support/betting conditions. | **Correction:** OBD is present locally and is not a common-label task: Random/all contains logged item-position actions, clicks, UTC impression timestamps, and uniform `1/80` propensities. This supports a bounded-weight fixed-candidate development replay on one position, conditional on the item-position/no-interference contract. User/session/slate dependence, feedback timing, and exposure remain unresolved, so OBD is not a validity-bearing real-data confirmation. The 412-row Criteo BLBF sample is still too small and outcome-subsampled for evaluation. | **Conditional development comparison; not a real-data guarantee claim.** A frozen OBD position-1 replay using Random/all is now specified in [`OBD MOPE protocol`](open_bandit_mope_development_protocol_v1.md); it must report as retrospective/exploratory and preserve its IID limitation. Do not describe the seven-day OBD replay as prospective monitoring or independent confirmation. BLBF remains a feasibility candidate pending the full archive and its sampling correction. |
| **High-Confidence Policy Improvement (HCPI)** ([ICML 2015 paper](https://proceedings.mlr.press/v37/thomas15.html)) | Batch/incremental RL policy improvement with probability control on returning a policy below a user-set performance lower bound, based on trajectory/policy evaluation assumptions. | Current data have no verified episodic trajectories, behavior-policy log, action support, or potential outcomes for treatment changes. | **Exclude from current datasets' faithful comparisons.** Retain as a scope comparator and revisit only with a supported offline-RL dataset and trajectory contract. |
| **Conformal Policy Control (CPC)** ([ICML 2026 paper](https://proceedings.mlr.press/v306/prinster26a.html), [author code](https://github.com/samuelstanton/conformal-policy-control)) | Regulates how aggressively an optimized policy acts relative to a safe reference using conformal calibration; finite-sample risk control for the paper's safe-policy sampling, support, and bounded-risk construction. | Public author code exists. Its LLM/protein-design, constrained-optimization and active-learning experiments have a safe reference and action-dependent feasibility/risk outcomes; current ShiftLab data do not identify those potential outcomes or provide behavior/target treatment support. | **Exclude from current data runs; correct prior “no implementation identified” statement.** Keep as a mandatory novelty/scope comparison. Reproduction is appropriate only with a compatible safe-reference action task and a separately audited data/feedback contract. |
| **Conformal Policy Selection (CPS)** ([paper](https://arxiv.org/abs/2610.22930)) | Selects units for a fixed target policy while controlling outcome-threshold FDR under its behavior/target covariate-treatment shift and calibration conditions. | The current temporal paired-average harm problem, with no treatment propensities or counterfactual outcomes, is a different estimand. | **Scope comparator only** unless a treatment-policy dataset is acquired. |

## Q3: resource allocation and intervention

| Comparator | Published target and necessary information | Fit to current ShiftLab evidence | Decision |
|---|---|---|---|
| **Cost-Aware Best Arm Identification (CABAI)** ([RLC 2024 paper](https://arxiv.org/abs/2402.16710), [RLJ publication](https://rlj.cs.umass.edu/2024/papers/Paper193.html)) | Identify the arm with highest implementation reward while minimizing heterogeneous experiment cost; testing and implementation phases have distinct reward/cost distributions. | The full-feedback synthetic and classification tasks reveal all candidate costs from the same label; they do not have arm-specific experimentation costs followed by distinct implementation rewards. | **Do not adapt to common-label data.** Use only in an explicitly chosen-action/arm task where query cost and implementation reward are separately observed. |
| **UPF / When to Retrain** ([ICML 2025 paper](https://proceedings.mlr.press/v267/regol25a.html)) | Forecasts future bounded predictive performance and compares horizon cost distributions for retrain versus keep under an elicited cost ratio. | The repository has a tested paper-rule adaptation and matched CISO/ERCO EIA frontier. It is regression/event-time adaptation with assumed label delays, not the seven-dataset classification reproduction. An algebraic counterexample to the paper's Proposition 3.1 count bound is documented separately; it does not by itself refute the retrain rule. | **Development comparison complete; paper-fidelity gap remains.** The strongest present task-compatible Q3 baseline. Retain never/always/periodic/error-trigger and cost frontier. |
| **Temporal reliability/cost control** ([Rahman & Tabassum, arXiv:2604.02351v1](https://arxiv.org/abs/2604.02351)) | Annual binary credit-risk maintenance; controls AUC/ECE reliability volatility with drift-triggered recalibration/retraining and reports an imposed cost–volatility frontier. | Overlaps generic cost-aware temporal intervention, but uses yearly label batches, predictive reliability rather than paired decision harm, and a single retrospective credit-risk horizon. Its MORC threshold sweep/knee uses outcomes/shift values over the full evaluation horizon. | **Mandatory scope comparator; no matched run on current tasks.** Do not claim generic temporal cost-control novelty; do not compare its imposed units or AUC/ECE results numerically with ShiftGuard. See `temporal_reliability_cost_control_audit.md`. |
| **RCCDA** ([NeurIPS 2025 paper](https://proceedings.neurips.cc/paper_files/paper/2025/hash/e3d1b6d954a204267fd334cbaf9cd4af-Abstract-Conference.html), [author code](https://github.com/Adampi210/RCCDA_resource_constrained_concept_drift_adaptation_code)) | Virtual-queue update control for predictive loss/resource constraints under boundedness, smoothness and drift/resource assumptions. | EIA paper-rule regression adaptation is evaluated on the same frontier with mature-prefix feedback and two assumed delay values; it is not an author-task reproduction, and the ideal-estimator theorem does not automatically cover the delayed finite estimator. | **Development comparison complete; fidelity gap remains.** Compare only on a task matching predictive-loss/update budgets; do not interpret it as paired decision-harm certification. |
| **CARA, ADWIN, DDM** (sources and repositories in `sota_fidelity_matrix.md`) | CARA makes batch retraining decisions from distribution overlap and relative staleness/retraining costs; ADWIN/DDM trigger on observed error streams under their detector assumptions. | All are implemented as bounded-loss EIA adaptations and compared on the same 40-cell cost frontier, with mature-prefix assumed-delay access. The regression-to-binary DDM mapping and EIA data use are adaptations. | **Matched task-specific comparison complete; published-task fidelity remains incomplete.** Current results do not indicate consistent frontier dominance. |
| **Active Statistical Inference / Robust ASI** ([ASI project materials](https://github.com/Active-Statistical-Inference/active-statistical-inference)) | Efficient fixed-horizon mean estimation/allocation under its score model; Robust ASI adds a robustness treatment for trial distributions. | The repository has a matched-budget fixed-horizon paired-cost adaptation and a corrected original-task ACS reproduction. Neither is sequential validity or an end-to-end intervention comparison. | **Component comparison complete at its stated scope.** Keep label-estimation efficiency separate from intervention utility. |

## Q1 bounded-risk monitor update (2026-10-26)

Timans et al., [*On Continuous Monitoring of Risk Violations under Unknown Shift*](https://proceedings.mlr.press/v286/timans25a.html), is a direct Q1 comparator for one fixed policy pair with bounded immediate feedback. For paired excess cost `d_t-m` and known support `[-b,b]`, `z_t=(d_t-m+b)/(2b)` maps its conditional risk null `E[z_t|F_(t-1)]<=0.5` exactly to the ShiftLab conditional paired-cost null. The source-pinned synthetic comparison used 1,000 seeds per null scenario and 300 per alternative. Official `approx_grapa` and `grapa` wealth paths were independently reproduced to maximum absolute log-wealth errors `0` and `1.86e-7`. False escalations were 0–2 per 1,000 streams in each null cell; every method detected all boundary-local, recurring-regime, and harmful-adaptation cases, with no significant paired differences after Holm adjustment. Residual-variance detection was 8–11/300 for all methods. This materially weakens a novelty claim for the standalone harm gate. It does not compare the downstream intervention or candidate-promotion transition. See [`frozen protocol`](timans_unknown_shift_paired_cost_protocol_v1.md), [`results`](../../outputs/shiftguard_unified/sota_reproductions/timans_unknown_shift_paired_cost_v1/report.md), and [`independent verifier`](../../scripts/verify_timans_risk_monitor_paired_cost.py). The upstream implementation is AGPL-3.0; ShiftLab independently implemented the scalar formulas and did not vendor its code.

## Gate disposition

The ranked inclusion/exclusion decision for the current shared benchmark is now consolidated in [`comparator_scope_decision_v1.md`](comparator_scope_decision_v1.md). The individual decisions below remain the detailed source/task audit; the consolidation does not promote conditional development runs to confirmatory comparisons.

1. **Do not begin RIVE/ASC.** Integrated synthetic efficacy favors simpler arms in the supported harm profiles and shows reversal/late-onset weaknesses; no concrete new method has earned a justified development branch.
2. **Treat AnyRank as a scope choice.** Its partial distributional ranking is not the same target as expected decision-cost improvement. Do not hold mean-cost promotion completion hostage to a larger ranking-only benchmark. If distributional ranking becomes a stated contribution, freeze and run an adequately powered source-faithful benchmark with familywise-error calibration; otherwise retain the corrected pilot as a scope audit and cite the estimand mismatch.
3. **Separate logged-bandit from common-label comparator eligibility.** OCS/MOPE has a compatible but limited OBD development task and is no longer excluded for lack of logged actions; any OBD run is retrospective and cannot claim theorem validity unless its IID/decision-unit assumptions are justified. HCPI, CPC, CPS, and CABAI remain ineligible on the current common-label tasks because their trajectory, safe-reference treatment, target-policy, or distinct experiment-cost contracts are absent.
4. **Decide the paper scope after the remaining compatible comparator and real-data audit.** Phase F's full success condition remains unmet until genuinely held-out real data support downstream candidate intervention/resource allocation under a defensible information contract.

## Primary-source record

- AnyRank paper and its statement of i.i.d. task trials, bounded shared metrics, graphical FWER testing and active allocation: [arXiv:2610.14603](https://arxiv.org/abs/2610.14603); [author repository](https://github.com/irom-princeton/AnyRank). Audited repository commit: `4d16a972811d03780919a97c98790850a7cd0dea`. Source hashes: `sequential_graphical_active.py` `ac7d4dfd5890b5d68f9cd8cb77ceb7b2df94ef470e9ce9367056b8563c1dff09`; `sequential_graphical.py` `11ef96efccdb0b65922f1317807c1ad9e76d51038c371dbbab9565fefb407eb9`; `inference_modes.py` `527ca9a5c07d627a06aab68e155f2a57c7d3f7c3ffd518931244c83fc716d`. The README identifies its MIT repository license and CC BY-NC 4.0 dependencies.
- OCS: [PMLR ICML 2021 paper](https://proceedings.mlr.press/v139/karampatziakis21a.html).
- HCPI: [PMLR ICML 2015 paper](https://proceedings.mlr.press/v37/thomas15.html).
- CPC: [PMLR ICML 2026 paper](https://proceedings.mlr.press/v306/prinster26a.html); [author repository](https://github.com/samuelstanton/conformal-policy-control).
- CABAI: [Reinforcement Learning Journal, volume 4 (2024)](https://rlj.org/volumes/1-5).
- UPF: [PMLR ICML 2025 paper](https://proceedings.mlr.press/v267/regol25a.html).

## Updated AnyRank gate — 2026-10-26

The official source was pinned at commit
`4d16a972811d03780919a97c98790850a7cd0dea`; dependency versions were recorded
as `nscore 0.1.2`, `statistical-comparison-core 0.2.1`, and
`sequentialized-barnard-tests 0.0.9`. The repository is MIT licensed, while
the latter two dependencies are CC BY-NC 4.0 and are kept external. The
development run used CUDA RTX 4060 stream generation and official CPU-side
sequential tests. A three-policy orientation smoke test correctly identified
both known higher-reward challengers.

The matched pilot tested six fresh streams (three zero-signal and three
positive-signal at prevalence 0.50, proxy error 0.10), comparing AnyRank,
pooled fixed-mixture certification, source-validation fixed split, and
Target-Scout on common labels and the same post-monitor holdout. All four
methods made zero promotions in both cells. AnyRank resolved 19–21 of 24
candidate-versus-incumbent directions per stream, but no context had an
eligible challenger. Mean label counts were 638.7/640 in the control and
625.7/640 in the positive-signal cell; counts matched across methods within
each stream. The independent verifier checked all 24 rows, seed/method
completeness, matched query counts, hard caps, protocol/source hashes, and
artifact hashes.

This pilot is descriptive and inconclusive: three streams per cell cannot
calibrate the familywise guarantee or estimate efficacy. The tested star
family is an explicit adaptation of AnyRank's graphical procedure, and its
tie-aware reward-distribution ordering is stricter than the mean-cost target.
The all-pairs 13-policy diagnostic was interrupted after more than five CPU
minutes in its first context without observing a result; the protocol was
then narrowed before the six-stream run to test only candidate-versus-
incumbent decisions. Full ranking, adequate null calibration, and a
well-powered efficacy comparison remain uncompleted. Original active
per-policy trial allocation is not applicable to common-label evaluation and
was not represented as label savings.

**Correction:** the v1 reward builder reversed false-positive and false-negative
costs. Its AnyRank and comparator outcomes are invalid; the verifier checked
artifact integrity, not methodological correctness. The run remains preserved
with an invalid status in its manifest.

The corrected v2 replay uses the same six seed IDs and therefore is a
corrective development replay, not independent evidence. It fixed the cost
mapping, added a runtime cost-direction assertion, and passed the independent
artifact verifier over all 24 method-stream rows, source snapshot, checksums,
matched query counts, and caps. All methods still made zero promotions. An
evaluator-only oracle diagnostic found 12 positive finite-design mean-gain
candidates in one positive-signal context (mean best gain +35.775), but none
strictly first-order stochastically dominated the incumbent on the registered
reward-threshold grid. This reveals an estimand mismatch for this instance:
AnyRank's strict distributional ordering does not certify mean-cost-positive
candidates. It does not demonstrate efficacy, FWER calibration, or equivalence.
The implementation remains a star-shaped adaptation, not a full all-pairs
reproduction; common labels also prevent interpreting AnyRank's adaptive
per-policy trial allocation as label savings.

Artifacts: `anyrank_adaptation_protocol_v1.md` (historical, invalid method
results), `anyrank_adaptation_protocol_v2.md`,
`scripts/reproduce_anyrank_shiftguard.py`,
`scripts/verify_anyrank_shiftguard_pilot.py`,
`scripts/diagnose_anyrank_pilot_estimand.py`, and the v1, v2 and oracle
diagnostic output directories under
`outputs/shiftguard_unified/sota_reproductions/`.

## Matched MOPE and OPI comparator update — 2026-10-26

The frozen synthetic comparison now places MOPE's fixed candidate-versus-logger gate and Molitor OPI's finite-class identification method on identical 200-event logged-bandit streams, with matched fixed-horizon controls. On 1,000 all-tied null streams, MOPE promoted 11 (1.10%; exact 95% CI 0.55%–1.96%) and three paths became empty (0.30%; 0.06%–0.87%). On 300 streams where the fixed candidate improved expected reward by 0.15, MOPE promoted 279 (93.0%; 89.50%–95.62%) using 114.04 labels on average, while the fixed-horizon Hoeffding candidate gate promoted 92 (30.67%; 25.50%–36.22%) using all 200 labels. The empty paths were independently reconstructed from seed-matched CUDA streams; all event times and the one promotion preceding a later empty set are preserved. OPI and the fixed-horizon finite-class selector did not identify a singleton by event 200. These methods target different decisions, so do not use their rates as a unified ranking.

This strengthens the conclusion that candidate-versus-incumbent certification is already solved for supported logged-bandit feedback by established methods. The comparison is synthetic and IID. A separate frozen OBD fixed-candidate replay has since completed as exploratory diagnostics, but it does not establish MOPE coverage or validity on OBD and does not close the downstream-utility, delayed-feedback, adaptive-candidate, or integrated-system gates. The OBD position-level contract remains a conditional offline development candidate, not a validity-bearing or prospective confirmation task. Full protocol, analysis, and hashes are in `opi_mope_matched_protocol_v1.md`, `opi_mope_matched_results_v1.md`, and `../../outputs/shiftguard_unified/sota_reproductions/molitor_mope_matched_v1/`.
