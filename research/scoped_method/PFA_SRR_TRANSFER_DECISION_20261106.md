# PFA-SR transfer decision — 2026-11-06

## Decision

**`EXISTING_METHOD_ALREADY_SOLVES_IT` in one narrowly defined synthetic regime; overall paper disposition: `BENCHMARK_OR_CASE_STUDY_ONLY`.** The matched-host confirmation finds a practically meaningful PFA-SR advantage for the frozen strong-persistent iid regime, but the full target-region criterion fails and the detector is established prior art. The experiment does not identify a distinct repair to publish as a new method. It does not establish a real-world transfer claim.

## Frozen experiment and exact artifacts

- Protocol frozen in `research/scoped_method/pilots/pfa_srr_transfer_confirmation_20261106/protocol.md` and method registry in `scripts/sota_sprint/pfa_confirmation_spec.py` before opening fresh outcomes.
- Runner: `PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py --kind synthetic --regimes PFA_confirm_persistent,PFA_confirm_near,PFA_confirm_delay_scarce@B100,PFA_confirm_null,F3_reversal_800 --policies 'CONTROL_never_switch,xu_acquisition_only,E_rb:gated_adaptive_range,rmm:gated_deployment+RMM,rmm:gated_adaptive_range+RMM,E_swcert,E_srrSR:gated_deployment,PFA-SR:gated_deployment,PFA-SR:gated_adaptive_range' --seeds 100 --seed-base 2026110628 --workers 4 --out research/scoped_method/pilots/pfa_srr_transfer_confirmation_20261106/run`.
- 100 paired streams in each of five cells; 4,500 policy rows. Horizon 2,000; pathwise label budgets 200 (100 in the delayed/scarce cell); label price 0.05; switch cost 5. The analyzer, raw rows, summary and manifest are checked in beside `RESULTS.md`.
- Source commit recorded by the manifest: `ff4fefbfa5c1099d1f05311f4e4b4010f7451c14`. Outcomes and analysis were committed and pushed in `d505493e`.

## Contributions and evidence status

| Contribution | Status | Evidence and limit |
|---|---|---|
| Diagnosis | **PASS, scoped** | In `PFA_confirm_persistent`, the frozen PFA-SR deployment host improves net cost over both Xu acquisition-only and same-host RMM by >5 with paired 95% intervals below zero. Not a general failure of RMM or all deployment hosts. |
| Explanation | **PARTIAL** | The matched-host comparison isolates the PFA start-time prior / detector from its host. Gain is localized to strong persistent evidence; the weaker persistent cell fails. No mechanism ablation separates prior mass, bet grid, label delay, and deployment threshold. |
| Repair | **FAIL as a novel contribution** | PFA-SR is directly drawn from published e-detector work. No original intervention survives the novelty gate. It remains a reproducible benchmark/application result. |
| Validation | **PARTIAL** | Fresh 100-seed synthetic confirmation and null/adverse cells are complete. No independent real-data evaluation was run. The reviewed Wild-Time/Monash sources do not provide verified label-release chronology for this deployment claim; imposing delays would be a simulated-feedback replay and serial dependence would not support the iid conditional-null guarantee by itself. |

## Primary results

Net cost is predictive loss + 0.05 × labels requested + 5 × switches. Paired intervals use the 100 shared streams. The frozen gate required at least 5 units of savings and a 95% interval below zero against both Xu acquisition-only and same-host RMM.

- Strong persistent, `PFA-SR:gated_deployment`: vs Xu **−18.34** [−25.57, −11.11]; vs same-host RMM **−14.24** [−20.71, −7.77].
- Strong persistent, `PFA-SR:gated_adaptive_range`: vs Xu **−20.39** [−27.33, −13.44]; vs same-host RMM **−19.19** [−24.81, −13.57].
- Near persistent: neither host clears the 5-unit gate against either comparator.
- Delayed/scarce (`B=100`, 400-step feedback delay): deployment host vs Xu **−30.86** [−38.63, −23.08] and same-host RMM **−20.14** [−28.96, −11.32]. Adaptive-range host vs same-host RMM is **−5.21** [−13.52, +3.10], so that host comparison fails. The all-target gate therefore fails.
- Null: PFA-SR deployment host promoted 0/100 (Wilson 95% CI [0.000, 0.037]); adaptive-range host promoted 1/100 ([0.002, 0.054]). This is a screening check, not a guarantee beyond the registered iid conditional null.
- Reversal diagnostic: deployment PFA-SR costs **+65.04** [+60.33, +69.75] vs never-switch; adaptive-range PFA-SR costs **+59.18** [+54.60, +63.76].
- Accounting residual is zero. Full policy rows, label/switch/promotion counts, and provenance hashes are in `run/RESULTS.md`, `run/records.jsonl`, and `run/manifest.json`.

## Baseline fidelity and prior art

