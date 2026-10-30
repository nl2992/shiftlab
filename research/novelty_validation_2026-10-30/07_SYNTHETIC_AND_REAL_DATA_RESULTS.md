# 07. Synthetic and real-data results

All results below were produced in this programme by the scripts in `scripts/` (outputs in `outputs/`). Classification:
§1 X1 **DEVELOPMENT_ONLY** (stylised, auditor-designed, not frozen); §2 X2 **exact but toy** (benchmark illustration);
§3 D2 **EXPLORATORY real data** (batches already inspected by earlier work; protocol 06 committed at 89dba6a before the run).
**No result here is CONFIRMED.** The only CONFIRMED item in the whole lineage is the repository's G5 run (01 §3).

## 1. X1 — what Brier-guided bet selection does (C1)  `scripts/x1_guidance_mechanism.py`

Setup. Bounded labelled increments for a cost loss `5·Bern(p_c)` (null `p_c=0.10`, `r0=0.5`) and a Brier-like loss `Bern(p_b)`
(null `p_b=0.20`), onset at t = 500 of T = 1500, 2000 paths per named world (600 per sweep cell), discount γ = 0.995, delay 5,
cap 0.5, threshold ln 20, label-rate q ∈ {1, 0.2, 0.1} with the repository's PP-IPW increment and **uniform support caps**
(`caps()` = repository formulas). Arms: cost-only discounted Kelly (C1) and H2c (`guided_disc` bet logic copied from
`detectors.py`). Power = alarm in [500, 1500); false alarm = before 500.

Exact reduction (guide := cost statistic): max |Δ log-wealth| = 0 (q=1, 0.1) and 8.9e-16 (q=0.2) — H2c *is* discounted Kelly with a
substituted moment ratio.

| world (cost shift, Brier shift, ρ) | q=1: C1 / H2c power | q=0.2: C1 / H2c | q=0.1: C1 / H2c | false alarm, H2c (q=1 / .2 / .1) |
|---|---|---|---|---|
| aligned (p_c .10→.13, p_b .20→.30, ρ .8) | .542 / .443 | .076 / **.153** | .029 / **.071** | .018 / .009 / .004 |
| aligned, independent (ρ 0) | .527 / .471 | .079 / **.164** | .029 / **.065** | .012 / .003 / .001 |
| masked (cost up, Brier flat) | .536 / .157 | .091 / .047 | .040 / .028 | .015 / .010 / .004 |
| opposed (cost up, Brier **down**) | .532 / .002 | .072 / .001 | .034 / .004 | .021 / .009 / .004 |
| misleading null (cost flat, Brier up) | .008 / .024 | .005 / .022 | .006 / .014 | .020 / .007 / .004 |
| null (nothing changes) | .008 / .011 | .006 / .007 | .005 / .006 | .020 / .006 / .005 |

4×4 sweep of (cost harm × Brier shift), 16 cells each: H2c better by > .02 power in 1 / 6 / 6 cells and worse by > .02 in 9 / 6 / 6 cells
(q = 1 / .2 / .1); best gain +.023 / +.142 / +.118, worst loss −.587 / −.585 / −.318; maximum H2c false-alarm rate in any sweep cell ≤ .028 (< α = .05).

**Reading (DEVELOPMENT_ONLY).** (i) Guidance never helps with full labels (caps loose; the relative-position map over-bets). (ii) At the
10–20 % label rates where the caps bind, it helps **only when the Brier statistic shifts in the same direction**, and the gain is
about the same when the Brier shift is statistically independent of the cost events (ρ = 0), so it behaves like a lower-variance
**shift-timing signal that sizes the bet**, not like information that the cost increment is positive. (iii) It is harmful when the
guide is flat or opposed (up to −.59 power). (iv) Validity is untouched in every world (as the supermartingale argument says).
Limits: two-point increments, one discounting rate, my own world design; says nothing about the G5 generator's own co-movement.

