# Synthetic generator and feedback contract v1

## Status and scope

Implemented four CPU-only synthetic families, thirteen named scenarios per family,
and a multi-model label broker. No real-data reader, network, downloaded dataset,
or protected holdout is invoked. This checkpoint validates the generator contract;
it is not the complete parameter grid or substantive SOTA search.

The entry point is `shiftlab.sota_search.generators.make_world`. Every world has
three fixed analytic models (incumbent, opposite predictor, neutral predictor),
public immutable event tuples, and a separate evaluator-only truth object.
Predictors are specified before all outcomes. No train/test fitting is performed
by these generators, so later baseline fitting/tuning costs must be added explicitly.

## Distinct data-generating mechanisms

| Family | Covariates and conditional law | Hidden evaluator state |
|---|---|---|
| G1 | Gaussian covariates; Bernoulli outcome with logit `1.5 X0 - .6 X1`, modified by the scenario | Scenario schedule and label probability |
| G2 | Gaussian covariates plus a 10% observed subgroup; Bernoulli logit `2 sin(X0) + .8(X1²-1) - .6 group` | Conditional probability and rare-group intervention |
| G3 | AR(1) first feature, rho .6; Bernoulli logit from the linear signal plus a hidden two-state persistent Markov offset | Markov state, schedule and label probability |
| G4 | AR(1) first feature, rho .3; alpha `.3 tanh(X0)-.1 tanh(X1)`; clipped return `clip(alpha + volatility * innovation, -1, 1)` | Persistent Markov volatility (.08 or .20), scenario schedule, finite return support |

G4 innovations are uniformly sampled from 64 midpoint quantiles of Student-t(3).
This finite, clipped law is the actual synthetic DGP. Conditional expected losses
are exact averages over that law. It is not a claim of exact integration under an
unclipped continuous Student-t distribution and says nothing about trading profit.

The existing `SyntheticConfig` / `schedule` machinery supplies abrupt, temporary,
gradual and recurrent schedules. Existing `binary_action`, `binary_risk`, and
`bounded_position` functions supply decision rules and risk calculations. This
reuses the repository's infrastructure without changing historical implementations.

## Prediction loss, decisions and costs

G1–G3 prediction loss is Brier loss in [0,1]. Decision actions are negative (0),
positive (1), or abstention (-1). A mistake costs the disclosed event weight;
abstention costs .2 regardless of the label. Weights lie in [.02,1].

G4 prediction loss is squared return error divided by four. Positions lie in
[-1,1]. With `pnl=position*return`, decision loss is
`.5 - .3*pnl + .15*weight*position² + .05*weight*max(-pnl,0)`, which lies in [0,1].
Labels and switches have separate disclosed costs. A query costs .001 by default;
the expensive-label scenario charges 2, exceeding the maximum per-event benefit
of a label. This does not prove labels cannot benefit multiple future decisions.
Switch cost defaults to .01. Retraining actions and training costs are not yet
implemented at this generator checkpoint.

One true outcome identifies all three model losses: actions do not change the
outcome distribution. This is an explicit full-feedback synthetic assumption,
not off-policy causal identification from selective real-world outcomes.

## Separating the three dimensions

For each realized covariate and latent-state path, the evaluator computes both
the current conditional loss and the nominal conditional loss at the *same*
covariates. Their difference isolates the scenario's conditional/cost change;
it is not an independent population source-risk estimate.

- Distribution diagnostics: imposed nuisance mean displacement, descriptive
  pre/post unbiased kernel MMD, and conditional-outcome-mean displacement.
- Predictive deterioration: current minus nominal expected incumbent Brier or
  normalized squared loss at the realized covariates.
- Decision deterioration: current minus nominal expected incumbent decision cost.
- Challenger benefit: paired current incumbent minus challenger expected cost.
- Available-model regret: current incumbent minus best of the three current
  expected costs, an evaluator-only diagnostic ceiling.

MMD uses up to 128 pre-change and 128 post-change feature rows, with bandwidth
chosen from pre-change features. It is a descriptive statistic, not a calibrated
alarm or a universal distribution distance. In particular, G3/G4 temporal
dependence prevents transferring IID permutation claims to those streams.
Conditional-mean displacement is also a diagnostic, not total variation distance.
Large decision cost relative to a small baseline is not asserted to violate
the standard bounds relating bounded-loss changes and distribution discrepancy.

## Required scenario relations

