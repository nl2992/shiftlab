# Regime-warning and incumbent-abstention comparison

## Question and scope

This exploratory benchmark asks whether a learner-visible feature that warns of a regime change
can make a previously promoted candidate less harmful than (a) fixed candidate coverage and
(b) the existing promotion/rollback gate. The warning is a covariate available at prediction time;
it is not the evaluator's scenario label. This is a controlled synthetic comparator study, not a
novel algorithm, a calibrated intervention guarantee, or a real-data claim.

The promotion/rollback baseline uses queried paired costs with query probability 0.80, a pathwise
40% label cap across both stages, `alpha=0.05`, promotion and rollback costs 0.05, and label price
0.01. The warning and fixed-coverage baselines are post-promotion decision rules: they pay the same
promotion cost, then choose between the candidate and incumbent at each deployment event. The
warning rule also pays 0.0005 cost units per deployment event for access to its feature. It uses no
outcome labels. These policies use different information and query resources; compare their net
utility and resource use jointly rather than calling them matched-information tests.

## Warning feature and policies

The dedicated warning feature is `Z_t`, the eighth feature supplied with the request. Outside the
harmful-adaptation deployment phase, `Z_t ~ N(0,1)`. During harmful adaptation it follows
`N(delta,1)`, where `delta` is varied over `{0, 0.5, 1, 2}`. Other features and potential outcome
paths are shared across the delta grid. The earlier benign-nuisance shift is removed from this
dedicated coordinate, so its registered warning null remains standard normal. The regime change
and `delta` are evaluator-side parameters; the rule sees only the realized `Z_t`.

For a predeclared conditional per-read warning probability `r`, set `c_r = Phi^{-1}(1-r)` and use
the incumbent if `Z_t > c_r`; otherwise use the candidate. The read is independently missing with
probability `m`; missingness is MCAR in this registered grid, and a missing read triggers fallback.
Under no warning signal, candidate coverage is `(1-m)(1-r)`. Under the shift it is
`(1-m)Phi(c_r-delta)`. Here `r` is conditional on a feature being available. The unconditional
per-event warning probability under the null is `(1-m)r`, not a run-level familywise error rate.
Repeated warnings are expected over the horizon and their opportunity cost is charged in net
utility. Sensor acquisition cost is charged on every attempted read, including missing reads.

For the specified Gaussian location-shift alternative and fixed per-event warning rate, this
one-sided threshold is the Neyman-Pearson most-powerful test: the log likelihood ratio is
`delta*Z - delta^2/2`, which is increasing in `Z` for `delta > 0`. This optimality is local to
detecting the registered feature shift; it does not imply optimal decision utility, robust
performance under an unknown shift, or validity for a learned warning feature.

Fixed-coverage comparators deploy the candidate with a predeclared independent Bernoulli mixture
rate in `{0.25, 0.50, 0.75}` and fall back to the incumbent otherwise. They have no outcome-label
cost. Their candidate coverage is a randomized policy mixture, not a feature-selected subgroup.
The existing sequential gate is included on the same generated outcomes and query-random-number
paths. Evaluator expected gain is used only to score expected utility, never as a policy input.

An additional `matched_coverage_oracle` row randomizes candidate use at the warning rule's exact
theoretical coverage. It is an evaluator-only diagnostic: computing that rate requires the
registered warning distribution. It isolates any value of the feature beyond reducing candidate
exposure and is not an implementable learner policy. In this DGP, warning and missingness are
independent of the paired decision gain conditional on the scenario. Thus, at equal candidate
coverage, both rules have the same expected decision gain; the warning rule is lower by exactly
`H*k_warning` when the feature has positive acquisition cost. The runner asserts this identity for
every generated grid cell. A benefit beyond matched coverage requires warning features that
predict heterogeneous gains among events, which this benchmark intentionally does not include.

For a scenario with evaluator mean candidate gain `g_t`, the warning rule has expected net utility
`sum_t g_t (1-m) Phi(c_r-delta) - k_promote - H*k_warning`, where `k_promote=0.05`,
`m` is the MCAR missingness rate, and `k_warning` is the varied acquisition cost per attempted
event. Under the null `delta=0`, candidate coverage is `(1-m)(1-r)`. This identity gives an
analytic check on the simulated coverage and utility calculations.

## Frozen development grid

The CUDA screen uses 500 paired streams per scenario, `H=400` shadow and deployment events,
signal strengths `{0,0.5,1,2}`, conditional warning targets `{0.01,0.05,0.10}`, MCAR missingness
`{0,0.10,0.30}`, sensor event costs `{0,0.0005,0.002}`, fixed coverage `{0.25,0.50,0.75}`, and the
four existing deployment baselines. Same-seed potential costs, warning noise, and missingness draws
are reused across the grid. Contrasts use a seed-cluster bootstrap with 2,000 replicates. This block
is for development and method comparison only. Any threshold or policy selected from this grid
requires a new registered calibration/confirmation block.

Reproduce with:

```powershell
uv run shiftlab-dive-regime-warning-grid `
  --seeds 500 `
  --seed-offset 79102024 `
  --horizon 400 `
  --signal-strengths 0 0.5 1 2 `
  --warning-false-positive-rates 0.01 0.05 0.10 `
  --warning-missingness-rates 0 0.10 0.30 `
  --warning-event-costs 0 0.0005 0.002 `
  --device cuda `
  --bootstrap-replicates 2000 `
  --output-dir outputs/regime_warning_grid_500
```

The manifest records the source hashes, resolved environment, metric checksum, grid, and
cap-verification status. No figure is included; research visuals must use PaperBanana.
