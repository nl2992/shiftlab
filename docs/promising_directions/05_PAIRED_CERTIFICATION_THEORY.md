# 05 Paired-benefit certification: validity statement and scope

Status: an elementary validity argument written out for the B1 setting. The ingredients are
established and are not claimed as novel: IPW paired increments, structural zeros on
agreement, predictable bounded bets, and Ville's inequality. Closest sources are recorded in
`02_LITERATURE_AND_NOVELTY_AUDIT.md`: CAMS (Liu et al., NeurIPS 2024), active RCPS / active
betting (Xu et al.), and paired confidence sequences.

## Setting

Use the contract of `03_FORMAL_PROBLEM_AND_INFORMATION_CONTRACT.md` with one incumbent and one
candidate under 0/1 loss.

- Paired advantage: `D_t = l(f_0, Y_t) - l(f_1, Y_t)`, which lies in {-1, 0, 1}.
- Agreement: `G_t = 1{f_0(X_t) = f_1(X_t)}`. This is free and observed at issue time. If `G_t = 1`,
  then `D_t = 0` surely (structural zero).
- Query probability: `p_t`, which is `H_t`-measurable. If `G_t = 1`, then `p_t = 0`; otherwise
  `p_t >= p_min > 0`. `Q_t ~ Bern(p_t)` is drawn with public randomness, independently of `Y_t`
  given `(H_t, X_t)`.
- Increment: `Z_t = (1 - G_t) Q_t D_t / p_t`. It is released at `t + d`, and `|Z_t| <= 1/p_min`.
- Bet: `lambda_t in [0, p_min/2]`. It is fixed at issue time `t` and is `H_t`-measurable.
- Wealth: `W_n = prod_{t : t + d <= n} (1 + lambda_t Z_t)`. Each factor is at least 1/2.

## Null and claim

Fixed-delay conditional null H0:

    E[D_t | H_{t+d-1}^{(-t)}] <= 0 for every t.

Here `H_{t+d-1}^{(-t)}` is all learner information up to `t+d-1` except `Y_t` itself. The
statement allows the advantage to change arbitrarily over time.

Claim. Under H0, `(W_n)` is a nonnegative supermartingale with respect to the release filtration,
with `W_0 = 1`. Hence `P(sup_n W_n >= 1/alpha) <= alpha` (Ville's inequality). Promoting at the
first crossing gives false-promotion probability at most `alpha`, uniformly over the stopping
time.

Proof. At release time `n = t + d`, the new factor is `1 + lambda_t Z_t`. `lambda_t`, `p_t`, `G_t`
and `Q_t` are all measurable with respect to `H_{t+d-1}^{(-t)}`, and `Q_t` is conditionally
independent of `Y_t`. Therefore

    E[Z_t | H_{t+d-1}^{(-t)}] = (1 - G_t) E[D_t | H_{t+d-1}^{(-t)}] <= 0,

which gives `E[1 + lambda_t Z_t | .] <= 1`. Positivity follows from `lambda_t |Z_t| <= 1/2`. QED.

## Where the guarantee is weaker than it looks

1. **Informative delay or covariates after issue.** H0 conditions on information that arrives
   after `t`, such as later agreement indicators. If such information predicts `Y_t`, then
   "`E[D_t | F_{t-1}] <= 0`" alone is not enough. The repository's event-prefix analysis
   (`docs/delayed_event_prefix_validity.md`) records this distinction. Outcome-dependent
   delays are not covered.
2. **Marginal versus conditional.** H0 is a conditional null. It does not certify a stationary
   marginal advantage. Under persistent latent regimes, the dependence-gate bound
   `alpha + eps(1 + (T-1) delta)` limits any marginal-null test.
3. **Rollback.** A mirrored e-process started at promotion is valid for its own null from that
   time. Repeated promote/rollback cycles need an alpha-spending rule, for example
   `alpha_i = alpha / (i(i+1))`, as in `promotion.py`, if a pathwise bound on total wrong
   promotions is required. B1 reports wrong-promotion frequencies empirically. It does not
   claim a multi-cycle bound unless spending is used.
4. **Certificate does not imply profit.** Proposition B0 shows this. Turning a certificate into an
   economic guarantee needs a persistence or drift assumption. The P4 rule in B1 uses a declared
   known hazard. With that assumption, the expected-benefit inequality
   `LB_t * E[persistence] > c_s` is plug-in decision theory. A *data-driven* persistence
   certificate would be a new object. It is residual question 2 in the literature audit and
   has not been constructed here.

## Open proof obligation (residual question 2)

Construct an anytime-valid lower bound on the future cumulative advantage
`sum_{s=t+1}^{t+m} D_s`, rather than only on the past mean. It must hold under a nonparametric
persistence class, for example a bounded-variation drift `|E[D_{s+1} - D_s | F_s]| <= kappa`.

Under bounded drift `kappa`, a past-mean lower bound `LB` over a window of length `w` that ends
at `t` implies `E[D_{t+j} | F_t] >= LB - kappa (w/2 + j)`. A future-benefit bound then follows
by summation:

    E[sum_{j=1}^m D_{t+j} | F_t] >= m LB - kappa m (w + m + 1)/2.

This step is elementary. It does not identify `kappa` from data, and it is not novel unless
paired with a lower bound showing that `kappa` (or a persistence parameter) must be known.
The qualitative necessity is already trivial: Proposition B0's reversal construction is an
unbounded-drift instance. So a *nontrivial* result would need a quantitative minimax rate,
namely the regret of certified switching as a function of `kappa`, `B`, `d` and `c_s`, with
matching upper and lower bounds. No such result exists in this repository.
