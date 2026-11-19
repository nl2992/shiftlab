# E2 / E3 / E3b: long-horizon causal-safety premium and RB-DP scaling

**Date:** 2026-11-13. Not committed. Solver for all headline numbers: `src/shiftlab/paper4/risk_budget_dp_fast.py` with `lattice_exact=True`
(w lattice Z/(10*2^B), alpha = 1/10, n_beta = 401, delay 1, c = k = 0, emissions (e, 1-e), prior 1/2, C0 = T/2).
The first pass used the old solver `risk_budget_dp.py` (uniform w grid, K = 20, n_beta = 201); those numbers are kept as a cross-check (`e2e3_cells.jsonl`).
Every cell records both L and U for each mode. Point estimate rho = (U_c - U_i)/(C0 - U_i); bracket rho in [(L_c - U_i)/(C0 - L_i), (U_c - L_i)/(C0 - U_i)].
**U is an upper bound on V*, L a lower bound (lattice lemma is derived in the solver docstring, not formally proved in the repo), so rho from U is a point estimate, not a certified bound.**
Tables show rho with a "±half-width" of the bracket when it is at least 5e-5.

## 1. E3: rho_Gamma(T), e = 1/10

### t = 2/3 (r = 0.3333)

| B | T=6 | T=8 | T=12 | T=16 | T=24 | T=32 | T=48 | T=64 | T=100 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3352 | 0.3335 | 0.3333 | 0.3333 | 0.3333 | 0.3333 | 0.3333 | 0.3333 | 0.3333 |
| 2 | 0.2133 | 0.2041 | 0.2004 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 3 | 0.1701 | 0.1543 | 0.1454 | 0.1434 | 0.1429 | 0.1429 | 0.1429 | 0.1429 | 0.1429 |
| 4 | 0.1603 | 0.1666 | 0.1254 | 0.1130 | 0.1113 | 0.1111 | 0.1111 | 0.1111 | 0.1111 |
| 5 | 0.1612 | 0.1806 | 0.1486 | 0.1276 | 0.1179 | 0.1143 | 0.1135 | 0.1135 | 0.1135 |
| 6 | 0.1612 | 0.1999 | 0.2032 | 0.1817 | 0.1520 | 0.1433 | 0.1406 | 0.1404 | 0.1404 |

### t = 3/4 (r = 0.5)

| B | T=6 | T=8 | T=12 | T=16 | T=24 | T=32 | T=48 | T=64 | T=100 | T=200 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.2619 | 0.2529 | 0.2502 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| 2 | 0.1746 | 0.1564 | 0.1458 | 0.1436 | 0.1429±0.0002 | 0.1429 | 0.1429 | 0.1429 | 0.1429 | 0.1429 |
| 3 | 0.2227 | 0.1956 | 0.1488 | 0.1188 | 0.1007±0.0001 | 0.1001±0.0005 | 0.1000 | 0.1000 | 0.1000 | 0.1000 |
| 4 | 0.2944 | 0.2852 | 0.2292 | 0.1832 | 0.1499 | 0.1414±0.0003 | 0.1383±0.0002 | 0.1380 | 0.1379 | 0.1379 |
| 5 | 0.3120 | 0.3694 | 0.3318 | 0.2858 | 0.2429 | 0.2240±0.0003 | 0.2150±0.0004 | 0.2141±0.0001 | 0.2139 | 0.2139 |
| 6 | 0.3120 | 0.4139 | 0.4294 | 0.4001 | 0.3459±0.0001 | 0.3216±0.0002 | 0.3064 | 0.3039±0.0003 | 0.3034±0.0001 | - |
| 7 | - | - | - | 0.4559 | - | 0.3881±0.0001 | - | 0.3687±0.0003 | 0.3680±0.0001 | - |
| 8 | - | - | - | 0.4752 | - | 0.4189 | - | 0.4018±0.0005 | - | - |

### t = 9/10 (r = 0.8)

