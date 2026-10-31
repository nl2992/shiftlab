# 11 Experiment Type II: optimised-controller comparison (H6 and H1 under tuning)

**Label: development, synthetic (Setting C). Seeds < 7,000,000 only. Nothing here is confirmatory.**
Script: `scripts/decision_value/run_type2_tuning.py`. Engine unchanged. This section (Design) was written
BEFORE any evaluation-seed run; results are appended below it afterwards.

## 1. Question

Doc 06 found that with fixed, untuned controllers (Permanent / Hold(L/2)) a monitor beat the best simple
reference by >= MME in only 1 of 66 cells. Is "sequential monitors rarely beat simple deployment policies" an
artifact of those untuned controllers? Type II tunes the *whole system* (controller, controller parameter,
alarm level) for each monitor, and gives the simple-policy family a comparable tuning budget.

## 2. Design (frozen before evaluation)

**Cells (11), all paired target, c_q = 0, other parameters as in the originating experiment:**

| id | family | params | q | d | c_s | origin |
|---|---|---|---|---|---|---|
| th3_rho{0.995,0.999}_d{0,50}_useful | S2 | challenger_bad=useful | 0.2 | 0/50 | 2 | TH-3 |
| th3_rho0.999_d0_useless | S2 | challenger_bad=useless (negative control) | 0.2 | 0 | 2 | TH-3 |
| th4_L{400,1600}_d{0,50} | S1 | L as named | 0.5 | 0/50 | 5 | TH-4 |
| th2_strong, th2_weak | S3 | challenger=strong / weak | 0.2 | 50 | 5 | TH-2 (paired target) |

T = 3000, p0 = 0.2, Delta = 0.15, delta = 0.05 (family defaults).

**Monitor systems (32 per monitor, 160 total per cell):** monitors cusum, page_hinkley, batch, sr_betting,
kelly_h2c_inspired (engine defaults, as doc 06) x controller in {Permanent, Hold(H) for
H in {25,50,100,200,400,800}, Reverse} (8 controllers) x alpha in {0.01, 0.05, 0.2, 0.5}. Thresholds are the
(1-alpha) "higher" quantile of the null max statistic (n_cal = 6000, seed 5,000,000, same as doc 06; null data
are family-independent, so calibration is keyed on (monitor, q, d)). Reverse reuses the main threshold, as in the
earlier engine scripts.

**Simple-reference family (32 configs, no monitor, no calibration):** never; always;
CalendarBatch(K) with decision margin m (K in {25,50,100,200,400,800} x m in {0,0.01,0.02,0.05}: every K steps
move to the challenger only if the released window-mean advantage mean(l0)-mean(l1) exceeds m, move back only if
it is below -m, otherwise keep the current action; m = 0 is the engine CalendarBatch except for ties) = 24
configs; StaticThreshold(W) with margin m (W in {50,100,200} x m in {0,0.02}: engine rule plus the extra condition
buffer-mean-gap > m) = 6 configs. 2 + 24 + 6 = 32. The batch monitor with Hold is the "monitor-free
fixed-sample" analogue and is counted among the monitors.

**Seeds and selection.** Tuning seed = 100000 + cell index, n = 500 (CRN: every config in a cell sees the same
episodes). Selection criterion: mean expected net cost `cost_exp` (loss + c_s x switches; c_q = 0) on tuning
seeds. Per cell select (a) best config per monitor, (b) best monitor overall (= best of (a)), (c) best simple.
Evaluation seed = 200000 + cell index (fresh, disjoint), n = 2000; only selected configs (plus never, always,
oracles) are evaluated.

**Primary estimand (per cell):** Dsys = mean over eval episodes of [cost(best simple) - cost(best monitor
overall)] (positive = monitor system better), 95% paired percentile bootstrap (10,000 resamples), two-sided
bootstrap p; Holm correction across the 11 cells. MME = 1% of never-switch cost in the cell. Classification:
"monitor wins" iff Dsys >= MME, CI lower bound > 0 and Holm-adjusted p < 0.05; "simple wins" symmetric;
otherwise tie. Secondary: the same difference per monitor, fraction of headroom captured =
(never - cost)/(never - dynamic oracle) for each selected system, N_s, best static, dynamic oracle, and selection
optimism = tuning-seed cost minus evaluation-seed cost of the selected config (positive = selected config looks
better than it is).

**H1 under tuning:** per cell, Kendall tau between the tuned monitors' detection ranking (power_T at the chosen
alpha on eval seeds; also delay) and their tuned value ranking (never - cost) over the 5 monitors; plus the
engine protocol reversal classifier on the 20 ordered monitor pairs (power diff >= 0.05 with CI excluding 0 AND
cost disadvantage >= MME with CI excluding 0).

**Pre-declared verdict rules.** H6 ("simple policies are competitive") is *not an artifact of untuned
controllers* if the monitor system wins in <= 1 of the 10 non-control cells; it is *falsified under tuning* if the
monitor system wins in >= 4 of 10 non-control cells; 2-3 cells = mixed. H1 (detection ranking can reverse the cost
ranking) is *supported under tuning* if protocol reversals occur in >= 1 cell among the tuned monitors AND tau < 0
in >= 3 cells; otherwise *not supported / unresolved*. Negative control: in th3_rho0.999_d0_useless no system
should beat never-switch; a monitor win there is a pipeline red flag.

**Known limitations (declared up front).** (i) Selection over 160 configs on n = 500 is noisy; the winner's curse
is measured, not corrected. (ii) The simple family has 32 configs vs 160 monitor configs; comparing the best-of-160
to best-of-32 favours monitors by a max-of-more-draws effect on the tuning seeds, but evaluation is on fresh seeds,
so this only affects which config is picked, not bias of the reported cost. (iii) Hold/Reverse horizons are
tuned per cell, i.e. with knowledge of the cell's L / rho; this is an oracle-tuned monitor system, an upper bound
for monitors. (iv) One tuning/eval seed pair per cell; cells share monitor implementations, not independent.

---

# Results (run `type2_20261031T020507Z`, development)

## 3. Commands and runtime

```
PYTHONPATH=src python scripts/decision_value/run_type2_tuning.py run --procs 4        # full run
PYTHONPATH=src python scripts/decision_value/run_type2_tuning.py run --procs 4 --n-tune 20 --n-eval 40 --cells th4_L400_d0 --tag smoke   # pipeline smoke test only (tiny n; output dir type2_smoke_*, not analysed)
PYTHONPATH=src python scripts/decision_value/run_type2_tuning.py analyze --dir outputs/decision_value/development/type2_20261031T020507Z
```
Outputs (gitignored): `outputs/decision_value/development/type2_20261031T020507Z/{cells/,results.json,tables.md}`; log
`outputs/decision_value/logs/type2_run.log`; registry entry appended to `outputs/decision_value/manifests/run_registry.jsonl`
(run_id `type2_20261031T020507Z`; a second entry `type2_smoke_*` is the tiny smoke run). Runtime 287 s on 4 processes of a shared
machine (calibration 16 s, tuning+evaluation 261 s, ~85 s per cell). Calibration null check: the family-independence of the
null data (s1 vs s2 vs s3 `null=True` batches are bit-identical for the same seed) was verified before the run. Engine unchanged.

Implementation notes: tuning uses the Rao-Blackwellised `cost_exp` computed lean (loss + c_s x switches); evaluation uses the engine
`score`. Simple-policy margin controllers (`CalendarMargin`, `StaticMargin`) live in the script, not the engine. S2 cells have no
change-time `tau` for episodes whose regime never leaves state 0, so `delay_cens` is NaN there and tau(delay, value) is undefined.

## 4. System-level result (best monitor system vs best simple policy, fresh eval seeds, n = 2000)

diff = cost(best simple) - cost(best monitor system); positive = monitor system better. MME = 1% of never-switch cost.

## Per-cell system-level comparison (eval seeds; diff = cost(best simple) - cost(best monitor system), positive = monitor better)

