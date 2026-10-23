# Mixed-sign conditional gains under an aggregate promotion null

This CUDA/CPU experiment uses 2000 independent streams per cell, a 600-event horizon, one frozen candidate, and a pathwise label cap. It constructs an aggregate expected paired gain of exactly zero while conditional gains have opposite signs across two equally likely covariate strata.

The incumbent chooses action 0 and the candidate action 1. In the low-cost stratum the false-positive and false-negative cost is 1 and P(Y=1)=0.56, so candidate gain is +0.12. In the high-cost stratum the symmetric cost is 2 or 5 and its outcome probability is set so expected gain is -0.12 in cost units. Averaging the two strata gives zero overall gain. Thus the candidate is non-improving in the aggregate but violates the pointwise conditional null.

The global process has the aggregate-mean null as its target and uses max_cost/q. The decision-local process divides each queried contrast by the revealed stratum cost/q; this weights low-cost positive gains more heavily and therefore does not test the same aggregate estimand. Both use identical query draws and stop at the same hard cap.

| High cost | Query cap | Bound | Crossings / streams (95% Wilson CI) | Mean labels / cap |
|---:|---:|---|---:|---:|
| 2 | 10% | global | 24/2000 (0.008, 0.018) | 57.0/60 |
| 2 | 10% | decision_local | 49/2000 (0.019, 0.032) | 57.0/60 |
| 2 | 20% | global | 29/2000 (0.010, 0.021) | 116.2/120 |
| 2 | 20% | decision_local | 71/2000 (0.028, 0.045) | 116.2/120 |
| 2 | 30% | global | 35/2000 (0.013, 0.024) | 175.4/180 |
| 2 | 30% | decision_local | 80/2000 (0.032, 0.050) | 175.4/180 |
| 5 | 10% | global | 25/2000 (0.008, 0.018) | 57.1/60 |
| 5 | 10% | decision_local | 59/2000 (0.023, 0.038) | 57.1/60 |
| 5 | 20% | global | 38/2000 (0.014, 0.026) | 116.1/120 |
| 5 | 20% | decision_local | 94/2000 (0.039, 0.057) | 116.1/120 |
| 5 | 30% | global | 41/2000 (0.015, 0.028) | 175.7/180 |
| 5 | 30% | decision_local | 115/2000 (0.048, 0.069) | 175.7/180 |

Under the aggregate null, a decision-local crossing is an erroneous promotion for the stated mean-net-benefit objective, even though it may be valid evidence against the stronger pointwise null. This is a direct falsification check of using local scaling as an aggregate promotion certificate; the Monte Carlo rate does not replace the proof-level estimand argument.

Reproduce with `uv run python scripts/calibrate_mixed_mean_null_local_bounds.py --streams 2000 --horizon 600 --seed 27102026 --device cuda --output outputs/mixed_mean_null_local_bound`.
