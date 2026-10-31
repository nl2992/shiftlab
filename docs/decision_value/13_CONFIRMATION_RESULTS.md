# 13 Confirmation results (protocol `12`, v1; one shot)

Executed 2026-10-31. Nothing was re-run, re-selected or changed after execution. Outputs (gitignored):
`outputs/decision_value/confirmation/confirm_synthetic_20261031T025215Z/` and
`.../confirm_real_20261031T025239Z/`; registry entries flagged `stage: confirmation`, git commit
`ca84d30`, `dirty: false`; logs `outputs/decision_value/logs/confirm_{synthetic,real}.log`.

## Verdict

- **Part S: CF-S1 FAILED** (estimate 6.58 < mean MME 6.79, although the one-sided lower bound is 6.07 > 0).
  CF-S2 passed. CF-S3 (negative control) passed, so Part S is valid. By the pre-declared rule, with CF-S1
  failing the development wins are **not confirmed** and are not re-tested; "conditional value of monitoring"
  is **not** confirmed in this synthetic family (the effect is positive and nonzero, but below the
  1%-of-cost materiality bar on average).
- **Part R: FAILED (negative / uninformative).** On the primary pair no monitor of any kind alarmed in the
  reserved window, so every monitor system equals never-switch (E = 0.0 vs MME 7.3). Controls satisfied
  V <= MME. This does not contradict Part S (different settings).
- Continue/pivot/stop assessment: **pivot / stop the "monitors beat tuned simple policies" claim** for
  these regimes. The measured effect (about 1% of cost where bad states are rare and persistent, d = 0) has
  the sign seen in development but is at or below the materiality threshold, and the one real dynamic pair
  gave nothing. What survives is the narrower statement that any monitor advantage is tiny and conditional on
  short delay.

## Pre-execution freeze

