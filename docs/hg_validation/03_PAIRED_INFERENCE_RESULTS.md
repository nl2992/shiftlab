# 03. Paired inference results (source: `outputs/hg_validation/03_PAIRED_INFERENCE.csv`)

| gen | labels | arm | mean gain | within-world 95% CI | across-world 95% CI | meets frozen +0.05 |
|---|---|---|---|---|---|---|
| G1 | 10% | HG | +.053 | [.031, .076] | [.020, .120] | yes |
| G1 | 20% | HG | +.086 | [.068, .103] | [.005, .220] | yes |
| G2 | 10% | HG | +.051 | [.032, .071] | [.024, .097] | yes (barely) |
| G2 | 20% | HG | +.035 | [.022, .048] | [.001, .091] | **no** (CI upper bound .048 < .05 within-world) |
| G1 / G2 | 10/20% | HG_unifcap | +.070 / +.091 / +.056 / +.041 | all within-world CIs exclude 0 | lower bounds .028 / .008 / .026 / .001 | 3 of 4 |

**Per-world gains show the concentration** (HG): G1 10%: abrupt δ1.2 +.12, gradual +.02, recurrent +.02; G1 20%: +.22, +.005, +.032; G2 10%: +.028, +.020, +.038, `cov_benign` +.120; G2 20%: +.010, −.005, **recurrent +.118**, +.018. The average gain is carried by one world per cell; elsewhere the gain is 0–0.04 and in one case slightly negative.

**Reading.**
1. Every HG gain is distinguishable from 0 *within the simulated worlds* (CIs exclude 0), so these are not seed noise.
2. Across worlds, intervals are wide and several lower bounds are ≈0 (.005, .001): with 3–4 harm worlds the data cannot establish a typical gain, only that it is rarely negative.
3. Against the frozen threshold, three cells reach +0.05 (two only by ≤0.003 of margin) and G2/20% does not; the verdict stays "partially supported". The threshold is not changed.
4. False alarms: the largest per-world change in benign/null false alarm is +0.040 (G1 20%), +0.0175 (G2 20%); harm before alarm falls 16–33 units in all cells.
5. `HG_unifcap`, the repair that restores the marginal-null guarantee, is as good or better in every cell (gain +.041 to +.091). It is a post-hoc development refinement, so any confirmation claim requires a fresh frozen pool (Goal 11).
Not done: runtime/memory comparison, weighting sensitivity across worlds, multiplicity-controlled simultaneous claims over many configs.
