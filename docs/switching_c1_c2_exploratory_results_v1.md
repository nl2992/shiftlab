# Exploratory results: C1 and C2 against R6 baselines on one shared harness

**Date:** 2026-10-30. **Status:** EXPLORATORY, development-only (R4). No novelty, theorem, efficacy or confirmatory claim follows from anything here. Protocol: `docs/switching_c1_c2_exploratory_protocol_v1.md`. Outputs (git-ignored): `outputs/switching_c1_c2_exploratory_v1/summary.md`, `outputs/switching_c1_c2_exploratory_v1/results.json`.

## Run record

* Code: `src/shiftlab/dive/switching_explore.py`, `scripts/run_switching_c1_c2_exploratory.py`, `tests/test_switching_explore.py`. Tests: 54 passed (`.venv/Scripts/python -m pytest tests/test_switching_explore.py`).
* Reproduce (full grid; the script default is `--mode smoke`):
  `.venv/Scripts/python scripts/run_switching_c1_c2_exploratory.py --mode full`
* Git: head `b1441254d81846124469b180f372b7f917cb0247`, dirty flag `true` at run time. At session start the protocol, the script, the module and the test file were untracked. The results describe the working tree as it was at the run; `results.json` records the SHA-256 of the four files at run time (below), not of any later edit.
* Source SHA-256 (from `results.json`): `switching_explore.py` `f7a330f5...23dbee`; `run_switching_c1_c2_exploratory.py` `f4f38a0e...eda5c`; `test_switching_explore.py` `a6cebf76...308e`; protocol `60390bfd...b1b3`.
* Elapsed 355.7 s. Mode `full`. Development seeds 0-7 (C2 `rho` selection only); evaluation seeds 1000-1029 (30 paired seeds per cell).
* `rho*` (development) = 0.75. No real stream was dropped (`real_dropped` is empty).
* Deviations from the protocol text are logged in the protocol's Deviation log (items 1-4), recorded before the full grid was launched.

## 1. Primary results (copied from `summary.md`)

Tables below are copied from `outputs/switching_c1_c2_exploratory_v1/summary.md`. Numbers are not re-rounded. Column `c2_rho0.75` is C2 at the development-selected `rho*`.

**Primary: net-cost difference vs strongest baseline per cell (all baselines)** (negative = candidate cheaper; 8 cells per scenario)

| scenario | c1_hmm_cs mean diff/round | c1_hmm_cs better/worse/ns cells | c2_rho0.75 mean diff/round | c2_rho0.75 better/worse/ns cells |
|---|---|---|---|---|
| persistent_std | +0.0924 | 0/7/1 | +0.0925 | 0/7/1 |
| fast_std | +0.0128 | 0/3/5 | +0.0134 | 0/3/5 |
| persistent_weak | +0.0250 | 0/4/4 | +0.0241 | 0/3/5 |
| null_boundary | +0.0018 | 0/7/1 | +0.0015 | 0/7/1 |
| null_harm | +0.0011 | 0/8/0 | +0.0013 | 0/8/0 |
| late_onset | +0.2286 | 0/8/0 | +0.1914 | 0/8/0 |
| reversal | +0.1510 | 0/8/0 | +0.1148 | 0/8/0 |
| offgrid_hmm | +0.0488 | 0/6/2 | +0.0515 | 0/6/2 |
| ALL | +0.0702 | 0/51/13 | +0.0613 | 0/50/14 |

**Secondary: vs strongest safety-gated baseline per cell (no_switch, episode_*, allonset)** (negative = candidate cheaper; 8 cells per scenario)

| scenario | c1_hmm_cs mean diff/round | c1_hmm_cs better/worse/ns cells | c2_rho0.75 mean diff/round | c2_rho0.75 better/worse/ns cells |
|---|---|---|---|---|
| persistent_std | +0.0067 | 0/3/5 | +0.0067 | 0/3/5 |
| fast_std | +0.0007 | 0/7/1 | +0.0013 | 0/8/0 |
| persistent_weak | +0.0023 | 0/5/3 | +0.0014 | 0/7/1 |
| null_boundary | +0.0016 | 0/8/0 | +0.0013 | 0/8/0 |
| null_harm | +0.0011 | 0/8/0 | +0.0013 | 0/8/0 |
| late_onset | +0.0885 | 0/8/0 | +0.0514 | 0/8/0 |
| reversal | +0.0513 | 0/8/0 | +0.0151 | 0/5/3 |
| offgrid_hmm | +0.0023 | 1/3/4 | +0.0049 | 0/3/5 |
| ALL | +0.0193 | 1/50/13 | +0.0104 | 0/50/14 |

