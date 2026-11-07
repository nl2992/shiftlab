# Fixed-challenger control run status

- Protocol/script commit: `7b02420f`.
- Command: `uv run python scripts/sota_sprint/eia930/evaluate_static_f8_controls.py` (completed successfully).
- Reconstructed and verified all 11 BA F8 profiles; evaluated all 81 common 2,000-event episodes.
- Records: 162 rows (fixed incumbent and fixed challenger for each episode); CAMS comparator is the five-seed mean from the completed frozen panel.
- Analyzer: `uv run python research/scoped_method/pilots/eia930_f8_static_challenger_control_20261107/analyze.py`.
- Lint/syntax: `uv run ruff check scripts/sota_sprint/eia930/evaluate_static_f8_controls.py research/scoped_method/pilots/eia930_f8_static_challenger_control_20261107/analyze.py` and `uv run python -m py_compile scripts/sota_sprint/eia930/evaluate_static_f8_controls.py` (pass).
- Positive development diagnostic: fixed challenger net cost 26.37 vs CAMS 29.93; paired equal-BA saving 3.53, hierarchical 95% interval [1.98, 5.11] units saved; directional win in 11/11 BAs. It uses zero labels and charges one switch per episode.
- Critical limitation: the same 2022–2023 period both selected the 11 BAs using the F8 profile and supplied this comparison. This is post-selection development evidence, not independent confirmation or proof that the fixed-challenger choice can be made prospectively.
- No 2024+ outcomes were opened. All BAs come from one provider; feedback timing and monetary costs are simulated/hypothetical.
