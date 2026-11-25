# R3 Paper claim audit: f3_tmlr main.tex (commit e418865f)

Auditor: fresh same-family (Claude) auditor. review_independence: same-family; acceptance_status: PROVISIONAL.
Scope: main.tex + tables/*.tex + figures/*.py vs results/riskbudget/*, outputs/paper3/riskbudget/*, configs/paper3/*, ledger, git history. Read-only.
Tex/tables in the working tree equal HEAD; only main.pdf differs (rebuilt after the commit). Uncommitted edits exist in src/.../bounds_v2.py and shield_v2.py (diagnostic `scale`/`mix_m` options, defaults unchanged); not paper-relevant but the supplement ships these files.

## Summary (about 115 claim groups)
- verified (incl. rounding_ok): ~104
- mismatch: 4
- unsupported / misleading: 4
- not checkable / partially checkable: 4
Independent recomputation: all simulation numbers (violation counts, worst-regime rates and Wilson bounds, pooled/stress/original rates, J, bootstrap deltas) recomputed from outputs/confirm/*.json (30 regimes x 1000 seeds, 18 arms); all real-stream numbers (3,880 runs/arm, exceed/violation counts, J, dJ, max harm, all three conditions) recomputed from outputs/real/*/*.json excluding openml_ldpa and uci_occupancy; Props 3/4, ledger wall-clock, running-example arithmetic, Fig. 3 tape (re-run mech_data.py) and 56/62 sprint episodes recomputed.

## Mismatches and unsupported claims (details)
| # | Location | Exact text | True value / issue | Fix |
|---|---|---|---|---|
| M1 | Sec 5.4 Regime map ("The median is at least \LargeXMin") | "The median is at least 0.96 for x>=1" | min over paced arms is real/paced bin [1,2) = 0.9572 (<0.96) | "at least 0.95" or "about 0.96"; make_tables.py should floor, not round |
| M2 | Sec 5.3 Real streams | "it stays within \RealSixVsNever{} units of never switching" (10.0) | f3_pi1_h6 dJ vs never = -10.01: the shield is 10.0 units *better* than never, not "within" 10.0 (and 10.01>10.0) | "improves on never switching by 10.0 units per episode" |
| M3 | App. Reproducibility/Compute | "real-stream study (12 streams, 194 episodes, ...) 1,873 s"; "its second look at the real streams 487 s" | ledger stages real_streams and real_streams_v3_second_look ran 14 streams / 230 episodes (n_episodes=230); the 12-stream numbers are a re-analysis of existing outputs (ledger note, "No new simulation was run") | "ran on 14 streams (230 episodes); 12 (194) retained in analysis" |
| M4 | Abstract, Intro, Conclusion, Fig 1 caption | "five tuned comparators" | only wald_cut, cusum, gate_wald have tuned parameters; cusum_rb_h8 (theta=8 fixed) and stoploss_R20 (R set by user) are untuned (App. C "have no tuned parameters of their own") | "five comparators (three tuned)" or drop "tuned" |
| U1 | App. Calibrated results | "The most conservative threshold leaves worst-regime violation rates of 0.535 and 0.671"; Table caption "(the others are the most conservative grid value)" | not the least-violating threshold: on calibration seeds at R=20 theta=2 gives worst violation 0.250 vs 0.680 for theta=0.5 (generator computes CalCusBestH=2, CalCusBestViol=0.250 but never prints them). theta=0.5 is only the protocol's fallback, "most conservative" in rollback-eagerness, not in violation. Conclusion "none met .05" still true | say "the fallback threshold (smallest grid value)" and report best-on-grid (theta=2, 0.250 at R=20; 0.595 at R=12 for theta=.5) |
| U2 | Sec 4 end / App. Exposure-ratio test | "The prediction and test were fixed before the test run"; "thresholds (x=.5 and 1) were fixed before the analysis script ran" | commit 5f1cdae2 (22:15:12, one minute before results commit e5ac7146) states only "L increases with x" (Spearman>0, CI above 0) with bins [0,.5),[.5,1),[1,2),[2,inf) as descriptive. The quantitative form "small for x<.5, near one for x>1" is not in the pre-run script (the bin edges are). Timing claim itself is true | "the monotone prediction (Spearman > 0) and bin edges were committed before the run; the 'small below .5, near one above 1' reading is post hoc" |
| U3 | Sec 5.3 | "0 violations ... in every arm ..., as Theorem 1 implies" | Theorem implies surely-zero only for full-sampling/blind arms; paced arms only <= delta (0 observed) | "as Theorem 1 implies for full sampling" |
| U4 | Fig. 6 (regime map) caption | "L is small when x<0.5 and close to 1 when x>=1" | holds for paced/v3 arms (median L 0.04-0.12); full-sampling medians at x<.5 are 0.40 (sim) and 0.32 (real); real full-sampling at [1,2) is 0.87 | restrict to "for the paced arms" |

