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
null `p0=1/2` to the alternative `p1=1/2+delta`. Every event is a disagreement (`|D_t|=1`), so the
bound uses the maximum per-event headroom. This marginal null is not the conditional-mean null
used by P3b. Assume all policy-visible information, including
predictions, query randomization and release timing, has a conditional law given `Z` that is the
same under both hypotheses. The policy starts on the incumbent. Thus even unlimited repeated labels
reveal at most the single latent sign. Let `A_t` indicate challenger deployment, and let
`phi=1{sum_t A_t>0}`. A policy is
`alpha`-safe if `P_{p0}(phi=1)<=alpha`; query and switching costs are nonnegative.

**Proposition.** If `alpha<=1/2` and `T>c_s`, every such policy's expected net gain over the
incumbent under `p1` is at most

```text
2 alpha (1/2 + delta) (T - c_s).
```

The policy that deploys the challenger for all `T` events after one switch has expected net gain
`2 delta T - c_s`. Hence the constrained policy's regret relative to this fixed-policy oracle is
at least

```text
max(0, 2 delta T - c_s - 2 alpha (1/2 + delta) (T - c_s)).
```

**Proof.** Let `q_+ = P(phi=1 | Z=+1)` and `q_- = P(phi=1 | Z=-1)`. The common-channel assumption
makes these conditional promotion probabilities identical under `p0` and `p1`. Null safety gives
`(q_+ + q_-)/2 <= alpha`, so `q_+ <= 2 alpha`. On a negative-sign episode, every period of
challenger deployment has nonpositive gross gain, and any promotion pays at least one switch cost.
On a positive-sign episode, total gross gain is at most `T`, with at least one switch cost `c_s`;
nonnegative query costs further reduce net gain. Hence net gain is at most zero on the negative
branch and at most `T-c_s` on the positive branch. Under `p1`, expected net gain is at most
`p1 (T-c_s) q_+ <= 2 alpha p1 (T-c_s)`. The fixed-challenger policy has expected gross gain
`T E_{p1}[Z] = 2 delta T` and pays one switch cost `c_s`. Subtracting yields the regret bound. QED.

For `alpha=.05`, `delta=.05`, `T=2000`, and `c_s=5`, the fixed challenger oracle gains `195` units;
every alpha-safe policy is bounded above by `109.725` units before label costs, so the gap is at
least `85.275` units. These are maximum-headroom toy-model units, not a measured bound for the
benchmark's streams. Increasing the event horizon does not close this gap: at `rho=1`, those events are
repeated observations of the same latent sign. A label cap or delay cannot improve the bound.

This is a decision-value result for one episode and a marginal-null safety requirement. It does not
cover a conditional-mean null, a lower bound uniform over `rho<1`, multiple independent episodes,
or the benchmark's full stream family. It is a two-point reduction and may be standard in substance;
the finite-refresh coupling extension below is valid but does not give a useful regret lower bound
on the registered range. Do not call this a novel algorithm or a proven SOTA improvement.

### Finite-refresh extension by coupling (valid, but weak)

For `rho<1`, couple the refresh-or-hold chain to its constant initial-sign path. The probability
that the two paths differ is exactly the probability of at least one sign change,

```text
eps(p; T, rho) = 1 - p [rho + (1-rho)p]^(T-1)
                    - (1-p) [rho + (1-rho)(1-p)]^(T-1).
```

This is also the total-variation distance between the Markov path law and the constant-path law
with the same initial Bernoulli draw. Let `eps0=eps(1/2;T,rho)` and
`eps1=eps(1/2+delta;T,rho)`. If `phi` is alpha-safe under the Markov null, its probability on the
constant-path null is at most `alpha+eps0`. Repeating the perfect-persistence argument on that
constant-path law, and then transferring expected gross gain from the constant-path alternative
to the Markov alternative for a payoff in `[-T,T]`, gives

```text
E_(p1,rho)[net gain] <= min(T, p1*T*min(1, 2*(alpha+eps0)) + 2*T*eps1).
```

