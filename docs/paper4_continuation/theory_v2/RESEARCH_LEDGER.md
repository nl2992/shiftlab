# theory_v2 research ledger (append-only)

## 2026-11-10 — start
- Fetched origin; Paper 4 branch HEAD `b1215242` (not `76b9f744`). Created and pushed
  `research/paper4-causal-premium-theory-2026-11-10` from it, in worktree `shiftlab-methods-strategy-dba13e`.
  The worktree `failure-atlas-v2-sota-195428` (session "Risk-preserving approximate optimization", idle) still holds
  the old branch and a running A3 campaign; it is left untouched.
- ARIS: skills present under `.agents/skills/` (research-pipeline, novelty-check, proof-checker, proof-orchestrator,
  experiment-plan, research-review, result-to-claim). No `.aris/reviewer.json`; no Codex/Grok/Antigravity/claude-review
  tools loaded ⇒ BL-1 persists; all reviews same-family / provisional.

## 2026-11-10 (afternoon)
- 03:48 EST: launched WP-A (Opus auditor), WP-B, WP-C (Opus theory), WP-F (Sonnet retrieval), WP-E (Sonnet auditor).
  All five stopped on the account's 5-hour usage limit before writing any file (HTTP 429). Resumed at 12:50 EST
  from their saved transcripts; no partial outputs existed. The A3 campaign process had ended by then, so the
  quiet-CPU restriction was lifted.

## 2026-11-10 — WP B (multi-label zero premium), agent report
- PROVED Theorem S0: static alternative, c = 0, any B, d, k, prior, alpha => Gamma = 0. The proof uses the calendar
  reduction plus an induction on the closed G/D recursions. Audit: 254 cells, 0 violations.
- FALSIFIED Z2 / U-M / "TP2 + multi-label W". Counterexample CE-B1: T=5, B=4, d=1, t=1/10, e=(1/100,99/100), prior 1/2,
  c=k=0, alpha=25/32, Gamma in [0.00209251952, 13078247/6250000000]. Certified two ways: by gamma_cell, and
  independently by the wpB_dual_check lower bound.
- OPEN: static with c > 0 (Lemma S+). 0 failures in 29,297 cells.
- Details: `MULTILABEL_ZERO_PREMIUM.md`. Nothing committed.

## 2026-11-10 20:28 EST — paused at the user's request
- Done and pushed: WP-A audit, WP-B (S0 proved; Z2 falsified incl. α ≤ 1/2), WP-C (SP1), WP-D, WP-E, WP-F audit,
  reviews (S0, SP1, novelty, significance), REVIEW_REPORT, registry update.
- The relative-premium scaling run (`wpC2_relative_premium.py`, descriptive) was stopped mid-run; its partial file
  was written to a temporary path that could not be recovered, so it restarts fresh at 22:02 with 3 workers and a
  partial file in the session scratchpad. The script is committed with that restart.
- Remaining: scaling results, PUBLICATION_DECISION.md, EXPERIMENT_RESULTS.md, NEXT_ACTION.md.

## 2026-11-10 ~20:50 EST — scaling run restarted; decision rule locked before seeing its data
- Run: `wpC2_relative_premium.py`, 1,808 cells, 3 workers, `nice 10`, 2.5 h wall cap, partial file in the session
  scratchpad. Descriptive only.
- Relative premium ρΓ := Γ / (C₀ − V*_IID) (Γ per unit of IID value of information). Family-level statistic:
  max over α ≤ 1/2 of ρΓ at each (T, B).
- **Rule (stated before any scaling output was read):**
  - **Launch one bounded general-B theorem attempt** (target: ρΓ ≥ c > 0 uniformly along a growing (T, B) sequence
    in a named symmetric stationary family, or a matching Θ-rate) **only if** in at least one family (F_persist or
    F_anti) the max-over-α ρΓ at the largest completed B is ≥ 0.05 and is not lower than at B = 2 by more than a
    factor 2 (i.e. no clear decay with B), and certified Γ > 0 in at least 3 of the largest-B cells.
  - Otherwise: **no theorem attempt; publication decision is main-track NO-GO** (too restrictive / reduces to known
    mechanisms), with the scaling data recorded as evidence.
  - Either way, outcomes are main-track GO / CONDITIONAL GO / NO-GO only (`AGENTS.md` publication-outcome rule).

## 2026-11-11 00:10 — scaling run finished; locked rule applied
- 1,762/1,808 cells ok (46 dropped at T=10, B=6 by the wall cap). F_anti: max ρΓ rises 0.32 → 0.72 with B (all cells
  Γ > 0); F_persist: 0 up to B = 3, 0.029 at B = 6; F_coin flat ≈ 0.18. Two F_anti cells re-computed exactly by the lead.
- Rule fires for F_anti only ⇒ one bounded general-B theorem attempt (anti-persistent family). See
  `RELATIVE_PREMIUM_SCALING.md`.

## 2026-11-11 — wpG bounded general-B attempt (anti-persistent family), agent report
- Scope: one bounded attempt (~3 h, ≤ 3 processes, nice 10) triggered by the locked wpC2 rule. Write-up:
  `GENERAL_B_PREMIUM.md`; scripts `wpG_*.py`; outputs `results/wpG_*.json`. Nothing committed.
