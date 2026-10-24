# Propensity-floor and e-process bound development grid

**Protocol lock:** 2026-10-24. Development only; no confirmatory method-selection or validity claim.

## Research question

The completed harmful-stream confirmation found much lower fixed-mixture detection for adaptive query policies than for uniform querying. Adaptive policies had a guaranteed propensity floor of 0.10 and a PPI support bound of 96.9; uniform querying had fixed propensity 0.20 and bound 45.9. This grid separates a possible floor effect from a possible query-allocation effect while preserving paired stream seeds and query random numbers.

Compare the registered five query policies under propensity floors 0.10 and 0.11, the same 20% pathwise dollar cap, and the same five scenarios. A tariff-only feasibility preflight over the fixed seed block found the maximum-cost neutral propensity floor ranged from 0.1167 to 0.1237; 0.11 is therefore feasible for the cost-stabilized policy across all registered validation slices, while 0.12 is not. The preflight examined only generated covariate-based tariffs, not labels, harm outcomes, or monitor results. On every realized stream-policy path, evaluate (a) the fixed monitor bound implied by the policy's registered floor, (b) a common conservative 0.10-floor bound, and (c) a propensity-specific event bound as an explicitly assumption-sensitive diagnostic. The monitors are post-processing only and cannot alter query selection, label acquisition, or budget stopping.

## Design

- Scenarios: stationary and benign-nuisance population-null controls; boundary-local harm, recurring regimes, and harmful adaptation.
- Query policies: uniform, variance proxy, decision-value proxy, cost-variance proxy, and cost-stabilized proxy.
- 60 independent stream seeds per scenario, seed block `56000000–56000059`, reused across the two propensity-floor configurations. The block is disjoint from the 54M calibration and 55M harm-confirmation blocks.
- `n=3200`, `d=16`, `alpha=0.05`, excess-cost margin `0.10`, budget rate `0.20`, `q_max=0.80`, maximum tariff `2.5`, CUDA generation, two workers. Do not tune on these seeds or stop early.
- Run each floor configuration (`q_min=0.10` and `q_min=0.11`) with identical per-seed synthetic outcomes and common query uniforms. A raised floor changes the acquisition policy; its comparison is a floor-plus-allocation intervention, not a monitor-only contrast.
- The common 0.10-floor monitor is applied to the same observed PPI increments without changing policy paths. For `q_min=0.11`, this isolates fixed-bound conservatism from the query policy on that path.
- The eventwise diagnostic uses `B_t = M(2/q_t - 1)`, where `M=max(fn,fp)+epsilon`, and the existing fixed stake mixture. It is a valid e-process only if the null holds conditional on the information used to select `q_t` and `B_t`, including current context. The project’s population-average conditional-on-past null does not imply this stronger condition when `q_t` depends on current features. Therefore eventwise-bound null crossings are descriptive diagnostics only and cannot pass calibration, support a deployment guarantee, or determine the primary method.
- Save only per-stream metrics, paired analysis, report, and hash manifest; do not retain event-level traces. Generate no figures under this protocol. If a later protocol requires a figure, create it with PaperBanana.

## Measures and interpretation

For each floor, scenario, policy, and monitor bound, report detection and false-escalation counts, Wilson intervals, paired seed-level rate differences against the registered-floor monitor, onset reachability, delay, propensity summaries, mean labels and spend, processed events, and budget violations. The population-null family is a development diagnostic with 60 seeds and does not establish a 5% false-escalation guarantee. The three harmful scenarios are also development results and cannot select a confirmatory winner.

The primary conclusion is descriptive: whether raising the floor from 0.10 to 0.11 changes adaptive-policy detection and whether the tighter fixed support bound changes detections on exactly the same q_min=0.11 paths. A future confirmatory comparison requires a new registered null-calibration block and fresh harmful-stream seeds. No novelty claim follows from this grid. Closest established references remain bounded-mean e-processes with predictable bets and propensity-weighted prediction-powered inference; this experiment tests their operating characteristics in the registered simulator.

## Reproduction

```powershell
uv run python scripts/run_propensity_floor_bound_development.py
uv run python scripts/analyze_propensity_floor_bound_development.py
uv run pytest tests/test_propensity_floor_bound_development.py -q
```
