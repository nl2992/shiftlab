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

## Label-scarce fix attempt (v3; 03F section 7, selection `03F_V3_SELECTION.md`)
Exploratory. v3 = v2 shield with a lower pacing floor and a wider mixture grid (new `v_targets`
option; the default reproduces v2 exactly, pinned by a test). Selected on a new 47-regime
label-scarce family (`regimes_f3_scarce_v1.json`, T = 2000, B = 200, k = 5) on dev seeds
70000-70199; frozen in `configs/paper3/f3_v3_frozen.json` (pi_min .25, label_reserve_frac .25,
no optional blind rounds). Tables: `results/riskbudget/v3_{scarce,orig30}_tables.md`,
`real_v3_tables.md`.

- **Selection did not beat the earlier paced arm.** At h = 50 on its own selection family the best
  v3 candidate scored 395.5 against 388.3 for f3v2d and 340.8 for wald_cut. The pacing floor barely
  mattered (scores within 1.5 across pi_min .05-.25): the look-ahead guard keeps pi = 1 almost
  always.
- **Fresh scarce seeds (71000-71499).** v3 vs wald_cut: +54.0 [+53.4, +54.7] at h = 50, +14.5
  [+14.0, +15.0] at h = 100; f3v2d +46.8 and +16.7. The cost grows with disagreement rate and delay
  (h = 50: +2 at r = .1, +40 at r = .25, +125 at r = .4; +31 at d = 24, +75 at d = 144) and is
  near zero on harmful paths. Violations: 1 in 23,500 for v3_h24, 0 elsewhere.
- **Original 30 regimes (72000-72299).** v3 matches f3v2d at R = 20 and 30 (within .02) and is
  worse at R = 12 (+4.74 vs wald_cut, worse than never). 0 violations.
- **Real streams, SECOND LOOK** (streams seen once before; v3 designed after that run and selected
  on simulation only). Clean, pooled 14: v3 vs wald_cut +40.8 at h = 50 and +17.6 at h = 100,
  against f3v2d +46.7 and +30.1; the gain over f3v2d comes mostly from metro (-44.1 [-73.1, -18.9])
  and uci_occupancy. At h <= 24 v3 is worse than f3v2d. 1 violation in 4,600 (dropout, h = 50,
  within delta); 0 elsewhere.
- **Reading.** The fix narrows the gap only at large headroom and does not close it. The cost
  tracks exposure inside one delay window (r*d) relative to headroom h, as Proposition 3 predicts;
  the remaining gap looks structural for any controller with this guarantee, not a tuning defect.

## Exposure-ratio test (script committed with its prediction before the first run, 5f1cdae2)
`scripts/paper3/riskbudget/exposure_ratio_test.py`, existing outputs only:
scarce-family fresh seeds and the 14 real streams (clean). Unit = (regime or stream, F3 arm,
headroom h), kept where wald_cut gains at least 10% of J(never). x = r d / h (disagreement rate x
label delay / headroom); L = (J_F3 - J_wald) / (J_never - J_wald), the share of wald_cut's
improvement that F3 gives up. Results: `results/riskbudget/exposure_ratio_test.json`.

- **Primary (6 tests, all supported).** Spearman(x, L) with regime/stream-bootstrap 95% CI:
  scarce f3_pi1 .69 [.55, .81], f3v2d .73 [.62, .82], v3 .78 [.71, .83]; real f3_pi1 .83
  [.64, .95], f3v2d .80 [.63, .92], v3 .83 [.67, .94] (scarce 32 regimes, real 10 streams).
- **Regime map (median L by x).**

| x = r d / h | scarce f3v2d | scarce v3 | real f3v2d | real v3 | real f3_pi1 |
|---|---|---|---|---|---|
| < .5 | .12 | .12 | .05 | .04 | .33 |
| .5 - 1 | .61 | .81 | .50 | .50 | .58 |
| 1 - 2 | 1.18 | 1.15 | .98 | 1.00 | .90 |
| >= 2 | 1.12 | 1.14 | 1.08 | 1.08 | 1.10 |

  With paced sampling, F3 keeps about 90-96% of wald_cut's improvement when one delay window holds
  less than half the headroom in exposure, and keeps none of it (as costly as never switching) once
  the window exceeds the headroom, as Proposition 3 says it must. Full sampling loses a third even
  at small x, because it spends one label per exposed round.
- **Confounding check.** OLS of L on log x and log(labels per exposed round): the log x
  coefficient is positive in all six fits (.13-.31); the label coefficient is small with mixed sign.
- **Post-hoc (not pre-stated): holding h fixed,** Spearman(r d, L) is positive at every h for every
  arm and source (+.07 to +.83), so the effect is not only "more headroom costs less".
- **Caveats.** Within a source, the units for one regime share tapes across h and arms; the
  bootstrap resamples regimes/streams to account for this. Real streams: 10 of 14 pass the 10% gain
  filter, all were seen before. No PaperBanana figure yet (PaperBanana is not installed here).

## Calibrated comparators (2026-11-17; `results/riskbudget/calib_{summary.json,tables.md}`)
Stop-loss with margin c and CUSUM rollback with threshold h_c plus a resolved-harm stop, each
calibrated on dev seeds 80000-80199 to the shield's standard (violation <= .05 in every one of 30
regimes); frozen in `configs/paper3/f3_calibrated_comparators_v1.json`; evaluated on dev seeds
81000-81999 and on the real streams (THIRD LOOK; transferred by headroom).
- Stop-loss: the smallest margin meeting the standard (c = 7, 15, 25 at R = 12, 20, 30) blocks every
  promotion (c > R - 2k). Deployed fraction 0; J 73.53 against never 71.59 and shield 69.51 (R=20).
  Same on real streams (J 603.6, never 597.9).
- CUSUM rollback: standard not reachable at R = 12, 20 (fresh worst-regime .535, .671 in
  dropout_adverse; J above never by 8.5 and 12.1). At R = 30 it met the standard on calibration
  seeds (.040) but not on fresh seeds (.099 [.082, .119]). Real streams, clean h = 14: cheaper than
  the shield by 50.2 [19.8, 91.9] per episode but 443 / 4,600 runs over budget (1,872 adverse
  dropout, 1,115 adverse delay).
- Not tried: a comparator combining a margin with a CUSUM threshold.
