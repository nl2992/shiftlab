# Candidate A1 finite-grid complexity audit

**Date:** 2026-10-29. **Decision:** do not implement the proposed denominator-grid
planner in its current form. This is a complexity/no-go checkpoint, not a rejection
of all continuation approximations. It makes no synthetic or real-data efficacy
claim.

## Proposed construction under review

Candidate A1 retains the robust pre-promotion sequence-form game and replaces only
the known-alternative post-promotion exact belief DP with a denominator-`N`
probability-simplex grid. Its conditional transfer bound is
`L K T(T+1)/(2N)`, where `K=2^(q+1)` and `q=min(B,d-1)` is the maximum number of
pending binary labels. The proposed grid contains at most
`G=binomial(N+K-1,K-1)` points per public queue schedule, time, remaining budget,
and deployment state.

## Reproducible state-count arithmetic

The following are exact integer counts from the displayed binomial formula, not
runtime measurements. With delay one, `K=2`; at `N=4662` (the proposal's stated
minimum for a 0.01 cost bound at `T=6`, `L=1.11`) there are 4,663 grid points for
each time/budget/deployment context. At `T=6,B=3`, even the loose count over
`T*(B+1)*2=48` such contexts is 223,824 grid-context pairs before release
branches or transitions. The exact DP instead visits only beliefs reachable from
the finite observation histories, so no advantage follows from this count.

For `d=2,B=3`, `q=1`, `K=4`; at the same `N`, `G=16,909,250,380` points per
context. For growing delay/budget the
combinatorial term grows as `Theta(N^(K-1)/(K-1)!)`; since `K` is exponential in
`min(B,d-1)`, this is not a favorable uniform complexity bound. The exact
pre-promotion game is retained in full, so its XP dependence on `B` is unchanged.

These counts do not prove that a carefully chosen reachable grid, adaptive mesh,
or sparse interpolation cannot help. They do show that the current full-simplex
grid specification has not established the computational advantage required to
justify implementation. Any next version must compare explicit reachable-state,
transition and storage counts against the exact continuation cache and account for
the unchanged pre-promotion LP.

## Proof audit outcome

- **Risk invariance — PROVED conditionally:** post-promotion actions cannot alter
  the already determined first-promotion event, if the pre-promotion controller
  is fixed and unchanged.
- **Pathwise budget — PROVED conditionally:** the post-promotion controller must
  use the same remaining-rights state and reject queries at zero rights.
- **Value transfer — SKETCHED, not established:** a per-projection TV bound alone
  does not supply the required uniform comparison over all full-history policies.
  One needs a precisely defined reset model and a coupling that covers rounded
  transition/release branches, zero-grid-probability observations, policy
  randomization and every terminal cost. The grid policy's realized value is
  evaluated in the true model while its DP objective is in the reset model. The
  source document asserts this bridge but has not proved it.
- **Approximation of the unrestricted optimum — UNRESOLVED:** even with a valid
  continuation error bound, the pre-promotion robust LP remains exact and is the
  principal history-growth bottleneck. No end-to-end memory/time bound improves
  the reference.
- **Novelty — UNRESOLVED:** finite-grid POMDP approximation is established prior
  art; no source-matched reduction or distinct computational theorem is shown.

## Decision and next test

Retain A1 as a diagnostic baseline and do not spend compute on its naïve complete
simplex grid. Continue toward a candidate whose state construction is sparse by
proof (rather than by an assumed favorable reachable set), or a certified
approximate-optimization method that reduces the robust pre-promotion search.
Before another efficacy run, write down the candidate's end-to-end state/transition
complexity, prove policy transfer including off-support histories, and identify a
strong baseline it could beat. The pre-existing stronger calendar comparator and
all prior negative results remain in force.

## Provenance

Arithmetic was checked with exact Python integers using the formula above; the
command and outputs are recorded in `candidate_a1_complexity_audit_v1.json`.
No model data, outcomes, holdouts or seeds were read or generated.
