# Exact causal-null risk verifier for deterministic public-memory FSCs

**Date:** 2026-10-29. **Status:** reusable verification infrastructure; no method or novelty claim.

## Contract

The controller has finite deterministic memory updated only from public actions/queries and labels
released to the learner. It can request at most one binary label per event, with fixed delay `d`,
and has a pathwise hard cap `B` that counts pending requests. The causal-null opponent sees every
generated label immediately, including pending labels, and chooses each queried label's
conditional success probability in `[0,1/2]` after observing the full event history. The event of
interest is any promotion by the finite horizon `T`.

## Recursion

The evaluator state is `(t,z,b,p)`: event time, controller memory `z`, remaining query rights `b`,
and pending labels `p` with request/release times and outcomes. At event `t`, release all labels due
at `t` to the controller and apply its deterministic memory update. Then follow its action/query
choice. Promotion returns risk one. A non-query action advances deterministically. For a query,
the next-state risk is affine in the null success probability `q`; maximizing over `[0,1/2]`
therefore attains an endpoint, so the recursion takes the maximum of the `q=0` and `q=1/2`
continuations. The null can retain arbitrary past history, but once `(z,b,p,t)` is fixed, that
history changes neither the controller's future behavior nor the allowed next-label set. Thus this
state is sufficient for exact risk evaluation of the fixed deterministic public-memory controller.

The memoized recursion is implemented in
[`switching_fsc_risk.py`](../src/shiftlab/dive/switching_fsc_risk.py). Its cost depends on the
number of reachable product states; merging equivalent controller histories can be much smaller
than enumerating the full event tree, but worst-case growth is exponential in delay length and
controller memory bits. It evaluates risk for a fixed controller and does not optimize the
controller or establish approximation quality to the unrestricted oracle.

## Cross-checks

[`test_switching_fsc_risk.py`](../tests/test_switching_fsc_risk.py) compares the compressed
recursion with the existing full-history causal-game evaluator on two delayed policies:

- A two-positive promotion threshold with one-event delay has exact risk `1/4`.
- A nonmonotone XOR promotion rule with two-event delay has exact risk `3/4`, confirming that the
  verifier retains the null's advantage from seeing pending labels.

A third check verifies rejection of a controller that would exceed its pathwise query cap. The
focused tests and Ruff checks pass. These checks validate this verifier on representative finite
controllers; they do not prove a compression theorem for arbitrary controllers.

## Research consequence

Use this as a required policy-level risk evaluator for future finite-state candidates and for
Lagrangian-frontier recovery. A method still needs a source-audited acquisition/switching rule, a
nontrivial guarantee against the strongest scalable baseline, and evidence on the full declared
contract. The verifier supplies none of those claims. Historical evidence for promotion remains
distinct from current-regime value evidence after reversal.
