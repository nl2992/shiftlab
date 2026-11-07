# CAMS eta-scale follow-up results

**Status:** completed, bounded development-only screen.

Rows: 2025; episodes: 81; BAs: 11; five policy seeds per episode.
Maximum net-cost identity residual: 1.42e-14.

## Equal-BA mean cost decomposition

| Method | Net cost | Loss | Labels | Label cost | Switches | Switch cost | Promotions | Rollbacks | First promotion |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| cams_eta_3 | 29.793 | 22.513 | 33.16 | 1.658 | 1.125 | 5.623 | 0.966 | 0.159 | 364.6 |
| cams_adapter | 30.031 | 22.691 | 36.34 | 1.817 | 1.104 | 5.522 | 0.952 | 0.152 | 356.6 |
| cams_eta_1p5 | 30.107 | 22.692 | 34.75 | 1.737 | 1.135 | 5.677 | 0.973 | 0.162 | 358.6 |
| cams_eta_2 | 30.260 | 22.646 | 34.40 | 1.720 | 1.179 | 5.894 | 0.994 | 0.185 | 367.8 |
| cams_max_adapter | 32.030 | 23.208 | 30.97 | 1.549 | 1.455 | 7.273 | 1.121 | 0.333 | 351.7 |

## Paired eta-scale contrasts versus CAMS

### `cams_eta_1p5`

Equal-BA mean difference: **+0.076**; hierarchical 95% interval [-0.883, +1.021]; directional BA wins 7/11; BAs with ≥5 savings and episode interval below zero: 0/11.

| BA | Mean difference | 95% episode-bootstrap interval |
|---|---:|---:|
| AZPS | -0.120 | [-0.925, +0.521] |
| BANC | -0.260 | [-0.517, -0.016] |
| EPE | +1.271 | [-0.276, +3.226] |
| ERCO | +2.230 | [-0.514, +5.971] |
| FMPP | -2.680 | [-6.283, +0.093] |
| FPC | +2.004 | [+0.101, +4.191] |
| MISO | -0.674 | [-1.254, -0.167] |
| NEVP | -0.344 | [-0.982, +0.274] |
| NYIS | -0.207 | [-1.429, +0.848] |
| SWPP | -0.535 | [-1.161, +0.010] |
| TIDC | +0.152 | [-0.490, +0.942] |

### `cams_eta_2`

Equal-BA mean difference: **+0.229**; hierarchical 95% interval [-0.578, +1.041]; directional BA wins 3/11; BAs with ≥5 savings and episode interval below zero: 0/11.

| BA | Mean difference | 95% episode-bootstrap interval |
|---|---:|---:|
| AZPS | +0.642 | [+0.131, +1.178] |
| BANC | +0.146 | [-0.746, +0.936] |
| EPE | +0.765 | [+0.152, +1.535] |
| ERCO | -0.584 | [-3.830, +3.328] |
| FMPP | -0.487 | [-2.820, +1.923] |
| FPC | +0.481 | [-0.668, +1.869] |
| MISO | +0.224 | [-1.406, +2.668] |
| NEVP | +0.995 | [-0.567, +3.280] |
| NYIS | +0.937 | [-0.746, +3.168] |
| SWPP | +1.156 | [-1.376, +5.476] |
| TIDC | -1.760 | [-3.744, -0.108] |

### `cams_eta_3`

Equal-BA mean difference: **-0.238**; hierarchical 95% interval [-1.048, +0.513]; directional BA wins 5/11; BAs with ≥5 savings and episode interval below zero: 0/11.

| BA | Mean difference | 95% episode-bootstrap interval |
|---|---:|---:|
| AZPS | -0.824 | [-2.640, +0.810] |
| BANC | +1.179 | [-0.044, +3.231] |
| EPE | +0.576 | [-1.016, +2.269] |
| ERCO | +0.417 | [-2.205, +3.751] |
| FMPP | -2.260 | [-4.638, +0.039] |
| FPC | +0.074 | [-0.600, +0.810] |
| MISO | +0.071 | [-0.854, +1.131] |
| NEVP | -0.110 | [-1.121, +1.334] |
| NYIS | -1.400 | [-3.485, +0.279] |
| SWPP | -0.591 | [-1.878, +0.766] |
| TIDC | +0.254 | [-0.376, +1.110] |

## Decision

The lowest-cost variant is `cams_eta_3`. Frozen gate: **FAIL**. No variant achieved the required ≥5-unit savings, at least 8/11 BA-level wins, and a hierarchical interval below zero.
The future holdout remains closed. This is a standard schedule-tuning result, not a novel-method result.

All BAs are within one provider; chronology and one-hour feedback delay are simulated/revised; the cost contract is not calibrated field utility; no known-null error rate is available.
