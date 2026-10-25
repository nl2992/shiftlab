# Eventwise-scout null calibration under persistent contexts

## Frozen calibration question

The frozen protocol asked whether the eventwise-propensity-bound context scout controls false
promotion across stationary Markov context prevalence, persistence, proxy error, and hard label
caps when every target event satisfies the conditional-mean null. The outcome probability was set
to the FN/FP decision threshold in both latent groups; the fixed switching cost made net expected
gain nonpositive. The protocol was committed before the run and is available at
[`scout_context_policy_eventwise_markov_null_protocol.md`](scout_context_policy_eventwise_markov_null_protocol.md).

## Result

The CUDA run used 1,000 independent streams in each of 36 cells (seed block 20300000–20300999),
with six worker processes. It crossed stationary context prevalence `{0.10, 0.50, 0.90}`, Markov
persistence `{0, 0.50, 0.80}`, proxy error `{0, 0.25}`, and 20%/40% hard caps. The exact eventwise
scout was evaluated with its registered fixed split, candidate-selection procedure, uniform query
process, immediate feedback, and alpha 0.05.

| Calibration summary | Result |
| --- | ---: |
| Streams / cells | 36,000 / 36 |
| False promotions | 262 (0.728%) |
| Largest observed cell rate | 16/1,000 (1.60%) |
| Largest simultaneous one-sided exact 95% upper limit | 3.175% |
| Cells passing the 5% familywise gate | 36/36 |
| Cap violations | 0 |
| Evaluator-defined null checks passed | 36,000/36,000 |

Cell limits used one-sided exact Clopper–Pearson intervals with Bonferroni per-cell alpha
`0.05/36`. The maximum rate and maximum upper limit both occurred at prevalence 0.50, persistence
0.50, proxy error 0.25, and the 40% cap. The pooled false-promotion rates were 0.306% at the 20%
cap and 1.150% at the 40% cap. Every cell's simultaneous upper limit was below 5%, so the frozen
calibration gate passed.

## Interpretation and next step

This is finite calibration evidence for the registered eventwise rule under this Markov context
family and the stated immediate, uniform-query feedback process. It does not by itself prove the
supermartingale result; mathematical validity still rests on predictable selection, the
event-conditional cost null, positive known propensities, bounded paired gains, and the fixed
certification split. It does not cover delayed or selective feedback, adaptive query propensities,
nonstationary context, or different outcome dependence.

Together with the positive-signal development result, the passed gate justifies a disjoint frozen
confirmation on the registered Markov alternatives. Confirmation must retain paired seeds and
compare eventwise with pooled rank and nested volume using simultaneous one-sided limits; the
minimum-bound scout remains a secondary mechanistic comparison. No novelty claim follows.

The full stream and cell Parquet files, report, environment, protocol hash, and SHA-256 checksums
are in [`outputs/scout_context_policy_eventwise_markov_eventwise_null_1000/`](../outputs/scout_context_policy_eventwise_markov_eventwise_null_1000/).
