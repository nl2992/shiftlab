# Protected multiscale betting comparison protocol

## Candidate and guarantee

Compare three fixed stake mixtures for the same bounded prediction-powered increment `X_t` with prespecified bound `B`:

- Baseline: equal weight on stakes `(0.05, 0.10, 0.20, 0.40, 0.80)`.
- Broad multiscale: equal weight on 13 geometric stakes from `1/1024` to `0.99`.
- Protected multiscale: total prior mass `0.90`, split equally across the five baseline stakes; remaining mass `0.10`, split equally across eight geometric stakes from `1/1024` to `0.04`.

For each fixed `eta in (0, 1]`, `product_t (1 + eta * X_t / B)` is a nonnegative supermartingale under `|X_t| <= B` and `E[X_t | F_{t-1}] <= 0`. A fixed convex mixture preserves this property, so all three mixtures share the same Ville crossing guarantee under the stated assumptions. The protected prior changes power allocation across betting scales; it does not create a new theorem or verify the data assumptions.

## Locked evaluation

Use a fresh seed block, `n=3200`, `d=16`, 60 seeds per scenario, and the existing five query-allocation policies. Include `stationary`, `benign_nuisance`, `boundary_local_harm`, `residual_variance`, `recurring_regimes`, and `harmful_adaptation`; keep the common 20% hard label-dollar cap, propensity bounds `[0.10, 0.80]`, common e-process bound, alpha `0.05`, streams, policy choices, and query random numbers identical across monitors. Run on CUDA when available.

Primary descriptive contrast: protected minus baseline detection over the four shifted/intervention scenarios, paired by seed across all scenarios and allocation policies; bootstrap the 60 seed clusters. Also report discordant protected-only and baseline-only detections within each scenario-policy cell. Stationary and benign-nuisance scenarios are population-null controls for the registered 0.10 margin. Their finite-stream oracle averages may exceed the margin by chance; retain those as pathwise diagnostics and count every alarm as a null false escalation. For controls report alarms per policy out of 60 and separate pathwise materiality flags. Report all hard-budget violations and onset reachability. Do not retune the mixture after inspecting this evaluation block.

## Reproduction

```powershell
uv run shiftlab-dive-hard-budget `
  --seeds 60 `
  --seed-offset 20365022 `
  --n 3200 `
  --d 16 `
  --budget-rate 0.20 `
  --q-min 0.10 `
  --q-max 0.80 `
  --common-eprocess-bound `
  --device cuda `
  --scenarios stationary benign_nuisance boundary_local_harm residual_variance recurring_regimes harmful_adaptation `
  --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy `
  --output outputs/hard_budget_protected_multiscale_60
```

Expected output cardinality: 1,800 allocation-scenario-seed rows. This is a candidate comparison, not a confirmatory universal power claim or a novelty claim.