| Baseline | Role in this run | Fidelity/status |
|---|---|---|
| `xu_acquisition_only` | Corrected acquisition comparator | ShiftLab acquisition adapter only; it is **not** Xu et al.'s published certificate. Matched in the frozen contract. |
| RMM on each same host | Isolates PFA detector contribution | Uniform-start restart mixture with the same gated deployment/adaptive-range host. This is the key matched-host comparison. |
| `E_rb:gated_adaptive_range` | Existing rollback comparator | Existing corrected implementation; included to contextualize detector-on-host results. |
| `E_swcert` | Risk-controlled comparator | Existing certificate implementation; included under the same horizon, budget and costs. |
| `E_srrSR:gated_deployment` | Conventional fast/restart diagnostic | ARL-style control is not comparable to probability-of-any-false-promotion control. It is reported as a diagnostic, never as equally safe SOTA. |
| `CONTROL_never_switch` | Feasible no-deployment reference | Exact zero-label, zero-switch policy. PFA-SR's adverse reversal cost is compared directly with it. |
| PFA-SR | Published competitor, not new method | Implemented with fixed bets {0.15, 0.30, 0.50}, start weights `1/[2 s log(e s)^2]`, and fixed threshold/alpha wrapper. Published PFA-weighted e-SR construction; see [Shin et al. (2026), e-detectors](https://nejsds.nestat.org/journal/NEJSDS/article/59/text) and [Non-partitioned e-detectors, §2.2/Theorem 2.3](https://arxiv.org/abs/2607.28322). Its guarantee requires the stated conditional-null filtration; this experiment does not validate it under arbitrary dependence. |

The old 30-seed screen in `pilots/pfa_srr_reversal_20261106/` is development-only and not pooled: its PFA and RMM rows used different hosts, so that detector contrast was confounded. The new same-host confirmation repairs that comparison. Earlier registered experiment records remain unchanged.

## Statistical / operational limits

The positive results establish a synthetic application comparison, not a real deployment advantage. There is no multiplicity adjustment across alternative cells; the full target-region gate is explicitly reported as failed. Paired t intervals assume the 100 generated streams are independent across seeds; uncertainty over simulator specification is not represented. PFA's null statement assumes the run-level conditional null and predictable sampling/order; the study does not prove those assumptions in dependent real-world data. Costs and label budgets are the shared synthetic contract and are not sourced from a field deployment.

## Real-data decision and next step

No fresh real confirmation was run. Existing ShiftLab time series/Monash and Wild-Time feasibility material has already been exposed for development, and Wild-Time label-release logs are unavailable. A replay with imposed delay would have to be labelled simulated feedback, and source-level uncertainty would be limited by the number of independent providers. Since this screen confirms a published detector only and the full scope gate fails, opening more data would not validate a novel repair. If a benchmark/case study is pursued, the smallest next step is to freeze a source-level real replay protocol before opening any holdout: authentic model-pair forecasts, train-only preprocessing, pointwise prediction times, explicit simulated release-delay contract, source-cluster intervals, and no claim that the iid conditional-null guarantee transfers automatically.

### Registered late-label extension follow-up

A separate frozen development screen tested a heavier-tailed finite-budget change-start prior (`q=1.2`) against canonical PFA-SR (`q=2`) at equal total prior mass. In the late-improvement, 400-step-delay, B=100 cell it was more costly by 4.40 [−1.27, +10.07] than canonical PFA-SR, 5.30 [−0.01, +10.61] than same-host RMM, and 4.09 [−0.48, +8.66] than Xu acquisition-only. It promoted 1/30 under the iid null but also promoted less in the target cell (1/30 vs canonical's 3/30) without saving cost. It failed the frozen screen and is stopped. Full reproducibility is in [`heavy_tail_pfa_screen_20261106/protocol.md`](pilots/heavy_tail_pfa_screen_20261106/protocol.md), `run/RESULTS.md`, `run/records.jsonl`, `run/manifest.json`, and `run/analysis_summary.json`; its analyzer is `research/scoped_method/analyze_heavy_tail_pfa_screen.py`. Prior-weight mixtures are a conventional e-detector design choice, so even a favorable result would have required a narrow application claim and separate novelty audit.

## Manuscript-ready four-contribution outline

1. **Failure:** a strong published certificate/acquisition baseline can leave measurable net-cost savings in a strong persistent iid feedback regime; this is a scoped synthetic diagnosis, not evidence all prior methods fail.
2. **Mechanism:** same-host contrasts attribute the measured incremental gain to the published PFA start-time-weighted restart detector in the tested simulator; the weaker-effect and adverse reversal cells bound the claim.
3. **Repair:** no new repair contribution. PFA-SR is prior art and must be presented as a competitor/application component.
4. **Validation:** fresh synthetic matched-host confirmation only. Independent chronological real-data validation and source-level transfer remain open; no paper-ready method claim follows from this run.

## Final scientific decision

**`BENCHMARK_OR_CASE_STUDY_ONLY`.** The strong-persistent synthetic effect is real under the frozen simulator contract, but the complete target-region gate and novelty gate do not pass. Do not write this up as a new detector or general rollback/acquisition method. Preserve the full results and adverse cells as a scoped comparison against the Failure Atlas.

## Append-only real-transfer update (2026-11-06)

After this decision was written, one newly sourced chronological source passed the frozen
validation-only selection rule and was opened for a single-source PFA-SR application replay.
Wild-Time HuffPost's date-only labels were assigned a **simulated** +24-hour release clock; this is
not observed feedback. On 3,877 test rows, PFA-SR used all 200 labels, never promoted, and cost
3,163. Same-host RMM cost 2,039; Xu acquisition-only cost 1,454. PFA-SR was +289.91/1,000 versus
RMM (time-block 95% interval `[+193.64,+391.18]`) and +440.80/1,000 versus Xu
(`[+394.19,+486.84]`). This negative case does not revise the synthetic findings or create a new
method contribution. It strengthens the scoped late-improvement failure diagnosis and leaves the
primary paper contribution C4 **FAIL**: one source cluster, simulated label clock, and no repair
validation. Exact artifacts and a trace-persistence limitation are in
`docs/scoped_method_research_2026-11-06/REAL_DATA_AUDIT.md` and the registered HuffPost pilot run.
