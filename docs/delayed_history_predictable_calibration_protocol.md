# Independent delayed history-predictable null calibration

**Status:** frozen before execution, 2026-10-24. The exploratory 30-stream screen and its seeds are excluded.

## Question and arms

Calibrate false escalation for the two delayed, history-only evidence-directed query systems before considering any delayed harm confirmation. The primary comparison is not a superiority test: it asks whether each arm's family-adjusted exact upper limit is at most 5% under both registered nonpositive-mean controls.

The arms share `q_min=0.05`, `q_max=0.80`, a 20% hard request cap, the same seed-generated contexts, outcomes, query uniforms, 12-event deterministic feedback delay, event-order prefix rule, stakes, proxy, and fixed action pair. The fixed arm uses `B=M(2/q_min-1)`; the candidate uses `B_t=M(2/q_t-1)`. These are different adaptive monitor-query systems because evidence paths and propensities can diverge.

## Frozen calibration design

- 2,000 independent streams per null scenario and arm; total 8,000 stream-arm rows.
- Exact-zero mixed-sign null: registered marginal expected paired contrast is zero and has nonzero variance.
- Strict-negative control: registered marginal expected paired contrast is −0.20.
- Horizon 2,400; event-time onset marker 1,200; label delay 12; per-stream request cap 480.
- Root seed `27304027`. The two scenario blocks use disjoint stream seed ranges; fixed and predictable arms are paired within each scenario block. Seeds from the 30-stream development screen are not reused.
- Synthetic random streams are generated on CUDA when requested. The state recursion is replayed with NumPy because its event/arrival ordering is sequential; the GPU-generated streams are transferred once per arm to the CPU monitor.
- Labels are reserved against the cap at request time. Queried outcomes are read only at the registered arrival. Evidence is committed in event order, and every request and event-specific support bound is checked.

## Primary gate

There are four calibration cells: two nulls crossed with two arms. Compute one-sided Clopper–Pearson upper limits with per-cell alpha `0.05/4=0.0125`, giving at least 95% simultaneous coverage over this family. Retain an arm for a disjoint harm confirmation only if both of its simultaneous upper limits are no greater than 0.05 and every run invariant passes. If either arm fails, do not use it as a statistically calibrated monitor under this design. The observed finite-run rate is descriptive; the supermartingale argument still depends on the assumptions stated in `delayed_history_predictable_bound_protocol.md`.

Do not tune the propensity, bound, delay, threshold, or scenario after opening the calibration. A passing result permits a separately frozen harm-power confirmation; it does not establish power, delayed-feedback validity under dependence, or method novelty.

No research figure is required. If one is later made, it must use PaperBanana; no substitute figure generator is permitted.

## Reproduction

```powershell
uv run python scripts/calibrate_delayed_history_predictable_bounds.py --streams 2000 --seed 27304027 --delay 12 --device cuda --output outputs/delayed_history_predictable_calibration_2000
uv run pytest tests/test_delayed_history_predictable_bounds.py tests/test_delayed_feedback.py -q
```