- PROVED: fixed-calendar causal-risk recursion (T1; pattern risk 2^-#ones; single least-favourable null per α);
  IID calendar reduction at t = 1 (CAL-t1); Lemma A (≤ ⌊B/2⌋ informative labels against the RIPr null);
  Prop L (calendar long-horizon slope limit), Prop P (calendar ρ_∞ → 1 for α ≤ 2^{1−B});
  Thm A (t = 1: Γ ≤ (1−2e)(B+1) for T ≥ 2B, so ρ → 0 in T); Thm V (t = 1: sup_T ρ → 0 as B → ∞ at fixed α).
- NEGATIVE / corrections: the fixed calendar is NOT WLOG for V*_causal (exact: T=8,B=2 calendar Γ 0.048 vs exact
  0.032; calendar exact only for T−B ≤ 4 where checked). Causal upper probability is not 2-alternating at B = 3
  (Huber–Strassen inapplicable). FCG-fast failed to terminate at (T,B)=(9,6), t=1, α=1/20.
- Reading: the wpC2 rise of ρ in B is a finite-resource effect (T−B small and B·I_e ≲ 2 log 1/α); no B- or
  T-uniform positive lower bound at t = 1. t < 1: CONJECTURED same, not proved. Verdict PIVOT; no main-track
  positive theorem from this attempt.

## 2026-11-11 — decision recorded
- Bounded general-B attempt: no positive theorem; at t = 1 the relative premium vanishes as T or B grows
  (Thm A/V, unreviewed); lead verified Γ = 0.032 constant in T (B = 2).
- **Publication decision: main-track NO-GO (existing results too narrow).** `PUBLICATION_DECISION.md`,
  `NEXT_ACTION.md` written. The programme's mandatory work packages are closed with verified outcomes.

## 2026-11-11 — correction and reopening
- The user challenged the NO-GO as setting the bar in the wrong place. On review the lead agrees: the locked target
  was the label-rich limit, the theorem attempt studied only the degenerate t = 1 chain, and a claim that t < 1 would
  also fail was unsupported and contradicted by committed data (relative premium flat in T for t = 3/4, 9/10).
- Decision reopened; salvage protocol `SALVAGE_PLAN.md` locked before any new work.

## 2026-11-11 ~01:50 — P3 run re-prioritised (order only; criteria unchanged)
- After 156 cells the partial data showed ρΓ identical at α = 1/20 and 1/10 (α-free) and B = 2 trends: t = 2/3
  0.25 → 0.200 (flat from T ≈ 12); t = 3/4 → 0.144 at T = 14, still drifting down slowly; t = 9/10 → 0.18 at T = 14,
  still falling. The original order would have spent the remaining budget on α = 1/4 and k = 1/50 before any
  B ≥ 3 cell.
- Lead stopped the run (finished cells kept in the partial file), added `WPM_PRI=v2` ordering to
  `wpM_scaling.py` (finish k = 0, d = 1, B ≤ 2; then B = 3, 4 at α = 1/10 for t ∈ {2/3, 3/4}; then t = 9/10; then
  d = 3 at B ≤ 2; then the rest) and relaunched with a 3 h budget, 2 workers, nice 10. The P3 agent was stopped; the
  lead runs the summariser.

## 2026-11-11 04:05 — detached supervisor and Codex handoff
- `wpM_supervise.sh` started in its own process session (survives agent sessions): relaunches `wpM_scaling.py` from
  the partial file if it dies, writes `MIXING_SCALING.md` when outputs exist, never commits. P5 review was
  interrupted by a network drop and resumed. Handoff for Codex: `HANDOFF_CODEX.md`.

## 2026-11-11 04:55 — salvage outcome recorded
- P3 finished (926 ok); supervisor wrote `MIXING_SCALING.md` and exited. P5 accepted M1–M3, M5; M4 with scope
  corrections. Locked criteria: CONDITIONAL GO clause (c) not met (B = 3, 4 still falling at T = 12; t = 9/10, B = 2
  still falling); NO-GO not triggered. Decision OPEN; single obligation: general-B uniform-in-T lower bound.

## 2026-11-11 — general-B attempt launched (user approved); criteria are the locked SALVAGE_PLAN.md ones
- GO requires S-1 PROVED for general B (label-scarce range, explicit open set of t < 1, uniform in T), accepted by an
  independent review, S-2 reviewed (done), no certified cell below the proved bound, novelty conditions of P4.
- NO-GO if the attempt proves ρΓ → 0 in T at some B ≥ 3 for t < 1, or certified B = 3 cells at T = 13–15 show a
  collapse (below half of the T = 12 value).
- Otherwise the decision stays OPEN with the obligation restated.
- Work: one Opus prover (1 process); certified B = 3 extension (t ∈ {2/3, 3/4}, d = 1, k = c = 0, α = 1/10,
  T = 13–15; 2 workers, detached, partial file). Then an independent review of whatever is proved.
