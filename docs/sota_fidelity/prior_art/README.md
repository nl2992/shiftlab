# Track B prior-art check: levers (a) pacing, (b) delay, (c) alpha allocation — lead verdict

**Date:** 2026-11-07. **Status:** prior-art and theorem-scope review only. It establishes no
method, novelty or efficacy result.

**Inputs.** These levers came from
[late_change_diagnosis_results.md](../late_change_diagnosis_results.md). The review used:
- an internal sweep of the October lanes (summarised in Section 1);
- two external retrieval reports: [pacing_external.md](pacing_external.md) and
  [delay_alpha_external.md](delay_alpha_external.md);
- an independent check: [CHECK.md](CHECK.md);
- this lead review.

The sources already audited in the repo (about 212 arXiv ids, in `docs/switching_*.md` and
`docs/lane_b_burst_allocation/`) were not re-audited.

## Verdicts

| Lever | Verdict | Why |
|---|---|---|
| (a) pacing under change-time uncertainty | **Closed as a mechanism. Open only as a theorem target**, and that target already failed in-repo screens | Each part is published separately. Predictable-sampling validity: Xu et al. 2406.10490; DISCERN. Evidence-gated sampling intensity: Ren et al. 1503.04999, Eq. 9 and Thm 2 (asymptotically optimal); VSI-CUSUM (Reynolds et al. 1990); DE-CuSum. Closed loop beats the best open loop: Premkumar–Kumar 2008, cost 38 vs 55 in one setting. Time- and posterior-dependent sampling over a finite run: Tagaras 1996 / Tagaras–Nikolaidis 2002 (abstracts only). Finite sampling rights: Geng–Bayraktar–Lai. Generic budget pacing: Braverman et al. 2610.11074. In-repo, the evidence-adaptive controller lost to a fixed temporal schedule (WP3: 55% vs 100% detection, paired interval [−65, −25] points). Lane B's "responsive beats oblivious" claim was withdrawn after review (W-B1). Fixed calendars matched fully adaptive timing in all 6 small HMM cells, and 504 paced-epoch configurations did not beat uniform pacing |
| (b) delay robustness | **Closed** | Without a faster information channel, "delay adds d" is unavoidable. Evidence: the repo's lower bounds (`switching_budget_delay_lower_bound_v1.md`, `switching_finite_horizon_qcd_budget_delay_audit_v1.md`), plus Vernade et al. 2006.02119 Prop. 1 (a bandit-regret analogue with a sketched proof). The fast-surrogate escape was closed in October (split-clock, D0/D2). Pipeline-aware economic stopping is precedent (Chick–Forster–Pertile; Hampson–Jennison). What remains is to stop buying labels whose release comes too late to repay a switch. That is a baseline and saves only query cost |
| (c) promotion vs rollback alpha | **Closed as a contribution. It changes the comparator, not the method** | The contract's error criterion (`switching_problem_v1.md:42-50`, criterion (i)) counts only promotions under the global no-benefit null. Every promotion path contains the first promotion, so rollback needs **no** alpha and re-promotions need no halving. The alpha/2 split is conservative under the stated contract. Under a law-level FWER (criterion (ii)), fixed-sequence chains at full alpha per leg are textbook: Goeman–Solari Thm 1, offline; Fischer–Bofill Roig–Brannath Thm 3.2, online; Hartog–Lei Thm 2.5, e-processes with fixed hypotheses. Hypotheses formed after earlier rejections rest on Fischer–Ramdas 2407.15733 §2. Under a pathwise criterion (iii), full alpha on promotion forces alpha_R = 0 (union bound, or the product form if the rollback detector starts fresh at promotion) |

## Lead review notes

1. **Criterion (i) is weak, so lever (c)'s "free" alpha is not free for track A.** Criterion (i)
   is evaluated only under the *global* null, where the challenger never helps. It does not control a
   false re-promotion or a false rollback after a real change or reversal. Any track-A claim about
   reversal safety needs criterion (ii) or (iii). The repo should state which criterion each result
   uses. For track B (late improvement, no reversal), criterion (i) is the relevant one. The fair
   comparator is then full-alpha promotion with an economic or uncertified rollback. The track-B
   diagnosis already used `esr_rmmbets_fullalpha` / `rmm:LRMD_k1` as that comparator. Its null rates
   are recorded (0.016 / 0.019 / 0.000 at 1000 seeds, Wilson upper bound <= 0.029).
