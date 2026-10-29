# Paired-copy compact risk state: a useful counterexample, not a new method

**Date:** 2026-10-29. **Status:** exact growing-family screen with a value bound; novelty rejected.

## Contract

There are `m` adjacent pairs of queried binary labels, requests at events `1,...,2m`, fixed delay
one, and hard request budget `B=2m`. The learner receives each label at the start of the next
round. Its null guarantee is the full-history causal condition

`P(Y_t=1 | all earlier outcomes, actions, and requests) <= 1/2`.

Under the economic alternative, draw independent `X_i ~ Bernoulli(1/2)` and emit
`Y_(2i-1)=Y_(2i)=X_i`. Before the final pair is released, both deployed models have equal expected
loss. After release, the challenger has per-round advantage one for `H` rounds. Query cost is `c`
per request and promotion costs `k`. This is a finite-state hidden Markov source (pair phase and
the current bit are hidden states); it is a synthetic structural family, not a finance-data model.

## Exact test and causal-risk proof

Let `Z_i = 1{Y_(2i-1)=Y_(2i)=1}`. Promote at the first permitted decision after the final label
release exactly when `sum_i Z_i >= h`. Under every history-adaptive causal null,

`P(Z_i=1 | full history before pair i) <= (1/2)(1/2)=1/4`.

Sequential common-uniform coupling therefore upper-bounds the count by `Binomial(m,1/4)` in
stochastic order. The bound is exact: IID `Bernoulli(1/2)` labels are an admissible null and make
the `Z_i` IID `Bernoulli(1/4)`. Thus worst-case any-promotion risk is exactly
`P(Binomial(m,1/4) >= h)`. Under the alternative, `Z_i=X_i`, so promotion probability is exactly
`P(Binomial(m,1/2) >= h)`.

The controller stores a count capped at `h`, one bit while waiting for the second label in a pair,
and terminal state. Public time supplies pair phase; a simple upper bound on its states is
`4(m+1)+2`. The pending-feedback queue is also constant-sized for delay one. The controller never
uses unreleased labels. This is an exact policy-sufficient statistic for this particular event and
alternative value, not for the unrestricted two-law switching game.

More generally, a threshold `h` between `m/4` and `m/2` gives Hoeffding bounds
`risk <= exp(-2m(h/m-1/4)^2)` and `1-power <= exp(-2m(1/2-h/m)^2)`. Taking `h` near `3m/8`
therefore gives both errors exponentially small in `m`, with linear state count and a pathwise
budget of `2m` labels. The result supplies a compact risk-preserving construction on a growing
family; it defeats a blanket memory-lower-bound argument based only on expanding the horizon.

## Economic-value bound against the full-history oracle

No policy can earn more than `H` gross alternative utility over the post-release window, and all
query and switch charges are nonnegative. Hence the full-history safe oracle value is at most `H`.
The compact policy obtains

`V_compact = H * P(Binomial(m,1/2) >= h) - k * P(Binomial(m,1/2) >= h) - 2mc`.

Consequently its gap below the unrestricted full-history oracle is at most

`H * (1-power) + k*power + 2mc`.

This is a defensible but deliberately coarse comparison bound. It does not show that the compact
policy is globally optimal, nor that the bound is useful under short horizons or large label cost.
For a sequence with fixed `c,k,alpha`, `m=O(log(1/epsilon))`, target power `1-epsilon`, and
`H` growing faster than `m/epsilon`, the relative gap vanishes while controller state count is
polynomial in `log(1/epsilon)`.

## Exact screen

The checker `scripts/screen_switching_paired_copy_compact.py` selects the smallest `m`, then the
smallest `h`, attaining `alpha=1/10` and alternative power at least `99/100`. It uses exact
rational tails and records code hash and outputs in
`outputs/switching_paired_copy_compact_screen_v1/results.json`:

- `m=50`, `h=17`, and pathwise budget `B=100`;
- worst causal-null risk `0.09830732478526508` (exact fraction in the results file);
- alternative promotion probability `0.992326661083685`;
- at `c=1/100`, `k=1/10`, and `H=10,000`, net improvement is about `9,922.2`;
- the full-history oracle is at most `10,000`, so the relative oracle-gap upper bound is about
  `0.0077833`;
- the controller uses at most 206 states (8 bits under binary state encoding).

These numbers are an exact synthetic screen, not empirical efficacy evidence or a new baseline
win. The bound compares with an upper bound on the oracle, not its computed exact value.

## Novelty decision

The test reduces the queried tape to bounded Bernoulli trials with null success probability at
most `1/4` and alternative success probability `1/2`; its threshold is ordinary fixed-sample
hypothesis testing. Compact counters, delayed sequential testing, and the robust null guarantee
are established ingredients, including the adaptive composite-null supermartingale prior audited
in [`switching_robust_sequential_testing_prior_audit_v1.md`](switching_robust_sequential_testing_prior_audit_v1.md).
Therefore this construction closes the proposed *generic growing-memory lower-bound route* for
this family, but it is not a methodological contribution for the paper. A future lower-bound
family must rule out such compact event statistics and compare against the strongest safe test,
not merely the full-tape rule.

Historical promotion evidence still does not certify current benefit after an unobserved reversal.
This instance has a declared post-release reward window and no reversal; it makes no rollback claim.
