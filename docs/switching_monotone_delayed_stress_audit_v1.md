# Monotone promotion restriction: delayed-reversal stress test and prior-art decision

**Date:** 2026-10-28. **Status:** candidate rejected as a methodological contribution; no paper claim.

## Constrained comparison

The sequence-form learner LP now optionally constrains the probability of ever promoting on the
full potential-outcome tape to be coordinatewise nondecreasing. The restriction is linear in
realization weights: on a fixed tape each learner randomization path has a realization-sequence
weight, and the promotion event is a disjoint union of first-promotion sequences. The hard
pathwise query cap remains encoded by feasible actions; delayed label release remains encoded by
learner information sets. The objective is predictive HMM decision loss plus query/switch costs.
The robust causal-null promotion constraint is unchanged and is separately enforced against all
causal endpoint responses. See `src/shiftlab/dive/causal_switching_game.py`.

For a symmetric HMM with transition 1/4, emissions (1/10,9/10), prior 1/2, hard budget 2,
query cost 1/100 and switch cost 1/10, restricted and unrestricted floating-point LP objectives
matched at delays 1 and 2. At delay 2, horizon 6, budget 3, alpha 1/10, query cost 1/100,
switch cost 1/10, emissions (1/50,49/50), restricted and unrestricted objectives again matched:
2.955693376 at transition 1/4 (causal risk 1/10), and 3.0 at transition 9/20 (the returned
policy never promotes; causal risk 0). The second cell is weakly informative about promotion
structure because the optimum declines to promote.

## Source-level novelty decision

The structural intuition is already classical in partially observed control. Lovejoy (1987)
provides sufficient conditions for monotonicity of finite-POMDP value functions under likelihood-
ratio ordering and gives conditions for monotone optimal policies in a replacement problem. The
standard two-state POMDP structural results summarized in Krishnamurthy's *Partially Observed
Markov Decision Processes* derive threshold optimal policies under sufficient MLR/TP2 and cost
conditions. Our binary persistent HMM uses an MLR emission channel and a TP2 transition matrix
when the flip probability is at most 1/2. This is not an exact theorem reduction: our tape-level
probability constraint, pathwise query cap, delays, and robust causal-null risk are additional
structure. But the candidate's empirical pattern follows a known structural route, and no
advantage over the unrestricted planner appears in the tested cells.

Sources: Lovejoy, “Some Monotonicity Results for Partially Observed Markov Decision Processes,”
*Operations Research* 35(5), 1987, DOI 10.1287/opre.35.5.736; Krishnamurthy, *Partially Observed
Markov Decision Processes*, Cambridge University Press, 2016, chapters 10–12.

## Decision

Reject monotone promotion as the proposed new acquisition-and-switching mechanism. The exact
signed-future-value counterexample already rules out a broad guarantee without excluding reversals;
with MLR HMM assumptions, monotonicity resembles established POMDP structure; the constrained LP
shows no objective gain in the tested delayed cells. Keep the constraint implementation as a
research diagnostic, not as the candidate algorithm. G1 remains open. Return to the central
acquisition question only with a narrower interaction that can beat a faithful composition of
controlled sensing, robust finite-horizon planning and delayed-feedback switching under one
explicit contract. No matched efficacy study or real-data evaluation is justified yet.
