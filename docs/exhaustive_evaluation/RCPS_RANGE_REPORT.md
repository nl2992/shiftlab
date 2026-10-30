# Predictable range-bound follow-up

2026-10-30. Registered run completed; previous work was progress (component parity and live experiment). Goal remains active. This is development baseline validation, not an independent novelty confirmation.

## Correctness and fidelity

Fixed-beta predictor extrema are evaluated exactly at the three interpolation knots. Query lower bounds and CV lower bounds depend only on released history, before current covariates. Query-range mode uses the native conservative .001 slack; predictor mode additionally uses the CV minimum in xi_min=theta+(1/q_min−1)cv_min−1/q_min. Stake cap=.5/abs(xi_min). Issued bets and factors remain frozen until fixed-delay release.

On200 random predictor states, minimum/maximum and stake-cap errors against the author components are0; increment, FTL stake and factor errors are at most4.44e−16. This checks supplied fresh bounds at a fixed question, not the entire native loop/grid. The original factory does not pass its CV predictor into the martingale constructor: query-only tightening and query-plus-CV tightening are distinct here. Full native loop timing is not claimed reproduced.

Eight focused tests cover range extrema, factor lower bounds, release chronology, hidden-outcome invariance, hard caps, no-budget and long-horizon finite behavior. The default global mode exactly replays the retained late-case diagnostic. Prior executed-source snapshots remain unchanged.

## Registered comparison

15 nonredundant adaptations plus4 frozen references on8 cases ×128 paths=1024 shared synthetic streams, horizon2000, budget400, delay5. Four learned predictor/normalizer pairs cross3 cap modes;3 uniform controls complete the family. Uniform query-bound aliases were excluded. Fresh seeds202658000/202659000. Same query, switch and benefit costs as previous development studies. No winner selected for confirmation and no new≥500-combination count assigned to these baseline refinements.

Mean persistent total cost over four equal-weight cases:

| Predictor/normalization | Global cap | Query range cap | Query+CV range cap |
|---|---:|---:|---:|
| Raw risk/source | 361.627 | 361.627 | 353.373 |
| Raw risk/projected paper | 420.004 | 308.108 | 308.108 |
| Residual²/source | 361.554 | 361.554 | 353.331 |
| Residual²/projected paper | 420.004 | 408.640 | 405.290 |

Uniform controls cost353.371 (floor.05 global),288.955 (floor.2 global),287.412 (floor.2 plus CV range). References cost204.698 (Kelly),206.872 (tuned FTL),205.117 (CUSUM slack.05),200.713 (CUSUM slack.1).

Range conservatism explains part of the earlier poor result, particularly raw-risk/projected-paper. Removing it does not recover competitive utility. All12 adaptive-query variants still fail to promote in the late-benefit case. Their maximum observed null promotion rate is0/128 per cell, which cannot establish a5% safety claim across the family. Uniform tight controls have maximum null rate.0078125. No adaptation beats the strong references in the primary mean-cost comparison. This is a negative result for these declared variants, not for the full published active-RCPS method.

Source normalization still underspends; projected-paper variants still front-load the hard cap. The tighter uniform controls demonstrate another issue: learning a CV and using pooled FTL evidence does not by itself solve late evidence recovery. A next pacing/reset comparison must include equally equipped direct-gain FTL and classical controls. Pacing and resets are known ingredients, not a novelty claim.

Artifacts: learned_rcps_range_registration.json, learned_rcps_range_status.json, learned_rcps_range_results.json, rcps_range_component_parity.json;8 per-case NPZs in outputs/exhaustive_evaluation/learned_rcps_range. Command: python scripts/exhaustive_evaluation/compare_learned_rcps.py --profile range. Existing registration prevents overwrite. Reserved real windows remain closed; no raw data acquisition or remote jobs.
