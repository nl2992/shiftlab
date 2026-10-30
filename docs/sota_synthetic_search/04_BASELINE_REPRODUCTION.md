# Baseline reproduction status

No baseline is a VERIFIED_REPRODUCTION (see `01_*`). Checks actually run (`tests/sota_search`, 9 tests):
- **Causality of the feedback contract:** perturbing events after step 300 leaves the labeled evidence before step 305 unchanged (delay 5).
- **Null calibration of theory-threshold methods** (`pr_cs`, `pprm`, `watch`, `pp_cost`, and the tight variants): crossing probability ≤ 0.08 on 300 null streams.
- **Distinction:** the decision-cost e-process detects harmful `concept` shift and ignores large benign `cov_benign` shift.
- **Bet-cap validity:** with the tight one-sided cap every betting factor stays ≥ 0.5 for both risks, so the supermartingale argument is unchanged.

## A baseline defect found by the search itself
The initial `pprm` and `pp_cost` used a symmetric worst-case cap `M(2/q−1)+M` (M = 5 for decision cost, 1 for Brier). Positivity of `1+λX` only needs the one-sided minimum `−(R̂(1/q−1)+r₀+tol)`, which is 8× (Brier) to 13× (cost) smaller at q = 0.2. The loose versions are therefore **weak baselines** of my own making and are kept only as the historical implementation; **`pprm_tight` and `pp_cost_tight` are the strong baselines** used from here on. Any improvement over the loose versions is a correction, not a contribution.
