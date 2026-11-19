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

## 2026-11-11 — user-approved acceptance-range amendment, before prover launch
- The bounded continuation requested today is one proof process alongside the already-running certified B=3
  extension (two numeric workers). The numerical run is `wpM_b3ext.py`, B=3, t ∈ {2/3, 3/4}, d=1, c=k=0,
  α=1/10, T=13–15; it resumes from `outputs/paper4_theory_v2/wpM_b3ext_partial.jsonl` and refuses to overwrite
  its compact result.
- The user is willing to accept looser criteria. For this bounded attempt, a rigorous **uniform-in-T lower bound
  for B=3** over an explicit nonempty open parameter family is an acceptable narrower positive milestone; a bound
  for a finite explicit label-scarce budget range is also acceptable if its dependence and scope are stated. Such
  a result does not by itself change the publication decision to GO. GO still requires independent review and no
  certified cell below the proved bound. General B remains open unless the proof actually covers it.
- NO-GO remains reserved for a proof of vanishing premium for B=3 at t<1, or certified extension data showing a
  collapse under the previously locked threshold (below half the T=12 value). If neither condition is established,
  keep the decision open and restate the remaining obligation. Finite-horizon decreases alone are not proof of a
  zero limit.

## 2026-11-11 — bounded B=3 proof attempt completed
- The single bounded attempt is documented in `B3_UNIFORM_PREMIUM_ATTEMPT.md`. It proves an algebraic comparison
  between two explicit infinite-horizon B=3 continuation witnesses on a nonempty open parameter region, but both
  are lower bounds on optimal branch slopes; the comparison does not upper-bound all adaptive continuations and
  cannot close the M3 relaxation. No uniform-in-T lower bound or counterexample was established.
- Status remains OPEN. The conjecture is neither supported nor falsified by this proof attempt; the certified
  T=13–15 extension is still running and its result is not yet available. No publication decision follows from this
  partial proof attempt.

## 2026-11-11 — interim certified B=3 horizon extension (2/6 cells)
- `wpM_b3ext_partial.jsonl` now contains the certified T=13 cells. For t=2/3, rho_Gamma ∈
  [0.1443847942775929, 0.14438479428105994], versus the T=12 interval
  [0.1454202838934605, 0.14542028389690626]. For t=3/4, the T=13 interval is
  [0.1360924381080214, 0.1360924381097912], versus T=12
  [0.148754586060125, 0.14875458606138808]. Both exceed half their respective T=12 values, so the locked
  collapse trigger has not fired. These two cells do not establish the horizon limit; four planned cells at T=14,15
  remain in progress under the same two-worker run.

## 2026-11-11 — bounded B=4 horizon extension queued before launch
- To continue the handoff's suggested B=3/4 horizon extension with a looser, narrow first pass, run only B=4,
  T=13, t ∈ {2/3, 3/4}, d=1, c=k=0, α=1/10. Use one additional solver worker at nice 18, at most 1,800 s
  per cell, while the existing B=3 run uses two workers at nice 15 (three solver workers total, within the cap).
- Script: `scripts/paper4_continuation/theory_v2/wpM_b4ext.py`; resumable partial:
  `outputs/paper4_theory_v2/wpM_b4ext_partial.jsonl`; compact output refuses overwrite at
  `docs/paper4_continuation/theory_v2/results/wpM_b4ext_v1.json`. Exact certificates are descriptive.
- This B=4 slice is exploratory and does not change the locked B=3 collapse rule or any publication decision. If a
  cell times out, retain the timeout and report incomplete coverage rather than infer a value.

## 2026-11-11 — B=4 T=13 extension started
- Started `wpM_b4ext.py` in one worker. Script SHA-256: `87dd74d5e03252190b7dbc7ad692b7aa3988e0d7836a135b7aae8a59330691ca`.
  The runner has a 1,800 s per-cell cap, records each result/timeout to its JSONL partial, and writes the compact
  output only after both cells certify. The run is active in this Codex session; no B=4 result is available yet.

