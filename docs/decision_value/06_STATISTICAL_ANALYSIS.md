# 06 Statistical analysis: mechanism experiments TH-1..TH-4 and H6

**Label: development, synthetic (Setting C). Seeds < 7,000,000 only. Nothing here is confirmatory.**
Script: `scripts/decision_value/run_mechanism_analysis.py` (subcommands `th1 th2 th3 th4 analyze`).
Engine unchanged (30 tests pass: `pytest tests/decision_value -q`, 7 s). No engine bug found.
Outputs (gitignored): `outputs/decision_value/development/mech_<exp>_<ts>/{cells/,results.json,tables.md}`; registry entries appended to `outputs/decision_value/manifests/run_registry.jsonl`.

## 1. Design actually used

- Episodes: n = 1000 per cell; all monitors and references share the same episodes (CRN); T = 3000, p0 = 0.2, Delta = 0.15, delta = 0.05 (family defaults), c_q = 0.
- **Monitors (declared before any cost result was inspected):** `cusum` (k=.02), `cusum_k005`, `cusum_k06`, `page_hinkley` (delta=.005), `ph_d03` (delta=.03), `batch` (n_b=50), `batch_nb20`, `batch_nb200`, `sr_betting`, `kelly_h2c_inspired`: the five engine defaults plus five variants chosen to span power/delay profiles.
- **Calibration:** per (monitor, target, q, d), threshold = 0.95 "higher" quantile of the null max statistic, n_cal = 6000 null episodes at seed 5,000,000 (engine default is 2000; raised to cut threshold noise), checked on 6000 fresh episodes (seed 5,000,001). Fresh-seed null rates ranged 2.8%-5.2% (e.g. batch_nb20 2.75%, cusum 4.6%): "matched" means <= 5%, not exactly 5%; discrete batch statistics are conservative. Thresholds cached in `_calibration_cache/`.
- **Cost:** expected-loss (Rao-Blackwellised) `cost_exp`; value V = never-switch cost minus cost (positive is good). MME = 1% of never-switch cost per cell.
- **Inference:** percentile bootstrap over episodes, **10,000 resamples** (shared resamples across monitors within a cell), 95% intervals. Exceptions: TH-3 per-(cell, monitor) intervals use 2,000 resamples; Kendall-tau CIs in TH-2 use every 5th of the 10,000 shared resamples (2,000). Reversals use the engine `classify_reversal` (power >= 0.05 or delay >= 10% lower with CI excluding 0; cost disadvantage >= MME with CI excluding 0). Necessary point conditions are screened before bootstrapping (this can only remove pairs the classifier would also reject).
- **H6:** best monitor and best simple reference (never, always, calendar K=100/200/400) are chosen on episodes 0-499; the gap is evaluated on episodes 500-999 (CI on that half). In-sample gap is also reported (optimistic).
- Cells within an experiment share seeds and are correlated; counts across cells are not independent replications.
- Deviations from the brief: (i) TH-1 c_s grid extended to {0,1,2,5,10,20,50,100,200,500,1000} because only 4 pairs cross at <= 100; (ii) TH-2 uses q = 0.2, d = 50 (unspecified in the brief); (iii) TH-3 P5 uses engine indexing, see section 4; (iv) smoke runs at n = 200 also appear in the registry (their directories were deleted).
- Runtimes (4 processes, shared machine): th1 26 s, th2 106 s, th3 141 s, th4 123 s including bootstrap analysis.

## 2. TH-1 (P2 crossing). Run `mech_th1_20261030T230124Z`

Command: `python scripts/decision_value/run_mechanism_analysis.py th1 --n 1000 --procs 4`
S3 strong, fixed tau = 1000, d = 50, q = 0.2, Permanent, paired target. Two independent seed sets (set 1 = 1000, set 2 = 2000). Prediction c_s* = D_0 / g(T-1) from the **set-1** empirical alarm-time CDFs at c_s = 0; empirical crossing from **set-2** simulated costs over the c_s grid.

- Exact identity (same episodes): max |mean simulated V - (sum_t Delta_t F(t) - c_s F(T-1))| = 1.7e-13; per-episode formula 3.5e-12 (all monitors, all 11 c_s values, both sets). Alarm times and actions are bitwise identical between c_s = 0 and c_s = 100 for all 10 monitors in both sets.
- 45 pairs, none with equal power. 39 have c_s* > 0 (A more powerful and better at c_s = 0); 6 have c_s* <= 0 (A worse at every c_s >= 0). 38 cross in (0, 1000], 4 in (0, 100], 1 above 1000.
- **Out-of-sample agreement: for all 39 pairs with c_s* > 0 the CI of (empirical set 2 minus predicted set 1) contains 0** (38/38 in (0,1000]; 4/4 in (0,100]). Within-sample, prediction vs interpolated crossing differ by <= 6e-11 (algebraic identity).

