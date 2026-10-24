# PPRM-style paired decision-harm benchmark specification

**Status:** Implementation specification; the unbiased block-estimator helper and support tests are
implemented, but the confidence sequence, stream integration, and experiment are not. No result or
novelty claim. This comparison follows the completed 30-seed severity/onset/horizon screen and is a
prerequisite to selecting a new monitor.

## Why this comparator is necessary

Prediction-Powered Risk Monitoring (PPRM) already combines imputed risks with labeled residual
corrections, constructs anytime-valid lower confidence sequences for running risk, and permits a
predictable sequence of proxy-reliance weights. The published setting monitors a model's running
predictive risk against an upper confidence bound on its source risk. It assumes bounded loss,
i.i.d. calibration data, and independent within-round labeled and unlabeled samples; test
distributions can vary over rounds. Its adaptive reliance coefficient is estimated only from prior
rounds.

ShiftLab's primary target differs: the paired excess cost of a deployed action policy relative to a
specified reference in the current environment. It can be negative and need not be a prediction
loss. For a frozen deployed/reference pair, define

\[
D_t = c(\pi(X_t),Y_t)-c(\pi_{\mathrm{ref}}(X_t),Y_t),\qquad
H_0: \mathbb{E}[D_t\mid\mathcal F_{t-1}]\leq\epsilon\quad\forall t.
\]

The PPRM comparison therefore tests a running-mean consequence of this stronger null, not an
equivalent hypothesis. It is a strong, established-method comparator for the same paired-cost
estimand, not a reproduction of the published source-risk procedure and not a new method.

## Paired-cost PPI construction

Use nonoverlapping chronological blocks. Within block \(b\), the evaluator generates independent
test events from the block's distribution. The learner observes all block covariates and frozen
policy actions, but receives labels only for a random labeled subset. The labeled sample and
unlabeled sample must be disjoint and conditionally independent given the block schedule; do not
obtain the labeled set by reusing observations from the unlabeled set.

For each event compute a predictable proxy \(h(X)\) for the paired cost \(D\), without access to
the current label. The per-event decision costs for both policies become observable once that label
arrives. If \(|D|\leq M\) and \(|h|\leq M\), map both to \([0,1]\):

\[
Z=(D+M)/(2M),\qquad \tilde Z=(h+M)/(2M).
\]

For block \(b\), with \(n_b>0\) labeled and \(N_b>0\) unlabeled events, form

\[
\widehat\mu_b(\eta_b)=
\eta_b\frac{1}{N_b}\sum_{i\in U_b}\tilde Z_i
+\frac{1}{n_b}\sum_{i\in L_b}(Z_i-\eta_b\tilde Z_i),
\]

where \(\eta_b\) is chosen using only earlier blocks and is bounded by a preregistered
\(\eta_{\max}\). Conditional independence and random sampling from the same block distribution
make this estimate unbiased for the block's mean normalized paired cost for every predictable
\(\eta_b\). Its support is contained in \([-\eta_{\max},1+\eta_{\max}]\); normalize this range
before applying the bounded empirical-Bernstein confidence sequence. Compare its anytime lower
bound on the running mean with the normalized materiality threshold
\((\epsilon+M)/(2M)\). Use an explicit alpha split between any source/calibration bound and the
test-stream confidence sequence if a source-risk version is also reported. For the direct known
threshold comparison specified here, spend the full registered alpha on the test-stream bound.

Do not update a block estimate before all labels assigned to that block have arrived. The first
implementation should use immediate feedback; delayed-arrival handling is a separate extension.
Freeze the proxy, reference policy, block size, labeled/unlabeled ratio, \(\eta\) update rule,
confidence-sequence mixture, alpha, and stopping rule before evaluation. A valid implementation
must keep learner-visible block estimates separate from evaluator-only true block means and
counterfactual oracle costs.

## Matched experiment

Compare the PPRM-style paired-cost confidence-sequence monitor with:

1. full-label paired-cost monitoring;
2. the existing eventwise prediction-powered fixed-mixture e-process;
3. eventwise direct inverse-propensity monitoring; and
4. uniform label sampling with a fixed-horizon paired-mean interval as a nonsequential reference.

Match the total label-dollar cap, event horizon, policy/reference pair, cost matrix, alpha, synthetic
streams, and observable covariates. Because block PPI consumes labels in fixed batches, report any
unused remainder and compare only event horizons that fit the same total cap. Report false
escalation probability and confidence interval on stationary and benign-nuisance controls; power,
unconditional/censored detection delay, and cumulative pre-alarm excess decision cost on local harm,
recurring regimes, and harmful adaptation; plus labels, dollars, and events processed. Include a
predictive-loss-only alternative to check whether detection is decision-specific.

First run CPU unit tests and a small CUDA smoke. Then use a fresh development seed block to debug
only. Freeze the protocol and run at least 2,000 independent streams per null cell for calibration
and a separate power block sized from a pre-run paired-power analysis. Keep those blocks disjoint
from the existing null calibration, confirmation, and 36-cell development grid. No scale, block
size, \(\eta\), predictor, or threshold may be selected on the confirmatory block.

## Validity gates and interpretation

- Prove the block estimator is conditionally unbiased under the documented split and predictable
  \(\eta_b\), and verify the finite support bound in tests for every allowed configuration.
- Verify the confidence-sequence implementation against the cited conjugate-mixture empirical-
  Bernstein construction, including its one-sided error allocation; do not substitute a fixed-time
  interval while retaining an anytime-valid label.
- The published PPRM theorem uses a running-risk null. State clearly that pointwise conditional
  harm implies the running-mean null, but the converse does not hold. Also report if the simulation
  only meets independent block observations rather than arbitrary serial dependence.
- This comparator cannot certify an adapted replacement. Candidate promotion remains a separate
  frozen-candidate problem with its own selection and deployment-cost accounting.
- If PPRM-style monitoring matches or exceeds the e-process on harm detection at equal dollars and
  false-escalation control, narrow Paper 1 to any empirically supported distinction. If no method
  improves on existing baselines, keep the negative result and do not add algorithmic novelty prose.

## Primary references

- Zhang et al., [Prediction-Powered Risk Monitoring of Deployed Models for Detecting Harmful
  Distribution Shifts](https://arxiv.org/abs/2602.02229), especially its PPI risk estimator,
  adaptive predictable reliance, and CM-EB running-risk bounds.
- Howard et al., [Time-uniform, nonparametric, nonasymptotic confidence sequences](
  https://projecteuclid.org/journals/annals-of-statistics/volume-49/issue-2/Time-uniform-nonparametric-nonasymptotic-confidence-sequences/10.1214/20-AOS1991.full),
  for the general time-uniform confidence-sequence framework.
- The current ShiftLab estimand, feedback contract, and unresolved guarantees are recorded in
  [`research_charter.md`](research_charter.md), [`streaming_decision_contract.md`](streaming_decision_contract.md),
  and [`theory_targets.md`](theory_targets.md).