## 2026-11-11 — interim certified B=3 horizon extension (4/6 cells)
- Both T=14 cells completed. For t=2/3, rho_Gamma ∈ [0.1440419976786119, 0.14404199768317]; for t=3/4,
  rho_Gamma ∈ [0.1317882147057557, 0.13178821470773688]. Together with T=13, all four new B=3 cells are
  certified positive and above half their matching T=12 baseline. The locked collapse trigger remains unmet.
  T=15 (two cells) and the separate exploratory B=4 T=13 run are still in progress.

## 2026-11-11 — B=3 horizon extension completed; B=4 first pass timed out
- All six B=3 cells at T=13–15 certified positive. T=15 rho_Gamma intervals: t=2/3,
  [0.14370167398436476, 0.14370167399043238]; t=3/4,
  [0.1254796164388513, 0.12547961644230946]. Relative to the matching T=12 lower endpoints, these are 98.8%
  and 84.4%, respectively; every new B=3 cell is above half the T=12 value. This finite extension does not establish
  a positive limit or any uniform-in-T theorem. Compact result: `results/wpM_b3ext_v1.json` (script SHA-256
  `a716a8dd60d5a5746edecfba4616d422a02c247b9be8f4e016c4e87f650dae43`).
- Both B=4, T=13 cells (t=2/3 and 3/4) timed out at 1,800 s; no certified value was produced and no premium claim
  follows. At the user's request to continue more loosely, raise only this small run's per-cell cap to 3,600 s;
  keep one worker at nice 18. The original timeout rows remain in the partial; the runner retries non-success cells.
  Updated runner SHA-256: `f4f28b54a0dcf2b1f3fc4df054f23aaf545920789ba64ede9891f7be1dafacfd`.

## 2026-11-11 — B=4 T=13 retry started with relaxed runtime cap
- Restarted the two T=13 cells from the timeout partial using the updated 3,600 s/cell cap, sequentially, one
  worker at nice 18. Script SHA-256 is recorded above. The retry is active; no result is available yet.

## 2026-11-11 — ratio-interval reporting correction from secondary review
- The first B=3 extension runner used `C0 - U_IID` for both relative-premium endpoints. This is the lower VOI
  endpoint; the upper rho endpoint can use it, but a certified lower rho endpoint needs an upper VOI endpoint. The
  reported Gamma positivity is unaffected.
- Corrected enclosure: `Gamma_hi - Gamma_lo` upper-bounds the IID value-interval width because the Gamma interval
  width is the sum of the causal and IID value widths. Widen the stored float endpoints outward by one ULP, set
  `VOI_upper <= nextafter(VOI_lower,+inf) + Gamma_width_upper`, and use `rho ∈ [Gamma_lower/VOI_upper,
  Gamma_upper/VOI_lower]`. The deterministic sidecar `results/wpM_b3ext_rho_corrected_v1.json` contains the
  corrected enclosures; they are less than 1e-12 below the originally displayed T=15 lower endpoints. This does
  not change the conclusion: all six B=3 cells remain positive and above half their T=12 baselines.
- Fixed both extension runners to compute the ratio from `L_IID` and `U_IID` directly and retain exact rational
  fields. The B=4 retry stopped before producing a result; restart it with the corrected runner (SHA-256
  `0c48b14c84209f62a4410ef8cd046ebbe28f21ec48130a20adc0ae97c25b893a`), still one worker at nice 18 and
  3,600 s/cell. Keep the earlier timeout rows as evidence; they are not premium values.

## 2026-11-11 — corrected B=4 T=13 retry running
- Restarted the B=4 T=13 cells with the corrected `L_IID/U_IID` denominator formula. Two cells, sequential, one
  worker at nice 18, 3,600 s per cell; the partial currently contains only the two prior timeout rows. Script SHA-256:
  `0c48b14c84209f62a4410ef8cd046ebbe28f21ec48130a20adc0ae97c25b893a`. No B=4 value has been produced yet.

