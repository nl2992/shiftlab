# Proof task

Status: `LOCAL_ATTEMPT`

## Target

In the symmetric two-state hidden Markov model, let both transition probabilities equal `t=(1+r)/2`, so the spin autocorrelation is `-r`, with `r in (1/200,1/100)`. Let the symmetric emission error be `e=(1-sqrt(g))/2`, with `g in (2/5,1/2)`, stationary prior `1/2`, delay `d=1`, query cost `c=0`, switching cost `k=0`, label budget `B=3`, and risk level `alpha=1/10`.

Prove that there are explicit constants `T0` and `c_star>0` such that for every integer `T>=T0` and every `(r,g)` in this open rectangle,

`rho_Gamma(T) = Gamma(T) / VOI_IID(T) >= c_star`.

The intended quantitative target is `T0=16` and `c_star=0.18`, subject to completing every bound below. This is a B=3 theorem only; it does not claim uniformity in B.

## Allowed dependencies

Use only definitions and proved statements in the source snapshots, especially the finite-horizon decision model, the first-promotion decomposition, and the exact symmetric hidden-Markov observation law. The prior B=3 attempt is evidence of a rejected proof route, not an accepted lemma. Numerical cells are not proof premises.

## Proof criterion

A proof must cover every deterministic learner plan, including adaptive query timing, pending labels at promotion, and arbitrary post-promotion query schedules. Randomized plans may then be handled by linearity/mixtures. Every causal null used must satisfy the project's stated causal-null class.

An explicit counterexample or a rigorously audited blocker is an acceptable output of this local attempt; do not label it a proof.
