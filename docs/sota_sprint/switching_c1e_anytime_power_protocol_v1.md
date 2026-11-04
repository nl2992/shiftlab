# C1-E anytime promotion-power screen — protocol v1

**Status:** frozen finite-cell development screen. Not a method, SOTA, or novelty claim.
**Question:** does the small adaptive-sensing information gain from the C1-E KL screen survive
when the objective is actual first-promotion power under an anytime false-promotion threshold?

## Contract

- Hidden state is binary, initially stationary `(1/2, 1/2)` under both hypotheses.
- Alternative transition matrix has switch probability `0.3`; null transition matrix has switch
  probability `0.1`; transitions are symmetric.
- Emission probabilities are shared: `P(+ | state 0)=0.8`, `P(+ | state 1)=0.2`.
- There are `T=20` event times, one-step label release, and pathwise query cap `B=4`.
- At each event, the learner may query or skip using only previously released queried labels.
  A queried label is released before the next event's decision. There is no query value after the
  horizon; the last event's label is evaluated at the horizon boundary.
- Query actions do not alter hidden state or emissions.
- A promotion occurs at the first released-observation history for which the simple-hypothesis
  likelihood ratio `P_alt(history)/P_null(history)` is at least `1/alpha`. Because querying is
  predictable and the models are fixed, this likelihood ratio is a nonnegative null martingale;
  Ville's inequality gives false-promotion probability at most `alpha` for every policy.

## Outcomes and comparisons

Primary estimand is exact alternative probability of crossing by the horizon. Compare:

1. The best fixed calendar using at most four requests.
2. The best single contiguous burst using at most four requests.
3. The exact belief-state dynamic program maximizing alternative crossing probability under the
   same threshold, deadline, delay, and cap.

For each selected policy, also compute its exact null crossing probability, expected query count
under the alternative, and the policy decisions on reachable alternative histories. The DP is an
exact finite-cell oracle; the study does not claim a scalable implementation, strict oracle gap,
or theorem. It does not include repeated reversals, model misspecification, or a robust
history-adaptive composite null.

Run alpha values `{0.05, 0.10, 0.20}` as a fixed sensitivity panel. Do not select alpha from results.
Do not tune model constants or expand the horizon/cap after seeing outcomes.

## Advance / stop interpretation

- If the adaptive power gain is negligible or is captured by a simple burst/calendar, close this
  particular mechanism as an empirical lead.
- If material, retain it only as a finite-cell diagnostic. Further work would still require a
  tractable policy with a certified oracle gap and comparison to active Markov hypothesis testing,
  finite-budget sequential testing, and the strongest scalable matched composition.
- No novelty, SOTA, or broad validity claim follows from a positive cell.

## Prior-art boundary

Controlled sensing for multihypothesis testing with Markovian observations is established; see
[Nitinawarat, Atia & Veeravalli (2013)](https://arxiv.org/abs/1310.1844). Finite-budget active
testing and exact belief-state sensing are also required comparators. This screen asks only whether
the previously observed KL gap changes a finite-sample anytime promotion decision under this
specific delay/cap cell.
