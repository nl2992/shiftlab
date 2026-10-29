# Chance-constrained POMDP approximation: prior-art boundary

**Date:** 2026-10-28. **Status:** source-level approximation audit; no contribution claim.

## Primary source inspected

Khonji, Jasour and Williams, “Approximability of Constant-horizon Constrained POMDP,” IJCAI
2019, pp. 5583–5590. The primary proceedings PDF is cached and hashed in
`switching_source_manifest_v19.json`.

Inspected Definitions 2.1–2.2, the sequence/conditional-plan formulation, Sections 3–5, the
constant-horizon hardness reduction, Theorem 5.4 and Corollary 5.5. Their CC-POMDP uses a fixed
known stochastic transition and observation model, expected reward, and a chance constraint on
reaching a risky state. For constant horizon `h`, their FPTAS is polynomial in the expanded
sequence-tree size and `1/epsilon`; the stated complexity scales as
`O((1/epsilon)|A|^(3h)|O|^(3(h-1)))`. They also prove NP-hardness for the constrained/chance-
constrained problem even at horizon two. The result is explicit about not scaling in horizon.

## Exact relation to the ShiftLab oracle

Our finite sequence-form oracle has a related tree representation and a terminal risk constraint,
but its risk is `sup` over causal conditional-null strategies whose choices depend on hidden past
outcomes and public learner choices. The working alternative has a separate known recurrent
model. This is a robust partially observed game with two different environment laws, not the
single fixed stochastic CC-POMDP analyzed by the FPTAS. The hard label cap and pending-label queue
can be included in a state augmentation, but the conditional-null adversary and its order of
information cannot be replaced by a fixed transition kernel without proving a reduction.

Because the finite null game is multilinear in each conditional Bernoulli parameter, its risk
maximum is attained by a deterministic endpoint strategy with each parameter in `{0,1/2}`.
Equivalently, one can enumerate a finite family of fixed null kernels and impose a separate
chance-risk constraint for every kernel. That is an exact finite reformulation, but the number of
such opponent strategies grows with the full hidden-history tree. The cited FPTAS states one
risky-state chance constraint for one fixed model; it does not establish an FPTAS for this
exponentially large robust family. This reduction identifies the computational obstacle precisely
without calling it a new algorithm.

Consequently, this paper closes generic finite-horizon chance-constrained planning and
approximation as a novelty claim. Its FPTAS does not directly provide a scalable approximation
guarantee for the robust causal oracle, and it does not scale polynomially in a variable long
horizon. A valid new result could still concern an approximation with a proven risk guarantee for
this robust game, but it must establish that reduction and beat established robust/sequential
planning methods. Merely adding budget, pending-label or reversal fields to the state is not a
contribution. No algorithm or experiment follows from this audit.