| B | T=6 | T=8 | T=12 | T=16 | T=24 | T=32 | T=48 | T=64 | T=100 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.1799 | 0.1454 | 0.1166 | 0.1065 | 0.1011 | 0.1002 | 0.1000 | 0.1000 | 0.1000 |
| 2 | 0.2818 | 0.2692 | 0.2101 | 0.1514 | 0.0705±0.0001 | 0.0543±0.0002 | 0.0529±0.0004 | 0.0527±0.0006 | 0.0526 |
| 3 | 0.5154 | 0.4714 | 0.3551 | 0.2713 | 0.1703 | 0.1542 | 0.1496±0.0003 | 0.1489±0.0006 | 0.1460±0.0002 |
| 4 | 0.5178 | 0.5434 | 0.4437 | 0.3498 | 0.2548 | 0.2326 | 0.2241±0.0002 | 0.2227±0.0006 | 0.2218±0.0003 |
| 5 | 0.5633 | 0.6211 | 0.5279 | 0.4161 | 0.3244 | 0.2913 | 0.2729±0.0002 | 0.2699±0.0005 | 0.2688±0.0003 |
| 6 | 0.5633 | 0.6293 | 0.5496 | 0.4344 | 0.3391 | 0.3055 | 0.2838±0.0001 | 0.2783±0.0003 | 0.2762±0.0007 |

Reading: for every (t, B) with B <= 6 and every t, rho_Gamma(T) decreases and then flattens; by T = 48-100 the last values agree to about 3 decimals (t = 9/10 is slowest, mixing factor r^T with r = 0.8; its small remaining drift is of the order of the bracket width). No curve heads to zero. B = 7, 8 exist only at t = 3/4 and only to T = 100 (B = 7) and T = 64 (B = 8); B = 8 (0.4189 at T=32, 0.4018 at T=64) and B = 7 at T=64 to 100 (0.3687, 0.3680) have not fully levelled.

### Level-off summary (last three T per cell, relative change between the last two)

| t | B | last 3 T | last 3 rho | rel. change last two | VOI_causal(last T) | VOI_iid(last T) | causal risk of iid-mode policy | of causal-mode policy |
|---|---|---|---|---|---|---|---|---|
| 2/3 | 1 | [48, 64, 100] | 0.3333, 0.3333, 0.3333 | -0.00% | 0.01600 | 0.02400 | 0.2000 | 0.1000 |
| 2/3 | 2 | [48, 64, 100] | 0.2000, 0.2000, 0.2000 | -0.00% | 0.03200 | 0.04000 | 0.2000 | 0.1000 |
| 2/3 | 3 | [48, 64, 100] | 0.1429, 0.1429, 0.1429 | -0.00% | 0.04800 | 0.05600 | 0.2000 | 0.1000 |
| 2/3 | 4 | [48, 64, 100] | 0.1111, 0.1111, 0.1111 | +0.00% | 0.06400 | 0.07200 | 0.2000 | 0.1000 |
| 2/3 | 5 | [48, 64, 100] | 0.1135, 0.1135, 0.1135 | -0.00% | 0.08000 | 0.09024 | 0.2000 | 0.1000 |
| 2/3 | 6 | [48, 64, 100] | 0.1406, 0.1404, 0.1404 | -0.01% | 0.09600 | 0.11168 | 0.4000 | 0.1000 |
| 3/4 | 1 | [64, 100, 200] | 0.2500, 0.2500, 0.2500 | -0.00% | 0.03200 | 0.04267 | 0.2000 | 0.1000 |
| 3/4 | 2 | [64, 100, 200] | 0.1429, 0.1429, 0.1429 | -0.00% | 0.06400 | 0.07467 | 0.2000 | 0.1000 |
| 3/4 | 3 | [64, 100, 200] | 0.1000, 0.1000, 0.1000 | -0.00% | 0.09600 | 0.10667 | 0.2000 | 0.1000 |
| 3/4 | 4 | [64, 100, 200] | 0.1380, 0.1379, 0.1379 | -0.00% | 0.12800 | 0.14848 | 0.2000 | 0.1000 |
| 3/4 | 5 | [64, 100, 200] | 0.2141, 0.2139, 0.2139 | -0.00% | 0.15999 | 0.20352 | 0.4000 | 0.1000 |
| 3/4 | 6 | [48, 64, 100] | 0.3064, 0.3039, 0.3034 | -0.16% | 0.19197 | 0.27559 | 0.3833 | 0.1000 |
| 3/4 | 7 | [32, 64, 100] | 0.3881, 0.3687, 0.3680 | -0.20% | 0.22821 | 0.36108 | 0.3833 | 0.1000 |
| 3/4 | 8 | [16, 32, 64] | 0.4752, 0.4189, 0.4018 | -4.10% | 0.26707 | 0.44644 | 0.3833 | 0.1000 |
| 9/10 | 1 | [48, 64, 100] | 0.1000, 0.1000, 0.1000 | -0.00% | 0.12800 | 0.14222 | 0.2000 | 0.1000 |
| 9/10 | 2 | [48, 64, 100] | 0.0529, 0.0527, 0.0526 | -0.10% | 0.25599 | 0.27022 | 0.2000 | 0.1000 |
| 9/10 | 3 | [48, 64, 100] | 0.1496, 0.1489, 0.1460 | -1.94% | 0.38389 | 0.44953 | 0.2000 | 0.1000 |
| 9/10 | 4 | [48, 64, 100] | 0.2241, 0.2227, 0.2218 | -0.43% | 0.56913 | 0.73132 | 0.4000 | 0.1000 |
| 9/10 | 5 | [48, 64, 100] | 0.2729, 0.2699, 0.2688 | -0.41% | 0.84488 | 1.15546 | 0.4000 | 0.1000 |
| 9/10 | 6 | [48, 64, 100] | 0.2838, 0.2783, 0.2762 | -0.76% | 1.25437 | 1.73295 | 0.4000 | 0.1000 |

