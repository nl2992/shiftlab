# Candidate F: adaptive e-process bets for delayed switching control

**Date:** 2026-10-29. **Decision:** exact safety lemma is an established
supermartingale argument; adaptive betting control is source-matched prior art.
No implementation is authorized by this audit because no computational or
approximation theorem against the unrestricted two-law oracle is identified.

## Delayed-feedback safety lemma

Fix an integer delay `d>=1`. Before generating queried label `Y_s`, select
`beta_s in [0,1]` using only learner information then available, and retain it
with the pending request. Release all queried labels in source-time order at
their declared fixed delay. Set

`M_t = product_{s: s+d<=t, query_s=1} [1+beta_s(2Y_s-1)]`, with `M_0=1`.

Let `G_{s-}` be the full null history immediately before `Y_s` is generated,
including the request and any known stake. The null assumption is
`P(Y_s=1 | G_{s-}, query_s=1) <= 1/2`. Since `beta_s` is `G_{s-}`-measurable,
`E[1+beta_s(2Y_s-1)|G_{s-}] <= 1`. At the release of `Y_s` (event `s+d`),
the learner's information just before that release contains outcomes only
through source time `s-1`; fixed-delay ordering prevents labels generated after
`Y_s` from entering first. The previously accumulated capital and the pending
stake are measurable before `Y_s`. Taking conditional expectation first under
`G_{s-}` and then onto the learner's release filtration proves that `M_t` is a
nonnegative supermartingale under each null. Ville's inequality therefore
certifies the threshold event at `1/alpha`. This proof uses the predictable
stake and fixed ordered delay; arbitrary reordering of feedback would require a
new filtration audit.

## Candidate statement

At each query time `s`, choose a stake `beta_s in [0,1]` using only the
learner-visible history and attach it to that query. When its label `Y_s` is
released, multiply capital by

`1 + beta_s * (2*Y_s - 1)`.

Promote only after released-label capital reaches `1/alpha`. A planner could
optimize query, stake, promotion and switching decisions over an alternative-HMM
belief, pending outcomes/stakes, remaining query rights, deployment, time and
capital. Fixed delay preserves query order at release. Under each causal null,
`E[Y_s | full null history at generation] <= 1/2`; the stake is predictable at
query time. Conditional expectation and the tower property therefore give a
nonnegative supermartingale in the learner's ordered release filtration. Ville's
inequality gives `P_null(max capital >= 1/alpha) <= alpha`. The null may use its
full history and pending outcomes; the certificate does not ask the planner to
compress or predict that response.

This is a risk guarantee for the gated policy class. It gives no cost-loss bound
against the unrestricted causal-null optimum. Optimizing stakes and betting
thresholds can also create many distinct capital values; no favorable
`T,B,d` state bound has been proved. The existing fixed-stake `EProcessGatedPlanner`
already performs a finite wealth-state economic DP, exact alternative evaluation
and an independent full-history null-risk check.

## Source-matched audit

- Clerico et al., [*Time-sensitive anytime-valid testing*](https://arxiv.org/abs/2605.06521),
  formulate betting as a finite-horizon control problem, prove a Bellman
  representation in time and evidence/wealth for their setting, and show
  simple-vs-simple hard-deadline testing connects to Neyman–Pearson. Optimizing
  predictable bets over a time/wealth state is therefore established.
- Clerico, [*Sequential testing of conditionally constrained hypotheses*](https://arxiv.org/abs/2606.06769),
  proves a complete-class result: for the studied finite conditional-constraint
  hypotheses, any e-process is pointwise dominated by a predictable product of
  affine one-step e-variables. The conditional-mean null `E[Y|past] <= 1/2`
  falls directly in this broad family. Choosing affine stakes is not a novelty
  delta.
- Costed adaptive sampling is also established. Li et al., [*Sequential
  Hypothesis Test with Online Usage-Constrained Sensor Selection*](https://arxiv.org/abs/1601.06447),
  study finite/infinite-horizon adaptive sensor selection under usage and error
  constraints through Bayesian optimal stopping. Nitinawarat and Veeravalli,
  [*Controlled Sensing for Sequential Multihypothesis Testing with Controlled
  Markovian Observations and Non-Uniform Control Cost*](https://arxiv.org/abs/1310.1844),
  cover controlled Markov observations and control costs.

The ShiftLab-specific differences are the hidden Markov economic alternative,
first-promotion loss, hard pathwise query budget, switching/rollback costs,
delayed release, and the unrestricted causal-null response. Those differences
make the concrete model nonidentical to these sources, but the proposed DP is a
direct composition of established betting control and active-sensing POMDP
planning. No argument shows a value bound against `V*`, a compact state bound,
or advantage over the exact decomposed solver. That is not enough to pass G1 or
justify a compute experiment under the working plan.

## Decision

Do not implement adaptive stake optimization as the next lead. Retain the fixed
stake e-process planner as a sequential-testing baseline. The exact delayed
supermartingale lemma may be useful as a general verifier fact, but its
fixed-delay filtration condition and its relation to all risk event timings
would need a separate formal proof before it is used as a standalone result.
Continue candidate search for an implicit optimizer or a policy class with a
nonvacuous value guarantee against the full two-law oracle. No real-data or
holdout access is authorized by this audit.