| cell | best monitor system (tuned) | cost | best simple (tuned) | cost | diff [95% CI] | MME | Holm p | winner |
|---|---|---|---|---|---|---|---|---|
| th3_rho0.995_d0_useful | kelly_h2c_inspired|permanent|0.5 | 690.72 | always | 677.01 | -13.71 [-14.78, -12.64] | 8.25 | 0.0011 | simple |
| th3_rho0.995_d50_useful | kelly_h2c_inspired|permanent|0.5 | 695.19 | always | 676.98 | -18.21 [-19.38, -17.09] | 8.25 | 0.0011 | simple |
| th3_rho0.999_d0_useful | kelly_h2c_inspired|reverse|0.5 | 672.73 | always | 677.84 | 5.11 [2.88, 7.36] | 8.22 | 0.0011 | tie |
| th3_rho0.999_d50_useful | kelly_h2c_inspired|reverse|0.5 | 680.38 | always | 676.10 | -4.28 [-6.55, -2.06] | 8.28 | 0.0011 | tie |
| th3_rho0.999_d0_useless | page_hinkley|hold:25|0.01 | 823.80 | never | 823.70 | -0.10 [-0.13, -0.08] | 8.24 | 0.0011 | tie |
| th4_L400_d0 | cusum|hold:200|0.05 | 660.40 | never | 660.00 | -0.40 [-0.82, 0.02] | 6.60 | 0.1318 | tie |
| th4_L400_d50 | batch|hold:200|0.01 | 660.79 | never | 660.00 | -0.79 [-1.01, -0.57] | 6.60 | 0.0011 | tie |
| th4_L1600_d0 | cusum|permanent|0.5 | 723.18 | statm:200:0.0 | 722.80 | -0.39 [-0.92, 0.16] | 8.40 | 0.1683 | tie |
| th4_L1600_d50 | cusum|permanent|0.5 | 727.16 | statm:200:0.0 | 724.25 | -2.90 [-3.46, -2.35] | 8.40 | 0.0011 | tie |
| th2_strong | cusum|permanent|0.5 | 738.95 | statm:100:0.0 | 726.19 | -12.76 [-13.69, -11.85] | 9.00 | 0.0011 | simple |
| th2_weak | cusum|permanent|0.5 | 864.33 | statm:100:0.02 | 859.16 | -5.17 [-5.74, -4.63] | 9.00 | 0.0011 | tie |

## Reference costs, headroom capture, switches, selection optimism

| cell | never | always | static* | dynamic | headroom | captured monitor | captured simple | N_s mon | N_s simple | optimism mon | optimism simple |
|---|---|---|---|---|---|---|---|---|---|---|---|
| th3_rho0.995_d0_useful | 824.97 | 677.01 | 676.50 | 624.60 | 200.37 | 0.67 | 0.74 | 0.98 | 1.00 | 2.36 | 1.13 |
| th3_rho0.995_d50_useful | 825.06 | 676.98 | 676.41 | 624.44 | 200.62 | 0.65 | 0.74 | 0.98 | 1.00 | -0.64 | -0.76 |
| th3_rho0.999_d0_useful | 822.48 | 677.84 | 662.23 | 606.57 | 215.91 | 0.69 | 0.67 | 2.87 | 1.00 | 0.06 | -0.01 |
| th3_rho0.999_d50_useful | 827.69 | 676.10 | 662.06 | 606.75 | 220.95 | 0.67 | 0.69 | 2.85 | 1.00 | 1.11 | 1.29 |
| th3_rho0.999_d0_useless | 823.70 | 901.13 | 823.70 | 823.70 | -0.00 | NA | NA | 0.05 | 0.00 | 1.64 | 1.64 |
| th4_L400_d0 | 660.00 | 755.00 | 660.00 | 630.00 | 30.00 | -0.01 | 0.00 | 1.66 | 0.00 | -0.90 | 0.00 |
| th4_L400_d50 | 660.00 | 755.00 | 660.00 | 630.00 | 30.00 | -0.03 | 0.00 | 0.30 | 0.00 | -0.11 | 0.00 |
| th4_L1600_d0 | 840.00 | 755.00 | 755.00 | 690.00 | 150.00 | 0.78 | 0.78 | 1.00 | 1.00 | -0.04 | -0.19 |
| th4_L1600_d50 | 840.00 | 755.00 | 755.00 | 690.00 | 150.00 | 0.75 | 0.77 | 1.00 | 1.00 | -0.21 | 0.14 |
| th2_strong | 900.05 | 755.00 | 755.00 | 705.02 | 195.03 | 0.83 | 0.89 | 1.00 | 1.00 | -0.87 | 0.68 |
| th2_weak | 899.83 | 894.92 | 892.98 | 844.86 | 54.97 | 0.65 | 0.74 | 0.97 | 1.00 | -0.75 | -0.25 |

(*static = per-episode hindsight best of never/always, oracle.) Optimism = tuning-seed cost - eval-seed cost of the selected config.

## Per-monitor tuned systems vs best simple (secondary)