**Mean cost per round minus no_switch**, averaged over the 8 cells of each scenario (negative = better than never switching)

| scenario | no_switch | periodic_mean | episode_geo | episode_equal | episode_front | allonset_edetector | dal_restart | pacing_bernoulli | c1_hmm_cs | c2_rho0.75 |
|---|---|---|---|---|---|---|---|---|---|---|
| persistent_std | +0.0000 | -0.0602 | -0.0054 | -0.0009 | -0.0077 | +0.0069 | -0.0403 | -0.0770 | -0.0023 | -0.0023 |
| fast_std | +0.0000 | +0.0010 | +0.0020 | +0.0017 | +0.0021 | +0.0017 | +0.0035 | -0.0082 | +0.0007 | +0.0013 |
| persistent_weak | +0.0000 | -0.0029 | +0.0017 | +0.0017 | +0.0014 | +0.0022 | -0.0013 | -0.0106 | +0.0022 | +0.0013 |
| null_boundary | +0.0000 | +0.0050 | +0.0017 | +0.0017 | +0.0017 | +0.0017 | +0.0059 | +0.0036 | +0.0016 | +0.0013 |
| null_harm | +0.0000 | +0.0352 | +0.0017 | +0.0017 | +0.0017 | +0.0017 | +0.0349 | +0.0362 | +0.0011 | +0.0013 |
| late_onset | +0.0000 | -0.2250 | -0.0860 | -0.0488 | -0.0943 | -0.1034 | -0.2107 | -0.1671 | -0.0151 | -0.0522 |
| reversal | +0.0000 | -0.1107 | -0.0432 | -0.0204 | -0.0463 | +0.1405 | -0.0637 | -0.0993 | +0.0015 | -0.0347 |
| offgrid_hmm | +0.0000 | -0.0300 | +0.0013 | +0.0017 | +0.0005 | -0.0034 | -0.0116 | -0.0360 | -0.0019 | +0.0008 |

Evaluator-only references over all cells: always_f1 +0.1035, regime_clairvoyant -0.2365.

**False-promotion frequency** (fraction of runs with at least one false promotion; regime-based with Wilson 95% interval, then `/` predictive-mean-based on HMM-drawn cells; pooled over the 8 cells x 30 seeds)

