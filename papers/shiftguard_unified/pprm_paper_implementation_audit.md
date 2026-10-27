# PPRM paper-to-implementation audit

**Audit date:** 2026-10-26. **Primary source:** Zhang, Cai, Yu, and Simeone,
[*Prediction-Powered Risk Monitoring of Deployed Models for Detecting Harmful
Distribution Shifts*](https://proceedings.mlr.press/v306/zhang26g.html), ICML 2026,
PMLR 306, 154241–154262. The audit used the complete published PDF linked from
the PMLR record. No paper code repository was identified in the record.

## Published estimand

PPRM monitors the time-averaged predictive risk of one fixed deployed model,
\[
\bar R_t=t^{-1}\sum_{s=1}^t R_s,
\]
against its nominal source risk plus a fixed tolerance. Its null is
\(\bar R_t\le R_0+\epsilon_{\rm tol}\) for every time \(t\). This is a
running-average predictive-risk hypothesis. It is not the eventwise conditional
paired decision-cost null used by DIVE, and PPRM does not certify that a
replacement policy improves downstream utility.

## Estimator and inference path in the paper

Each test round has a strictly positive labeled sample of size \(n_t\) and a
separate, independent unlabeled sample of size \(N_t\), both drawn from that
round's distribution. A fixed auxiliary predictor supplies synthetic labels.
With a predictable reliance coefficient \(\eta_t\), the round estimate is
\[
\widehat R_t^{PP}=\eta_t\,\overline{\tilde\ell}^{\,U}_t+
\overline{(\ell-\eta_t\tilde\ell)}^{,L}_t.
\]
It is unbiased for the round risk because \(\eta_t\) uses only prior
information and the current true and imputed risks are corrected on the
labeled sample. The source-risk estimate uses a separate nominal sample. The
paper partitions source unlabeled observations into disjoint blocks paired
with source labeled observations, forming independent prediction-powered
per-sample values for its source upper bound.

For the test stream, the paper affinely maps estimates in
\([-\eta_{\max},1+\eta_{\max}]\) to \([0,1]\), then uses a conjugate-mixture
empirical-Bernstein confidence sequence. Its cumulative prediction error is
\(V_t=\sum_{s\le t}(Z_s-\bar Z_{s-1})^2\), where \(\bar Z_{s-1}\) is the
past running estimate. The lower bound on test risk is compared with a separate
upper bound on source risk; the source and test miscoverage levels add to the
type-I error budget. The source bound in the paper is a betting-based bound
over the paired source estimator values.

The adaptive version estimates the variance-minimizing reliance coefficient
from a fixed sliding window of earlier labeled and unlabeled observations:
\[
\eta_t=\frac{\widehat{\mathrm{Cov}}(u,\tilde u^L)}
 {(1+n_t/N_t)\widehat{\mathrm{Var}}(\tilde u^U)}.
\]
The estimate must be made predictable and constrained by the predeclared
\(\eta_{\max}\). The paper reports \(n_t=1,N_t=15\), initial \(\eta_0=1\),
and a 60-round window in its image and language-model experiments.

The finite-sample argument requires bounded losses, a valid source sample,
positive labeled and unlabeled sample sizes at each test round, independent
labeled and unlabeled samples from the same current round distribution, and a
predictable \(\eta_t\). The paper allows test distributions to change across
rounds; the prediction-powered estimate must still be conditionally unbiased
for each round. These assumptions are not automatic under selective queries,
delayed labels, overlapping labeled/unlabeled pools, adaptive model updates, or
action-dependent outcomes.

## Current ShiftLab implementation boundary

The repository contains extensive code and experiments in
[`docs/pprm_paired_decision_benchmark.md`](../../docs/pprm_paired_decision_benchmark.md)
and `src/shiftlab/dive/eprocess.py::PPIBlockConfidenceSequence`. Those are
project-specific paired-decision-cost adaptations. The current block process
uses a discrete finite mixture for its test confidence sequence and omits the
paper's source-risk upper bound; its earlier registered runs also required an
indexing-bug correction documented in that benchmark file. The local
calibrations and confirmations therefore do not constitute a reproduction of
published PPRM and cannot be cited as evidence that PPRM detects decision harm.

The new module `src/shiftlab/dive/pprm_risk_monitor.py` implements the
published predictive-risk batch estimator, predictable sliding-window
reliance rule, CM-EB test lower sequence, and a one-sided betting source upper
bound. The source-bound recursion was compared against ConfSeq's MIT-licensed
implementation at commit
[`5ffe733ca2447a2e28c2c91f3b00086173f2ab2c`](https://github.com/gostevehoward/confseq/tree/5ffe733ca2447a2e28c2c91f3b00086173f2ab2c);
three fixed test cases matched at or below `1.4e-17` absolute difference.
The test-stream CM-EB uses a finite discrete mixing distribution over
\(\lambda\), which remains a valid mixture but is a chosen implementation
parameterization. Eight CPU tests cover the estimator, source pairing,
predictable coefficient, source upper bound, and threshold crossing. There is
the frozen development run and an independent 300-seed-per-cell confirmation
now exist at
[`outputs/shiftguard_unified/sota_reproductions/pprm_predictive_risk_confirmation_v1/`](../../outputs/shiftguard_unified/sota_reproductions/pprm_predictive_risk_confirmation_v1/).
In confirmation, PPRM detected predictive harm in 7/300 streams (exact 95% CI
[0.94%, 4.75%]) and supervised risk monitoring (SRM) in 19/300 ([3.86%,
9.71%]); both recorded 0/300 alarms in each of two controls (one-sided
empirical upper bound is not a theorem; exact two-sided 95% upper bound is
1.22%). DIVE detected decision-cost-only harm in 70/300 ([18.67%, 28.54%]),
while predictive-risk monitors each recorded 0/300 there. The low predictive
detection rates establish no method advantage, and alarm rates across distinct
nulls are not head-to-head power comparisons. This is confirmation only for
the frozen synthetic generator and operating point.

## Required next implementation and stopping rule

Source-bound parity, focused CPU tests, CUDA smoke, the frozen development
study, and independent 300-seed-per-cell confirmation are complete. The
benchmark uses stationary and benign-nuisance controls, predictive-risk harm,
and decision-cost-only shift, with equal labeled feedback for PPRM and SRM.
Details, assumptions, label counts, delays, confidence intervals, and
checksums are in its protocol and manifest. Deeper source-pairing and CM-EB
boundary audits remain useful, but the result currently establishes only low
detection at this operating point, not superiority or general validity. Any
paired-cost transfer remains a separately named adaptation and must be
calibrated under its own null.

This is the next finite Q1 comparator task, not a new algorithm branch and not
a novelty claim. The existing method decision remains **NO-GO** for speculative
algorithm development until the comparator and the rest of the finite closure
gate are resolved.