| cell | monitor | tuned (controller|alpha) | cost | simple - monitor [CI] | power_T | delay_cens | N_s | optimism |
|---|---|---|---|---|---|---|---|---|
| th3_rho0.995_d0_useful | cusum | permanent|0.5 | 699.24 | -22.23 [-23.32, -21.17] | 1.00 | 494 | 1.00 | 0.82 |
| th3_rho0.995_d0_useful | page_hinkley | permanent|0.5 | 762.79 | -85.78 [-88.97, -82.67] | 0.75 | 1750 | 0.75 | 6.01 |
| th3_rho0.995_d0_useful | batch | permanent|0.5 | 708.25 | -31.24 [-32.51, -30.02] | 1.00 | 592 | 1.00 | 1.90 |
| th3_rho0.995_d0_useful | sr_betting | permanent|0.5 | 708.09 | -31.09 [-32.38, -29.85] | 1.00 | 663 | 1.00 | 1.52 |
| th3_rho0.995_d0_useful | kelly_h2c_inspired | permanent|0.5 | 690.72 | -13.71 [-14.82, -12.65] | 0.98 | 342 | 0.98 | 2.36 |
| th3_rho0.995_d50_useful | cusum | permanent|0.5 | 703.48 | -26.50 [-27.60, -25.41] | 1.00 | 519 | 1.00 | -0.74 |
| th3_rho0.995_d50_useful | page_hinkley | permanent|0.5 | 769.65 | -92.67 [-95.96, -89.42] | 0.72 | 1829 | 0.72 | 1.27 |
| th3_rho0.995_d50_useful | batch | permanent|0.5 | 710.43 | -33.45 [-34.72, -32.19] | 0.99 | 620 | 0.99 | -0.51 |
| th3_rho0.995_d50_useful | sr_betting | permanent|0.5 | 712.93 | -35.95 [-37.26, -34.68] | 1.00 | 704 | 1.00 | -1.94 |
| th3_rho0.995_d50_useful | kelly_h2c_inspired | permanent|0.5 | 695.19 | -18.21 [-19.34, -17.09] | 0.98 | 385 | 0.98 | -0.64 |
| th3_rho0.999_d0_useful | cusum | reverse|0.5 | 674.81 | 3.03 [0.69, 5.43] | 0.95 | nan | 2.15 | 0.79 |
| th3_rho0.999_d0_useful | page_hinkley | permanent|0.5 | 749.91 | -72.07 [-77.76, -66.35] | 0.68 | nan | 0.70 | 2.43 |
| th3_rho0.999_d0_useful | batch | reverse|0.5 | 689.05 | -11.21 [-13.74, -8.56] | 0.94 | nan | 1.98 | 0.41 |
| th3_rho0.999_d0_useful | sr_betting | reverse|0.5 | 685.13 | -7.29 [-10.00, -4.55] | 0.94 | nan | 1.85 | -1.98 |
| th3_rho0.999_d0_useful | kelly_h2c_inspired | reverse|0.5 | 672.73 | 5.11 [2.95, 7.35] | 0.93 | nan | 2.87 | 0.06 |
| th3_rho0.999_d50_useful | cusum | reverse|0.5 | 683.40 | -7.30 [-9.85, -4.83] | 0.95 | nan | 2.11 | 2.46 |
| th3_rho0.999_d50_useful | page_hinkley | permanent|0.5 | 753.13 | -77.03 [-83.10, -71.14] | 0.71 | nan | 0.73 | 4.48 |
| th3_rho0.999_d50_useful | batch | permanent|0.5 | 695.06 | -18.96 [-21.25, -16.69] | 0.94 | nan | 0.96 | 3.15 |
| th3_rho0.999_d50_useful | sr_betting | reverse|0.5 | 692.39 | -16.28 [-19.16, -13.49] | 0.95 | nan | 1.82 | 1.98 |
| th3_rho0.999_d50_useful | kelly_h2c_inspired | reverse|0.5 | 680.38 | -4.28 [-6.58, -2.02] | 0.93 | nan | 2.85 | 1.11 |
| th3_rho0.999_d0_useless | cusum | hold:25|0.01 | 824.30 | -0.60 [-0.67, -0.53] | 0.14 | nan | 0.29 | 1.62 |
| th3_rho0.999_d0_useless | page_hinkley | hold:25|0.01 | 823.80 | -0.10 [-0.13, -0.08] | 0.02 | nan | 0.05 | 1.64 |
| th3_rho0.999_d0_useless | batch | hold:25|0.01 | 823.83 | -0.13 [-0.17, -0.10] | 0.03 | nan | 0.06 | 1.66 |
| th3_rho0.999_d0_useless | sr_betting | hold:25|0.01 | 823.95 | -0.25 [-0.30, -0.21] | 0.06 | nan | 0.12 | 1.58 |
| th3_rho0.999_d0_useless | kelly_h2c_inspired | hold:25|0.01 | 823.94 | -0.25 [-0.29, -0.20] | 0.05 | nan | 0.12 | 1.57 |
| th4_L400_d0 | cusum | hold:200|0.05 | 660.40 | -0.40 [-0.82, 0.02] | 0.79 | 614 | 1.66 | -0.90 |
| th4_L400_d0 | page_hinkley | hold:25|0.01 | 660.58 | -0.58 [-0.69, -0.48] | 0.06 | 1914 | 0.12 | 0.23 |
| th4_L400_d0 | batch | hold:200|0.01 | 660.21 | -0.21 [-0.41, -0.01] | 0.16 | 1722 | 0.33 | -0.30 |
| th4_L400_d0 | sr_betting | hold:200|0.05 | 660.86 | -0.86 [-1.26, -0.46] | 0.62 | 933 | 1.31 | -0.47 |
| th4_L400_d0 | kelly_h2c_inspired | hold:200|0.01 | 661.26 | -1.26 [-1.53, -0.99] | 0.28 | 1520 | 0.59 | 0.17 |
| th4_L400_d50 | cusum | hold:200|0.2 | 663.79 | -3.79 [-4.33, -3.25] | 0.92 | 405 | 2.27 | -1.13 |
| th4_L400_d50 | page_hinkley | hold:25|0.01 | 660.74 | -0.74 [-0.85, -0.62] | 0.07 | 1895 | 0.14 | -0.04 |
| th4_L400_d50 | batch | hold:200|0.01 | 660.79 | -0.79 [-1.01, -0.57] | 0.15 | 1750 | 0.30 | -0.11 |
| th4_L400_d50 | sr_betting | hold:100|0.01 | 662.51 | -2.51 [-2.73, -2.29] | 0.36 | 1403 | 0.72 | -0.23 |
| th4_L400_d50 | kelly_h2c_inspired | hold:100|0.01 | 662.43 | -2.43 [-2.66, -2.20] | 0.29 | 1511 | 0.64 | 0.01 |
| th4_L1600_d0 | cusum | permanent|0.5 | 723.18 | -0.39 [-0.94, 0.14] | 1.00 | 161 | 1.00 | -0.04 |
| th4_L1600_d0 | page_hinkley | permanent|0.5 | 729.04 | -6.24 [-6.90, -5.61] | 1.00 | 230 | 1.00 | 0.51 |
| th4_L1600_d0 | batch | permanent|0.5 | 732.50 | -9.71 [-10.66, -8.79] | 1.00 | 275 | 1.00 | -1.01 |
| th4_L1600_d0 | sr_betting | permanent|0.5 | 724.27 | -1.48 [-2.06, -0.90] | 1.00 | 183 | 1.00 | -0.10 |
| th4_L1600_d0 | kelly_h2c_inspired | permanent|0.5 | 742.21 | -19.41 [-20.32, -18.53] | 1.00 | 345 | 1.00 | -0.98 |
| th4_L1600_d50 | cusum | permanent|0.5 | 727.16 | -2.90 [-3.45, -2.36] | 1.00 | 215 | 1.00 | -0.21 |
| th4_L1600_d50 | page_hinkley | permanent|0.5 | 732.83 | -8.58 [-9.25, -7.93] | 1.00 | 272 | 1.00 | -0.61 |
| th4_L1600_d50 | batch | permanent|0.5 | 735.07 | -10.82 [-11.72, -9.93] | 1.00 | 308 | 1.00 | -0.41 |
| th4_L1600_d50 | sr_betting | permanent|0.5 | 728.40 | -4.15 [-4.76, -3.56] | 1.00 | 236 | 1.00 | 0.08 |
| th4_L1600_d50 | kelly_h2c_inspired | permanent|0.5 | 743.79 | -19.54 [-20.43, -18.70] | 1.00 | 392 | 1.00 | -0.04 |
| th2_strong | cusum | permanent|0.5 | 738.95 | -12.76 [-13.70, -11.84] | 1.00 | 344 | 1.00 | -0.87 |
| th2_strong | page_hinkley | permanent|0.5 | 750.50 | -24.31 [-25.82, -22.83] | 0.99 | 450 | 0.99 | 2.06 |
| th2_strong | batch | permanent|0.5 | 750.37 | -24.18 [-25.53, -22.89] | 1.00 | 473 | 1.00 | 0.37 |
| th2_strong | sr_betting | permanent|0.5 | 742.74 | -16.55 [-17.55, -15.57] | 1.00 | 387 | 1.00 | -0.06 |
| th2_strong | kelly_h2c_inspired | permanent|0.5 | 754.42 | -28.23 [-29.89, -26.62] | 0.96 | 613 | 0.98 | -1.04 |
| th2_weak | cusum | permanent|0.5 | 864.33 | -5.17 [-5.74, -4.62] | 0.96 | 611 | 0.97 | -0.75 |
| th2_weak | page_hinkley | permanent|0.5 | 868.23 | -9.06 [-9.76, -8.39] | 0.90 | 774 | 0.90 | -1.32 |
| th2_weak | batch | permanent|0.5 | 870.57 | -11.40 [-12.08, -10.74] | 0.90 | 849 | 0.92 | -1.10 |
| th2_weak | sr_betting | permanent|0.5 | 866.06 | -6.90 [-7.50, -6.31] | 0.96 | 702 | 0.97 | -0.45 |
| th2_weak | kelly_h2c_inspired | permanent|0.5 | 880.01 | -20.85 [-21.65, -20.07] | 0.59 | 1247 | 0.76 | -0.89 |

## H1 under tuning: detection ranking vs tuned cost ranking

| cell | tau(power_T, value) | tau(-delay, value) | protocol reversals (power, of 20 pairs) |
|---|---|---|---|
| th3_rho0.995_d0_useful | 0.32 | 0.80 | 0 |
| th3_rho0.995_d50_useful | 0.20 | 1.00 | 0 |
| th3_rho0.999_d0_useful | 0.40 | nan | 0 |
| th3_rho0.999_d50_useful | 0.40 | nan | 0 |
| th3_rho0.999_d0_useless | -1.00 | nan | 0 |
| th4_L400_d0 | 0.00 | 0.00 | 0 |
| th4_L400_d50 | -1.00 | -1.00 | 0 |
| th4_L1600_d0 | 0.84 | 1.00 | 0 |
| th4_L1600_d50 | 0.77 | 1.00 | 0 |
| th2_strong | 0.95 | 0.80 | 0 |
| th2_weak | 1.00 | 1.00 | 0 |

