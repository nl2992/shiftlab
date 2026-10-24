# PPRM-style paired decision-harm benchmark specification

**Status:** The unbiased block-estimator helper, predictable plug-in reliance estimate, finite-mixture
CM-EB lower confidence sequence, and hard-budget stream integration are implemented and unit-tested.
The original PPRM runs described below are superseded: a block-local indexing bug reused labels from
the first stream block in later blocks. Eventwise comparator results remain valid, but PPRM estimator,
reliance-sensitivity, and horizon results from those runs must not be interpreted. The bug is fixed and
has a regression test. A corrected four-setting, 30-seed-per-cell CUDA grid is stored in
[`outputs/pprm_block_grid_corrected_v1/`](../outputs/pprm_block_grid_corrected_v1/); all methods still
recorded zero detections, while block-PPI estimation RMSE is now comparable to or better than the
frozen eventwise control in many cells. Corrected variance diagnostics are recorded in
[`outputs/pprm_variance_diagnostic_corrected_v1/`](../outputs/pprm_variance_diagnostic_corrected_v1/).
Corrected independent-seed horizon and long-horizon block-size screens are also recorded below. A
fixed mixture of two valid block-level e-processes provides a mathematically grounded development
candidate: it detected harms missed by CM-EB alone, but remained less powerful than eventwise PPI on
the tested streams. All results remain developmental; confirmatory null calibration and separately
powered evaluation are outstanding.

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
before applying a bounded confidence sequence. The current code applies the CM-EB test-stream
boundary using a fixed discrete mixture over λ. This is the PPRM running-risk bound adapted to
paired-cost block estimates; it omits PPRM's source-risk upper bound. Compare its anytime lower
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

The current block comparator initializes \(\eta_1=1\), then estimates later reliance from
completed labeled/unlabeled blocks using the PPRM plug-in rule
\(\hat\eta=\mathrm{Cov}(Z,h)/[(1+n/N)\mathrm{Var}(h)]\), clipped to \([0,1]\). This is
predictable and preserves unbiasedness; its variance-optimal interpretation is only a plug-in
approximation under nonstationary blocks. The CM-EB test-stream mixture uses 64 equally weighted
log-spaced \(\lambda\) values from \(10^{-4}\) to \(0.99\), with \(\psi_E(\lambda)=-\log(1-\lambda)-\lambda\).

## Block-size development grid

The matched-proxy development grid uses block sizes \(B\in\{5,10,20,40\}\), with \(n_b=B/5\)
labels per block to target a 20% label fraction. It compares adaptive block PPI against eventwise
prediction-powered monitoring with both frozen and updating proxies. All cells use the same 30
stream seeds (seed offset 20372023), six registered scenarios, 20% nominal label-dollar budget,
and common eventwise increment bound. The original run at
[`outputs/pprm_block_grid_development_v1/`](../outputs/pprm_block_grid_development_v1/) is retained
for audit, but its PPRM results are invalid due to the indexing bug described above. Corrected
Parquet metrics, manifests, paired analysis, and figure are in
[`outputs/pprm_block_grid_corrected_v1/`](../outputs/pprm_block_grid_corrected_v1/).
Reproduce the run and report from the repository root with:

```powershell
uv run python scripts/run_pprm_block_grid.py --output-root outputs/pprm_block_grid_reproduction --device cuda
uv run python scripts/analyze_pprm_block_grid.py --output-root outputs/pprm_block_grid_reproduction
```

The corrected run used the NVIDIA GeForce RTX 4060 Laptop GPU. Across all block sizes, all three
monitors detected 0/30 harms in each harmful scenario and recorded 0/30 false escalations in each
null control. Corrected PPRM stream-mean RMSE is comparable to or below frozen eventwise PPI in
many cells, although its ranking varies by scenario. At \(B=5\), boundary-local-harm RMSE was
0.0721 for block PPI versus 0.1108 for frozen eventwise PPI; at \(B=40\), it was 0.0931 versus
0.1108. At \(B=10\), recurring-regime RMSE was 0.0424 versus 0.0872. This accuracy improvement
did not produce detections under the current sequential boundary and budget. Paired seed-bootstrap
intervals are exploratory and unadjusted. Larger blocks processed fewer events and used fewer labels.

