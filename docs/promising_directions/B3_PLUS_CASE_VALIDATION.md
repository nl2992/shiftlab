# Phase 8 validation of the two new case studies

Method frozen at `e846107`; screening rules registered at `670c1bf`. The model pair is **not**
re-selected: `validate_case.py` re-derives it deterministically from rows [0, 60%) with the same
`select_pair` call the screening used, so reproducing it is itself the first check. The registry
and the screening status files are never written by validation.

Command: `uv run python research/b3_plus/dataset_discovery/validate_case.py openml_ldpa uci_occupancy`
Records: `docs/promising_directions/results/b3_plus/screening/<id>/validation/validation.json`

## Configurations

| ID | Change | Purpose |
|---|---|---|
| V0 | registered seeds (base 20261101) | reproduce the screening result |
| V1 | **disjoint** seed batch (base 20261103) | the result is not a seed artefact |
| V2 | `c_s = 20` | switching-cost sensitivity |
| V3 | `B = 400` | budget sensitivity |

## openml_ldpa (K = 32, episode bootstrap)

| Config | P0 | P3b | P6 | **P7s** | P7s vs P3b (95% CI) | labels | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| V0 | 663.00 | 483.25 | 506.51 | **478.82** | -4.43 [-7.03, -2.58] | 181 -> 115 | WIN |
| V1 | 663.00 | 483.68 | 506.68 | **479.10** | -4.58 [-7.41, -2.61] | 181 -> 116 | WIN |
| V2 | 663.00 | 498.81 | 518.16 | **493.52** | -5.29 [-9.54, -2.57] | 181 -> 115 | WIN |
| V3 | 663.00 | 483.07 | 485.82 | **471.59** | **-11.48** [-16.45, -7.69] | 329 -> 158 | WIN |

V0 reproduces the screening value exactly. The sign and magnitude survive a disjoint seed batch.
P7s beats P6 in **every** configuration. At `B = 400` the gain more than doubles, as expected for
a label-saving mechanism with more label spend available to remove.

**Per-episode consistency: 30 of 32 episodes improve**, 2 worsen, none tie. Worst episode +3.13,
best -36.95. The mean is therefore a broad majority effect, not one outlier.

**The two losses are fully attributed.** Episodes 3 and 8 are *exactly* the episodes in which P7s
promoted later than P3b (975.0 vs 965.5, and 1027.4 vs 978.2). The cause is the **pre-promotion
hopeless gate** firing and briefly starving acquisition, which is the same mechanism identified
on synthetic world W1. No other episode promoted later and lost. This is the method's known
failure mode, observed on real data, and it costs +1.60 and +3.13 against gains of up to -36.95.

Mechanism, e.g. episode 0: P3b spends 195.4 labels; P7s promotes at the identical time having
spent 34.4 before promotion and 60.4 after, so the saving is post-promotion spend, as specified.

## uci_occupancy (K = 4, seed bootstrap, LOW-POWER)

| Config | P0 | P3b | P6 | **P7s** | P7s vs P3b (95% CI) | labels | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| V0 | 481.25 | 177.63 | 236.45 | **176.62** | -1.01 [-1.03, -0.99] | 102 -> 81 | WIN |
| V1 | 481.25 | 179.44 | 239.08 | **178.42** | -1.02 [-1.04, -1.00] | 101 -> 81 | WIN |
| V2 | 481.25 | 181.38 | 240.20 | **180.37** | -1.01 [-1.03, -0.99] | 102 -> 81 | WIN |
| V3 | 481.25 | 171.13 | 183.08 | **168.33** | -2.80 [-2.82, -2.77] | 149 -> 93 | WIN |

### Material weakness, disclosed

**Three of its four episodes are exactly tied** (`dcost = +0.000`); the entire effect comes from
**one episode** (episode 1, -4.03). The reason is mechanistic and benign: P3b promotes in only
that one episode (promotion rate 1.0 there, 0.0 in episodes 0, 2 and 3), and with no promotion
there is no settled phase for the gate to act on, so P7s is identical to P3b by construction.

The seed-level CI `[-1.03, -0.99]` is therefore **misleadingly tight**: it measures seed noise
around an effect that is concentrated in a single episode, not agreement across episodes. The
pre-registered SUCCESS rule is met and is not being revised after the fact, but this case must be
reported as **one-episode evidence**, and it should not be given equal visual weight to ldpa or
rialto in any table or figure. If a reviewer discounts it entirely, the paper still has four cases
and two properly powered ones.

## Invariants, all configurations, both datasets

| Check | Result |
|---|---|
| Hard label budget respected pathwise | **pass** — `max_queries` equals the budget exactly (200, and 400 at V3), never exceeds it |
| No promotion before the first label release | **pass** — earliest promotion 212-229 against a declared delay of 100 |
| Pair selected without locked data | **pass** — `select_pair` receives only rows [0, n60) and raises otherwise; recorded `selection_inputs: "rows [0, 60%) only"` |
| Declared delay fixed before evaluation | **pass** — 100 events for both, justified in the registry |
| Test suite | **72 passed, 6 skipped** |

## Figure

Validated per-episode source data for the mechanism figure is exported to
`docs/promising_directions/results/b3_plus/figure_data/ldpa_per_episode.csv` (32 rows: promotion
times for both policies, labels before and after promotion, per-episode costs and differences).

**PaperBanana is not available in this environment** and `AGENTS.md` requires it for research
visuals and forbids silently substituting another generator. It is a separate repository
(https://github.com/dwzhu-pku/PaperBanana) requiring a clone plus a Gemini or OpenRouter API key.
**The figure is therefore not generated, and this dependency is reported rather than worked
around.** The data above is ready for it.