Non-control cells (10): monitor wins 0, simple wins 3, ties 7.

## 5. Interpretation

1. **Non-control cells: monitor system wins 0 of 10, simple policy wins 3 (th3 rho=0.995 d=0 and d=50, th2 strong), ties 7.** By the
   pre-declared rule (monitor wins <= 1 of 10), "sequential monitors rarely beat simple policies" is **not an artifact of untuned
   controllers** in this synthetic family. Doc 06's 1/66 became 0/10 here. The one cell where the tuned monitor point estimate is
   ahead (th3 rho=0.999, d=0: +5.1 [2.9, 7.4], kelly + Reverse) is below the MME (8.2) and is a tie by the rule; at d=50 the sign flips
   (-4.3). Per-monitor comparisons are worse than the system-level one in almost every case (best monitor overall is usually cusum or
   kelly).
2. **Tuning converges to the simple policy.** In 8 of the 10 non-control cells the chosen monitor system is Permanent at the largest
   alpha on the grid (0.5), or Reverse/Permanent at alpha = 0.5 in the S2 cells, i.e. a near-immediate one-way switch; it is a
   noisier version of `always` / a static-threshold policy, and the best simple policy is `always` (S2), `statm` (S1 long, S3) or
   `never` (S1 short). The tuned alpha sits on the grid boundary, so this experiment cannot say how much further a larger alpha
   (or a different monitor-level parameterisation) would help; the tuned monitor cannot do better than "act earlier", and the simple
   policies do exactly that without paying for a calibrated threshold. Honest reading: the grid may be too narrow at the top end, but the
   direction of the optimum (towards alpha -> 1, i.e. no evidence requirement) is itself the finding.
3. **Headroom.** Captured fractions are comparable (S2 rho=0.995: monitor 0.65-0.67 vs simple 0.74; rho=0.999: 0.67-0.69 vs 0.67-0.69;
   S1 L=1600: 0.75-0.78 both; S3 strong 0.83 vs 0.89; weak 0.65 vs 0.74). S1 L=400 has headroom 30 (per-episode) and neither system
   captures any of it (-0.03..0.00): transient-burst with the best simple policy being `never`.
4. **Negative control** (th3 rho=0.999 d=0 useless): headroom 0; the best monitor system (page_hinkley + Hold(25), alpha=0.01) costs
   +0.10 over never (CI [0.08, 0.13] in the simple-minus-monitor direction, i.e. monitor slightly worse); no false win. Pipeline sanity OK.
5. **Selection optimism** is small relative to MME (|optimism| mostly < 2.5 and of either sign; largest 2.4 for kelly at S2 rho=0.995
   d=0, per-monitor up to 6.0 for page_hinkley). It does not explain the result: the monitor systems lose on fresh seeds even though
   tuning picked them from 160 configs. The simple family's best-of-32 optimism is similar (-0.8 to 1.6).
6. Several tuned monitors choose Hold(200) at alpha 0.01-0.05 in S1 L=400: these are essentially "do nothing" systems (N_s about 0.3-1.7,
   cost within 1 of never, headroom capture about 0).

## 6. Verdicts under tuning

- **H6 (simple policies competitive with monitors): SUPPORTED under tuning**, and not an untuned-controller artifact (0 monitor wins of
  10, 3 simple wins; pre-declared criterion <= 1). Scope: synthetic Setting C, paired target, five default monitors, this grid, one
  tuning/eval seed pair per cell; the grid-boundary alpha and the oracle-tuned controller horizon (an upper bound for monitors) are the
  main caveats. Doc 06's caveat "monitors run with untuned controllers" is now answered for these cells.
- **H1 (detection ranking can reverse the cost ranking): NOT SUPPORTED under tuning in these cells.** 0 protocol reversals among the 20
  ordered monitor pairs in every cell. tau(power_T, tuned value) is positive in 8 cells (0.20-1.00), 0.00 in th4_L400_d0 (all costs within 1.3 of
  never), and negative in only 2: th4_L400_d50 (-1.00) and the useless-fallback control (-1.00), both cells where every monitor's value is
  within about 4 and 0.6 of zero (below MME), so those taus rank noise. The pre-declared support rule needed tau < 0 in >= 3 cells and a
  protocol reversal; neither holds. This contrasts with doc 06 (16/1620 reversals with untuned Hold): tuning removes the
  reversals (each monitor picks the controller/alpha that suits it, which re-aligns detection speed with value in the cells where there
  is value to capture). tau(-delay, value) is >= 0.8 in the six cells with value to capture where it is defined (th3 rho=0.995 x2, th4 L=1600 x2, th2 x2); undefined (NaN) in the other S2 cells.
- Not tested here: the doc-06 reversal mechanisms (incumbent target under common_shock/reversing), real data, other c_s, q, L-grid
  neighbours, and larger alpha grids. Confirmation seeds untouched.

## 7. Limitations and next steps

- Extend alpha beyond 0.5 (e.g. 0.8, 0.95) and Hold horizons for S1 L=400 to see whether the boundary result is an artifact of the grid; add a
  monitor-score margin controller (switch if statistic > thr and window gain > m) to test whether monitors can add value beyond calendar/static.
- Single seed pair per cell; tune/eval separation is clean, but cell-to-cell conclusions share monitor implementations.
- Continue / pivot / stop (development): the "monitor value over simple policies" claim is weakly supported for the incumbent-monitoring
  story in these regimes; the live, differentiating questions are the mismatched-target and cost-aware cases (TH-2 reversals) and the
  information-budget setting, not detection-power ranking.

---

# 8. Asymmetric regimes and extended grids (follow-up; design written BEFORE running)

**Label: development, synthetic. Seeds < 7,000,000. Nothing confirmatory.** Motivation (coordinator): in the symmetric S2 chain
(pi_b = 0.5, useful fallback) `always` is near-optimal and favours static policies. Monitoring should matter most when the bad state is
rare and persistent, so that both `never` and `always` are poor. Also, section 5 found the tuned alpha at the top of the grid (0.5), so the
grid is extended to test whether that boundary mattered.

## 8.1 Engine change (backward compatible)

`synthetic.py`, family S2: optional params `rho_g`, `rho_b` (stay probabilities of the good / bad state; default `None` = old symmetric
path with the same random draws). If either is given the other defaults to `rho`; the initial state is drawn from the stationary
distribution pi_b = (1-rho_g)/(2-rho_g-rho_b); transition rule is the old one (flip iff uniform > stay prob of the current state), so
`rho_g = rho_b = rho` reproduces the symmetric path bit-identically. Checks: (a) SHA-256 of one old cell's data (s2, rho 0.995 useful and
rho 0.999 useless, seed 100000, n = 200, q = 0.2, d = 50: l0, l1, mask, mu0, regime, tau) is identical before and after the change
(`bf4ff827...`); (b) new test `test_s2_asymmetric_chain` (explicit symmetric = default bit-identical; empirical bad fraction within 0.01 of pi_b;
stationary initial state; mean bad-run length within 15 of 1/(1-rho_b)); (c) full decision-value suite: 31 passed (30 before + 1 new).
Mean bad run B = 1/(1-rho_b); 1 - rho_g = pi_b (1-rho_b)/(1-pi_b).

## 8.2 Cells

