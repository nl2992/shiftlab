# SHIFTLAB: SOTA EXTENSION, HYBRID SEARCH AND NOVELTY DISCOVERY
## Autonomous Synthetic Research Programme — Revised Master Prompt

### ROLE AND OVERALL OBJECTIVE

You are an autonomous research team combining the expertise of:

- A senior machine learning researcher specializing in distribution shift.
- A sequential inference and statistical learning theorist.
- An active learning and decision-theoretic optimization researcher.
- A research software engineer.
- A skeptical empirical-methodology reviewer.

**Repository:** `https://github.com/nl2992/shiftlab`

**Source branch:** `research/rpoq-s1-fatal-flaw-audit`

**Research objective:** Systematically search modifications, extensions and hybrids of established state-of-the-art algorithms to discover measurable improvements in performance, accuracy, detection power, label efficiency, robustness, computational speed or intervention utility under distribution shift.

We are explicitly seeking methodological innovation through experimentation.

Do not require an entirely new theory before implementing a candidate. Do not abandon candidates simply because their components are established.

A meaningful contribution may be a carefully engineered improvement to an existing method, especially where it addresses a previously neglected failure mode.

The intended research process is:

**Existing SOTA → Systematic variation → Synthetic experiments → Complete result archive → Cross-method failure analysis → Targeted fix → New algorithm → Held-out validation → Research contribution.**

There are two outcomes we are pursuing:

**Outcome A: Measurable SOTA improvement.** Find an extension or hybrid that outperforms correctly implemented and tuned established methods in general performance, an important special case, computation time, sample efficiency or another justified metric.

**Outcome B: Stronger novelty through synthesis.** Use patterns observed across the *entire experimental archive* to identify a shared limitation of multiple methods and design a specific algorithmic correction that generalizes across settings.

Outcome B is the principal opportunity for a more substantial methodological contribution.

Do not assume either outcome is guaranteed. If the search is unsuccessful, preserve the evidence and report that precisely. The process must genuinely attempt algorithm discovery rather than devolve into an audit-only exercise.

**SCOPE RESTRICTION: SYNTHETIC DATA ONLY.**

Do not access CRSP, WRDS, Binance, financial market datasets, downloaded benchmark datasets, or any reserved real-data holdouts. A subsequent research phase will handle actual data after the synthetic findings are frozen.

---

# 1. ESTABLISH AN ISOLATED RESEARCH WORKSPACE

Fetch the latest branch refs and inspect the worktree.

Create a new branch from the current HEAD of `research/rpoq-s1-fatal-flaw-audit`:

`research/shiftlab-sota-synthetic-search-2026-10-29`

Use an independent Git worktree.

Preserve every pre-existing result and research conclusion.

Do not alter:

- `main`
- The existing RPOQ branch
- The risk-preserving approximation branch
- Historical output JSON
- Historical experiment protocols
- Previous negative-results records
- Previous scientific verdicts
- Protected validation or confirmation data

Record the starting SHA and verify the historical RPOQ outputs remain intact.

Fix reproducible CI and lint errors in the isolated branch, without modifying historical results or their provenance.

Create a branch-specific research directory:

```text
docs/sota_synthetic_search/
src/shiftlab/sota_search/
scripts/sota_search/
configs/sota_search/
tests/sota_search/
outputs/sota_search/
```

The new code should reuse existing ShiftLab infrastructure wherever possible.

---

# 2. THE THREE SHIFTLAB OBJECTIVES

Research should target three tasks separately and together where appropriate.

## Q1 — Harmful-shift detection

Determine whether the deployed model has become materially worse.

Evaluate:

- Harmful-shift detection power.
- False-alarm control.
- Detection delay.
- Cumulative harm before detection.
- Label requirements.
- Performance under benign distribution shifts.

We want algorithms that distinguish harmful changes from inconsequential distribution differences.

## Q2 — Replacement-model certification

Determine whether a candidate model is reliably better than the incumbent.

Evaluate:

- False promotion.
- Power to certify a superior candidate.
- Time to certification.
- Labels required.
- Paired-loss uncertainty.
- Multiple-model selection.
- Correct sequential validity where claimed.

## Q3 — Cost-aware intervention

Determine whether to acquire labels, recalibrate, retrain, switch, roll back or do nothing.

Evaluate:

- Cumulative regret.
- Prediction or decision utility.
- Label expenditure.
- Retraining expenditure.
- Switching and rollback costs.
- Policy stability.
- Post-reversal exposure.
- Computational cost.

Do not require a single algorithm to win all three tasks.

A substantial improvement in one task may be a valid contribution.

### Three separate performance dimensions

All synthetic generators must distinguish:

1. **Statistical distribution discrepancy:** how much the data distribution changes.
2. **Predictive deterioration:** how much prediction performance changes.
3. **Decision harm:** how much downstream utility deteriorates.

The benchmark must create examples in which these dimensions disagree.

For example, a large feature shift with no decision harm, or a subtle conditional shift that creates large downstream losses.

This distinction is central to our research programme.

---

# 3. OFFLINE-RESEARCH CONSTRAINT

### IMPORTANT: arXiv and some research websites are blocked in this environment.

Do not make the research programme dependent on successful access to arXiv, publisher websites or external PDF hosts.

The following information is supplied as the initial research specification.

Use sources in this priority order:

1. Existing ShiftLab source code, tests and paper-to-code audits.
2. Existing locally available research PDFs, implementations and reference files.
3. Already cached external repositories or locally installed dependencies.
4. The self-contained algorithm specifications in this prompt.
5. Online sources only if actually accessible.

Do not repeatedly retry blocked websites.

Do not fabricate details of inaccessible publications.

### Implementation provenance classes

Every baseline must have one of these labels:

**VERIFIED_REPRODUCTION:** Direct reproduction checked against a primary paper, official implementation or an existing validated repository implementation.

**FAITHFUL_ADAPTATION:** Verified key algorithmic operations, but adapted to a clearly different data or feedback contract.

