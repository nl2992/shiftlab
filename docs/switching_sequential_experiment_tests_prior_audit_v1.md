# Optimal tests after sequential experiments: novelty boundary

**Date:** 2026-10-29. **Status:** primary-source theorem-scope audit; no new method claim.

## Source and inspected results

Karun Adusumilli, “Optimal Tests Following Sequential Experiments,” *Journal of Political Economy*
134(9), 2778–2823 (2026), DOI 10.1086/742418; full author preprint arXiv:2305.00403. I inspected
the full 2023 arXiv PDF, including the scope discussion in Section 1.1, Assumptions 1–2 and
Theorems 1–2 for bounded stopping-time experiments, the α-spending construction, the costly
sampling example, Section 5's batched adaptive-allocation setup and Theorem 3, and the corresponding
appendix proof passages.

The paper studies local asymptotic power under differentiability-in-quadratic-mean regularity and
bounded normalized stopping times. Theorem 1 represents limiting tests through a Gaussian
diffusion experiment. Theorem 2 derives a power envelope under conditional α-spending across
stopping-time values. Theorem 3 extends the representation to adaptive sampling updated at a fixed
finite number of batches. For post-experiment testing, the sufficient statistics include arm
sample counts and terminal score/efficient-influence-function processes; under additional
assumptions these reduce further. The paper's costly-sampling application studies terminal testing
after a sample-size stopping rule.

## Consequence for ShiftLab

Close novelty claims based on (a) optimizing a terminal test after a costly sequential experiment,
(b) reducing adaptive-treatment test statistics to a fixed-dimensional count/score summary in a
regular local asymptotic regime, or (c) using conditional α-spending by stopping time. These are
established results and are relevant strong asymptotic comparators for any proposed acquisition
rule whose assumptions fit.

The paper explicitly distinguishes its classical, protocol-conditional size guarantee from
anytime-valid inference: its test is sized when the registered sampling/stopping protocol is
followed, whereas anytime-valid methods must remain valid under arbitrary allowed stopping and
continuation. Its results are asymptotic local-power envelopes, not finite-sample worst-case bounds
under the history-adaptive conditional null `P(Y_t=1 | full past, current query) <= 1/2`. They do
not provide a hard pathwise total-query constraint with pending delayed labels, an absorbing
any-promotion event over repeated interventions, recurrent regimes, rollback costs, or post-change
decision regret. These distinctions define the remaining contract mismatch; they do not establish
novelty by themselves.

Any new claim involving sequential power must now compare against this source where regularity
and protocol assumptions apply, and explain why its finite-sample anytime risk, delayed release,
hard-budget, and repeated-switch result cannot be reduced to the paper's fixed-protocol asymptotic
envelope plus an established e-process wrapper. Merely replacing expected-cost stopping by a cap
or adding a known delay to the schedule is insufficient without a theorem-level gain.

## Decision

This source further narrows G1 but does not resolve the full two-law problem. It makes a generic
“optimal costly acquisition followed by a statistically optimal test” contribution untenable.
G1 remains open only for a structural result that jointly improves acquisition and reversible
deployment under the finite-sample causal-null contract and beats the strongest resource-matched
sequential-design baseline. The prior-output separate-risk/current-value rule still applies: a
valid global promotion test does not certify continued value after reversal.

## Provenance

- Published record: [JPE, DOI 10.1086/742418](https://www.journals.uchicago.edu/doi/abs/10.1086/742418).
- Full primary preprint: [arXiv:2305.00403](https://arxiv.org/abs/2305.00403).
- Cached PDF: `outputs/switching_source_audit_v1/adusumilli_optimal_tests_sequential_experiments_2023.pdf`.
- SHA256: `19329601743C64F755E3E5AA7F3F905759EFFE5E16939603EFC9D730C6D79FD2`.
- This is a selected scope audit, not an independent reproof. The published 2026 abstract was
  checked against the official JPE record; theorem details were read from the full arXiv preprint.