| scenario | no_switch | periodic_mean | episode_geo | episode_equal | episode_front | allonset_edetector | dal_restart | pacing_bernoulli | c1_hmm_cs | c2_rho0.75 |
|---|---|---|---|---|---|---|---|---|---|---|
| persistent_std | 0.000 [0.000,0.016] / 0.000 | 0.450 [0.388,0.513] / 0.346 | 0.054 [0.032,0.090] / 0.000 | 0.021 [0.009,0.048] / 0.000 | 0.042 [0.023,0.075] / 0.000 | 0.050 [0.029,0.085] / 0.000 | 0.275 [0.222,0.335] / 0.113 | 0.433 [0.372,0.497] / 0.142 | 0.042 [0.023,0.075] / 0.000 | 0.021 [0.009,0.048] / 0.000 |
| fast_std | 0.000 [0.000,0.016] / 0.000 | 0.750 [0.692,0.801] / 0.787 | 0.000 [0.000,0.016] / 0.004 | 0.000 [0.000,0.016] / 0.000 | 0.008 [0.002,0.030] / 0.008 | 0.013 [0.004,0.036] / 0.013 | 0.471 [0.409,0.534] / 0.588 | 0.679 [0.618,0.735] / 0.425 | 0.042 [0.023,0.075] / 0.000 | 0.000 [0.000,0.016] / 0.000 |
| persistent_weak | 0.000 [0.000,0.016] / 0.000 | 0.758 [0.700,0.808] / 0.729 | 0.004 [0.001,0.023] / 0.000 | 0.000 [0.000,0.016] / 0.000 | 0.008 [0.002,0.030] / 0.000 | 0.004 [0.001,0.023] / 0.000 | 0.317 [0.261,0.378] / 0.196 | 0.696 [0.635,0.751] / 0.667 | 0.000 [0.000,0.016] / 0.000 | 0.000 [0.000,0.016] / 0.000 |
| null_boundary | 0.000 [0.000,0.016] / 0.000 | 0.996 [0.977,0.999] / 0.996 | 0.000 [0.000,0.016] / 0.000 | 0.000 [0.000,0.016] / 0.000 | 0.008 [0.002,0.030] / 0.008 | 0.017 [0.006,0.042] / 0.017 | 0.867 [0.818,0.904] / 0.867 | 0.921 [0.880,0.949] / 0.921 | 0.000 [0.000,0.016] / 0.000 | 0.004 [0.001,0.023] / 0.004 |
| null_harm | 0.000 [0.000,0.016] / 0.000 | 0.617 [0.554,0.676] / 0.617 | 0.000 [0.000,0.016] / 0.000 | 0.000 [0.000,0.016] / 0.000 | 0.000 [0.000,0.016] / 0.000 | 0.000 [0.000,0.016] / 0.000 | 0.246 [0.196,0.304] / 0.246 | 0.533 [0.470,0.595] / 0.533 | 0.000 [0.000,0.016] / 0.000 | 0.000 [0.000,0.016] / 0.000 |
| late_onset | 0.000 [0.000,0.016] | 0.071 [0.045,0.110] | 0.000 [0.000,0.016] | 0.000 [0.000,0.016] | 0.000 [0.000,0.016] | 0.000 [0.000,0.016] | 0.000 [0.000,0.016] | 0.042 [0.023,0.075] | 0.000 [0.000,0.016] | 0.000 [0.000,0.016] |
| reversal | 0.000 [0.000,0.016] | 0.054 [0.032,0.090] | 0.008 [0.002,0.030] | 0.008 [0.002,0.030] | 0.021 [0.009,0.048] | 0.033 [0.017,0.064] | 0.067 [0.041,0.106] | 0.163 [0.121,0.214] | 0.029 [0.014,0.059] | 0.021 [0.009,0.048] |
| offgrid_hmm | 0.000 [0.000,0.016] / 0.000 | 0.579 [0.516,0.640] / 0.517 | 0.017 [0.006,0.042] / 0.000 | 0.004 [0.001,0.023] / 0.000 | 0.029 [0.014,0.059] / 0.000 | 0.017 [0.006,0.042] / 0.000 | 0.379 [0.320,0.442] / 0.204 | 0.550 [0.487,0.612] / 0.208 | 0.042 [0.023,0.075] / 0.004 | 0.013 [0.004,0.036] / 0.000 |

**Query use and switches** (mean over all 64 cells)

| method | queries / B | switches | queries never released |
|---|---|---|---|
| no_switch | 0.00 | 0.00 | 0.00 |
| periodic_mean | 1.00 | 3.70 | 0.00 |
| episode_geo | 1.00 | 0.31 | 0.00 |
| episode_equal | 1.00 | 0.17 | 0.00 |
| episode_front | 1.00 | 0.35 | 0.00 |
| allonset_edetector | 1.00 | 0.24 | 0.00 |
| dal_restart | 0.85 | 1.72 | 0.00 |
| pacing_bernoulli | 0.94 | 7.76 | 0.00 |
| c1_hmm_cs | 0.85 | 0.41 | 0.00 |
| c2_rho0.75 | 0.76 | 0.30 | 0.00 |

Strongest baseline by cell count: dal_restart 5, no_switch 16, pacing_bernoulli 25, periodic_mean 18

### Secondary descriptive tables

**C2 rho sweep on evaluation seeds** (cost per round minus no_switch; rho* was chosen on development seeds only)

| scenario | c2_rho0.25 | c2_rho0.5 | c2_rho0.75 |
|---|---|---|---|
| persistent_std | +0.0004 | -0.0006 | -0.0023 |
| fast_std | +0.0004 | +0.0008 | +0.0013 |
| persistent_weak | +0.0004 | +0.0009 | +0.0013 |
| null_boundary | +0.0004 | +0.0009 | +0.0013 |
| null_harm | +0.0004 | +0.0009 | +0.0013 |
| late_onset | -0.0057 | -0.0216 | -0.0522 |
| reversal | -0.0048 | -0.0214 | -0.0347 |
| offgrid_hmm | +0.0004 | +0.0009 | +0.0008 |

**Candidates vs the best episode-composition baseline per cell** (the separable-composition null of the C2 candidate note; negative = candidate cheaper)