Both VOIs converge (M2): e.g. t = 3/4, B = 3: VOI_causal/VOI_iid = 0.09592/0.10659 (T=32), 0.09600/0.10667 (T=48 and beyond, to T = 200). At t = 2/3 they are exactly 0.016 B (causal) and 0.024, 0.040, 0.056, 0.072 (iid, B = 1..4) from T = 48 on. The IID-mode policy, evaluated against the causal null, has worst-case risk 0.2-0.4 against the budget alpha = 0.1 (the causal-mode policy sits at 0.1000), so the IID design is unsafe under the causal null in every cell of the table at large T.
Full VOI series are in `results/e2e3_fast_summary.json` and `results/e2e3_fast_cells.jsonl`.

## 2. Theorem checks

- **M1 (B = 1).** Max |rho - closed form| over all B = 1 cells (T = 4..100/200, three t): 1.3e-12 (t=2/3), 2.3e-12 (t=3/4), 2.0e-14 (t=9/10). Passes.
- **M4 (B = 2, liminf >= (1-r)/(2(3+r)), c = 0).** t=2/3: bound 0.10000, rho(T=100) = 0.20000. t=3/4: bound 0.07143, rho(T=200) = 0.14286. t=9/10: bound 0.02632, rho(T=100) = 0.05263 (min over T >= 16 equals the last value). The proved bound holds with a factor of about 2 to spare; the observed limits are (1-r)/(3+r) = 0.2, 0.1429, 0.0526 to the printed digits, exactly twice the bound (numerical observation only).
- **Certified cells.** 60 cells with d = 1, k = 0, alpha = 1/10, e = 1/10, c = 0 (same e and c as `wpM_scaling.py`; B <= 4, T <= 12 (B=1 to 16), t in {2/3, 3/4, 9/10}) from `wpM_scaling_v1_compact.json`: max |rho diff| = 4.2e-13, max |Gamma diff| = 3.3e-14, max |VOI_iid diff| = 1.5e-13. Agreement to float precision (the certified numbers are rational intervals of width ~1e-12).
- **Contradictions with a proved theorem:** none found.

