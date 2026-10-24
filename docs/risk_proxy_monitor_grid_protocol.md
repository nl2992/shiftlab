# Risk-proxy monitor comparison protocol

## Question and estimand

The proxy stress grid found consistent reduction in prediction-powered estimator RMSE from a
training-only logistic decision-risk proxy, without a reliable detection gain. This study isolates
the monitor: it compares three already implemented, mathematically valid processes while keeping
the proxy, policy pair, outcomes, query randomization, label costs, and hard dollar cap matched.

Each monitor tests the history-conditional mean null for centered paired decision cost,
`E[Z_t - epsilon | F_(t-1)] <= 0`, with the same known global prediction-powered support bound.
Compare the fixed stake-mixture e-process, predictable plug-in Kelly e-process, and predictable
plug-in empirical-Bernstein process. The latter two use past observations only to choose their
next stake. No algorithm or validity theorem is claimed as new.

## Frozen design

Use two registered population-null controls: stationary outcomes and large benign nuisance shift.
Use four alternatives: boundary-local harm, residual-variance shift, recurring regimes, and
harmful adaptation. Run query rates 0.20 and 0.40 with false-negative/false-positive costs 5:1,
the registered 0.10 materiality margin, 2,400 events, a 12.5% historical training slice, and a
12.5% validation/budget-calibration slice. Fit one logistic outcome model on historical training
labels and freeze the probability-derived paired-cost proxy before monitor labels arrive. Use
outcome-independent Bernoulli query uniforms and the same path for all monitor processes.

Run 1,000 streams per null-scenario/query-rate cell and 300 per alternative-scenario/query-rate
cell. The seed block begins at 20403024 and is disjoint from the proxy-development blocks. Apply
one-sided exact Clopper-Pearson upper bounds with Bonferroni coverage across the 12 null
scenario-by-rate-by-process cells. The finite calibration pass criterion is an upper bound no
larger than 5% in every cell. This simulation check supplements the proof; it does not replace it.

## Validity assumptions

For each event, the query propensity is known, positive, and chosen before the outcome. Conditional
on current features and past history, query randomization is independent of the current outcome.
The risk proxy and support bound are available before current feedback. Thus the prediction-powered
estimate remains conditionally unbiased, and a valid bounded-mean e-process remains valid under the
eventwise history-conditional null. The fixed mixture, predictable Kelly, and plug-in empirical-
Bernstein implementation guarantees are documented and tested in `src/shiftlab/dive/eprocess.py`.

The synthetic stationary and nuisance-shift controls are nondegenerate for the paired-cost process;
verify their stream-level contrast variance in the saved output. A zero-alarm result is reported
with the simultaneous upper bound. Do not claim a theorem from Monte Carlo frequencies. The study
uses immediate labels, a frozen deployed/reference policy pair, known synthetic cost matrices, and
evaluator-only change parameters; external validity and candidate promotion remain out of scope.

## Reproduction

```powershell
uv run shiftlab-dive-risk-proxy-monitor-grid --device cuda --null-seeds 1000 --alternative-seeds 300 --seed-offset 20403024 --n 2400 --output-dir outputs/risk_proxy_monitor_grid
```

The run saves event-stream metrics, scenario summaries, Bonferroni-adjusted null calibration, code
hashes, runtime information, and a checksum manifest. No figure is prespecified. Use PaperBanana
for any later visual and verify its values against the saved metrics.