## 2. X2 — joint acquisition+switching vs independently optimised policies (C2)  `scripts/x2_joint_vs_separate_dp.py`

Exact belief-MDP, T = 8, hidden two-state Markov chain (challenger better/worse by Δ per period), query cost `c_q`, hard cap B,
switch cost `c_s`, accuracy a, delay D ∈ {0,1} (D=1: signal arrives at the next period), 192 instances (Δ ∈ {.3,.6}, c_s ∈ {.5,1.5}, c_q ∈
{.02,.1}, B ∈ {1,2,3}, ρ ∈ {.8,.95}, a ∈ {.75,.9}, D ∈ {0,1}). Arms with identical information, budget, horizon and costs:
**J** joint optimum; **S_ol** best open-loop query schedule (exhaustive over all subsets ≤ B) + optimal switching; **S_us**
uncertainty-sampling rule (κ optimised over 6 values) + optimal switching; **S_vo** myopic one-step VOI + optimal switching;
no-query and always-incumbent.

* J ≤ every separate arm in **192/192** instances (0 violations; a code-correctness check, since both go through the same recursion).
* J strictly better than the best separate arm (> 1e-6) in **27/192** (14 %), by > 0.01 in 16; maximum absolute gap 0.076, maximum relative to J's net cost **1.1 %**, mean 0.04 %.
* Gap by B: 0 for B = 1; mean .0016 (max .050) for B = 2; mean .0066 (max .076) for B = 3. By D: mean .0039 (D=0) vs .0016 (D=1).
* Best separate arm: S_ol in 188, S_us in 4 instances.
* Any querying beats no-query/incumbent by > 1e-6 in 86/192 instances.

**Reading.** The only source of the gap is closed-loop adaptivity of the query decision to the belief — i.e. the optimum of a finite
belief-MDP, which is the textbook value-of-information DP. It needs B ≥ 2 (with B = 1, an optimal open-loop schedule loses nothing here).
**Gate C branch 2: a strict improvement on a toy instance that standard dynamic programming already implies ⇒ benchmark
illustration, not novel methodology.** Not tested: constrained false-promotion risk, unknown model parameters, retraining/operational
costs, larger horizons, multiple candidates.

## 3. D2 — UCI Gas Sensor Array Drift, counterfactual replay (EXPLORATORY)  `scripts/d2_gas_sensor_replay.py`

Provenance, loss, partitions and arms are fixed in 06 (committed before the run). Numbers: train batch 1 (445 rows, 74 positives),
calibration n_cal = 622 (random half of batch 2), `r̂_0` = 0.01125, Hoeffding `U_0` = **0.3155** (margin 0.304 ≈ 27× the mean cost), Brier `r_0` (guide only) = 0.00455,
total budget δ_S + α_T = 0.01 + 0.04, threshold ln 25, ε = 0.10 (primary). Re-running the script reproduced the first run's JSON
byte-for-byte (the only edit between runs added the per-seed `.npz` output).

**Per-batch descriptive decision risk (frozen model, FN 5 / FP 1).** Batches 3–5 are near the calibration cost; batches 6, 7, 9 carry large increases:

| batch | n | positive rate | mean cost | excess vs calibration mean | Brier |
|---|---|---|---|---|---|
| 1 | 445 | 0.166 | 0.018 | +0.007 | 0.003 |
| 2 | 1244 | 0.004 | 0.016 | +0.005 | 0.008 |
| 3 | 1586 | 0.000 | 0.033 | +0.022 | 0.025 |
| 4 | 161 | 0.000 | 0.106 | +0.094 | 0.077 |
| 5 | 197 | 0.000 | 0.005 | -0.006 | 0.005 |
| 6 | 2300 | 0.203 | 0.997 | +0.985 | 0.196 |
| 7 | 3613 | 0.157 | 0.765 | +0.754 | 0.149 |
| 8 | 294 | 0.061 | 0.289 | +0.278 | 0.057 |
| 9 | 470 | 0.215 | 1.077 | +1.065 | 0.217 |
| 10 | 3600 | 0.167 | 0.227 | +0.215 | 0.076 |

