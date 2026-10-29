# SAB belief aggregation prior-art audit

**Date:** 2026-10-29. **Status:** primary-source screen; generic aggregation is closed as a
novelty claim. No method or efficacy result follows.

## Source checked

Hammar et al., “Scalable Solutions to Zero-Sum Partially Observable Stochastic Games Through
Belief Aggregation with Approximation Guarantees,” AAAI 2026, [official proceedings paper]
(https://ojs.aaai.org/index.php/AAAI/article/download/38750/42712). The paper's model is a
one-sided partially observable zero-sum stochastic game. Its SAB algorithm aggregates beliefs,
solves an aggregate game by Shapley iteration, and interpolates a value approximation. Proposition
4 bounds hard-aggregation value error by `epsilon/(1-gamma)`, where `epsilon` is the maximum
within-cluster variation of the true value function (official paper, pp. 2–4). Proposition 5 gives
convergence as a uniform belief grid is refined. The paper also states that its approximate value
can be used to derive an epsilon-Nash equilibrium, referring to Horák et al. for that analysis.

## Mapping to this project

The exact hidden-root Lagrangian reduction in
[`switching_lagrangian_posg_reduction_v1.md`](switching_lagrangian_posg_reduction_v1.md)
places each fixed risk multiplier in a one-sided partially observed game. The finite-horizon game
can be embedded exactly in SAB's discounted model: augment the finite state with the public time
index, send the process to an absorbing state after the horizon, and multiply the reward at time
`t` by `gamma^(-t)`. For any `gamma` in `(0,1)`, the discounted sum then equals the original
undiscounted finite-horizon scalar payoff pathwise. If the undiscounted per-stage payoff is bounded
by `G`, choose `gamma=T/(T+1)` for `T>=1`; the transformed reward is bounded by
`G*(1+1/T)^T < eG`, while SAB's hard-aggregation error factor is `1/(1-gamma)=T+1` times its
within-cell value variation. Time can be kept as a separate aggregation stratum. Thus the
infinite-horizon statement is not a barrier to applying SAB to each finite-horizon scalarization.
Generic approximate one-sided-POSG value solving is prior art here, too.

The remaining gap is the constrained-policy recovery, not finite-horizon scalar-game value
approximation. The scalar value error depends on within-cell variation of the true value function;
SAB's cited propositions do not by themselves give separate errors for the alternative economic
cost and worst history-adaptive causal-null promotion probability of the recovered policy. Nor
does a near-equilibrium for one multiplier alone ensure risk at most `alpha`. A complete transfer
would need uniform error control over the relevant dual multiplier range, a policy extraction and
duality argument, and a risk-feasibility repair with a bound on its economic cost under the exact
hard-cap/delay contract. The simple finite-horizon embedding above supplies none of those
multiobjective recovery guarantees.

There is a generic exact repair once a candidate policy's robust risk has been independently
computed. Let its cost and risk be `(C,R)`, let the never-promote policy have cost `C0` and risk
zero, and suppose every policy cost lies in `[Cmin,Cmax]`. If `R>alpha>0`, mix the candidate with
the never-promote policy, choosing the candidate with probability `alpha/R`. Convexity of
`sup_nu R(policy,nu)` gives repaired risk at most `alpha`, and linearity gives cost increase at
most `min(1,(R-alpha)/alpha)*(Cmax-Cmin)`. This makes the missing quantity explicit: a scalarized
SAB value or exploitability bound does not provide the candidate's separate `R` or bound its risk
violation. The repair is a recovery lemma, not a new acquisition method.

The belief state must also preserve the learner's shared information across the hidden economic/null
root, while the null branch sees generated but pending labels. A generic belief grid may therefore
have a large state and action representation; the cited value theorem alone gives no useful
complexity bound for this family.

## Decision and reopening test

Close generic SAB-style aggregation and scalarization as a novelty route, including their generic
finite-horizon extension by time augmentation and reward rescaling. Retain SAB as a mandatory
scalar-game solver baseline if a finite-horizon constrained approximation is later prototyped.
Reopen only with a specific structural state/partition and a proved policy-level result that (i)
gives separate economic-value and worst causal-null-risk errors for the original finite-horizon
game, (ii) recovers a truly feasible policy at risk level `alpha`, and (iii) improves a relevant
complexity or regret bound over SAB/one-sided-POSG planning and the sequence-form oracle. A
discretization convergence statement or scalarized value bound alone does not pass this gate.

Any later promotion procedure must also preserve the project invariant: historical evidence can
control its declared test-epoch false-promotion event, but it does not certify current challenger
benefit after an unobserved reversal. Current-regime forecasts/evidence and post-reversal exposure
remain separately represented and reported; see
[`switching_information_risk_contract_v1.md`](switching_information_risk_contract_v1.md).

No experiments were run for this screen. G1 remains open for a different theorem-level candidate;
G2–G5 remain held.
