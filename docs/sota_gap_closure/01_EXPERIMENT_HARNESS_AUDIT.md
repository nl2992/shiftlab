# 01 Experiment harness audit

Earlier harness (`sota_search.harness`, `run_*.py`): aggregates only (per-config means in SQLite `secondary_metrics`), uniform Bernoulli labels with an expected budget, fixed delay shift, label mask from `lseed` shared across detectors (partial pairing), no hard budget, no peak-memory or runtime profile (runtime recorded per (config, world) batch), empirical-threshold detectors calibrated on one 400-seed null stream.

## Gaps found
1. **No per-seed records** - a per-seed alarm time, harm-before-alarm or label count could not be recovered. Fixed: `src/shiftlab/gap/store.py` stores one row per (world, config, seed): first alarm, false-alarm / detection indicators, delay, harm before alarm, queried labels, label arrival statistics (mean delay, last arrival, mean / max pending queue), hard-budget exhaustion time, batch runtime (and per-seed share), process peak RSS. Aggregates are derived by `store.summarise`; nothing from the earlier registries is overwritten (`outputs/sota_search` untouched).
2. **Pairing** - arms in the new harness share worlds, seeds and the query uniform matrix (`qseed`); arms with equal `q_t` query identical events (`test_seed_reproducibility_and_common_random_numbers`). Allocation arms keep compatible query randomness (monotone coupling `Q = U < q_t`).
3. **Registry** - `outputs/gap_closure/registry.sqlite` (append-only; config hash, config JSON, number of worlds, seeds, seed block, commit SHA, wall time, note). Per-seed parquet files live next to it. `.gitignore` now whitelists `outputs/gap_closure/` and `outputs/sota_search/` (the previous phase lost its G2 held-out summary and registry because `outputs/*` was ignored; see `00_MANDATE_COMPLETION_MATRIX.md`).
4. **Limitation** - seeds are vectorised, so runtime and memory are batch-level quantities (per-seed runtime = batch / S; peak RSS = process high-water mark). `RUNTIME_SCALING.csv` / `MEMORY_SCALING.csv` use dedicated clean measurements.

## Parity with the earlier implementation
`Cfg(cap_mode="x", release="legacy", unq_delay=True)` reproduces legacy `pprm_tight` and HG log-wealth to float32 precision (max |diff| 4.8e-7, identical alarms; `tests/gap/test_engine.py::test_legacy_parity_pprm_tight_and_hg`).

## Test inventory (`tests/gap`, 18 tests)
legacy parity; exact finite-support cap; hard budget (pathwise `labels <= B` for six pacing rules, forced exhaustion, wealth frozen after exhaustion); causality (perturbing future events does not change the past; a label's value cannot influence wealth before `t + delay`); seed reproducibility / CRN; parent-modified identities (`rel=hard,fallback=none`, `mix=(1,0,0)`, `gamma=1, gate=None` equal the parent); prefix = arrived under fixed delay; generator tests (`GENERATOR_VALIDATION_TESTS.md`).
