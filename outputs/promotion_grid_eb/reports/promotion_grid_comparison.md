# Forward-time certified candidate grid

Evaluated 6 synthetic scenarios with 30 independent streams each using `cuda` generation. The candidate grid contains one exact copy of the incumbent policy plus 12 logistic-regression candidates per stream. Logistic candidates are fitted on the initial training slice, ranked by labeled validation net gain, frozen before a later shadow-evaluation slice, and only deployed on the final untouched slice.

The one-time switching charge is `0.05`. For certification against its value over the fixed 800-event deployment horizon, it is amortized as `0.00006250` per candidate evaluation event. The deployment metric subtracts the full one-time charge once. Candidate index `i` receives `alpha_i=alpha/[i(i+1)]`; because the grid is ordered by validation score before monitoring and every candidate is tested on fresh feedback, the sum of test levels is at most `alpha` for every realized candidate ordering. The Hoeffding gate is valid for bounded increments under a conditional-mean null. The empirical-Bernstein gate tests average expected gain on the fixed horizon, using independent bounded monitor observations; it allows deterministic changes in distribution over time. Its candidate level is split between variance estimation and the one-sided Bernstein tail.

The sequential certificate is absorbing: after the first `e_t >= 1/alpha_i` crossing it remains certified even if later e-values decline. The statistical gate certifies a mean shadow-period improvement under its conditional-mean and bounded-cost assumptions. It does not guarantee benefit on the later deployment slice if the regime changes. `false_post_nongain` explicitly measures such deployment reversals and is not the same as a false statistical certification. Both action costs are observable on the same synthetic outcome; settings where actions affect outcomes require randomized or off-policy evaluation.

## Untouched deployment performance by controller

Positive net gain means lower decision cost than retaining the incumbent, after the one-time switching charge. Rates and averages use independent seeds as the unit.

| Scenario | Strategy | Promotion rate | Mean expected net gain | Mean realized net gain | Post-promotion nongain rate |
|---|---|---:|---:|---:|---:|
| benign_nuisance | empirical_bernstein_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| benign_nuisance | fixed_horizon_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| benign_nuisance | never_promote | 0.000 | 0.0000 | 0.0000 | 0.000 |
| benign_nuisance | sequential_grid_gate | 0.500 | -24.2991 | -21.4583 | 0.133 |
| benign_nuisance | validation_always_promote | 1.000 | -65.8261 | -64.5500 | 0.367 |
| boundary_local_harm | empirical_bernstein_grid_gate | 1.000 | 271.7651 | 272.0500 | 0.000 |
| boundary_local_harm | fixed_horizon_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| boundary_local_harm | never_promote | 0.000 | 0.0000 | 0.0000 | 0.000 |
| boundary_local_harm | sequential_grid_gate | 1.000 | 269.0129 | 268.9833 | 0.000 |
| boundary_local_harm | validation_always_promote | 1.000 | 269.0129 | 268.9833 | 0.000 |
| harmful_adaptation | empirical_bernstein_grid_gate | 1.000 | 279.1283 | 274.8500 | 0.000 |
| harmful_adaptation | fixed_horizon_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| harmful_adaptation | never_promote | 0.000 | 0.0000 | 0.0000 | 0.000 |
| harmful_adaptation | sequential_grid_gate | 1.000 | 279.1283 | 274.8500 | 0.000 |
| harmful_adaptation | validation_always_promote | 1.000 | 279.1283 | 274.8500 | 0.000 |
| recurring_regimes | empirical_bernstein_grid_gate | 0.967 | 256.9641 | 256.7517 | 0.000 |
| recurring_regimes | fixed_horizon_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| recurring_regimes | never_promote | 0.000 | 0.0000 | 0.0000 | 0.000 |
| recurring_regimes | sequential_grid_gate | 1.000 | 269.0129 | 268.9833 | 0.000 |
| recurring_regimes | validation_always_promote | 1.000 | 269.0129 | 268.9833 | 0.000 |
| residual_variance | empirical_bernstein_grid_gate | 0.033 | 3.3543 | 4.2983 | 0.000 |
| residual_variance | fixed_horizon_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| residual_variance | never_promote | 0.000 | 0.0000 | 0.0000 | 0.000 |
| residual_variance | sequential_grid_gate | 0.967 | 101.3661 | 104.2183 | 0.000 |
| residual_variance | validation_always_promote | 1.000 | 105.8164 | 108.9833 | 0.000 |
| stationary | empirical_bernstein_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| stationary | fixed_horizon_grid_gate | 0.000 | 0.0000 | 0.0000 | 0.000 |
| stationary | never_promote | 0.000 | 0.0000 | 0.0000 | 0.000 |
| stationary | sequential_grid_gate | 0.700 | 33.0494 | 37.3317 | 0.000 |
| stationary | validation_always_promote | 1.000 | 45.3330 | 46.1833 | 0.000 |

Exact-copy null candidate certificates: `0/180 [0.000,0.021]` over candidate-stream tests where the tested action exactly matches the incumbent throughout the shadow interval; its net gain is pointwise negative from the positive switching charge. This simulation is a diagnostic; the familywise guarantee follows from valid candidate e-processes and alpha spending under their stated assumptions.

## Reproduction

`uv run shiftlab-dive-promotion-grid --seeds 30 --seed-offset 20381023 --device cuda --output outputs/promotion_grid_eb`

The candidate-level Parquet preserves validation ranking, candidate alpha, sequential, Hoeffding, and empirical-Bernstein certification, evaluator-known shadow gain, exact-copy null status, and untouched post-promotion outcomes. The strategy-level Parquet contains paired deployment outcomes for never promote, unconditional validation selection, both fixed-horizon gates, and sequential certification.
