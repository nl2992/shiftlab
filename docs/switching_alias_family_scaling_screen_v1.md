# Scaling screen for the alternative-belief alias witness

**Date:** 2026-10-29. **Status:** exact counterexample to a naive growing-family memory lower
bound; no method claim.

## Proposed extension

Extend [`switching_alt_belief_risk_alias_counterexample_v1.md`](switching_alt_belief_risk_alias_counterexample_v1.md)
from two queried labels to `B` queries, all requested at rounds `1,...,B` with delay one and
charged at request time. Keep the incumbent through round `B+1`, after all labels are released,
then make one promotion decision and hold the selected policy for `H` rounds. Under the known
alternative, `Y_1=1` with probability `9/10` and `Y_1=0` with probability `1/10`; after round 1
the hidden state deterministically resets to a favorable state that emits `Y_t=1` for every
`2<=t<=B`. At the decision time the current alternative state is favorable on both supported
histories, so the alternative posterior aliases them. Let the promotion's gross deployment value
net of its switch charge be `G>0`; every policy below pays the same query cost `Bc`.

## Safe tests and scaling

For any causal null with conditional success probabilities at most `1/2`, the probability of `m`
specified consecutive positive labels is at most `2^{-m}`. Therefore the full-history test that
promotes with probability `min(1, alpha*2^B)` only when all `B` labels are positive is safe. Its
alternative promotion probability is

```text
P_full = (9/10) * min(1, alpha*2^B).
```

But the last `B-1` labels are also all positive under every alternative-supported history. A
controller that stores only one bit (`suffix_still_all_positive`) can safely promote with
probability `min(1, alpha*2^(B-1))` when that bit remains true. Its causal-null risk is at most
`min(1, alpha*2^(B-1))*2^{-(B-1)} <= alpha`, and its alternative power is

```text
P_suffix = min(1, alpha*2^(B-1)).
```

Both net values multiply their displayed powers by `G` and subtract the same `Bc`. At `alpha=1/10`,
the exact powers for `B=2,3,4,5` are respectively
`(9/25,1/5)`, `(18/25,2/5)`, `(9/10,4/5)`, and `(9/10,1)` for `(full,suffix)`. From `B=5`
onward the one-bit suffix policy promotes with probability one under the alternative while keeping
the global causal-null risk at most `1/16` (and decreasing thereafter). Hence no growing memory
requirement follows from this extension; an even simpler compact rule eventually dominates the
particular full-history witness.

The exact Fraction screen was run for `B=2,...,8` with
`uv run python scripts/check_switching_alias_family_scaling.py`; results are reproduced directly
by the two formulas above. It is a finite algebra check, not a simulation or a theorem about the
unrestricted oracle.

## G1 consequence

This rejects the naive plan to grow the existing posterior-alias example by appending labels from a
deterministic favorable regime. Each appended positive creates a new risk-cheap trigger and destroys
the value of remembering the aliased prefix. Any future finite-memory lower bound must compare
against *all* later trigger opportunities and compact event summaries, and it must preserve
reversible decisions while other queried outcomes are pending. A two-history alias or an
alternative-posterior-only gap is not enough. The overall G1 gate remains open.