**SOURCE_INSPIRED_BASELINE:** Mechanism consistent with published descriptions but not independently verified against the complete source.

**LOCAL_HEURISTIC:** A deliberately simplified comparator designed in this research programme.

**ORACLE_ONLY:** Uses inaccessible ground truth, future outcomes or data-generating parameters. May serve as a diagnostic reference, never as an implementable SOTA method.

Never call a source-inspired implementation a faithful reproduction.

If documentation is insufficient, implement the defined source-inspired comparator and continue the synthetic study. Record the missing verification obligation rather than halting all research.

Use locally available material to upgrade reproduction status when possible.

---

# 4. EXPLICIT SOTA BASELINE SPECIFICATIONS

The following methods are the minimum research starting set.

These descriptions provide the conceptual implementation contract, not a substitute for every detail of the original papers.

## A. Shift detection

### A1. MMD two-sample detection

**Source:** Gretton et al., JMLR 2012.

Use reference-window and current-window samples.

Compute a kernel maximum mean discrepancy statistic:

\[
\widehat{\mathrm{MMD}}^2
=
\frac{1}{n(n-1)}
\sum_{i\ne j}k(X_i,X_j)
+
\frac{1}{m(m-1)}
\sum_{i\ne j}k(Y_i,Y_j)
-
\frac{2}{nm}\sum_{i,j}k(X_i,Y_j).
\]

For independent samples, use an appropriate permutation or other justified calibration procedure.

Grid:

- Gaussian kernel bandwidth.
- Window size.
- Linear versus quadratic estimator.
- Fixed versus adaptive reference.
- Single versus multiple bandwidths.

**Strength:** Detects generic distribution differences.

**Weakness:** A distribution difference need not imply predictive degradation or decision harm.

Do not transfer IID permutation validity directly to serially dependent streams.

### A2. C2ST

**Source:** Lopez-Paz and Oquab, 2017.

Train a classifier to distinguish source from target samples. Evaluate discrimination on independent held-out samples.

Grid:

- Logistic regression versus shallow nonlinear classifier.
- Window sizes.
- Calibration methods.
- Feature subsets.
- Classifier regularization.

Compare held-out discrimination, alarm quality and runtime.

Avoid training/test reuse and invalid repeated-testing claims.

### A3. BBSD / Failing Loudly

**Source:** Rabanser et al., NeurIPS 2019.

Apply distribution-shift tests to the deployed classifier's predicted probabilities or related prediction representations, rather than only raw features.

Grid:

- Predicted class versus probability vector.
- Univariate versus joint tests.
- Multiple-testing correction.
- Window size.
- Representation dimension.

Include benign feature shifts and harmful shifts that may be small in the model's output distribution.

### A4. ADWIN, CUSUM, Page–Hinkley and BOCPD

Implement separate, clearly defined classical baselines.

For CUSUM, a representative one-sided statistic is:

\[
S_t=\max\{0,S_{t-1}+U_t-\kappa\}.
\]

Alarm when \(S_t\ge h\).

Grid drift allowance, reference estimation, thresholds, forgetting and restart rules.

For BOCPD, maintain a run-length posterior under an explicit hazard model.

These are strong low-compute baselines.

Their thresholds must be calibrated to the declared false-alarm metric, especially under repeated monitoring and dependency.

### A5. Podkopaev–Ramdas harmful-risk monitoring

**Source:** *Tracking the Risk of a Deployed Model and Detecting Harmful Distribution Shifts*, ICLR 2022.

The central task is detecting increases in a deployed model's risk rather than arbitrary feature-distribution change.

Implement a sequential risk-tracking procedure using labeled or delayed-labeled observations, a nominal-risk reference and a source-appropriate time-uniform confidence mechanism.

Compare against simple empirical-risk monitoring, CUSUM and PPRM.

Keep the method's specific assumptions and guarantee distinct from exchangeability-based conformal methods.

### A6. WATCH

**Source:** Prinster, Han, Liu and Saria, ICML 2025.

Full title: *WATCH: Adaptive Monitoring for AI Deployments via Weighted-Conformal Martingales*.

Core architecture:

- Construct sequential conformity/nonconformity evidence.
- Apply a weighting scheme to accommodate specified covariate-shift behavior.
- Accumulate evidence with a conformal test martingale.
- Support monitoring and diagnosis of relevant changes.

Searchable extension dimensions:

- Weight estimation.
- Adaptive calibration windows.
- Weight clipping.
- Multi-scale conformity scores.
- Score aggregation.
- Drift-sensitive reference updates.
- Selective reweighting for benign covariate shifts.

A simplified weighted-conformal implementation must be labeled source-inspired unless the exact published construction and guarantees have been checked.

Do not assume reweighting preserves validity under arbitrary concept drift.

### A7. PPRM

**Source:** Zhang, Cai, Yu and Simeone, ICML 2026.

Full title: *Prediction-Powered Risk Monitoring of Deployed Models for Detecting Harmful Distribution Shifts*.

Core architecture:

- Use proxy or synthetic labels to estimate risk.
- Correct proxy errors using available real labels.
- Construct sequential risk bounds.
- Detect harmful deterioration by comparing risk evidence with the nominal-risk benchmark.

For a bounded risk observation \(R_t\), an implementable prediction-powered building block under independent predictable querying is:

\[
\widetilde R_t
=
\widehat R_t+
\frac{Q_t}{q_t}(R_t-\widehat R_t).
\]

Here \(\widehat R_t\) and \(q_t\) must be available before the current true outcome is revealed.

This unbiased correction is a starting building block; it is not the complete published PPRM algorithm.

The selected confidence-sequence or e-process construction must be implemented and validated separately.

Search:

- Proxy correction models.
- Risk-bound construction.
- Query allocation.
- Sequential aggregation.
- Reference-risk estimation.
- Multiple risk definitions.
- Adaptation after detected drift.

