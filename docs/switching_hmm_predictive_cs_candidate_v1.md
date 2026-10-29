# Candidate: delayed-HMM predictive confidence gate

**Registered development hypothesis, 2026-10-29.** This is not a validated novel method, not a
confirmatory protocol, and not evidence that the information structure is unoccupied. The goal is
to replace the impossible distribution-free current-value claim with a model-conditional guarantee
that allows latent regimes to reverse under a fixed recurrent HMM.

## Contract

The latent regime is a finite-state HMM with unknown but fixed parameter `theta` in a declared
finite model set `Theta`. Conditional paired loss differences `X_t` are bounded in `[-1,1]`, with
known emission family and transition structure indexed by `theta`. The hidden state and unqueried
losses are not observed. Queries are chosen predictably, at most one per event, under a pathwise
cap `B`; a queried `X_s` is released exactly `d>=1` events later. Querying does not affect the
outcome process. Decisions may use covariates and all labels released before the decision; no
unreleased label or latent state is available. Model parameters do not change with time, although
the hidden regime can transition and reverse benefit repeatedly. Safety is relative to the true
model's current predictive mean
`mu_t(theta) = E_theta[X_t | learner-observable history before the action]`.
This is explicitly model-conditional; arbitrary transition/emission drift is outside the claim.

## Anytime confidence-set lemma

Let `L_t(theta)` be the likelihood of the observed query/action/release history through time `t`
under model `theta`, including adaptive query selection and fixed-delay release. The policy's
randomization kernels are functions of observable history and are the same under every `theta`.
For a fixed prior `pi` with support on `Theta`, define

```text
E_t(theta) = sum_{theta' in Theta} pi(theta') L_t(theta') / L_t(theta)
C_t = {theta in Theta : E_t(theta) < 1/alpha}.
```

For the true parameter `theta*`, the likelihood-ratio terms are nonnegative likelihood-ratio
martingales under `theta*`; therefore `E_t(theta*)` is a nonnegative martingale with initial mean
one. Ville's inequality gives

```text
P_theta*(exists t : theta* not in C_t) <= alpha.
```

This remains true under predictable adaptive query times and delayed release when the likelihood
is the correct marginal likelihood of the released data under the known sampling policy. At each
release, HMM forward filtering marginalizes unqueried and still-pending outcomes; one must not
pretend pending outcomes are observed. If likelihood support fails, regularize the family or define
`E_t=+infinity` and stop safely.

## Predictive safety corollary

Permit promotion at time `t` only when

```text
min_{theta in C_t} mu_t(theta) > h.
```
If the confidence set is empty, do not promote. On the simultaneous-coverage event, every
permitted promotion has `mu_t(theta*)>h`; hence

```text
P_theta*(exists promotion t with mu_t(theta*) <= h) <= alpha.
```
The proof is containment: a false promotion while `theta* in C_t` contradicts the gate, so any
false promotion implies confidence-set failure. Unlike a historical benefit e-process, the gate
recomputes `mu_t(theta)` from the current released history at every decision; post-reversal labels
can lower the current forecast. The result controls conditional expected benefit under the true
fixed HMM parameter, not realized latent-state sign, HMM misspecification, or out-of-family change.
The hard query cap is enforced by any acquisition policy used with the gate; the lemma itself does
not establish acquisition efficiency or regret.

## Novelty audit and candidate mechanism boundary

Arnold et al., “Sequential model confidence sets,” JRSS B (published 2026), already provide
anytime-valid confidence sets for strongly/weakly superior forecasters using e-processes for
conditional expected loss differences. This closes generic “confidence set then model switch.”
Their stated object is a set of forecasters' relative performance, not a parameter confidence set
for an adaptively sampled, delayed hidden-state HMM followed by a current HMM-filter forecast; that
difference is a research question, not proof of novelty. See the [primary article](https://doi.org/10.1093/jrsssb/qkag066).
Likelihood-ratio confidence sequences, HMM filtering, and active sensing are established separately.
The corollary above is a standard Ville argument and is not claimed as a new theorem by itself.

The only possible method contribution left in this candidate is a query-allocation rule that uses
(1) the current HMM-filter forecast, (2) the confidence-set ambiguity over its sign, (3) remaining
query rights, (4) release delay and pending labels, and (5) promotion/rollback costs, with a proved
regret or approximation advantage over a matched safe calendar, sequential model-confidence-set
baseline, and the exact two-law oracle. Before implementation, audit active sensing and sequential
forecast comparison at source level and test whether this reduces to a standard finite-horizon
constrained POMDP or controlled-sensing policy. If it does, close it. Do not claim current-value
safety under misspecified or time-varying HMM parameters.

## Stop conditions and next gate

Do not run confirmatory simulations or real-data studies yet. G1 passes only if the query allocation
rule has a nontrivial theorem-level advantage beyond the confidence-set gate, active sensing, robust
FSC/POSG planning, and sequence-form oracle. Next: audit the exact delayed/adaptive likelihood
factorization (including query-policy terms), derive a small exact HMM confidence-set example, then
source-audit the proposed query score. The full research goal and G2-G5 remain open/held.