S2, useful fallback, Delta = 0.15, delta = 0.05, c_s = 2, q = 0.2, T = 3000, paired target, c_q = 0. B in {100, 400, 1000} x pi_b in {0.1, 0.25} x
d in {0, 50} = 12 cells (`asym_B{B}_pi{pi}_d{d}_useful`), plus one negative control `asym_B400_pi0.1_d0_useless` (13 cells). Per cell we report never,
always, hindsight static, dynamic oracle, headroom H_T = never - dynamic, and the P5 ceiling per alarm
theta_max = pi_b + (1-pi_b) lambda^(d+1), lambda = rho_g + rho_b - 1 (precision ceiling of an alarm raised at the release of an event that
was in the bad state; the symmetric formula of the TH-3 analysis with pi_b and lambda of the asymmetric chain).

## 8.3 Tuning protocol (extended)

Same as sections 2: monitors cusum, page_hinkley, batch, sr_betting, kelly_h2c_inspired x controllers {Permanent, Hold(H), Reverse} x alpha, with
alpha in {0.01, 0.05, 0.2, 0.5, 0.8, 0.95} and Hold H in {25, 50, 100, 200, 400, 800, 1000, 1600} (10 controllers): 60 configs per monitor,
**300 monitor configs per cell**. Thresholds: same null calibration (n_cal = 6000, seed 5,000,000), new cache files for the extended alpha grid.
Simple family (extended so counts stay comparable): never, always, CalendarBatch(K) with margin m for K in {25, 50, 100, 200, 400, 800, 1000, 1600}
x m in {0, 0.01, 0.02, 0.05, 0.1} (40), StaticThreshold(W) with margin m for W in {50, 100, 200, 400} x m in {0, 0.02, 0.05} (12): **54 simple
configs** (original run: 160 vs 32; now 300 vs 54, i.e. 60 per monitor vs 54).
Seeds: asymmetric cells tuning 300000 + cell index (n = 500), evaluation 400000 + cell index (n = 2000), fresh. Selection by mean `cost_exp` on
tuning seeds; primary estimand, MME, bootstrap (10,000), Holm (across the 13 asymmetric cells; the control is included in the family),
winner rule: identical to section 2.

**Original cells re-run with the extended grids ("orig_ext")**: the 11 cells of section 2 on the SAME tuning (100000 + idx) and evaluation
(200000 + idx) seeds as the first run, same extended grids. Caveat declared up front: the evaluation seeds are not fresh (the first run's
results on them were seen when the grid extension was decided); selection still uses only tuning seeds, so the winner's-curse
protection is intact, but the grid-extension decision is a researcher degree of freedom. Holm family: these 11 cells.

## 8.4 Pre-declared verdict rules

- *H6 is symmetric-chain-dependent* if the monitor system wins (>= MME, CI > 0, Holm p < 0.05) in >= 3 of the 12 useful asymmetric cells;
  *H6 robust to asymmetry* if <= 1; 2 = mixed. A monitor win in the negative control is a red flag.
- *The alpha boundary mattered* if, in any original non-control cell, the extended grid changes the winner classification or improves the
  monitor-system diff by >= MME. It "still sits at the boundary" if the selected alpha equals the grid maximum (0.95) or the Hold H equals 1600.
- Headroom: report fraction captured by monitor system and simple policy; no pre-declared threshold.
- Limitations as in section 2 plus: one seed pair per cell; asymmetric chains with B = 1000 give few bad runs per episode (T = 3000, so some
  episodes never see a bad state, which has no delay/tau).


## 8.5 Commands and runtime

```
PYTHONPATH=src python scripts/decision_value/run_type2_tuning.py run --procs 4 --suite asym       # run type2_asym_20261031T021545Z
PYTHONPATH=src python scripts/decision_value/run_type2_tuning.py run --procs 4 --suite orig_ext   # run type2_orig_ext_20261031T022617Z
```
Script changed from the first run only by adding the `--suite` option and per-suite grids (suite `orig` unchanged; first-run outputs untouched). Outputs
(gitignored): `outputs/decision_value/development/type2_asym_20261031T021545Z/` and `.../type2_orig_ext_20261031T022617Z/` (`tables.md` also holds the
per-monitor secondary tables; `results.json`; `cells/`); logs `outputs/decision_value/logs/type2_asym.log`, `type2_orig_ext.log`; two registry entries appended.
Runtime: asym 629 s (calibration 10 s, simulation 607 s), orig_ext 506 s (13 s + 482 s), 4 processes, shared machine. (`type2_asym_smoke_*` is a tiny
pipeline smoke run, not analysed.) Config counts: 300 monitor configs (60 per monitor) vs 54 simple per cell.

## 8.6 Asymmetric cells (fresh seeds 300000+/400000+, n_tune = 500, n_eval = 2000)

### Per-cell system-level comparison (eval seeds; diff = cost(best simple) - cost(best monitor system), positive = monitor better)

| cell | best monitor system (tuned) | cost | best simple (tuned) | cost | diff [95% CI] | MME | Holm p | winner |
|---|---|---|---|---|---|---|---|---|
| asym_B100_pi0.1_d0_useful | page_hinkley|hold:200|0.01 | 644.49 | calm:1600:0.1 | 644.54 | 0.04 [-0.07, 0.17] | 6.44 | 0.8430 | tie |
| asym_B100_pi0.1_d50_useful | page_hinkley|hold:50|0.01 | 646.29 | never | 646.19 | -0.10 [-0.14, -0.06] | 6.46 | 0.0013 | tie |
| asym_B100_pi0.25_d0_useful | cusum|reverse|0.95 | 702.27 | statm:200:0.05 | 711.69 | 9.42 [7.88, 10.96] | 7.13 | 0.0013 | monitor |
| asym_B100_pi0.25_d50_useful | sr_betting|hold:800|0.2 | 713.62 | calm:1600:0.1 | 713.16 | -0.46 [-1.62, 0.69] | 7.13 | 0.8430 | tie |
| asym_B400_pi0.1_d0_useful | cusum|hold:400|0.2 | 637.13 | calm:1600:0.1 | 644.54 | 7.40 [6.04, 8.79] | 6.44 | 0.0013 | monitor |
| asym_B400_pi0.1_d50_useful | cusum|hold:400|0.2 | 640.13 | never | 644.77 | 4.64 [3.42, 5.92] | 6.45 | 0.0013 | tie |
| asym_B400_pi0.25_d0_useful | cusum|reverse|0.95 | 671.24 | calm:100:0.1 | 679.89 | 8.65 [7.70, 9.58] | 7.11 | 0.0013 | monitor |
| asym_B400_pi0.25_d50_useful | cusum|reverse|0.8 | 680.85 | calm:100:0.1 | 688.31 | 7.46 [6.36, 8.57] | 7.18 | 0.0013 | monitor |
| asym_B1000_pi0.1_d0_useful | cusum|reverse|0.2 | 629.22 | calm:400:0.1 | 635.72 | 6.50 [5.22, 7.79] | 6.49 | 0.0013 | monitor |
| asym_B1000_pi0.1_d50_useful | cusum|reverse|0.05 | 629.91 | calm:400:0.1 | 633.89 | 3.97 [2.95, 5.02] | 6.44 | 0.0013 | tie |
| asym_B1000_pi0.25_d0_useful | cusum|reverse|0.8 | 651.37 | calm:200:0.1 | 659.13 | 7.76 [6.47, 9.04] | 7.11 | 0.0013 | monitor |
| asym_B1000_pi0.25_d50_useful | cusum|reverse|0.5 | 657.35 | calm:200:0.1 | 663.91 | 6.56 [5.41, 7.70] | 7.13 | 0.0013 | tie |
| asym_B400_pi0.1_d0_useless | page_hinkley|hold:25|0.01 | 642.73 | never | 642.68 | -0.05 [-0.07, -0.03] | 6.43 | 0.0013 | tie |

### Reference costs, headroom capture, switches, selection optimism