PPRM is a primary Q1 comparator.

### A8. Prediction-Powered E-Values

**Source:** Csillag, Struchiner and Goedert, ICML 2025.

Construct e-values or e-processes using prediction-powered corrections, respecting the stated null and filtration.

Use the existing ShiftLab implementation and paper-to-code audits where available.

For the specific bounded conditional-mean setting, a possible local construction is:

\[
E_t=\prod_{s=1}^{t}(1+\lambda_s X_s),
\]

with \(X_s\) a correctly constructed, null-centered prediction-powered increment and nonnegative factors.

This is a particular betting-e-process candidate, not an assertion that it reproduces the entire paper.

Search betting fractions, mixture strategies, predictable adaptation, reset rules and multiple horizons.

Null calibration and nonnegativity are mandatory.

---

## B. Model comparison and certification

### B1. Paired sequential confidence sequences

Use paired loss differences:

\[
D_t=\ell(f_{\mathrm{inc}},Y_t)-\ell(f_{\mathrm{cand}},Y_t).
\]

Positive \(D_t\) means the candidate is better.

For bounded differences under a suitable conditional-mean null, construct a valid betting or confidence-sequence procedure.

Measure certification power, first-crossing delay, label cost and false-promotion probability.

Include a source-matched version of Choe–Ramdas sequential forecaster comparison where feasible.

### B2. Sequential Model Confidence Sets

Use the 2026 *Sequential Model Confidence Sets* methodology as a source target.

Maintain a set of models not yet eliminated by sequential evidence.

Compare:

- Pairwise testing.
- Multiple-testing corrections.
- E-process-based elimination.
- Different model multiplicities.
- Shared-label versus individually allocated observations.

The original method's time-uniform coverage must not be claimed for a simplified implementation without checking its construction.

### B3. Prediction-powered paired certification

Adapt the prediction-powered risk/e-value correction to a paired economic loss contrast.

Both candidate and incumbent may use the same revealed label.

Search:

- Proxy quality.
- Difference-prediction quality.
- Shared-label budget.
- Growth-aware query selection.
- Multiple challenger policies.
- Conservative risk allocation.

This is a promising hybrid search family, not a presumed novel invention.

### B4. Contextual Active Model Selection (CAMS)

**Source:** Liu, Xia, Stevens and Chen, NeurIPS 2024.

Core task:

- Observe context.
- Choose among candidate predictors.
- Decide when to request the true label.
- Update model-selection information from observed feedback.
- Minimize prediction regret and label expenditure.

The original provides contextual model-selection and active-query components with regret/query analysis.

Search modifications to query scores, budget pacing, delayed updates, model multiplicity and switching penalties.

Use existing ShiftLab delayed-CAMS adapters, but distinguish them from the source implementation.

---

## C. Query allocation and intervention

### C1. Active Statistical Inference (ASI)

**Source:** Zrnic and Candès, ICML 2024.

Use predictor-assisted estimates and unequal-probability querying to obtain more informative labels within a fixed budget.

For a target mean, a representative correction is:

\[
\widehat\theta
=
\frac1n\sum_{i=1}^n
\left[
H_i+\frac{Q_i}{q_i}(Y_i-H_i)
\right].
\]

Residual-variance allocation has the familiar candidate form:

\[
q_i\propto \sqrt{
\mathbb E[(Y_i-H_i)^2\mid X_i]
},
\]

subject to actual sampling-design constraints.

Implement:

- Uniform sampling.
- Classical ASI allocation.
- Online/sequential ASI where source support is available.
- A fixed-predictor ablation.
- A learned residual-variance model.

Evaluate estimator accuracy and confidence-interval behavior separately from sequential e-value growth.

### C2. Robust Sampling for ASI

**Source:** Li, Zrnic and Candès, NeurIPS 2025.

Core objective: protect estimator efficiency against inaccurate uncertainty scores.

The published approach uses robust sampling and interpolation between active and uniform allocation.

Its stated variance-efficiency property concerns the paper's estimator and assumptions, not arbitrary sequential wealth or detection power.

Implement the source-supported robust allocation if code/theory is available locally.

Otherwise construct an explicitly labeled interpolation baseline:

\[
q_i(\varepsilon)=
\varepsilon q_i^{\mathrm{uniform}}
+(1-\varepsilon)q_i^{\mathrm{active}}.
\]

Search \(\varepsilon\), uncertainty reliability models and budget constraints.

Do not claim the paper's dominance guarantee for this simplified mixture.

### C3. Pro-Active Inference (PAI)

**Source:** Wu, Nair, Maechler and Candès, October 2026 preprint.

Core setting:

- An unlabeled covariate pool is available.
- The learner selects observations for labeling without replacement.
- Predictions and uncertainty estimates may update after labels arrive.
- Statistical estimation remains the principal objective.

Implement pool-aware adaptive selection and update loops, with proper inclusion-probability accounting.

Compare against:

- Uniform without replacement.
- Batch ASI.
- Sequential ASI.
- Robust ASI.
- Fixed-predictor PAI ablation.

The pool-access assumption is essential.

Do not permit PAI to inspect future covariates in an otherwise strictly streaming comparison unless every competitor has the same information.

### C4. Balanced Active Inference

**Source:** Chen, Zhou, Peng and Wang, NeurIPS 2025.

Core idea: use balanced sampling constraints, including cube-method principles, to improve the efficiency of active label acquisition.

Possible extensions:

- Approximate balancing.
- Faster balancing.
- Cost-aware balance constraints.
- Dynamic balancing targets.
- Delayed label updates.
- Combining uncertainty and balancing constraints.

Use a verified implementation where available. An independent approximate-balancing heuristic is not automatically equivalent to the paper's algorithm.

### C5. Prediction-powered active monitoring under a hard budget

Reuse ShiftLab's RPOQ solver, delayed evidence machinery and exact risk verifiers.

A local algorithm can choose predictable \(q_t\) to improve future sequential decision performance rather than merely minimize estimator variance.

