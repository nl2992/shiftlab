# Feature-dependent promotion and rollback integration protocol

## Purpose and status

This protocol integrates the existing `CertifiedPromotionRollback` gate with ShiftLab's logged
decision-stream contract and feature-dependent binary decision costs. It is a development
benchmark. It does not replace the existing Bernoulli-cost intervention study, establish a new
guarantee, or support a novelty claim. Development outcomes must not be used to select and report a
confirmatory result on the same seeds.

## Data-generating process

Each stream has a shadow phase and a forward deployment phase, each with `H` events. Features are
independent standard Normal vectors in eight dimensions. The incumbent always selects action 0; a
candidate is frozen before each stream and selects action 1 exactly when `X[0] > 0`. The binary
outcome is sampled independently conditional on the phase and candidate action region. In the
candidate region, the positive-outcome probabilities are:

| Scenario | Shadow | Deployment | Purpose |
| --- | ---: | ---: | --- |
| `stationary` | 1/6 | 1/6 | Exact zero candidate gain under FN=5, FP=1 |
| `benign_nuisance` | 1/6 | 1/6 | Same null, with a +3 shift in nuisance coordinates after the phase boundary |
| `boundary_local_harm` | 1/6 | 0.50 | Candidate does not improve in shadow; the incumbent becomes harmful in deployment |
| `harmful_adaptation` | 0.50 | 0.05 | Candidate benefits in shadow, then reverses and should be rolled back |
| `persistent_benefit` | 0.50 | 0.50 | Positive deployment-gain control for rollback monitoring |
| `rollback_boundary` | 0.50 | `1/6 - k_rollback/(3H)` | Least-favourable rollback-null calibration; expected deployment gain equals `-k_rollback/H` |

Outside the candidate action region, the outcome probability is 0.25; both policies take action 0
there, so it does not affect the paired contrast. For a positive-region event the incumbent-minus-
candidate expected gain is `(FN + FP) p - FP = 6p - 1`. Since `P(X[0] > 0)=1/2`, the population
mean gain is `(6p - 1)/2`. Thus `p=1/6` is an exact marginal zero-gain control. All costs and
change profiles are imposed synthetic research utilities, not application estimates.

## Learner interface and filtration

The learner receives `DecisionRequest` before choosing the action and query, then the logged
`PolicyDecision`, and receives `DecisionFeedback` only when a queried label arrives. The
`OracleDecisionRecord` and the true phase probabilities remain evaluator-side and are not arguments
to stream replay. Actions depend only on current features and the already frozen policy pair.
The label query coin has fixed propensity `q`, is drawn before and independently of the current
outcome, and is logged for queried and unqueried events. Labels are immediate in this first
integration. A single hard cap is applied across shadow and deployment; after exhaustion, the gate
continues with a zero evidence contribution and incurs no new label acquisition.

Paired costs are identifiable because the simulator's binary label defines both actions' losses.
This is not valid for arbitrary action-dependent outcomes. That case needs randomized behavior
policies or a stated off-policy identification design and separate support checks.

## Gates and bounds

Let `G_t = c(incumbent(X_t), Y_t) - c(candidate(X_t), Y_t)`, with known `|G_t| <= M=5`. For a
queried event use `I_t G_t/q`; for an unqueried event use zero. Promotion tests the conditional-mean
null `E[G_t | F_{t-1}] <= k_promote/H` using increments `I_t G_t/q - k_promote/H`. After promotion,
rollback tests `E[-G_t | F_{t-1}] <= k_rollback/H` using increments `-I_t G_t/q - k_rollback/H`.
The event support bound is `M/q + k/H`; the gate allocates `alpha/2` to each stage. The intervention
cost is expressed in the same imposed decision-cost units as `G_t` and amortized over the fixed
deployment horizon.

