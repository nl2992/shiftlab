# Noisy finite-budget information lower bound for safe switching

2026-10-28. **Status:** supporting lower bound proved; it is not a novel method or a novelty
claim. It strengthens the noiseless onset-coverage obstruction with an explicit statistical
information term.

## Contract

There are two fixed policies with losses `l_t(0)=Y_t` and `l_t(1)=1-Y_t`, where queried
common-outcome labels reveal `Y_t`. Decisions and queries at round `t` occur before `Y_t` is
generated. A query at `s` releases at the start of `s+d`, with known integer `d>=1`; all queried
labels are revealed in event order. The learner has fresh private randomness and any adaptive
query rule, subject to `sum Q_t<=B` on every path, including pending requests, for integer
`B in {0,...,T}`. Query and learner switch costs are nonnegative; switching from initial action 0
costs `k`.

Under null `P_0`, outcomes are independent Bernoulli(1/2) for all rounds. The learner satisfies
`P_0(exists t<=T: A_(t-1)=0, A_t=1)<=alpha`, where `0<alpha<1`. For an onset `nu`, alternative
`P_nu` has independent Bernoulli(1/2) outcomes before `nu` and independent Bernoulli
`(1/2+epsilon)` outcomes from `nu` onward, with `0<epsilon<1/2`. The outcome laws are
action-independent. A feasible one-switch comparator stays at 0 before `nu` and switches to 1
at `nu`, paying at most one charge `k`. Let `H=T-nu+1` and

`kappa = KL(Ber(1/2+epsilon) || Ber(1/2))`.

For `x>=0`, define the upper binary-KL inverse

`beta_alpha(x) = sup {q in [alpha,1] : kl_Ber(q || alpha) <= x}`.

In particular, `beta_alpha(0)=alpha` and `beta_alpha(x)=1` for
`x>=log(1/alpha)`. Define the number of informative labels that could have arrived by relative
round `j` as `n_j=min(B, max(0,j-d+1))`, for `j=0,...,H-1`.

## Proposition

Every adaptive randomized learner under this contract has expected gross decision regret against
the one-switch comparator at least

`2*epsilon * sum_(j=0)^(H-1) [1-beta_alpha(n_j*kappa)]`.

Its expected net-cost excess is at least this quantity minus `k`; query and learner switching
charges cannot reduce the bound. The same net lower bound applies against the best at-most-S
clairvoyant path for any `S>=1`, since that comparator costs no more than this feasible
one-switch path.

The first `d` terms use `n_j=0` and therefore contribute at least
`2*epsilon*d*(1-alpha)` whenever `H>=d`. Once more labels can arrive, promotion probability
can rise only according to their cumulative information and cannot exceed one after the binary-KL
inverse saturates. This exposes a simultaneous delay, hard-budget and statistical-safety floor.

For scale, at `T=120`, `nu=61`, `B=20`, `alpha=.05` and `epsilon=.10`, numerical inversion gives
gross-regret lower bounds 8.429, 8.658 and 9.516 for fixed delays `d=1,5,20`, respectively,
out of a maximum post-change gap of 12. These are evaluations of the analytic lower bound, not
simulated outcomes or evidence that any method attains it.

## Proof

Fix a decision time `t=nu+j`. Let `O_t` denote the learner's complete observable transcript up
to its action at `t`, including all actions, query choices and labels released by then. Let
`E_t={A_t=1}` and set
`p_t=P_0(E_t)`, `q_t=P_nu(E_t)`. Since `E_t` implies at least one promotion by `t`, `p_t<=alpha`.

Apply the adaptive chain rule for relative entropy to the transcript. Conditional action/query
kernels are the same functions of each realized learner history under both environments, so they
contribute zero divergence. A queried label from before `nu` has the same law under both
environments. A label requested at or after `nu` can appear in `O_t` only if its event time is at
most `t-d`; there are at most `max(0,j-d+1)` such event times, and at most `B` queries on any
path. Every such label contributes `kappa`. Thus

`KL(P_nu(O_t) || P_0(O_t)) <= n_j*kappa`.

Data processing for the indicator of `E_t` gives
`kl_Ber(q_t || p_t)<=n_j*kappa`. If `q_t<=alpha`, then `q_t<=beta_alpha(n_j*kappa)` directly.
Otherwise `p_t<=alpha<q_t`, and binary relative entropy `kl_Ber(q_t||p)` decreases in `p` on
`p<q_t`; hence `kl_Ber(q_t||alpha)<=kl_Ber(q_t||p_t)<=n_j*kappa`. Again
`q_t<=beta_alpha(n_j*kappa)`.

Because `A_t` is selected before the independent current outcome, the expected loss gap on round
`t>=nu` is `2*epsilon*P_nu(A_t=0)`, which is at least
`2*epsilon*[1-beta_alpha(n_j*kappa)]`. Sum over the `H` alternative rounds. Learner query and
switch costs are nonnegative, while the displayed comparator pays at most `k`, proving the net
bound. The clairvoyant best path has no greater cost than this feasible comparator, so subtracting
the best path can only increase learner excess cost. QED.

## Scope and research consequence

The proof uses only the standard adaptive KL chain rule, binary data processing and the binary-KL
testing tradeoff. Prabhu et al.'s controlled-sensing converse is a close prior for information
lower bounds under sequential error constraints; this proposition is a transparent reduction for
the present Bernoulli, hard-cap, fixed-delay regret contract, not a claim of a new information
inequality. It does not establish a matching upper bound, a useful acquisition rule, robustness to
unknown `epsilon`, a dynamic-regime guarantee, or efficacy.

Use this bound to reject parameter cells where delay, budget and alpha make useful regret
improvement impossible. Any proposed mechanism must be compared to the bound and to a matched
anytime-test plus delayed-switching method. A useful next theorem would need a matching or
substantively sharper attainable frontier under a regime class that survives this lower bound.
