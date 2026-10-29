# Stratified monitor phase execution record

The scope and stopping rules are in [the phase goal](agent_goal_stratified_monitor_phase.md).
Initial HEAD: `42709d70840e2e72ac8abea27bac9eb4108ef797`. No confirmation seeds are authorised.

## WP0 initial verification, 2026-10-27

At `2026-10-27T08:05:26.199770+00:00`, the existing EIA snapshot was on disk:
`data/raw/eia/EBA.zip`, 697,661,852 bytes, filesystem modification timestamp
`2026-10-20T01:32:48.624972+00:00`. Its recomputed SHA-256 is
`3a6143c4bd853c3d6a9d9d3bb3ca7f1603a641835e9c7a050e5c8a927101936f`, matching
`data/reports/eia_2026_holdout_readiness.json`. The receipt retrieval timestamp is
`2026-10-20T01:32:49.393495+00:00`. Filesystem modification time is not publication time.
All of this snapshot is development data. This observation timestamp is not an arm freeze;
each prospective clock still requires frozen code, policies, costs, threshold, and strata.

The four ADG output files match their existing manifest hashes; both implementation source
hashes match. The protocol hash differs, as the existing results document discloses: its
status and sanity-check correction were added after the run. There is no recoverable
committed pre-run protocol in this checkout; do not retroactively describe G1 as commit-frozen.
Retain the historic exploratory negative result and its provenance limitation.

Checks: `uv run --no-sync pytest tests/test_adg_growth_prescreen.py -q`: 17 passed;
targeted Ruff passed; configured mypy passed. The initial full suite passed:
1,593 passed, 1 skipped in 679.47 seconds (`uv run --no-sync pytest -q`).
New WP1/panel files written during that background run were not in its initial collection;
they require their own focused checks and a later complete S0 suite.

## Requested tools

Read and apply [Ponytail's source skill](https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail/SKILL.md)
directly this session: reuse repository components and keep changes limited to the phase.
No global hooks or settings were installed.

[PaperBanana's author repository](https://github.com/dwzhu-pku/PaperBanana) documents source
execution and model API configuration; it also identifies
[llmsresearch/paperbanana](https://github.com/llmsresearch/paperbanana) as a community
implementation. At the observation timestamp, `paperbanana` is not importable in the pinned
environment and none of `GOOGLE_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, or
`OPENAI_API_KEY` is set in the process environment. This does not audit other credential
stores. No dependency changes, reference-dataset downloads, or external generation calls were
made. Figures require a working PaperBanana configuration and source-value verification.
Tabular research work can proceed without generating a figure.

## Pre-freeze validity audit

A scoped independent read found that WP1's iid control generator supports the required
history-conditional null even when finite-path oracle averages exceed epsilon. The comparison
protocol now explains the bridge before freeze. The primary agent verified the generator's
nuisance-only changes, actions, and past-only pacing formula.

For WP4 stratified random-orientation checks, strata and their constant bounds must be invariant
to the current orientation coin, and each bound must cover both swapped action directions.
Conditioning on an orientation-dependent stratum can destroy the sign cancellation. This
constraint must be included in the new protocol before any such check.
