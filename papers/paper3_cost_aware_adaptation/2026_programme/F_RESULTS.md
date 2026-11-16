# F results: risk-budgeted reversible intervention (F3), registered confirmation

Registration: `04F_F3_CONFIRMATION_REGISTRATION.md`, frozen at commit f5cadbd9. Run once on
2026-11-15 from that commit (ledger `riskbudget.jsonl`, stage `confirmation`; the working tree was
flagged dirty only for the untracked build file `src/shiftlab.egg-info/SOURCES.txt`).
Seeds 5303500000-5303500999, 1000 per regime, 30 regimes, T = 300, 18 frozen arms. Wall 659 s.
Raw: `outputs/paper3/riskbudget/confirm/`; statistics: `results/riskbudget/confirm_summary.json`
(`scripts/paper3/riskbudget/analyze_confirm.py confirm`). Dev results (exploratory):
`results/riskbudget/dev_tables.md`, `dev_v2_tables.md`.

## Registered outcomes (all six SUPPORTED)
- **C1 deterministic budget.** 0 violations in 30,000 runs for each of f3_pi1_R12, f3_pi1_R20,
  f3_pi1_R30 and f3v2_R20_blind8 (per-regime Wilson upper bound .004).
- **C2 sampled budget (delta .05).** f3v2d_R20: 1 violation in 30,000 (bait_reversal);
  f3v2d_R30: 1 in 30,000 (dropout_adverse). Largest per-regime Wilson upper bound .006.
- **C3 comparators exceed R = 20.** Worst-regime rate [Wilson 95%], pooled rate:
  wald_cut .852 [.829,.873], 6.6%; cusum .987 [.978,.992] (expensive_switch), 7.9%;
  gate_wald .635 [.605,.664], 4.3%; cusum_rb_h8 .830 [.805,.852], 4.4%;
  stoploss_R20 .841 [.817,.862], 4.2%. Worst regime is dropout_adverse except for cusum.
- **C4 price of safety.** f3_pi1_R20 - wald_cut = +0.96 [+0.86,+1.06] (+1.4%; upper +1.55% < 3%);
  f3_pi1_R20 - never = -2.10 [-2.22,-1.98]. Secondary: f3v2d_R30 - wald_cut = +0.25 [+0.15,+0.35].
- **C5 adverse feedback.** Stress-6: f3_pi1_R20 - wald_cut = -5.19 [-5.40,-4.98] (-7.4%).
  Original-24: +2.50 [+2.38,+2.62] (+3.7%, worse).
- **C6 reserves needed (R = 12).** Worst-regime violation: no pending reserve .940 [.924,.953];
  no rollback reserve .862 [.839,.882]; no confidence width .341 [.312,.371].

## Descriptive table (pooled over 30 regimes)
| arm | J | labels | q99 harm | max harm |
|---|---|---|---|---|
| never | 71.53 | 0 | 0 | 0 |
| wald_cut | 68.47 | 38.8 | 37 | 59 |
| cusum | 68.97 | 47.0 | 34 | 117 |
| gate_wald | 71.89 | 49.7 | 33 | 57 |
| cusum_rb_h4 / h8 | 68.97 / 68.62 | 47.8 / 49.8 | 31 / 35 | 68 / 71 |
| stoploss_R12 / R20 / R30 | 69.28 / 68.79 / 68.74 | 49.1 / 49.8 / 49.9 | 34 / 34 / 34 | 59 |
| f3_pi1_R12 / R20 / R30 | 70.32 / 69.43 / 69.25 | 42.1 / 44.2 / 44.5 | 12 / 20 / 28 | 12 / 20 / 30 |
| f3v2_R20_blind8 | 69.18 | 40.0 | 17 | 20 |
| f3v2d_R20 / R30 | 69.80 / 68.72 | 37.8 / 40.5 | 16 / 21 | 22 / 31 |

## Limits
- No mean-cost win over tuned Wald+cutoff: F3 is 0.4-2.7% worse pooled, and 3.7% worse on the 24
  original regimes at R = 20. The gain is confined to harmful, reversal and adverse-feedback regimes.
- The largest comparator failures are in stress regimes built to stress delayed and missing
  feedback; on the original 24 the comparators' exceedance is smaller (see dev tables).
- Simulation only (exogenous outcomes, two frozen models, T = 300). No real stream was run.
- The sampled variants' bound is conservative (2 violations in 60,000 against delta = .05) and
  sampling saves few labels at R <= 20.
- Theory: Theorem 2, Lemma 1/1' and Propositions 3-4 are proved in 03F (Propositions 3-4 added
  2026-11-16, after the confirmation run, with a numerical check in `results/riskbudget/props_check.json`).
  Proposition 4 covers the first deployment spell with labels available; it does not bound the
  forced rollbacks caused by label exhaustion or repeated spells.
- Baselines are in-house or documented adapters, not native-source reproductions.

## Real-stream check (protocol `05F_F3_REAL_STREAM_PROTOCOL.md`, run once 2026-11-16)
Label EXPOSED_STREAMS_FROZEN_CONFIG: 14 cached real loss streams (230 episodes, T = 2000, B = 200,
k = 5), 20 policy seeds per episode, 4,600 runs per arm and condition; every arm frozen from
simulation, budgets R = 10 + h. Tables: `results/riskbudget/real_tables.md`,
`real_summary.json`; code `riskbudget/real_streams.py`, `scripts/paper3/riskbudget/run_real.py`,
`analyze_real.py`. Harness debugged on synthetic tapes only; no re-run.

- **Budget holds.** 0 violations in 4,600 runs for every F3 arm (full sampling, paced sampling,
  blind-round variant) in every stream, budget and condition.
- **Comparators exceed it.** Runs with harm above R = 24 (of 4,600): wald_cut 475 clean, 890
  adverse dropout, 1,017 adverse delay; the naive stop-loss breaks its own R = 24 in 311 / 886 /
  979 runs. Largest harm seen: wald_cut 175 / 529 / 400; F3 never above its R.
- **Cost is high on beneficial streams.** Pooled mean J, clean: never 597.9, wald_cut 403.8,
  f3_pi1 591.0 / 522.8 / 510.9 / 495.8 / 478.4 at h = 6 / 14 / 24 / 50 / 100, f3v2d 519.1 / 450.5 /
  433.9 at h = 14 / 50 / 100. Against wald_cut that is +75 to +187 for full sampling and +30 at best
  for paced sampling (h = 100). F3 is significantly worse than wald_cut on 8-9 of the 10 streams
  with intervals and never significantly better in the clean condition. At h = 6, and for the
  blind-round variant at h = 14, F3 is about as costly as never switching.
- **Where it pays.** On the two harmful streams under corrupted feedback: f3_pi1 vs wald_cut pooled
  over airlines and bank is -33 to -55 (dropout) and -46 to -88 (delay). In the clean condition it
  is +1 to +6 there.
- **Reading.** Full sampling needs a label on every exposed round; these streams have 120-1,560
  disagreement rounds per episode (disagreement rate .06-.78) against 200 labels, so the shield runs out of labels, books rounds
  blind and is forced back (1.3 forced rollbacks per episode at h = 14). Paced sampling removes
  much of that at large budgets but pays the confidence width. The simulation price of safety
  (0.4-2.7%) does not carry over to this label-scarce setting: here it is 7-46% of J(wald_cut).