**Stream A (real-data null, held-out half of batch 2, 622 events × 300 re-orderings): every arm × label rate × ε raised 0 alarms.** This is
**uninformative about validity**: the Hoeffding margin (0.30 + ε) is so large that no alarm is possible even for harmful costs. It is not evidence of calibration
quality or of anytime validity.

**Stream B (batches 3–10 in documented order, 12,221 events; batch 6 begins at index 1944, 7 at 4244, 8 at 7857, 9 at 8151, 10 at 8621), ε = 0.10:**

| labels | ε | arm | alarm rate (300 label-mask seeds) | median alarm index | mean labels spent at alarm | mean realised excess cost accumulated before alarm |
|---|---|---|---|---|---|---|
| 0.05 | 0.1 | C0_cost_parent | 0.743 | 6637 | 391 | 4624 |
| 0.05 | 0.1 | C1_cost_disc_Kelly | 1.000 | 3968 | 199 | 1039 |
| 0.05 | 0.1 | C2_cost_ONS | 1.000 | 3916 | 196 | 779 |
| 0.05 | 0.1 | H2c_guided_disc | 0.980 | 4165 | 238 | 2279 |
| 0.05 | 0.1 | PR_style_Hoeffding_CS | 0.000 | – | 611 | 6397 |
| 0.05 | 0.0 | C0_cost_parent | 0.990 | 5737 | 280 | 3187 |
| 0.05 | 0.0 | C1_cost_disc_Kelly | 1.000 | 3956 | 198 | 959 |
| 0.05 | 0.0 | C2_cost_ONS | 1.000 | 3908 | 196 | 748 |
| 0.05 | 0.0 | H2c_guided_disc | 1.000 | 4081 | 210 | 1659 |
| 0.05 | 0.0 | PR_style_Hoeffding_CS | 0.000 | – | 611 | 6397 |
| 0.10 | 0.1 | C0_cost_parent | 0.987 | 5817 | 585 | 3456 |
| 0.10 | 0.1 | C1_cost_disc_Kelly | 1.000 | 3899 | 390 | 662 |
| 0.10 | 0.1 | C2_cost_ONS | 1.000 | 3870 | 387 | 518 |
| 0.10 | 0.1 | H2c_guided_disc | 1.000 | 4121 | 426 | 1837 |
| 0.10 | 0.1 | PR_style_Hoeffding_CS | 0.000 | – | 1222 | 6397 |
| 0.10 | 0.0 | C0_cost_parent | 1.000 | 4203 | 460 | 2315 |
| 0.10 | 0.0 | C1_cost_disc_Kelly | 1.000 | 3890 | 389 | 608 |
| 0.10 | 0.0 | C2_cost_ONS | 1.000 | 3866 | 387 | 497 |
| 0.10 | 0.0 | H2c_guided_disc | 1.000 | 4046 | 407 | 1400 |
| 0.10 | 0.0 | PR_style_Hoeffding_CS | 0.007 | 6902 | 1219 | 6386 |
| 0.20 | 0.1 | C0_cost_parent | 1.000 | 5670 | 1013 | 2741 |
| 0.20 | 0.1 | C1_cost_disc_Kelly | 1.000 | 3861 | 772 | 455 |
| 0.20 | 0.1 | C2_cost_ONS | 1.000 | 3842 | 769 | 378 |
| 0.20 | 0.1 | H2c_guided_disc | 1.000 | 4098 | 821 | 1631 |
| 0.20 | 0.1 | PR_style_Hoeffding_CS | 0.010 | 7004 | 2434 | 6383 |
| 0.20 | 0.0 | C0_cost_parent | 1.000 | 4142 | 830 | 1850 |
| 0.20 | 0.0 | C1_cost_disc_Kelly | 1.000 | 3853 | 771 | 413 |
| 0.20 | 0.0 | C2_cost_ONS | 1.000 | 3840 | 769 | 373 |
| 0.20 | 0.0 | H2c_guided_disc | 1.000 | 4020 | 804 | 1240 |
| 0.20 | 0.0 | PR_style_Hoeffding_CS | 0.517 | 6922 | 1894 | 5540 |

