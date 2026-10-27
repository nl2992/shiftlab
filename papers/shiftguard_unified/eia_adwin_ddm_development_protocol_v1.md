# ADWIN and DDM on EIA: matched drift-triggered retraining protocol

**Version:** 1.0  
**Status:** frozen exploratory development comparison; not confirmation.  
**Question:** Do published error-stream drift detectors add useful retraining points to the EIA resource frontier containing CARA, UPF, RCCDA, and operational controls?

## Scope and source fidelity

The official CARA repository includes ADWIN and DDM retraining baselines implemented through scikit-multiflow. This experiment uses River 0.26.1, the maintained successor ecosystem to scikit-multiflow, and labels these as detector adaptations rather than reproductions of the official implementation. ADWIN receives bounded normalized absolute regression loss. DDM receives a Bernoulli exceedance indicator because its original input is a binary error stream; an error is defined as bounded loss greater than the period-0 in-sample 95th-percentile normalized loss. ADWIN uses `delta=0.002`; DDM uses River defaults `warm_start=30`, `warning_threshold=2`, and `drift_threshold=3`.

## Data and feedback contract

Use the exact EIA EBA release, 15 contiguous periods, features, Ridge candidate models, robust loss scale, assumed additional label delays (0 and 168 hours), and eight online held-out tails in [`cara_eia_development_protocol_v1.md`](cara_eia_development_protocol_v1.md). The checked CARA v1 matched result is the input frontier and retains CARA-T, CARA-CT, and CARA-P plus never/always, periodic, error-threshold, UPF, RCCDA, and evaluator-only oracle methods.

At period `t`'s evaluation-tail start, the detector processes only current-period prefix outcomes that are finite and mature by that cutoff. Rows are fed in their recorded event order. Scores are computed under the incumbent model active before the period decision. If a detector reports at least one change during the batch, the candidate model trained on labels mature at this same decision boundary is selected for that period's held-out tail. During warm-up periods 1–6, the detector state is updated using the same event-time rule; at the end of period 6 the common period-6 model is installed as the declared online incumbent while detector state is preserved. No evaluation-tail feature or outcome enters a detector decision.

All alarms within one prefix batch lead to at most one model promotion at its tail boundary. An alarm detected from a batch cannot cause a model to be fitted on labels that have not matured at that boundary. All historical source release timestamps remain unknown; the added delay is imposed as a sensitivity convention.

## Outcomes and stopping rule

Run exactly 2 domains × 2 delay settings × 2 detector methods over the eight online periods. Compare held-out bounded loss, raw MAE/RMSE, update count, fit-row proxy, and `sum(bounded loss) + alpha * updates` across the unchanged ten-point `alpha` frontier. Preserve each authority as a separate historical series. The oracle is evaluator-only and must remain no worse than every feasible method in total objective for each of the 40 frontier cells.

Stop after detector outputs, matched row keys, label-maturity cutoffs, source/data/artifact hashes, candidate chronology, and oracle lower-bound checks pass. No figures are generated here; future research visuals must use PaperBanana and validated source metrics.

## Interpretation limits

This is a task-specific drift-detection adaptation on two previously inspected retrospective electricity series. DDM's regression-to-binary mapping is imposed, River's detector code is not byte-for-byte scikit-multiflow, label delays are assumed, and decision costs are normalized research scenarios. The result does not establish a sequential false-alarm guarantee, real-time deployment performance, causal intervention value, independent real-data confirmation, or general detector superiority.
