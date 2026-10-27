# Active Statistical Inference paired-cost allocation benchmark

**Status:** frozen development protocol v0.6; no independent confirmation claim. `dev_v5` captured v0.5 at execution. This update records the inspected authors' code commit and clarifies that the local implementation is an adaptation. `dev_v1` is retained but superseded because its stated budgets were not matched. `dev_v2/dev_v3` are preserved as budget-matched development runs but did not isolate random streams by outcome component. `dev_v4` uses dedicated component-specific generators and adds paired uncertainty intervals. `dev_v5` repeats the same seed block to verify determinism and stores execution-time source snapshots.  
**Question:** at a fixed horizon and equal expected label budget, does the ASI uncertainty allocation reduce the uncertainty of a model-assisted estimate of mean paired policy-cost gain versus uniform label sampling?  
**Primary source:** Zrnic and Candès, [Active Statistical Inference, ICML 2024](https://proceedings.mlr.press/v235/zrnic24a.html), including the [authors' code](https://github.com/tijana-zrnic/active-inference).

The authors' repository was inspected at commit `0f99f7ee6055b6f86c0ce88ece3cb2bf3c9c19cd`; its notebooks and utility module were not executed. The implementation follows the paper's mean-estimation equations and batch allocation logic, adapted to the paired-cost target defined below.

## Scope and estimand

This benchmark evaluates the fixed-horizon mean-estimation component of ASI. It does not evaluate an anytime-valid alarm, a candidate promotion guarantee, or the full sequential pipeline. The target is the average paired score `Z = cost(reference, Y) - cost(candidate, Y)` over a 3,200-event post-shift covariate batch. The synthetic evaluator knows the conditional outcome law and target-batch expected paired gain. The learner sees covariates and 800 source labels, then receives only queried target labels.

The reference and candidate are deterministic binary policies with false-negative cost 2 and false-positive cost 1. Outcomes follow a fixed logistic conditional law; the target feature distribution has a declared mean shift of 0.5 on the first feature. This is a covariate-shifted batch, not a time-indexed or performative environment.

## Methods

- **Uniform PPI, matched spend (primary):** a constant Bernoulli query probability equal to the per-seed mean ASI propensity. This compares the methods at exactly the same expected query count for each target batch.
- **Uniform PPI, full budget (secondary):** constant Bernoulli query probability `B/n`, with augmented estimate `mean(f(X) + I(Y-f(X))/q)`.
- **ASI allocation:** fit logistic outcome probabilities on the 800 source events. For each target event, compute the model-implied conditional standard deviation of the paired score, which is the mean-estimation residual-scale allocation signal. Choose `q_i = (1-τ) min(η u_i, 1) + τ B/n`, `τ=0.5`, with the largest `η` satisfying `sum_i min(η u_i,1) ≤ B`. Use the same augmented estimator.
- **Oracle allocation diagnostic:** replace fitted outcome probabilities by evaluator probabilities when calculating the ASI uncertainty score. This is an upper-bound diagnostic and is never learner-visible.

For ASI, `n=3,200`, and maximum expected budget `B=640`. Because the uncertainty signal is zero where the two policies agree, the ASI mixture can leave some of that allowance unused. The primary uniform comparator is calibrated to exactly the resulting ASI expected spend within each seed. A second uniform comparator uses the full expected budget of 640. Independent Bernoulli query decisions use common uniform random numbers across methods. The published batch procedure constrains expected labels; it does not guarantee a pathwise 640-label cap. The realized label count is reported, and no claim of hard-cap compliance is made.

## Metrics and stopping rule

Use development seeds `2026102800–2026102829` (corrected runs reuse the seed block solely to repair the comparison and add paired uncertainty analysis). Use independent torch random generators per stream component, with fixed documented seed offsets. Report per-seed point-estimation error, nominal 95% asymptotic interval width and coverage, realized labels, and expected labels. For ASI-minus-uniform differences in absolute error, squared error, interval width, and empirical coverage, report paired seed-block percentile bootstrap intervals with 20,000 draws and a fixed seed. These exploratory intervals do not turn 30 seed blocks into confirmation and do not calibrate the per-stream CLT interval. Stop after these 30 seeds. Do not tune the model, mixture, or costs on these outputs.

## Information and validity limits

The score predictor and propensity are fixed using source labels and the complete unlabeled target batch before target labels are released. Unqueried target outcomes remain evaluator-only. The augmented estimate is unbiased under the registered independent Bernoulli sampling design and positive propensities. Its reported normal interval is asymptotic as in the paper, not finite-sample or time-uniform. The evaluation isolates label allocation for a paired-cost mean; it cannot establish sequential decision-harm monitoring or net intervention value.
