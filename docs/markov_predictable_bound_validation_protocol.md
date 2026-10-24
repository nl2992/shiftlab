# Markov volatility validation protocol for history-predictable query bounds

**Status:** frozen before validation, 2026-10-24. The independent benchmark used seeds 27104027–27108026. This extension begins at seed `27108027` and uses 4,000 new stream IDs (27108027–27112026). Do not tune the model or thresholds after opening these results.

## Question

Does the registered history-only query policy and predictable PPI support bound retain calibration and its detection-versus-label behavior when contexts and cost magnitudes are dependent through a persistent latent volatility regime, while the required marginal past-conditional-mean null remains true?

This is a validity-boundary test of the standard supermartingale construction, not a new algorithm or proof. The monitor and query arms, q floor, stake mixture, alpha, horizon, budget, event onset, and primary retention rule are exactly those of the independent confirmation. The primary comparison is q-min 0.05 evidence-directed querying with `B_t=M(2/q_t-1)` versus the same q-min query design with fixed `B=M(2/q_min-1)`. Uniform q=0.20 remains an established reference.

## Dependent data-generating process

Each stream has a latent state `S_t in {0,1}` that starts in its stationary distribution `(0.5,0.5)` and flips with probability 0.05 per event. Conditional on the state, current context is sampled independently, with `P(high cost | S=0)=0.5` and `P(high cost | S=1)=0.25`. The corresponding current paired-cost conditional means are:

| State | P(low cost) | E[Z | low cost, state] | P(high cost) | E[Z | high cost, state] | E[Z | state] | E[cost squared | state] |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.50 | -0.12 | 0.50 | +0.12 | 0 | 13 |
| 1 | 0.75 | -0.10 | 0.25 | +0.30 | 0 | 7 |

With false-positive and false-negative costs 1 and 5, these means correspond to outcome probabilities `P(Y=1 | low,S=0)=0.56`, `P(Y=1 | high,S=0)=0.488`, `P(Y=1 | low,S=1)=0.55`, and `P(Y=1 | high,S=1)=0.47`. The statewise marginal mean is exactly zero. Since each state has zero conditional mean, for the full past filtration `E[Z_t | F_(t-1)] = 0`, even though context prevalence and cost-square moments persist in a Markov regime. The generator validates the statewise null algebra before simulating.

The strict-negative control changes the high-cost outcome probability starting at zero-based event index 1,200 by `-(-0.20)/3.75` (an increase), yielding state-conditional means -0.2667 and -0.1333; both are nonpositive. Harm alternatives decrease high-cost outcome probability by `delta/3.75`, for `delta in {0.04,0.20,0.40,0.60}`. Under stationary state mass 0.5/0.5, the corresponding aggregate expected excess costs are exactly the registered delta values. The per-state harm increments per unit delta are 4/3 and 2/3.

The learner's two-stratum proxy is estimated from 512 independent training events drawn from the same stationary Markov-regime model. At test time it sees only the current cost context, queried labels, and prior monitor history. Latent state and conditional probabilities are evaluator/generator-only. Query coins are independent of states, contexts, outcomes, and training samples.

## Locked size, analysis and retention rule

Use 4,000 paired streams per scenario, 2,400 events, alpha 0.05, a 480-label cap, and the disjoint seed block above. There are two nonpositive-mean calibration controls crossed with three arms (six cells); report exact one-sided Clopper–Pearson upper limits using Bonferroni per-cell alpha `0.05/6`. Calibration passes only when every upper limit is no more than 0.05.

The primary harm estimand is the equal-weight mean over the four dose levels of the paired, stream-level post-onset detection difference (predictable minus fixed). Resample whole stream IDs 10,000 times. Retain only if the two-sided 95% paired-bootstrap lower limit exceeds +0.02, the 95% upper limit for mean label-count difference is at most zero, and every simultaneous calibration upper limit is at most 0.05. Pre-onset alarms remain competing outcomes. Report dose-specific detection, pre-onset alarms, delay, labels, processed events, and evaluator-known exposure as secondary outcomes with paired bootstrap intervals.

For the dependent alternatives, evaluator-known exposure sums the state-conditional expected paired-cost increase for each processed post-onset event through alarm or stopping. This conditions on the evaluator's latent state path and assumes mitigation follows the first alarm. It is not realized loss or empirically prevented harm.

## Limits

The test covers this two-state Markov-volatility martingale-null construction, immediate randomized labels, a frozen action pair, and history-only q. It does not establish validity for arbitrary serial dependence, non-martingale conditional-mean violations, delayed or informative feedback, changing policies, repeated candidate selection, or interventions that affect outcomes. A failure rejects the registered candidate for this dependent DGP; do not retune on this seed block. A pass supports only the stated dependent synthetic process and the standard bounded-factor argument.

Research figures require PaperBanana. If it is unavailable, report that limitation rather than substituting another figure generator.

## Reproduction

```powershell
uv run python scripts/validate_markov_predictable_query_bounds.py --streams 4000 --seed 27108027 --device cuda --output outputs/markov_predictable_bound_validation
uv run pytest tests/test_markov_predictable_query_bounds.py -q
```