## 2026-11-11 — B=2 T=16 extension queued
- To extend the reviewed B=2 horizon series at the lowest cost, evaluate T=16 at t ∈ {2/3, 3/4, 9/10},
  d=1, c=k=0, alpha=1/10, e=(1/10,9/10), prior=1/2. Run sequentially on one additional worker at nice 18;
  the existing B=4 retry remains on its single low-priority worker (two numeric workers total).
- Runner `scripts/paper4_continuation/theory_v2/wpM_b2_t16.py` uses exact `gamma_cell` bounds, computes rho from
  separate `L_IID/U_IID` bounds, resumes from `outputs/paper4_theory_v2/wpM_b2_t16_partial.jsonl`, and refuses
  overwrite of `results/wpM_b2_t16_v1.json`. This is confirmatory finite-horizon evidence for B=2 only; it cannot
  establish uniformity in T or upgrade the theorem's scope.

## 2026-11-11 — B=2 T=16 extension started
- Started the three cells sequentially with one solver worker at nice 18 in exec session 96725; the existing B=4
  retry remains the other numeric worker. The first B=2 cell is computing; no T=16 output is available yet.
- Runner SHA-256: `0a8459ba7da95e541e6847934e6abdeb94d76ff958fef2f2874b9d9a6556b629`.

## 2026-11-12 — B=2 T=16 extension completed; B=4 retry outcome
- All three certified B=2 T=16 cells completed with corrected ratio intervals: rho=0.2000487961 (t=2/3),
  0.1435819915 (t=3/4), and 0.1514228628 (t=9/10). Each remains above half its T=12 baseline. The t=9/10 series
  declined 12.66% from T=15 to T=16 and remains below the reviewed M4 activation horizon T₀=37. Full exact output:
  `results/wpM_b2_t16_v1.json`.
- The B=4 retry timed out again at t=2/3 after 3,600 s; the t=3/4 cell did not run. This is incomplete compute,
  not evidence of zero premium. See `outputs/paper4_theory_v2/wpM_b4ext_partial.jsonl`.
- Next bounded experiment: one B=2, T=17, t=9/10 cell (same other settings), one low-priority worker, 3,600 s cap.
  This targets the only B=2 series still declining materially; it tests a finite-horizon trend, not the asymptotic
  theorem. Runner `scripts/paper4_continuation/theory_v2/wpM_b2_t17_t9.py`.

## 2026-11-12 — targeted B=2 T=17 cell started
- Running in exec session 38924, one worker at nice 18. Runner SHA-256:
  `b011c4c367524d091e270da2ff9705e888916ca80349c5d6c4aeeb28d879270b`. No certified value is available yet.

## 2026-11-12 — B=3 open-family uniform theorem proved and reviewed
- Proved Theorem M6 for `B=3`, `d=1`, `c=k=0`, `alpha=1/10`, `r in (1/200,1/100)`, and `g in (2/5,1/2)`:
  for every `T>=16`, `Gamma >= 0.38 alpha g r` and `rho_Gamma >= 19/101 > 0.18`.
- The proof uses a four-null dual mixture (IID plus one null per query position), a uniform posterior continuation
  envelope, exact rational path enumeration, and a fixed IID witness. Full proof: `B3_UNIFORM_PREMIUM_PROOF.md`;
  arithmetic: `prompts/26111216-1/constant_audit.py`.
- A fresh adversarial reviewer found no fatal gap, requested four wording fixes, then accepted the revised proof.
  This was a separate agent from the same model family, not external or independent-model review. The corrected
  witness limit is `G0 + v1(2-r^4-r^3)`; the earlier `G0+2v1` sentence was inaccurate but did not affect the lower bound.
- This establishes the requested narrow B=3 theorem, not a general-budget result. `SALVAGE_PLAN.md` is unchanged;
  the locked general-budget GO criterion remains unmet and the publication decision remains open. B>=4 and growing-B
  uniformity are the next proof obligations. The certified B=2 T=17, t=9/10 cell remains active in session 38924.

