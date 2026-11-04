# A finite-horizon information bound near unit persistence

**Status:** finite-horizon theory screen; no simulation or new empirical claim. The postprocessing
corollary below applies to adaptive queries and delayed feedback under the stated exogenous-stream
model. This is not a lower bound for the full P2 benchmark or a novelty claim.

## Question

Can a fixed-horizon procedure distinguish a marginally unfavorable stream from a marginally
favorable one when serial persistence is unknown and may be arbitrarily close to one? The current
SOTA sprint uses binary favorable-sign outcomes and the refresh-or-hold Markov model in
[`fam_a.py`](../../scripts/sota_sprint/fam_a.py): at each event the sign is retained with
probability `rho`, otherwise redrawn from `Bernoulli(p)`. The initial sign is also `Bernoulli(p)`.

## Proposition (two-point testing bound)

Let `X_1,...,X_T` follow that stationary binary chain. Fix `delta` in `(0, 1/2)` and `rho` in
`[0,1]`. Let `P0` have `p0=1/2` and let `P1` have `p1=1/2+delta`, with the same `rho`. For any
possibly randomized test `phi` with rejection probability at most `alpha` under `P0`,

```text
P1(phi rejects) <= alpha + delta
                      + (T - 1)(1 - rho)(1 - 2 delta^2).
```

The right-hand side may be capped at one. In particular, at `rho=1`, the full length-T path is
just the initial Bernoulli draw and the power is at most `alpha + delta`, regardless of T. More
generally, to achieve power at least `1-beta`, it is necessary that

```text
(T - 1)(1 - rho)(1 - 2 delta^2) >= 1 - beta - alpha - delta,
```

when the right-hand side is positive. The left-hand side is the sum of the expected numbers of
observed sign changes under `P0` and `P1`.

### Proof

For each `p`, let `Q_p` be the law of the constant path whose first value is `Bernoulli(p)`. Couple
the Markov path and this constant path with the same first value. The paths differ only if at least
one observed sign change occurs, so the coupling inequality gives

```text
TV(P_{p,rho}^T, Q_p) <= E_{p,rho}[N_T]
                       = 2 p (1-p) (T - 1)(1 - rho),
```

where `N_T = sum_{t=2}^T 1[X_t != X_{t-1}]`. Also,
`TV(Q_{1/2}, Q_{1/2+delta}) = delta`. The triangle inequality therefore yields

```text
TV(P0, P1) <= delta
              + (T - 1)(1 - rho) [1/2 + 2(1/2+delta)(1/2-delta)]
            = delta + (T - 1)(1 - rho)(1 - 2 delta^2).
```

For every test, the difference in rejection probabilities is at most total variation. Since its
size under `P0` is at most `alpha`, the claimed power bound follows. The same argument applies to
the event that an anytime procedure has promoted by horizon T.

## KL bound for stationary and scheduled alternatives

Write `d(a||b)` for the KL divergence between Bernoulli variables with means `a` and `b`. Let the
null retain `p0,t = 1/2` at every event, and let the alternative use any fixed, known schedule
`p1,1,...,p1,T` in `(0,1)`; both chains have the same fixed persistence `rho`. Define
`q_{i,t,x} = rho*x + (1-rho)*p_{i,t}`. The Markov-chain KL chain rule and stationarity under `P0`
give the exact divergence

```text
D_KL(P0^T || P1^T)
  = d(1/2 || p1,1)
    + (1/2) * sum_{t=2}^T sum_{x in {0,1}} d(q_{0,t,x} || q_{1,t,x}).
```

The stationary alternative in the proposition is the special case `p1,t=1/2+delta`. Pinsker's
inequality gives power at most `min(1, alpha + sqrt(D_KL(P0^T || P1^T)/2))` for any test of size
`alpha` under `P0`.

In particular, any deployment method that controls false promotion over the registered stationary
null class has size at most `alpha` under this `p=.5` null member. Its probability of ever promoting
by event T under each fixed scheduled alternative is therefore bounded by the expression above,
provided the common-channel condition below holds.

