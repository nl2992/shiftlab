# Twin v3 rebuild (2026-11-09)

Rebuilt the exchangeable-twin null loss arrays for splits 40..159 (T=2000 plus T=1000/4000 re-windowings) from the five UCI archives.

## Environment
- venv python (main checkout `.venv`): numpy 2.5.4, pandas 3.0.6, scikit-learn 1.9.1 (identical to the recorded versions).
- Raw archives copied into `data/raw/sprint_fresh/uci_{235,275,374,381,492}` (gitignored via `data/raw/`).
- `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=2`, 16 worker processes.

## Command (what was actually run)
`scripts/p2_benchmark/build_twin_v3.py` was NOT run as-is: it needs `--v2-stats data/sprint_twin_losses_v2/stats.json`, which is not in this worktree or the main checkout (v2 arrays/stats were never committed). It is also single-process and was estimated at many hours on this loaded machine. Instead a driver outside the repo (scratchpad `chunks.py`, `merge.py`) called the same `wp2_twins.build_splits(name, range(lo, lo+5))` in 16 parallel chunks (resumable, per-chunk npz in `data/sprint_twin_losses_v3/_chunks/`), concatenated the chunks in split order, and wrote the same `twin3_<ds>.npz` (`l0,l1,split,ep`) and `twin3_<ds>_T{1000,4000}.npz` via `wp2_twins.rewindow`. Chunking does not change arrays: `build_splits` seeds per (dataset, split) via `twin_null._seed`.
Instead of the v2 check, the v1 registry (splits 0..19) was rebuilt and checked against `data/sprint_twin_losses/stats.json`. No repo code was modified.

Runtime: ~65 min wall for 140 chunks (heavy contention from other jobs on the machine; a chunk took 5-20 min, versus about 8 s per appliances chunk on an idle machine).

## Output
`data/sprint_twin_losses_v3/` (120 MB, gitignored): `twin3_<ds>.npz`, `twin3_<ds>_T1000.npz`, `twin3_<ds>_T4000.npz`, `stats_rebuild.json`, `_chunks/` (intermediate).

## Verification against `docs/p2_benchmark/results/twin_v3_stats.json`
| dataset | episodes (rebuilt = recorded) | v1 splits 0-19 hash | v3 hash | T1000 / T4000 hash |
|---|---|---|---|---|
| metro | 1920 | match | match | match / match |
| beijing_pm25 | 1680 | match | match | match / match |
| bike_hour | 720 | match | match | match / match |
| household_power | 2400 | match | match | match / match |
| appliances | 720 | match | **MISMATCH** | mismatch / mismatch |

Appliances mismatch: rebuilt `49f3092e...` vs recorded `cb16332e...` (the recorded value was not edited). Err0, err1 and mean advantage agree with the recorded stats to all printed digits, but the rebuilt disagreement rate is 0.12880347 versus recorded 0.12880486, i.e. exactly one (l0, l1) cell out of 720,000 differs. So the rebuilt array is statistically the same stream with a single borderline prediction flipped. The v1 appliances registry (splits 0-19) does reproduce exactly. Most likely cause: nondeterminism in `HistGradientBoostingClassifier` floating-point accumulation (CPU/thread layout differs from the original build machine). Thread count is ruled out for 1 vs 2 OMP threads (24 appliances chunks identical); a 16-thread check did not finish. Not caused by library versions (they match).

Consequence: any confirmatory result computed on the rebuilt appliances v3 arrays will differ from the recorded run by at most one cell; hash-locked comparisons must either use the original archived arrays or note this deviation.

The v2 reproduction check in `build_twin_v3.py` was not performed (no v2 stats available).
