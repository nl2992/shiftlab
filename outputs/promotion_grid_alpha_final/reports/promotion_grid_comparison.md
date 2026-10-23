# Forward-time certified candidate grid

Evaluated 6 synthetic scenarios with 30 independent streams each using `cuda` generation. The candidate grid contains one exact copy of the incumbent policy plus 12 logistic-regression candidates per stream. Logistic candidates are fitted on the initial training slice, ranked by labeled validation net gain, frozen before a later shadow-evaluation slice, and only deployed on the final untouched slice.

The one-time switching charge is `0.05`. For certification against its value over the fixed 800-event deployment horizon, it is amortized as `0.00006250` per candidate evaluation event. The deployment metric subtracts the full one-time charge once. Three candidate-level alpha allocations are compared: rank spending `alpha/[i(i+1)]`, equal spending over this finite grid, and validation-power weighting. Validation-power weights are `alpha_i=alpha(0.1/K+0.9 softmax(z_i))`, where `z_i` is the clipped positive validation net-gain z-score and `K` is the grid size. Every allocation is frozen before fresh shadow monitoring and sums to at most alpha, so the union bound remains valid conditional on validation. This pilot-weighting approach is an established weighted-testing idea; we use it as a benchmark, not a novelty claim. The Hoeffding gate is valid for bounded increments under a conditional-mean null. The empirical-Bernstein gate tests average expected gain on the fixed horizon, using independent bounded monitor observations; it allows deterministic changes in distribution over time. Its candidate level is split between variance estimation and the one-sided Bernstein tail.

The sequential certificate is absorbing: after the first `e_t >= 1/alpha_i` crossing it remains certified even if later e-values decline. The statistical gate certifies a mean shadow-period improvement under its conditional-mean and bounded-cost assumptions. It does not guarantee benefit on the later deployment slice if the regime changes. `false_post_nongain` explicitly measures such deployment reversals and is not the same as a false statistical certification. Both action costs are observable on the same synthetic outcome; settings where actions affect outcomes require randomized or off-policy evaluation.

## Untouched deployment performance by controller

Positive net gain means lower decision cost than retaining the incumbent, after the one-time switching charge. Rates and averages use independent seeds as the unit.

