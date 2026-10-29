# Real paired-loss reduction: correction and audit

2026-10-29. **Status:** algebraic reduction PROVED under stated filtration and
boundedness; known-HMM adequacy and real-data performance UNRESOLVED. No real
observations or holdouts were accessed.

## Correction to the preregistered proposal

`REAL_PAIRED_REDUCTION_PROTOCOL_V1.md` incorrectly proposed halving query and
switch fees, and the first checker incorrectly multiplied the encoded loss and
offset by two. The first run failed its assertion. Its exact source is preserved
in `real_paired_reduction_failed_source_v1.txt`; the protocol remains unchanged.
The correct transformation below keeps query and switch fees in their original
units. The corrected checker passes 50 exact-fraction cases and its results and
source hashes are in `real_paired_reduction_checks_v1.json`.

## Cost identity and information contract

Suppose both paired losses lie in [0,1], Z_t=l0_t-l1_t, and U_t is a fresh
independent uniform draw after the paired outcome, independent of past, current
loss and learner randomization. Define Y_t=1{U_t<=(1+Z_t)/2}, and let the
encoded losses for actions 0 and 1 be Y_t and 1-Y_t. Define
K_t=(l0_t+l1_t-1)/2. Conditional on the current loss pair and any action
chosen before the U_t draw,

    E_U[ encoded_loss(A_t) + K_t | losses, A_t ] = l_{A_t,t}.

For any predictable nonanticipating policy using the encoded feedback, and a
fixed exogenous paired-loss sequence or a policy-independent outcome process,
linearity yields

    E[original cumulative decision loss + c Q + k switches]
      = E[encoded cumulative decision loss + c Q + k switches]
        + E[sum_t K_t].

The final offset is common across policies only when the distribution of the
outcome process is unaffected by policy choices; action-dependent outcomes need
an explicit causal model and do not inherit the comparison automatically. This
identity is in expectation over the encoding coins, not pathwise. The same
policy must act with the same information in both evaluations. Sampling a new
encoding separately for each policy can destroy paired comparisons; generate
one outcome-dependent coin per event in the evaluator, while revealing only
queried encodings at their prescribed release time. Never expose unqueried Y,
U, Z or loss pairs to the learner. Charge request-time costs in unchanged units.

If the full event-time null is E[Z_t | null full past, current public choices]
<=0 and the fresh U_t is independent conditional on that information and Z_t,
then P(Y_t=1 | that same full information)<=1/2 by iterated expectation. This
requires the null to condition on any prior encoder coins and generated outcomes
that the adversary can observe. It is not implied by a sample mean, a fitted HMM,
or a retrospective data replay. Fixed delayed release and predictable requests
must preserve the original event-time filtration; informative or reordered delay
requires a separate proof.

## Limits: information and HMM

The encoding reveals one binary draw, not the real-valued loss pair. Distinct
loss pairs can produce the same Y with positive probability: for pairs
(1/2,1/4) and (1/4,1/2), their P(Y=1) values are 5/8 and 3/8 respectively.
Thus a controller allowed to observe actual loss magnitudes has strictly more
information than an encoded-only controller. A fair matched comparison must
choose and disclose a common feedback contract; comparing against a full-loss
baseline is meaningful but does not put both algorithms in the same policy class.

The existing optimizer's loss model assumes a known two-state HMM with specified
transition and state-emission laws. The affine cost identity does not imply that
real encoded labels obey that HMM, nor that its hidden state is identified from
training data. Fitting a working HMM can yield a misspecified economic planner;
its model-based optimality gap and expected-cost claims then concern that working
model, not automatically the empirical process. The causal-null safety guarantee
must also be justified separately under the actual bounded-loss conditional null.
Exact fixed-model null risk cannot certify false-promotion risk under an
unverified real-data conditional distribution.

Before real replay, freeze bounded loss definitions and clipping thresholds on
training/validation only, training and evaluation splits, model fitting and
uncertainty, encoder seed allocation, event/feedback clock and matched baseline
information. Existing CRSP next-return targets and its assumed daily clock can
support exploratory predictive-loss replay only after the candidate and baseline
pass the planned synthetic/method gates. A new unused period with verified
availability would be required for prospective/confirmatory claims. Do not
upgrade the user-requested empirical win from an exposed-development result.

## Decision

The binary reduction provides a possible common feedback channel and preserves
expected action-cost comparisons for a fixed exogenous process. It does not make
the real-data evaluation already valid or establish an algorithmic contribution.
Continue candidate development and source-matched baseline comparisons; preserve
this failed-first-check correction and all existing real-data restrictions.
