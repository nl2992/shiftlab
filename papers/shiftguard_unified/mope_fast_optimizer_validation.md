# Exact optimizer validation for the OBD/MOPE replay

**Status:** validated computational acceleration for the frozen exploratory
OBD replay; not a change to MOPE's statistical method and not evidence that
its assumptions hold on Open Bandit data.

## Why the acceleration was needed

The pinned author routine calls CVXPY once per event to solve a two-variable
concave quadratic program. On the frozen 274,737-event position-1 evaluation
segment, that prevented completion of the eventwise path. The initial stopped
attempt is preserved in
[`execution note`](open_bandit_mope_development_execution_note_2026-10-26.md).

## Exact optimization used

For matrix `A`, vector `b`, and `psi = 2 - 4 log(2) < 0`, the reference solves

`maximize psi * x' A x + b' x` subject to four linear inequalities defining a
bounded polygon in two dimensions. `A` is positive semidefinite, so the
objective is concave. Its global maximum on this polygon is attained at an
interior stationary point, a stationary point on a feasible edge, or a
polygon vertex. `scripts/fast_mope_optimizer.py` enumerates these finite
candidates and returns the one with the largest objective. The official
confidence-sequence recursion, betting updates, score support and 10,000-point
parameter grid are unchanged.

## Comparison evidence

At MOPE commit `a4b8584b622f3a8296932568c520c1bb3e1957f0`, 250 deterministic
positive-semidefinite quadratic programs were solved both with the original
CVXPY function and the exact optimizer. Maximum objective difference was
`1.48e-13`; maximum coordinate difference was `8.32e-7`, with no infeasible
reference solutions. Four 75-event paths spanning zero, positive, negative,
and random reward patterns matched exactly, with no empty-set differences.
On the actual OBD stream, the original reference and accelerated routine also
matched lower and upper paths exactly through 1,000 events; both first
returned an empty set at event 866. The full accelerated path was subsequently
independently reconstructed from the source Parquet file and its aggregate
artifacts verified.

The complete machine-readable QP/path comparison is
[`reference_qp_and_path_validation.json`](../../outputs/shiftguard_unified/sota_reproductions/mope_fast_solver_validation_v2/reference_qp_and_path_validation.json).
The runnable check is
[`validate_fast_mope_optimizer.py`](../../scripts/validate_fast_mope_optimizer.py);
the full-run verifier is
[`verify_open_bandit_mope_development.py`](../../scripts/verify_open_bandit_mope_development.py).

## Scope limits

This establishes numerical equivalence of the optimizer and the checked
confidence paths, not the real-data theorem assumptions. OBD still lacks
verified user/session or complete-slate units, click-release times, and
feature-availability times; previous ShiftLab OPE diagnostics used the same
week. Accordingly the MOPE interval is not a validity-bearing OBD confidence
statement. Its empty-set outcome blocks promotion in this replay and is kept
as a method diagnostic, not evidence of candidate harm or a measured false
alarm.