Search log-wealth growth, detection power and budget-aware lookahead.

Keep this algorithm family separate from classical ASI inference claims.

### C6. Cost-aware switching and model adaptation

Strong references:

- Frozen model.
- Periodic retraining.
- Rolling-window recalibration.
- Detection-triggered retraining.
- Hysteresis-based switching.
- Evidence-certified switching.
- CAMS-derived model selection.
- Existing ShiftLab exact first-promotion optimizer.
- Existing risk-preserving approximation methods.

Compare actual net decision loss including all intervention costs.

The exact solver is a small-instance oracle, not a computationally competitive baseline at every horizon.

---

# 5. PRIMARY ALGORITHMIC CANDIDATES TO SEARCH

Do not generate random combinations without a clear interpretation.

Start with the following twelve candidate families. Each has a defined parent algorithm, proposed modification, predicted benefit and failure regime.

These are hypotheses, not pre-established improvements.

## Candidate S01 — Decision-Harm-Aware PPRM

**Parents:** PPRM + paired decision-cost monitoring.

**Modification:** Replace or augment predictive risk monitoring with a bounded downstream decision-loss signal.

**Hypothesis:** A monitor tailored to decision harm will alarm earlier when a small predictive change creates severe economic losses, while ignoring benign shifts.

**Primary metric:** Cumulative harm before alarm at matched false-alarm control.

**Relevant stress case:** Small global accuracy change, large asymmetric decision loss.

**Comparators:** PPRM, labeled risk-monitoring CS, Podkopaev–Ramdas, WATCH adaptation, CUSUM.

**Failure test:** No benefit after controlling for the information and label access required to construct downstream loss.

## Candidate S02 — Multi-Resolution Sequential Risk Monitoring

**Parents:** PPRM or valid e-process + multiple temporal scales.

**Modification:** Combine short-, medium- and long-horizon evidence with predetermined or predictably chosen mixture weights.

Example:

\[
E_t^{\mathrm{mix}}
=
\sum_{j=1}^{J}w_jE_t^{(j)},
\quad w_j\ge0,\quad\sum_jw_j=1.
\]

Only use this as a validity-preserving e-process mixture when each constituent and the weighting scheme satisfy the necessary requirements.

**Hypothesis:** Better detection across unknown shift durations.

**Primary metric:** Worst-onset detection delay at matched false alarm.

**Stress cases:** Abrupt, gradual, transient and recurring changes.

**Comparators:** Best single-window baseline, e-mixtures, CUSUM, BOCPD, WATCH.

**Failure test:** Gains disappear against a properly tuned multi-scale or restart mixture already available in prior art.

## Candidate S03 — Proxy-Reliability-Adaptive Risk Monitoring

**Parents:** PPRM + Robust ASI-style uncertainty assessment.

**Modification:** Track predictable proxy reliability and adapt the degree of reliance on predictions.

**Hypothesis:** Less deterioration when prediction models suddenly become biased or anti-informative.

**Primary metric:** Detection power/label cost under proxy misspecification.

**Stress cases:** Accurate proxy before shift, stale or biased proxy afterward.

**Comparators:** PPRM with fixed proxy, source-supported robust allocation, uniform-label monitor.

**Failure test:** Reliability estimation lags behind the shift or invalidates the monitor's filtration.

## Candidate S04 — Growth-Aware Active Querying

**Parents:** ASI + prediction-powered betting.

**Modification:** Allocate labels to improve expected sequential evidence growth rather than solely estimator variance.

A candidate local objective:

\[
g_t(q)
=
\mathbb E_{\widehat P_t,Q_t}
[
\log(1+\lambda_t X_t(q,Q_t))
].
\]

Optimize \(q_t\) over a feasible grid using only the predictive distribution estimated from available information.

**Hypothesis:** Better power or detection delay at the same query budget.

**Stress cases:** Highly heterogeneous residuals, informative proxy, rare decisive observations.

**Comparators:** Uniform, ASI, Robust ASI, local evidence-directed PPI, best fixed query table, exact RPOQ oracle.

**Failure test:** The gain is only from a better-tuned betting fraction or disappears on unseen alternatives.

## Candidate S05 — Robust Growth/Variance Hybrid

**Parents:** Robust ASI + growth-aware querying.

**Modification:** Combine variance-reduction and sequential-growth scores, with a reliability-dependent uniform fallback.

Example candidate family:

\[
q_t =
w_{u,t}q_t^{u}
+w_{v,t}q_t^{v}
+w_{g,t}q_t^{g}.
\]

All weights must be predictable and produce feasible inclusion probabilities.

**Hypothesis:** Preserve growth-aware gains when predictive scores are reliable, while reducing damage from poor scores.

**Primary metric:** Power/label-efficiency Pareto frontier.

**Stress cases:** Heterogeneous proxy reliability and abrupt predictive model deterioration.

**Comparators:** Optimally tuned Robust ASI, ASI, growth-only sampler, uniform, and simpler two-way mixtures.

**Failure test:** Strong robust ASI already matches or beats the hybrid.

## Candidate S06 — Budget-Paced Delayed Query Allocation

**Parents:** Sequential ASI/PAI-inspired allocation + hard-budget control.

**Modification:** Incorporate remaining horizon, pending labels, remaining budget and expected value of future labels into propensity selection.

**Hypothesis:** Reserve labels for informative periods instead of exhausting the budget too early.

**Primary metric:** Decision quality or evidence power per hard-budget unit.

**Stress cases:** Long delays, late shift onset, rare informative contexts.

**Comparators:** Uniform pacing, fixed ASI, Robust ASI, source-matched delayed allocation and exact RPOQ where available.

**Failure test:** Benefit disappears against a correctly tuned budget-aware sampling baseline.

## Candidate S07 — PAI With Robust Uncertainty Updates

**Parents:** Pro-Active Inference + Robust ASI.

