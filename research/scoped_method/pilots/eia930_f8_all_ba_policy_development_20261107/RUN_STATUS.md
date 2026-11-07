# EIA-930 F8 policy-run recovery record

- Frozen protocol commit: `3619144f` (`EIA F8 all-BA policy development comparison`).
- Executed code commit: `b3e8bfb27cadee8e0180df9051b916805f9ea74f`.
- Command: `uv run python scripts/sota_sprint/eia930/run_f8_all_ba_policy_development.py`.
- The command completed all 81 contiguous 2,000-event episodes, five matched policy seeds, and 16 methods, then exited nonzero during final manifest construction because it referenced nonexistent `scripts/sota_sprint/strong_hosts.py`. The runtime had imported the registered module from `scripts/failure_atlas_v2_flq/strong_hosts.py` and the policy experiments themselves completed.
- The 6,480 episode-policy rows were recovered from `episode_policy_records.jsonl`; checks confirm all 11 registered BAs, 81 episodes, all 16 methods, all five policy seeds, and exactly 16 rows per BA/episode/seed. Maximum absolute cost-identity residual is below `1.2e-14`.
- `run_manifest.json` was reconstructed from the immutable run commit and checksummed raw-file manifest. It records the finalization error; no outcomes were rerun or overwritten.
- Analyzer: `uv run python research/scoped_method/pilots/eia930_f8_all_ba_policy_development_20261107/analyze.py`.
- Analyzer and runner lint: `uv run ruff check research/scoped_method/pilots/eia930_f8_all_ba_policy_development_20261107/analyze.py scripts/sota_sprint/eia930/finalize_f8_all_ba_policy_development.py scripts/sota_sprint/eia930/run_f8_all_ba_policy_development.py` (pass).
- Outcome: candidate PFA-SR did not clear its frozen development gate. CAMS is the lowest-cost panel method; the full statistics and adverse comparisons are in `RESULTS.md` and `ANALYSIS.json`.
- Holdout status: no 2024+ rows were read.
