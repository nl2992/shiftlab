# Broad EIA-930 F8 profile screen decision

**Profile gate: PASS (development screen only).** The fixed 2021-trained classifier pair matched the F8 profile in 11 of the 64 BAs present across the six checksummed 2021–2023 source files. This clears the prewritten threshold of five. The screen generated no policy outcomes, deployment costs, label expenditures, or switch expenditures.

## Matching BAs

| BA | Eligible 2022–2023 events | Disagreement rate | Challenger accuracy on disagreements | Complete 2,000-hour blocks |
|---|---:|---:|---:|---:|
| AZPS | 17,516 | 3.226% | 88.673% | 8 |
| BANC | 17,445 | 3.015% | 86.882% | 7 |
| EPE | 17,493 | 3.116% | 88.257% | 8 |
| ERCO | 17,520 | 3.693% | 85.008% | 8 |
| FMPP | 17,350 | 4.778% | 86.610% | 6 |
| FPC | 17,520 | 4.789% | 85.578% | 8 |
| MISO | 17,461 | 3.860% | 90.059% | 7 |
| NEVP | 17,520 | 1.998% | 88.286% | 8 |
| NYIS | 17,520 | 4.486% | 87.150% | 8 |
| SWPP | 17,519 | 3.510% | 87.967% | 8 |
| TIDC | 17,456 | 2.967% | 91.506% | 5 |

All 64 registered BAs and their individual profiles are retained in `DATASET_PROFILE.json`; no BA was excluded based on its result. The original three-BA pilot remains separately recorded and unchanged.

## Interpretation and next gate

This establishes a promising real chronological **profile match** for an F8-style replay: a train-only day-ahead load classifier disagrees with a one-day persistence incumbent on 2.0–4.8% of eligible hours and is correct on 85.0–91.5% of those disagreements in 2022–2023. It does not establish an algorithmic advantage or resolve the issue economically.

The 11 matching BAs were selected by a frozen development-period rule and are not independent provider-level sources. EIA historical values are revised snapshots, and one-hour label release is simulated. The following policy screen, if run, must include all 11 matching BAs, a full comparator suite, paired uncertainty clustered at the BA and contiguous-time levels, and explicit net-cost decomposition. Any positive 2022–2023 development result would still require an untouched chronological window (2024 onward) and should be described as a simulated-feedback replay. No cross-provider transfer claim is justified by this screen.

## Reproduction

```bash
uv run python scripts/sota_sprint/eia930/profile_all_balancing_authorities.py
```

Frozen specification: `PROTOCOL.md`. Runner: `scripts/sota_sprint/eia930/profile_all_balancing_authorities.py`.