| scenario | C1 diff/round | C1 better/worse/ns | c2_rho0.75 diff/round | C2 better/worse/ns |
|---|---|---|---|---|
| persistent_std | +0.0063 | 0/1/7 | +0.0063 | 2/1/5 |
| fast_std | -0.0011 | 2/0/6 | -0.0004 | 8/0/0 |
| persistent_weak | +0.0009 | 1/0/7 | +0.0000 | 6/0/2 |
| null_boundary | -0.0001 | 1/0/7 | -0.0004 | 6/0/2 |
| null_harm | -0.0006 | 6/0/2 | -0.0004 | 8/0/0 |
| late_onset | +0.0810 | 0/6/2 | +0.0438 | 2/6/0 |
| reversal | +0.0506 | 1/4/3 | +0.0143 | 2/3/3 |
| offgrid_hmm | -0.0023 | 2/0/6 | +0.0003 | 3/0/5 |

**Fraction of the evaluator-only clairvoyant gain captured** (1 = matches a zero-query follower of the true better regime; negative = worse than never switching; scenarios where the clairvoyant gain is below 1% of T per round are omitted)

| scenario | episode_front | episode_geo | periodic_mean | dal_restart | pacing_bernoulli | c1_hmm_cs | c2_rho0.75 |
|---|---|---|---|---|---|---|---|
| persistent_std | 0.02 | 0.01 | 0.15 | 0.10 | 0.19 | 0.01 | 0.01 |
| fast_std | -0.01 | -0.01 | -0.00 | -0.01 | 0.02 | -0.00 | -0.00 |
| persistent_weak | -0.01 | -0.01 | 0.02 | 0.01 | 0.05 | -0.01 | -0.01 |
| late_onset | 0.30 | 0.27 | 0.71 | 0.66 | 0.52 | 0.05 | 0.16 |
| reversal | 0.17 | 0.16 | 0.40 | 0.23 | 0.36 | -0.01 | 0.13 |
| offgrid_hmm | -0.00 | -0.00 | 0.09 | 0.03 | 0.11 | 0.01 | -0.00 |

## 2. Tiny oracle cells (reference only, R1)

**T=6, B=3, d=1** (5000 paired seeds). Oracle (HiGHS, numerical, risk 0.100 <= alpha 0.1): cost 2.8582; never switching: 3.0000.

| method | MC cost [95% CI] | gap to oracle | queries | switches | null promotion freq (iid 1/2) |
|---|---|---|---|---|---|
| no_switch | 2.9936 [2.9429,3.0443] | +0.1354 | 0.00 | 0.00 | 0.000 [0.000,0.001] |
| periodic_mean | 2.5451 [2.5039,2.5862] | -0.3131 | 3.00 | 0.69 | 0.496 [0.482,0.509] |
| episode_geo | 3.0236 [2.9729,3.0743] | +0.1654 | 3.00 | 0.00 | 0.000 [0.000,0.001] |
| episode_equal | 3.0236 [2.9729,3.0743] | +0.1654 | 3.00 | 0.00 | 0.000 [0.000,0.001] |
| episode_front | 3.0236 [2.9729,3.0743] | +0.1654 | 3.00 | 0.00 | 0.000 [0.000,0.001] |
| allonset_edetector | 3.0236 [2.9729,3.0743] | +0.1654 | 3.00 | 0.00 | 0.000 [0.000,0.001] |
| dal_restart | 2.6336 [2.5876,2.6796] | -0.2246 | 3.00 | 0.50 | 0.490 [0.476,0.504] |
| pacing_bernoulli | 2.6677 [2.6222,2.7133] | -0.1905 | 2.27 | 0.48 | 0.471 [0.458,0.485] |
| c1_hmm_cs | 3.0236 [2.9729,3.0743] | +0.1654 | 3.00 | 0.00 | 0.000 [0.000,0.001] |
| c2_rho0.25 | 2.9936 [2.9429,3.0443] | +0.1354 | 0.00 | 0.00 | 0.000 [0.000,0.001] |
| c2_rho0.5 | 3.0036 [2.9529,3.0543] | +0.1454 | 1.00 | 0.00 | 0.000 [0.000,0.001] |
| c2_rho0.75 | 3.0136 [2.9629,3.0643] | +0.1554 | 2.00 | 0.00 | 0.000 [0.000,0.001] |

**T=6, B=3, d=2** (5000 paired seeds). Oracle (HiGHS, numerical, risk 0.100 <= alpha 0.1): cost 2.9557; never switching: 3.0000.

