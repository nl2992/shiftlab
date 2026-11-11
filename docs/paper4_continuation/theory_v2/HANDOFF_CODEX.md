# Handoff to Codex — Paper 4 theory_v2 salvage (written 2026-11-11 04:05 EST by Claude, lead)

## Where to work

- Worktree: `/Users/nigelli/Desktop/ICML/Shift-lab/.claude/worktrees/shiftlab-methods-strategy-dba13e`
- Branch: `research/paper4-causal-premium-theory-2026-11-10` (pushed to origin). Push **this branch only**; never
  push to or merge into `main`.
- This branch's `AGENTS.md` also describes a separate Codex lane on another branch. For this task the user's Paper 4
  directive governs: continue here, on this branch.
- Rules that bind every outcome (`AGENTS.md`, "Publication-outcome rule"): **never suggest a workshop paper or short
  note**; decisions are main-track GO / CONDITIONAL GO / NO-GO only; a falsified conjecture or negative result is
  evidence, never a finding.
- Machine load: at most 3 concurrent solver processes. The user asked for gentle load.

## What is running (detached; survives agent sessions)

| Process | What | Check |
|---|---|---|
| `scripts/paper4_continuation/theory_v2/wpM_supervise.sh` (own process session) | Restarts `wpM_scaling.py` from its partial file if it dies before writing outputs; when outputs exist, runs the summariser and exits. Holds idle sleep off. Never commits | `cat outputs/paper4_theory_v2/wpM_supervise.log`; `pgrep -fl wpM_supervise` |
| `wpM_scaling.py` (P3 certified numerics, 2 workers, `nice 10`, `WPM_PRI=v2`, 3 h budget per launch) | 1,512 planned cells; ~300 done at 04:01 | partial: `/private/tmp/claude-501/-Users-nigelli-Desktop-ICML-Shift-lab--claude-worktrees-shiftlab-methods-strategy-dba13e/06bf436b-d27c-42d6-9116-89f769a07352/scratchpad/wpM_partial.jsonl` (`wc -l`); logs: that scratchpad's `wpM_run2.log`, or `outputs/paper4_theory_v2/wpM_scaling_run.log` after a supervisor relaunch |

Outputs when it ends: `outputs/paper4_theory_v2/wpM_scaling_v1.json` (exact, gitignored),
`docs/paper4_continuation/theory_v2/results/wpM_scaling_v1_compact.json`, and `docs/paper4_continuation/theory_v2/MIXING_SCALING.md`
(written by the supervisor). Commit the compact JSON and the summary; keep the exact file out of git.
To stop everything: `pkill -f wpM_supervise.sh; pkill -f theory_v2/wpM_scaling.py`.
Caveat: the user re-enabled sleep (`SleepDisabled 0`). A closed lid pauses the run; it resumes on wake, and the
supervisor relaunches if needed.

## State of the salvage (read `SALVAGE_PLAN.md` first; its criteria are locked)

| Step | Status | File |
|---|---|---|
| Correction + reopening of the earlier NO-GO | done | `PUBLICATION_DECISION.md` ("Reopened") |
| P1 proofs | **M1** (B = 1: ρΓ α-free, uniform in T, limit (1−r)/2) and **M4** (B = 2, k = 0, small c: liminf ρΓ ≥ (1−r)/(2(3+r))) PROVED by agent, **not yet reviewed**; general B CONJECTURED | `MIXING_PREMIUM_THEOREM.md` |
| P2 review of Thm A/V (vanishing at t = 1) | done: accepted with fixable gaps; ADAPT wording wrong | `REVIEW_GENERAL_B.md` |
| P3 numerics | running (above) | `MIXING_SCALING.md` when done |
| P4 novelty | done: two-regime statement not found in prior art; conditions for novelty listed | `PRIOR_ART_TWO_REGIME.md`, plan erratum |
| P5 review of M1–M5 | **in progress or interrupted**: a Claude subagent was writing `REVIEW_MIXING.md`; partial red-team outputs exist (`scripts/.../rev3_mix_lib.py`, `rev3_mix_redteam.py`, `results/rev3_mix_b1_v1.json`, `rev3_mix_b2_v1.json`) | `REVIEW_MIXING.md` (may not exist) |

**If `REVIEW_MIXING.md` does not exist:** run a fresh adversarial correctness review of M1–M5 in
`MIXING_PREMIUM_THEOREM.md` (obligation ledger, counterexample red team on ≥ 150 certified cells with
`scripts/paper4_continuation/theory_C/gamma_lib.py::gamma_cell`, an independent implementation that does not import
`wpM_*`). Key risks: whether M3's first-label null is valid against plans that re-time or skip the first query, and
the T → ∞ interchange in M4.

## Numbers so far (certified; α = 1/10, k = 0, d = 1; ρΓ = Γ/(C₀ − V*_IID), C₀ = T/2)

| t | B = 1 | B = 2 (T → 15) | B = 3 (T → 12) | B = 4 (T → 12) |
|---|---|---|---|---|
| 2/3 | 1/3 for all T | 0.25 → 0.200 (flat) | 0.21 → 0.145 (falling slowly) | 0.17 → 0.125 (falling) |
| 3/4 | 0.25 | 0.33 → 0.144 (~flat) | 0.28 → 0.149 (falling) | 0.29 → 0.229 (falling) |
| 9/10 | odd T 0.10 | 0.44 → 0.173 (falling) | 0.49 → 0.355 (falling) | 0.51 → 0.444 (falling) |

d = 3 reproduces d = 1 shifted by two steps. ρΓ is identical at α = 1/20 and 1/10.

## How to finish (decision procedure)

1. Wait for `MIXING_SCALING.md`; check two or three cells exactly with `gamma_cell` (e.g. t = 3/4, B = 3, T = 12,
   α = 1/10). Commit and push.
2. Ensure `REVIEW_MIXING.md` exists (above). Commit and push.
3. Apply `SALVAGE_PLAN.md` criteria **verbatim** and append a dated section to `PUBLICATION_DECISION.md`:
   - CONDITIONAL GO needs M1 and M4 accepted by review, S-2 reviewed (done), **and** P3 showing ρΓ flat in T for
     B ≤ 4 in all three t values. At 04:01 the B = 3, 4 and t = 9/10 series were still falling at the largest T, so
     this clause was **not met** on the data so far.
   - NO-GO needs a certified collapse (by more than half beyond T = 12 in every family), a counterexample at B ≤ 2,
     or prior publication. Not met so far.
   - If neither applies cleanly, record exactly that, the met and unmet clauses, and the single obligation:
     **a general-B lower bound on ρΓ uniform in T** (it would settle both the B ≥ 3 horizon question and the
     general-B gap). Do not soften the outcome.
4. Update `NEXT_ACTION.md`, `RESEARCH_LEDGER.md` (append-only), `THEOREM_REGISTRY.md` (append rows for M1–M5) and
   `EXPERIMENT_RESULTS.md`; commit and push after each finished piece.

## Update 2026-11-11 (P5 finished)
`REVIEW_MIXING.md` exists: M1, M2, M3, M5 ACCEPTED; M4 ACCEPTED WITH CORRECTIONS (scope: k = 0, odd d,
c < g r^d/(16(1+r)), T ≥ T₀ — T₀ = 6 at t = 2/3, 10 at 3/4, 21 at 0.85, 37 at 9/10; not "uniform in T" outright).
M1 needs α ≤ 1/2 (ρΓ drops at α = 3/4). M3 holds only in the symmetric stationary family. 312 certified cells, no
counterexample. Remaining: the P3 summary, then the decision (step 3 of "How to finish"), stating M4 with these
qualifiers.