The standard bounded-factor e-process guarantee requires the stated conditional-mean null,
predictable policies/query propensity, positive query support while querying, bounded gains, and
appropriate conditional independence/filtration. The rollback guarantee after data-dependent
promotion additionally requires deployment feedback to satisfy its null conditional on promotion
history. Fresh independent forward deployment events suffice in this simulator; arbitrary
post-promotion dependence is not covered. If the label cap is exhausted, deterministic zero
increments cannot create an upward crossing, but the estimator is no longer an unbiased estimate
of the unobserved mean and power can only decrease.

## Comparators and endpoints

Compare `continue`, `unconditional_promote`, `promotion_only`, and `promotion_rollback` on the same
potential-outcome and query-random-number paths. Primary development endpoints are expected net
decision utility relative to continuing with the incumbent, promotion and rollback rates, and label
use under the hard cap. Report realized utility, false promotions on the two exact null controls,
false rollback on persistent benefit, and seed-paired utility contrasts as diagnostics. Do not treat
individual time points as independent replications. This small development grid is not a calibration
or confirmation set.

## Paired development grid

The initial sensitivity screen varies fixed query propensity `q ∈ {0.40, 0.80}` and total
label-budget fraction `b ∈ {0.20, 0.40}`. Every cell uses the same scenario outcome path and query
uniforms. This is development-only; the screen is descriptive and its small null counts are not
calibration. The primary selection diagnostic is the trade-off in paired expected net utility,
rollback effectiveness under harmful reversal, and labels consumed under the cap. If no setting
has an interpretable advantage, keep the simpler previously studied setting and report that result.

```powershell
uv run shiftlab-dive-feature-intervention-grid `
  --seeds 30 `
  --seed-offset 76102024 `
  --horizon 400 `
  --query-rates 0.40 0.80 `
  --budget-rates 0.20 0.40 `
  --device cuda `
  --output-dir outputs/feature_intervention_grid
```

The sensitivity command saves each child cell and a combined Parquet/CSV report and manifest.

## Single-cell reproduction command

```powershell
uv run shiftlab-dive-feature-intervention `
  --seeds 30 `
  --seed-offset 76102024 `
  --horizon 400 `
  --query-rate 0.80 `
  --budget-rate 0.40 `
  --device cuda `
  --output-dir outputs/feature_intervention_development
```

The command writes the actual Parquet/CSV metrics, paired contrasts, a manifest with source hashes
and environment information, and a Markdown report. It intentionally generates no figures.

## Required next steps

Before any claim, run disjoint scenario-specific null calibration for stationary and nuisance-shift
promotion and for least-favourable-boundary and persistent-benefit rollback. Use simultaneous one-sided exact binomial upper
bounds against the predeclared familywise 5% error target. Only after that gate passes, run a
disjoint confirmation on boundary-harm and harmful-reversal alternatives. Report conditional
rollback rates among promoted streams as well as unconditional rates; never pool development,
calibration, and confirmation seeds. Add delay, dependent outcomes, adaptive candidates, and
action-dependent feedback only as separate registered extensions.

The frozen calibration block uses 2,000 streams per cell from seed offset `77102024`, `H=400`,
`q=.80`, a 40% cap, total `alpha=.05`, and `k_promote=k_rollback=.05`. Its four cells are false
promotion under `stationary` and `benign_nuisance`, plus false rollback among promoted streams under
`rollback_boundary` and `persistent_benefit`. Bonferroni simultaneous one-sided exact
Clopper–Pearson upper limits use cell alpha `.05/4`; all four must be at most `.05`, and no cap may
be violated. Reproduction command:

```powershell
uv run shiftlab-dive-feature-intervention-calibrate `
  --seeds 2000 `
  --seed-offset 77102024 `
  --horizon 400 `
  --query-rate 0.80 `
  --budget-rate 0.40 `
  --device cuda `
  --output-dir outputs/feature_intervention_calibration_2000
```

The separate alternative confirmation has a disjoint seed block and is defined in
[`feature_intervention_confirmation_protocol.md`](feature_intervention_confirmation_protocol.md).
Its runner refuses to start unless this calibration manifest passes with matching parameters.
