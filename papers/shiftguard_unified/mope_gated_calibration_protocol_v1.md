# MOPE gated-deployment calibration and power protocol v1

**Status:** frozen before execution, 2026-10-26. **Purpose:** complete the
explicitly approved finite synthetic audit of the official MOPE gated policy
confidence sequence. This is a source-fidelity comparison, not a new method
proposal and not a real-data confirmation.

## Estimand and information contract

For a fixed target policy selected before the evaluation stream, compare its
expected reward with the logging policy's reward:

`Delta = E_mu[(pi(A|X)/mu(A|X)) R - R]`.

Each IID event reveals the logged action, its known propensity, and its binary
reward. The candidate is fixed before all events. Context/action/reward laws
are independent across events. The target/logging importance weight lies in
`[0.4, 1.6]`, and reward lies in `[0, 1]`. This meets the small bounded IID
MOPE gated-deployment contract exercised here. It does not model delayed or
selectively queried labels, candidate scouting, multiple candidates, or
dependence.

Each event has a binary context `X`. The logging policy chooses action 1 with
probability 0.5 in either context. The fixed target policy chooses action 1
with probability 0.2 when `X=0` and 0.8 when `X=1`. Reward probabilities are
0.1 for action 0 and 0.9 for action 1 in both contexts. Therefore the
context-specific target-minus-logger value differences are −0.24 for `X=0`
and +0.24 for `X=1`. The three registered contexts are:

| Cell | `P(X=1)` | True `Delta` | Role |
|---|---:|---:|---|
| `zero_mean` | 0.50 | 0.00 | Nondegenerate aggregate null |
| `positive_gain` | 0.75 | +0.12 | Power alternative |
| `negative_gain` | 0.25 | −0.12 | Strict no-promotion control |

The evaluator constructs the importance weights and outcomes. The MOPE runner
receives only the per-event `(weight, reward)` pairs, as required by the
reference routine.

## Methods and endpoints

1. **Official MOPE:** pinned author implementation `wealth_lb_gd` at commit
   `a4b8584b622f3a8296932568c520c1bb3e1957f0`; promote at the first event
   where the lower confidence-sequence bound is strictly positive. If there
   is no crossing, do not promote by event 200. Labels used are the first
   crossing time or 200.
2. **Fixed-horizon Hoeffding gate:** at event 200, compute the sample mean of
   `Z=(weight-1)*reward`, whose range is `[-0.6, 0.6]`; promote only if
   `mean(Z) - 1.2*sqrt(log(1/0.05)/(2*200)) > 0`. This is a valid fixed-N
   one-sided comparison under the same IID/bounded-score contract. It uses
   all 200 labels.

Primary outcomes are false-promotion rate in `zero_mean`, promotion rate in
`positive_gain`, and mean labels used. The `negative_gain` promotion rate is a
 strict-control endpoint. Report two-sided exact Clopper–Pearson intervals for
all rates. Also count any stream whose MOPE two-sided confidence set is empty
at any event (`lower > upper`); this is a coverage-failure event, not an
implementation abort. Its one-sided exact upper limit is assessed in all
three cells. The error family has seven endpoints: four method ×
nonpositive-cell false-promotion rates and three MOPE empty-set rates. Use
simultaneous one-sided upper limits with Bonferroni-adjusted confidence
`1 - 0.05/7`, and report paired seed-bootstrap intervals for positive-cell
power and label-use differences. Use 1,000 independent streams per cell
(3,000 total),
200 events per stream, alpha 0.05, and a fixed seed block beginning at
2040000000. CUDA generates the registered stream uniforms; the pinned MOPE
calculation remains on CPU as in its reference implementation.

## Stopping and interpretation

Stop after all 3,000 streams have completed and an independent verifier
confirms source/input/output hashes, complete cell/method keys, finite
monotone lower/upper paths, empty-set indicators, exact-rate intervals, and
recomputed primary summaries. A simultaneous error-rate upper limit above
0.05, any non-finite or non-monotone path, or missing run keys fails the
registered calibration check and requires diagnosis before efficacy
interpretation. Power differences are descriptive; no novel-algorithm gate
or broad advantage is claimed from one DGP.

This fixed IID study does not validate MOPE on OBD's seven-day archive, establish
real-time validity, test multiple-candidate FWER, or answer ShiftGuard's full
label/query/retraining resource-allocation objective. Preserve the separate
OBD contract limitations in `mope_obd_applicability_audit.md`.

