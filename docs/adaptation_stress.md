# Controlled adaptation stress and evaluator references

Run the small CPU example:

```powershell
python -m uv run python scripts/adaptation_reference.py --config configs/data/synthetic/adaptation_stress.yaml
```

This generates an immutable concept-shift stream, then writes synthetic evaluator-only
references under `data/reports/evaluator_only/adaptation`. These references are never
part of learner requests. The source version, processing configuration and code identity
are recorded in the protocol. This interface does not implement Paper 3's novel algorithm.

The baseline predictor has coefficient vector `(1,-.9)` and the fixed update has
`(1-severity,-.9)`. In a regime with weight `w`, the true vector is
`(1-severity*w,-.9)`. IID unit-variance Gaussian features imply expected squared losses
`noise²+(severity*w)²` and `noise²+(severity*(1-w))²`. The update remains fixed through
future changes. An independently generated Monte Carlo test checks both references.

`intervention_reference` compares cumulative losses over a bounded horizon at each
independent possible start. Before deployment it retains the stale model; after deployment
it adds the supplied temporary expected-loss penalties to the fixed candidate's risk.
An imposed update cost is in cumulative loss units. Separate resource costs must fit
the supplied remaining compute budget. Ties choose hold. The final horizon is truncated
at stream end. This is a full-future, single-intervention reference, not a dynamic optimum,
an attainable finite-sample estimator, or a sequence of budget-consuming oracle choices.
`ComputeBudget.charge` accounts for actual sequential resource use; rejected charges
leave the budget unchanged. Recalibration requires a separately specified interval-loss
reference and must not be inferred from squared-error risks.

For that separate task, run:

```powershell
python -m uv run python scripts/interval_adaptation_reference.py --config configs/data/synthetic/adaptation_interval_stress.yaml
```

This Gaussian abrupt-variance example computes the expected central interval (Winkler) score
analytically for a stale pre-shift radius and the exact post-shift Gaussian radius. It then
uses the same restricted independent-start comparator, but update, transient and horizon
costs are explicitly in cumulative interval-score units. At the default 1,000-row stream, the
reference selects recalibration at 505/1,000 independent starts for horizon 10 and 567/1,000
for horizon 100. Protocol and per-start CSVs are stored under
`data/reports/evaluator_only/adaptation_interval`. This is an evaluator-only known-DGP
reference; it is not a learned or dynamic recalibration controller, and it does not make
application-cost or finite-sample coverage claims.

The `oblivious_adversarial` temporal pattern assumes scheduled reviews at multiples of
`review_period`. It fixes regime flips one step after those reviews, before observing
any learner actions or stream values. The wait until the next scheduled review is then
`review_period-1`. This is adversarial relative to that schedule, not a claim about all
possible detectors. The configured first-change fraction bounds the earliest flip;
the next aligned flip may occur later. Realized changes are stored in evaluator truth.
One regime, zero severity and stationary-control scenarios still produce the null.

Existing mechanisms can express the remaining adaptation contrasts explicitly:

| Contrast | Mechanism / temporal configuration | Reference interpretation |
|---|---|---|
| Long stationary period | `iid_regression`, or late `concept` change | Hold when the fixed candidate has no net benefit |
| Frequent small changes | `concept`, small severity, `multiple` | Compare cumulative risks over the selected horizon |
| Rare large break | `concept`, large severity, `abrupt` | Update may offset cost after a sufficiently long horizon |
| Recurring known structure | `concept`, `recurring` | A fixed candidate may help one regime and harm the next |
| One-off structural break | `concept`, `abrupt` | Gaussian analytic example applies |
| Temporary shock/recovery | `concept`, `temporary` | Reference integrates recovery, rather than assuming permanence |
| Gradual degradation | `concept`, `linear` or `sigmoid` | Record transition interval, not an invented point change |
| Changing feedback | `feedback_change` | Oracle known losses do not imply labels are available to fit a learner |
| Variable retraining cost | `resource_cost` evaluator cost column | Pass per-start costs in explicit loss/resource units |
| Limited compute | `ComputeBudget`, remaining-budget argument | Beneficial updates can remain infeasible |
| Harm after an update | Nonzero `transient_penalties`, deployment delay | Short horizons may favor hold while longer horizons favor update |
| Adversarial timing | `oblivious_adversarial` | Valid only for the declared periodic-review assumption |

The example loss and resource numbers are imposed research controls. They are not actual
training-time measurements or operational utility. Generic cost units do not establish
which real adaptation intervention is beneficial; each application needs its own reference.
