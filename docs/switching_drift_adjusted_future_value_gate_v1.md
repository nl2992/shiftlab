# Drift-adjusted future-value gate under a hard query cap

**Date:** 2026-11-04. **Status:** conditional theorem, closed for the repository's default HMM
model; not a method or novelty claim. The result below gives an anytime-valid finite-horizon
safety gate under a pathwise drift envelope. The concrete HMM counterexample in the limitations
section makes that assumption too costly for the current target.

## Contract

Fix one incumbent/challenger pair and let `Z_t in [-1,1]` be its paired incremental utility at
time `t` (positive favors the challenger). Let `F_t` be the full history just before the round-`t`
outcome is generated, including all labels released by the decision at `t`, and let
`mu_t = E[Z_t | F_t]`. Assume:

1. `|mu_{t+1} - mu_t| <= v` almost surely for every `t`;
2. query decisions `Q_t in {0,1}` are predictable, at most one outcome can be queried per round,
   and `sum_t Q_t <= B` on every path;
3. a query at `s` is observed no later than `s+d`, with deterministic delay bound `d`;
4. switching at time `t` changes the action for a declared `h`-round evaluation horizon and costs
   `k >= 0`.

At decision time `t`, the round-`t` outcome has not yet been generated. The future value at `t`,
conditional on the full history, is

```text
U_t = E[sum_{j=0}^{h-1} Z_{t+j} | F_t] - k.
```

The target is the familywise event that a switch is made at some time with `U_t <= 0`. This is a
single frozen pair. Multiple candidate versions need an additional error allocation.

## Proposition: sliding-window lower bound for current mean

For each eligible decision time `t <= T-h+1`, use queried outcomes from the last `W` issue times
that are known by `t` (take `W >= d+1`):

```text
S_t = {s : max(1,t-W+1) <= s <= t-d, Q_s=1},   n_t = |S_t|.
```

For `1 <= n_t <= B`, define

```text
r(n) = sqrt(8 log(T B / alpha) / n)
L_t = average_{s in S_t}(Z_s) - r(n_t) - v W.
```

With probability at least `1-alpha`, simultaneously at every `t` with `n_t > 0`,
`L_t <= mu_t`.

*Proof.* Fix an endpoint `t` and write its deterministic window as `[a_t,b_t]`, where
`a_t=max(1,t-W+1)` and `b_t=t-d`. Let `tau_j` be the `j`th queried issue time in that interval,
when it exists. The query decisions are predictable, so these are sampled stopping times. The
residuals `D_j = Z_{tau_j} - mu_{tau_j}` are bounded martingale differences in the sampled
query-index filtration, with `D_j in [-2,2]`. Equivalently, absent increments may be padded by
zero. Hoeffding's martingale inequality gives, for every fixed `m <= B`,

```text
P(sum_{j=1}^m D_j < -sqrt(8 m log(T B / alpha))) <= alpha/(T B).
```

For each fixed `m`, the event `{n_t=m, sum_{j<=m} D_j < -x}` is contained in
`{tau_m exists, sum_{j<=m} D_j < -x}`. Apply the concentration bound to the latter event; do not
condition on the random event `n_t=m`. A union bound over `m=1,...,B` and `t=1,...,T` gives the
simultaneous sample-mean bound. The drift envelope implies
`mu_s <= mu_t + v(t-s) <= mu_t+vW` for every `s in S_t`, so the average queried conditional mean
is at most `mu_t+vW`. Rearranging the sample-mean bound proves `L_t <= mu_t`. QED.

The delayed labels used in `S_t` are all available by `t` because `s <= t-d`. The pathwise cap
enters through `n_t <= B`; query choices may depend on earlier released labels.

## Corollary: anytime false-promotion control for finite-horizon value

The drift envelope also gives, by iterated expectation from `F_t`,

```text
E[sum_{j=0}^{h-1} Z_{t+j} | F_t] >= h mu_t - v h(h-1)/2.
```

Thus define the observable lower bound

```text
U_lower(t) = h L_t - v h(h-1)/2 - k.
```

Promoting only when `n_t > 0` and `U_lower(t) > 0` guarantees

```text
P(exists t <= T-h+1: promote at t and U_t <= 0) <= alpha.
```

On the simultaneous coverage event, every promotion has `U_t >= U_lower(t) > 0`; its complement
has probability at most `alpha`. This statement tolerates reversals in the utility sequence,
provided the pathwise drift bound holds. It is a value-based guarantee, distinct from global-null
false-promotion control.

## What this does and does not establish

- This supplies a candidate resolution of the project note's delay-adjusted future-value
  certificate, with predictable adaptive sampling and a hard cap. It does not optimize which
  queries to buy, query costs, rollback, or repeated candidate selection.
