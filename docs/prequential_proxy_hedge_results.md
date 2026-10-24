# Prequential proxy-Hedge development results

## Design and mathematical scope

The CUDA development grid ran 100 shared seeds in each of six synthetic scenarios (3,600
method-stream rows). Six proxy choices used the same event-level query uniforms, fixed 20% query
probability, global PPI support bound, and realized dollar cap within each scenario/seed. Four
material-harm scenarios contributed to the clustered detection comparison. The complete frozen
design is in [`prequential_proxy_hedge_protocol.md`](prequential_proxy_hedge_protocol.md); raw
metrics and source hashes are in [`outputs/prequential_proxy_hedge_development/`](../outputs/prequential_proxy_hedge_development/).

The predictable Hedge proxy is mathematically admissible: its weights are updated only after queried
labels, its output is a convex combination of bounded pre-outcome forecasts, and the prediction-
powered correction remains unbiased under the specified Bernoulli query mechanism. With normalized
squared expert losses in `[0,1]`, inverse-propensity losses are bounded by `1/q_min`; the ordinary
exponential-weights regret bound applies to those realized bounded losses. This does not prove
better detection power. The monitor guarantee still depends on the stated history-conditional null,
outcome-independent query randomization, and known common support bound.

## Findings

Against fixed ridge, prequential Hedge improved the seed-clustered macro detection rate by **4.25
percentage points** (95% bootstrap interval **[2.25, 6.50]**). Detection was 70% versus 67% for
boundary-local harm, 70% versus 63% for recurring regimes, 96% versus 89% for harmful adaptation,
and 0% for both methods under residual-variance shift. It reduced estimator RMSE versus ridge in
each of the four material-harm scenarios.

The stronger static comparator performed better. The training-only logistic risk proxy detected 77%
of boundary-harm streams and 78% of recurring-regime streams, versus 70% for Hedge in both; its
paired macro detection advantage over Hedge was **3.50 points** (post-hoc seed-cluster 95% interval
**[1.00, 6.25]**). It also had lower macro estimator RMSE (1.75 versus 1.84). The validation-selected
single proxy averaged 60.75% detection versus Hedge's 59.00%; its post-hoc paired interval for
Hedge-minus-validation-best was **[-4.00, 0.50]** points. Hedge's only clear advantages are over
ridge and the weaker fixed proxies. Thus the adaptive mixture did not beat the best simple
decision-aware proxy and **does not advance to confirmation**.

All six methods received identical labels, spend, and processed horizon within each stream; there
were no cap violations. The two population-null controls had 0/100 false escalations per method. A
two-sided exact 95% bound for 0/100 still reaches 3.62%, and these development diagnostics are not
simultaneous calibration evidence. No method detected residual-variance harm in this design,
indicating a monitor-power limitation shared across proxy choices.

## Decision and next work

Retain `prequential_hedge` as a tested, mathematically valid proxy-aggregation baseline; stop this
candidate as a lead method. The fixed logistic risk proxy is the strongest tested choice in this grid,
but it is a standard supervised conditional-cost prediction and not a novelty claim. Before spending
on a confirmation, stress-test that proxy against ridge and the validation-selected predictor under
registered misspecification, nuisance-shift severity, label rates, and bounded-cost changes. Any new
method should improve on this stronger comparator, not only on ridge.

The aggregate experiment has no figure. PaperBanana is required for future research visuals when it
is available.