| method | MC cost [95% CI] | gap to oracle | queries | switches | null promotion freq (iid 1/2) |
|---|---|---|---|---|---|
| no_switch | 2.9936 [2.9429,3.0443] | +0.0379 | 0.00 | 0.00 | 0.000 [0.000,0.001] |
| periodic_mean | 2.8794 [2.8337,2.9252] | -0.0763 | 3.00 | 0.50 | 0.496 [0.482,0.509] |
| episode_geo | 3.0236 [2.9729,3.0743] | +0.0679 | 3.00 | 0.00 | 0.000 [0.000,0.001] |
| episode_equal | 3.0236 [2.9729,3.0743] | +0.0679 | 3.00 | 0.00 | 0.000 [0.000,0.001] |
| episode_front | 3.0236 [2.9729,3.0743] | +0.0679 | 3.00 | 0.00 | 0.000 [0.000,0.001] |
| allonset_edetector | 3.0236 [2.9729,3.0743] | +0.0679 | 3.00 | 0.00 | 0.000 [0.000,0.001] |
| dal_restart | 2.8728 [2.8267,2.9188] | -0.0829 | 3.00 | 0.50 | 0.490 [0.476,0.504] |
| pacing_bernoulli | 2.8911 [2.8445,2.9378] | -0.0646 | 1.94 | 0.46 | 0.456 [0.443,0.470] |
| c1_hmm_cs | 3.0236 [2.9729,3.0743] | +0.0679 | 3.00 | 0.00 | 0.000 [0.000,0.001] |
| c2_rho0.25 | 2.9936 [2.9429,3.0443] | +0.0379 | 0.00 | 0.00 | 0.000 [0.000,0.001] |
| c2_rho0.5 | 3.0036 [2.9529,3.0543] | +0.0479 | 1.00 | 0.00 | 0.000 [0.000,0.001] |
| c2_rho0.75 | 3.0136 [2.9629,3.0643] | +0.0579 | 2.00 | 0.00 | 0.000 [0.000,0.001] |

**T=7, B=3, d=2** (5000 paired seeds). Oracle (HiGHS, numerical, risk 0.100 <= alpha 0.1): cost 3.4461; never switching: 3.5000.

| method | MC cost [95% CI] | gap to oracle | queries | switches | null promotion freq (iid 1/2) |
|---|---|---|---|---|---|
| no_switch | 3.5156 [3.4589,3.5723] | +0.0695 | 0.00 | 0.00 | 0.000 [0.000,0.001] |
| periodic_mean | 3.3368 [3.2871,3.3865] | -0.1093 | 3.00 | 0.80 | 0.615 [0.601,0.628] |
| episode_geo | 3.5456 [3.4889,3.6023] | +0.0995 | 3.00 | 0.00 | 0.000 [0.000,0.001] |
| episode_equal | 3.5456 [3.4889,3.6023] | +0.0995 | 3.00 | 0.00 | 0.000 [0.000,0.001] |
| episode_front | 3.5456 [3.4889,3.6023] | +0.0995 | 3.00 | 0.00 | 0.000 [0.000,0.001] |
| allonset_edetector | 3.5456 [3.4889,3.6023] | +0.0995 | 3.00 | 0.00 | 0.000 [0.000,0.001] |
| dal_restart | 3.3600 [3.3084,3.4116] | -0.0861 | 3.00 | 0.50 | 0.498 [0.484,0.512] |
| pacing_bernoulli | 3.3505 [3.2989,3.4022] | -0.0955 | 2.02 | 0.47 | 0.468 [0.454,0.481] |
| c1_hmm_cs | 3.5456 [3.4889,3.6023] | +0.0995 | 3.00 | 0.00 | 0.000 [0.000,0.001] |
| c2_rho0.25 | 3.5156 [3.4589,3.5723] | +0.0695 | 0.00 | 0.00 | 0.000 [0.000,0.001] |
| c2_rho0.5 | 3.5256 [3.4689,3.5823] | +0.0795 | 1.00 | 0.00 | 0.000 [0.000,0.001] |
| c2_rho0.75 | 3.5356 [3.4789,3.5923] | +0.0895 | 2.00 | 0.00 | 0.000 [0.000,0.001] |

**T=8, B=4, d=2** (5000 paired seeds). Oracle (HiGHS, numerical, risk 0.100 <= alpha 0.1): cost 3.9287; never switching: 4.0000.

