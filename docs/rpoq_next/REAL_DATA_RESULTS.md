# Real-data results

## R0 (protocol [`REAL_DATA_PROTOCOL.md`](REAL_DATA_PROTOCOL.md)): context heterogeneity and stability, development splits only

CRSP CIZ panel, 10 disjoint cohorts of 300 train-universe PERMNOs, benefit `Y = −Z` (candidate over reference, 5 bps), 8 train-quantile bins. Validation 2015–2017 versus calibration 2018–2019. **Test split not read.** Artifact: `outputs/rpoq_next/r0/results.json`; code `scripts/rpoq_next/crsp_heterogeneity.py`.

| Context | top-bin SNR / median (val) | top-bin val μ̂ 95% CI (cohort bootstrap) | Spearman(val SNR, cal SNR) | top-bin cal μ̂ | Heterogeneity | Stable |
|---|---|---|---|---|---|---|
| size (`log1p_dlycap`) | 5.09 | excludes 0 | **0.738** | +0.0013 (+13 bps) | **yes** | **yes** |
| abs_return (`|dlyret|`) | 1.85 | — | −0.762 | ≈ 0 | no | no |

Mean benefit by size bin (bps per event), validation: 16.0, 8.3, 4.9, 2.6, 4.5, 3.0, 2.7, 3.7; calibration: 12.7, 6.9, 4.6, 1.8, 1.5, −0.9, −0.1, −1.3 (bin 0 = smallest).

**Registered verdict:** the mechanism has purchase on CRSP through the size context (both criteria met for one definition); not through absolute return.

**Caveats that bound what this means.**
- Bin 0 is the smallest-cap stocks, where a flat 5 bps cost is not credible; the apparent benefit there is partly a consequence of the imposed cost assumption, and these stocks are where microstructure effects are largest. This is a retrospective property of the panel, not a deployable edge.
- Heterogeneity weakened between validation and calibration (large bins turned negative), i.e. the nonstationarity the synthetic `het_flip` setting warns about is partly present in the data, even though the top bin held.
- This establishes only that there is structure for an allocation rule to use. It says nothing yet about whether the rule beats uniform at a matched budget.

## R1 (protocol [`REAL_DATA_PROTOCOL.md`](REAL_DATA_PROTOCOL.md), second section): exploratory allocation replay on the size context

10 cohorts × 20 query seeds, 2020–2025 test split (**exposed**, so descriptive), benefit direction, budgets 5% and 20%. Per-cohort bin estimates from the pooled validation and calibration splits (declared before running). Artifacts: `outputs/rpoq_next/r1/runs.csv`, `meta.json`, `summary.json`; code `src/shiftlab/dive/rpoq_next/crsp_r1.py`, `scripts/rpoq_next/analyze_r1.py`.

Mean final log-wealth (each arm with its better bet type), crossing rate in brackets:

| Budget | uniform | neyman | growth | random_conc | Δ = growth − best baseline [95% CI] |
|---|---|---|---|---|---|
| 5% | 1.41 (0.31) | 1.43 (0.31) | **0.27 (0.01)** | 0.98 (0.36) | **−1.15 [−1.56, −0.76]** (baseline: neyman) |
| 20% | 6.54 (0.84) | 6.50 (0.86) | **3.33 (0.64)** | 2.71 (0.55) | **−3.21 [−5.16, −0.87]** (baseline: uniform) |

Uniform reproduces the S6 values (1.41 and 6.54) exactly, which is a consistency check on this harness.

**Registered verdict: NOT SUPPORTED, and the allocation is significantly worse than uniform at both budgets** (the interval excludes 0 on the harm side).

Descriptive notes (the diagnostic below is post-hoc and not part of the registered rule):
- Neyman is indistinguishable from uniform here (residual second moments are similar across size bins), so variance-based allocation has nothing to exploit on this stream either.
- The random-concentration placebo is also worse than uniform, so concentrating labels in one bin is costly on this stream whether or not the bin is informed.

### R1 post-hoc diagnostic (not part of the registered rule): why the allocation lost

`scripts/rpoq_next/r1_diagnostic.py`, same cohorts. Averages over cohorts (bps of benefit per event; bins 0 to 7, smallest to largest cap):

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| pre-test μ̂ (validation + calibration) | 15.1 | 7.4 | 4.7 | 2.2 | 3.3 | 1.7 | 1.7 | 1.7 |
| test-period μ | 5.0 | 7.3 | 7.8 | 7.7 | 8.3 | 7.1 | 6.8 | 3.9 |
| growth `q` at 5% budget | 0.488 | 0.212 | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 |
| test event share | 0.064 | 0.069 | 0.077 | 0.085 | 0.084 | 0.097 | 0.165 | 0.359 |

The allocator sent about half the labels to bin 0, whose benefit fell from 15 bps before 2020 to 5 bps in the test period, and starved bins 2 to 7, which hold about 80% of test events and had higher benefit. This is the synthetic `het_flip` failure condition on real data (with a second effect: the test-period size distribution moved toward large caps, 36% of events in bin 7). A stability check on the pre-test periods (R0, ρ = 0.74 between validation and calibration) did **not** warn of it, so a pre-test stationarity diagnostic is not sufficient protection.

**Spend was not exactly matched** (mean labels, runs.csv): at 5% budget uniform 5455, neyman 5319, growth 5073, random_conc 5028; at 20% uniform 21,878, neyman 21,289, growth 20,224, random_conc 12,676. Growth spent about 7–8% fewer labels than uniform (a mild disadvantage); the placebo at 20% spent far less because a small bin cannot absorb the budget, so that placebo comparison is not budget-matched. Neither changes the sign of the main result.

## B1 (protocol [`REAL_DATA_PROTOCOL.md`](REAL_DATA_PROTOCOL.md), third section): repo evidence-directed rule as a benchmark on CRSP

10 cohorts × 20 seeds, 2020–2025 test split (exposed), benefit direction, pooled Kelly bet. `EvidenceDirectedQueryPolicy` imported unchanged; `q_min = 0.25·frac`, `q_max = min(1, 2.5·frac)`, default curve. Artifacts: `outputs/rpoq_next/b1/runs.csv`, `summary.json`; code `src/shiftlab/dive/rpoq_next/crsp_b1.py`.

| Budget | uniform LW (crossing) | evidence-directed LW (crossing) | Difference [95% CI] | Mean labels, uniform vs ED |
|---|---|---|---|---|
| 5% | 1.41 (0.31) | 0.66 (0.135) | **−0.75 [−1.00, −0.51]** | 5,455 vs 2,441 |
| 20% | 6.54 (0.845) | 2.63 (0.47) | **−3.91 [−4.77, −2.98]** | 21,878 vs 12,221 |

Uniform reproduces the S6/R1 values (1.41 and 6.54) exactly.

**Reading (descriptive; no gate).** The repo's evidence-directed rule is significantly worse than uniform on this stream at both budgets. It is **not label-matched**: it spends 45% (5% budget) and 56% (20% budget) of what uniform spends, because its propensity sits at the `q_min` floor while evidence is low and the budget taper reduces it further. Per label spent, log-wealth is similar at the 5% budget (about 2.7e-4 per label for both) and lower for ED at 20% (2.2e-4 vs 3.0e-4). So the comparison shows "worse at the configured spend", not "less efficient per label", and a spend-matched version (for example a higher `q_min`) was not run; it would be a new protocol.

Benchmarks still not run: PPRM, Podkopaev–Ramdas, `comparecast`, Robust ASI proper (S6b/A2 used an adaptation).