**Modification:** Combine without-replacement pool selection with conservative uncertainty-score updates and predictive reliability checks.

**Hypothesis:** Improve PAI's behavior when early residual estimates are inaccurate.

**Primary metric:** Estimation error or confidence interval width at matched label count and coverage.

**Stress cases:** Small initial labeled sample, heterogeneous residuals, poorly estimated uncertainty.

**Comparators:** Original PAI, uniform without replacement, batch/sequential ASI, Robust ASI.

**Failure test:** Modification introduces no advantage over PAI with standard validation tuning.

## Candidate S08 — Balanced Growth-Aware Sampling

**Parents:** Balanced Active Inference + growth-aware allocation.

**Modification:** Optimize evidence-growth scores subject to balancing constraints.

**Hypothesis:** Better use of scarce labels in heterogeneous groups while avoiding overconcentration.

**Primary metric:** Estimator accuracy or sequential power at matched labels, depending on the declared task.

**Stress cases:** Severe group imbalance and localized harmful shifts.

**Comparators:** Balanced Active Inference, ASI, growth-aware sampling, stratified uniform.

**Failure test:** Balancing consumes the gain or the improvement depends on privileged group information.

## Candidate S09 — Selective Model Certification Under Shift

**Parents:** Sequential model confidence sets + CAMS + prediction-powered paired evidence.

**Modification:** Use context-aware label acquisition to accelerate confidence-based elimination or certification of models.

**Hypothesis:** Fewer labeled observations are needed to select a superior model.

**Primary metric:** Labels to correct certification at controlled false-promotion probability.

**Stress cases:** Several near-tied models, regime-dependent model ranking, sparse feedback.

**Comparators:** Standard sequential model confidence sets, CAMS, uniform paired certification, established multiple-testing procedures.

**Failure test:** No improvement after correcting for additional label or context information.

## Candidate S10 — Reversal-Aware Evidence-Certified Switching

**Parents:** Sequential certification + existing ShiftLab switching policy.

**Modification:** Maintain separate statistical evidence for historical candidate superiority and an economic monitoring state for current regime value.

Add hysteresis, rollback and budget reservation.

**Hypothesis:** Less post-reversal harm and fewer unnecessary switches.

**Primary metric:** Net cumulative regret, including all costs.

**Stress cases:** Recurrent regimes, rapid reversals, expensive rollback.

**Comparators:** Frozen, periodic, CUSUM-triggered, simple evidence-certified switching and exact small-instance oracle.

**Failure test:** Improvement is explained entirely by a standard switching-cost threshold or extra feedback.

## Candidate S11 — Amortized Approximation to Exact Querying

**Parents:** RPOQ exact DP + approximate policy optimization.

**Modification:** Generate exact optimal decisions on small synthetic worlds and train an approximate policy that maps observable information states to actions.

Potential representations:

- Decision tree.
- Small finite-state controller.
- Shallow neural policy.
- Short-horizon rollout.
- Quantized belief/value lookup.

**Hypothesis:** Large computational savings with small power or decision-value loss.

**Primary metric:** Oracle gap versus end-to-end runtime and memory.

**Stress cases:** Longer horizons, moderate delays, multiple budget levels and unseen synthetic model parameters.

**Comparators:** Exact RPOQ DP, approximate DP, standard finite-state-controller baselines, simple heuristics.

**Failure test:** The approximate policy only works on parameters included in its training distribution.

## Candidate S12 — Efficient Multi-Scale Shift Detection

**Parents:** MMD/C2ST + lightweight sequential detection.

**Modification:** Kernel sketches, random features, incremental statistics, early-exit tests or adaptive representation selection.

**Hypothesis:** Comparable shift detection with materially lower runtime and memory.

**Primary metric:** Detection performance at matched false-alarm rate versus compute.

**Stress cases:** High-dimensional features, high event rates, moderate sample windows.

**Comparators:** Exact MMD, standard C2ST, efficient approximate MMD, BBSD.

**Failure test:** The apparent speedup is due only to implementation language or excludes preprocessing.

---

# 6. EXTRA CANDIDATES GENERATED FROM EXPERIMENTAL RESULTS

The twelve candidates above are the initial search space, not its final boundary.

The agent is allowed to generate additional candidates from observed development failures.

However, every additional candidate must specify:

1. Parent SOTA method.
2. Exact modification.
3. Targeted failure mechanism.
4. Predicted direction of improvement.
5. Appropriate matched baseline.
6. Primary metric.
7. Cost of the modification.
8. Conditions under which it should fail.
9. A falsification experiment.

Do not introduce a candidate solely because one random parameter combination performed well.

---

# 7. SYNTHETIC GENERATOR DESIGN

Implement four independent generator families.

## G1 — Controlled parametric shifts

Gaussian/logistic classification or regression.

Vary:

- Mean and covariance.
- Class prior.
- Decision boundary.
- Feature-label dependence.
- Noise and missingness.
- Covariate versus concept shift.
- Predictive calibration.
- Benign versus harmful shift.

## G2 — Nonlinear heterogeneous shifts

Nonlinear classification/regression with:

- Informative and nuisance features.
- Spurious correlations.
- Group heterogeneity.
- Imbalanced subpopulations.
- Nonlinear loss surfaces.
- Rare high-cost errors.
- Proxy misspecification.
- Support mismatch.

## G3 — Sequential regime shifts

HMM/Markov-switching data with:

- Abrupt changes.
- Gradual changes.
- Persistent regimes.
- Transient shifts.
- Recurrence.
- Multiple change points.
- Autocorrelation.
- Sparse and delayed outcomes.
- Regime-dependent predictor rankings.

## G4 — Synthetic finance-oriented decisions

Simulate:

- Time-varying predictive alpha.
- Volatility regimes.
- Heavy-tailed returns.
- Sign reversals.
- Signal degradation.
- Position-dependent costs.
- Transaction/switching costs.
- Asymmetric tail losses.
- Multiple competing predictors.

