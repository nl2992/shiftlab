# Exact causal-risk verification on a finite-state controller

**Date:** 2026-10-28. **Status:** constructive verifier lemma checked on a delayed signed event; established robust-FSC prior art closes generic novelty.

## Restricted class and proposition

Fix a deterministic finite-state controller (FSC), a finite horizon, fixed known release delays, and a pathwise query cap. Its state updates from its own past actions/queries and the labels released to it. The causal-null environment sees the full event-time queried outcomes, including pending labels, and at each queried event selects a conditional Bernoulli parameter in `[0,1/2]` after observing the public current action/query.

**Proposition.** The controller's exact worst-case probability of ever promoting is computed by backward dynamic programming on the product state

`(time, FSC memory, incumbent action, remaining query rights, pending-label queue)`.

The recursion assigns risk 1 at a first promotion. At a nonpromotion state with a query, it takes

`max_{p in {0,1/2}} ((1-p) V(s_0') + p V(s_1'))`;

without a query it follows the deterministic next state. Because the conditional-null set is rectangular (the next conditional parameter can be selected independently at every full history), histories sharing a product state have the same feasible continuation set and continuation values. An adversary with the larger full history cannot improve by distinguishing those histories. The maximum is attained at an endpoint because the one-step expression is affine in `p`. Thus the product-state recursion gives the exact causal risk, including nonmonotone promotion events. For fixed delay d, the pending queue has at most `3^d` configurations (empty, pending zero, pending one in each slot); complexity is linear in horizon times the reachable product-state count. This proposition concerns risk verification for a fixed deterministic FSC, not optimizing the controller.

The restriction to deterministic FSCs matters: with hidden persistent controller coins, the environment may not know the internal memory state, and the product state must preserve the corresponding information structure. The proposition does not silently give the adversary access to future private randomness.

## Delayed signed-event check

Query `Y1` at event 1 and `Y2` at event 2. Both labels have fixed delay 2; the controller stores `Y1` when it arrives at the start of event 3 and at event 4 promotes iff `Y1 != Y2`. This is a deterministic FSC with one bit of memory after the first release and a nonmonotone terminal event. Its compact risk recursion gives

`V(after Y1=0)=1/2`, `V(after Y1=1)=1`, and `V(initial)=3/4`.

The independent full-history endpoint enumeration over `(p1,p2|Y1=0,p2|Y1=1) in {0,1/2}^3` also gives exact worst risk `3/4`, attained at `(1/2,1/2,0)`. The checker is `scripts/verify_switching_fsc_delayed_risk_compression.py`; exact output and code hash are in `outputs/switching_fsc_delayed_risk_compression_v1/results.json`.

This demonstrates exact risk compression for a signed event that the monotone-event shortcut cannot cover, and is consistent with the previous `Y1 != Y2` versus static-null-mixture separation. It does not give the policy any new information: pending outcomes are in the adversary's state, while the controller sees them only at release.

## Prior-art boundary and decision

Robust finite-state controller verification for partially observed uncertain models is established by Cubuktepe et al., AAAI 2021; see [`switching_robust_fsc_reduction_audit_v1.md`](switching_robust_fsc_reduction_audit_v1.md). Their robust verification already supplies the general product-state idea. This delayed-risk derivation is a contract-matched verification reference, not a new theorem claim or acquisition algorithm.

The still-open contribution would have to optimize a shared FSC for economic HMM cost while enforcing the distinct causal-null reachability constraint and prove a useful utility/regret approximation to the unrestricted extensive-form oracle. A finite-memory search, risk DP, or sequential-convex solver alone does not pass G1/G2. No efficacy or real-data run follows from this check.