Now let `Y` be the entire transcript of any deployment policy that receives a stream of horizon T:
its queried event IDs, labels released (possibly after delays), actions, and final promotion event.
Assume the full sign path exists exogenously. Also assume the joint conditional law of every other
policy-visible input given that path is the same under `P0` and `P1`; this includes model predictions,
contexts, disagreement indicators, policy randomization and delays. The policy may process these
inputs and requested, delayed labels adaptively, provided its actions do not alter the future sign
path. Under these conditions, the complete transcript Y is a common randomized channel of the sign
path, so KL and total variation cannot increase under this postprocessing. The same power bounds
then hold for adaptive label requests and delayed release. The query schedule need not be fixed in
advance.

For the SOTA sprint's synthetic streams, the common-kernel condition can be checked in the code:
`Regime.sample` draws the disagreement indicator independently of the Markov sign, and
`stream_from_losses` constructs predictions by XORing each loss with an independent fair label
(`scripts/failure_atlas_v2_flq/regimes.py`, `scripts/failure_atlas_v2_flq/suite.py`). Thus predictions
alone do not reveal the sign; a requested label reveals its loss through a hypothesis-invariant
channel. The fixed delay and private policy randomness also have the same law under both hypotheses.
This verifies the corollary for the synthetic runner under the declared regime model. It does not
automatically verify it for other stream builders, including real-data or alternate label encodings;
each requires its own coupling check.

## Numerical reading under the sprint contract

For `T=2000`, `alpha=.05`, `delta=.05`, the coupling bound's necessary condition for 80% power
requires `rho <= 0.99965` (rounded). The KL/Pinsker caps for the stationary alternative are .412 at
rho=.95, .281 at .98, .217 at .99, .121 at .999, and .100 at 1. For the registered V_late_600
schedule (`p1=.42` through event 599, then `.70`), the caps are 1.000 at .95, .863 at .98, .627 at
.99, .247 at .999 and .131 at 1. For W_late_1000 (`.42` through event 999, then `.72`), they are
1.000, .834, .606, .241 and .131 at the same persistence values. These are upper bounds, not
predicted operating characteristics; Pinsker can be loose. They are vacuous for the two late
schedules at rho=.95, so this calculation does not explain the observed cost/power gaps there. It
does show that no fixed-horizon guarantee can promise high power uniformly over persistence
arbitrarily close to one. The data-processing corollary means this limitation also applies to
adaptive querying and delay under the exogenous-stream assumptions.

## Decision-value lower bound at perfect persistence

The testing bound has a direct, cost-sensitive decision corollary in the limiting case `rho=1`.
Let one episode have a latent sign `Z in {-1,+1}` that remains constant for all `T` events, with
`P_p(Z=+1)=p`. The paired deployment advantage of the challenger is `D_t=Z`. Compare the marginal
null `p0=1/2` to the alternative `p1=1/2+delta`. Assume all policy-visible information, including
predictions, query randomization and release timing, has a conditional law given `Z` that is the
same under both hypotheses. Thus even unlimited repeated labels reveal at most the single latent
sign. Let `A_t` indicate challenger deployment, and let `phi=1{sum_t A_t>0}`. A policy is
`alpha`-safe if `P_{p0}(phi=1)<=alpha`; query and switching costs are nonnegative.

**Proposition.** If `alpha<=1/2` and `2 delta T > c_s`, every such policy's expected net gain over
the incumbent under `p1` is at most

```text
2 alpha (1/2 + delta) T.
```

The policy that deploys the challenger for all `T` events after one switch has expected net gain
`2 delta T - c_s`. Hence the constrained policy's regret relative to this fixed-policy oracle is
at least

```text
max(0, 2 delta T - c_s - 2 alpha (1/2 + delta) T).
```