| method | MC cost [95% CI] | gap to oracle | queries | switches | null promotion freq (iid 1/2) |
|---|---|---|---|---|---|
| no_switch | 4.0166 [3.9564,4.0768] | +0.0879 | 0.00 | 0.00 | 0.000 [0.000,0.001] |
| periodic_mean | 3.8569 [3.8022,3.9116] | -0.0718 | 4.00 | 0.67 | 0.620 [0.606,0.633] |
| episode_geo | 4.0566 [3.9964,4.1168] | +0.1279 | 4.00 | 0.00 | 0.000 [0.000,0.001] |
| episode_equal | 4.0566 [3.9964,4.1168] | +0.1279 | 4.00 | 0.00 | 0.000 [0.000,0.001] |
| episode_front | 4.0566 [3.9964,4.1168] | +0.1279 | 4.00 | 0.00 | 0.000 [0.000,0.001] |
| allonset_edetector | 4.0566 [3.9964,4.1168] | +0.1279 | 4.00 | 0.00 | 0.000 [0.000,0.001] |
| dal_restart | 3.9403 [3.8834,3.9971] | +0.0115 | 4.00 | 0.37 | 0.256 [0.244,0.269] |
| pacing_bernoulli | 3.8976 [3.8412,3.9539] | -0.0312 | 2.88 | 0.50 | 0.500 [0.486,0.514] |
| c1_hmm_cs | 4.0566 [3.9964,4.1168] | +0.1279 | 4.00 | 0.00 | 0.000 [0.000,0.001] |
| c2_rho0.25 | 4.0266 [3.9664,4.0868] | +0.0979 | 1.00 | 0.00 | 0.000 [0.000,0.001] |
| c2_rho0.5 | 4.0366 [3.9764,4.0968] | +0.1079 | 2.00 | 0.00 | 0.000 [0.000,0.001] |
| c2_rho0.75 | 4.0466 [3.9864,4.1068] | +0.1179 | 3.00 | 0.00 | 0.000 [0.000,0.001] |

## 3. Real development windows (imposed timing and costs)

Only realized net cost, queries and switches are reported (no oracle). Intervals are moving-block bootstrap (block 50, 500 resamples) on the per-round cost difference to the strongest baseline in that setting. Costs are imposed, not observed.

**elec2**: T=3000, replay mean loss f0/f1 = 0.2993/0.3297; HMM fit {m0 +0.017, m1 +0.017, sigma 0.160, a 0.050, b 0.050}; bank 216 models.

| setting | no_switch | always_f1 | best baseline | C1 | C1 - best [block-boot 95%] | C2 | C2 - best [block-boot 95%] |
|---|---|---|---|---|---|---|---|
| d=1 B=300 c=0.005 s=0.05 | 898.0 | 989.0 | no_switch 898.0 | 898.4 (q74/s0) | +0.4 [+0.3,+0.4] | 899.1 (q225/s0) | +1.1 [+1.1,+1.2] |
| d=1 B=300 c=0.02 s=0.2 | 898.0 | 989.2 | no_switch 898.0 | 899.5 (q74/s0) | +1.5 [+1.4,+1.6] | 902.5 (q225/s0) | +4.5 [+4.4,+4.6] |
| d=1 B=750 c=0.005 s=0.05 | 898.0 | 989.0 | pacing_bernoulli 885.0 | 898.9 (q187/s0) | +13.9 [-2.2,+35.4] | 900.8 (q562/s0) | +15.8 [-0.4,+37.2] |
| d=1 B=750 c=0.02 s=0.2 | 898.0 | 989.2 | pacing_bernoulli 897.2 | 901.7 (q187/s0) | +4.5 [-11.8,+25.9] | 909.2 (q562/s0) | +12.0 [-4.2,+33.4] |
| d=10 B=300 c=0.005 s=0.05 | 898.0 | 989.0 | no_switch 898.0 | 898.4 (q74/s0) | +0.4 [+0.3,+0.4] | 899.1 (q225/s0) | +1.1 [+1.1,+1.2] |
| d=10 B=300 c=0.02 s=0.2 | 898.0 | 989.2 | no_switch 898.0 | 899.5 (q74/s0) | +1.5 [+1.4,+1.6] | 902.5 (q225/s0) | +4.5 [+4.4,+4.6] |
| d=10 B=750 c=0.005 s=0.05 | 898.0 | 989.0 | pacing_bernoulli 892.0 | 898.9 (q186/s0) | +6.9 [-8.3,+26.6] | 900.8 (q562/s0) | +8.8 [-6.4,+28.5] |
| d=10 B=750 c=0.02 s=0.2 | 898.0 | 989.2 | no_switch 898.0 | 901.7 (q186/s0) | +3.7 [+3.7,+3.9] | 909.2 (q562/s0) | +11.2 [+11.1,+11.4] |

**eia_nyis**: T=3000, replay mean loss f0/f1 = 0.2228/0.1227; HMM fit {m0 +0.292, m1 -0.090, sigma 0.187, a 0.194, b 0.028}; bank 216 models.

