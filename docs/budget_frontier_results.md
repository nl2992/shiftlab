# Budget frontier: measured results

This is the completed screening result for the paired hard-dollar acquisition frontier. The frozen comparison uses 60 independent streams per scenario, seven registered policies, `n=3200`, and target budget rates of 10%, 20%, and 25%. It covers stationary and benign-nuisance controls plus boundary-local harm and recurring regimes. The full row-level metrics, confidence intervals, manifest, and figure are in [`outputs/budget_frontier_60/reports/budget_frontier.md`](../outputs/budget_frontier_60/reports/budget_frontier.md), [`outputs/budget_frontier_60/metrics/budget_frontier.parquet`](../outputs/budget_frontier_60/metrics/budget_frontier.parquet), and [`outputs/budget_frontier_60/figures/budget_frontier.png`](../outputs/budget_frontier_60/figures/budget_frontier.png).

The manifest's hard-budget source hashes match Git commit `64d0aad`, and its analysis-script hash matches `1b02af6`; the generated result package is committed at `de9d68e`.

## Main findings

- **The decision-harm monitor did not detect harm in this design.** Every method had 0/60 single-e-process detections for both harmful scenarios at every budget. All 60/60 harmful streams reached the known harm onset before budget stopping, so this is not explained by onset censoring. The 95% Wilson interval for each 0/60 rate is 0% to 6.0%. This is weak evidence about power and does not establish that the monitor lacks power in other regimes.
- **No control-stream escalations occurred.** Each method had 0/60 false escalations on stationary and benign-nuisance controls at every budget. The same 6.0% Wilson upper endpoint means this sample cannot establish 5% calibration. Zero observed errors are not a calibration result.
- **Exact and robust mixture-growth allocation reduced stream-mean estimation RMSE against uniform in both harmful scenarios at all three budgets.** For exact mixture-growth, RMSE was 0.0280 versus 0.0859 at 10%, 0.0167 versus 0.0457 at 20%, and 0.0150 versus 0.0419 at 25% for boundary-local harm. For recurring regimes it was 0.0299 versus 0.0660, 0.0211 versus 0.0477, and 0.0190 versus 0.0419. Paired bootstrap 95% intervals for each exact-mixture RMSE difference were below zero; the full intervals appear in the generated report.
- **The robust mixture did not clearly improve on exact mixture-growth.** Its RMSE was nearly identical at 20% and 25%, and slightly higher at 10% in both harmful scenarios. Both methods had the same zero harm detections. The current grid therefore provides no evidence that the robustness radius improves monitoring or estimation over the exact allocation.
- **Lower RMSE came with shorter monitored horizons for mixture-growth policies.** At the 25% budget, exact mixture-growth processed 71.3% of the boundary-harm stream and 53.4% of recurring-regime streams on average, versus 98.2% for uniform. The event onsets were still reached in all 60 streams. Any follow-up should treat estimation accuracy, detection, and observation horizon as separate outcomes.
- **Hard caps were respected throughout.** The combined table has 5,040 method-stream rows and zero cap violations. Mean realized spend was close to each target cap. The upper endpoint is 25% because 30% is infeasible under the common `q_max=0.80` and the registered tariff support; the derivation and validation-slice check are documented in [`budget_frontier_protocol.md`](budget_frontier_protocol.md).

## Interpretation and next experiment

The strongest current result is a separation between estimation and monitoring: the mixture-growth samplers estimate stream-mean excess cost more accurately in this synthetic design, but that improvement did not translate into a single sequential harm escalation. This is a benchmark finding, not a new algorithm or a novelty claim. The zero-event cells are too small to establish either nominal false-alarm control or useful power.

One plausible power bottleneck is the shared worst-case bound. With maximum cost 5, margin 0.10, and `q_min=0.05`, the proxy is clipped at `M=5.1` and each prediction-powered increment is bounded by `M(2/q_min-1)=198.9`. The harmful streams' mean expected decision-cost difference is about 0.26, so the mean excess over the margin is only about `0.16/198.9 = 0.0008` of this bound before variance is considered. This is a scale diagnosis, not a proof that the bound alone caused every miss. The next development experiment compares predictable stake rules while keeping this global bound and the sampled increments unchanged.

No detection delay can be estimated because there were no single-e-process alarms. This grid has no intervention controller, so it does not measure cumulative decision loss, intervention costs, or regret; those remain required outcomes for the next decision-focused controller study.

The next study should diagnose power before adding a new acquisition rule: use a development-only grid over harm effect size, onset time, monitoring length, and predictable propensity floor, then freeze a confirmation design with a nonzero expected detection rate. Keep the 5% decision-harm margin and the e-process assumptions explicit; report detection delay conditional on detection, onset reachability, false escalation, cumulative decision loss, and realized spend. Any changed monitor or query policy needs fresh seeds and a separate null calibration study.

## Reproduction

```powershell
uv run python scripts/grid_search_budget_frontier.py `
  --output outputs/budget_frontier_60 `
  --seeds 60 `
  --seed-offset 28802026 `
  --n 3200 `
  --d 16 `
  --budgets 0.10 0.20 0.25 `
  --scenarios stationary benign_nuisance boundary_local_harm recurring_regimes `
  --device cuda
```

CUDA was available on the NVIDIA GeForce RTX 4060 Laptop GPU and used for the generator's latent random draws. Policy fitting and most sequential evaluation remain CPU NumPy/scikit-learn work; the per-stream workload is too small to keep the GPU busy. The run manifest records the device and software versions.
