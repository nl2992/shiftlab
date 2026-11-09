# Paper 1 — Stage 3 failure analysis and recovery protocol

Source branch: `research/paper1-eqsdp-foundation-2026-11-08`, HEAD `3064006314be5dbac71aa573634d329fddc87015` (2026-11-09 02:44 UTC). This document is **not a result** from a new experiment. The Stage 3 selection failure and original frozen protocols remain unchanged.

## 1. What actually failed

In the first independent odd-episode selection check, the frozen BO winner lost to `s2armr_H1100`: mean paired total cost difference +1.074 units (95% episode-bootstrap interval [-1.495, +5.071]), prediction-error difference +0.1205 percentage points, compared with a predeclared allowable 0.1 pp. It bought 46.57 labels per episode rather than 70.94. The fee reduction (-1.218 units) did not compensate for larger late adoption (+1.718) and false promotion (+0.634). The remaining components were reversal churn -0.082 and residual +0.023.

Eight of nine dataset-level means were lower for the candidate, but Kansas City was +21.85 units worse per episode. In episode 39, the candidate adopted the better challenger roughly 940 rounds later, with a ~610-unit loss penalty. One such episode contributed +607.8 to the 40-episode cumulative delta. Episode 37 displayed a large false-promotion penalty. These are outcomes from an exposed selection check and cannot be excluded to rescue the predeclared result.

The simpler arm-R + end-of-horizon purchasing cutoff `H=1100` (for `T=2000`, `d=100`, labels requested only through `t=800`) generalized on odd episodes: -4.345 cost against Wald *without* that cutoff, +0.0183 pp prediction-error difference. **This is not a Wald superiority result at matched acquisition.** In the even split, Wald 0.97/0.2 with the same H=1100 cutoff scored J=475.0134 versus J=475.0223 for EQSDp Arm R + cutoff, a tie. The improved fee policy is usable by Wald as well.

## 2. Mechanistic diagnosis — to validate by tracing

**Misaligned value score.** The candidate's `p_cross(t)` computes a Beta-binomial probability that an imaginary `L=13`-label block pushes an EQSDp confidence bound past the switching hurdle. It does not estimate `E[J | do(query)] - E[J | do(skip)]`, nor does it price the magnitude of a miss. Even a low-probability extra label can be worth `c_q=0.05` if it can avert hundreds of prediction losses. The probability threshold therefore optimizes a proxy rather than expected total cost.

**Potential self-starvation.** The code reduces `virtual_remaining` when requests were skipped. That can reduce subsequent paced purchase propensity, and repeated skipping may suppress future evidence. This is an implementation mechanism hypothesis, **not yet an observed explanation of Kansas City**.

**Tail-blind Bayesian optimization.** The optimizer minimized average cost plus a mean-accuracy constraint on only 377 even episodes, selected best-of-80 settings, and did not constrain adverse conditional tails. The winning candidate's even-split mean gain was -1.724 units; the odd-split point estimate flipped to +1.074, with one heavy-tailed dataset dominating the result. Modules B (pending weight) and G (dependence calibration) did not independently help; the frozen candidate was effectively C1 alone.

## 3. Immediate action: reproduce the rare failures

Place `paper1_stage3_failure_trace.py` in the repo as `scripts/paper1_eqsdp/stage4_failure_trace.py` and run:

```bash
python scripts/paper1_eqsdp/stage4_failure_trace.py
```

This reads only the original sealed, checksum-verified development episodes 37 and 39 from `kc_311`, across ten original policy seeds, and replays `s3_candidate` and `s2armr_H1100` without modifying either policy or opening confirmation data. It writes per-seed cost/label/first-deployment summaries and a per-event timeline for the worst seed, including the gate's observed `p_cross`, threshold, skipped draws and virtual budget. Verify that rerun nets match the original Stage 3 records before drawing conclusions. *The script was syntax-checked but could not be run against local sealed data in this chat.*

Questions to answer using those traces:

1. Was the pivotal missed label rejected because of a low `p_cross`, a depressed virtual budget, or a time cutoff?
2. When did the candidate last receive an informative label before its delayed correct adoption? Compare with the simple reference's query/release times.
3. How many later labels were purchased after the gate had essentially starved itself?
4. Does the failure repeat across many seeds for the same episode, or is it a query-randomness outlier?
5. Is its detectable precursor available from **released** labels and prediction-only signals, or does it require unavailable future ground truth?

## 4. What to try next — in order

### R1: baseline + evidence-insurance floor (control, not novelty)

Start from `s2armr_H1100` and also `s2wald_l0.97_g0.2_H1100`. Introduce a strictly prospective minimum early query coverage on *eligible disagreement events*, plus a maximum gap between purchased informative disagreements before the cutoff. Only then allow selective suppression. Compare matched-cost or matched-query-count schedules. This tests whether the failure was due to information starvation. It is not an ICML-level new method on its own.

