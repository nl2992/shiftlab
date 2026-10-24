# Prespecified start-time mixture: development results

This CUDA-requested development grid uses 30 paired seeds per cell, a fixed $720 label-dollar cap, identical query labels for all eventwise monitors, and horizons 1000, 1800, 2600. It compares a four-start equal e-process mixture with the full-stream fixed mixture, predictable-variance e-process, and PM-EB.

The starts are fixed as `{0, H/4, H/2, 3H/4}` (integer floors, duplicate positions removed). A convex mixture of valid e-processes is an established construction; this benchmark does not claim novelty. The 30-stream null controls are too small to establish the target false-escalation rate.

## Harm detection

| Cell | Horizon | Monitor | Detections / harm streams | Onsets reached | Mean delay | False escalations / controls | Mean labels | Mean spend |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| benign_nuisance | 1000 | fixed_mixture | 0/0 | 0 | nan | 0/30 | 197.8 | $297.26 |
| benign_nuisance | 1000 | pm_eb | 0/0 | 0 | nan | 0/30 | 197.8 | $297.26 |
| benign_nuisance | 1000 | predictable_variance | 0/0 | 0 | nan | 0/30 | 197.8 | $297.26 |
| benign_nuisance | 1000 | started_mixture | 0/0 | 0 | nan | 0/30 | 197.8 | $297.26 |
| benign_nuisance | 1800 | fixed_mixture | 0/0 | 0 | nan | 0/30 | 355.5 | $669.83 |
| benign_nuisance | 1800 | pm_eb | 0/0 | 0 | nan | 0/30 | 355.5 | $669.83 |
| benign_nuisance | 1800 | predictable_variance | 0/0 | 0 | nan | 0/30 | 355.5 | $669.83 |
| benign_nuisance | 1800 | started_mixture | 0/0 | 0 | nan | 0/30 | 355.5 | $669.83 |
| benign_nuisance | 2600 | fixed_mixture | 0/0 | 0 | nan | 0/30 | 376.2 | $718.77 |
| benign_nuisance | 2600 | pm_eb | 0/0 | 0 | nan | 0/30 | 376.2 | $718.77 |
| benign_nuisance | 2600 | predictable_variance | 0/0 | 0 | nan | 0/30 | 376.2 | $718.77 |
| benign_nuisance | 2600 | started_mixture | 0/0 | 0 | nan | 0/30 | 376.2 | $718.77 |
| boundary_early | 1000 | fixed_mixture | 0/30 | 30 | nan | 0/0 | 197.8 | $297.26 |
| boundary_early | 1000 | pm_eb | 0/30 | 30 | nan | 0/0 | 197.8 | $297.26 |
| boundary_early | 1000 | predictable_variance | 0/30 | 30 | nan | 0/0 | 197.8 | $297.26 |
| boundary_early | 1000 | started_mixture | 1/30 | 30 | 593.0 | 0/0 | 197.8 | $297.26 |
| boundary_early | 1800 | fixed_mixture | 18/30 | 30 | 1107.2 | 0/0 | 357.8 | $537.84 |
| boundary_early | 1800 | pm_eb | 0/30 | 30 | nan | 0/0 | 357.8 | $537.84 |
| boundary_early | 1800 | predictable_variance | 15/30 | 30 | 1121.5 | 0/0 | 357.8 | $537.84 |
| boundary_early | 1800 | started_mixture | 15/30 | 30 | 1147.8 | 0/0 | 357.8 | $537.84 |
| boundary_early | 2600 | fixed_mixture | 29/30 | 30 | 1348.0 | 0/0 | 477.1 | $717.40 |
| boundary_early | 2600 | pm_eb | 7/30 | 30 | 1817.3 | 0/0 | 477.1 | $717.40 |
| boundary_early | 2600 | predictable_variance | 26/30 | 30 | 1369.6 | 0/0 | 477.1 | $717.40 |
| boundary_early | 2600 | started_mixture | 22/30 | 30 | 1451.9 | 0/0 | 477.1 | $717.40 |
| boundary_late | 1000 | fixed_mixture | 0/30 | 0 | nan | 0/0 | 197.8 | $297.26 |
| boundary_late | 1000 | pm_eb | 0/30 | 0 | nan | 0/0 | 197.8 | $297.26 |
| boundary_late | 1000 | predictable_variance | 0/30 | 0 | nan | 0/0 | 197.8 | $297.26 |
| boundary_late | 1000 | started_mixture | 0/30 | 0 | nan | 0/0 | 197.8 | $297.26 |
| boundary_late | 1800 | fixed_mixture | 0/30 | 30 | nan | 0/0 | 357.8 | $537.84 |
| boundary_late | 1800 | pm_eb | 0/30 | 30 | nan | 0/0 | 357.8 | $537.84 |
| boundary_late | 1800 | predictable_variance | 0/30 | 30 | nan | 0/0 | 357.8 | $537.84 |
| boundary_late | 1800 | started_mixture | 0/30 | 30 | nan | 0/0 | 357.8 | $537.84 |
| boundary_late | 2600 | fixed_mixture | 1/30 | 30 | 976.0 | 0/0 | 477.1 | $717.40 |
| boundary_late | 2600 | pm_eb | 0/30 | 30 | nan | 0/0 | 477.1 | $717.40 |
| boundary_late | 2600 | predictable_variance | 0/30 | 30 | nan | 0/0 | 477.1 | $717.40 |
| boundary_late | 2600 | started_mixture | 0/30 | 30 | nan | 0/0 | 477.1 | $717.40 |
| harmful_adaptation | 1000 | fixed_mixture | 0/30 | 1 | nan | 0/0 | 197.8 | $297.26 |
| harmful_adaptation | 1000 | pm_eb | 0/30 | 1 | nan | 0/0 | 197.8 | $297.26 |
| harmful_adaptation | 1000 | predictable_variance | 0/30 | 1 | nan | 0/0 | 197.8 | $297.26 |
| harmful_adaptation | 1000 | started_mixture | 0/30 | 1 | nan | 0/0 | 197.8 | $297.26 |
| harmful_adaptation | 1800 | fixed_mixture | 1/30 | 30 | 749.0 | 0/0 | 357.8 | $537.84 |
| harmful_adaptation | 1800 | pm_eb | 0/30 | 30 | nan | 0/0 | 357.8 | $537.84 |
| harmful_adaptation | 1800 | predictable_variance | 0/30 | 30 | nan | 0/0 | 357.8 | $537.84 |
| harmful_adaptation | 1800 | started_mixture | 0/30 | 30 | nan | 0/0 | 357.8 | $537.84 |
| harmful_adaptation | 2600 | fixed_mixture | 22/30 | 30 | 1075.5 | 0/0 | 477.1 | $717.40 |
| harmful_adaptation | 2600 | pm_eb | 0/30 | 30 | nan | 0/0 | 477.1 | $717.40 |
| harmful_adaptation | 2600 | predictable_variance | 19/30 | 30 | 1184.9 | 0/0 | 477.1 | $717.40 |
| harmful_adaptation | 2600 | started_mixture | 23/30 | 30 | 1119.5 | 0/0 | 477.1 | $717.40 |
| recurring_regimes | 1000 | fixed_mixture | 9/30 | 30 | 807.8 | 0/0 | 197.8 | $297.26 |
| recurring_regimes | 1000 | pm_eb | 0/30 | 30 | nan | 0/0 | 197.8 | $297.26 |
| recurring_regimes | 1000 | predictable_variance | 8/30 | 30 | 827.8 | 0/0 | 197.8 | $297.26 |
| recurring_regimes | 1000 | started_mixture | 4/30 | 30 | 848.8 | 0/0 | 197.8 | $297.26 |
| recurring_regimes | 1800 | fixed_mixture | 9/30 | 30 | 807.8 | 0/0 | 357.8 | $537.84 |
| recurring_regimes | 1800 | pm_eb | 0/30 | 30 | nan | 0/0 | 357.8 | $537.84 |
| recurring_regimes | 1800 | predictable_variance | 8/30 | 30 | 827.8 | 0/0 | 357.8 | $537.84 |
| recurring_regimes | 1800 | started_mixture | 3/30 | 30 | 955.0 | 0/0 | 357.8 | $537.84 |
| recurring_regimes | 2600 | fixed_mixture | 13/30 | 30 | 1257.5 | 0/0 | 477.1 | $717.40 |
| recurring_regimes | 2600 | pm_eb | 1/30 | 30 | 2226.0 | 0/0 | 477.1 | $717.40 |
| recurring_regimes | 2600 | predictable_variance | 12/30 | 30 | 1317.5 | 0/0 | 477.1 | $717.40 |
| recurring_regimes | 2600 | started_mixture | 6/30 | 30 | 1567.8 | 0/0 | 477.1 | $717.40 |
| stationary | 1000 | fixed_mixture | 0/0 | 0 | nan | 0/30 | 197.8 | $297.26 |
| stationary | 1000 | pm_eb | 0/0 | 0 | nan | 0/30 | 197.8 | $297.26 |
| stationary | 1000 | predictable_variance | 0/0 | 0 | nan | 0/30 | 197.8 | $297.26 |
| stationary | 1000 | started_mixture | 0/0 | 0 | nan | 0/30 | 197.8 | $297.26 |
| stationary | 1800 | fixed_mixture | 0/0 | 0 | nan | 0/30 | 357.8 | $537.84 |
| stationary | 1800 | pm_eb | 0/0 | 0 | nan | 0/30 | 357.8 | $537.84 |
| stationary | 1800 | predictable_variance | 0/0 | 0 | nan | 0/30 | 357.8 | $537.84 |
| stationary | 1800 | started_mixture | 0/0 | 0 | nan | 0/30 | 357.8 | $537.84 |
| stationary | 2600 | fixed_mixture | 0/0 | 0 | nan | 0/30 | 477.1 | $717.40 |
| stationary | 2600 | pm_eb | 0/0 | 0 | nan | 0/30 | 477.1 | $717.40 |
| stationary | 2600 | predictable_variance | 0/0 | 0 | nan | 0/30 | 477.1 | $717.40 |
| stationary | 2600 | started_mixture | 0/0 | 0 | nan | 0/30 | 477.1 | $717.40 |