| Scenario | Intended controlled relation |
|---|---|
| stationary | Nominal law and costs throughout |
| benign_covariate | Last nuisance feature moves by up to five; predictions and outcomes are unchanged |
| harmful_concept | Signal reverses; incumbent prediction and decision risks increase |
| risk_without_harm | Signal reverses but all models abstain/hold flat, fixing decision cost |
| harm_without_accuracy | Outcomes and predictions stay identical; disclosed decision cost rises |
| incumbent_best | The incumbent-aligned signal strengthens rather than reverses |
| transient_challenger | Challenger is preferable only during the temporary reversal |
| challenger_optimal | The opposite predictor becomes preferable after reversal |
| tied_models | All three predictions and decisions coincide |
| labels_too_expensive | Reversal with high disclosed label price |
| localized_harm | Reversal only in a small subgroup, with high subgroup error cost |
| gradual | Linear transition into signal reversal |
| recurrent | Repeated regime changes driven by the existing HMM schedule |

Unit tests verify the dimension-disagreement and challenger-ranking relations,
loss bounds, empirical versus oracle risk agreement, and source/development
separation. These do not certify every future hyperparameter combination.

Not yet covered: the full G1 covariance/prior/missing-feature grid, G2 support
mismatch and feature-correlation grid, G4 volatility/tail parameter grid, arbitrary
model multiplicities, fitted/retrained challengers, and the final held-out
generator-family constructions. These remain requirements of the full programme.

## Proxy information contract

The stale proxy uses the frozen nominal prediction law; miscalibration distorts
that nominal score. Excellent, moderate, weak and anti-informative proxies use
a cheap synthetic auxiliary reading jointly generated with the outcome and
delivered before the paid true label. For classification the reading flips the
outcome with probabilities .05/.25/.5/.95; for returns it is a noisy, independent,
or sign-reversed return reading. This deliberately models an auxiliary information
source and must be matched across every competing algorithm. It is not a learned
model trained on future true labels or an exposed exact DGP probability.

Proxy loss scores use that reading and have small independent estimation noise.
Their actual RMSE against realized losses is recorded; names alone never establish
proxy reliability. Deterioration of a stale proxy after reversal is intentional.

## Query, feedback and isolation contract

Algorithms receive only `PublicEvent`, `QueryReceipt`, and `Feedback` values.
The evaluator alone owns `SyntheticWorld` and `FeedbackStream`. This is an API
boundary, not a security sandbox against deliberately introspective Python code.
Adapters must never receive the broker, world, or raw evaluator artifact path.

At round t:

1. Previously purchased feedback due at t is released, sorted by arrival/index.
2. The current public event appears; a policy chooses its action/query from
   current public information and prior received feedback.
3. One Bernoulli query coin uses the recorded propensity. Paid labels reserve
   the hard count budget immediately, including delayed and eventually missing labels.
4. Immediate labels may be released only after that query decision. A receipt
   reveals no outcome or future arrival time. At budget exhaustion the effective
   propensity is zero and no extra label is bought.

Delay models are fixed, independent geometric, or outcome-dependent. Missingness
is independent Bernoulli with configurable rate. Missing feedback carries no
loss; callers must justify any correction. The existing `EventOrderBuffer` is
available for adapters requiring source-event order. Buffering itself does not
prove statistical validity. Outcome-dependent delay, selective labeling, stopping
after budget exhaustion, and temporal dependence require explicit null/filtration
analysis before any sequential guarantee is claimed.

## World partitions and locked final evaluation

SeedSequence namespaces separate source and development data even for equal
numeric seeds; family and feature/label/proxy/delay streams also have separate
namespaces. Source worlds suppress the scenario transition and use nominal costs.
The current entry point refuses validation or confirmation partitions. A later
freeze-gated implementation must create independent validation and final
confirmation pools, including new generator laws, without exposing outcomes during
selection. No such protected synthetic pool is generated or opened here.

## Registered validation batch, before execution

The driver `scripts/sota_search/validate_generators.py` runs all 52 family/scenario
pairs with seed 281001, horizon 512, stale proxy, independent geometric delay of
mean three, query propensity .2 and hard label count 64. It records boundedness,
feedback purchase/delivery accounting, descriptive dimension diagnostics, raw
evaluator arrays, and per-world JSON. Primary endpoint is contract validity;
there is no algorithm survivor or SOTA comparison selected from this batch.

All attempts use clean committed code/protocol provenance and an immutable batch
manifest, enter the append-only registry, and are subject to both batch limits
and a shared programme ledger. A later failure is retained, not overwritten.