PR-style = supervised Hoeffding-stitched CS (SOURCE_INSPIRED). At ε = 0 (secondary, in the JSON) the ordering is unchanged but the gap is smaller: median alarm index H2c 4081 / 4047 / 4020 vs C1 3956 / 3890 / 3853 and C2 3909 / 3866 / 3841 at 5 / 10 / 20 % labels, all alarm rates ≥ 0.99; pre-alarm excess cost H2c 1659 / 1400 / 1240 vs C2 748 / 497 / 373.

**Pre-declared primary hypothesis (06): H2c is not worse than the better of C1/C2 in alarm index on B at ε = 0.10 — FAILED.** Paired by label-mask seed:

| labels | H2c − comparator (alarm index) | mean diff [95 % bootstrap over label-mask seeds] | share of seeds H2c later |
|---|---|---|---|
| 0.05 | C1 | +772 [+627, +931] | 0.99 |
| 0.05 | C2 | +824 [+680, +983] | 1.00 |
| 0.05 | better_of_C1_C2 | +824 [+681, +976] | 1.00 |
| 0.10 | C1 | +353 [+302, +409] | 1.00 |
| 0.10 | C2 | +382 [+332, +436] | 1.00 |
| 0.10 | better_of_C1_C2 | +382 [+331, +438] | 1.00 |
| 0.20 | C1 | +242 [+232, +257] | 1.00 |
| 0.20 | C2 | +257 [+248, +270] | 1.00 |
| 0.20 | better_of_C1_C2 | +257 [+248, +271] | 1.00 |

(The 300 seeds vary only the label mask over **one** fixed stream, so the intervals describe query randomness, not dataset sampling.)
In realised-cost terms H2c accumulates 2–4× more excess cost before alarming than C1/C2 at 10–20 % labels (1837 vs 662 / 518 at 10 %).

**Mechanism diagnostic (post-hoc, descriptive, nothing re-tuned; `d2_followup_paired_and_diagnostic.py`, `d2_wealth_at_onset_diagnostic.py`).**
Before batch 6 the cost increments have mean ≈ −0.36 (the nominal margin dominates), so cost-only Kelly bets λ = 0 and sits at log-wealth ≈ 0.
The Brier guide has no margin (point estimate `r_0`, tolerance 0) and is positive early (Brier 0.025 and 0.077 on batches 3–4 vs 0.0045 nominal), so H2c bets
λ ≈ 0.025 (≈ 40 % of the cost cap 0.063) against a negative-drift statistic. Mean log-wealth at index 1943: **H2c −7.2 / −15.4 / −30.0 nats**
(5 / 10 / 20 % labels) vs C1 −0.01 / −0.00 / 0.00 and C2 −0.5 / −1.1 / −1.9. Inside batch 6 H2c's mean bet is larger (0.0119 vs 0.0032) but it must first
repay the deficit; at index 4243 its mean log-wealth is 6.3 / 12.4 / 25.6 vs C1 11.0 / 22.7 / 46.8 and C2 22.1 / 46.7 / 99.1.
This is the X1 "guide not aligned with the tested statistic's margin" failure on real data.

**Caveats that bound this result.** (a) One dataset, one fixed stream, exposed; (b) a *much* tighter nominal bound (empirical Bernstein, larger n_cal) would shrink the margin asymmetry and could change the ordering — **not run**, because choosing it after seeing these outcomes would be tuning on exposed data; (c) no causal shift label, so no power/size is defined on B; (d) replay feedback is simulated; (e) positive-class definition and costs follow earlier repository convention rather than a domain utility.