## 3. E3b: the theorem rectangle (t = 63/125, r = 1/125, e = 3/20, g = 0.49)

U values (12 significant digits) from the lattice solver; L equals U to 12 digits in all these cells (symmetric chain, beliefs stay at 1/2 before the first label, so the beta grid does not matter). Rows at n_beta = 401 and 801 agree to ~1e-11 in rho.

| B | T | U_iid | U_causal | VOI_iid | VOI_causal | Gamma | rho_Gamma (12 digits) | proved bound |
|---|---|---|---|---|---|---|---|---|
| 1 | 16 | 7.99960797491 | 7.99980241935 | 3.920251e-04 | 1.975806e-04 | 1.944444e-04 | 0.495999999944 | 0.49600 |
| 1 | 20 | 9.99960797491 | 9.99980241935 | 3.920251e-04 | 1.975806e-04 | 1.944444e-04 | 0.495999999943 | 0.49600 |
| 1 | 32 | 15.9996079749 | 15.9998024194 | 3.920251e-04 | 1.975806e-04 | 1.944444e-04 | 0.495999999938 | 0.49600 |
| 2 | 16 | 7.99941039427 | 7.99960483871 | 5.896057e-04 | 3.951613e-04 | 1.944444e-04 | 0.329787234032 | 0.16489 |
| 2 | 20 | 9.99941039427 | 9.99960483871 | 5.896057e-04 | 3.951613e-04 | 1.944444e-04 | 0.329787234089 | 0.16489 |
| 2 | 32 | 15.9994103943 | 15.9996048387 | 5.896057e-04 | 3.951613e-04 | 1.944444e-04 | 0.329787234065 | 0.16489 |
| 3 | 16 | 7.99921281362 | 7.99940725806 | 7.871864e-04 | 5.927419e-04 | 1.944444e-04 | 0.247011952191 | 0.18812 |
| 3 | 20 | 9.99921281362 | 9.99940725806 | 7.871864e-04 | 5.927419e-04 | 1.944444e-04 | 0.247011952178 | 0.18812 |
| 3 | 32 | 15.9992128136 | 15.9994072581 | 7.871864e-04 | 5.927419e-04 | 1.944444e-04 | 0.247011952179 | 0.18812 |
| 4 | 16 | 7.99901523308 | 7.99920967752 | 9.847669e-04 | 7.903225e-04 | 1.944444e-04 | 0.197452250066 | 0.15476 |
| 4 | 20 | 9.99901523298 | 9.99920967742 | 9.847670e-04 | 7.903226e-04 | 1.944444e-04 | 0.197452229454 | 0.15476 |
| 4 | 32 | 15.999015233 | 15.9992096774 | 9.847670e-04 | 7.903226e-04 | 1.944444e-04 | 0.197452229368 | 0.15476 |
| 5 | 16 | 7.99881765284 | 7.99901209728 | 1.182347e-03 | 9.879027e-04 | 1.944444e-04 | 0.164456303774 | 0.13201 |
| 5 | 20 | 9.99881765243 | 9.99901209688 | 1.182348e-03 | 9.879031e-04 | 1.944444e-04 | 0.164456247938 | 0.13201 |
| 5 | 32 | 15.9988176523 | 15.9990120968 | 1.182348e-03 | 9.879032e-04 | 1.944444e-04 | 0.164456233413 | 0.13201 |
| 6 | 16 | 7.99862010992 | 7.99881455437 | 1.379890e-03 | 1.185446e-03 | 1.944444e-04 | 0.140912995687 | 0.11017 |
| 6 | 20 | 9.99862007219 | 9.99881451664 | 1.379928e-03 | 1.185483e-03 | 1.944444e-04 | 0.140909142640 | 0.11017 |
| 6 | 32 | 15.9986200717 | 15.9988145161 | 1.379928e-03 | 1.185484e-03 | 1.944444e-04 | 0.140909090903 | 0.11017 |

