# Hard-budget e-process bound sensitivity

The primary comparison uses each method's true minimum propensity in its fixed e-process increment bound. Uniform sampling always queries at 0.10, so it receives a tighter bound than adaptive methods that can query at 0.05. This is operationally valid, but detection differences then combine query allocation with threshold width.

This sensitivity holds the threshold bound common at the registered `q_min=0.05`. It reruns the same uniform streams, same per-seed query uniforms, same hard-dollar budget and same generated outcomes; only the e-process minimum propensity changes. The adaptive methods in the primary run already use this bound. The non-e-process fields of the uniform sensitivity run were checked against the primary uniform run and match exactly.

|Scenario|Method|Minimum propensity in bound|Detections / reached / harmful|False escalations|Mean realized spend|Budget violations|
|---|---|---:|---:|---:|---:|---:|
|benign_nuisance|uniform_proxy|0.05|0 / 1 / 1|0|359.43|0|
|benign_nuisance|variance_proxy|0.05|0 / 1 / 1|0|359.37|0|
|benign_nuisance|decision_value_proxy|0.05|0 / 1 / 1|0|359.39|0|
|benign_nuisance|cost_variance_proxy|0.05|0 / 1 / 1|0|359.34|0|
|benign_nuisance|cost_stabilized_proxy|0.05|0 / 1 / 1|0|352.13|0|
|boundary_local_harm|uniform_proxy|0.05|0 / 30 / 30|0|349.90|0|
|boundary_local_harm|variance_proxy|0.05|0 / 30 / 30|0|352.22|0|
|boundary_local_harm|decision_value_proxy|0.05|0 / 30 / 30|0|351.10|0|
|boundary_local_harm|cost_variance_proxy|0.05|0 / 30 / 30|0|352.50|0|
|boundary_local_harm|cost_stabilized_proxy|0.05|0 / 30 / 30|0|350.89|0|
|stationary|uniform_proxy|0.05|0 / 0 / 0|0|349.90|0|
|stationary|variance_proxy|0.05|0 / 0 / 0|0|352.22|0|
|stationary|decision_value_proxy|0.05|0 / 0 / 0|0|353.17|0|
|stationary|cost_variance_proxy|0.05|0 / 0 / 0|0|352.50|0|
|stationary|cost_stabilized_proxy|0.05|0 / 0 / 0|0|350.89|0|


## Interpretation

On boundary-local harm, uniform detects 4/30 under its tighter method-specific bound but 0/30 under the common `q_min=0.05` bound. The adaptive methods also detect 0/30 under that common bound, even though all 30 onsets are reached. Thus the primary 4-versus-0 difference should not be presented as evidence that uniform allocation is intrinsically more powerful; it is sensitive to the fixed-bound conservatism. The common-bound run is a conservative sensitivity check, not a claim of no power difference. A confirmatory comparison should predeclare one common e-process bound or use a sharper valid eventwise construction, with sample size chosen for detection power.

Reproduce the sensitivity uniform run with `uv run shiftlab-dive-hard-budget --seeds 30 --n 3200 --device cuda --common-eprocess-bound --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy --output outputs/hard_budget_common_bound_sensitivity_30`.