| setting | no_switch | always_f1 | best baseline | C1 | C1 - best [block-boot 95%] | C2 | C2 - best [block-boot 95%] |
|---|---|---|---|---|---|---|---|
| d=1 B=300 c=0.005 s=0.05 | 668.3 | 368.0 | pacing_bernoulli 368.9 | 443.7 (q140/s5) | +74.7 [+27.4,+128.1] | 538.7 (q289/s2) | +169.7 [+112.7,+233.2] |
| d=1 B=300 c=0.02 s=0.2 | 668.3 | 368.2 | pacing_bernoulli 373.7 | 446.5 (q140/s5) | +72.8 [+25.5,+126.7] | 543.3 (q289/s2) | +169.6 [+112.7,+233.4] |
| d=1 B=750 c=0.005 s=0.05 | 668.3 | 368.0 | pacing_bernoulli 358.8 | 419.9 (q233/s5) | +61.1 [+18.3,+104.1] | 439.5 (q690/s2) | +80.7 [+39.2,+126.0] |
| d=1 B=750 c=0.02 s=0.2 | 668.3 | 368.2 | pacing_bernoulli 372.9 | 424.1 (q233/s5) | +51.2 [+7.4,+96.1] | 450.1 (q690/s2) | +77.3 [+35.0,+121.8] |
| d=10 B=300 c=0.005 s=0.05 | 668.3 | 368.0 | pacing_bernoulli 372.2 | 439.8 (q129/s1) | +67.6 [+24.5,+121.4] | 526.1 (q201/s2) | +153.9 [+95.2,+220.4] |
| d=10 B=300 c=0.02 s=0.2 | 668.3 | 368.2 | pacing_bernoulli 376.9 | 441.9 (q129/s1) | +65.0 [+21.9,+119.5] | 529.4 (q201/s2) | +152.5 [+93.7,+219.5] |
| d=10 B=750 c=0.005 s=0.05 | 668.3 | 368.0 | pacing_bernoulli 376.6 | 442.8 (q226/s1) | +66.2 [+19.9,+121.1] | 426.9 (q705/s2) | +50.3 [+1.2,+101.2] |
| d=10 B=750 c=0.02 s=0.2 | 668.3 | 368.2 | pacing_bernoulli 390.7 | 446.3 (q226/s1) | +55.6 [+8.6,+110.5] | 437.8 (q705/s2) | +47.1 [-2.4,+98.1] |

**crsp_subset**: T=2516, replay mean loss f0/f1 = 0.0522/0.0526; HMM fit {m0 +0.000, m1 -0.006, sigma 0.026, a 0.151, b 0.353}; bank 216 models.

| setting | no_switch | always_f1 | best baseline | C1 | C1 - best [block-boot 95%] | C2 | C2 - best [block-boot 95%] |
|---|---|---|---|---|---|---|---|
| d=1 B=252 c=0.005 s=0.05 | 131.5 | 132.4 | no_switch 131.5 | 132.7 (q252/s0) | +1.3 [+0.8,+1.5] | 132.4 (q189/s0) | +0.9 [+0.9,+1.0] |
| d=1 B=252 c=0.02 s=0.2 | 131.5 | 132.5 | no_switch 131.5 | 136.5 (q252/s0) | +5.0 [+3.3,+6.1] | 135.2 (q189/s0) | +3.8 [+3.7,+3.9] |
| d=1 B=629 c=0.005 s=0.05 | 131.5 | 132.4 | no_switch 131.5 | 134.6 (q629/s0) | +3.1 [+2.1,+4.0] | 133.8 (q471/s0) | +2.4 [+2.3,+2.4] |
| d=1 B=629 c=0.02 s=0.2 | 131.5 | 132.5 | no_switch 131.5 | 144.0 (q629/s0) | +12.6 [+8.6,+16.2] | 140.9 (q471/s0) | +9.4 [+9.3,+9.6] |
| d=10 B=252 c=0.005 s=0.05 | 131.5 | 132.4 | no_switch 131.5 | 132.7 (q252/s0) | +1.3 [+0.9,+1.6] | 132.4 (q189/s0) | +0.9 [+0.9,+1.0] |
| d=10 B=252 c=0.02 s=0.2 | 131.5 | 132.5 | no_switch 131.5 | 136.5 (q252/s0) | +5.0 [+3.6,+6.4] | 135.2 (q189/s0) | +3.8 [+3.7,+3.9] |
| d=10 B=629 c=0.005 s=0.05 | 131.5 | 132.4 | no_switch 131.5 | 134.0 (q502/s0) | +2.5 [+2.5,+2.5] | 133.8 (q471/s0) | +2.4 [+2.3,+2.4] |
| d=10 B=629 c=0.02 s=0.2 | 131.5 | 132.5 | no_switch 131.5 | 141.5 (q502/s0) | +10.0 [+10.0,+10.1] | 140.9 (q471/s0) | +9.4 [+9.3,+9.6] |

