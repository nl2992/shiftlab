# Paired-loss reduction for a real-sequence replay: audit protocol v1

Registered 2026-10-29 before constructing the audit. Starting revision 7ee5e81.
This is a data-free mathematical and software-contract audit; no real data,
seeds or reserved holdouts are accessed.

The capped two-law reference models binary Y with action losses (Y,1-Y) and
an event-time causal null P(Y=1 | full past, public query choice)<=1/2. CRSP
replay instead supplies two bounded paired losses l0,l1 from a common outcome.
Assess (i) whether a transform can preserve each policy's expected decision
cost differences, query and switch costs, timing and filtration, and (ii)
whether the null and planner likelihood assumptions survive the transform.

Test the following proposed randomized encoding under explicit, fixed bounds:
0<=l0,l1<=1 and Z=l0-l1 in [-1,1]. After the common loss pair becomes observable
to the evaluator, draw an independent uniform U and define
Y=1{U <= (1+Z)/2}. Then E[2Y-1 | Z]=Z. Use paired action losses
(Y,1-Y), and scale query/switch fees by 1/2 when converting from original loss
units to encoded loss units. Prove the affine equality in conditional expected
cost and explicit common offset, including arbitrary action choices that are
predictable before the current outcome, queries and switches. State the scaling
and all requirements on private randomness, observed feedback, delayed release,
and event-time conditional mean null.

Explicitly test whether encoding twice changes the information available to the
learner, whether true squared-loss magnitudes remain observable, and whether an
arbitrary empirical binary sequence satisfies the planner's known two-state HMM
law. Construct deterministic finite counterexamples with exact fractions to
falsify any claim that preserving expected cost differences also preserves pathwise
losses, full-information policies or the HMM. Check nonfinite and unbounded loss
handling; clipping requires a declared alternative estimand and frozen threshold.

Record results and source provenance in a new artifact; do not run a real-data
comparison until the algorithm, transformations and matched baselines are frozen
under the research gates. Do not claim empirical validity or novelty from this
algebraic reduction. The existing exposed CRSP test period remains development
only and does not certify production clocks or financial utility.