### R2: one-label economic value of information (candidate)

Replace block crossing probability by a preposterior estimate of **the incremental deployment regret prevented by acquiring the next label**. Include exact release time `t+d`, already pending observations as uncertain futures rather than observed evidence, the deployed model, remaining switching opportunities, query price, and budget shadow price. The baseline reference is the **same cutoff and same evidence engine**. Distinguish a one-step approximation from a genuine joint short-horizon rollout. Include a matched simple deadline-aware scheduler and matched one-step uncertainty/entropy baseline.

An example decision criterion (conceptual, not a calibrated algorithm yet) is to query when

\[
 c_q+\lambda_t < \mathbb E[J_{t+d:T}\mid\text{skip},s_t]-\mathbb E[J_{t+d:T}\mid\text{query},s_t].
\]

Here both expectations must integrate the *unseen* label and pending labels under an explicitly stated, stress-tested posterior, rather than using evaluator-side labels. A low probability of a decision change is insufficient: its **cost** is critical.

### R3: risk-aware query insurance (candidate)

Use a calibrated posterior predictive *upper-tail* measure of excess cost from skipping, such as CVaR on `J_skip - J_query`. Require both favorable expected economics and acceptable tail risk before withholding an offered baseline query. Maintain a simple sentinel coverage control to determine whether the new risk score adds anything. Stress-test calibration under temporal dependence and low challenger prevalence; any safety claim requires theory or independent calibration.

### R4: targeted deployment recovery (optional)

If trace evidence points to false promotion more than missed adoption, test a low-cost post-promotion check with reserved labels and a symmetric rollback option. Earlier C2/C5 mechanisms already tied simple controls; do not rerun those implementations under new names. Build only if new diagnostic evidence identifies a different mechanism.

## 5. Search methodology and stopping rules

Do **not** re-open Stage 3 as a confirmation test or retune the existing frozen winner after its failure. The nine original datasets (both parities) are now development-exposed. Other F/S/D datasets already opened in the branch are also development-exposed for a new method. Register entirely **new** chronological periods or different source organizations for a new, one-time held-out confirmation.

A small, testable, predeclared factorial experiment precedes Bayesian optimization:

- `cutoff-only` on EQSDp and on Wald (fair reference)
- `cutoff + coverage floor` and an equal-label-count calendar control
- `cutoff + one-label EVSI` and an equal-label-count uncertainty control
- `cutoff + EVSI + tail penalty` and each individual ablation
- if beneficial, a short joint rollout versus a cheap one-step approximation

Evaluate mean total cost, prediction loss per event, label/switch costs, late adoption, false promotion, paired **worst-dataset** mean and upper-tail (p95/p99 and CVaR95) of per-episode excess cost. The primary inference remains equal-dataset paired cost; tail metrics are safeguards, not replacements for mean cost. If Bayesian optimization is used, optimize on development only and account for best-of-N selection optimism.

An advance criterion for a *new* candidate must be declared before its final evaluation. Proposed criterion: lower paired mean J with interval excluding zero against both fairly tuned EQSDp+cutoff and Wald+cutoff, prediction error deterioration <= +0.1 pp, and no substantial degradation of a prespecified excess-loss tail statistic; identify meaningful losing subsets. A >=2% gain is a **research goal**, not an expectation or universal threshold. If there is no attributable improvement, close this method search; retain the reliable benchmark and corrected baselines for a narrower paper.

## 6. Research novelty

The components `hard cutoff`, `finite-horizon VOI`, `Bayesian optimal switching`, and `CVaR` all have prior art. A publishable new method would require a precise result specifically addressing the interaction of **hard paid-label budgets, delayed feedback, pending observations, reversible economic deployment, and tail losses**, with convincing gains over equally equipped Wald/EQSDp and simple controls. Do not claim that adding several known components is inherently novel.

## Source files

- [`14_STAGE3_SELECTION_CHECK.md`](https://github.com/nl2992/shiftlab/blob/3064006314be5dbac71aa573634d329fddc87015/docs/paper1_eqsdp/14_STAGE3_SELECTION_CHECK.md)
- [`13_STAGE2_FREEZE.md`](https://github.com/nl2992/shiftlab/blob/3064006314be5dbac71aa573634d329fddc87015/docs/paper1_eqsdp/13_STAGE2_FREEZE.md)
- [`stage1_policies.py`](https://github.com/nl2992/shiftlab/blob/3064006314be5dbac71aa573634d329fddc87015/scripts/paper1_eqsdp/stage1_policies.py)
- [`stage2_policies.py`](https://github.com/nl2992/shiftlab/blob/3064006314be5dbac71aa573634d329fddc87015/scripts/paper1_eqsdp/stage2_policies.py)

This protocol and trace utility were prepared externally because GitHub's connected write action returned HTTP 403. They have not been committed to the branch, and no new candidate result is being claimed.