2. **The only route left for lever (a) is a theorem.** One example: a minimax-regret or
   competitive-ratio bound over change times, against the best fixed pacer for each change time, under
   a hard cap with delay. The repo lists this as open (`switching_unknown_onset_mixture_lower_bound_v1.md`,
   `PRIOR_ART_AND_NOVELTY_MATRIX.md:32,543`). Its worst objection is already recorded: the theorem may
   come out making uniform sampling optimal (Geng–Bayraktar–Lai's first-order result points that way).
   Every empirical attempt at the mechanism has lost to a fixed schedule. This is Paper 3 (allocation)
   territory per the charter and `algorithm_search_exit_ledger.md`, not track B monitoring.
3. **Corrections applied.**
   - `B0_prior_art.md:29` wrongly said 1411.3107 censors based on the statistic; only 1503.04999 does.
     A note was added there.
   - The delay report claimed no null check existed for the full-alpha e-SR. One does exist; the
     report has been corrected.
   - The checker's qualifications are recorded in `CHECK.md`: Premkumar–Kumar Thm 5 is conditional on
     an unproven monotonicity; Goeman–Solari is offline; the product formula needs the rollback
     detector to restart at promotion. Notes were added to both reports.

## Continue / pivot / stop

- **Stop** track B as a monitoring-method contribution. None of the three levers leaves a mechanism
  that the published literature and the repo's own screens have not already covered.
- **Keep** the track-B findings as benchmark content:
  - stale evidence explains why certificate methods miss late improvement;
  - RMM's acquisition stacking;
  - fixed pacers trade early against late change;
  - delay at 400 erases the benefit.
- **Fix the comparator convention.** Under criterion (i), report full-alpha promotion
  (`esr_rmmbets_fullalpha`) as the e-SR baseline, alongside the published two-sided alpha/2 version.
- **Possible pivots (each needs the user's approval):**
  - Paper 3 lever (a) as a theory-first target, with a stop rule if the bound makes uniform optimal;
  - track A under an explicitly declared criterion (ii) or (iii) with economic gating. The E_rb
    results showed every valid method loses to never-switch on reversal, so this needs regimes with
    enough beneficial horizon before the reversal.

---

# Addendum (2026-11-10): scheduled periodic bursts — lead verdict

Inputs: [bursts_external.md](bursts_external.md) (retrieval), an in-repo sweep (summarised here), and
[BURSTS_CHECK.md](BURSTS_CHECK.md) (independent check, which opened the sources the retrieval missed).

| Sub-question | Verdict | Why |
|---|---|---|
| (b1) periodic bursts beat spread sampling when the detector needs m > 1 samples under a budget | **Closed: the classic result points the other way** | For detectors that accumulate evidence (CUSUM/EWMA, and our SR e-detector), spread single observations beat grouped samples at a fixed sampling rate (Reynolds & Stoumbos 2004, via a secondary source); grouping helps only memoryless Shewhart charts. Geng & Lai 1302.3834 (worst-case delay, sampling constraint) gives greedy sampling, not bursts. The fluid-model gain in `PACING_CHECK.md` reverses between m = 66 and m = 54, consistent with a rounding/edge effect at B/m ≈ 3, not a mechanism |
| (b2) random phase beats deterministic schedules against an adversarial change time | **Known principle** | Inspection and patrolling games (Alpern–Morton–Papadaki 2011; Cohen et al. 1302.0792), with m = 1; the detection-delay version with m > 1 was not found |
| (b3) combination with label delay and an anytime-valid detector | Not found | A combination of known parts; on its own not a contribution |
| (b4) in-repo A2 "confirmation burst" | **Different mechanism** | A single burst forced by a tight risk constraint requiring unanimous confirmation (Theorem 7, `13_A2_BRANCH_CONFLICT_THEORY.md`); without that constraint the A2 optima spread out. WP3's end-loaded step schedule is a third mechanism (late-onset prior) |

**Decision:** periodic bursts are closed as a contribution; no new protocol for a novelty claim. The
only remaining use is an optional small hygiene check (random-phase periodic bursts in the locked
stochastic screen, with STOP pre-registered as the expected outcome) to remove the "untested class"
caveat in `pacing_minimax_results.md`. With this, the Paper 3 pacing target has no open method lever.
