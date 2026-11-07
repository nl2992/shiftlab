# RPOQ S3: exact structure test, protocol (pre-registered)

**Branch:** `research/rpoq-s1-fatal-flaw-audit`. **Date:** 2026-10-29. **Stage:** S3 of [`rpoq_plan_v1.md`](rpoq_plan_v1.md).

| Label | Value |
|---|---|
| Work type | Exact dynamic programme on a toy instance. Synthetic only, no data. |
| Claim level | None. A pass nominates S4; it does not establish novelty. |
| Frozen before | Any solver output. Instance parameters below were fixed before the first run, except `T`, which may be changed once after a recorded calibration run (see Calibration). |

## Question

On the smallest instance of the RPOQ problem, is the optimal admissible query policy (a) a monotone threshold in the resolved-prefix wealth, and (b) materially better than the best non-adaptive query table?

## Instance (frozen)

- Events `t = 0..T−1`, `T = 12` (changed to 10, see Calibration record); label delay `d = 2` events; pathwise query budget `B ∈ {2, 3, 4, 6}`, with a query counted at issue.
- Context `x ∈ {A, B}`, `P(A) = 1/2`, revealed before the query decision.
- Contrast `Z ∈ {−1, +1}`. Null: `P(Z=+1 | x) = 1/2` for both contexts (mean 0). Alternative: `P(Z=+1 | A) = 0.8`, `P(Z=+1 | B) = 0.7`.
- Proxy `H(A) = 0.6`, `H(B) = 0` (predictable, bounded).
- Query propensity `q ∈ {0.25, 0.5, 0.75, 1}`, chosen after seeing `x`, with `Q ~ Bernoulli(q)` independent of `Z`.
- Increment `X = H + Q (Z − H) / q`, so `E[X | x] = E[Z | x]` and the null gives `E[X] ≤ 0`.
- Bet `λ = c / |X_min(x, q)|` with `c = 0.5`, where `X_min` is the smallest possible `X`. The bet is a fixed function of `(x, q)`. It is **not** optimised, which is a limitation to report.
- When the budget is exhausted, no query is possible and the wealth is frozen (factor 1). Using `X = H` without a correction would be invalid.
- Wealth is updated only through the contiguous resolved prefix of events. An unqueried event resolves at once but waits behind an earlier pending one.
- Success is absorbing: an alarm once the resolved-prefix wealth reaches `1/α` with `α = 0.2` (threshold 5). Pending labels at the horizon are allowed to resolve (up to `T − 1 + d`).
- Objective: maximise `P(alarm)` under the alternative.

## Policies compared

1. **Optimal admissible** by backward induction on the information state `(t, wealth, buffer, budget)`.
2. **Best constant table**: the best of all 16 `(q_A, q_B)` pairs held fixed over time.
3. **Neyman table**: `q ∝ sqrt(E[(Z − H)² | x])` under the alternative, scaled so the largest is 1, rounded to the grid. This is the Active Statistical Inference allocation shape.
4. **Always q = 1** while budget lasts.

## Pre-registered criteria

- **C0 (validity, must hold):** under the null, the exact `P(alarm)` of the optimal policy and of each baseline is ≤ α = 0.2.
- **C1 (structure):** group states by `(t, x, budget, buffer)`. For groups with at least 3 distinct wealth values, ties within 1e-9 are treated as equal. The group passes if some selection of optimal `q` is weakly monotone in wealth (either direction). Structure holds if at least 90% of groups pass; it is strong if all do. The failing groups are listed.
- **C2 (adaptivity value):** `V_opt − V_best_constant_table ≥ 0.02` (absolute power) for at least one `B`.

## Decision rule

| C0 | C1 | C2 | Outcome |
|---|---|---|---|
| fail | any | any | Bug. Fix and rerun. Not a finding. |
| pass | holds | ≥ 0.02 | Nominate the threshold policy class for S4. |
| pass | holds | < 0.02 | The optimum is effectively a static table (the Neyman/ASI shape). Stop the adaptive-policy claim. |
| pass | fails | any | No compact structure. Stop. Keep Options 1 and 2 as separate results. |

## Calibration

A scratch run may report whether the optimal power lies in (0.05, 0.95) at `B = 4`. If it does not, `T` alone may change (once), and the change and reason are recorded in the results file. No other parameter changes after the first output.

## Reproduction

`uv run python -m shiftlab.dive.rpoq_exact` (writes `outputs/rpoq_s3_structure_v1/results.json`). Tests: `uv run pytest tests/test_rpoq_exact.py`.

## Calibration record (appended 2026-10-29, before the registered run)

Scratch run at the frozen parameters (`T` varied, optimal power only, alternative law): `B=4` power 0.3488 (T=6), 0.3635 (T=8), 0.3684 (T=10), 0.3697 (T=12); `B=2` power at most 0.0011 (degenerate at every `T`). The `B=4` calibration condition (0.05, 0.95) holds at every `T`, so the criterion did not force a change. `T` is moved from 12 to **10** for compute cost alone: one optimal solve at `B=4` took 153 s at T=12 versus 43 s at T=10 (2.3M versus 0.9M states), and `B=6` would be costlier. This is the single permitted `T` change. `B=2` has power near zero, so C2 can only be met at larger budgets; it is reported, not removed.
