# Fresh evaluation of robust mixture-growth acquisition

This independent evaluation uses the development-selected probability radius `0.20`, 60 paired seeds per scenario, and the same hard dollar cap, propensity bounds, common e-process bound, stream seeds, and query uniforms for the robust method and six established baselines. The uncertainty interval is centered on the pre-monitor classifier probability. Evaluator-only coverage compares it with the synthetic true conditional probability after query decisions have been made.

RMSE intervals resample independent stream seeds and are descriptive, unadjusted comparisons across the six baselines. Detection differences are shown descriptively with discordant paired-seed counts; the exact McNemar test is reported for the prespecified robust-versus-uniform contrast because detection events are sparse. Detection is only defined for boundary-local harm; every method's harm reachability is shown separately. A finite run with no false escalation is an implementation diagnostic, not a 5% calibration proof.

`figures/hard_budget_tradeoff.png` plots paired-seed bootstrap intervals for boundary stream-mean RMSE, Wilson intervals for boundary-harm detection, and the processed stream fraction for all seven acquisition policies.

|Scenario|Baseline|Robust detections / baseline|Harm reached robust / baseline|Paired detection difference (wins / losses)|Robust / baseline RMSE|RMSE difference (95% bootstrap CI)|Spend difference|Label difference|Processed-fraction difference|Robust interval coverage|False escalations robust / baseline|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|uniform_proxy|n/a|0/60 / 0/60|n/a|0.0152 / 0.0402|-0.0250 [-0.0316, -0.0184]|-0.64|+7.6|-0.046|0.836|0 / 0|
|benign_nuisance|variance_proxy|n/a|0/60 / 0/60|n/a|0.0152 / 0.0395|-0.0243 [-0.0303, -0.0182]|-0.80|+7.2|+0.133|0.836|0 / 0|
|benign_nuisance|decision_value_proxy|n/a|0/60 / 0/60|n/a|0.0152 / 0.0412|-0.0260 [-0.0315, -0.0204]|-0.80|+6.4|+0.090|0.836|0 / 0|
|benign_nuisance|cost_variance_proxy|n/a|0/60 / 0/60|n/a|0.0152 / 0.0369|-0.0218 [-0.0274, -0.0159]|-0.70|-0.2|+0.072|0.836|0 / 0|
|benign_nuisance|cost_stabilized_proxy|n/a|0/60 / 0/60|n/a|0.0152 / 0.0450|-0.0298 [-0.0367, -0.0226]|+7.62|-4.3|-0.257|0.836|0 / 0|
|benign_nuisance|exact_mixture_growth_proxy|n/a|0/60 / 0/60|n/a|0.0152 / 0.0151|+0.0000 [-0.0012, +0.0014]|-0.89|-0.1|+0.007|0.836|0 / 0|
|boundary_local_harm|uniform_proxy|0/60 / 4/60|60/60 / 60/60|-0.067 (0 / 4)|0.0163 / 0.0496|-0.0333 [-0.0419, -0.0244]|+11.87|+20.5|-0.280|0.854|0 / 0|
|boundary_local_harm|variance_proxy|0/60 / 4/60|60/60 / 60/60|-0.067 (0 / 4)|0.0163 / 0.0514|-0.0351 [-0.0450, -0.0249]|+9.55|+19.9|-0.270|0.854|0 / 0|
|boundary_local_harm|decision_value_proxy|0/60 / 2/60|60/60 / 60/60|-0.033 (0 / 2)|0.0163 / 0.0540|-0.0377 [-0.0458, -0.0293]|+10.36|+20.9|-0.258|0.854|0 / 0|
|boundary_local_harm|cost_variance_proxy|0/60 / 3/60|60/60 / 60/60|-0.050 (0 / 3)|0.0163 / 0.0486|-0.0323 [-0.0423, -0.0221]|+9.01|-1.2|-0.270|0.854|0 / 0|
|boundary_local_harm|cost_stabilized_proxy|0/60 / 3/60|60/60 / 60/60|-0.050 (0 / 3)|0.0163 / 0.0472|-0.0309 [-0.0405, -0.0213]|+11.24|-23.5|-0.280|0.854|0 / 0|
|boundary_local_harm|exact_mixture_growth_proxy|0/60 / 0/60|60/60 / 60/60|+0.000 (0 / 0)|0.0163 / 0.0151|+0.0011 [+0.0002, +0.0024]|-0.09|+0.5|-0.001|0.854|0 / 0|
|stationary|uniform_proxy|n/a|0/60 / 0/60|n/a|0.0117 / 0.0363|-0.0246 [-0.0306, -0.0186]|-1.99|+10.4|-0.053|0.948|0 / 0|
|stationary|variance_proxy|n/a|0/60 / 0/60|n/a|0.0117 / 0.0408|-0.0291 [-0.0352, -0.0226]|-4.31|+9.8|-0.043|0.948|0 / 0|
|stationary|decision_value_proxy|n/a|0/60 / 0/60|n/a|0.0117 / 0.0413|-0.0296 [-0.0360, -0.0228]|-8.61|+6.6|-0.018|0.948|0 / 0|
|stationary|cost_variance_proxy|n/a|0/60 / 0/60|n/a|0.0117 / 0.0404|-0.0287 [-0.0358, -0.0211]|-4.85|-11.4|-0.043|0.948|0 / 0|
|stationary|cost_stabilized_proxy|n/a|0/60 / 0/60|n/a|0.0117 / 0.0369|-0.0252 [-0.0302, -0.0198]|-2.62|-33.6|-0.053|0.948|0 / 0|
|stationary|exact_mixture_growth_proxy|n/a|0/60 / 0/60|n/a|0.0117 / 0.0115|+0.0002 [-0.0003, +0.0007]|-1.19|-0.2|-0.001|0.948|0 / 0|

## Interpretation

The development rule selected radius `0.20` because the candidate radii all had zero boundary-harm detections and this setting had the lowest boundary stream-mean RMSE under the tie-break. In the fresh boundary-harm block, the robust method detected 0/60 and uniform detected 4/60. 0 paired seeds favored robust sampling and 4 favored uniform; exact two-sided McNemar p=0.125. This is evidence about one synthetic scenario only.

Interpret the RMSE contrasts as estimation efficiency, separately from harm detection. A lower stream-mean RMSE does not establish higher e-process power, and the interval-robust optimization is valid only as an allocation objective under the specified probability set. The anytime-validity conditions do not require that set to contain the true post-shift probability, but model misspecification may eliminate the intended allocation benefit.

Reproduce the run with `uv run shiftlab-dive-hard-budget --seeds 60 --seed-offset 28702026 --n 3200 --d 16 --budget-rate 0.20 --q-min 0.10 --q-max 0.80 --robust-growth-probability-radius 0.20 --common-eprocess-bound --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy exact_mixture_growth_proxy robust_mixture_growth_proxy --device cuda --output outputs/robust_growth_grid_fresh_60`, then run `uv run python scripts/analyze_robust_growth_fresh.py --output outputs/robust_growth_grid_fresh_60`.
