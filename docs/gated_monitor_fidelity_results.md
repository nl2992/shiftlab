# WP1 S1 historic fidelity replay

**S1: PASS, 2026-10-27.** The registered historic counts reproduce exactly:

| Uniform PPI support bound | Crossings on the same 60 paths |
|---|---:|
| Common 96.9 | 6/60 |
| Correct policy-specific 45.9 | 47/60 |

This is a replay of the same observed increments, not a fresh power study. It verifies the
bound correction and authorizes the disjoint smoke stage under the [frozen protocol](gated_vs_ungated_monitor_comparison_protocol.md).
It does not establish a gating gain or calibration result.

Command: `uv run --no-sync python scripts/run_gated_monitor_comparison.py --stage fidelity`.
CPU core runtime: 0.3551 seconds. HEAD: `0c45bf85152d122686204aef4063d5a4ba5e4b9c`.
The manifest records the two dirty documentation paths; research code was committed.

All 60 seed IDs were checked against 20373024–20373083. Query propensities equal 0.20.
The historic `ppi_increment` schema is verified by unit tests. The common-bound replay's full
log-wealth trajectories match the stored trajectories to absolute tolerance 1e-10. Replaying
those identical increments with bound 45.9 gives 47 crossings. No new stream or query coin was
generated, and no confirmation block was accessed.

Input trace SHA-256:
`ed2c2d71554434d6152e55cfe80b3caa33e89d338ae9f070d2917a58811f4965`.
The receipt itself is hashed in the [stage manifest](../outputs/gated_monitor_fidelity/manifest.json).
Output hashes:

- `streams.parquet`: `33b29c58002bae1c76e05dd21e2616ff76b4cb8cac7954dd01861a53a9638356`
- `decision.json`: `8728324433ab2a590d46663f3ba5401a469fa170b8a4864475a5f9e9fbe2e29f`

Before this results commit, the complete pinned suite passed: 1,750 passed, 1 skipped in
665.55 seconds; targeted Ruff and configured mypy also passed. Large inputs/outputs remain
where the repository's ignore rules place them. No figure was generated.

**Assessment: continue to the five-seed CUDA smoke, record runtime, and project full-run
cost before launching calibration/comparison.** The empirical gating decision remains pending.
