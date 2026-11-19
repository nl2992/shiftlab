# RB-DP: risk-budget dynamic programming for causal-null-safe budgeted promotion

**Date:** 2026-11-13. **Lead:** Fable 5.2 (plan, verification). **Builders:** Sonnet subagents.
**Branch:** `codex/paper4-causal-premium-continuation`. Nothing here is pushed or merged.

## Why this direction

Paper 4 so far has (i) an exact solver (FCG) that stops at T ≈ 10–16 because it enumerates the learner tree, and
(ii) theorems M1–M11 showing causal-null safety costs a positive fraction of the value of information. What is
missing is an algorithm a practitioner can run. Candidate F (`risk_preserving_approx/CANDIDATE_F_*`) proposed a
planner over (belief, capital) and was shelved before implementation because no optimality statement was in hand.
This plan supplies the statement and builds the planner.

User directive (2026-11-13): aim for a positive algorithmic contribution; caveats and weaknesses are acceptable and
get reported, but a result is not discarded for failing a self-imposed bar.

## Claim to establish

For delay d = 1, any two-state HMM alternative and the causal null (queried-label conditional mean in [0, 1/2]):

**(R1, exact reduction)** `V*_causal` equals the value of a Markov decision problem on the state
(time t, alternative belief β, remaining budget n, **risk budget w**), where w is the worst-case probability of
ever promoting from here on. The same program with one constraint removed gives `V*_IID`.

- Promote now with private probability π, continue with budget w': `π + (1 − π) w' ≤ w`.
- On a query, split w' into (w0, w1) for the two label values:
  - causal null: `max(w0, (w0 + w1)/2) ≤ w'`  (the null picks p ∈ [0, 1/2]; the maximum is at p = 0 or 1/2);
  - IID null: `(w0 + w1)/2 ≤ w'`.
- **Correction (2026-11-13, found by the builder's first test):** the learner may also randomise at any node between
  continuation budgets or between query and no-query, so the value is the lower convex hull in w of the expression
  above. Without the hull the relaxed DP exceeded the exact optimum (L = 2.4461 > V*_causal = 2.44189 on T5 B2).
  With it, U equals the certified optimum to ≤ 1e-9 on all 20 (cell, mode) pairs checked (14 builder, 6 lead).
- So the premium Γ is exactly the price of the single constraint `w0 ≤ w'`: the risk budget may not grow after a
  negative label.

Proof sketch: Kuhn equivalence makes behavioural strategies on the public learner history sufficient; the
worst-case risk-to-go of a behavioural strategy obeys the recursion above because the null class is rectangular;
any w satisfying the inequalities upper-bounds the true risk-to-go; cost-to-go depends on the history only through
(t, β, n, w). The belief-alias counterexample (`switching_alt_belief_risk_alias_counterexample_v1.md`) is why β
alone fails; w is the missing coordinate.

**(R2, certified sandwich)** On grids (β linear interpolation, w grid of step δ):
- U: restrict all risk budgets to the w grid, extract the policy, evaluate its alternative cost exactly on its own
  forward tree (≤ 2^B label paths) and verify its worst-case risk by exact backward recursion on that tree. U is a
  true upper bound whatever the grid error.
- L: V is concave in β (interpolation underestimates) and nonincreasing in w (round up, relax the split
  constraint by δ). The relaxed DP is a lower bound.

**(R3, scale)** Cost O(T · B · N_β · N_w²) against the exponential tree. Target T in the hundreds, B up to 8+.

## Experiments

| ID | Question | Pass signal |
|---|---|---|
| E1 | Does RB-DP reproduce certified exact values? | certified `V*_causal`, `V*_IID` inside [L, U] on small d = 1 cells; U − L small relative to VOI |
| E2 | Does it scale where FCG does not? | wall time and gap at T = 16…200+, B = 1…8, incl. the B = 3, T = 16 cell that timed out at 3,600 s |
| E3 | What does the premium do at long horizons? | ρΓ(T) curves for t ∈ {2/3, 3/4, 9/10}, B = 1…8; agreement with M1/M4 closed forms; behaviour for B ≥ 3 |
| E4 | Is the policy better than what exists? | VOI of RB-DP vs IID-optimal (true causal risk reported), IID + repair, fixed-bet e-process gate, never-promote |

All cells are synthetic; no holdout or real data is opened. Caveats to state with results: d = 1 only (d ≥ 2 needs
a vector risk state over pending labels), two-state alternative, float arithmetic in the DP (U is evaluated on the
policy, not read from the DP table).

## Files

- `src/shiftlab/paper4/risk_budget_dp.py`, `tests/paper4/test_risk_budget_dp.py`
- `scripts/paper4_continuation/rbdp/`, results under `docs/paper4_continuation/rbdp/results/`
- `docs/paper4_continuation/rbdp/RESULTS.md`
