# C_RANK_INVERSION_ANALYSIS: alarm-metric ranking vs economic ranking (dev, exploratory)

Data: dev pilot `outputs/paper3/atlas/dev1` (+`dev1b` for calibrated detectors / legacy DISCERN), 32 cells x 30 seeds x
{alt, null twin} x 18 methods, seed base 7,300,000, run ids in `ledger/atlas.jsonl`. Protocol: `C_ATLAS_PROTOCOL.md`.
Scripts: `scripts/paper3/atlas/{run_pilot,analyze_inversions,analyze_repairs,run_real,analyze_real}.py`.
All numbers are development/exploratory; thresholds untuned; CIs are seed-cluster bootstrap (300 reps, jointly over cells
and methods). Machine-readable: `outputs/paper3/atlas/{inversion_results,repair_results,real_results}.json`,
`cell_method_table.csv`, `cell_inversions.csv`.

## 1. Headline (12 non-control, non-repair methods, synthetic grid)
| quantity | estimate | 95% CI |
|---|---|---|
| mean per-cell Kendall tau(EDD rank, J rank) | **-0.168** | [-0.199, -0.125] |
| tau(null false-alarm rank, J rank) | +0.193 | [0.125, 0.220] |
| tau(composite alarm rank, J rank) | -0.189 | [-0.216, -0.127] |
| inversion frequency, X better on EDD AND null-FA but worse on J | **0.499** of dominated pairs | [0.468, 0.549] |
| inversion frequency, EDD-only dominance | 0.583 | [0.557, 0.598] |
| mean excess cost J_X - J_Y in an inverted pair | **17.97** J units (about 3.8% of mean J 470) | [16.6, 20.9] |
| same, EDD-only | 33.6 | [33.2, 36.3] |
Reading: a negative tau means *faster* detection goes with *higher* economic cost; about half of the pairs in which one method
dominates another on both alarm metrics are economically reversed. Adding the never_switch control strengthens it (tau_EDD
-0.227, inversion frequency 0.553 [0.521, 0.593], magnitude 22.7). This is a per-grid statement about *this* registered grid
and zero-tuning defaults (see limitations); it is not a population frequency.

## 2. Why: cost decomposition (mean over alt streams; J units; identity asserted per episode)
| method | J | EDD | missed | null FA | fees | interv. | harm_bad | noise | cert. lag | re-miss |
|---|---|---|---|---|---|---|---|---|---|---|
| never_switch | 445.3 | - | - | 0 | 0 | 0 | 0 | 0 | 83.2 | 0 |
| cusum | 469.0 | 393 | 0.26 | 0.424 | 28.9 | 13.2 | 22.4 | -1.3 | 43.2 | 0.5 |
| wald_econ | 470.6 | 535 | 0.53 | 0.145 | 28.9 | 6.8 | 13.7 | -0.1 | 59.0 | 0.2 |
| edetector_cal | 472.3 | 500 | 0.39 | 0.228 | 28.9 | 9.1 | 19.0 | -1.0 | 54.0 | 0.2 |
| gated_mope | 472.6 | 723 | 0.85 | 0.044 | 25.4 | 1.8 | 4.3 | -0.1 | 79.1 | 0.0 |
| markov_skeleton | 474.2 | 781 | 1.00 | 0.000 | 28.9 | 0 | 0 | 0 | 83.2 | 0 |
| discern_fixed | 474.2 | 781 | 1.00 | 0.000 | 28.9 | 0 | 0 | 0 | 83.2 | 0 |
| cusum_cal | 474.9 | 612 | 0.58 | 0.100 | 28.9 | 5.8 | 12.4 | -0.3 | 66.0 | 0 |
| smcs_retain | 475.1 | 685 | 0.79 | 0.091 | 28.9 | 2.2 | 8.7 | 0.1 | 73.2 | 0 |
| thinned_iid | 475.4 | 730 | 0.85 | 0.022 | 28.9 | 3.4 | 2.0 | -0.1 | 78.1 | 1.0 |
| iid_gate | 475.6 | 629 | 0.65 | 0.124 | 28.9 | 9.3 | 4.9 | -0.3 | 67.5 | 3.2 |
| page_hinkley | 482.6 | 128 | 0.04 | 0.995 | 28.9 | 45.0 | 17.5 | -0.5 | 13.0 | 16.8 |
| edetector | 515.9 | 87 | 0.01 | 1.000 | 28.9 | 86.1 | 18.4 | -0.7 | 9.3 | 11.8 |
(Null FA from the null twin. "Cert. lag" = forgone gain before the first deployment inside the first good window.)
Decomposition of the 193 inverted pair-cells (mean of J_X - J_Y = 17.97): switching cost +11.1, post-change avoidable harm
(`harm_bad`) +12.6, fees +0.3 (budgets are equal), noise +0.4, certification lag **-6.6** (the faster method does
shorten lag, but it is outweighed). So the inversions come from intervention cost and avoidable harm after dwell ends, i.e.
speed bought with unvalidated switching, not from fees.
**Dominant caveat:** `never_switch` (445.3) beats every method in this grid; the cheapest method is +24 J worse (about 5%).
Fees average 28.9 J and the detectable gain of a window rarely repays fees + switching at these tariffs/budgets and
zero tuning. The grid therefore mostly measures how much each method *loses* relative to not acquiring, and some inversion
frequency is inherited from that. A grid with a cheaper tariff or a longer/larger gain window would be needed to test whether the
inversions persist where acquiring pays; not run.