**Proof.** Let `q_+ = P(phi=1 | Z=+1)` and `q_- = P(phi=1 | Z=-1)`. The common-channel assumption
makes these conditional promotion probabilities identical under `p0` and `p1`. Null safety gives
`(q_+ + q_-)/2 <= alpha`, so `q_+ <= 2 alpha`. On a negative-sign episode, every period of
challenger deployment has nonpositive gross gain; on a positive-sign episode, total gross gain is
at most `T`. Therefore under `p1` the gross expected gain is at most
`p1 T q_+ <= 2 alpha p1 T`. Nonnegative query and switch costs can only reduce net gain. The fixed
challenger policy has expected gross gain `T E_{p1}[Z] = 2 delta T` and pays one switch cost
`c_s`. Subtracting yields the regret bound. QED.

For `alpha=.05`, `delta=.05`, `T=2000`, and `c_s=5`, the fixed challenger oracle gains `195` units;
every alpha-safe policy is bounded above by `110` units before query costs, so the gap is at least
`85` units. Increasing the event horizon does not close this gap: at `rho=1`, those events are
repeated observations of the same latent sign. A label cap or delay cannot improve the bound.

This is a decision-value result for one episode and a marginal-null safety requirement. It does not
cover a conditional-mean null, a lower bound uniform over `rho<1`, multiple independent episodes,
or the benchmark's full stream family. It is a two-point reduction and may be standard in substance;
the useful next check is whether a multi-episode, finite-refresh extension yields a sharp bound that
changes the interpretation of the registered cost objective. Do not call this a novel algorithm or
a proven SOTA improvement.

## Scope and consequence for P2

- This is an elementary finite-sample information bound for a known pair of simple hypotheses. It
  does **not** establish a new sequential testing method, prove the validity of A5b, or show that the
  empirical candidate is optimal.
- It does not show that *observed run changes alone* are sufficient statistics for evidence. It says
  the two distributions become close in total variation as the expected number of sign changes
  vanishes and the marginal means approach each other.
- It assumes one binary trajectory, a simple null and a fixed alternative persistence; the KL form
  also allows a fixed, known time-varying `p_t` schedule. Adaptive label issuance and delayed feedback
  are covered only when all other visible inputs have a common conditional law given that path.
  Independent episodes can be handled by applying KL chain rules to a specified product law;
  persistent covariates, richer paired losses, and unknown model parameters need separate treatment.
- Under this model, the bound gives an information-theoretic distinguishability limitation relevant
  to a putative validity-power frontier: allowing persistence arbitrarily near one limits how much
  finite-horizon evidence is available. It does not justify the stronger claim that every
  dependence-robust method must follow run changes or that a particular observed performance gap is
  unavoidable.
- The testing bound does not optimize over rho, characterize the best test, or quantify the actual
  cost of A5b/RMM. The perfect-persistence corollary gives a cost-objective bound only for its
  single-episode two-point model; it is not yet a bound for the registered stream family or a novel
  algorithmic contribution. A broader result would need to match the benchmark's random episode
  alternatives and stream count and yield a decision-relevant bound beyond this special case.

## Literature positioning

This result is a standard information-theoretic testing argument specialized to the repository's
refresh-or-hold chain. The nearby sequential literature already contains (i) anytime-valid,
distribution-free inference for bounded sequential score differences under a conditional-mean weak
null, as in [Choe and Ramdas, *Comparing Sequential Forecasters*](https://pubsonline.informs.org/doi/10.1287/opre.2021.0792), and (ii) safe e-processes with power against specified Markovian alternatives, as in
[Ramdas et al., *Testing exchangeability: fork-convexity, supermartingales, and e-processes*](https://doi.org/10.1016/j.ijar.2021.06.017). The repo's existing novelty audit also identifies [universal inference](https://pmc.ncbi.nlm.nih.gov/articles/PMC7382245/) and this Markov-e-process work as direct prior art. This screen adds a statistical distinguishability limitation for one narrow model, not a method novelty delta.