- The gate can be vacuous. Its radius is
  `sqrt(8 log(TB/alpha)/n_t) + vW`, and labels newer than `t-d` are unavailable. For a
  deterministic schedule with exactly `n` queried outcomes in the window, define the utility
  threshold `c = k/h + v(h-1)/2`. If `mu_t >= c+Delta`, a sufficient
  high-probability promotion condition is
  `Delta > 2vW + sqrt(8 log(TB/alpha)/n) + sqrt(8 log(1/beta)/n)` for power at least `1-beta`.
  The two drift terms arise because old outcomes can be lower than the current mean and the lower
  confidence bound must also subtract the allowed age. For a schedule querying every eligible
  time in the window, `n=min(B,W-d)` (when `W<=T`); its sufficient margin is minimized over
  integer `W` in `[d+1,T]`. For illustration, at `(T,B,d,v,alpha,beta)=(200,40,2,.001,.05,.1)`,
  this Hoeffding condition requires `Delta>2.31` even at its best window `(W,n)=(42,40)`; since
  `Z` lies in `[-1,1]`, alternatives with smaller mean separation cannot be certified by this
  bound. At `(1000,100,5,.0005,.05,.1)` the required margin is `1.61`. These calculations expose
  severe conservatism at moderate budgets; they are diagnostic algebra, not efficacy evidence.
  A matched lower bound and a useful budget/delay/power frontier are still needed.
- **Variance-known strengthening (development hypothesis).** If every eligible queried residual has
  predictable conditional variance `Var(Z_s | F_s) <= sigma2`, the same endpoint/count union can
  use a one-sided Freedman radius
  `r_F(n,L)=sqrt(2 sigma2 L/n) + 2L/(3n)`, `L=log(TB/alpha)`, for the sample-mean error. Its
  fixed-schedule power margin replaces the Hoeffding radii above by
  `2vW + r_F(n,log(TB/alpha)) + r_F(n,log(1/beta))`. This uses a known conditional variance
  envelope; plugging in an empirical variance is not justified by this argument. At
  `(T,B,d,v,alpha,beta,sigma2)=(200,40,2,.001,.05,.1,.1)`, the optimized sufficient margin is
  `0.674` at `(W,n)=(42,40)`, versus `2.31` under Hoeffding. At `(1000,100,5,.0005,.05,.1,.1)`,
  it is `0.455` at `(105,100)`, versus `1.61`. These are analytical screens under an assumed
  variance envelope, not empirical results. They suggest a possible useful regime but add a strong
  assumption and use a standard concentration inequality; no novelty follows.
- The assumptions are materially stronger than the hidden HMM setting: the predictable
  conditional means must satisfy a pathwise Lipschitz bound under the full outcome filtration.
  A Markov latent state can violate this at a state transition. For the repository's default
  `RegimeModel` (switch probabilities `0.1`, emissions `P(Y=1|S=0)=.25`,
  `P(Y=1|S=1)=.75`), take bounded utility `Z=2Y-1`. Conditional on the full state history,
  `mu_t` is `-.5` in state 0 and `+.5` in state 1, so a regime switch changes it by 1 with
  probability .1. A pathwise envelope therefore needs `v>=1`; even at the minimum eligible window
  `W>=d+1>=2`, the `2vW` power margin already exceeds the full utility range. This concrete
  HMM-style stream makes the candidate vacuous under its required assumption. It is not
  established that a filter-level or marginal drift assumption preserves the guarantee.
- The proof uses a standard bounded-martingale concentration argument. Anytime-valid confidence
  sequences and test-supermartingale methods are established tools; see Howard et al.,
  [*Time-uniform, nonparametric, nonasymptotic confidence sequences*](https://arxiv.org/abs/1810.08240).
  A 2026 preprint on [sequential tradeability testing](https://ssrn.com/abstract=6922558) also
  studies economic sequential activation with an implementation hurdle. These precedents make
  the gate itself a weak novelty candidate. The remaining possible delta is a sharp, useful
  acquisition/power result under simultaneous delay, hard-cap accounting, and reversible
  switching, compared with episode-wise group-sequential control and the source-matched economic
  adoption rules.

## Kill/reopen gates

Do not implement a broad simulator or claim novelty until all are resolved:

1. Independently verify the martingale-indexing proof for adaptive query times, delayed release,
   and the random queried sample count. In particular, check the query-index filtration and the
   union over endpoints and counts.
2. Show a power/usefulness region with real values of `(T,B,d,h,v,k,alpha)` where the gate beats
   the strongest episode-wise sequential-design composition under identical query and switching
   costs; report vacuity boundaries analytically.
3. Establish whether a justified data source supports the pathwise drift condition. If only a
   latent-state or expected drift condition is available, rederive the coverage result or kill the
   candidate.
4. Audit the 2026 tradeability preprint and relevant nonstationary confidence-sequence sources at
   theorem level. Any novelty claim must come from an advantage theorem, not this concentration
   corollary or the addition of a cost threshold.

**Current decision:** close as a method lead for the repository's default HMM. Retain the
conditional theorem only as a reference for a future stream with a justified pathwise drift and
variance envelope. It is not an algorithm lead, SOTA improvement, or authorization for an
empirical efficacy screen.
