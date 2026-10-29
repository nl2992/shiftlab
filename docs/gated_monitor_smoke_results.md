# WP1 smoke and throughput receipt

Observed 2026-10-27. This is an integrity and runtime check, excluded from inference.
The frozen five smoke seeds 58600000–58600004, `boundary_local_harm`, budget 0.2,
produced 205 rows (41 arms per seed) on the RTX 4060 Laptop GPU in 42.7062 seconds.
All recorded matched-arm expenditures obeyed their caps; no violations were found.
No smoke treatment outcomes were used to tune the protocol.

Command: `uv run --no-sync python scripts/run_gated_monitor_comparison.py --stage smoke --workers 1`.
Receipt: `outputs/gated_monitor_smoke/manifest.json`; streams SHA-256
`63047e4948a88631f490fec420610c786d09e25b21c70aa685a924f12fb85560`;
decision SHA-256 `5c4b27983b2a9dc5b85116d1ba7de3e11f5c1a9b988e96075cc399bf47c6dc9a`.

A performance-only spawned five-worker benchmark reused exactly these seeds twice,
with OMP, MKL, OpenBLAS, and NumExpr thread limits all 1. Cold/warm batches took
14.6641/8.3880 seconds; each produced 205 rows with zero cap violations.
Warm throughput projects 26,841.75 seconds (7.46 hours) for 16,000 calibration tasks
and 2,684.18 seconds (44.74 minutes) for 1,600 comparison tasks. These are estimates,
not completed runs. Script and machine/source receipt are preserved in ignored
`tmp/benchmark_gated_parallel.py` and `tmp/gated_parallel_benchmark.json`.
The latter records starting HEAD `d55ba721ee980d6dfcb6e16ceabf61cf51313c32`.

Validation before this result commit: full pinned suite 1,750 passed, 1 skipped
in 665.55 seconds (`tmp/phase_s1_results_full.log`). Calibration may proceed under
the frozen protocol after recording starting provenance for the long run.
