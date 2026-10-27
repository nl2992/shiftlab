# Frozen reference implementations, v0

**Freeze date:** 2026-10-25. **Repository HEAD:** `525c79e36614c1611a801e3e39d598412efba9ad`. This freezes source implementations for the Phase B benchmark. It does not freeze outcome thresholds, costs, candidate sets, data splits, or experiment protocols; those must be fixed in the benchmark protocols before any comparison run.

## 1. DIVE direct monitor

**Reference:** `shiftlab.dive.eprocess.BoundedMeanEProcess` at repository HEAD. Source: [`eprocess.py`](../../src/shiftlab/dive/eprocess.py), SHA-256 `a9355d3883118ed32039feafe0db0b01fd8824dfbaed2e3d70e6710964565d41`.

The process is the fixed mixture of bounded betting factors in the source. Its benchmark input is a single predeclared bounded paired-cost increment, with the sign convention and tolerance recorded in each protocol. The process is valid only if each increment is adapted to the declared information filtration, remains inside its stated support, and has conditional mean no larger than zero under the null. It is an established bounded-mean e-process. The code is frozen as-is; do not alter its mixture, stake family, boundary or update order during the confirmatory benchmark.

**Historical validation anchor:** the source hash is identical to `eprocess.py` in `outputs/delayed_evidence_ppi_start_mixture_calibration_500/manifest.json`, whose registered conditional null is zero conditional mean under fresh fair sign innovations with a possibly persistent amplitude regime. That calibration supports only that registered synthetic null family. For the unified study, direct full-feedback and query-corrected paired-cost inputs are distinct arms and require separate calibration/protocols; the historical calibration is not sufficient for a new input construction.

## 2. Target-Scout candidate selection and certification

**Reference:** the implementation snapshot from commit `87454014d85c3641a4239d44fb2acf2ec526393a`, source blob SHA-256 `525e7f452e86d32e18f65b3a482da6dad39b8b4ce68c6894ee972bef1595cca0` for `src/shiftlab/dive/budgeted_promotion.py`. The identical blob hash is recorded by the independent confirmation manifest `outputs/scout_context_policy_confirmation_600/reports/manifest.json`.

The frozen candidate is `scout_context_policy`, compared against `rank` and `rank_context_volume` on that confirmation's candidate set and protocol. Selection/scouting information and held-out confirmation feedback must remain separate. The source implementation is frozen to the historical commit for fidelity; do not silently substitute the later current-HEAD version of `budgeted_promotion.py`, whose hash differs. If a benchmark needs the later variant, record it as a new version and rerun its calibration and confirmation.

**Historical result anchor:** 600 confirmation seed blocks across 18 settings; expected post-promotion net-gain contrasts were +5.2837 over `rank` and +4.1822 over `rank_context_volume`; each contrast's simultaneous confidence interval was adjusted to 97.5%, and label caps passed. These are evaluator-known synthetic utility results, not real deployment benefit. The full manifest carries protocol hash, per-source hashes, data artifacts and runtime.

## 3. Existing cost-aware intervention controller

**Reference:** `shiftlab.dive.controller.InterventionController` at repository HEAD. Source: [`controller.py`](../../src/shiftlab/dive/controller.py), SHA-256 `bdeb77dcf4089d72a795d54bd1d2fd9a415757feeb7be020860e3a02b796178c`.

The controller selects the highest positive supplied one-step net value after subtracting label, compute and switching costs. It requires `continue`; promotion and fallback are blocked unless their separate authorization booleans are true. The forecasts supplied in `ActionEstimate` are not certified by this class. Its status is a heuristic resource allocator, not a safety or utility guarantee.

For paired monitoring and intervention, the separate `CertifiedPromotionRollback` state machine in the same file is a different reference component: it uses distinct promotion and rollback e-processes, separate alpha allocations, an amortized intervention-cost threshold, and a fresh feedback condition for post-promotion rollback. Do not silently combine its guarantees with the heuristic controller. The confirmatory protocol must state whether the controller only chooses among already-authorized actions, and must specify how the action forecasts and gates are generated.

**Historical validation anchor:** `contextual_stratified_intervention_results.md` records a registered 2,000-stream synthetic heterogeneous-reversal comparison and independent calibration. The stratified gate gained 13.00 realized net-utility units over continue (95% interval [11.51, 14.51]) in the deliberately balanced, observable-context design. This is evidence about that separate stratified gate, not evidence that the `InterventionController` forecasting heuristic is calibrated or superior.

## Comparators held outside the freeze

These remain open before Phase B exit unless excluded with a documented mismatch: paper-faithful PPRM and Prediction-Powered E-Values; *Comparing Sequential Forecasters*; original-data ASI and robust ASI batch estimators (a fixed-horizon ASI cost-contrast adaptation now exists, but does not reproduce the paper's original tasks); WATCH where a cost-linked score/null can be justified; sample-split candidate evaluation; OCS/HCPI/CPC/AnyRank on compatible action-feedback tasks; CABAI on arm-feedback tasks; RCCDA and *When to Retrain* for resource-constrained updating; and fixed-schedule/never/always intervention controls. Their existence in related work does not imply full source-faithful reproduction in ShiftLab.

## Freeze verification

The DIVE and controller hashes above match the current worktree at the stated HEAD. The Target-Scout frozen source blob is retrievable from local Git history and matches the confirmation manifest; the current `main` source blob is a later implementation and is intentionally not substituted. The full baseline files and their historical records are described in [`evidence_inventory.md`](evidence_inventory.md). Experiment-level parameters remain to be frozen in [`sota_fidelity_matrix.md`](sota_fidelity_matrix.md) and the protocol files.