Bounds used: B=1 (1-r)/2 = 0.496; B=2 M4's liminf (1-r)/(2(3+r)); B=3..6: 19/101, 13/84, 40/303, 13/118 (the B = 6 proof needs T >= 20; the T = 16 value 0.140913 is shown anyway). Every cell is at or above its bound (B = 1 equals the closed form 0.496 to 6e-11). Gamma is the same 1.944444e-4 for all B and T: the extra queries raise VOI_iid and VOI_causal by the same amount per query.

**Sensitivity.** (a) Lattice solver, n_beta 401 -> 801: rho unchanged to at least 1e-11 in all 18 cells (table above is for 401; the 801 rows are in the JSONL). (b) Old solver (w_step_div 20 -> 40 and n_beta 401 -> 801) on B = 2 and B = 3 at T = 16: change in rho -8.5e-12 and +1.1e-12; change in U_causal and U_iid below 5e-15 in absolute value. These two cells are on-lattice at both grids, so this shows only that, here, grid doubling changes nothing; it does not test B >= 4 (covered instead by the old-vs-lattice comparison in section 5).

## 4. E2: scaling

Lattice-exact fast solver, t = 3/4, e = 1/10, causal mode, n_beta = 401, one CPU thread, other jobs were running on the machine (3 of my workers plus another agent's), so timings are pessimistic by an unknown factor. 'Full' = L and U together (in lattice mode L is the same DP as the upper DP, so full and U-only coincide).

| T | B | N_w | full solve s | L-only s | U-only s | L | U |
|---|---|---|---|---|---|---|---|
| 16 | 3 | 81 | 0.6 | 0.8 | 0.6 | 7.90700000 | 7.90700000 |
| 32 | 3 | 81 | 1.2 | 1.4 | 1.1 | 15.90402320 | 15.90407812 |
| 64 | 3 | 81 | 2.2 | 2.6 | 2.1 | 31.90400000 | 31.90400018 |
| 128 | 3 | 81 | 4.4 | 5.3 | 4.4 | 63.90400000 | 63.90400004 |
| 256 | 3 | 81 | 8.3 | 12.2 | 9.5 | 127.90400000 | 127.90400004 |
| 32 | 1 | 21 | 0.2 | 0.1 | 0.1 | 15.96800000 | 15.96800000 |
| 32 | 2 | 41 | 0.4 | 0.4 | 0.4 | 15.93600005 | 15.93600146 |
| 32 | 4 | 161 | 2.6 | 3.1 | 2.7 | 15.87262485 | 15.87262487 |
| 32 | 6 | 641 | 15.5 | 20.4 | 15.6 | 15.81329574 | 15.81329575 |
| 32 | 8 | 2561 | 122.1 | 128.1 | 136.7 | 15.74506126 | 15.74506130 |

Growth: at B = 3, time doubles when T doubles (0.6, 1.2, 2.2, 4.4, 8.3 s for T = 16..256): linear in T. At T = 32 the time is 0.2, 0.4, 1.2, 2.6, 15.5, 122 s for B = 1, 2, 3, 4, 6, 8: growth in B is exponential (about 6x from B = 4 to 6 and 8x from 6 to 8), because the lattice has N = 10*2^B points. The old uniform-grid solver instead grows about linearly in B because its grid is fixed.
Rough rule: seconds ~ 1.6e-3 * T * B * 2^B per mode.

For comparison the old solver (uniform K = 20 grid, N_w = 200, n_beta 401, run concurrently with load) took:

| T | B | full s | upper-only s | lower DP s |
|---|---|---|---|---|
| 16 | 3 | 30.3 | 15.4 | 14.9 |
| 32 | 3 | 61.1 | 31.4 | 29.7 |
| 64 | 3 | 121.4 | 62.4 | 59.1 |
| 128 | 3 | 271.7 | 149.7 | 122.0 |
| 32 | 1 | 26.3 | 13.5 | 12.8 |
| 32 | 2 | 45.2 | 23.5 | 21.7 |
| 32 | 4 | 85.0 | 44.6 | 40.4 |
| 32 | 6 | 130.3 | 68.1 | 62.2 |
| 32 | 8 | 169.5 | 87.0 | 82.5 |

Old solver: linear in T (30, 61, 121, 272 s for T = 16..128 at B = 3) and about linear in B; T = 256 not run. Exact solver limits from the repo docs (not re-run): T = 16, B = 3, t = 63/125, e = 3/20 timed out at 3,600 s; `docs/paper4/experiments/04_scaling_and_comparators.md` reports 37-71 s at T = 10. The lattice solver does T = 16, B = 3 in 0.6 s (this run, loaded machine); T = 256, B = 3 in 8 s.

## 5. Old uniform-grid solver versus lattice solver (anomaly list)

The lead's note is confirmed. Over the 30 overlapping cells per B (T <= 64, three t), max |U_old - U_new| (old is never below new, as it must be for a restricted grid, except the +/- 1e-12 float noise at B <= 2):
B = 1, 2: <= 1.3e-12. B = 3: causal 6.8e-6, iid 1.4e-5 (t=9/10, T=48). B = 4: causal 1.4e-5. B = 5: iid 2.1e-4 (t=9/10, T=32). B = 6: iid 1.4e-4 (t=9/10, T=32). Largest effect on rho: 1.3e-4 (t=9/10, B=5, T=32). So the first-pass numbers for B >= 5 at t = 9/10 were slightly suboptimal (U not tight on that grid); conclusions do not change, but the first-pass JSONL should not be used for B >= 3 at t = 9/10. At t = 2/3 and 3/4 old and lattice agree to ~1e-13 except noted B = 3 cells.
One further note: the first old-solver driver crashed once (B > T cells, e.g. B = 5 at T = 4) and was restarted with those cells removed; completed cells are unaffected.

## 6. Caveats

- rho values are point estimates from U; they are not certified bounds. The lattice L-U gap is zero for the symmetric-belief cells (rectangle) and reaches 1.1e-3 in V (rho bracket half-width up to 7e-4) at t = 9/10, B = 5, 6, T = 100, because of linear beta interpolation in L (n_beta = 401 not refined).
- n_beta = 201 was used in the first pass (checked: U identical to 1e-12 at two cells); all headline numbers use 401.
- Only t = 3/4 has B = 7 (T = 16, 32, 64, 100), B = 8 (T = 16, 32, 64) and T = 200 (B <= 5). t = 2/3 and 9/10 at B = 7, 8 and T = 200 at B = 6 were not run. The fast pass alone used about 70 CPU-minutes (sum of per-task runtimes) and the old-solver pass more; the 40-minute wall budget was exceeded (about 85 minutes wall in total).
- The M6-M9 tests concern a tiny VOI (1e-4..1e-3); U values near 16 carry ~1e-15 float noise, so rho is trustworthy to about 1e-10 there (B = 4..6 show differences of order 1e-8 in rho between T = 16, 20 and 32; whether these are small finite-T effects or float noise was not resolved).
- Timings were taken under shared load.
- Lattice-exactness (the dyadic-lattice lemma) is derived by the lead in the solver docstring, not proved; evidence is exact agreement with certified values on 60 cells.

## 7. Reproduce

```
uv run --no-sync python scripts/paper4_continuation/rbdp/e2e3_run.py 42            # first pass, old solver -> results/e2e3_cells.jsonl
uv run --no-sync python scripts/paper4_continuation/rbdp/e2e3_fast_run.py 28        # lattice solver -> results/e2e3_fast_cells.jsonl (resumable)
uv run --no-sync python scripts/paper4_continuation/rbdp/e2e3_fast_analyze.py       # tables + results/e2e3_fast_summary.json
uv run --no-sync python scripts/paper4_continuation/rbdp/e2e3_report.py             # regenerates this file
```
Files: `scripts/paper4_continuation/rbdp/e2e3_*.py`, `docs/paper4_continuation/rbdp/results/e2e3_*`. Every JSONL line carries the script and solver sha256.

