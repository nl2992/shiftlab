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
places each fixed risk multiplier in a one-sided partially observed game. Therefore SAB is a direct
generic approximation comparator for scalarized game values. A contribution cannot be “aggregate
beliefs in the scalarized switching game” or “obtain a convergent belief-grid value approximation.”

The transfer is incomplete for the target contract. SAB's stated error is for a scalar discounted
infinite-horizon value, and depends on the unknown within-cell variation of that value. It does not
directly provide the project's finite-horizon, undiscounted policy guarantee. More importantly, a
scalarized error at one multiplier does not certify a returned policy's economic cost and worst
history-adaptive causal-null promotion probability separately. To obtain a feasible policy one
would need, at minimum, a finite-horizon policy/exploitability bound, uniform control over the
relevant multiplier range (including a duality/recovery argument), and a risk-feasibility repair
whose economic loss is bounded under the actual hard query cap and delayed information structure.
No such derivation is established here.

The belief state must also preserve the learner's shared information across the hidden economic/null
root, while the null branch sees generated but pending labels. A generic belief grid may therefore
have a large state and action representation; the cited value theorem alone gives no useful
complexity bound for this family.

## Decision and reopening test

Close generic SAB-style aggregation and scalarization as a novelty route. Retain SAB as a mandatory
solver baseline if a finite-horizon approximate method is later prototyped. Reopen only with a
specific structural state/partition and a proved policy-level result that (i) gives separate
economic-value and worst causal-null-risk errors for the original finite-horizon game, (ii) recovers
a truly feasible policy at risk level `alpha`, and (iii) improves a relevant complexity or regret
bound over SAB/one-sided-POSG planning and the sequence-form oracle. A discretization convergence
statement or scalarized value bound alone does not pass this gate.

Any later promotion procedure must also preserve the project invariant: historical evidence can
control its declared test-epoch false-promotion event, but it does not certify current challenger
benefit after an unobserved reversal. Current-regime forecasts/evidence and post-reversal exposure
remain separately represented and reported; see
[`switching_information_risk_contract_v1.md`](switching_information_risk_contract_v1.md).

No experiments were run for this screen. G1 remains open for a different theorem-level candidate;
G2–G5 remain held.