| cell | never | always | static* | dynamic | headroom | captured monitor | captured simple | N_s mon | N_s simple | optimism mon | optimism simple |
|---|---|---|---|---|---|---|---|---|---|---|---|
| asym_B100_pi0.1_d0_useful | 644.45 | 737.18 | 643.50 | 610.34 | 34.11 | -0.00 | -0.00 | 0.03 | 0.00 | 1.91 | 1.83 |
| asym_B100_pi0.1_d50_useful | 646.19 | 736.60 | 645.07 | 610.39 | 35.80 | -0.00 | 0.00 | 0.05 | 0.00 | -1.43 | -1.35 |
| asym_B100_pi0.25_d0_useful | 713.00 | 714.33 | 689.94 | 624.12 | 88.88 | 0.12 | 0.01 | 5.93 | 0.67 | 0.90 | -1.86 |
| asym_B100_pi0.25_d50_useful | 713.01 | 714.33 | 691.21 | 624.28 | 88.73 | -0.01 | -0.00 | 1.74 | 0.01 | -3.32 | -1.36 |
| asym_B400_pi0.1_d0_useful | 644.12 | 737.29 | 633.60 | 602.92 | 41.20 | 0.17 | -0.01 | 1.27 | 0.02 | 1.96 | -1.35 |
| asym_B400_pi0.1_d50_useful | 644.77 | 737.08 | 634.07 | 602.96 | 41.81 | 0.11 | 0.00 | 1.20 | 0.00 | 2.88 | 3.13 |
| asym_B400_pi0.25_d0_useful | 711.19 | 714.94 | 668.84 | 607.36 | 103.84 | 0.38 | 0.30 | 4.96 | 5.82 | 1.08 | 2.40 |
| asym_B400_pi0.25_d50_useful | 717.68 | 712.77 | 670.05 | 607.65 | 110.03 | 0.33 | 0.27 | 3.41 | 5.88 | -0.17 | -2.14 |
| asym_B1000_pi0.1_d0_useful | 648.68 | 735.77 | 623.53 | 601.40 | 47.28 | 0.41 | 0.27 | 0.67 | 0.40 | -0.10 | -1.76 |
| asym_B1000_pi0.1_d50_useful | 643.78 | 737.41 | 620.97 | 601.35 | 42.42 | 0.33 | 0.23 | 0.35 | 0.41 | -1.44 | -1.25 |
| asym_B1000_pi0.25_d0_useful | 710.52 | 715.16 | 647.00 | 603.40 | 107.11 | 0.55 | 0.48 | 2.82 | 1.77 | -0.57 | 0.18 |
| asym_B1000_pi0.25_d50_useful | 712.87 | 714.38 | 648.78 | 603.43 | 109.44 | 0.51 | 0.45 | 1.78 | 1.80 | -2.20 | -3.40 |
| asym_B400_pi0.1_d0_useless | 642.68 | 780.46 | 642.68 | 642.68 | -0.00 | NA | NA | 0.02 | 0.00 | -0.91 | -0.91 |

(*static = per-episode hindsight best of never/always, oracle.) Optimism = tuning-seed cost - eval-seed cost of the selected config.


### Selected configs, grid boundary, P5 ceiling (B = mean bad run, pi_b, theta_max = pi_b + (1-pi_b) lam^(d+1) per alarm), config counts

| cell | best monitor system | boundary | best simple | B/pi_b/theta_max | configs monitor vs simple |
|---|---|---|---|---|---|
| asym_B100_pi0.1_d0_useful | page_hinkley|hold:200|0.01 | alpha=min | calm:1600:0.1 | 100/0.1/0.990 | 300 (60/monitor) vs 54 |
| asym_B100_pi0.1_d50_useful | page_hinkley|hold:50|0.01 | alpha=min | never | 100/0.1/0.609 | 300 (60/monitor) vs 54 |
| asym_B100_pi0.25_d0_useful | cusum|reverse|0.95 | alpha=max | statm:200:0.05 | 100/0.25/0.990 | 300 (60/monitor) vs 54 |
| asym_B100_pi0.25_d50_useful | sr_betting|hold:800|0.2 | interior | calm:1600:0.1 | 100/0.25/0.628 | 300 (60/monitor) vs 54 |
| asym_B400_pi0.1_d0_useful | cusum|hold:400|0.2 | interior | calm:1600:0.1 | 400/0.1/0.998 | 300 (60/monitor) vs 54 |
| asym_B400_pi0.1_d50_useful | cusum|hold:400|0.2 | interior | never | 400/0.1/0.881 | 300 (60/monitor) vs 54 |
| asym_B400_pi0.25_d0_useful | cusum|reverse|0.95 | alpha=max | calm:100:0.1 | 400/0.25/0.997 | 300 (60/monitor) vs 54 |
| asym_B400_pi0.25_d50_useful | cusum|reverse|0.8 | interior | calm:100:0.1 | 400/0.25/0.883 | 300 (60/monitor) vs 54 |
| asym_B1000_pi0.1_d0_useful | cusum|reverse|0.2 | interior | calm:400:0.1 | 1000/0.1/0.999 | 300 (60/monitor) vs 54 |
| asym_B1000_pi0.1_d50_useful | cusum|reverse|0.05 | interior | calm:400:0.1 | 1000/0.1/0.950 | 300 (60/monitor) vs 54 |
| asym_B1000_pi0.25_d0_useful | cusum|reverse|0.8 | interior | calm:200:0.1 | 1000/0.25/0.999 | 300 (60/monitor) vs 54 |
| asym_B1000_pi0.25_d50_useful | cusum|reverse|0.5 | interior | calm:200:0.1 | 1000/0.25/0.951 | 300 (60/monitor) vs 54 |
| asym_B400_pi0.1_d0_useless | page_hinkley|hold:25|0.01 | alpha=min | never | 400/0.1/0.998 | 300 (60/monitor) vs 54 |
### H1 under tuning: detection ranking vs tuned cost ranking

| cell | tau(power_T, value) | tau(-delay, value) | protocol reversals (power, of 20 pairs) |
|---|---|---|---|
| asym_B100_pi0.1_d0_useful | 0.00 | nan | 0 |
| asym_B100_pi0.1_d50_useful | -1.00 | nan | 0 |
| asym_B100_pi0.25_d0_useful | 0.60 | 1.00 | 0 |
| asym_B100_pi0.25_d50_useful | 0.20 | 0.20 | 0 |
| asym_B400_pi0.1_d0_useful | 1.00 | nan | 0 |
| asym_B400_pi0.1_d50_useful | 0.60 | nan | 0 |
| asym_B400_pi0.25_d0_useful | 0.40 | nan | 2 |
| asym_B400_pi0.25_d50_useful | 0.60 | nan | 0 |
| asym_B1000_pi0.1_d0_useful | 0.40 | nan | 0 |
| asym_B1000_pi0.1_d50_useful | 0.20 | nan | 0 |
| asym_B1000_pi0.25_d0_useful | 0.60 | nan | 0 |
| asym_B1000_pi0.25_d50_useful | 0.40 | nan | 0 |
| asym_B400_pi0.1_d0_useless | -1.00 | nan | 0 |

Non-control cells (12): monitor wins 6, simple wins 0, ties 6.

## 8.7 Original cells re-run with the extended grids (same seeds as section 4; evaluation seeds not fresh, see caveat in 8.3)

### Per-cell system-level comparison (eval seeds; diff = cost(best simple) - cost(best monitor system), positive = monitor better)