## Paired start-mixture versus full-stream contrasts

McNemar tests are paired by seed; Holm adjustment covers every harmful cell and horizon in this grid.

| Cell | Horizon | Start-only | Full-only | Rate difference | Paired 95% bootstrap interval | Holm p |
|---|---:|---:|---:|---:|---:|---:|
| boundary_early | 1000 | 1 | 0 | 0.033 | [0.000, 0.100] | 1 |
| boundary_early | 1800 | 0 | 3 | -0.100 | [-0.233, 0.000] | 1 |
| boundary_early | 2600 | 0 | 7 | -0.233 | [-0.400, -0.100] | 0.1875 |
| boundary_late | 1000 | 0 | 0 | 0.000 | [0.000, 0.000] | 1 |
| boundary_late | 1800 | 0 | 0 | 0.000 | [0.000, 0.000] | 1 |
| boundary_late | 2600 | 0 | 1 | -0.033 | [-0.100, 0.000] | 1 |
| harmful_adaptation | 1000 | 0 | 0 | 0.000 | [0.000, 0.000] | 1 |
| harmful_adaptation | 1800 | 0 | 1 | -0.033 | [-0.100, 0.000] | 1 |
| harmful_adaptation | 2600 | 1 | 0 | 0.033 | [0.000, 0.100] | 1 |
| recurring_regimes | 1000 | 0 | 5 | -0.167 | [-0.300, -0.033] | 0.5625 |
| recurring_regimes | 1800 | 0 | 6 | -0.200 | [-0.333, -0.067] | 0.3125 |
| recurring_regimes | 2600 | 0 | 7 | -0.233 | [-0.400, -0.100] | 0.1875 |

## Interpretation limits

These development estimates map the trade-off; they do not select a universally best process. Every monitor shares the same eventwise corrected estimates and dollar expenditure within a seed. Nondetections remain in the all-harm denominator, and onset reachability is shown separately. A confirmatory result requires independent high-precision null calibration and a fresh alternative seed block with a frozen primary contrast.

Reproduction: `uv run python scripts/run_started_mixture_horizon_grid.py --seeds 30 --seed-offset 57100000 --budget-dollars 720 --device cuda`, then `uv run python scripts/analyze_started_mixture_horizon_grid.py`.
