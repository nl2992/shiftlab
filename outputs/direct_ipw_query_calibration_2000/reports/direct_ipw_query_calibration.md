# Direct-IPW history-evidence query null calibration

**Status: calibration_passed.** This fresh-seed calibration evaluates the candidate frozen after the separate development grid: `evidence_curve_a0_p0.5` at `q_min=0.05`, against `uniform_proxy`. It is not confirmation of harm-detection power.

The run used 2000 independent stream seeds per cell, seed IDs `32102026`–`32104025`, n=3200, d=16, a 20% realized label-dollar cap, `q_max=0.80`, alpha=0.05, and immediate randomized labels. Both methods share the scenario/seed stream and query random numbers. Requested device: `cuda`; resolved device: `cuda`. The candidate's query propensities use only prior monitor wealth and past realized spend.

The four-cell family is the two frozen population-null controls (`stationary`, `benign_nuisance`) crossed with both query procedures. Each one-sided exact Clopper–Pearson upper limit uses Bonferroni cell alpha 0.0125, giving at least 95% simultaneous coverage. A calibration cell passes only when it has all registered seeds and its upper limit is at most 0.05; the family passes only when every cell passes and all run invariants hold.

|Scenario|Query procedure|Streams|False escalations|Rate|Simultaneous CP upper|Mean labels|Mean spend|Mean events|Cell pass|
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
|benign_nuisance|evidence_curve_a0_p0.5|2000|0|0.0000%|0.2189%|197.3|398.75|2397.6|True|
|benign_nuisance|uniform_proxy|2000|0|0.0000%|0.2189%|362.8|718.64|1813.1|True|
|stationary|evidence_curve_a0_p0.5|2000|0|0.0000%|0.2189%|208.0|311.86|2400.0|True|
|stationary|uniform_proxy|2000|0|0.0000%|0.2189%|471.1|706.54|2353.9|True|

The formal guarantee is the bounded-mean e-process argument under the history-conditional null, predictable query probabilities, immediate unbiased randomized feedback, and the registered support bound. The finite simulator calibration does not prove those assumptions, extend to delayed or selectively observed labels, establish robustness to unregistered dependence, or establish a query-policy advantage. A disjoint alternative confirmation is a separate step.

Reproduce with `uv run shiftlab-dive-direct-ipw-query-calibration --output outputs/direct_ipw_query_calibration_2000 --seeds 2000 --seed-offset 32102026 --n 3200 --d 16 --device cuda --workers 4`.