- Pre-execution commit: **`ca84d302dd4e5c85cb56d0c3df4f8fae088fa0d3`** ("Freeze confirmation configs, script and
  hashes (pre-execution)"; parent `6f63da1`, protocol frozen).
- sha256 (manifest `docs/decision_value/manifests/confirmation_hashes.json`; it also covers the engine
  sources, `run_real_data.py`, `run_type2_tuning.py`, `audit_real_data.py`; the script refuses to run on any
  mismatch and on a second run of a part):
  - `12_CONFIRMATION_PROTOCOL.md` `4271e70e4509182124cb1378a046651d4ed071b6f7cba9aa9d72bd3dec6ba07f`
  - `10_REAL_DATA_DEV_RESULTS.md` `8785c17780d4920b9b190783aea660c7505e66f5484e5d795cf4d017bb759b7f`
  - `confirmation_selected_configs.json` `d421cd92166e3b5ec7ea04c54e65887bdcc2330093abb571df43198f71264b28`
  - `run_confirmation.py` `5752691040ed62410522f86b20308c1fe7fdd2f0af15311953098813a63420b7`
- Step 0 (development only, tuning seeds 300000+idx, n = 500): simple family re-tuned over 98 configs (never,
  always, calendar K x 8 margins, static W x 8 margins; margins {0, .01, .02, .05, .1, .15, .2, .3}).
  The extended grid changed the selected simple policy in 9 of 13 cells (e.g. calm:100:0.1 -> calm:100:0.15,
  `never` -> statm:200:0.2); monitor selection kept from `type2_asym_20261031T021545Z`. Per-cell monitor config,
  threshold, simple config and dev tuning costs are in `confirmation_selected_configs.json`.
- Dry runs before freezing (development seeds 600000+, n = 200; dev windows): Part S ran end to end; Part R
  reproduced the development replay (200 matched q = 1 rows, max |cost difference| 9e-13; primary dev cell
  E = 24.3, as in `10`), and the new reserved-window loaders, parametrised to the dev windows, reproduced the
  `run_real_data.py` loaders exactly (assertions in the script).

## Commands

```
export PYTHONPATH=$WT/src PYTHONIOENCODING=utf8
python scripts/decision_value/run_confirmation.py step0                     # development, then commit
python scripts/decision_value/run_confirmation.py synthetic --dry-run       # development seeds
python scripts/decision_value/run_confirmation.py real --dry-run [--pairs ... --compare-dev --n-cal 150 --n-masks 6 --n-boot 200]
python scripts/decision_value/run_confirmation.py write-hashes
python scripts/decision_value/run_confirmation.py synthetic                 # Part S, one shot (4 procs)
python scripts/decision_value/run_confirmation.py real                      # Part R, one shot (4 procs)
```
Runtime: Part S 19 s (13 cells x n = 2000, 10,000 bootstrap resamples); Part R 260 s (4 min 22 s wall).
Seeds: Part S `7_000_000 + 10_000*cell_index` (cell order as the `run_type2_tuning` asym suite), calibration
5,000,000 (thresholds loaded from the cache and asserted equal to the frozen values), bootstrap seeds
`20261031 + cell_index`; Part R calibration 5,100,000/5,200,000 (n_cal = 2000), eval masks 20261030,
bootstrap `[20261030, 900+pair, block]`.

## Part S

Estimand: diff = cost_exp(best simple) - cost_exp(monitor system), positive favours the monitor; per-cell
paired bootstrap over 2000 episodes, 10,000 resamples, cells independent seed blocks.

| endpoint | estimate | bound | rule | p (1-sided) | Holm p | result |
|---|---|---|---|---|---|---|
| CF-S1 (4 cells, d = 0, B in {400, 1000}) | 6.58 | one-sided 95% LB 6.07 | LB > 0 and estimate >= mean MME 6.79 | 0.0001 | 0.0002 | **FAIL** (estimate below MME by 0.21) |
| CF-S2 (mean over 6 (B, pi_b) of diff(d=0) - diff(d=50)) | 1.87 | one-sided 95% LB 1.35 | LB > 0 | 0.0001 | 0.0002 | **PASS** |
| CF-S3 (useless fallback; value vs never) | -0.05 | two-sided 95% CI [-0.07, -0.03] | upper <= MME 6.44 | - | - | **PASS** (Part S valid) |

CF-S2 per-pair erosion diff(d=0) - diff(d=50): B100/pi.1 0.08, B100/pi.25 6.83, B400/pi.1 3.84, B400/pi.25 0.47,
B1000/pi.1 -0.24, B1000/pi.25 0.26. The pooled erosion is driven by two pairs; the longest-bad-run pairs show
essentially none, so the "delay erosion" pass is not uniform.

### Secondary: per-cell diffs (reported, not primary; Holm across the 12 useful cells)

| cell | monitor system | simple | cost mon | cost simple | diff [95% CI] | MME | Holm p | captured mon / simple | N_s mon / simple | alpha |
|---|---|---|---|---|---|---|---|---|---|---|
| B100 pi.1 d0 | page_hinkley hold200 | statm:400:0.1 | 645.71 | 645.72 | 0.01 [-0.09, 0.12] | 6.46 | 0.927 | -0.00 / -0.00 | 0.04 / 0.00 | 0.01 |
| B100 pi.1 d50 | page_hinkley hold50 | never | 644.52 | 644.44 | -0.07 [-0.11, -0.04] | 6.44 | 0.001 | -0.00 / 0.00 | 0.03 / 0.00 | 0.01 |
| B100 pi.25 d0 | cusum reverse | calm:100:0.2 | 702.84 | 708.12 | 5.28 [4.10, 6.48] | 7.12 | 0.001 | 0.11 / 0.05 | 5.92 / 2.46 | 0.95 |
| B100 pi.25 d50 | sr_betting hold800 | statm:50:0.2 | 712.56 | 711.01 | -1.55 [-2.75, -0.37] | 7.12 | 0.019 | -0.01 / 0.01 | 1.75 / 0.61 | 0.2 |
| B400 pi.1 d0 | cusum hold400 | calm:400:0.2 | 637.81 | 645.72 | 7.91 [6.50, 9.34] | 6.45 | 0.001 | 0.18 / -0.01 | 1.27 / 0.09 | 0.2 |
| B400 pi.1 d50 | cusum hold400 | statm:200:0.2 | 639.59 | 643.66 | 4.07 [2.86, 5.32] | 6.44 | 0.001 | 0.11 / 0.01 | 1.20 / 0.01 | 0.2 |
| B400 pi.25 d0 | cusum reverse | calm:100:0.15 | 670.11 | 676.43 | 6.32 [5.22, 7.44] | 7.09 | 0.001 | 0.39 / 0.32 | 4.82 / 3.61 | 0.95 |
| B400 pi.25 d50 | cusum reverse | calm:100:0.15 | 678.37 | 684.22 | 5.85 [4.70, 7.02] | 7.14 | 0.001 | 0.33 / 0.28 | 3.35 / 3.74 | 0.8 |
| B1000 pi.1 d0 | cusum reverse | calm:400:0.1 | 629.17 | 633.85 | 4.68 [3.47, 5.90] | 6.48 | 0.001 | 0.41 / 0.31 | 0.71 / 0.41 | 0.2 |
| B1000 pi.1 d50 | cusum reverse | statm:50:0.2 | 629.75 | 634.67 | 4.92 [3.81, 6.05] | 6.43 | 0.001 | 0.32 / 0.20 | 0.36 / 0.28 | 0.05 |
| B1000 pi.25 d0 | cusum reverse | calm:100:0.15 | 651.95 | 659.35 | 7.40 [6.33, 8.49] | 7.14 | 0.001 | 0.56 / 0.49 | 2.83 / 3.15 | 0.8 |
| B1000 pi.25 d50 | cusum reverse | calm:200:0.1 | 658.19 | 665.34 | 7.14 [6.03, 8.27] | 7.13 | 0.001 | 0.50 / 0.44 | 1.74 / 1.79 | 0.5 |
| control (useless) | page_hinkley hold25 | never | 643.94 | 643.90 | -0.05 [-0.07, -0.03] | 6.44 | (control) | NA | 0.02 / 0.00 | 0.01 |

Reading: of the 12 useful cells the monitor system has CI above 0 in 9, CI below 0 in 2 (the B100 d50 cells,
where the simple policy is at least as good) and a tie in 1; 3 cells reach >= MME (B400/pi.1/d0, B1000/pi.25/d0,
and B1000/pi.25/d50 marginally at 7.14 vs 7.13) versus 6 in development, consistent with development selection
optimism. Reference costs (never, always, dynamic oracle, headroom) per cell are in `tables.md` of the run
directory; headroom captured by the monitor system is at most 0.56 (B1000/pi.25/d0), by the best simple policy
at most 0.49.

## Part R

Windows opened once, in one run: OPSD 2020-01-01..2020-09-30 (T = 274 daily steps; max utc read 2020-09-30
23:00), Monash 2014 (T = 365), Binance ETHUSDT 1h 2026-01-01..2026-09-30 (T = 6,551 bars; checksums validated).
OPSD ridge penalty equal to phase 1 (0.1; asserted). Monitors, controllers, scaling (validation windows),
thresholds (stationary block-bootstrap null, alpha = 0.05, per (d, q)), costs and delays as protocol items 1-10.

### Primary endpoint (OPSD TSO vs sliding; CUSUM + Hold(7), c_s = 5, d = 1, q = 1)

| quantity | value |
|---|---|
| never / calendar28 / always / static28 | 726.0 / 776.8 / 836.8 / 824.8 |
| CUSUM + Hold(7) | 726.0 (no alarm in the window, N_s = 0) |
| E = better of never, calendar28 minus CUSUM+Hold(7) | **0.0** |
| MME (1% of never) | 7.3 |
| percentile CI, block 7 d / block 28 d | [-11.3, 0.0] / [-18.0, 0.0] |
| dynamic oracle / headroom | 680.7 / 45.3 |
| result | **FAIL** (E <= MME, CI lower bound not > 0) |

None of the 5 monitors alarmed on this pair in the reserved window at any (d, q) tested, so all 20
monitor x controller cells and the sensitivity grid (c_s in {0, 1, 5, 20}, d in {1, 7}, q in {0.25, 1}) give
E = 0. The headroom itself was small (45.3, 6% of never). The block-bootstrap CI is degenerate at the upper end
(0.0) because most resamples also produce no alarm; it understates persistence by construction.

### Controls (max V vs never over 5 monitors x 4 controllers; c_s = 5, d = 1, q = 1; pass if <= MME)

| control | max V | MME | result |
|---|---|---|---|
| Monash 2014 frozen vs sliding | 0.0 | 14.0 | pass (CUSUM+Hold(7) lost 65.7 vs never through false switches; other monitors silent or negative) |
| Binance 2026-01..09 frozen vs sliding | 0.0 | 32.8 | pass (only PH alarmed, V = -6 to -13; headroom 123; at c_s = 0 max V = +1.0) |

**Part R pass rule: FAIL** (primary fails; controls pass).

### Secondary pairs and comparisons (c_s = 5, d = 1, q = 1)

E = best of {never, always, calendar28} minus CUSUM+Hold(7); block-7 bootstrap, Holm across the 4 non-primary
pairs (bootstrap p values are descriptive: the bootstrap understates persistence).

| pair | never / always / cal28 | CUSUM+Hold7 | E | Holm p |
|---|---|---|---|---|
| OPSD frozen vs TSO | 895.1 / 731.0 / 779.7 | 901.9 | -171.0 | 0.021 |
| OPSD frozen vs sliding | 895.1 / 836.8 / 884.9 | 918.5 | -81.7 | 0.003 |
| Monash frozen vs sliding | 1398.7 / 1424.6 / 1440.6 | 1464.3 | -65.7 | 0.006 |
| Binance frozen vs sliding | 3277.0 / 3302.0 / 3869.0 | 3277.0 | 0.0 | 1.000 |

On the two frozen-incumbent OPSD pairs the Permanent controllers (CUSUM, SR-betting, Kelly) beat never by
V = +19 to +26 (first alarms 2020-05-23 to 2020-06-14), but always-challenger is far better (the pairs are
static-dominated, as flagged in `10`); CUSUM+Hold(7) lost 6.8 and 23.4 vs never. Full 5 x 4 V tables,
first-alarm tables, sensitivity grids and the reversal classification (block-7 bootstrap, 2000 series: 0 of 20
ordered monitor pairs for the primary pair; 2 and 7 for OPSD frozen/sliding and Monash) are in `tables.md`;
per-cell data in `cells.csv.gz`.

## Deviations, interpretations and incidents

- **Interpretations made explicit in the script docstring before execution** (protocol text ambiguous): pass
  rule needs point estimate > MME and CI lower bound > 0 for both the 7 d and the 28 d block (Binance 168/672
  h); bootstrap = replay of the monitor on moving-block resamples (percentile CI); control rule = maximum V
  over the 20 paired cells <= MME; Holm over the 4 non-primary pairs; Part S Holm decision for CF-S1/S2
  required adjusted p < 0.05 in addition to the stated bound rules (all adjusted p = 0.0002); Binance frozen
  model = phase-1 model (fit 2025-01..06), refit-free. Under any alternative reading the primary endpoint is
  E = 0 and CF-S1's estimate 6.58 vs MME 6.79 is unchanged, so the verdicts do not depend on them.
- The hash manifest also covers `run_real_data.py`, `run_type2_tuning.py`, `audit_real_data.py` and the engine
  sources (stricter than the four files named in the protocol). Per-cell thresholds were asserted equal to the
  frozen values.
- Crashes: none during execution. Step 0 (development) crashed on a cp1252 print of a non-ASCII path after
  the JSON was written; fixed by `PYTHONIOENCODING=utf8` (no code change). Re-running `write-hashes` once after
  the commit only changed the manifest's `created_utc`; reverted with `git checkout`, hashes unchanged and
  re-verified.
- Dry runs wrote development registry entries (`dryrun_confirm_*`, stage development).
- Disclosed risks from the protocol stand: selection risk of the primary monitor/controller, the OPSD 2020
  spring disturbance, one series per pair, imposed delays and costs. Part R is case evidence only.
- Limitations: Part S uses oracle-tuned configs (knowledge of B, pi_b) and one seed block per cell; the simple
  family was re-tuned in Step 0 but still selects margin 0.2 in several cells (grid maximum 0.3).