## Not checkable / partial
- "six stress regimes specified before any F3 run": 04F registration says so; regimes_f3_v1.json mtime 2026-11-14 07:02 precedes the first (pilot) run (ledger 06:17 UTC end, 433 s); but first git commit of the file is f5cadbd9 (2026-11-15), so ordering rests on mtime/registration text.
- "run once": confirm output dir refuses overwrite (run_confirm.py), single ledger record, no source change between f5cadbd9 and result commit 5f4ecb55; ledger shows git_dirty=true at run (uncommitted files not provable). Real-stream run: protocol commit e008838c/faf4ef87 (08:05-08:06 +01) precedes run start (~08:09 +01), single ledger record.
- Tuning claims ("32-config random search on six tuning seeds over 24 original regimes, same budget for every method"): tune_v2.py confirms 24 regimes, 6 seeds, 32 configs for shield; wald_cut/cusum/gate parameters come from earlier joint study (not in this repo's outputs), so equal-budget claim not verifiable here.
- Related-work descriptions of Lindon-Kallus (martingale only in event-time filtration) and Prudent-Banker rates not checked beyond abstract.

## Claim table
Status: V verified, R rounding_ok, M mismatch, U unsupported, N not checkable.
| Claim (location) | Paper | Source / recomputed | Status |
|---|---|---|---|
| 30 regimes, 30,000 runs/arm (abstract, Fig1, tables) | 30; 1000x30 | confirm_summary n_regimes=30,n_seeds=1000; 30 files x 1000 | V |
| Full sampling 0 violations (abstract, intro, Sec5.1, concl.) | 0 | 4 arms total_k=0 (recomputed) | V |
| Paced arms "far below delta" | max Wilson upper 0.006; 1 violation each of 30,000 | recomputed (k=1,1) | V |
| Comparator worst-regime exceedance "64-99%" | .635/.830/.841/.852/.987 | recomputed identical; 63.5% rounds to 64 | R |
| Worst regime adverse dropout for four, high fee for CUSUM; k=30>R | yes | worst regimes recomputed; expensive_switch k=30 | V |
| Wilson ranges, worst rates in Table 1/C3 (0.852 [.829,.873] etc.) | | recomputed | V |
| Original-regime pooled rates "1-6%"; stress 23/17/13/16/17; orig 2/6/2/2/1 | | recomputed 2.5,5.6,2.0,1.5,1.1 / 23.1,16.8,13.2,16.0,16.8 | R |
| Table 1 pooled viol. 6.6/7.9/4.3/4.4/4.2, q99, max | | recomputed (6.59,7.86,4.26,4.40,4.23) | V |
| J never 71.53, Wald 68.47, shield 69.43; vs never -2.10 [-2.22,-1.98], 2.9% | | recomputed -2.100 [-2.222,-1.988]; my bootstrap (2000 resamples) vs paper 10,000 | V |
| vs Wald +0.96 [+0.86,+1.06], 1.4%; stress -5.19 [-5.40,-4.98], 7.4%; orig +2.50, 3.7% | | recomputed | V |
| "In six stress regimes shield costs less than Wald" | CI upper -4.98 | V |
| Ablations 0.940/0.862/0.341 (R=12) | | recomputed incl. Wilson | V |
| C1-C6 table rows, "supported" | | confirm_summary + registration text (criteria match) | V |
| Registered 2026-11-15 before seeds opened; 18 arms; seeds 5303500000-999; dev offsets | | 04F registration doc commit f5cadbd9 21:07 +01; run ended 23:53 +01 (ledger 22:53 UTC, 659 s) | V |
| x = .25/.11/.06 at R=12/20/30 | r=.3,d=5 | 1.5/6,1.5/14,1.5/24 | V |
| Defaults T=300,B=60,k=3,c_q=.05; real T=2000,B=200,k=5 | | regimes_v1 defaults; real_streams.py assert | V |
| Stress-regime descriptions (40 rounds late, 30%, .6, bait first quarter, rho .95) | | regimes_f3_v1.json | V |
| 12 streams, 194 episodes, 3,880 runs/arm, 20 seeds | | recomputed from outputs | V |
| Real: Wald exceed R=24 456/863/966; stop-loss own R 298/863/936; max harm 175/529/400 | | recomputed identical | V |
| Real: shield 0 violations all arms/h/conditions | | recomputed (f3_pi1, f3v2d, blind8; also v3 table 0/3880) | V |
| Real: gains vs never at h=14..100: 82-116 (clean), 83-116 dropout, 81-105 delay | | recomputed | V |
| 82 of 180 cost units, 46% | 82.27/179.58=45.8 | V/R |
| h=6 "within 10.0 units" | | -10.01 (shield better) | M (M2) |
| "more with paced sampling at large headroom" | 160 vs 116 at h=100 | V |
| Table 5 (real) J/dJ/viol cells | | recomputed spot-check all arms | V |
| Regime map: n_units 472; 47 scarce regimes; 8 real streams; Spearman .69-.80; CIs>0; OLS coef>0 in 6 fits | | exposure_ratio_test.json (352+120 rows) | V |
| Retained "88-96%" paced | 1-median L[0,.5): .885,.876,.954,.963 | V/R |
| "median at least 0.96 for x>=1" | min .957 | M (M1) |
| "several bins exceed one" | yes (sim bins 1.12-1.19) | V |
| Pre-stated Spearman tests / prediction fixed before run | | commits 5f1cdae2<e5ac7146; content narrower | V (timing) / U2 |
| Scarce family spec (T=2000,B=200,k=5, r,d grid, 5 paths, 2 rho=.8, 47) | | regimes_f3_scarce_v1.json | V |
| v3: 12 candidates, selected pi_min=.25, reserve .25, best score 395.5, seeds 70000-70199 / fresh seeds | | v3_select_summary, f3_v3_frozen.json, ledger | V |
| Calibration: c=7,15,25; theta=.5,.5,1; only R=30 qualified (not on fresh seeds: .099, LB .082); 200 cal seeds; 1000 fresh | | calib_summary.json | V |
| Stop-loss deployed 0.000, J 73.53 vs 71.59 never vs 69.51 shield; +1.94; real 608.1 | | calib_summary | V |
| c=14 worst 0.585 at R=20 | | frontier | V |
| CUSUM-cal worst .535/.671, LB .504/.641 on fresh seeds; costs +8.50/+12.13 | | calib_summary | V |
| "most conservative threshold" wording | | | U (U1) |
| Real calibrated: CUSUM-cal minus shield -25.2 [-42.1,-9.8]; violations 415/1785/1055 at h=14 | | generator reads calib_summary; spot-read | V |
| Prop 3: 12 cells all attain; Prop 4: 24 cells, 5 above bound, max z 0.7, .203 v .198, .035 v .034 | | props_check.json (z recomputed .73) | V |
| Running example (W1=7, 8, roll at 15th, W=21, H=20, peak 11, 10, 6; m=9; (3/7)^10=2.1e-4; e^-7.2=7.5e-4; x=.36) | | recomputed by hand | V |
| Fig 3 caption: shield rolls back round 35 peak 20; stop-loss round 40 peak 25 | | re-ran mech_data.py | V |
| Fig 1b/Fig 4/Fig 5 data | | read from confirm_summary / outputs/real / descriptive; q99 31-37 recomputed | V |
| Fig 6 data from exposure_ratio_test.json rows | | V |
| Fig 2 pipeline counts (30, 1,000, 194, 12) | | asserted vs macros | V |
| Table 12 streams: 194 episodes, delays, 56/62 sprint better; per-stream errors | | recomputed from npz | V |
| Compute: wall-clock 659/1,873/1,163/2,535/112/487, 15 stages, 227 min | | ledger sums to 226.7 min | V (but see M3) |
| "frozen", "no arm tuned on these streams" (real) | | 05F protocol, v3 selected on sim only, calibration on sim only | V |
| "Pre-specified and run once 2026-11-16 on 14 streams" | | protocol commit precedes run | V |
| Stress regimes "specified before any F3 run" | | mtime only | N |
| "five tuned comparators" | | | M (M4) |
| 12 streams "from earlier studies by the authors", "no arm of this study ... before" | | protocol text consistent | V |
| Wall-clock streams count | | | M (M3) |
| Citations: Prudent-Banker (2605.23351), Drift2Act (2603.08578), RAR (2611.02251), Challenger (2512.18390), Lindon-Kallus (2603.25971), Zhou et al. (2610.10393), Policy Learning with Abstention (2510.19672), CAMS (2207.06030) | | arXiv abstracts fetched: exist, authors match, descriptions accurate (CAMS key says 2024 but year field 2022, cosmetic) | V |
| Classic citations (Wu 2016, Kazerouni 2017, Garcelon 2020, Katariya 2019, Moradipari 2020, Joulani 2013, Cesa-Bianchi 2013, Cheng 2023, Karimi 2021, Howard 2021, Waudby-Smith 2024, Johari 2017/2022, Thomas 2015 x2, Laroche 2019, Karampatziakis 2021, Ramdas 2023, Badanidiyuru 2013/2018, Podkopaev 2022) | | well-known works; bib metadata plausible, not individually web-verified | N (low risk) |