Selected pairs (A = more powerful; the 38-row table is in `tables.md`):

| pair (A vs B) | g(T-1) | D_0 | predicted c_s* set 1 [95% CI] | empirical set 2 [95% CI] |
|---|---|---|---|---|
| batch_nb200 vs batch | 0.181 | 5.46 | 30.1 [9.4, 47.7] | 35.1 [15.3, 51.9] |
| page_hinkley vs batch_nb20 | 0.410 | 34.66 | 84.5 [77.2, 91.6] | 78.1 [70.2, 85.6] |
| batch_nb200 vs batch_nb20 | 0.520 | 44.38 | 85.4 [80.3, 90.2] | 86.5 [81.3, 91.7] |
| batch_nb200 vs page_hinkley | 0.110 | 9.72 | 88.4 [64.1, 112.7] | 111.0 [91.2, 131.4] |
| cusum vs batch | 0.237 | 49.40 | 208.4 [192.7, 227.0] | 205.3 [189.8, 223.3] |
| cusum vs page_hinkley | 0.166 | 53.66 | 323.3 [290.8, 364.3] | 309.2 [279.9, 345.5] |
| cusum vs sr_betting | 0.015 | 12.58 | 838.4 [515.0, 2213.7] | 570.5 [414.7, 878.5] |

Alarm laws F(T-1), set 1: cusum .988, sr_betting .973, batch_nb200 .932, kelly .870, page_hinkley .822, batch .751, batch_nb20 .412.
Caveat: crossings at c_s of 30-800 are large relative to a 0.10 per-step gain over ~2000 steps; the check validates the accounting, not the practical frequency of cost-driven reversals. H6: `always` beats the best monitor (cusum) by 17.5 [14.3, 21.0] on set 2 (set 1: 19.2 [15.8, 22.5]; held-out halves); never-switch cost 900.

**Verdict TH-1 (P2): CONFIRMED_NUMERICALLY** (exact identity to floating point; out-of-sample crossing agreement 39/39).

## 3. TH-2 (P3 incumbent-target reversal, H4). Run `mech_th2_20261030T230151Z`