| cell | best monitor system (tuned) | cost | best simple (tuned) | cost | diff [95% CI] | MME | Holm p | winner |
|---|---|---|---|---|---|---|---|---|
| th3_rho0.995_d0_useful | kelly_h2c_inspired|permanent|0.8 | 683.22 | always | 677.01 | -6.21 [-7.00, -5.46] | 8.25 | 0.0011 | tie |
| th3_rho0.995_d50_useful | kelly_h2c_inspired|permanent|0.8 | 686.49 | always | 676.98 | -9.51 [-10.27, -8.75] | 8.25 | 0.0011 | simple |
| th3_rho0.999_d0_useful | cusum|reverse|0.95 | 668.39 | calm:100:0.1 | 677.29 | 8.90 [7.87, 9.93] | 8.22 | 0.0011 | monitor |
| th3_rho0.999_d50_useful | cusum|reverse|0.95 | 678.26 | always | 676.10 | -2.16 [-4.51, 0.12] | 8.28 | 0.1959 | tie |
| th3_rho0.999_d0_useless | page_hinkley|hold:25|0.01 | 823.80 | never | 823.70 | -0.10 [-0.13, -0.08] | 8.24 | 0.0011 | tie |
| th4_L400_d0 | cusum|hold:200|0.05 | 660.40 | never | 660.00 | -0.40 [-0.82, 0.02] | 6.60 | 0.1959 | tie |
| th4_L400_d50 | batch|hold:200|0.01 | 660.79 | never | 660.00 | -0.79 [-1.01, -0.57] | 6.60 | 0.0011 | tie |
| th4_L1600_d0 | sr_betting|permanent|0.8 | 721.41 | statm:200:0.0 | 722.80 | 1.39 [0.91, 1.87] | 8.40 | 0.0011 | tie |
| th4_L1600_d50 | sr_betting|permanent|0.95 | 722.75 | statm:200:0.0 | 724.25 | 1.51 [1.06, 1.96] | 8.40 | 0.0011 | tie |
| th2_strong | sr_betting|permanent|0.95 | 725.85 | statm:100:0.0 | 726.19 | 0.34 [-0.19, 0.86] | 9.00 | 0.2029 | tie |
| th2_weak | sr_betting|permanent|0.95 | 857.89 | statm:100:0.02 | 859.16 | 1.27 [0.86, 1.68] | 9.00 | 0.0011 | tie |

### Reference costs, headroom capture, switches, selection optimism

| cell | never | always | static* | dynamic | headroom | captured monitor | captured simple | N_s mon | N_s simple | optimism mon | optimism simple |
|---|---|---|---|---|---|---|---|---|---|---|---|
| th3_rho0.995_d0_useful | 824.97 | 677.01 | 676.50 | 624.60 | 200.37 | 0.71 | 0.74 | 0.99 | 1.00 | 1.00 | 1.13 |
| th3_rho0.995_d50_useful | 825.06 | 676.98 | 676.41 | 624.44 | 200.62 | 0.69 | 0.74 | 0.99 | 1.00 | -0.58 | -0.76 |
| th3_rho0.999_d0_useful | 822.48 | 677.84 | 662.23 | 606.57 | 215.91 | 0.71 | 0.67 | 4.31 | 5.03 | -1.86 | -0.22 |
| th3_rho0.999_d50_useful | 827.69 | 676.10 | 662.06 | 606.75 | 220.95 | 0.68 | 0.69 | 4.34 | 1.00 | 0.92 | 1.29 |
| th3_rho0.999_d0_useless | 823.70 | 901.13 | 823.70 | 823.70 | -0.00 | NA | NA | 0.05 | 0.00 | 1.64 | 1.64 |
| th4_L400_d0 | 660.00 | 755.00 | 660.00 | 630.00 | 30.00 | -0.01 | 0.00 | 1.66 | 0.00 | -0.90 | 0.00 |
| th4_L400_d50 | 660.00 | 755.00 | 660.00 | 630.00 | 30.00 | -0.03 | 0.00 | 0.30 | 0.00 | -0.11 | 0.00 |
| th4_L1600_d0 | 840.00 | 755.00 | 755.00 | 690.00 | 150.00 | 0.79 | 0.78 | 1.00 | 1.00 | -0.49 | -0.19 |
| th4_L1600_d50 | 840.00 | 755.00 | 755.00 | 690.00 | 150.00 | 0.78 | 0.77 | 1.00 | 1.00 | -0.50 | 0.14 |
| th2_strong | 900.05 | 755.00 | 755.00 | 705.02 | 195.03 | 0.89 | 0.89 | 1.00 | 1.00 | 0.91 | 0.68 |
| th2_weak | 899.83 | 894.92 | 892.98 | 844.86 | 54.97 | 0.76 | 0.74 | 1.00 | 1.00 | -0.31 | -0.25 |

(*static = per-episode hindsight best of never/always, oracle.) Optimism = tuning-seed cost - eval-seed cost of the selected config.


### Selected configs, grid boundary, P5 ceiling (B = mean bad run, pi_b, theta_max = pi_b + (1-pi_b) lam^(d+1) per alarm), config counts

| cell | best monitor system | boundary | best simple | B/pi_b/theta_max | configs monitor vs simple |
|---|---|---|---|---|---|
| th3_rho0.995_d0_useful | kelly_h2c_inspired|permanent|0.8 | interior | always |  | 300 (60/monitor) vs 54 |
| th3_rho0.995_d50_useful | kelly_h2c_inspired|permanent|0.8 | interior | always |  | 300 (60/monitor) vs 54 |
| th3_rho0.999_d0_useful | cusum|reverse|0.95 | alpha=max | calm:100:0.1 |  | 300 (60/monitor) vs 54 |
| th3_rho0.999_d50_useful | cusum|reverse|0.95 | alpha=max | always |  | 300 (60/monitor) vs 54 |
| th3_rho0.999_d0_useless | page_hinkley|hold:25|0.01 | alpha=min | never |  | 300 (60/monitor) vs 54 |
| th4_L400_d0 | cusum|hold:200|0.05 | interior | never |  | 300 (60/monitor) vs 54 |
| th4_L400_d50 | batch|hold:200|0.01 | alpha=min | never |  | 300 (60/monitor) vs 54 |
| th4_L1600_d0 | sr_betting|permanent|0.8 | interior | statm:200:0.0 |  | 300 (60/monitor) vs 54 |
| th4_L1600_d50 | sr_betting|permanent|0.95 | alpha=max | statm:200:0.0 |  | 300 (60/monitor) vs 54 |
| th2_strong | sr_betting|permanent|0.95 | alpha=max | statm:100:0.0 |  | 300 (60/monitor) vs 54 |
| th2_weak | sr_betting|permanent|0.95 | alpha=max | statm:100:0.02 |  | 300 (60/monitor) vs 54 |
### H1 under tuning: detection ranking vs tuned cost ranking

| cell | tau(power_T, value) | tau(-delay, value) | protocol reversals (power, of 20 pairs) |
|---|---|---|---|
| th3_rho0.995_d0_useful | 0.12 | 1.00 | 0 |
| th3_rho0.995_d50_useful | 0.12 | 1.00 | 0 |
| th3_rho0.999_d0_useful | 0.60 | nan | 0 |
| th3_rho0.999_d50_useful | 0.20 | nan | 0 |
| th3_rho0.999_d0_useless | -1.00 | nan | 0 |
| th4_L400_d0 | 0.00 | 0.00 | 0 |
| th4_L400_d50 | -1.00 | -1.00 | 0 |
| th4_L1600_d0 | 0.63 | 0.60 | 0 |
| th4_L1600_d50 | 0.63 | 1.00 | 0 |
| th2_strong | 0.63 | 0.60 | 0 |
| th2_weak | 0.40 | 0.40 | 0 |

Non-control cells (10): monitor wins 1, simple wins 1, ties 8.

### Original grid vs extended grid, per cell