Use synthetic ground truth to calculate decision regret.

Do not claim real-world trading profitability.

### Required shift combinations

Each generator should produce examples where:

- Distribution discrepancy is large but harm is small.
- Distribution discrepancy is small but harm is large.
- Prediction risk increases but decision loss does not.
- Decision loss increases despite nearly unchanged average accuracy.
- The incumbent remains best after a shift.
- A challenger becomes best only temporarily.
- A previously inferior challenger becomes optimal.
- No model is reliably superior.
- Acquiring extra labels is more expensive than the value gained.

All algorithms must receive only information allowed under their declared feedback contract.

---

# 8. SEARCH SPACE AND GRID CONSTRUCTION

The purpose is extensive controlled experimentation.

Search over compatible algorithms and meaningful parameter variations.

### Evidence aggregation

```text
windows = [16, 32, 64, 128, 256]
ewma = [0.90, 0.95, 0.98, 0.995]
aggregation = [
  single_window,
  multi_window,
  exponential,
  changepoint_reset,
  predictable_mixture
]
```

### Acquisition

```text
budget_fraction = [0.01, 0.05, 0.10, 0.20]
temperature = [0.25, 0.5, 1.0, 2.0]
uniform_mixture = [0, 0.10, 0.25, 0.50, 0.75, 1.0]
query_score = [
  residual_variance,
  predictive_uncertainty,
  expected_growth,
  disagreement,
  estimated_decision_harm,
  mixed_score
]
```

### Feedback

```text
delay = [0, 1, 5, 20]
delay_model = [
  fixed,
  outcome_independent_random,
  outcome_dependent
]
```

### Intervention

```text
lookahead = [1, 2, 4, 8]
switch_cost = [0, 0.01, 0.05, 0.20]
hysteresis = [0, 0.01, 0.05, 0.10]
rollback = [disabled, evidence_gated, cost_aware]
```

### Predictor/proxy conditions

```text
proxy_quality = [
  excellent,
  moderate,
  weak,
  miscalibrated,
  stale,
  anti_informative
]

shift_type = [
  covariate,
  label_prior,
  concept,
  mixed,
  subgroup,
  recurrent
]
```

Use only parameters compatible with the algorithm and benchmark setting.

### Search execution

Do not execute the full Cartesian product.

Begin with approximately 500–1,500 valid configurations across the research tracks, subject to explicit resource limits.

Use staged screening and successive halving.

Keep high-performing candidates and candidates showing credible special-case benefits.

Preregister the screening metric and survival rule.

Maintain separate development and confirmation synthetic worlds.

---

# 9. BASELINE FAIRNESS

Every finalist must be compared with:

1. Its original parent SOTA method.
2. The best tuned parent under the same information and compute budget.
3. A strong simple baseline.
4. The strongest relevant alternative method from a different family.
5. An appropriate exact oracle when tractable.
6. Any obvious simpler version of the proposed modification.

Do not compare a tuned new algorithm against a poorly tuned or default-only SOTA baseline.

Track total training, tuning, updating, inference, querying and verification costs.

Methods using different observation sets or incompatible statistical nulls must be placed into clearly separated experimental contracts.

For example:

- PAI with access to a full unlabeled pool is not equivalent to strict streaming acquisition.
- MMD and C2ST measure generic shift, not necessarily harmful risk.
- An estimator-variance guarantee is not an e-process power guarantee.
- Predictive accuracy improvements are not necessarily economic improvements.
- A fixed-horizon confidence interval is not automatically an anytime-valid confidence sequence.

A comparison may still be useful, but the claim must reflect the actual contract.

---

# 10. RECORD EVERY EXPERIMENT

This is a mandatory component of the project.

Create an append-only machine-readable experiment database.

SQLite or Parquet is acceptable.

Every attempted configuration must have a record, including failures, aborted jobs and invalid configurations.

Required fields:

```text
run_id
parent_algorithm
candidate_algorithm
modification_id
component_configuration
hyperparameters
generator_family
shift_type
shift_magnitude
predictive_degradation
decision_harm
proxy_quality
delay_model
label_budget
cost_configuration
random_seed
code_commit
source_hash
configuration_hash
baseline_version
execution_status
failure_reason
validity_status
primary_metric
secondary_metrics
uncertainty_estimates
runtime
peak_memory
labels_used
artifacts
```

A failed run is not to be deleted.

Distinguish:

- Scientifically negative.
- Statistically inconclusive.
- Numerically invalid.
- Inference-invalid.
- Computational timeout.
- Implementation defect.
- Unsupported experimental contract.

Store raw per-world and per-seed results where feasible, alongside aggregate metrics.

Create an experiment manifest before each major batch.

Do not overwrite outputs during reruns.

Use unique run identifiers and immutable result snapshots.

Preserve historical ShiftLab artifacts separately.

---

# 11. FIRST-STAGE PERFORMANCE ANALYSIS

After initial screening and focused tuning, report the strongest algorithms separately for Q1, Q2 and Q3.

Classify results into:

### Global improvements

Algorithms outperforming relevant SOTA across multiple settings.

### Conditional improvements

Algorithms that reliably outperform in a defined shift regime.

### Resource improvements

Algorithms achieving similar performance at lower labeling or computational cost.

### Robustness improvements

Algorithms with smaller deterioration under unfavorable conditions.

### Pareto improvements

Algorithms offering a superior balance of detection, accuracy, labels, runtime or intervention cost.

Do not select only one overall winner.

Construct performance surfaces as functions of:

- Shift severity.
- Predictive degradation.
- Decision harm.
- Proxy reliability.
- Budget.
- Delay.
- Intervention cost.
- Horizon.
- Dimension.
- Regime persistence.

Report paired differences and uncertainty, not only raw mean scores.

A claimed improvement must survive appropriate held-out synthetic evaluation.

---

# 12. SECOND-STAGE CROSS-EXPERIMENT SYNTHESIS
## THE CRITICAL NOVELTY-DISCOVERY PHASE

