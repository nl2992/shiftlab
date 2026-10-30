# Candidate G scalarized-DP end-to-end screen

**Registered:** 2026-10-29 before implementation or execution. One deterministic
development screen on the already exposed synthetic instance. This protocol
tests an implementation-level computational hypothesis for an established
constrained-POMDP reduction; it is not a novelty or confirmation protocol.

## Hypothesis and frozen instance

On `T=10, B=4, d=2, alpha=1/10`, symmetric HMM transition `1/10`, emissions
`(1/50,49/50)`, prior `1/2`, query fee `1/100`, and switch fee `1/10`, a
scalarized Bellman solver on the exact 4,867-state hidden-root belief graph may
return a full-null-feasible policy at materially lower end-to-end cost than the
existing IID relaxation pipeline. The existing Candidate B output and exact
decomposed oracle are read-only comparators. No new seeds, parameter cells, real
rows, CRSP data or holdouts are used.

## Fixed algorithm

1. Build the exact rational reachable-belief graph using the state semantics in
   `CANDIDATE_G_IID_BELIEF_COMPRESSION_PROTOCOL_V1.md`: hidden root mode,
   alternative regime and pending outcomes/release times, event time, remaining
   query rights and deployment. Preserve request-time charges and release only
   due labels.
2. Solve the scalarized Bellman problem for the fixed multiplier grid
   `{0, 1, 2, 4, 8, 16, 32}`. Use exact rational transition/reward arithmetic and
   deterministic tie-breaking: incumbent/no-query, incumbent/query,
   promote/no-query, promote/query, in that order where legal. Do not consult
   the exact oracle's dual multiplier to select policies or refine the grid.
3. For each returned deterministic policy, independently compute exact
   alternative cost, IID risk and full-history causal-null risk. Compute its
   Lagrangian lower bound `min(C + lambda*R_iid) - lambda*alpha`. Safety-repair
   each policy by the registered root lottery with never-promote if its robust
   risk exceeds alpha; recompute exact cost and risk after repair.
4. Select the least-cost repaired policy with robust risk at most alpha. Also
   form exact root mixtures between adjacent grid policies only when their
   robust risks bracket alpha; validate those mixtures independently. Count
   all graph, solve, extraction, verification and repair time and peak RSS.

## Baselines and pass/fail rules

Compare to these already recorded results on precisely this cell:

- Candidate B IID-LP + exact certification: cost `51237636737353/12207031250000`,
  robust risk `1/10`, 13,421 learner variables, 114.845 seconds end to end.
- Decomposed exact robust oracle: same exact recovered cost and risk, 58.014
  seconds end to end; it is an optimum comparator, not a policy the candidate
  can beat economically.
- Best registered fixed calendar `[1,2,3,4]`: cost
  `20670239089321/4882812500000` (about `4.2332649655`), robust risk `1/10`.

All of the following are required to pass this screen:

- exact graph count and policy invariants match the registered model;
- independently verified robust risk is at most `1/10`, and all paths use at
  most four queries;
- repaired candidate cost is strictly below the exact best-calendar cost;
- end-to-end runtime, including exact verification and repair, is at most half
  the 58.014-second decomposed reference runtime;
- a valid lower/upper interval is reported; no unsupported claim of exact
  constrained-optimum recovery is made from a finite multiplier grid.

If any condition fails, preserve all output and close the scalarized-DP route.
Passing establishes only a one-cell implementation-level computational screen
on the IID-relaxation pipeline. It does not pass G1–G3, prove a general runtime
bound, or authorize real-data analysis.

## Artifacts and provenance

Implement in new branch-local files only. Write the output once to
`docs/risk_preserving_approx/candidate_g_scalarized_dp_screen_v1.json`; refuse
to overwrite it. Record this protocol hash, runner hash, source hashes, baseline
artifact hashes, exact multiplier values, all policy metrics, timing, peak RSS,
solver/library versions, proof status, failures and final continue/close
decision. Do not alter prior protocols or results.
