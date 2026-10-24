# Evidence-directed urgency-curve grid protocol

**Lock:** 2026-10-24, before the new-seed development screen.
**Purpose:** tune a predictable label-allocation heuristic after the first linear curve stayed near
its floor. This grid is exploratory and cannot establish false-alarm calibration or final power.

## Question and candidate family

Can a fixed, bounded transform of prior log e-evidence allocate more labels to boundary-local
decision harm under the same pathwise dollar cap than uniform querying?

For prior log e-value `L_(t-1)`, significance level `alpha`, remaining cap fraction `r_(t-1)`,
activation fraction `a`, and urgency power `gamma`, define

`v_t = clip(L_(t-1) / log(1/alpha) + a, 0, 1) ** gamma`

`q_t = q_min + (q_max - q_min) * v_t * r_(t-1)`.

Search the nine prespecified pairs `a in {0, 0.025, 0.05}` and `gamma in {0.5, 1, 2}`. The
budget taper remains linear (`r_t`) to limit the search. The positive floor, fixed support bound,
pre-outcome evidence, predictable tariff, and maximum-tariff reserve stopping rule are unchanged.
The fixed bounded betting process remains an e-process under its conditional-mean null and stated
filtration assumptions; the allocation curve itself has no optimality guarantee.

## Frozen comparison

- Compare all nine candidates with `uniform_proxy` on shared seeds and query uniforms.
- Generate 30 streams per scenario for stationary, benign nuisance, and boundary-local harm, using
  seeds `20372024` through `20372053`; these do not overlap the prior evidence-directed screen.
- Use `n=3200`, `d=16`, 10% target dollar rate, `q_min=0.05`, `q_max=0.50`, `alpha=0.05`, and a
  common e-process bound. Request CUDA; record the resolved device and environment.
- Primary selection statistic: boundary-harm detections divided by all 30 evaluator-labeled
  material-harm streams, so budget-censored onsets count as nondetections. Report reached-onset
  detection separately. Break ties by lower boundary-harm stream-mean RMSE, then lower mean spend.
  Do not select on null alarm counts from this 30-seed block.
- Record false escalations, reachability, delay, RMSE, spend, label count, horizon, propensity range,
  and cap violations. No candidate passes to confirmation unless it improves the primary statistic
  or offers a practically meaningful cost/accuracy tradeoff without degrading detection.

## Statistical and reporting limits

All nine candidates share this development block, so the selected result is subject to grid
selection and is descriptive. The 30-stream nulls cannot certify a 5% false-alarm target. A selected
candidate must receive fresh nondegenerate null calibration and a disjoint boundary/reversal
confirmation with a frozen candidate and comparison family. There is no novelty claim: predictable
propensity selection and bounded e-process betting are established constructions. Oracle truth is
used only for evaluation and reachability scoring.

## Reproduction

```powershell
uv run shiftlab-dive-hard-budget --seeds 30 --seed-offset 20372024 --n 3200 --d 16 --budget-rate 0.10 --q-min 0.05 --q-max 0.50 --common-eprocess-bound --device cuda --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy evidence_curve_a0_p0.5 evidence_curve_a0_p1 evidence_curve_a0_p2 evidence_curve_a0.025_p0.5 evidence_curve_a0.025_p1 evidence_curve_a0.025_p2 evidence_curve_a0.05_p0.5 evidence_curve_a0.05_p1 evidence_curve_a0.05_p2 --skip-figure --output outputs/evidence_urgency_curve_grid_30
