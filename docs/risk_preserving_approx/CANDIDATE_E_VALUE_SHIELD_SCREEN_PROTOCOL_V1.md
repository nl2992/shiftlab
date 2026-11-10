# Candidate E value-shield screen (value-sensitive pruning): protocol v1

**Registered:** 2026-11-09, before any run of this screen. **Branch:** `research/paper4-value-shielded-causal-planning`.
**Status:** development-only structural screen. It does not solve any pruned problem, does not
measure cost gaps against an exact optimum on the stress cell, and cannot establish novelty.

## Why this screen

The mass-envelope screen (`candidate_e_pruning_feasibility_v1.json`, commit `575a73b9`) selects
histories by exact alternative probability. It failed its registered rule: every depth and both
budgets remain below 5% prunable realization columns (maximum 5/122). That screen did not test the
value-sensitive selection rule of the Paper 4 directive:

    D(h) = W(h) - J_lower(h),

where `W(h)` is the expected alternative cost of permanent incumbent deployment with no further
queries from public history `h`, and `J_lower(h)` is a certified lower bound on the free continuation
optimum `J_free(h)` (cost with the promotion constraint removed). Its per-history theorem gives loss
at most `delta * P(reach S)` at uniform tolerance `delta`, with no mass envelope.

## Frozen case

The registered T=10 stress cell, identical to the mass screen: `T=10`, `B=4`, `d=2`,
transition `1/10` both ways, emissions `(1/50, 49/50)`, prior `1/2`, `alpha=1/10`,
query fee `1/100`, switch fee `1/10`. The exact public-history enumeration uses the same
`CausalSwitchingGame` primitives (`information`, `choices`, `model.propagate`, `model.emission`).

## Quantities (exact `Fraction` arithmetic)

For each exact public pre-promotion history `k` (all actions so far equal 0), with decision time `t`:

1. Posterior of the cost-generating state, conditioned on the public key only (pending labels
   marginalised): `Q_t(k) = P(s_t = 1 | k)`, computed as `B_k / A_k` where `A_k` sums path weights
   over alternative transcripts consistent with `k` and `B_k` sums the same weights times
   `propagate(posterior, 1)`. Learner action probabilities are constant within a key and cancel.
2. `W(k) = sum_{t'=t}^{T} emission(Q_{t'})`, with `Q_{t'+1} = propagate(Q_{t'}, 1)`, the incumbent
   playing action 0 with no queries and no switching.
3. `J_lower(k) = sum_{s in {0,1}} P(s_t = s | k) * V(t, s, old = 0)`, where
   `V(t', s, a_old) = min_a [ c(a, s) + switch_fee * [a != a_old] + sum_{s'} P(s' | s) V(t'+1, s', a) ]`,
   `c(0, s) = emission(s)`, `c(1, s) = 1 - emission(s)`, `V(T+1, ., .) = 0`, and queries are removed.
   Justification: the relaxed learner observes the cost-generating state and can simulate any
   original learner's label-dependent behaviour by its own randomisation, so its optimum is at most
   `J_free(k)`. Dropping queries only weakens the relaxed learner, and the relaxation remains a lower bound.
4. `D(k) = W(k) - J_lower(k)`. The screen asserts `D(k) >= 0` and `J_lower <= W` for every key.

## Selection and metrics

For `delta in {1/100, 1/20}`: `S_delta = {k : D(k) <= delta}` (first-entry: a selected key prunes its
subtree, and only keys with no selected proper ancestor count as entries). Report, per `delta`:

- number of entry keys and collapsed public histories,
- pre-promotion realization columns removed and the fraction of the total,
- the theorem loss bound `delta * P(reach S)` under the screen's own convention, reported as `delta`.

Column counting reuses the mass screen's convention, so fractions are comparable.

## Validity checks (must pass before the metrics are interpreted)

- Every key: `0 <= J_lower(k) <= W(k)` and `D(k) >= 0`.
- Lower-bound sanity on the exact cell `T=5, B=2, d=1` (transition `1/4`, emissions `(1/20, 19/20)`,
  `alpha=1/10`, query `1/100`, switch `1/10`): `J_lower(root) <= V_free`, where `V_free` is the exact
  reference optimum with the risk constraint removed (`alpha=1`). A failure stops the screen.

## Decision rule (locked in advance)

- **Mechanism pass for a solver:** not possible from this screen alone. Passing the rule here
  authorises only a separate protocol for certified region construction (Work Package C). It does
  not authorise implementation.
- **Fail:** if at every `delta` the maximum removed-column fraction is below 5%, the value-sensitive
  selection rule is recorded as failed at this cell, and no solver is built.
- **Stop regardless (paper-level stop condition):** the screen enumerates the full public
  pre-promotion tree to compute `W` and `J_lower`. Any implementation that needs this enumeration
  merely to identify safe regions is stopped by the directive. This is recorded in the report
  whatever the metrics say.

## Out of scope

No threshold tuning, no new seeds, no T=6/T=8 reruns beyond the sanity check, no LP solves on the
stress cell, no holdouts, no real data, no CRSP.
