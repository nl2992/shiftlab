# EIA-930 trained-challenger profile decision

**Decision:** stop this candidate before algorithm comparison. The preregistered F8 pair-profile gate did not pass.

## Frozen screen result

The model was fit separately by balancing authority on eligible 2021 observations only. Evaluation used 2022–2023, with fixed 2021 p90 demand thresholds and no policy simulation.

| BA | Eligible development events | Disagreement rate | Challenger accuracy on disagreements | Complete contiguous 2,000-hour episodes | F8 profile |
|---|---:|---:|---:|---:|---|
| PJM | 17,303 | 5.433% | 88.617% | 6 | Fail: disagreement rate above 5% |
| ERCO | 17,520 | 3.693% | 85.008% | 8 | Pass |
| CISO | 17,386 | 2.640% | 82.353% | 6 | Fail: conditional accuracy below 85% |

Only ERCO satisfies both the frozen frequency and conditional-accuracy criteria; the protocol requires at least two of three BAs. The profile gate therefore fails. No method policy, deployment cost, label expenditure, or switch expenditure was computed. The 2024–2025 holdout remains unopened.

## Interpretation and limits

This is a model-pair/profile mismatch for the registered three-BA development panel, not evidence that an adaptation algorithm failed. It does not establish the F8 mechanism on EIA-930, a method advantage, a novelty claim, or transfer to independent sources. Historical EIA values are revised values and the one-hour feedback delay is simulated; the BAs are correlated under one provider. Source and timing limitations are documented in `ELECTRICITY_SOURCE_FEASIBILITY_20261107.md`.

## Reproduction

From the repository root, with the six checksummed bulk CSVs at the ignored path `data/raw/eia930_f8_development_20261107/`:

```bash
uv run python scripts/sota_sprint/eia930/profile_ml_challenger.py
```

Protocol: `PROTOCOL.md`. Machine-readable output: `DATASET_PROFILE.json`. The run is deterministic (`random_state=1729`). No confirmatory evaluation was performed.
