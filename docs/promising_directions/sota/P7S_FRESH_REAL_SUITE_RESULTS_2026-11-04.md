# P7s fresh-stream suite results — 2026-11-04

## Decision

**SOTA gate not met. Close the current P7s parameterization as a candidate for beating the
published suite.** It is cheaper than Gated Deployment on all five streams, but the lower-cost
Model Picker adapter beats it on four and the Model Selector adapter beats it on household power.
The best suite method is cheaper than P7s on every stream. The result exposes an efficiency gap
for P7s; it does not validate a new method.

## Run and verification

This is an exploratory replay on the five chronologically held out UCI streams from the SOTA sprint.
The other sprint methods had already used these outcomes, so this is **not an untouched
confirmation**. It uses the actual frozen-model predictions and binary labels, not synthetic XOR or
zero labels. Exact elementwise checks verify that `prediction != label` reproduces each frozen
incumbent/challenger loss array and that episode starts match.

- Contract: `T=2000`, `B=200`, query price `.05`, switch price `5`, `alpha=.05`, `eps=0`,
  `p_min=.05`; 20 query seeds per episode, seed base `20261101`.
- Registered delays: metro 24, beijing_pm25 24, bike_hour 24, appliances 144, household_power 144.
- Suite: Gated Deployment, DISCERN-style stop, SMCS, Model Picker, Model Selector, Online LLM
  Picker, Xu acquisition-only, and P7s. Feature-dependent comparators requiring unavailable
  covariates or nuisance fits remain explicitly not-run.
- All five entries report an empty simulator validation-problem list. The corrected run output is
  [`vs_sota_results_cached.json`](../../../outputs/p7s_fresh_real_suite_screen_corrected/vs_sota_results_cached.json);
  its source/input checksums are in the adjacent `provenance.json`.
- Intervals are 4,000-resample percentile bootstraps over episode-level mean paired differences.
  They are descriptive and optimistic because each dataset is a single time series with consecutive
  episodes. The query seeds are averaged within episode, not treated as independent data episodes.

## Primary cost comparison

`Delta = P7s net cost − best method's net cost`; positive favors the comparator. Values are mean
net cost with mean requested labels in parentheses.

| Stream | Episodes | P7s | Best suite method | Delta [95% bootstrap interval] |
|---|---:|---:|---|---:|
| metro | 16 | 145.48 (63.7) | Model Picker, 109.84 (29.8) | +35.64 [+33.20, +38.48] |
| beijing_pm25 | 14 | 583.93 (148.0) | Model Picker, 553.78 (68.1) | +30.15 [+4.03, +59.21] |
| bike_hour | 6 | 285.65 (89.2) | Model Picker, 248.73 (46.4) | +36.92 [+30.73, +44.49] |
| appliances | 6 | 674.84 (173.9) | Model Picker, 599.46 (107.8) | +75.38 [+19.13, +121.17] |
| household_power | 20 | 555.43 (158.6) | Model Selector, 530.13 (197.6) | +25.30 [+3.36, +44.53] |

The 6-episode datasets have especially weak episode-level resolution. The intervals are not
population-level guarantees.

## Comparator pattern

- P7s is cheaper than Gated Deployment on all five streams; its cost difference ranges from
  `−31.65` to `−157.32` with the recorded bootstrap interval below zero in each case.
- P7s is more expensive than Model Picker on four streams and more expensive than Model Selector
  on household_power. It requests more labels than Model Picker in every stream, while also
  incurring greater prediction loss. This is the clearest actionable diagnosis: P7s does not
  convert its paired certificate into sufficiently early or economical deployment on these strong
  challenger episodes.
- P7s has lower mean cost than Xu acquisition-only on four streams and higher mean cost on
  household_power; only the metro interval excludes zero. Its mean cost exceeds SMCS on all five,
  but the intervals overlap zero on metro, beijing_pm25, bike_hour, and household_power.

This ranking is specific to the reported adapters and imposed economic contract. Model Picker,
Model Selector, and Online LLM Picker are selection methods without P7s's anytime promotion
certificate, so their lower net cost does not establish equivalent false-promotion safety.

## Data and cost limits

The UCI target labels and model predictions are authentic to the frozen task build, but outcome
release delays (one day in events) and query/switch prices are imposed. No causal deployment utility
or production label-ingestion timing is established. All five streams were used by other SOTA sprint
methods before this P7s comparison. The run therefore closes the current exposed-screen question;
it does not pass the full SOTA gate.

## Next research decision

Do not tune the P7s thresholds on these exposed streams. The next worthwhile question is whether a
fast active selector can be used as a *proposal mechanism* while a same-contract sequential safety
gate controls deployment, with shared queried labels, a pathwise cap, delayed release, and an
explicit rollback rule. Before coding, source-audit this composition against SMCS, anytime policy
identification, and gated deployment; then register a fresh task and compare the strongest valid
selector under the same safety event. A wrapper alone is not a novelty claim.