## 3. Which mechanism axes drive inversions (n = 32 cells; descriptive, no multiplicity correction; 20 tests)
Spearman of per-cell composite tau with each axis: **dwell** +0.80 (p<0.001; when the improvement persists, alarm speed and
cost agree; short dwell flips it), onset -0.24, k -0.24, rho -0.33 (p=.06, non-monotone). Per-cell inversion rate: dwell -0.34
(p=.06), disagreement rate +0.37 (p=.04, not robust to multiplicity), others |rho|<0.3. By rho, mean composite tau:
rho=0 +0.08, .5 -0.44, .8 +0.17, .95 -0.57 (inversion rates .50/.54/.36/.63): the highest-persistence cells invert most, but rho = .8
does not follow the trend, so I do not claim monotone dependence-driven inversion. Informative vs equal delay: inversion rate
0.45 vs 0.56, tau -0.17 vs -0.21 (no clear effect). Standardised OLS of inversion rate on all axes: R^2 = 0.49 with 32 cells
and 10 regressors, no single coefficient reliable. Honest summary: **dwell (transience of the benefit) is the one axis with strong
evidence; dependence contributes via false-alarm inflation (section 4) more than via ranking inversion.**

## 4. Dependence stress: null false promotion by rho (n=240 null-twin episodes per method per rho)
gated_mope .000/.008/.029/.138; smcs .021/.033/.063/.246; iid_gate .008/.021/.088/.379; thinned_iid .000/.000/.000/.088;
cusum .138/.258/.471/.829; cusum_cal .000/.004/.042/.354; edetector_cal .038/.067/.171/.638; wald_econ .013/.075/.125/.367;
edetector .997-1.0 and page_hinkley .99-1.0 at all rho (registered ARL-type thresholds are not null-calibrated);
c1_gapaware, markov_skeleton, discern_fixed 0/960. C1 with declared rho_max=.80 fails exactly where the bound is violated:
.075 at rho=.95 (Wilson [.048, .115]) vs 0 elsewhere. Note nominal alpha=.05 per episode.

