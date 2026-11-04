# C1-E exact information screen — protocol v1

**Status:** frozen exact development screen, not a method or SOTA claim. Freeze recorded before
execution. Purpose: determine whether observation-adaptive query timing buys information over the
best fixed calendar in the existing dynamics-only HMM family, and quantify the gap to the exact
belief-state optimum.

## Question and estimand

Two candidate HMMs have identical stationary one-label marginals but different transition rates.
Can an adaptive, pathwise-budgeted query policy collect more evidence for the true model than every
fixed calendar with the same horizon, delay, and query cap?

Primary estimand is the exact expected log likelihood ratio under the designated alternative,
equivalently the KL divergence between the queried-label transcripts under the alternative and
null for a fixed predictable query policy. This is an information diagnostic only. It does not
measure promotion power, false-promotion probability, expected deployment cost, or value against
the exact sensing oracle.

## Frozen cell

- Hidden state `S_t in {0,1}`, initialized from the stationary distribution `(1/2,1/2)`.
- Alternative transition matrix `A_1=[[.7,.3],[.3,.7]]`.
- Null transition matrix `A_0=[[.9,.1],[.1,.9]]`.
- Shared emission law: `P(Y=+|S=0)=.8`, `P(Y=+|S=1)=.2`; `Y in {+,-}`.
- Horizon `T=20`; pathwise cap `B=4`; fixed delay `d=1`.
- At event `t`, the prior event's queried label is released before the query decision. The event-`t`
  label is released before the next event's query decision. The final label is counted even though
  no post-horizon action is available.
- The learner may query or skip at each event. Query actions are deterministic functions of its
  released-label history and the remaining query cap. Querying does not affect the HMM.

The equal stationary marginals make one isolated label uninformative about the transition
parameter. Consecutive observations can reveal transition structure, which directly probes the
burst-versus-sparse information mechanism already recorded in
[`switching_c1_upper_bound_proofs_v1.md`](../switching_c1_upper_bound_proofs_v1.md).

## Comparators and calculation

1. Enumerate every deterministic fixed calendar with at most four queries and evaluate its
   transcript KL exactly by dynamic programming over rational HMM filtering beliefs.
2. Evaluate the best single contiguous burst of at most four queries as a named calendar subset.
3. Solve the finite-horizon belief-state dynamic program exactly for the maximum transcript KL
   under the same pathwise cap and delay. The DP is the sensing oracle; no candidate can beat it.
4. Report the adaptive-to-best-calendar KL ratio, the adaptive-to-oracle gap, expected query count
   of the adaptive policy, selected action decisions on reachable states, and the number of
   reachable DP states. Use deterministic tie-breaking: query on exact value ties.

All posterior probabilities and transition updates are rational. KL values use natural logarithms
of the exact rational predictive probabilities. No Monte Carlo, parameter tuning, or outcome-based
selection is used.

## Advance / stop rule

Advance this direction only if the adaptive optimum strictly exceeds every fixed calendar by a
material margin and the DP's policy structure suggests a tractable belief rule with a certified gap
to the oracle. A finite-cell calendar gap alone is established adaptive sensing behavior and is not
a novelty claim. Even a positive screen must be followed by a theorem proving a budget/delay/risk
rate beyond routine belief-state planning and a valid model-conditional promotion construction.
Close C1-E if the exact gap is zero/small, or if only the full DP captures the gain and no useful
tractable policy bound emerges.

## Provenance

Runner: [`scripts/screen_switching_c1e_information_dp.py`](../../scripts/screen_switching_c1e_information_dp.py).
Output is ignored under `outputs/switching_c1e_information_dp_v1/`. The runner records its own
SHA-256, this protocol's SHA-256, Python version, exact model constants, state counts, and all
calendar scores.
