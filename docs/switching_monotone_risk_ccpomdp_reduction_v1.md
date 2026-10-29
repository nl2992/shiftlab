# Monotone promotion risk reduces to a constrained POMDP: exact boundary

**Date:** 2026-10-29. **Status:** exact model reduction and novelty no-go for generic
scalarization; no new switching algorithm or scalability guarantee.

## Contract and monotone policy class

Fix a finite horizon `T`, two fixed policies with paired binary losses `(Y_t,1-Y_t)`, fixed
release delay `d`, request-time hard label cap `B`, query fee `c`, switch fee `k`, and initial
incumbent 0. The alternative law is a known two-state HMM: latent state `S_t` follows its declared
transition matrix and `P(Y_t=1|S_t=s)=theta_s`. Under the causal null, the adversary sees the full
event-time history and public request/action choices and selects each queried-label conditional
success probability in `[0,1/2]`; queried outcomes can remain pending and hidden from the learner.
The risk event is `A_t=1` for at least one `t<=T`.

Let `Pi_up` be any class of randomized policies whose every deterministic pure plan in its support
has a coordinatewise increasing any-promotion event on the full potential-label tape. The policies
still act only on their own actions, requests and released labels. The following reduction applies
only to `Pi_up`; it does not assume query timing itself is monotone.

## Proposition 1: exact causal-null reduction

For every `pi` in `Pi_up`,

`sup_{causal null P} P_pi(any promotion) = P_{IID Ber(1/2),pi}(any promotion)`.

**Proof.** Couple a causal null and an IID boundary sequence with common independent uniforms
`U_1,...,U_T`. At each event set `Y_t=1{U_t<=p_t}` for the causal null, where `p_t` is selected
from its permitted history and satisfies `p_t<=1/2`; set `Y*_t=1{U_t<=1/2}`. Then `Y_t<=Y*_t`
for every t, pathwise. For any fixed deterministic pure plan with an increasing promotion event,
promotion on the causal tape implies promotion on the IID tape. Average over the upfront policy
mixture. Since IID Ber(1/2) is itself in the null class, the upper bound is attained. QED.

This is a safety identity for a restricted policy class, not a current-regime benefit guarantee.
The existing proof and a nonmonotone counterexample are in
[`switching_monotone_promotion_reduction_v1.md`](switching_monotone_promotion_reduction_v1.md).

## Proposition 2: hidden-root constrained-POMDP representation

For a fixed Lagrange multiplier `lambda>=0`, minimizing

`C_alt(pi) + lambda * (R_causal(pi)-alpha)`

over `Pi_up` has the following exact finite-horizon model representation. Define an unobserved
root mode `M` with `P(M=alt)=1/(1+lambda)` and `P(M=null)=lambda/(1+lambda)`. In `alt`, evolve
the declared economic HMM and multiply each economic decision/query/switch cost by `1+lambda`.
In `null`, generate each potential label IID Ber(1/2) and assign terminal cost `1+lambda` if
promotion ever occurs. Both branches expose only the same delayed queried labels to one shared
learner policy; the root mode is never observed. The expected POMDP cost is exactly

`C_alt(pi) + lambda * R_IID(pi)`.

The hidden Markov state is `(M, S_t if M=alt, incumbent, remaining query rights, promotion
flag, pending queried labels by release time)`. Null labels can be generated IID without `S_t`.
Transitions charge each query against the cap at request time; fixed delay is represented by the
pending queue; terminal promotion is an absorbing reachability flag. For fixed `d`, the queue has
at most `3^d` label/empty configurations. This gives a compact finite physical-state model, while
the POMDP belief/policy optimization can still be exponentially hard in horizon.

For `0<alpha<1`, the feasible mixtures over finitely many pure plans form a compact polytope and
the never-promote policy has strict risk slack. Strong LP duality therefore recovers the
risk-constrained value as the supremum of these scalarized values minus `lambda*alpha`. The primal
or a mixture among tied scalarized policies may be needed to recover an exactly feasible optimizer.
The same mixture must be supported on monotone-event pure plans for Proposition 1 to apply.

## Prior-art consequence and limitation

Risk-constrained POMDPs already optimize expected utility with a chance constraint; RAO* is a
finite-horizon method for that model and Khonji, Jasour and Williams give approximation results
for constant-horizon constrained POMDPs. The hidden-root construction above is the standard
expected-cost scalarization of a chance-constrained problem. Adding a known HMM mode, a finite
delay queue, a remaining-budget coordinate and switching costs is ordinary state augmentation.
Thus the scalarization, duality, and POMDP representation do not provide a novelty claim.

There is also a real synthesis caveat: an unrestricted POMDP solver may return a policy with a
nonmonotone promotion event, for which its IID null cost can understate the causal-null risk. The
optimization must enforce support on `Pi_up` (for example, through explicit monotonicity
constraints on promotion probabilities over full potential tapes, or through a proved monotone
policy parameterization). The resulting structural constraints may themselves be exponentially
large. If one drops them, Proposition 1 no longer applies. If one keeps them, this is a restricted
chance-constrained POMDP, not an automatic scalable algorithm.

## Decision

Close “replace the causal adversary by a fair-coin null, then run a budgeted delayed POMDP” as a
standalone contribution. Keep it as an exact comparator/reduction for any future method that can
enforce monotone promotion events. G1 remains open only for a nontrivial synthesis or approximation
theorem that (i) retains the causal-risk guarantee, (ii) separately bounds economic-value loss,
(iii) avoids exponential monotonicity constraints or supplies a useful complexity result, and
(iv) improves on established constrained-POMDP and robust-FSC methods. No G2–G5 gate opens from
this reduction.

Primary sources: [RAO*: an Algorithm for Chance-Constrained POMDPs](https://ojs.aaai.org/index.php/AAAI/article/view/10423),
[Khonji, Jasour and Williams, IJCAI 2019](https://www.ijcai.org/proceedings/2019/0775.pdf).