| cell | orig best monitor system | orig diff | ext best monitor system | ext diff [CI] | MME | ext boundary | winner orig -> ext | best simple orig -> ext |
|---|---|---|---|---|---|---|---|---|
| th3_rho0.995_d0_useful | kelly_h2c_inspired|permanent|0.5 | -13.71 | kelly_h2c_inspired|permanent|0.8 | -6.21 [-7.00, -5.46] | 8.25 | interior | simple -> tie | always -> always |
| th3_rho0.995_d50_useful | kelly_h2c_inspired|permanent|0.5 | -18.21 | kelly_h2c_inspired|permanent|0.8 | -9.51 [-10.27, -8.75] | 8.25 | interior | simple -> simple | always -> always |
| th3_rho0.999_d0_useful | kelly_h2c_inspired|reverse|0.5 | 5.11 | cusum|reverse|0.95 | 8.90 [7.87, 9.93] | 8.22 | alpha=max | tie -> monitor | always -> calm:100:0.1 |
| th3_rho0.999_d50_useful | kelly_h2c_inspired|reverse|0.5 | -4.28 | cusum|reverse|0.95 | -2.16 [-4.51, 0.12] | 8.28 | alpha=max | tie -> tie | always -> always |
| th3_rho0.999_d0_useless | page_hinkley|hold:25|0.01 | -0.10 | page_hinkley|hold:25|0.01 | -0.10 [-0.13, -0.08] | 8.24 | alpha=min | tie -> tie | never -> never |
| th4_L400_d0 | cusum|hold:200|0.05 | -0.40 | cusum|hold:200|0.05 | -0.40 [-0.82, 0.02] | 6.60 | interior | tie -> tie | never -> never |
| th4_L400_d50 | batch|hold:200|0.01 | -0.79 | batch|hold:200|0.01 | -0.79 [-1.01, -0.57] | 6.60 | alpha=min | tie -> tie | never -> never |
| th4_L1600_d0 | cusum|permanent|0.5 | -0.39 | sr_betting|permanent|0.8 | 1.39 [0.91, 1.87] | 8.40 | interior | tie -> tie | statm:200:0.0 -> statm:200:0.0 |
| th4_L1600_d50 | cusum|permanent|0.5 | -2.90 | sr_betting|permanent|0.95 | 1.51 [1.06, 1.96] | 8.40 | alpha=max | tie -> tie | statm:200:0.0 -> statm:200:0.0 |
| th2_strong | cusum|permanent|0.5 | -12.76 | sr_betting|permanent|0.95 | 0.34 [-0.19, 0.86] | 9.00 | alpha=max | simple -> tie | statm:100:0.0 -> statm:100:0.0 |
| th2_weak | cusum|permanent|0.5 | -5.17 | sr_betting|permanent|0.95 | 1.27 [0.86, 1.68] | 9.00 | alpha=max | tie -> tie | statm:100:0.02 -> statm:100:0.02 |

## 8.8 Interpretation and verdicts

1. **H6 depends on the symmetric chain.** With a rare, persistent bad state the tuned monitor system beats the best tuned simple policy by >= MME, with
   Holm-significant CI above 0, in **6 of the 12 useful asymmetric cells** (B100/pi.25/d0; B400/pi.1/d0; B400/pi.25/d0 and d50; B1000/pi.1/d0;
   B1000/pi.25/d0); simple wins 0, ties 6. Pre-declared rule (>= 3 of 12) => *H6 is symmetric-chain-dependent*. The wins are modest: diffs 6.5-9.4 vs MME
   6.4-7.2 (1.0-1.3 x MME, i.e. about 1-1.3% of never cost); 5 of the 6 wins have d = 0. Of the 6 ties, 3 are B100 cells with diff about 0 (nothing beats
   never) and 3 have diffs of 4.0-6.6 with CI above 0 but below MME (B400/pi.1/d50, B1000/pi.1/d50, B1000/pi.25/d50). The point estimate favours the monitor system in
   10 of 12 cells.
2. **Where monitoring helps.** pi_b = 0.1, B = 100: headroom 34-36, neither system captures any (never wins). pi_b = 0.1, B >= 400: headroom 41-47, monitor
   systems capture 0.11-0.41 vs 0.00-0.27 for the best simple. pi_b = 0.25, B >= 400: headroom 104-110, monitor 0.33-0.55 vs simple 0.27-0.48. Both stay far
   from the dynamic oracle (monitor at most 0.55 captured). The per-alarm P5 ceiling theta_max is 0.88-0.999 in all cells except B100 at d = 50 (0.61-0.63), so the
   ceiling does not by itself explain the limited capture; delay and false alarms plausibly do (not tested here).
3. **Always is no longer near-optimal**: always costs about 737 vs never 644 at pi_b = .1 and about equals never at pi_b = .25 (713-718). The simple winners are
   calendar rules with the largest margin 0.1 and often large K (calm:1600:0.1, calm:400:0.1, calm:200:0.1, calm:100:0.1) or `never`: **the simple family also
   sits on its grid boundary (m = 0.1)**, so the simple side is not fully optimised; extending its margin grid is the symmetric follow-up to the alpha extension.
4. **Alpha boundary (asymmetric cells).** Selected alpha is at the grid maximum (0.95) in 2 cells (cusum + Reverse at pi.25/d0, B100 and B400), at the minimum
   (0.01) in 3 cells where the best is "do almost nothing" (B100/pi.1 d0 and d50, and the negative control), interior in the other 8. For rare-persistent
   bad states tuning does not collapse onto alpha -> 1.
5. **Negative control** (B400, pi.1, useless fallback): headroom 0; the best monitor system (page_hinkley + Hold25) costs 0.05 more than never (CI [0.03, 0.07]);
   no false win.
6. **The alpha boundary mattered in the original cells.** Extending alpha to 0.8/0.95 improves the monitor-system diff in 8 of 11 cells (th2_strong -12.8 to +0.3, th2_weak
   -5.2 to +1.3, th4_L1600 -0.4/-2.9 to +1.4/+1.5, th3 rho.995 -13.7/-18.2 to -6.2/-9.5, th3 rho.999 d0 +5.1 to +8.9, d50 -4.3 to -2.2; unchanged in the 3 cells where
   the selected alpha was already 0.01-0.05) and changes the winner classification in 3 cells (th3 rho.995 d0 simple -> tie; th3 rho.999 d0 tie -> monitor; th2_strong
   simple -> tie). The pre-declared criterion (winner change, or improvement >= MME in any cell: th2_strong +13.1, th3 rho.995 d50 +8.7) is met. After extension the
   non-control count is 1 monitor win (th3 rho.999 d0, +8.9 vs MME 8.2, alpha = 0.95), 1 simple win (th3 rho.995 d50, -9.5 vs 8.25), 8 ties; selected alpha is still
   at the grid maximum in 5 non-control cells (th3 rho.999 d0/d50, th4 L1600 d50, th2 strong/weak), so there the optimum remains at "no evidence requirement" and the
   monitors converge to near-always policies (consistent with section 5); the grid is still binding. The best simple policy also changed in th3 rho.999 d0 (always ->
   calm:100:0.1). The original H6 conclusion (<= 1 monitor win of 10 non-control cells) survives the extension (1 of 10).
7. **H1 under extended tuning.** Protocol reversals: 2 of 20 pairs in asym B400/pi.25/d0; 0 in every other asymmetric and extended-grid cell (1 of 24 cells). tau(power_T,
   value) is positive in 10 of 12 useful asymmetric cells (0.2-1.0), 0.00 in one, -1.00 in B100/pi.1/d50 (values within about 0.1 of never: noise). H1 stays
   unsupported under tuning (rule needs a reversal AND tau < 0 in >= 3 cells). tau(-delay) is NaN for most S2 cells (delay undefined for episodes without a regime change).
8. **Verdicts.** H6: not an artifact of untuned controllers in the symmetric chain (original and extended grid: 0 and 1 monitor wins of 10), but not robust to regime
   structure: in rare/persistent bad-state regimes the tuned monitor systems beat the best tuned simple policy in half the cells, by 1.0-1.3 x MME, capturing at most about
   half of the headroom. H1: not supported. Caveats: single seed pair per cell; selected systems use knowledge of the cell's B and pi (oracle tuning, an upper bound for
   monitors); the simple family's margin grid and the monitor alpha grid are both still binding in some cells; only the useful-fallback paired target; monitor wins
   are small in absolute terms and Holm-significant mainly because n = 2000 paired episodes give tight CIs; orig_ext evaluation seeds were not fresh.
9. **Continue / pivot / stop (development).** Continue on the rare-persistent-state regime: widen the simple-policy margin/K grid, add a monitor-score + margin
   hybrid, and use fresh evaluation seeds for the extended-grid original cells, before any confirmatory run.
