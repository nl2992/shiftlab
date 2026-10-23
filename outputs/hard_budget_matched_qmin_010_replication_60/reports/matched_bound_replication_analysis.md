# Matched-bound hard-budget replication

This is a fresh 60-seed replication under the locked protocol in `docs/hard_budget_matched_bound_protocol.md`. All five policies use the same fixed e-process bound with `q_min=0.10`, a 20% target spend rate, and `q_max=0.80`. Each policy shares the same stream seed and hard dollar cap within a stream. Synthetic truth is used for evaluator metrics only.

Validation checks passed: 900 unique method-stream rows; 60 seeds in each of three scenarios; common e-process minimum propensity 0.10; no hard-budget violations.

Exact two-sided Clopper-Pearson intervals describe detection rates. Paired percentile bootstrap intervals use 50,000 resamples of stream seeds and estimate adaptive-minus-uniform differences. These are descriptive intervals for this replication; they are not adjusted for multiple method comparisons.

|Scenario|Method|Detection / streams (95% exact CI)|Harm reached / material|False escalations / streams (95% exact CI)|Mean labels|Mean spend / cap|RMSE|RMSE difference vs uniform (95% paired bootstrap CI)|Mean delay if detected|Detection-rate difference vs uniform (95% paired bootstrap CI)|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|stationary|uniform_proxy|0/60 [0.000, 0.060]|1/1|0/60 [0.000, 0.060]|473.8|712.42 / 721.37|0.0327|—|—|—|
|stationary|variance_proxy|0/60 [0.000, 0.060]|1/1|0/60 [0.000, 0.060]|476.7|715.18 / 721.37|0.0384|+0.0057 [-0.0002, +0.0116]|—|+0.000 [+0.000, +0.000]|
|stationary|decision_value_proxy|0/60 [0.000, 0.060]|1/1|0/60 [0.000, 0.060]|476.4|714.57 / 721.37|0.0429|+0.0102 [+0.0029, +0.0177]|—|+0.000 [+0.000, +0.000]|
|stationary|cost_variance_proxy|0/60 [0.000, 0.060]|1/1|0/60 [0.000, 0.060]|498.8|715.71 / 721.37|0.0380|+0.0053 [-0.0016, +0.0123]|—|+0.000 [+0.000, +0.000]|
|stationary|cost_stabilized_proxy|0/60 [0.000, 0.060]|1/1|0/60 [0.000, 0.060]|518.3|713.25 / 721.37|0.0323|-0.0004 [-0.0051, +0.0042]|—|+0.000 [+0.000, +0.000]|
|benign_nuisance|uniform_proxy|0/60 [0.000, 0.060]|6/6|0/60 [0.000, 0.060]|363.0|719.94 / 721.37|0.0407|—|—|—|
|benign_nuisance|variance_proxy|0/60 [0.000, 0.060]|6/6|0/60 [0.000, 0.060]|364.4|720.01 / 721.37|0.0466|+0.0058 [-0.0020, +0.0138]|—|+0.000 [+0.000, +0.000]|
|benign_nuisance|decision_value_proxy|0/60 [0.000, 0.060]|6/6|0/60 [0.000, 0.060]|365.2|720.09 / 721.37|0.0537|+0.0129 [+0.0064, +0.0197]|—|+0.000 [+0.000, +0.000]|
|benign_nuisance|cost_variance_proxy|0/60 [0.000, 0.060]|6/6|0/60 [0.000, 0.060]|372.4|720.05 / 721.37|0.0424|+0.0017 [-0.0047, +0.0084]|—|+0.000 [+0.000, +0.000]|
|benign_nuisance|cost_stabilized_proxy|0/60 [0.000, 0.060]|6/6|0/60 [0.000, 0.060]|377.6|716.12 / 721.37|0.0391|-0.0016 [-0.0088, +0.0057]|—|+0.000 [+0.000, +0.000]|
|boundary_local_harm|uniform_proxy|8/60 [0.059, 0.246]|60/60|0/60 [0.000, 0.060]|473.8|712.42 / 721.37|0.0554|—|1600.0|—|
|boundary_local_harm|variance_proxy|5/60 [0.028, 0.184]|60/60|0/60 [0.000, 0.060]|476.7|715.18 / 721.37|0.0549|-0.0005 [-0.0087, +0.0077]|1549.0|-0.050 [-0.133, +0.033]|
|boundary_local_harm|decision_value_proxy|8/60 [0.059, 0.246]|60/60|0/60 [0.000, 0.060]|473.6|709.75 / 721.37|0.0647|+0.0094 [-0.0007, +0.0191]|1490.0|+0.000 [-0.100, +0.100]|
|boundary_local_harm|cost_variance_proxy|5/60 [0.028, 0.184]|60/60|0/60 [0.000, 0.060]|498.8|715.71 / 721.37|0.0569|+0.0015 [-0.0078, +0.0109]|1703.0|-0.050 [-0.133, +0.033]|
|boundary_local_harm|cost_stabilized_proxy|12/60 [0.108, 0.323]|60/60|0/60 [0.000, 0.060]|518.3|713.25 / 721.37|0.0548|-0.0006 [-0.0082, +0.0068]|1593.4|+0.067 [+0.000, +0.150]|

## Interpretation

Detection is the primary endpoint only for boundary-local harm. Stationary and benign-nuisance alarm counts are safety diagnostics; benign-shift power is interpretable only for evaluator-labeled materially harmful streams. On boundary-local harm, cost-stabilized allocation detected 12/60 streams versus 8/60 for uniform (paired difference +0.067; 95% seed-bootstrap CI [0.000, 0.150]); the interval touches zero, is not multiplicity-adjusted, and does not establish an advantage. Its RMSE difference was computed on the same paired seeds. Do not infer a general allocation winner from this single block.

No method is declared optimal from this single seed block. Any threshold, allocation, or budget change requires a new seed block for evaluation.