This is a development-only result, not a power or false-alarm guarantee. Diagnose why every method
misses the current harm signals despite corrected estimation accuracy before freezing a protocol for
the required 2,000-stream-per-null calibration and separately powered study. Use disjoint seeds. No
confirmatory conclusions may be drawn from this screen.

## Reliance-bound sensitivity

To test whether the monitor's worst-case support was obscuring evidence, a second development
screen fixed \(B=20\), four labels per block, the seed block above, all scenarios, the nominal
label-dollar budget, and the eventwise controls. It varied the PPRM maximum and initial reliance
together over \(\eta_{\max}\in\{0.10,0.25,0.50,1.00\}\). This is a valid support sensitivity because
the plug-in reliance is clipped to the declared cap before the next block. Run it with:

```powershell
uv run python scripts/run_pprm_reliance_bound_sensitivity.py --output-root outputs/pprm_reliance_bound_development_v1 --device cuda
uv run python scripts/analyze_pprm_reliance_bound_sensitivity.py --output-root outputs/pprm_reliance_bound_development_v1
```

This screen predates the indexing fix; its PPRM results are superseded and must not be interpreted.
The generated analysis is in
[`outputs/pprm_reliance_bound_development_v1/analysis/`](../outputs/pprm_reliance_bound_development_v1/analysis/).
The tightest cap materially raised the mean final lower bound: for boundary-local harm it rose from
0.032 at cap 1.0 to 0.329 at cap 0.10, against a normalized materiality threshold near 0.55.
However, **no cap detected any of the 30 harmful streams in any harmful scenario**. The lower bound
therefore remains short of the threshold, and this screen does not justify choosing 0.10 for
confirmatory use. The estimator RMSE changed little across caps, so support tightening improves the
confidence bound but does not solve the estimator's precision gap.

## Independent-seed horizon sensitivity

The next development screen held \(B=20\), four labels per block, \(\eta_{\max}=\eta_1=0.10\),
alpha 0.05, and the nominal 20% label-dollar budget fixed, then varied total stream size
\(n\in\{1600,3200,6400\}\) on a separate seed block (offset 20372123). It includes the same
eventwise frozen- and updating-proxy controls on each stream:

```powershell
uv run python scripts/run_pprm_horizon_sensitivity.py --output-root outputs/pprm_horizon_development_v1 --device cuda
uv run python scripts/analyze_pprm_horizon_sensitivity.py --output-root outputs/pprm_horizon_development_v1
```

This screen predates the indexing fix; its PPRM results are superseded and must not be interpreted.
The eventwise comparator results remain valid. The Parquet metrics, manifests and report are in
[`outputs/pprm_horizon_development_v1/`](../outputs/pprm_horizon_development_v1/), with the
summary in [`analysis/horizon_analysis.md`](../outputs/pprm_horizon_development_v1/analysis/horizon_analysis.md).
At \(n=1600\), eventwise methods detected 0/30 streams in each harmful scenario. At \(n=6400\),
eventwise frozen PPI detected 24/30 boundary-local-harm and 29/30 harmful-adaptation streams, and
24/30 recurring-regime streams. Eventwise controls recorded no stationary escalations. The PPRM
numbers from this run are invalid and omitted. Thirty streams are far too few to calibrate error
rates; the eventwise results are exploratory power diagnostics, not confirmatory evidence.

The corrected horizon rerun is in
[`outputs/pprm_horizon_corrected_v1/analysis/horizon_analysis.md`](../outputs/pprm_horizon_corrected_v1/analysis/horizon_analysis.md).
It uses the independent seed offset 20372123, \\(B=20\\), four labels per block, and reliance cap 0.1.
PPRM detected 0/30 harms at every horizon. Eventwise frozen PPI detected 0/30 at \\(n=1600\\),
2/30 boundary-local and 2/30 harmful-adaptation streams at (n=3200), then 24/30, 29/30, and
24/30 boundary-local, harmful-adaptation, and recurring-regime streams at \\(n=6400\\). There were
no false escalations in the 30 stationary streams. At \\(n=6400\\), PPRM's stream-mean estimation
RMSE was 0.0289, 0.0211, and 0.0318 in those three harm scenarios, close to the eventwise frozen
values 0.0325, 0.0255, and 0.0281. Yet the PPRM mean confidence-sequence lower bounds were only
0.488, 0.491, and 0.488, below the normalized materiality threshold 0.51. This points to evidence
accumulation and the block-level confidence sequence as the next bottleneck to test, rather than
assuming that the corrected estimator remains inaccurate. These 30-seed results remain exploratory.

