# PPRM predictive-risk development benchmark

**Status:** frozen development protocol, 2026-10-26. This is the first
end-to-end experiment for `src/shiftlab/dive/pprm_risk_monitor.py`; it is not
an independent confirmation and cannot establish comparative superiority.

## Question

On one controlled binary classification stream, how does prediction-powered
risk monitoring (PPRM) compare with supervised risk monitoring (SRM) when the
fixed classifier's predictive risk changes, and does either predictive-risk
monitor respond to a downstream decision-cost shift that leaves 0–1 risk
unchanged? The experiment keeps predictive degradation and decision harm as
separate outcomes.

## Data-generating process and information contract

Each event has four standard-normal features. The fixed monitored classifier
predicts `1[x0 > 0]`; the frozen auxiliary predictor supplies the synthetic
label `1[x0 > -0.25]`. The true label is Bernoulli with probability
`sigmoid(2*x0)`. The predictive-harm alternative adds an independent 0.30
label-flip probability after event 400. The benign-nuisance scenario shifts
only feature `x1` by +2 after event 400. The decision-cost-only scenario keeps
the feature and label distributions stationary but raises the false-negative
cost from 1 to 4 after event 400.

The learner receives one true label and fifteen disjoint unlabeled inputs per
round. It sees only the current true-label losses and auxiliary-prediction
losses needed by the estimator; evaluator-known scenario, onset, population
risk, and paired policy costs are excluded from the monitors. For the
decision-cost diagnostic, the candidate action is `1[x0 > 0]`, the reference
action is `1[x0 > -0.5]`, and costs are the declared false-positive and
false-negative costs. This imposed cost design is synthetic and is not a claim
about an application.

Source calibration uses 2,048 labeled examples and 30,720 independent source
unlabeled examples, split into disjoint blocks of 15 per labeled observation.
PPRM uses initial reliance 1, a maximum reliance of 1, and the predictable
60-round sliding-window rule. SRM uses only the labeled observations. Both use
the same alpha split (`0.025` source, `0.025` test) and predictive-risk
tolerance 0.05. A separate direct paired-cost e-process receives the same one
label per round, with a 0.05 materiality margin and a predeclared 4.05 bound.

## Frozen run

- Scenarios: stationary, benign nuisance, predictive-risk harm, and
  decision-cost-only shift.
- Replicates: 30 independent seeds per scenario, beginning at 70,000,000.
- Horizon: 1,200 rounds; onset at round 400 for changed scenarios.
- Batch: 1 labeled and 15 unlabeled observations each round.
- Primary summaries: any-alarm rate, post-onset detection rate, first-crossing
  delay, mean processed rounds, predictive risk, and expected paired decision
  cost. Report all per-seed observations and no cross-null pooling.
- Generator: CUDA when available, with an equivalent CPU path. Monitoring
  recursions remain deterministic and use the same generated streams.
- No parameter is tuned from these seeds. Any calibration or independent
  confirmation uses a new registered seed range.

## Interpretation and stopping rule

PPRM and SRM test a running-average predictive-risk null. DIVE's direct
paired-cost process tests an eventwise conditional-mean paired-cost null.
Their alarms answer different questions; report the metric and null beside
every rate. The decision-cost-only scenario is a negative control for
predictive-risk monitors, not evidence of PPRM failure. Thirty streams per
cell are only a development screen. Do not report Monte Carlo rates as proof
of type-I control, and do not infer that a predictive-risk alarm authorizes
adaptation.

The run is useful only if all streams pass support checks, source/test sample
counts and pairing checks, and the frozen seed/horizon checks. Preserve the
result even if all monitors fail to detect a designated alternative.

## Reproduction

```powershell
uv run python scripts/run_pprm_predictive_risk_benchmark.py `
  --seeds 30 --seed-offset 70000000 --device cuda `
  --output-dir outputs/shiftguard_unified/sota_reproductions/pprm_predictive_risk_dev_v1
```