The fixed challenger still gains `2*delta*T-c_s`, so subtracting the displayed upper bound gives a
valid regret lower bound, floored at zero. It applies to arbitrary adaptive acquisition and delay
under the same common-channel assumptions, because those are postprocessing of the full sign path.

**Usefulness check.** At `T=2000`, `alpha=delta=.05`, `c_s=5`, the fixed-policy oracle gains 195
units. The gross-gain upper bound is 110 at `rho=1`, giving the 85-unit gap above. At `rho=.9999`,
the exact coupling probabilities are `eps0=.0951`, `eps1=.0942`; the upper bound rises to about
696, so the regret lower bound is already zero. It remains zero throughout the registered
`rho<=.95` range. This extension therefore does not explain the sprint's dependence results and is
not useful as a quantitative bound for its registered parameter grid. It only formalizes continuity
at the singular `rho=1` boundary.

### Exact full-path relaxation for finite `T`

A sharper route avoids coupling. For a sign path `x in {-1,+1}^T`, define the offline switching
value

```text
R_cs(x) = max over a_0=0, a_1,...,a_T in {0,1}
          [sum_t a_t*x_t - c_s*sum_t |a_t-a_(t-1)|].
```

This allows the policy to see the entire path before choosing its actions, so it is an optimistic
relaxation. It includes any number of promotions and rollbacks; `R_cs(x)>=0` because the incumbent
can always be kept. For any actual policy starting on the incumbent, its realized deployment gain
before query costs is at most `R_cs(x)*1{ever promoted}`. Let `psi(x)` be the conditional
probability of ever promoting given the full path, integrating over the common policy-visible
channel and internal randomization. The common-channel assumption makes this same function apply
under both hypotheses. Any policy with `P_0(ever promote)<=alpha` therefore satisfies

```text
E_1[net gain] <= sup_{0<=psi(x)<=1, E_0[psi(X)]<=alpha} E_0[psi(X) L(X) R_cs(X)],
L(x)=P_1(x)/P_0(x).
```

This is a finite linear program over the `2^T` paths. Its exact solution sorts paths by
`L(x)R_cs(x)` and spends the false-promotion budget on the largest values, randomizing at the
cutoff if needed. It is a sharp upper bound for the full-observation relaxation and hence for every
adaptive acquisition/delay policy under the same data model. For `rho=1`, it reduces to the earlier
closed-form bound `2 alpha p1 (T-c_s)` when `alpha<=1/2` and `T>c_s`.

This formulation is decision-relevant and handles finite refresh, switching economics and rollback
in one object. However, the full-path relaxation is classical constrained Bayes/Neyman-Pearson
optimization, and `2^T` enumeration is infeasible at the registered `T=2000`. It is not a
contribution. An independent path-type screen gives a tractable, though looser, upper bound:
`R_cs(x) <= (M-c_s)_+`, where `M` is the number of positive signs. Under the symmetric binary
Markov model, the likelihood ratio and aggregate path mass can be grouped by initial sign, terminal
sign, flip count and `M`; sorting those type scores yields an O(T^2)-cell fractional LP. At
`T=2000`, `p1=.55`, `alpha=.05`, and `c_s=5`, its gross-gain ceilings are about 231.125 at
`rho=.95` and 509.693 at `rho=.8`, both above the fixed challenger oracle's net 195. Thus this
cheap finite-refresh bound gives no positive regret lower bound on those registered cells.

A tighter exact computation would need to retain transition counts for the likelihood ratio and
the max-plus switching reward jointly. The reward has the standard two-state offline recurrence,
but the joint sufficient-state table appears too large at `T=2000` without a proved compression.
The finite-refresh full-path relaxation is therefore closed as a current theory lead: it is valid
but uninformative in the registered persistence range, and the remaining route is computationally
and theoretically unresolved. Keep the perfect-persistence boundary result as a scoped observation;
do not present it as a finite-refresh explanation or novelty claim.

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