At the same horizon and seed offset, the smaller-block screen in
[`outputs/pprm_long_horizon_block_grid_corrected_v1/analysis/block_grid_analysis.md`](../outputs/pprm_long_horizon_block_grid_corrected_v1/analysis/block_grid_analysis.md)
compared \\(B=5\\) and \\(B=10\\), each with 20% of events labeled, on stationary, boundary-local-harm,
recurring-regime, and harmful-adaptation streams. PPRM detected 0/30 in all three harm scenarios at
both block sizes; eventwise updating PPI detected 26/30, 24/30, and 29/30, respectively. The mean
PPRM lower bounds for \\(B=5\\) on the three harms were 0.499, 0.503, and 0.499; for \\(B=10\\), they
were 0.480, 0.484, and 0.480. All remained below the 0.51 materiality threshold. More frequent
block updates alone therefore did not recover the eventwise power in this screen.

## Fixed mixture of block-level e-processes

The latest development candidate combines the existing CM-EB block e-process (E_t^{\mathrm{CM}})
with a predictable positive betting e-process (E_t^{\mathrm{bet}}):

\[
E_t^{(w)} = w E_t^{\mathrm{CM}} + (1-w) E_t^{\mathrm{bet}},\qquad 0<w<1.
\]

For block estimate \(\widehat\mu_b\) and normalized materiality threshold \(\tau\), the positive
process receives \(A_b=\widehat\mu_b-\tau\). Its deterministic absolute bound is
\(B=\max(\eta_{\max}+\tau,1+\eta_{\max}-\tau)\), from the declared PPI support
\([-\eta_{\max},1+\eta_{\max}]\). It maps \(A_b\) to
\(X_b=(1+A_b/B)/2\) and uses a predictable stake in \([0,1]\); under the block running-mean null,
\(\mathbb E[X_b\mid\mathcal F_{b-1}]\leq 1/2\), so each betting factor has conditional expectation
at most one. A fixed convex mixture of the component e-processes remains an e-process, and Ville's
inequality controls the probability that it ever crosses \(1/\alpha\). This guarantee requires the
block estimator's conditional unbiasedness, predictable reliance, bounded support, and the stated
conditional-mean null; it does not certify a changing policy or the stronger eventwise conditional
null.

The exact small-null enumeration test passes for all five tested fixed weights. On the 30-seed
development block at \\(n=6400\\), \\(B=20\\), and reliance cap 0.1, the weight screen is in
[`outputs/pprm_block_mixture_weights_development_v1/analysis/mixture_weight_analysis.md`](../outputs/pprm_block_mixture_weights_development_v1/analysis/mixture_weight_analysis.md).
The \\(w=0.1\\) mixture detected 17/30 boundary-local, 18/30 harmful-adaptation, and 17/30 recurring-
regime streams, compared with 0/30 for CM-EB alone and 24/30, 29/30, and 24/30 for eventwise frozen
PPI. No mixture weight falsely escalated in 30 stationary streams, which is far too few to establish
an error rate. The weights used the same development streams, so selecting \\(w=0.1\\) is a development
choice only; independent null calibration and power evaluation are required before any confirmatory
claim. The paired metrics are in
[`outputs/pprm_block_mixture_weights_development_v1/block_20/metrics/hard_budget_comparison.parquet`](../outputs/pprm_block_mixture_weights_development_v1/block_20/metrics/hard_budget_comparison.parquet).

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
- Verify the finite-mixture CM-EB boundary against the published formula, including its one-sided
  error allocation and predictable past-mean forecast; test optional stopping and the complete
  paired-cost estimator-to-alarm pipeline before the matched study.
- State the distinction between a running-average null and an eventwise conditional-mean null: the
  latter implies the former, but the converse does not. Report whether assumptions cover arbitrary
  serial dependence or only independent synthetic blocks.
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
