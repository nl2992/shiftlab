# Temporal context schedule × query-policy development protocol

**Status:** frozen exploratory development design. This protocol authorizes no calibration,
confirmation, safety, or novelty claim.

## Question

Does the previously observed advantage of variance-weighted predictable querying over uniform
querying persist when the prevalence of a learner-visible context changes gradually or recurs over
time? The primary descriptive comparison is the eventwise scout under variance-weighted querying
minus the same scout under uniform querying. Secondary comparisons benchmark each query policy's
eventwise scout against minimum-propensity scouting, pooled rank, and nested context-volume rank.

## Registered design

- Four context-prevalence schedules: `gradual_up`, `gradual_down`, `recurring_low_first`, and
  `recurring_high_first`.
- Signal strengths `0`, `0.05`, and `0.10`; proxy errors `0` and `0.25`; hard label-budget rates
  `0.20` and `0.40`.
- Matched query policies: `uniform` and predictable `variance`. Use shared query uniforms for
  common random numbers across these policies.
- Four allocation methods: pooled rank, nested context-volume rank, minimum-propensity scout, and
  eventwise-propensity scout. Keep all monitor, estimator, costs, split, horizon and other generator
  settings at the existing temporal-development defaults.
- Full development uses 60 matched seed clusters, beginning at seed `21420000` and ending at
  `21420059`, with `n=3200`, `d=16`, CUDA when available, and 10,000 seed-cluster bootstrap draws.
- The grid has 48 profile/cap cells per query policy (32 positive-signal, 16 zero-signal), 96
  query-policy/profile/cap cells total, and 23,040 stream-method rows. The seven registered
  descriptive contrasts are three within-policy scout comparisons for each query policy and one
  variance-versus-uniform eventwise comparison.

## Endpoints and analysis

For each positive-signal profile/cap cell, compare evaluator-known expected postpromotion net
decision gain, equally weighting cells and pairing by seed. Report cell-level outcomes, promotion
and harmful-promotion rates, queried-label counts, and cap/support checks. Use the existing
seed-cluster percentile bootstrap for descriptive 95% intervals. These intervals are exploratory:
the grid has not been independently calibrated or confirmed, and selection across this and earlier
development results is not accounted for.

The simulator's oracle parameters and future utility are evaluator-only. They must not enter model
features, query propensities, allocation rules, or monitoring evidence. The query policy must be
predictable from the permitted pre-query history. Verify positive propensity support, exact row
counts and keys, zero-signal expected-gain nonpositivity, finite outcomes, and realized hard label
caps before publishing artifacts.

## Interpretation limits

This is a development comparison on synthetic gradual and recurring prevalence schedules. It does
not establish false-alarm control for either query policy under these temporal schedules; the
existing calibration applies to its separately registered immediate-feedback Markov family. It
also does not validate delayed or informative labels, adaptive query probabilities based on
certification evidence, or real-data utility. Any candidate selected from this grid needs a new
frozen null calibration and a disjoint positive-signal confirmation. No algorithmic novelty claim
is authorized.