**This phase is mandatory. It must not be skipped even if a first-stage candidate already appears to outperform SOTA.**

The purpose is to analyze the entire experiment archive and find systematic opportunities for a more fundamental algorithmic improvement.

Do not simply produce a leaderboard.

We need to discover **common failure mechanisms** across existing algorithms.

### 12.1 Construct a cross-method failure matrix

For each baseline and candidate, identify the regimes in which it fails.

Examples:

| Failure pattern | Possible shared explanation |
|---|---|
| Several active samplers lose to uniform under noisy proxies | Allocation scores are unreliable |
| Multiple risk monitors detect benign shifts | Scores are not sufficiently decision-relevant |
| Detectors miss small high-harm shifts | Global shift scores obscure costly local failures |
| Adaptive sampling exhausts labels before late shifts | Budget pacing ignores future information value |
| Multiple monitors react slowly to short shifts | Evidence aggregation has an unsuitable time scale |
| Switching algorithms lose after reversals | Historical promotion evidence is confused with current economic value |
| Approximate controllers are fast but lose utility | State abstraction omits decision-relevant information |
| Sequential tests lose power under delay | Delayed observations create evidence-timing inefficiency |

These are possible patterns, not assumed findings.

Use actual experimental measurements to determine which occur.

### 12.2 Quantify each failure pattern

For every proposed shared weakness, record:

- Number of affected methods.
- Independent parent algorithm families affected.
- Generator families affected.
- Magnitude and uncertainty of performance deterioration.
- Important scenario parameters.
- Whether the effect persists after tuning.
- Whether simple controls already resolve it.
- Whether it results from invalid assumptions or an actual methodological weakness.

Use stratified paired comparisons, regression/meta-models and interpretable effect plots where appropriate.

Do not mistake an implementation bug for a novel statistical phenomenon.

### 12.3 Cluster failure modes

Identify groups of algorithms that fail for the same reason.

Possible categories:

- Proxy-estimation failure.
- Temporal evidence aggregation failure.
- Budget-allocation failure.
- Delayed-feedback failure.
- Model-selection multiplicity failure.
- Cost-blind decision failure.
- Nonstationarity or reversal failure.
- Calibration failure.
- Computational scaling failure.

Create an evidence-backed taxonomy.

### 12.4 Identify the shared missing mechanism

For each credible failure cluster, ask:

**What is one algorithmic change that could correct this shared weakness across several existing methods?**

The best research ideas should emerge from this question.

For example:

If PPRM-derived monitors and prediction-powered e-processes both lose power with stale proxies, investigate whether a common predictable reliability mechanism improves both.

If growth-aware and variance-aware samplers both waste labels during late-onset shifts, investigate a shared budget-reservation policy.

If WATCH-style and risk-based monitoring struggle with different shift time scales, investigate a valid and computationally efficient multi-resolution evidence mechanism.

If multiple switching methods exhibit reversal losses, investigate a shared policy that separates historical test evidence from current regime value.

These examples are hypotheses only.

### 12.5 Rank potential fixes

For each proposed common fix, estimate:

- Number of distinct SOTA methods it could improve.
- Importance of the affected use case.
- Size of observed performance gap.
- Likelihood of improving held-out synthetic performance.
- Computational cost.
- Effect on statistical validity.
- Novelty relative to known combinations.
- Feasibility of obtaining a theoretical explanation.

Select no more than three high-priority fixes.

Write:

`docs/sota_synthetic_search/COMMON_FAILURES_AND_NOVELTY_OPPORTUNITIES.md`

This document must be grounded directly in the full experiment registry.

---

# 13. THIRD-STAGE NOVELTY-DRIVEN ALGORITHM DEVELOPMENT

For each selected shared failure, construct one targeted algorithmic repair.

The repair must have a precise mechanism and falsifiable hypothesis.

Examples of possible repair types:

- A common proxy-reliability gate shared by several monitoring methods.
- A budget-aware query-value approximation that can be added to several existing samplers.
- A decision-harm-sensitive score compatible with multiple sequential detectors.
- A lightweight multi-resolution evidence aggregator.
- A hybrid combining robust uncertainty sampling with growth-aware selection.
- A compact policy approximator retaining essential delayed-feedback information.
- A source-compatible correction to an approximation that fails under recurrent regimes.

### Required comparison

For every proposed fix, evaluate:

1. Original SOTA method A.
2. Original SOTA method B.
3. A with the fix.
4. B with the fix.
5. The full proposed hybrid where appropriate.
6. A simpler alternative fix.
7. The strongest matched external comparator.
8. The relevant exact oracle or diagnostic ceiling.

A fix that improves two genuinely different parent methods is more interesting than one that only tunes a single implementation.

But cross-parent improvement is not itself proof of novelty.

### Mechanistic ablation

Remove components individually.

Determine whether the observed benefit comes from:

- The new score.
- The new allocation rule.
- The new state representation.
- The new weighting method.
- The new decision criterion.
- Additional computation.
- Better tuning.
- Additional information.

Reject claims whose apparent advantage disappears after fair resource and information matching.

---

# 14. VALIDATE THE FIX ON UNSEEN SYNTHETIC WORLDS

Use a separate final confirmation pool.

Do not select the fix using confirmation outcomes.

The final synthetic evaluation must include:

- Generator families not used to choose the fix.
- Different shift magnitudes.
- Different change-point positions.
- Different proxy qualities.
- Different delay distributions.
- Different budgets.
- Different cost levels.
- Different random seeds.
- More than one statistical or decision-loss metric.

When possible, create a **held-out generator-family test** rather than only changing the seed.

This is essential for establishing that a candidate has learned a general algorithmic principle rather than exploiting one synthetic distribution.

The agent must explicitly evaluate:

**Does the fix improve more than one original SOTA method?**

**Does it improve a meaningful subset of scenarios?**

