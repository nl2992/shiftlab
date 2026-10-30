# Candidate J: finite-controller exact risk certification with lower-bound stopping

**Date:** 2026-10-30. **Status:** theorem target for a bounded prototype;
G1 unresolved. **Do not claim a new synthesis algorithm.**

## Target and procedure

Search a class of deterministic finite-state learner controllers with `K`
memory states. Each controller emits deployment/query actions from its memory,
time and newly released labels, and updates memory using public actions and
released labels. It must enforce the hard query cap on every path. Root mixtures
may combine controllers, but every component is verified against the full
causal null.

For a candidate controller:

1. Compute its exact worst-case first-promotion risk by backward induction on
   the product of controller memory, time, remaining budget, deployed action,
   and the null-visible pending-label queue. At each queried event maximize over
   endpoint null probabilities `0` and `1/2`. A deterministic controller makes
   its memory reconstructible from the null-visible public history; histories
   that reach the same product state have identical continuation games.
2. Compute alternative expected cost on the analogous product with the finite
   alternative HMM state and pending queue.
3. Keep feasible controllers or apply a separately verified root-mixture repair.
   Compare the best feasible controller cost `U` with Candidate B's valid IID
   relaxation lower bound `L`. If `U-L <= epsilon`, return a full-oracle
   `epsilon`-optimal, exactly risk-feasible policy. Otherwise continue controller
   search; no gap claim follows merely from small `K`.

This is an anytime certificate framework, not yet an efficient controller
optimizer. A finite exhaustive search through all finite-history controllers
eventually contains an unrestricted finite-horizon optimum, but may be as large
as the original tree. The candidate only has practical value if exact response
evaluation plus a structured controller search closes the bound before that
point.

## Conditional verifier theorem and complexity

**PROVED target.** For a fixed deterministic controller and finite horizon,
fixed delay `d`, pathwise request budget `B`, and null conditional positive
probability in `[0,1/2]`, the recursion described above returns its exact
worst-case probability of ever selecting action 1. The null's full history
adaptivity is preserved: once the controller state, pending queried outcomes,
time, budget and deployment are fixed, that history cannot alter legal future
endpoint choices or the learner's future behavior. For finite-horizon reachability
in the resulting fully observed controlled state, a Markov endpoint best
response attains the maximum. This does not grant the null less information;
pending values are included because the null sees them.

With `Q_d = sum_{j=0}^{min(B,d-1)} binom(d-1,j) 2^j` possible pending
queues at a decision boundary, the risk verifier visits at most
`O(T K (B+1) 2 Q_d)` product states, with constant endpoint branching. The
alternative cost evaluator adds the finite HMM state count and the legal
controller action branching. Rational arithmetic has bit complexity dependent
on the input probabilities. These are verifier bounds only; controller search,
lower-bound construction, root mixing and verification overhead must be reported
separately.

**PROVED conditional stopping certificate.** If `L` is a valid lower bound on
the unrestricted risk-constrained optimum (the IID relaxation is one such
lower bound) and an independently evaluated returned policy has exact cost
`U` and full-null risk at most `alpha`, then its full-oracle gap lies in
`[0,U-L]`. This is an a-posteriori certificate; it does not bound how much
search is needed to find such a policy.

## Prior art and counterexamples

Finite-state-controller synthesis and robust verification are established; see
Cubuktepe et al., [AAAI 2021](https://ojs.aaai.org/index.php/AAAI/article/view/17401).
The product-state risk recursion is finite-horizon reachability in a controlled
Markov model after fixing the controller. Candidate B already supplies the IID
lower bound and root safety repair. The possible distinction is an exact,
compact best-response verifier for the full-history causal null combined with
an a-posteriori unrestricted-optimum certificate. This may still reduce to
standard robust FSC synthesis plus model checking; **UNRESOLVED — EXACT
REDUCTION REQUIRED**. It is not a G1 pass.

Required falsification checks: posterior-aliasing controller states must remain
distinct; preserve signed alternative continuation costs; do not collapse
pending labels before release; verify rollback and re-promotion costs while
stopping risk at first promotion; and test the null response conditioned on a
label still pending to the learner. Randomized internal controller memory is
excluded from the exact theorem unless represented as a root mixture of
deterministic controllers with branchwise verification.

## Go/no-go criteria

First implement only the exact fixed-controller verifier and compare it to the
independent full-history null recursion on registered small controllers. Then
audit whether robust FSC synthesis or standard product-MDP verification already
gives the same procedure. Proceed to a controller-search pilot only if (i) the
source audit identifies a defensible distinction, and (ii) candidate generation
can be bounded and the IID lower bound can certify a meaningful gap with less
end-to-end work than the decomposed oracle. Synthetic efficacy and real data
remain gated by G1–G3.