Across the 24 real rows (3 streams x 8 settings), the point difference of C1 and of C2 to the best baseline is positive in every row. The block-bootstrap interval excludes zero on the positive side in 21 of 24 rows for C1 and 20 of 24 for C2.

## Interpretation (exploratory)

* Neither C1 nor C2 shows signal against the strongest matched baseline. Pooled over the 64 synthetic cells the mean per-round difference is +0.0702 for C1 and +0.0613 for C2 (primary), with 0 cells better and 51 and 50 cells worse. Against the safety-gated baselines the pooled differences are smaller (+0.0193 and +0.0104) but still 0 of 64 cells better for C2 and 1 of 64 for C1. Real rows are positive in all 24 cases.
* Largest losses are on `late_onset` and `reversal`. Primary differences are +0.2286 (C1) and +0.1914 (C2) on `late_onset`, and +0.1510 and +0.1148 on `reversal`. Against the safety-gated set the gaps shrink to +0.0885 / +0.0514 and +0.0513 / +0.0151. Against the best episode-composition baseline they are +0.0810 / +0.0438 and +0.0506 / +0.0143. In both scripted cells C1 captures 0.05 and -0.01 of the clairvoyant gain, and C2 captures 0.16 and 0.13. The summary does not separate promotion delay from gate conservatism, so this is a description, not a diagnosis. The C1 pattern is consistent with under-promotion.
* Non-gated baselines reach lower cost than the gated methods, but they do so by violating the null. Mean cost minus `no_switch` on `late_onset`: `periodic_mean` -0.2250, `dal_restart` -0.2107, `pacing_bernoulli` -0.1671, against C1 -0.0151 and C2 -0.0522. On `persistent_std`, `pacing_bernoulli` is -0.0770 against C1 and C2 at -0.0023. On the two null cells the three non-gated baselines are worse than `no_switch` (`null_boundary` +0.0050, +0.0059, +0.0036; `null_harm` +0.0352, +0.0349, +0.0362 for `periodic_mean`, `dal_restart`, `pacing_bernoulli`). Their regime-based false-promotion frequencies are high: on `null_boundary` 0.996 (`periodic_mean`), 0.867 (`dal_restart`), 0.921 (`pacing_bernoulli`); on `null_harm` 0.617, 0.246, 0.533. `no_switch` and the gated methods are 0.000 on `null_harm`. On `null_boundary` they are 0.000 for `no_switch`, `episode_geo`, `episode_equal` and C1; 0.004 for C2; 0.008 for `episode_front`; and 0.017 for `allonset_edetector`.
* Missing R6 baselines are a limitation. The Gong-Zhang, Qiu et al. and Ryabchenko et al. delayed wrappers and the online FWER comparator are not implemented, so the claim "against strong baselines" covers only the six adapted baselines in the protocol.
* Other limits: the best-baseline reference is post-hoc (conservative against C); `rho*` was selected on development seeds; the real-data costs and release delays are imposed; ELEC2 uses file row order, not a verified clock; CRSP is a retrospective stress test; the tiny-oracle comparison uses four cells. Tiny-cell results show the same trade-off. The methods with zero null promotion (`no_switch`, `episode_*`, `allonset_edetector`, C1, C2) all sit above the exact oracle cost. Every method below the oracle cost has a null promotion frequency between 0.456 (T=6, B=3, d=2, `pacing_bernoulli`) and 0.620 (T=8, B=4, d=2, `periodic_mean`). This is on the iid causal-null boundary, not on the protocol's regime-based flag.

## 4. Assessment

**STOP C1 and C2 in their current form.** Neither shows signal against the strongest matched baseline, and their largest losses are on `late_onset` and `reversal`. This is an exploratory finding on this harness, not a theorem or an efficacy claim. Their failure on `late_onset` and `reversal` feeds Failure Atlas v1 (`docs/failure_atlas_v1_protocol.md`, being written now). No further C1 or C2 variant is registered from this run.

Not done here: no confirmatory run, no familywise error control, no R6 baselines beyond the six adapted ones, and no real-data claim beyond the imposed-timing development windows.
