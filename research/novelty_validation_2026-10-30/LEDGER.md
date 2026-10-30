# Append-only programme ledger (novelty validation, 2026-10-30)

| step | commit / artifact | note |
|---|---|---|
| base | merge 28f8a2d of `origin/research/exhaustive-candidate-evaluation-2026-10-30` (a7c88d8) into `claude/sweet-lovelace-pznpjq` | no conflicts; `main` untouched; no force-push; dependence-gates/mandate-gap line **not** merged (sibling) |
| env | `uv sync --all-extras`; Python 3.13.17, numpy 2.5.4, scikit-learn 1.9.1, pandas 3.0.6, scipy 1.18.1 | |
| baseline tests | 1475 passed / 4 skipped (`--ignore=tests/data`); 899 passed / 4 skipped (`tests/data`) | before any change of mine |
| sources | arXiv PDFs: 2602.02229 `e35a336e…d912`, 2605.28533 `eaba4ba5…8332d912` (full hashes in 02), 2110.06177, 2203.03532 | local copies in scratchpad, not committed (licence/size) |
| 89dba6a | X1, X2 scripts + outputs; D2 script + frozen protocol 06 | **protocol committed before D2 ran** |
| D2 run 1 | `outputs/d2_gas_sensor_replay.json` | UCI zip SHA-256 `91e8f466f202e7a093d657673ce47311c3e90416f7df3057966058961c351fe4` |
| D2 re-run | identical JSON; script edited only to add `d2_gas_sensor_per_seed_alarm_idx.npz` | output-only change |
| D2 follow-ups | `d2_followup_paired_and_diagnostic.py`, `d2_wealth_at_onset_diagnostic.py` | **post-hoc, diagnostic only** |

Seeds. X1: worlds 100–105, sweeps 900–933 (S=2000 / 600 paths). X2: deterministic. D2: split seed 20261030; permutation seed 7; label-mask seeds 5000+1000·frac (stream A), 6000+1000·frac (stream B); 300 mask seeds per cell (rows of one `rng.random((S,T))` draw).

Reproduce: `uv sync --all-extras`, then
`.venv/bin/python research/novelty_validation_2026-10-30/scripts/x1_guidance_mechanism.py <q> <q>` for q in 1.0 0.2 0.1;
`…/x2_joint_vs_separate_dp.py`; `…/d2_gas_sensor_replay.py <gas.zip> research/novelty_validation_2026-10-30/outputs`;
the two follow-up scripts; `pytest research/novelty_validation_2026-10-30/tests`.