**Does it degrade performance elsewhere?**

**Is the improvement statistically credible?**

**Does it preserve the guarantees claimed for the original method?**

**Is the computational overhead justified?**

A strong special-case result is acceptable if the special case is specified before final confirmation and the loss elsewhere is accurately reported.

---

# 15. THEORETICAL ANALYSIS AFTER EMPIRICAL DISCOVERY

Do not demand a new theorem before every experiment.

Once a candidate demonstrates a credible improvement, investigate the mechanism mathematically.

Potential theoretical results include:

- An optimal or approximately optimal score under specified assumptions.
- A regret or excess-cost bound.
- A power improvement in a restricted alternative family.
- A bound on the effect of proxy misspecification.
- A value bound for budget-aware lookahead.
- A sufficient condition under which a hybrid is preferable.
- A complexity improvement.
- A null-validity theorem.
- An impossibility or lower bound explaining a shared failure.

Classify proof status precisely.

A mathematically narrow but useful result is preferable to an unsubstantiated universal claim.

The key distinction:

**A tuned method with favorable results is an empirical improvement.**

**A new algorithmic mechanism with reproducible superiority and a defensible theoretical or structural distinction is a stronger methodological contribution.**

Do not confuse these categories.

---

# 16. REQUIRED RESEARCH REPORTS

Create the following completed artifacts as the work progresses:

```text
docs/sota_synthetic_search/
    00_BASELINE_AND_BRANCH_MANIFEST.md
    01_SOTA_ALGORITHM_REGISTRY.md
    02_SYNTHETIC_GENERATOR_CONTRACT.md
    03_SEARCH_SPACE_AND_PREREGISTRATION.md
    04_BASELINE_REPRODUCTION.md
    05_INITIAL_GRID_RESULTS.md
    06_TUNED_CANDIDATE_RESULTS.md
    07_PERFORMANCE_AND_PARETO_ANALYSIS.md
    08_COMMON_FAILURES_AND_NOVELTY_OPPORTUNITIES.md
    09_NOVELTY_FIX_DESIGNS.md
    10_FIX_ABLATIONS.md
    11_HELDOUT_SYNTHETIC_CONFIRMATION.md
    12_THEORY_AND_VALIDITY.md
    13_FINAL_ALGORITHM_COMPARISON.md
    14_REAL_DATA_HANDOFF.md
    RESEARCH_LEDGER.md
```

The final report must include two separate leaderboards.

### Leaderboard A — Empirically improved methods

Report:

- Method and SOTA parent.
- Modification.
- Winning metric.
- Shift regimes where it wins.
- Baselines beaten.
- Statistical uncertainty.
- Computational overhead.
- Generalization results.
- Whether the method retains its intended validity.

### Leaderboard B — Novelty-driven fixes

Report:

- Common failure discovered.
- Evidence that multiple algorithms share it.
- Proposed mechanism.
- Parent methods improved.
- Ablation evidence.
- Held-out generalization.
- Mathematical explanation or theorem status.
- Closest existing research.
- Whether the contribution is a new algorithm, meaningful extension, hybrid or primarily an engineering result.

If there is no confirmed winner in either category, report this clearly and preserve the best exploratory candidates.

---

# 17. EXECUTION DISCIPLINE AND AUTONOMY

The agent should actively implement and run experiments, rather than repeatedly returning plans.

Within this synthetic-only research branch, proceed through:

1. Repository and CI verification.
2. Baseline implementation and reproduction.
3. Synthetic generator construction.
4. Controlled combinatorial search.
5. Candidate tuning on development data.
6. Held-out confirmation of initial improvements.
7. Full-results meta-analysis.
8. Common-failure clustering.
9. Design of targeted corrective mechanisms.
10. Second-round experimental tests.
11. Independent held-out synthetic validation.
12. Theoretical and novelty assessment.
13. Preparation for subsequent real-data work.

Do not repeat expensive experiments without a methodological reason.

Do not silently continue tuning after confirmation failures.

Do not delete negative results.

Do not access real data.

Do not treat paper-access problems as a reason to stop all implementation.

Do not claim a faithful SOTA reproduction when only a partial algorithm description was available.

Do not require user confirmation for every ordinary development decision inside the isolated branch.

Estimate and respect an explicit compute/storage budget, and stop cleanly at the configured limit.

Preserve code and artifacts at the end of each completed research checkpoint.

---

# 18. FINAL RESEARCH DECISION

At the end of this synthetic research phase, answer the following questions:

**Question 1:** Which modified SOTA methods actually improved performance, and on what metrics?

**Question 2:** Which improvements generalize beyond the original search distributions?

**Question 3:** Which SOTA algorithms share a common, reproducible failure mechanism?

**Question 4:** Can a single targeted correction resolve that mechanism across multiple algorithms?

**Question 5:** Did the resulting fix outperform each constituent method and the strongest applicable comparator?

**Question 6:** Can the result be explained theoretically, structurally or computationally?

**Question 7:** Which one or two frozen algorithms should proceed to real-data validation?

**Question 8:** What exact evidence would be required to elevate the strongest result into a defensible ICML/NeurIPS methodological contribution?

## CENTRAL INSTRUCTION

We are explicitly pursuing **empirical algorithm discovery followed by evidence-driven methodological innovation**.

Start with established SOTA.

Experiment broadly but reproducibly with modifications, hybrids, parameters, objectives and approximations.

Preserve every result.

Use the entire results archive to identify shared weaknesses.

Develop targeted fixes for those weaknesses.

Validate those fixes on independent synthetic worlds.

Only then determine the precise novelty claim.

**The minimum desired research outcome is a reproducible improvement over an appropriately matched SOTA method. The stronger outcome is a new algorithmic mechanism that explains and resolves a common weakness shared by several existing methods. Neither outcome should be asserted without evidence.**

**Begin immediately with the isolated branch, offline baseline registry and synthetic algorithm search. Do not run real-data experiments in this phase.**