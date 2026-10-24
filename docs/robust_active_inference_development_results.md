# Robust active-inference allocation: development comparison

This exploratory run adds a comparator to the hard-budget DIVE benchmark. It is an adaptation of
[Robust Sampling for Active Statistical Inference](https://papers.nips.cc/paper_files/paper/2025/file/6389470564214983604d1ac81631c2c5-Paper-Conference.pdf),
not a reproduction of its batch estimator or a new sequential guarantee. The motivation and method
mapping are documented in [closest competitors](../references/closest_competitors.md).

## Method and run

`robust_active_inference_proxy` forms a geometric path from a cost-adjusted square-root residual
second-moment allocation to uniform querying. On the pre-monitor validation slice, it selects one
of 21 path points by minimizing

`mean(v_hat / q) + c * ||1/q||_2 / n`, with `c = 0.5 * ||v_hat||_2` by default.

The path point and propensity multiplier are frozen before monitoring. The residual model may be
updated using past queried labels, so event propensities remain predictable. A common
`q_min=0.05` support bound was used for the monitor, and the runner stopped before spending beyond
the shared pathwise dollar cap. The 0.5 radius fraction is a development setting; it was not
calibrated from an independent radius-selection study.

The CUDA run used seed offset `56110000`, 30 seeds per scenario, 3,200 events, and the stationary,
benign-nuisance, and boundary-local-harm scenarios. It compared uniform, square-root residual
variance, cost-adjusted residual variance, and robust active-inference allocation on common seeds
and common query random numbers. `common_eprocess_bound` was enabled. This was an exploratory
development grid, not a preregistered or confirmatory experiment.

## Results

Every one of the 360 method-stream runs respected its hard label-dollar cap. All 30 harmful
boundary-local streams reached the harm onset before budget stopping for every method. The
single-start monitor detected **0/30** harmful streams for each allocation. No false escalations
occurred among the 30 stationary and 30 benign-nuisance streams per method; these small control
counts do not establish calibration.

| Scenario | Uniform RMSE | Variance RMSE | Cost-variance RMSE | Robust allocation RMSE | Robust minus uniform, paired 95% bootstrap CI |
|---|---:|---:|---:|---:|---:|
| Stationary | 0.0550 | 0.0596 | 0.0590 | 0.0537 | -0.0014 [-0.0111, 0.0081] |
| Benign nuisance | 0.0742 | 0.0556 | 0.0620 | 0.0610 | -0.0133 [-0.0225, -0.0037] |
| Boundary-local harm | 0.0884 | 0.0952 | 0.0957 | 0.0824 | -0.0060 [-0.0192, 0.0084] |

The validation selector chose a mean path parameter `rho=0.545` (standard deviation 0.040; observed
range 0.45–0.60 across the 90 generated streams). In this development block, robust allocation
reduced stream-mean RMSE relative to uniform in the benign-shift cell, while the paired intervals
included zero in stationary and harmful cells. The variance-only rule had lower RMSE than the
robust rule in the benign cell. The robust rule therefore has no demonstrated across-scenario
advantage, and none of these differences can be read as a selected-method-adjusted result. Most
importantly, reduced estimator RMSE did not yield detectable harm evidence under this monitor and
budget in this block.

## Reproduction and artifacts

Run:

```powershell
uv run shiftlab-dive-hard-budget --seeds 30 --seed-offset 56110000 --n 3200 --d 16 --budget-rate 0.10 --q-min 0.05 --q-max 0.50 --device cuda --common-eprocess-bound --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy variance_proxy cost_variance_proxy robust_active_inference_proxy --skip-figure --output outputs/robust_active_inference_development
```

The run stores seed-level Parquet metrics, paired bootstrap summaries, a report, and an environment
and hash manifest in [`outputs/robust_active_inference_development/`](../outputs/robust_active_inference_development/).
No figure was generated because PaperBanana is not available in this session; the saved metrics and
tables are the authoritative results.

## Limitations and next step

This comparison addresses acquisition allocation under immediate labels. It does not validate the
L2 radius, reproduce the source paper's uncertainty-set optimization in full, establish a
sequential variance guarantee, or settle power of the paired-cost monitor. The next step is a
separate radius/path sensitivity design on development seeds followed by a frozen fresh-seed
confirmation that includes the paired-cost detection endpoint. The source paper's asymptotic
no-worse-than-endpoints result must remain confined to its batch inference assumptions.
