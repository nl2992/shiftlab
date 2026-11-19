# theory_v2 — next action

**State (2026-11-11):** programme complete; publication decision **main-track NO-GO (existing results too narrow)**,
see `PUBLICATION_DECISION.md`. No manuscript work.

Only these would reopen a main-track route. Each needs the user's approval and a new locked protocol:
1. **Non-vanishing relative premium for t < 1.** A proof that Γ/(C₀ − V*_IID) stays ≥ c > 0 as T and B grow in
   a stochastic anti-persistent or persistent family. At t = 1 it provably vanishes (Thm A/V, unreviewed), so this
   is expected to fail; attempt it only with a new mechanism in hand.
2. **Lemma S+** (static alternative, c > 0, B ≥ 2 ⇒ Γ = 0). Proving it extends S0 but stays inside known machinery;
   on its own it would not change the decision.

Housekeeping if the branch is kept:
- Independent review of Thm A, Thm V and Lemma A (`GENERAL_B_PREMIUM.md`).
- Carry-over from the earlier phase: D4 pending-asymmetry value test (`FALLBACK_SCREENS.md`), unblocked.
- The full exact scaling output is at `outputs/paper4_theory_v2/wpC2_relative_premium_v1.json` (gitignored, local
  only).
- Do not merge this branch into `main` automatically.

## Superseded 2026-11-11
Item 1's "expected to fail" for t < 1 is withdrawn: the committed data show a T-flat relative premium in mixing
anti-persistent chains. The live plan is `SALVAGE_PLAN.md`; the decision is reopened.

## Current (2026-11-11 04:05)
See `HANDOFF_CODEX.md`: a detached supervisor finishes the P3 run; remaining steps are the P5 review (if not done),
the scaling summary, and applying the locked `SALVAGE_PLAN.md` criteria.

## Continuation (2026-11-12)

The user authorized continuing the registered numeric extensions with a looser milestone. Do not change the
locked `SALVAGE_PLAN.md` decision thresholds based on this amendment.

- Completed certified B=2, T=16 cells at `t ∈ {2/3, 3/4, 9/10}`; results and interpretation are appended to
  `MIXING_SCALING.md` and `CLAIMS_FROM_RESULTS.md`. All are positive and above half their T=12 baselines; t=9/10
  continues to decline and T=16 is below M4's `T0=37`.
- The corrected B=4 retry timed out again for `t=2/3` at 3,600 s; `t=3/4` was not run. Do not report a B=4 value.
- A targeted certified B=2, T=17, `t=9/10` cell is running in one low-priority worker (3,600 s cap):
  `scripts/paper4_continuation/theory_v2/wpM_b2_t17_t9.py`; partial/output paths are recorded in
  `EXPERIMENT_MANIFEST.md` and `RESEARCH_LEDGER.md`.

When the cell completes, append its certified result and recompute the finite-horizon comparisons. Finite extension
cells alone do not establish uniformity in T. The reviewed theorems below are proof results; the pending in-region
cell is only a consistency check. Preserve the open decision until the locked criteria are evaluated.

## 2026-11-12 proof update

The independently reviewed B=3 through B=6 theorems are now recorded in `MIXING_PREMIUM_THEOREM.md` and fully
proved in `B3_UNIFORM_PREMIUM_PROOF.md` through `B6_UNIFORM_PREMIUM_PROOF.md`. On
`r in (1/200,1/100)`, `g in (2/5,1/2)`, `d=1`, `c=k=0`, and `alpha=1/10`, they give
`rho_Gamma(T)>=19/101>0.18` at B=3, `>=13/84>0.15` at B=4, and `>=40/303>0.13` at B=5, for every `T>=16`;
at B=6, `rho_Gamma(T)>=13/118>0.10` for every `T>=20`. They do **not** meet the locked general-budget GO
criterion for all budgets, but Corollary M10 combines M1/M4/M6–M9 into the explicit range `1<=B<=6`,
`T>=20`, `rho_Gamma>=0.10`; its separate same-family review accepted it. This meets the plan's bounded-budget
S-1 form with `Bbar=6` on the stated rectangle, while B>=7 and growing-budget uniformity remain outside scope.
The one in-region certified B=3 cell is running to check consistency. The low-priority B=2 T=17 run completed;
rho fell 5.12% from T=16 and remains below M4's T0=37. Do not extend the bounded-range claim beyond B=6 or
alter `SALVAGE_PLAN.md`; evaluate the remaining P3/P4 GO conditions after the cell completes.

## 2026-11-12 continuation in isolated Codex checkout

- P4 focused novelty review now says **PROCEED (6/10)** with no exact overlap found; see
  `NOVELTY_REVIEW_2026-11-12.md`. The result's defensible claim is the bounded-budget HMM decision-value
  separation. Do not call it an outcome-adaptivity premium without comparing an intermediate null class.
- The B=3, T=16 consistency cell is running in the isolated Codex worktree, under its own `.venv`, at
  nice 18 and with a 3,600 s cap. No result is written yet. Sleep remains enabled.
- Next proof target: the fresh arbitrary-fixed-B extension. Verify subset-moment remainders uniformly over
  adaptive histories and query gaps, the extended witness timing/gains, and explicit `r_0(B), T_0(B)` before
  making a theorem claim. This is a per-fixed-B direction and does not by itself cover growing B.
- Preserve the open publication decision and locked salvage thresholds until the numeric check and proof audit
  are complete.

## 2026-11-13 current state

- The B=3, T=16 consistency run inside the M6/M10 rectangle **timed out at 3,600 s**. It is outside M11's
  smaller B=3 radius, so it is not an M11 consistency check. Its artifact is a timeout record, not a certified
  cell; do not claim numerical reconciliation from it.
- The arbitrary-fixed-B theorem is recorded in `B_GENERAL_FIXED_PREMIUM_PROOF.md`; its fresh
  same-family adversarial audit returned PASS with no issues. See
  `B_GENERAL_FIXED_PREMIUM_PROOF_AUDIT_2026-11-13.md`. Treat the acceptance as provisional; cross-family review
  is still unavailable in this checkout.
- Next, reconcile the audited statement with the locked GO clauses and any certified data in its parameter
  region. The B=3, T=16 run timed out, so it supplies no consistency value. Preserve the open decision and do not
  claim a common positive bound for unbounded B: the proved candidate's radius and relative lower bound both
  depend on B.
- Keep the machine's existing sleep behavior unchanged.