| Scenario | Strategy | Promotion rate | Mean expected net gain | Mean realized net gain | Post-promotion nongain rate |
|---|---|---:|---:|---:|---:|
| benign_nuisance | empirical_bernstein_equal_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| benign_nuisance | empirical_bernstein_rank_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| benign_nuisance | empirical_bernstein_validation_power_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| benign_nuisance | fixed_horizon_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| benign_nuisance | never_promote | 0.000 | 0.0000 | 0.0000 | 0.000 |
| benign_nuisance | sequential_equal_alpha_grid_gate | 0.433 | -26.4775 | -21.6550 | 0.133 |
| benign_nuisance | sequential_grid_gate | 0.500 | -24.2991 | -21.4583 | 0.133 |
| benign_nuisance | sequential_validation_power_grid_gate | 0.467 | -25.6401 | -22.1233 | 0.133 |
| benign_nuisance | validation_always_promote | 1.000 | -67.0844 | -66.0500 | 0.367 |
| boundary_local_harm | empirical_bernstein_equal_grid_gate | 0.833 | 227.4031 | 227.5250 | 0.000 |
| boundary_local_harm | empirical_bernstein_rank_grid_gate | 1.000 | 269.9487 | 270.5500 | 0.000 |
| boundary_local_harm | empirical_bernstein_validation_power_grid_gate | 0.900 | 244.7189 | 244.4217 | 0.000 |
| boundary_local_harm | fixed_horizon_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| boundary_local_harm | never_promote | 0.000 | 0.0000 | 0.0000 | 0.000 |
| boundary_local_harm | sequential_equal_alpha_grid_gate | 1.000 | 267.1965 | 267.4833 | 0.000 |
| boundary_local_harm | sequential_grid_gate | 1.000 | 267.1965 | 267.4833 | 0.000 |
| boundary_local_harm | sequential_validation_power_grid_gate | 1.000 | 267.1965 | 267.4833 | 0.000 |
| boundary_local_harm | validation_always_promote | 1.000 | 267.1965 | 267.4833 | 0.000 |
| harmful_adaptation | empirical_bernstein_equal_grid_gate | 1.000 | 279.1764 | 275.1500 | 0.000 |
| harmful_adaptation | empirical_bernstein_rank_grid_gate | 1.000 | 279.1764 | 275.1500 | 0.000 |
| harmful_adaptation | empirical_bernstein_validation_power_grid_gate | 1.000 | 279.1764 | 275.1500 | 0.000 |
| harmful_adaptation | fixed_horizon_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| harmful_adaptation | never_promote | 0.000 | 0.0000 | 0.0000 | 0.000 |
| harmful_adaptation | sequential_equal_alpha_grid_gate | 1.000 | 279.1764 | 275.1500 | 0.000 |
| harmful_adaptation | sequential_grid_gate | 1.000 | 279.1764 | 275.1500 | 0.000 |
| harmful_adaptation | sequential_validation_power_grid_gate | 1.000 | 279.1764 | 275.1500 | 0.000 |
| harmful_adaptation | validation_always_promote | 1.000 | 279.1764 | 275.1500 | 0.000 |
| recurring_regimes | empirical_bernstein_equal_grid_gate | 0.733 | 201.8947 | 200.5967 | 0.000 |
| recurring_regimes | empirical_bernstein_rank_grid_gate | 1.000 | 267.1965 | 267.4833 | 0.000 |
| recurring_regimes | empirical_bernstein_validation_power_grid_gate | 0.867 | 229.2842 | 228.6900 | 0.000 |
| recurring_regimes | fixed_horizon_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| recurring_regimes | never_promote | 0.000 | 0.0000 | 0.0000 | 0.000 |
| recurring_regimes | sequential_equal_alpha_grid_gate | 1.000 | 267.1965 | 267.4833 | 0.000 |
| recurring_regimes | sequential_grid_gate | 1.000 | 267.1965 | 267.4833 | 0.000 |
| recurring_regimes | sequential_validation_power_grid_gate | 1.000 | 267.1965 | 267.4833 | 0.000 |
| recurring_regimes | validation_always_promote | 1.000 | 267.1965 | 267.4833 | 0.000 |
| residual_variance | empirical_bernstein_equal_grid_gate | 0.033 | 4.3205 | 5.0650 | 0.000 |
| residual_variance | empirical_bernstein_rank_grid_gate | 0.033 | 3.3543 | 4.2983 | 0.000 |
| residual_variance | empirical_bernstein_validation_power_grid_gate | 0.033 | 4.3205 | 5.0650 | 0.000 |
| residual_variance | fixed_horizon_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| residual_variance | never_promote | 0.000 | 0.0000 | 0.0000 | 0.000 |
| residual_variance | sequential_equal_alpha_grid_gate | 0.933 | 97.4178 | 99.8867 | 0.000 |
| residual_variance | sequential_grid_gate | 0.967 | 100.3368 | 103.5183 | 0.000 |
| residual_variance | sequential_validation_power_grid_gate | 0.933 | 97.4178 | 99.8867 | 0.000 |
| residual_variance | validation_always_promote | 1.000 | 104.7871 | 108.2833 | 0.000 |
| stationary | empirical_bernstein_equal_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| stationary | empirical_bernstein_rank_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| stationary | empirical_bernstein_validation_power_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| stationary | fixed_horizon_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| stationary | never_promote | 0.000 | 0.0000 | 0.0000 | 0.000 |
| stationary | sequential_equal_alpha_grid_gate | 0.533 | 25.5043 | 29.9400 | 0.000 |
| stationary | sequential_grid_gate | 0.667 | 30.9581 | 34.4000 | 0.000 |
| stationary | sequential_validation_power_grid_gate | 0.600 | 28.4265 | 33.5367 | 0.000 |
| stationary | validation_always_promote | 1.000 | 45.3811 | 46.4833 | 0.000 |

Exact-copy null candidate certificates under rank spending: `0/180 [0.000,0.021]` over candidate-stream tests where the tested action exactly matches the incumbent throughout the shadow interval; its net gain is pointwise negative from the positive switching charge. This simulation is a diagnostic; the familywise guarantee follows from valid candidate tests and conditional alpha weights under their stated assumptions.

Exact-copy null false-certificate counts by allocation: sequential/equal 0/180, sequential/validation-weighted 0/180, empirical-Bernstein/rank 0/180, empirical-Bernstein/equal 0/180, empirical-Bernstein/validation-weighted 0/180.

## Reproduction

`uv run shiftlab-dive-promotion-grid --seeds 30 --seed-offset 20381023 --device cuda --output outputs/promotion_grid_alpha_final`

The candidate-level Parquet preserves all three alpha allocations, their sequential and empirical-Bernstein certification outcomes, evaluator-known shadow gain, exact-copy null status, and untouched deployment outcomes. The strategy-level Parquet compares all alpha-allocation variants with never promote, unconditional validation selection, and the rank-spending Hoeffding gate.
