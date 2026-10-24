# Common hard label-dollar budget comparison

Evaluated 30 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap.

The eventwise e-process monitors use the common configured propensity floor in their support bound; the PPRM-style block confidence sequence instead uses its declared fixed block support.

Each monitor is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Primary detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Primary / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|boundary_local_harm|pprm_block_adaptive|1441.92|1428.08|0.990|953.7|0.993|0.0289|30/30|30|0.000 / 0.000|n/a / n/a|n/a / n/a|0.000 / n/a / n/a|
|boundary_local_harm|uniform_proxy|1441.92|1412.43|0.980|943.7|0.990|0.0320|30/30|30|0.867 / 0.867|0.800 / 0.800|0.800 / 0.800|0.000 / 0.000 / 0.000|
|boundary_local_harm|uniform_proxy_frozen|1441.92|1412.43|0.980|943.7|0.990|0.0325|30/30|30|0.800 / 0.800|0.767 / 0.767|0.767 / 0.767|0.000 / 0.000 / 0.000|
|harmful_adaptation|pprm_block_adaptive|1441.92|1428.08|0.990|953.7|0.993|0.0211|30/30|30|0.000 / 0.000|n/a / n/a|n/a / n/a|0.000 / n/a / n/a|
|harmful_adaptation|uniform_proxy|1441.92|1412.43|0.980|943.7|0.990|0.0243|30/30|30|0.967 / 0.967|0.967 / 0.967|0.967 / 0.967|0.000 / 0.000 / 0.000|
|harmful_adaptation|uniform_proxy_frozen|1441.92|1412.43|0.980|943.7|0.990|0.0255|30/30|30|0.967 / 0.967|0.967 / 0.967|0.933 / 0.933|0.000 / 0.000 / 0.000|
|recurring_regimes|pprm_block_adaptive|1441.92|1428.08|0.990|953.7|0.993|0.0318|30/30|30|0.000 / 0.000|n/a / n/a|n/a / n/a|0.000 / n/a / n/a|
|recurring_regimes|uniform_proxy|1441.92|1412.43|0.980|943.7|0.990|0.0283|30/30|30|0.800 / 0.800|0.800 / 0.800|0.800 / 0.800|0.000 / 0.000 / 0.000|
|recurring_regimes|uniform_proxy_frozen|1441.92|1412.43|0.980|943.7|0.990|0.0281|30/30|30|0.800 / 0.800|0.800 / 0.800|0.800 / 0.800|0.000 / 0.000 / 0.000|
|stationary|pprm_block_adaptive|1441.92|1428.08|0.990|953.7|0.993|0.0300|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy|1441.92|1412.43|0.980|943.7|0.990|0.0225|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy_frozen|1441.92|1412.43|0.980|943.7|0.990|0.0230|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

Each monitor is evaluated only through its hard-budget stopping time. The eventwise monitors are e-processes; the PPI block comparator is a Hoeffding-mixture confidence sequence for the running average of predictable block means. It does not reproduce PPRM's empirical-Bernstein bound. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation and monitor comparison under a finite spend cap, not an intervention controller or a new theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. Eventwise e-process validity requires the documented bounded-increment conditional-mean null and predictable query probabilities. The PPI block confidence sequence assumes bounded block estimates and valid predictable block means; its Hoeffding boundary is conservative and does not provide PPRM's empirical-Bernstein efficiency. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 30 --seed-offset 20372123 --n 6400 --d 16 --budget-rate 0.2 --q-min 0.1 --q-max 0.8 --device cuda --exact-growth-adaptive-weight 1.0 --robust-growth-probability-radius 0.0 --pprm-block-size 20 --pprm-labels-per-block 4 --pprm-max-reliance 0.1 --pprm-initial-reliance 0.1 --scenarios stationary boundary_local_harm recurring_regimes harmful_adaptation --methods uniform_proxy uniform_proxy_frozen pprm_block_adaptive --common-eprocess-bound --output outputs/pprm_block_mixture_weights_development_v1/block_20`.

![Hard-budget tradeoff](../figures/hard_budget_tradeoff.png)

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Primary / multiscale / protected detections / reached|Multiscale-only / primary-only|Protected-only / primary-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|boundary_local_harm|pprm_block_adaptive|-0.0031 [-0.0145, 0.0084]|15.64 [2.24, 29.05]|10.0 [2.6, 17.5]|0.004 [-0.000, 0.008]|0 / n/a / n/a / 30|n/a / n/a|n/a / n/a|n/a / 30|
|boundary_local_harm|uniform_proxy_frozen|0.0005 [-0.0003, 0.0012]|0.00 [0.00, 0.00]|0.0 [0.0, 0.0]|0.000 [0.000, 0.000]|24 / 23 / 23 / 30|0 / 1|0 / 1|0 / 30|
|harmful_adaptation|pprm_block_adaptive|-0.0032 [-0.0102, 0.0036]|15.64 [2.24, 29.05]|10.0 [2.6, 17.5]|0.004 [-0.000, 0.008]|0 / n/a / n/a / 30|n/a / n/a|n/a / n/a|n/a / 30|
|harmful_adaptation|uniform_proxy_frozen|0.0013 [0.0006, 0.0018]|0.00 [0.00, 0.00]|0.0 [0.0, 0.0]|0.000 [0.000, 0.000]|29 / 29 / 28 / 30|0 / 0|0 / 1|0 / 30|
|recurring_regimes|pprm_block_adaptive|0.0035 [-0.0039, 0.0115]|15.64 [2.24, 29.05]|10.0 [2.6, 17.5]|0.004 [-0.000, 0.008]|0 / n/a / n/a / 30|n/a / n/a|n/a / n/a|n/a / 30|
|recurring_regimes|uniform_proxy_frozen|-0.0001 [-0.0010, 0.0008]|0.00 [0.00, 0.00]|0.0 [0.0, 0.0]|0.000 [0.000, 0.000]|24 / 24 / 24 / 30|0 / 0|0 / 0|0 / 30|
|stationary|pprm_block_adaptive|0.0075 [-0.0013, 0.0157]|15.64 [2.24, 29.05]|10.0 [2.6, 17.5]|0.004 [-0.000, 0.008]|0 / n/a / n/a / 0|n/a / n/a|n/a / n/a|n/a / 30|
|stationary|uniform_proxy_frozen|0.0004 [-0.0002, 0.0009]|0.00 [0.00, 0.00]|0.0 [0.0, 0.0]|0.000 [0.000, 0.000]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