## 2026-11-12 — B=4 open-family uniform theorem proved and reviewed
- Extended the multi-position-null certificate to four labels, retaining the fourth-spin term in the transcript
  density and all four triple-label interactions in the posterior numerator. For the same open rectangle,
  `B=4`, `d=1`, `c=k=0`, `alpha=1/10`, every `T>=16` has `Gamma>=0.39 alpha g r` and
  `rho_Gamma>=13/84>0.15`.
- Exact rational audit maxima are `62875/29997<2.10` for causal VOI and `25150/9999<2.52` for IID VOI. An
  independent same-family adversarial reviewer accepted the proof; see `B4_UNIFORM_PREMIUM_PROOF.md` and its review.
- This strengthens the fixed-budget evidence but still does not meet the locked general-budget GO criterion.
  B>=5 and growing-B behavior remain open. Do not change `SALVAGE_PLAN.md` or the publication decision on this basis.

## 2026-11-12 — B=5 open-family uniform theorem proved and reviewed
- Extended the certificate to five labels, retaining all even-subset terms in the history density and all odd-subset
  terms through the six-spin posterior interaction. For the same open rectangle, `B=5`, `d=1`, `c=k=0`,
  `alpha=1/10`, every `T>=16` has `Gamma>=0.40 alpha g r` and `rho_Gamma>=40/303>0.13`.
- Exact rational audit maxima are `60400/23331<2.59` causal and `30200/9999<3.03` IID. A fresh same-family
  adversarial reviewer accepted the derivation after a self-contained Bellman/leaf/witness clarification.
  Full proof: `B5_UNIFORM_PREMIUM_PROOF.md`; exact audit: `prompts/26111216-3/b5_constant_audit.py`.
- The general-budget criterion still remains open: B>=6 and growing-B uniformity are unproved. `SALVAGE_PLAN.md`
  and the publication decision are unchanged.

## 2026-11-12 — targeted B=2 T=17 cell certified
- The low-priority `t=9/10`, `T=17`, `B=2` `gamma_cell` run completed in 2,717.2 seconds. Exact interval output:
  `Gamma in [0.035743913556156436,0.03574391355626086]`, `VOI_IID in
  [0.2487942405962072,0.24879424059626085]`, `rho_Gamma in [0.1436685731570493,0.1436685731575]`.
- Compared with T=16, the rho lower endpoint declined 5.12% and Gamma declined 3.55%. T=17 is below M4's reviewed
  `T0=37`; this is finite-horizon trend evidence only. Output: `results/wpM_b2_t17_t9_v1.json`.
- No sleep settings were changed. The general-budget proof obligation remains open notwithstanding the B=3,4,5
  fixed-budget theorems.

## 2026-11-12 — B=6 open-family uniform theorem proved and reviewed
- Extended the subset-moment certificate through six labels, including the six-spin transcript term and the
  five-emission posterior term. On the same open rectangle, `B=6`, `d=1`, `c=k=0`, `alpha=1/10`, every `T>=20`
  has `Gamma>=0.39 alpha g r` and `rho_Gamma>=13/118>0.10`.
- A fresh same-family reviewer accepted after small clarity edits. The independently checked endpoint maxima are
  `41125/13332<3.10` causal and `11750/3333<3.54` IID. Full proof: `B6_UNIFORM_PREMIUM_PROOF.md`.
- This now covers each fixed budget B=3,4,5,6 on the chosen rectangle, but still does not prove the locked
  general-budget S-1 for a label-scarce range or growing B. Do not change the salvage criteria or publication
  decision; continue with B>=7 or derive an explicit bounded-budget theorem.

## 2026-11-12 — explicit B<=6 S-1 corollary drafted; in-region numeric cell started
- M1, M4, and M6–M9 imply `rho_Gamma>=0.10` for every `1<=B<=6`, `T>=20` on the shared open rectangle. M10 states
  this as the explicit bounded-budget range `Bbar=6`; a separate reviewer accepted the combination. Calling it
  “label-scarce” is interpretive; no other scarcity threshold is asserted.