## 5. Real c4 streams (EXPLORATORY, all exposed to Papers 1/2; proxies, no causal onsets)
30 episodes per stream, B=200, c_q=.05, k=5. Only 8 of 27 streams have >=3 ex-post good (sum D >= 20) and >=3 bad
(sum D <= -20) episodes. Same 12 methods: mean tau(EDD proxy, J) = **+0.264** [0.087, 0.417] (agreement, opposite sign to the
synthetic grid), tau_FA +0.199 [0.126, 0.330], composite +0.340 [0.200, 0.495]; inversion frequency 0.237 [0.136, 0.314] (EDD-only 0.365
[0.289, 0.445]); magnitude 1.25 J [1.50, 3.30]-CI (point estimate lies below the bootstrap interval: small-sample
instability, treat as unreliable). So on real streams the inversion is **not** reproduced; with proxies built from ex-post
episode gain and 8 streams this says little beyond "no support for transfer of the synthetic inversion magnitude". Mean J over
the 8 streams: never_switch 465.6; best method wald_econ 448.3, cusum 448.9, edetector_cal 450.5 (acquisition pays on these streams).

## 6. Candidate repairs C1 and C3 (equal budget, paired streams, equal-weight cells)
Null FP: C1 (c1_gapaware, rho_max=.95) 0/960 across all rho, including rho=.95 where gated/iid gates reach .14-.38 and the
thinned gate .088. But **power is near zero**: promotes in 0.1% of alt episodes (markov_skeleton 0%, discern 0.2%); EDD = censored
(781). Its J (474.4) equals never_switch + fees (445.3 + 28.9). The conservative bound `(1+rho_max^g)/2` at typical gaps g ~ T/B
(7-40 events) is too close to 1 for 0.8-capped bets to accumulate evidence in <=270 labels; ex-ante safety is bought with the
entire benefit. Paired J (seed-cluster 95% CI):
* c1_gapaware vs markov_skeleton +0.17 [-0.00, +0.51] (no gain); vs thinned_iid -0.99 [-2.06, +0.13] (rho<=.5: -1.97
  [-3.16, -0.72], where thinned is valid; rho>=.8: -0.01 [-1.84, +1.70]); vs gated_mope +1.75 [+0.73, +2.75] (worse); vs wald_econ
  +3.7 [+1.2, +6.3]; vs cusum_cal -0.5 [-2.5, +1.5]; vs never_switch +29.0 [28.8, 29.4].
* c1c3 / c3_spaced_iid use only ~217 of ~271 labels (spacing leaves budget unspent), so their raw J gains (c1c3 -6.0 vs
  markov_skeleton; c3_spaced_iid -7.5 vs thinned) are mostly **saved fees**, not better decisions. Excluding fees (J - fees):
  c1c3 - markov_skeleton +0.03 [0.00, 0.08]; c3_spaced_iid - markov_skeleton -0.42 [-1.52, +0.73]; c3_spaced_iid - iid_gate
  -1.85 [-3.13, -0.63]; c3_spaced_iid - thinned_iid -1.58 [-2.86, -0.31]. So spacing gives a small (<0.5% of J) non-fee improvement over
  the dependence-unaware/thinned gates, nothing over the Markov skeleton, and **it is not an equal-label comparison**. C3 with the iid gate
  (c3_spaced_iid) also loses safety: null FP .017/.008/.042/.296 (rho=0..0.95).
* Against the strongest *valid* baselines, C1 has no demonstrated advantage: markov_skeleton (same bound, nominal gap) is
  indistinguishable and equally powerless; thinned_iid is valid only at rho=0 and is statistically indistinguishable from c1_gapaware at rho>=.8. **Negative
  result: C1 and C3 do not improve cost; C1 is a validity-preserving but inert gate in this regime.** Possible directions
  (not run): larger label budgets, a known/estimated-with-slack rho_max below .95, alternating-state bets that use
  `P(x=1|prev)` contrast instead of a one-sided bound, or hedging the bet with the lower bound on persistence.

## 7. Limitations
Dev-only, zero-tuning defaults (CUSUM h, PH delta/lam, SPRT p1=.65 are not tuned per cell, which affects every ranking);
never_switch dominates the grid; the e-detector/PH registered defaults are not null-calibrated (calibrated variants added);
20 axis-level tests are uncorrected; n=32 cells; 30 seeds; informative-delay form is one specific rule; the C1 validity
argument is a sketch, and rollback is not covered by any guarantee; real-data proxies are ex post; v2's other comparators
(Qiu, Gong-Zhang, Model Picker, CAMS, RMM wrapper) were not rerun here.