Command: `... th2 --n 1000 --procs 4`. S3 (tau random in [800,1200]); challengers strong/weak/none/common_shock/reversing; targets incumbent (r0 from the first 300 events' released labels) and paired; Permanent; c_s = 5; q = 0.2; d = 50; seed 3000. Never-switch cost 897, MME 8.97. Per-monitor power/delay/cost/V tables with CIs: `tables.md`.

Kendall tau between detection power (power_T) and V across the 10 monitors (95% CI):

| target | challenger | tau(power, V) | tau(-delay, V) | protocol reversals (power_T), of 90 ordered pairs | best-monitor V |
|---|---|---|---|---|---|
| incumbent | strong | 0.24 [0.20, 0.33] | 0.96 | 3 | 125.3 |
| incumbent | weak | 0.24 [0.16, 0.33] | 0.96 | 0 | 34.3 |
| incumbent | none | **-0.78** [-0.91, -0.69] | -0.51 | 0 | -3.4 |
| incumbent | common_shock | **-0.29** [-0.38, -0.24] | -1.00 | 21 | -31.6 |
| incumbent | reversing | **-0.38** [-0.47, -0.29] | -0.91 | 21 | -31.6 |
| paired | strong | 0.78 [0.73, 0.87] | 1.00 | 1 | 124.9 |
| paired | weak | 0.87 [0.78, 0.96] | 0.87 | 0 | 17.6 |
| paired | none | -0.67 [-0.78, -0.51] | -0.64 | 0 | -0.6 |
| paired | common_shock | -0.47 [-0.64, -0.27] | -0.60 | 0 | -2.6 |
| paired | reversing | -0.91 [-0.91, -0.73] | -0.91 | 25 | -8.0 |

Checks:
- **P3 invariance:** incumbent-target first-alarm times are bitwise identical across all five challenger types for all 10 monitors (paired-target alarm times differ from `strong` in 27%-98% of episodes, as expected).
- **Exact formula:** per-episode V = sum_{t>=S} Delta_t - c_s 1{S<=T-1} holds to 1.4e-11 in all 10 cells.
- **P3(a):** for none and common_shock (fallback never better) max over monitors of V + c_s F(T-1) is 0.00 and -27.9, i.e. <= 0 as required.
- **Ordering reversal:** under none/common_shock/reversing, more powerful incumbent monitors have lower value (tau < 0, CIs exclude 0); under strong/weak the relation is positive. Magnitude caveat: under `none` V differences (-3.4 to -4.8) are below MME, so no protocol-level reversal (0/90); protocol reversals occur for common_shock and reversing (21/90 each, incumbent) and paired reversing (25/90). Under `strong`, tau(power, V) is only 0.24 because power_T counts late alarms; delay ranks value almost perfectly (0.96).
- Not predicted by P3 (paired targets are outside its scope): paired-target monitors also show tau < 0 under none/common_shock; their low power there reflects pre-change false alarms, which cost delta per step.
- H6: incumbent/strong: `always` beats the best monitor by 20.7; incumbent/weak: the best monitor (ph_d03) beats the best reference (calendar400) by 21.0 [19.2, upper bound in results.json], the only monitor win in all 66 cells; other cells ties or reference wins.

**Verdict TH-2 (P3): CONFIRMED_NUMERICALLY** (invariance and identity exact; ranking reversal present; protocol-level reversals only for common_shock/reversing).

## 4. TH-3 (P5 Markov precision and ceiling). Run `mech_th3_20261030T230337Z`

Command: `... th3 --n 1000 --procs 4`. S2, symmetric rho in {0.98, 0.995, 0.999} (lambda = 2 rho - 1, pi_b = 0.5), d in {0, 50, 200}, fallback useful/useless, Hold(H in {50, 200}), c_s = 2, q = 0.2, paired target, seed 4000: 36 cells x 10 monitors = 360 (cell, monitor) tests.

Engine-indexing adaptation of P5: an alarm at decision step S switches the action at S itself (not S+1), so the gain sums h = 0..min(H, T-S)-1 of [P(Z_{S+h}=bad)(Delta_bad+delta) - delta] with P = pi_b + (theta - pi_b) lambda^h, minus c_s (1 + 1{S+H <= T-1}). Trigger times come from the action trace (0->1 transitions); theta_S = P(Z_S = bad | trigger) uses the evaluator-only regime. The ceiling theta_max = pi_b + (1-pi_b) lambda^(d+1) is unchanged (labels of events <= S-1-d are the latest released). The ceiling is tested per trigger with end-of-horizon truncation (the untruncated G_H x trigger count is also stored).

Results over all 360 tests:
- Predicted vs simulated V: correlation 0.99987, slope 1.011, intercept 0.007; mean absolute error 0.095 cost units. The exact per-trigger prediction (realised Z_S) has an error CI covering 0 in 93.1% of tests; the plug-in theta_hat version in 98.9% (nominal ~95%).
- **Ceiling: 0 of 360 tests have V above the per-trigger ceiling (CI lower bound > 0), and 0 of 360 have a theta_hat CI above theta_max.** Largest z-like excess 1.69. The bound is tight for d = 200 (rho = .98: theta_hat .493-.497 vs theta_max .500) and loose for d = 0 (theta_hat ~0.64-0.93 vs theta_max 0.98-0.999).
- Mean theta_hat falls with d and rises with rho (rho = .999, useful, H200: d0 .93, d50 .89, d200 .79).

Best-monitor V (vs never) with the references (full 36-row table in `tables.md`; all values cost units):

| cell | theta_max | G_H(theta_max) per alarm | best monitor V | dynamic oracle V | regime clairvoyant V | always V |
|---|---|---|---|---|---|---|
| rho .98, d0, useful, H200 | 0.980 | 8.4 | 12.9 (cusum) | 168.0 | 103.6 | 147.6 |
| rho .98, d200, useful, H200 | 0.500 | 6.0 | 10.1 | 168.0 | 103.6 | 147.6 |
| rho .98, d50, useful, H50 | 0.562 | -1.2 | -0.1 | 168.0 | 103.6 | 147.6 |
| rho .995, d0, useful, H200 | 0.995 | 14.6 | 25.7 (kelly) | 201.9 | 195.2 | 150.0 |
| rho .999, d0, useful, H200 | 0.999 | 22.5 | 49.9 (kelly) | 222.9 | 222.6 | 154.0 |
| rho .999, d200, useful, H200 | 0.834 | 17.0 | 36.1 (kelly) | 222.9 | 222.6 | 154.0 |
| rho .999, d50, useful, H50 | 0.951 | 2.8 | 7.7 | 222.9 | 222.6 | 154.0 |
| any rho/d, useless, H200 | 0.50-0.999 | -4.9 to -9.0 | -0.5 to -0.6 | 0.0 | 0.0 | -75.5 to -77.1 |
| any rho/d, useless, H50 | 0.50-0.999 | -4.1 to -5.2 | -0.3 to -0.4 | 0.0 | 0.0 | -75.5 to -77.1 |

Where the ceiling gain per alarm is <= 0 (useless fallback; useful with H = 50 at rho = .98) best-monitor V is <= 0; where it is positive monitors earn positive V that rises with rho and falls with d, as P5 predicts. The regime clairvoyant (switch iff bad) is not the optimum when regimes are short (rho = .98: clairvoyant 103.6 < always 147.6 < dynamic 168.0); this is the oracle's definition, not a bug.
H6: **`always` beats every monitor in all 18 useful cells (gap 100-148)**; in the 18 useless cells monitors never win (best reference is never; ties). In this S2 parametrisation always-deploying the challenger is worth it (stationary benefit 0.5 x 0.15 - 0.5 x 0.05 = 0.05 per step against c_s = 2), so monitor value is informative only relative to `never`.

**Verdict TH-3 (P5 gain and delay-persistence ceiling): CONFIRMED_NUMERICALLY** (no monitor exceeds the ceiling; per-trigger truncation at T was included from the start, so no revision of the formula was needed).

## 5. TH-4 (P6 conversion number, H1 transient, H3). Run `mech_th4_20261030T230558Z`

Command: `... th4 --n 1000 --procs 4`. S1, L in {100,400,1600} x d in {0,50,200} x q in {.1,.5} = 18 cells, Delta = .15, delta = .05, c_s = 5, Hold(H = L/2), paired, seed 6000. I = KL(in-window || pre) of x = l0 - l1 (trinomial) = 0.0427 nats per event; kappa = (L-d) q I / log(20). H_T = best-static minus dynamic expected cost. Full per-cell, per-monitor V with CIs: `tables.md` / `results.json`.

| L | d | q | kappa | H_T | best V [monitor] | median captured | mean power_T / power_opp | reversals power_T / power_opp (of 90) | H6 gap ref - monitor [CI] |
|---|---|---|---|---|---|---|---|---|---|
| 100 | all | .1/.5 | 0.00-0.71 | 0.0 | -0.3 to -0.6 | NA (H_T=0) | .06-.10 / .00-.04 | 0 / 0 | -0.3 to -0.7 (tie) |
| 400 | 0 | .1 | 0.57 | 30.0 | -0.9 | -0.06 | .16 / .08 | 0 / 0 | -1.3 [-1.7,-0.9] tie |
| 400 | 0 | .5 | 2.85 | 30.0 | +0.5 (cusum_k06) | -0.03 | .53 / .45 | 2 / 1 | +0.8 [0.0, 1.5] tie |
| 400 | 50 | .1 / .5 | 0.50 / 2.49 | 30.0 | -1.2 / -0.4 | -0.07 / -0.12 | .16 / .53 (power_T) | 0/0 ; 2/1 | tie |
| 400 | 200 | .1 | 0.28 | 30.0 | -1.5 | -0.11 | .17 / .03 | 0 / 0 | tie |
| 400 | 200 | .5 | 1.42 | 30.0 | -2.0 | -0.34 | .54 / .17 | **12 / 9** | -1.9 [-2.4,-1.4] tie |
| 1600 | 0 | .1 / .5 | 2.28 / 11.39 | 65.0 | +37.2 / +70.5 | -0.98 / -0.32 | .62 / .92 | 0/0 | -49.6 / -30.4 (reference) |
| 1600 | 50 | .1 / .5 | 2.21 / 11.04 | 65.0 | +35.2 / +66.9 | -1.01 / -0.36 | .62 / .92 | 0/0 | -51.8 / -27.9 (reference) |
| 1600 | 200 | .1 / .5 | 1.99 / 9.97 | 65.0 | +28.8 / +60.6 | -1.06 / -0.45 | .63 / .92 | 0/2 ; 0/0 | -57.7 / -24.2 (reference) |

(At L = 100 the dynamic gain, 100 x 0.10 = 10, equals 2 c_s, so H_T = 0 by construction.)

**Matched reversal counts (protocol definition, MME = 1% of never cost):** power_T: 16 of 1620 ordered monitor pairs, in 3 of 18 cells; power_opp: 13 of 1620, in 4 of 18 cells; delay-based: 16. Concentrated in L = 400, q = .5 (d = 200: 12/9; d = 0 and 50: 2/1 each) plus 2 power_opp reversals at L = 1600, d = 200, q = .1. Cells are correlated (shared seeds, same monitors); these are not 3-4 independent replications.

**Does kappa explain monitoring value better than power_T?** (180 (cell, monitor) points; 34% have V > 0.)
- Spearman(V, kappa) = 0.47; Spearman(V, power_T) = 0.39; Spearman(V, power_opp) = 0.53.
- Between cells (18): Spearman(mean V, kappa) = 0.40; (best V, kappa) = 0.74; (best V, mean power_T) = 0.65; (best V, H_T) = 0.62.
- Within cells, mean Spearman(V, power_T) over 18 cells = -0.19 (power_opp +0.10); kappa is constant within a cell and cannot rank monitors.
- Threshold rule "V > 0 iff x > k" (best in-sample threshold; majority baseline 0.66): kappa > 1.99: accuracy 0.90, AUC 0.93; power_T: 0.87, AUC 0.94; power_opp: 0.93, AUC 0.97.

So kappa is a usable cell-level coarse predictor (best V vs kappa 0.74) but does **not** beat power_opp, its threshold (~2) only separates L = 1600 from the rest, it misclassifies L = 400, q = .5 (kappa 1.4-2.9, V <= 0.5), and it cannot rank monitors. "Captured fraction" is negative for every monitor in the L = 1600 cells because the best static policy (always) beats Hold(800) controllers; this is a controller/headroom-definition effect, not evidence about kappa. Thresholds were fitted in-sample.

**Verdict TH-4 (P6 kappa as predictor): INCONCLUSIVE / not supported as a sharp predictor.** P6 is an asymptotic corollary and is not contradicted; kappa tracks which cells convert but is confounded with L, H_T and the controller, and is no better than power_opp.

## 6. H6 across all cells (66 cells)

Best monitor + fixed controller vs best of {never, always, calendar 100/200/400} (held-out half, MME rule):

| experiment | cells | monitor wins | tie | reference wins |
|---|---|---|---|---|
| TH-1 | 2 | 0 | 0 | 2 (always; gap 17.5-19.2) |
| TH-2 | 10 | 1 (incumbent/weak, +21.0 vs calendar400) | 5 | 4 |
| TH-3 | 36 | 0 | 18 | 18 (always; gap 100-148) |
| TH-4 | 18 | 0 | 12 | 6 (gap 24-58) |

Per-cell gaps and CIs: section "H6" of `tables.md` in each run dir. Caveat: monitors run with a fixed untuned controller (Permanent or Hold), so this tests monitors with naive controllers, not tuned systems (experiment type II is untested).

## 7. Verdicts

| item | verdict (development, synthetic Setting C) |
|---|---|
| TH-1 / P2 | CONFIRMED_NUMERICALLY |
| TH-2 / P3 | CONFIRMED_NUMERICALLY (reversal magnitude exceeds MME only for common_shock/reversing) |
| TH-3 / P5 | CONFIRMED_NUMERICALLY (ceiling never exceeded, 0/360) |
| TH-4 / P6 | INCONCLUSIVE as a predictor (kappa no better than power_opp) |
| H1 ranking reversal | Supported, weakly: 16/1620 pairs in TH-4 (3 of 18 cells); 21-25/90 in TH-2 target-mismatch cells; rare in matched transient cells |
| H2 actionability / persistence | Supported: V rises with rho, falls with d, vanishes when the fallback is useless |
| H3 small headroom, negligible value | Supported: H_T = 0 cells have V in [-0.6, 0] (below MME) for all 60 monitor-cells; H_T = 30 (L = 400) also gives about 0, so headroom is necessary, not sufficient |
| H4 alarm validity != usefulness | Supported (TH-2 incumbent targets) |
| H6 simple methods competitive | Supported in development (1 of 66 cells a monitor wins), with the untuned-controller caveat |
| H5 | not tested here |

Limitations: one seed set per cell, correlated cells, synthetic Bernoulli losses with fixed delay, Setting A/C labels; calibrated null rates are <= 5%, not equal; monitor variants were declared in advance but are ad hoc; kappa-rule thresholds are in-sample; no confirmation seeds used.
