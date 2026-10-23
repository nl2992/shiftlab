# Fresh evaluation of cost-neutral exact mixture-growth acquisition

This independent 60-seed-per-scenario evaluation follows the registered development grid. The selected development weight was `w=0`, so the exact-growth method reduces to the predictable cost-neutral propensity `q0(x)=b/k(x)`. Metrics are synthetic and evaluator truth is not visible to the query policy. All methods use the same per-stream budget, stream seed, query random uniforms, and fixed e-process bound.

The paired intervals below resample stream seeds. They are descriptive comparisons for this preselected candidate and are not adjusted for the development search. Detection is shown only for the boundary-local-harm alternative; every one of its 60 onsets was reached by every method. Null false-escalation rates are reported separately.

|Scenario|Method|Detection / harmful streams|Paired detection difference vs uniform (95% bootstrap CI)|False escalations / null streams|RMSE difference vs uniform (95% bootstrap CI)|Spend difference|Label difference|Monitor fraction difference|
|---|---|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|uniform_proxy|n/a|n/a|0/60|+0.0000 [+0.0000, +0.0000]|+0.00|+0.0|+0.000|
|benign_nuisance|variance_proxy|n/a|n/a|0/60|+0.0032 [-0.0082, +0.0133]|-0.21|+1.7|-0.173|
|benign_nuisance|decision_value_proxy|n/a|n/a|0/60|+0.0051 [-0.0074, +0.0165]|-0.10|+2.4|-0.143|
|benign_nuisance|cost_variance_proxy|n/a|n/a|0/60|-0.0018 [-0.0118, +0.0070]|-0.13|+9.7|-0.114|
|benign_nuisance|cost_stabilized_proxy|n/a|n/a|0/60|-0.0006 [-0.0067, +0.0062]|-9.29|+12.0|+0.212|
|benign_nuisance|exact_mixture_growth_proxy|n/a|n/a|0/60|-0.0016 [-0.0087, +0.0062]|-17.41|+8.8|+0.224|
|boundary_local_harm|uniform_proxy|4/60|+0.000 [+0.000, +0.000]|n/a|+0.0000 [+0.0000, +0.0000]|+0.00|+0.0|+0.000|
|boundary_local_harm|variance_proxy|3/60|-0.017 [-0.083, +0.050]|n/a|+0.0065 [-0.0007, +0.0134]|+4.24|+4.3|-0.008|
|boundary_local_harm|decision_value_proxy|7/60|+0.050 [-0.033, +0.133]|n/a|+0.0098 [+0.0003, +0.0188]|-0.21|+0.9|-0.033|
|boundary_local_harm|cost_variance_proxy|3/60|-0.017 [-0.083, +0.033]|n/a|+0.0025 [-0.0046, +0.0099]|+6.27|+26.9|-0.009|
|boundary_local_harm|cost_stabilized_proxy|8/60|+0.067 [+0.017, +0.133]|n/a|+0.0056 [+0.0002, +0.0114]|+3.94|+46.4|+0.000|
|boundary_local_harm|exact_mixture_growth_proxy|8/60|+0.067 [+0.017, +0.133]|n/a|+0.0049 [-0.0004, +0.0105]|+3.42|+46.6|-0.000|
|stationary|uniform_proxy|n/a|n/a|0/60|+0.0000 [+0.0000, +0.0000]|+0.00|+0.0|+0.000|
|stationary|variance_proxy|n/a|n/a|0/60|-0.0001 [-0.0074, +0.0066]|+4.24|+4.3|-0.008|
|stationary|decision_value_proxy|n/a|n/a|0/60|+0.0007 [-0.0070, +0.0084]|+8.86|+6.5|-0.050|
|stationary|cost_variance_proxy|n/a|n/a|0/60|+0.0003 [-0.0072, +0.0069]|+6.27|+26.9|-0.009|
|stationary|cost_stabilized_proxy|n/a|n/a|0/60|-0.0020 [-0.0053, +0.0013]|+3.94|+46.4|+0.000|
|stationary|exact_mixture_growth_proxy|n/a|n/a|0/60|-0.0025 [-0.0062, +0.0012]|+3.42|+46.6|-0.000|

## Interpretation

The development selection had 3/30 detections for `w=0`, compared with 2/30 for uniform; all other candidate weights had 0/30. In this independent evaluation, `w=0` detected 8/60 versus 4/60 for uniform. 4 paired streams favored `w=0` and 0 favored uniform; the exact two-sided McNemar/binomial test conditional on discordant pairs gives p=0.125. The paired bootstrap summarizes the same small number of discordances, and this is one synthetic boundary-local alternative. It does not establish general detection superiority.

The selected branch has a positive stream-mean RMSE difference versus uniform in this evaluation. Therefore the result is a detection-versus-estimation tradeoff, not an overall improvement. The cost-neutral derivation controls conditional expected label spend per event under the specified tariff support; the implemented hard cap controls realized spend. Neither property implies optimality across other shift mechanisms, budgets, costs, or policy losses.

Reproduce the acquisition run with `uv run shiftlab-dive-hard-budget --seeds 60 --seed-offset 28502026 --n 3200 --d 16 --budget-rate 0.20 --q-min 0.10 --q-max 0.80 --exact-growth-adaptive-weight 0.0 --common-eprocess-bound --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy exact_mixture_growth_proxy --device cuda --output outputs/cost_neutral_growth_grid_fresh_60`, then run `uv run python scripts/analyze_cost_neutral_growth_fresh.py --output outputs/cost_neutral_growth_grid_fresh_60`.
