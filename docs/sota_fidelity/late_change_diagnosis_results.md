# Track B mechanism diagnosis: results

Protocol: [late_change_diagnosis_protocol.md](late_change_diagnosis_protocol.md), locked in commit
`a69878c4` before the run (manifest: same HEAD, clean worktree). Seed base 2026120701,
100 seeds × 14 cells × 18 policies. Machine-readable:
[late_change_diagnosis_results.json](late_change_diagnosis_results.json); raw records gitignored at
`outputs/sota_fidelity/late_change_diagnosis/`. **Descriptive diagnosis on synthetic development
regimes; not confirmatory; nominates no method.**

## Verdict per mechanism (rule: harmful-direction 95% CI excluding 0 in >= 2 change-time cells at B=200)

| Mechanism | Verdict | Evidence (B=200; change at 400 / 800 / 1200 / 1500) |
|---|---|---|
| M2 stale evidence | **Supported (dominant)** | RMM single-start − mixture: +35.1, +28.5, +7.7, 0.0 (first three exclude 0); LRMD single − mixture: +45.8, +24.0, +4.7, 0.0. Published hosts miss every late improvement (gated, DISCERN: miss rate 1.00 in all cells; SMCS 0.68–1.00). |
| M1 budget exhaustion / front-loaded pacing | **Supported** | LRMD k=3 − k=1: −13.6, +17.0, +22.6, +3.2 (last three harmful, exclude 0); k=2 − k=1: −7.5, +6.6, +17.9, +3.2. Misses fall sharply with budget (e-SR at change 1200: 0.81 / 0.20 / 0.02 at B=100 / 200 / 400). |
| M4 feedback stops after verdict | **Not supported** | Hosts never stop buying labels in these regimes (share with zero post-change labels: 0.00 for gated, DISCERN, SMCS; only the front-loaded host exhausts). RMM no-acq − full: +5.8, +2.9 (n.s.), −8.5, −1.7: harmful in one cell only. This ablation also changes total spending speed (finding 1), so it does not isolate post-verdict acquisition cleanly. |
| M3 label delay | **Supported descriptively; rule not applicable** (one change time) | At change 800, B=200, delay 10 / 100 / 400: e-SR miss rate 0.09 / 0.15 / 0.39; e-SR − never-switch −21.0 / −16.4 / −0.6 [−3.3, +2.2]. A 400-round delay removes the benefit. |

## Findings that reinterpret earlier results

1. **The RMM "continued acquisition" component is a pacing change, not post-verdict acquisition.**
   Before the change, full RMM spends 109 labels vs 79 for its no-acq ablation and for the host
   (change 800). The wrapper's own pacer is uniform (`pace_k=1`), but it buys a label whenever the
   host declines one (`restart_monitor.py:179-194`), so the two acquisition streams stack and the
   budget is spent faster. That helps early
   changes and hurts late ones (miss rate at change 1200: 0.57 full vs 0.11 no-acq). The sprint's
   "continued acquisition contributes −8 to −11" was measured on earlier-change regimes and does not
   generalise across change times.
2. **Host restart does nothing in late regimes.** RMM no-restart − full = 0.00 exactly in every cell:
   the detector, not the host, drives deployment.
3. **The best late-change detector here is a plain e-SR-type statistic with uniform pacing and full
   alpha on the promotion side.** `rmm:LRMD_k1` beats the default two-sided e-SR (alpha/2 per side)
   in all six B=200 / delay cells (−7.6, −4.2, −9.7, −2.5, −10.8, −6.1; all exclude 0). It is
   indistinguishable from `esr_rmmbets_fullalpha` (exploratory, unadjusted: −0.4, +2.1, −1.0, −0.1,
   −0.6, −0.8; all include 0). Start spacing (every 10 labels vs every label) makes no measurable
   difference; the alpha allocation between sides does.
4. **Change at 1500 is unrecoverable under this contract.** Every adaptive method costs more than
   never-switch (e-SR +9.3 [8.7, 10.0]); the remaining horizon cannot pay for labels plus a switch.
5. **New fidelity comparators.** Label-clock ARW promotes before the change in 100% of episodes
   (it flips on noise without a margin), so its costs are the worst in the table. Shekhar–Ramdas
   any-excludes is very conservative (miss rate 0.63–1.00).

## Mean net cost (B=200; delay 100 unless named)

| Policy | late 400 | late 800 | late 1200 | late 1500 | 800, d10 | 800, d400 |
|---|---|---|---|---|---|---|
| never switch | 408.1 | 393.6 | 378.9 | 357.2 | 391.3 | 393.5 |
| gated (host) | 418.1 | 403.6 | 388.8 | 367.1 | 401.3 | 403.5 |
| SMCS (host) | 411.9 | 402.9 | 388.8 | 367.1 | 400.5 | 403.5 |
| gated + RMM | 369.0 | 374.3 | 380.9 | 367.2 | 366.7 | 390.7 |
| gated + RMM no-acq | 374.7 | 377.2 | 372.4 | 365.5 | 366.5 | 393.3 |
| gated + RMM single | 404.0 | 402.8 | 388.6 | 367.2 | 400.9 | 403.4 |
| LRMD k=1 (uniform) | 368.7 | 373.0 | 366.3 | 364.0 | 359.5 | 386.9 |
| LRMD k=3 (front) | 355.1 | 390.0 | 388.9 | 367.2 | 380.5 | 393.9 |
| two-sided e-SR | 376.3 | 377.1 | 375.9 | 366.5 | 370.3 | 393.0 |
| e-SR, full alpha | 369.1 | 370.8 | 367.3 | 364.1 | 360.1 | 387.7 |

## Assessment for track B

- **Do not build on** restart mixtures (Shin et al. e-SR already supplies them) or post-verdict
  acquisition (not the failure mode here).
- **Open levers the diagnosis points to:**
  (a) *pacing under uncertainty about change time*: no fixed pacer wins at every change time
  (k=3 best at 400, k=1 best at 800–1500). A pacer that adapts to the evidence state, under
  predictable sampling that keeps the e-process valid, is a candidate, but it overlaps track C and
  prior work on adaptive sampling, so a prior-art check comes first;
  (b) *delay*: at a 400-round delay the benefit disappears;
  (c) *alpha allocation between promotion and rollback*: here it costs 4–11 per episode; it trades
  against the reversal results in `esr_vs_erb_dev_results.md`.
- **Comparator for any track-B candidate:** `esr_rmmbets_fullalpha` / `rmm:LRMD_k1` (uniform
  pacing, full promotion alpha), not the certificate hosts, which never detect late improvement.
- **Continue / pivot / stop:** continue track B only with lever (a) or (b), after a prior-art check;
  stop pursuing RMM as a contribution.

## Reproduce

```bash
uv run --extra drift python scripts/sota_fidelity/late_change_diagnosis.py run --out outputs/sota_fidelity/late_change_diagnosis --workers 9
uv run python scripts/sota_fidelity/late_change_diagnosis.py analyze --out outputs/sota_fidelity/late_change_diagnosis
```
