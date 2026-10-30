# Nominal-risk uncertainty (`outputs/h2c_restart/nominal_risk_uncertainty.json`; development, 400 seeds)
**Guarantee (PROVED, standard union bound).** Let U0 be an upper confidence bound for the nominal cost c0 computed from an independent calibration sample with P(U0 ≥ c0) ≥ 1 − α_cal. On that event the cost increment built against U0 has non-positive conditional drift under H0, so the H2c e-process thresholded at 1/α_test has finite-horizon error ≤ α_test; the total error is ≤ α_cal + α_test. Here α_cal = .01, α_test = .04 (threshold 25), cost range B = 5, G1 deployed model (true c0 = 0.409). Requires the calibration sample to be independent of, and distributed like, the source-regime stream.
**Power cost (H2c, γ = .995, label rate 10% / 20%; power on abrupt concept shift δ = 2 / δ = 1.5 at t0 = 700; null FA was 0 in every row):**
| bound | n_cal | U0 | δ=2 power | δ=1.5 power |
|---|---|---|---|---|
| known c0 (reference) | – | .409 | .603 / .902 | .290 / .662 |
| Hoeffding | 300 | .778 | 0 / 0 | 0 / 0 |
| Hoeffding | 1,000 | .711 | 0 / .003 | 0 / 0 |
| Hoeffding | 5,000 | .519 | .098 / .200 | .048 / .058 |
| Hoeffding | 50,000 | .443 | .385 / .705 | .158 / .398 |
| empirical Bernstein (Maurer–Pontil) | 300 | .634 | .010 / .003 | 0 / .003 |
| empirical Bernstein | 1,000 | .609 | .025 / .010 | .003 / .003 |
| empirical Bernstein | 5,000 | .454 | .352 / .657 | .125 / .325 |
| empirical Bernstein | 50,000 | .420 | **.535 / .850** | .233 / .570 |
**Findings.** Treating the nominal risk as known hides a large practical cost: with a calibration sample of up to 1,000 events the monitor has essentially zero power, because the upper bound exceeds c0 by .2–.37 and the harmful increase is only ≈ .23. The empirical-Bernstein bound is far tighter than Hoeffding (cost std ≈ 0.72 against a range of 5), recovering most of the known-nominal power at n_cal = 50,000 (.535 vs .603; .850 vs .902). All earlier power numbers in this repository assume a known (large-simulation) nominal; the real-data protocol therefore needs a calibration period of the order of tens of thousands of labelled events, or a tighter nominal-risk bound, for the guarantee to be non-vacuous. Not done: the same analysis with the Brier-guidance nominal, a one-sample variance-adaptive calibration inside the monitor, or a sequentially updated calibration.
