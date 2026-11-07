# Fixed challenger control results

**Status:** positive but post-selection development diagnostic; independent confirmation is still required.

| Policy | Net cost | Prediction loss | Labels | Label cost | Switches | Switch cost |
|---|---:|---:|---:|---:|---:|---:|
| fixed_challenger | 26.37 | 21.37 | 0.00 | 0.00 | 1.00 | 5.00 |
| fixed_incumbent | 78.67 | 78.67 | 0.00 | 0.00 | 0.00 | 0.00 |
| CAMS (five-seed episode mean) | 29.93 | 22.67 | 36.47 | 1.82 | 1.09 | 5.43 |

## Primary fixed challenger contrast

Fixed challenger minus CAMS equal-BA cost: **-3.53**; hierarchical BA-then-episode 95% interval [-5.11, -1.98]; directional BA wins 11/11; BAs with at least 5 units saved and an episode interval below zero: 2/11.

| BA | Episodes | Fixed challenger − CAMS | 95% episode-bootstrap interval |
|---|---:|---:|---:|
| AZPS | 8 | -2.78 | [-6.27, +0.88] |
| BANC | 7 | -1.43 | [-3.68, +1.24] |
| EPE | 8 | -3.59 | [-8.10, +0.72] |
| ERCO | 8 | -4.73 | [-6.56, -3.15] |
| FMPP | 6 | -7.45 | [-11.61, -4.42] |
| FPC | 8 | -6.59 | [-9.17, -4.70] |
| MISO | 7 | -2.67 | [-4.65, +0.29] |
| NEVP | 8 | -0.26 | [-3.10, +2.84] |
| NYIS | 8 | -4.29 | [-6.68, -1.18] |
| SWPP | 8 | -3.83 | [-6.17, -0.97] |
| TIDC | 5 | -1.22 | [-6.49, +3.57] |

## Interpretation

The fixed challenger uses no label feedback and pays one switch cost per episode. It is a simple feasible policy, not a new algorithm. This panel was selected by the same 2022–2023 development-period F8 profile being evaluated, so the result is optimistic by construction. The next scientific test is an untouched chronological confirmation with a train-time model-selection rule fixed before opening outcomes; otherwise this is only a benchmark observation.

All BAs share one EIA provider, label release is simulated, historical values are revised, and cost units are hypothetical. No field-utility or cross-provider claim follows.
