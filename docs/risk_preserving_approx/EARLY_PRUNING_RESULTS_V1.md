# Early promotion pruning: development results v1

2026-10-29. **Decision:** retain as a verified small-cell pruning baseline;
do not select as the proposed research algorithm. No robust speed, memory,
synthetic-efficacy or real-data advantage is established.

## Reproduction and correctness

Protocol was committed before implementation in `EARLY_PRUNING_PROTOCOL_V1.md`.
`src/shiftlab/dive/early_promotion_pruning.py` adds an independent development
adapter: it marks economically dominated first-promotion actions during the
alternative-tree build, skips their continuation calculations and fixes their LP
realization variables to zero. The original null game and available choices are
preserved. A placeholder objective coefficient is safe only because each marked
column is fixed at zero. The adapter uses a temporary process-global LP patch and
is suitable only for the serial isolated runner; it is not a thread-safe library
interface.

`uv run --no-sync pytest tests/test_early_promotion_pruning.py -q`: 6 passed.
Checks covered B=0, delay beyond the horizon, delay 2, T=6, alpha=0, equivalence
of the reference and candidate learner/null information sets, zero probability
of marked promotions, and invariance of the mark to a hidden pending outcome.
The hidden-outcome test checks the information boundary for one representative
case, not every possible controller or delay.

`scripts/research_risk_approx/benchmark_early_pruning.py` ran the registered
three fresh-process repetitions for each of T=5,6,7,8. Full per-run data and
working-tree code/protocol hashes are in `early_pruning_development_v1.json`.
All 24 runs returned, recovered costs agreed within 1e-7 in each cell, and the
independently evaluated exact-rational causal-null risk was 1/10. T=6 recovered
461083/160000. These are known-model reference checks, not the requested real
or synthetic baseline win. The LP is numerical; exact risk refers to the
recovered policy, not an independently certified optimum.

## Timing and memory

Medians in seconds, three runs each on this machine:

| T | Reference build | Pruned build | Reference solve | Pruned solve | Reference / pruned continuation decision-cache entries |
|---|---:|---:|---:|---:|---:|
| 5 | 0.0614 | 0.0648 | 0.0147 | 0.0146 | 205 / 205 |
| 6 | 0.2134 | 0.1839 | 0.0216 | 0.0612 | 467 / 467 |
| 7 | 0.5434 | 0.5565 | 0.0354 | 0.0301 | 933 / 933 |
| 8 | 1.4761 | 1.5095 | 0.0520 | 0.0543 | 1691 / 1691 |

Timings are small, noisy and include only three repetitions. They do not establish
an improvement or asymptotic rate. Both methods had the same builder-node counts
and continuation decision-cache sizes. Skipping 68/132/230/370 promotion calls
at T=5/6/7/8 did not remove cached continuation states in these cells, because
other branches also reached those states. The candidate still builds the same
pre-promotion tree and LP variable structure.

**Memory measurement failure:** Windows' venv Python executable launches the
actual interpreter in a child process. The sampler attached only to the launcher;
its approximately 4.7 MB readings are not worker peak memory and must not be
used. They remain in the raw result as recorded evidence of the measurement
failure. A future registered comparison must sample the actual worker and its
children or use a verified peak-working-set API. No memory conclusion is drawn.

## Research decision

The safe-dominance lemma remains useful as a model-specific preprocessing rule,
but this realization did not improve the costly shared DP cache and leaves the
pre-promotion history tree unchanged. Existing POMDP branch-and-bound and
chance-constrained pruning remain strong prior-art comparators. Continue the
original approximation objective with a different mechanism focused on the
pre-promotion bottleneck; do not run a real-data efficacy study for this adapter.
Preserve this negative result and the prototype for reproducibility.
