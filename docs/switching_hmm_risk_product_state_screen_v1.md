# G1 screen: joint HMM and causal-null product state for a fixed FSC

**Date:** 2026-10-29. **Status:** exact representation for a supplied FSC; no new compression or synthesis result.

## Claim and contract

Fix a finite-state HMM alternative with `N` hidden states, a deterministic public-memory controller with `M` memory states, finite observable context/action alphabets, horizon `T`, fixed label delay `d`, and pathwise request cap `B`. Each event follows the registered order: release due labels, update FSC memory from released labels, observe current context, choose query/deployment action, reserve query rights, generate a queried label, charge query/switch costs. The causal-null branch sees each generated queried label immediately and chooses its conditional Bernoulli parameter in `[0,1/2]`; the learner sees it only at release. The same FSC is used under the HMM and null branches.

**Proposition (fixed-controller product-state evaluation).** For this contract, the HMM expected cumulative cost of a fixed FSC is computed by a finite recursion on

`(t, hidden_state, FSC_memory, incumbent_action, remaining_budget, pending_queue)`.

Its worst causal-null probability of any promotion is computed by a separate recursion on

`(t, FSC_memory, incumbent_action, remaining_budget, pending_queue, promoted_flag)`.

The queue has at most `3^d` configurations when each of the `d` release slots is empty or contains a pending binary label. The HMM recursion has at most

`O(T * N * M * 2 * (B+1) * 3^d)`

product states, up to context and action branching. The null recursion omits the HMM state; at a query, its Bellman backup maximizes the affine continuation value over the endpoints `q=0` and `q=1/2`. In both branches, pending outcomes are evaluator state and are withheld from the FSC until their release time. The controller is shared: its update/output maps are identical in the two recursions.

**Proof.** Under the alternative, the augmented state is Markov because the HMM state determines the next hidden-state and label distributions, the FSC memory determines future controller outputs from future releases, and the explicit queue determines which outcomes become available and when. Budget and incumbent are sufficient to enforce request reservation and charge switching. Under the null, conditional on the full augmented state, the only uncertain transition after a query is its binary outcome with parameter `q in [0,1/2]`. The continuation promotion probability is affine in `q`, so its maximum is attained at an endpoint. The full null history affects neither the fixed FSC's future behavior nor the allowed next `q` interval once the actual pending outcomes and FSC state are included. Thus the listed states are sufficient for exact evaluation of this fixed controller.

## What this answers—and what it does not

A finite statistic does replace full histories **for evaluating a supplied FSC**. The null-visible pending queue is essential; alternative HMM belief alone is not enough, and pending labels must not leak to the learner. This representation does not give a finite state independent of controller memory, nor does it construct a good FSC. Searching over FSC transition/output maps is nonconvex and can be exponential in `M`; the displayed product bound concerns verification of one controller, not optimization over the joint economic-cost/null-risk frontier.

## Source-level decision

This is already the standard product-state/finite-controller reduction audited in
`switching_robust_fsc_reduction_audit_v1.md`, with its null branch implemented in
`src/shiftlab/dive/switching_fsc_risk.py`. Cubuktepe et al., *Robust Finite-State Controllers for
Uncertain POMDPs* (AAAI 2021), formulate robust finite-state controller verification and search;
the source audit records the model, algorithm and proof sections. The HMM product adds an ordinary
finite Markov state for alternative-cost evaluation. No evidence here establishes a two-law
compression theorem, a globally useful controller optimizer, or a value/regret advantage over the
sequence-form oracle. This route therefore fails G1 as a method contribution and is retained only
as a verifier/reference contract.

Any continuation must find a policy family whose controller memory is itself bounded or
constructible with a theorem-level approximation to the unrestricted alpha-safe frontier. Merely
combining an HMM filter, e-wealth, pending queue and FSC risk recursion is a state augmentation,
not a new algorithm. A historical promotion-risk certificate remains distinct from current
challenger value after a regime reversal.
