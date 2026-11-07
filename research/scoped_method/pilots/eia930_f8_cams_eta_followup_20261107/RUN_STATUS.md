# CAMS eta-scale follow-up run status

- Frozen protocol and runner commit: `356f0248`.
- Command: `uv run python scripts/sota_sprint/eia930/run_f8_cams_eta_followup.py` (completed successfully).
- Runner reconstructed the same 11 BA profiles, confirmed the committed eligible row counts, disagreement rates, and conditional accuracies before outcomes.
- Outcomes: 2,025 episode-policy rows; 81 contiguous episodes; five paired policy seeds; five methods (`cams_adapter`, `cams_max_adapter`, and the three fixed eta scales).
- Cost accounting residual: below `1.5e-14`.
- Analyzer: `uv run python research/scoped_method/pilots/eia930_f8_cams_eta_followup_20261107/analyze.py`.
- Lint and syntax checks: `uv run ruff check scripts/sota_sprint/eia930/scaled_cams.py scripts/sota_sprint/eia930/run_f8_cams_eta_followup.py research/scoped_method/pilots/eia930_f8_cams_eta_followup_20261107/analyze.py` and `uv run python -m py_compile scripts/sota_sprint/eia930/scaled_cams.py scripts/sota_sprint/eia930/run_f8_cams_eta_followup.py` (pass).
- Result: no eta scale passed the frozen practical gate; eta=3 improved equal-BA mean cost by 0.24 but had a hierarchical 95% interval spanning zero and only 5/11 directional BA wins. See `RESULTS.md` and `ANALYSIS.json`.
- 2024+ holdout remains unopened.
