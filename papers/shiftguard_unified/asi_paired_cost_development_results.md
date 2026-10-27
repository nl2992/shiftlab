# Active Statistical Inference paired-cost development results

**Status:** exploratory fixed-horizon development benchmark, not confirmation.  
**Protocol:** [v0.5](asi_paired_cost_protocol.md).  
**Source method:** Zrnic and Candès, [Active Statistical Inference (ICML 2024)](https://proceedings.mlr.press/v235/zrnic24a.html); authors' [reference repository](https://github.com/tijana-zrnic/active-inference).  
**Run:** [`asi_paired_cost_dev_v5/`](../../outputs/shiftguard_unified/sota_reproductions/asi_paired_cost_dev_v5/).

The implementation adapts the paper's batch augmented mean estimator and residual-scale allocation to a fixed-horizon paired policy-cost contrast. It does not reproduce the paper's original application datasets or its complete experimental suite. Target covariates are available as an unlabeled batch; the learner fits a logistic outcome model using 800 historical synthetic events and uses it to predict the conditional mean and residual scale of the paired score. The target batch contains 3,200 covariate-shifted events, and the maximum expected label allowance is 640.

## Results

The primary comparison matches uniform Bernoulli sampling to ASI's expected query count within each seed. The ASI score is zero wherever the two fixed policies agree, so the uniform-mixture ASI rule uses some of its allowance only through the uniform floor. Its mean expected spend was 526.15 labels. The full-budget uniform arm uses 640 expected labels, and the oracle arm uses evaluator probabilities only to form an upper-bound allocation diagnostic.

| Method | Mean labels | MAE | RMSE | Mean 95% asymptotic interval width | Coverage |
|---|---:|---:|---:|---:|---:|
| ASI residual-scale | 526.93 realized / 526.15 expected | 0.0087 | 0.0111 | 0.0488 | 30/30 |
| Uniform, matched expected spend | 527.90 / 526.15 | 0.0176 | 0.0203 | 0.0801 | 30/30 |
| Uniform, full expected budget | 643.90 / 640.00 | 0.0169 | 0.0200 | 0.0739 | 29/30 |
| Oracle ASI allocation | 526.93 / 526.15 | 0.0086 | 0.0111 | 0.0488 | 29/30 |

The paired 20,000-draw percentile bootstrap interval for ASI minus matched uniform was −0.0089 in mean absolute error (95% interval [−0.0129, −0.0047]), −0.0003 in mean squared error ([−0.0004, −0.0001]), and −0.0313 in interval width ([−0.0336, −0.0290]). The coverage difference was 0/30 in this seed block, with a bootstrap interval [0.0000, 0.0000]; that degenerate descriptive interval reflects identical observed coverage counts and should not be interpreted as a calibrated coverage guarantee. Against full-budget uniform, the MAE difference was −0.0081 ([−0.0127, −0.0037]) and interval-width difference was −0.0251 ([−0.0269, −0.0233]).

The result is consistent with lower estimation error and narrower intervals from residual-informed allocation on this specific synthetic task. Thirty seed blocks are too few to assess the nominal 95% interval's repeated-sampling coverage, and the benchmark has one cost matrix, one policy pair, immediate labels, and a known parametric conditional law. It does not evaluate sequential detection delay, anytime validity, model promotion, hard pathwise label caps, intervention utility, or performance under residual-model misspecification. No superiority or real-world utility claim follows.

## Reproducibility checks

The CUDA run used the RTX 4060 Laptop GPU and stored the exact runner, estimator and protocol snapshots under the run directory. The independent verifier checked the 120-row table, unique seed-method keys, hashes, expected-budget equality within every seed, the full-budget propensity, and recomputed summaries and paired contrasts. A second execution with the same seed block reproduced stream-level metrics exactly. Five focused estimator tests passed; Ruff and mypy passed for the implementation, runner and verifier.

The first run was retained as `asi_paired_cost_dev_v1` but marked superseded after its uncertainty-mixed allocation averaged only 524 expected labels while the original uniform comparison used 640. The corrected primary comparison uses a per-seed matched-spend uniform arm and retains 640-label uniform as a secondary reference. Intermediate corrected runs are preserved; `dev_v5` is the source-snapshotted, independently verified run.