- Started one certified consistency cell at `B=3`, `T=16`, `t=63/125` (`r=0.008`), `e=3/20` (`g=0.49`),
  `alpha=1/10`, `d=1`, `c=k=0`. One sequential worker at nice 18; runner has a 3,600 s cap, resumable partial,
  and refuses overwrite of the final result. It is a consistency check, not a proof premise.

## 2026-11-12 — continuation moved to isolated Codex worktree; consistency cell restarted
- The documented Codex lane checkout was absent. Created `/Users/nigelli/Desktop/ICML/shift-codex-paper4`
  on branch `codex/paper4-causal-premium-continuation`, based on the current Paper 4 branch HEAD, and copied
  the uncommitted Paper 4 proof/docs/review state into it. No files were changed in the Claude worktree.
- The prior cell process was stopped after 13m with no result or resumable row written. A fresh `.venv` was
  installed from the locked project environment; the same registered cell was restarted there at nice 18.
  At ledger update it was live as PID 69170. Output and partial paths are now local to this Codex worktree.
- Reviewed code SHA-256: `aee5fc8f7743be8886ea443b29719d010a287ce33792baacd89a1c4a41e105dd`.
  This cell remains a consistency check only. Sleep remains enabled; no sleep setting was changed.

## 2026-11-12 — focused novelty review completed; arbitrary-fixed-B proof reopened
- Fresh-context novelty review returned **PROCEED, 6/10**: no exact published result was identified for the
  stated uniform-in-horizon HMM decision-value gap. Closest foundations are rectangular minimax sequential
  testing and dual mixtures of stopped null laws; neither gives the nominal-versus-causal VOI premium.
  Caveats: the current certificate does not isolate outcome-reactive adversary value, the parameter region is
  narrow, and the 10% is relative to VOI. Full record: `NOVELTY_REVIEW_2026-11-12.md` and its ARIS trace.
- An algebraic arbitrary-fixed-`B` lead suggests the same certificate has a normalized separation of order
  `1/(B+2)` as `r -> 0`, with the admissible open `r` region depending on `B`. This is conjectural pending a
  fresh proof attempt of all remainder, adaptivity, and witness-timing steps. It would not provide a common
  rectangle or constant for growing `B`.
- Keep the locked salvage plan unchanged. The in-region B=3 numeric consistency cell is still pending; the
  publication decision remains open until its certificate is reconciled with M6 and remaining criteria.

## 2026-11-13 — B=3 consistency timeout; arbitrary-fixed-B candidate drafted
- The one-worker B=3, T=16 cell at `r=1/125`, `g=49/100` reached its 3,600 s cap. The final artifact records
  `status=timeout`; there is no certified value to compare with M6. This is a compute limitation, not a
  contradiction of the theorem. No further sleep-setting changes were made; macOS still reports `sleep 1`.
- A complete theorem proof is now recorded in `B_GENERAL_FIXED_PREMIUM_PROOF.md`. For each fixed
  `B>=1`, it proposes `rho_Gamma>=3/[8(B+2)]` for `T>=3B`, on `2/5<g<1/2` and
  `0<r<1/[16(B+2)(6B^3+3B+2)]`. It also derives a finite simultaneous range `B<=floor((1056r)^(-1/4))`.
  The radius shrinks with B, so this is not a common open rectangle or a constant lower bound for unbounded B.
- The candidate is explicitly **not yet a theorem**. A fresh same-family adversarial review is in progress;
  the earlier reviewer request hit a provider usage limit and produced no verdict. A subsequent fresh
  adversarial review returned **PASS**, with no mathematical issues and a match to the repository's query/null
  timing; a separate fresh arithmetic/witness check also passed. The full audit is in
  `B_GENERAL_FIXED_PREMIUM_PROOF_AUDIT_2026-11-13.md`. This is same-family and provisional, not cross-family
  verification or formal proof-assistant verification; keep it out of the theorem registry pending assurance
  requirements and consistency/claim review.
- The publication decision and `SALVAGE_PLAN.md` remain open/unchanged. The timeout does not trigger NO-GO,
  and the candidate proof alone does not satisfy the overall GO criteria.
