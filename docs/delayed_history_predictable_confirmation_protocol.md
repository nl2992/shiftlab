# Delayed history-predictable bound: independent harm confirmation

**Status:** frozen after the development grid and fresh independent null calibration, before opening confirmation outcomes; 2026-10-24.

## Candidate and comparator

The candidate is the history-only evidence-directed query policy with `q_min=0.05`, `q_max=0.80`, eventwise PPI bound `B_t=M(2/q_t−1)`, 20% request cap, event-order prefix updates, and deterministic outcome-independent feedback delay `D=12`. The comparator uses the identical query policy and delayed-feedback protocol with fixed bound `B=M(2/q_min−1)`. Both arms share generated event streams and query uniforms within dose; each arm has its own evidence history and therefore may have a different adaptive query path.

The candidate passed the fresh selected-configuration calibration on seed root `27504027`, including four-cell family-adjusted one-sided exact upper limits at or below 5%. The confirmation is permitted only after that pass and uses no calibration or development seeds.

## Frozen alternative block

- 2,000 paired streams per harm dose, 8,000 per arm, 16,000 stream-arm rows total.
- Four localized-harm doses `delta ∈ {0.04, 0.20, 0.40, 0.60}` with onset index 1,200 and horizon 2,400.
- Root seed `27604027`; each dose uses a disjoint seed block of 2,000 streams. Both arms share the dose's CUDA-generated contexts, outcomes, and query uniforms.
- Queried labels arrive 12 events after request. Query spend is reserved immediately against the 480-label cap. The event-order evidence prefix is flushed after the horizon.
- Every stream remains in the detection denominator. An onset not reached before monitor stopping or horizon is a nondetection. Report event-time and wall-time delay separately.
- CUDA generates streams; CPU NumPy replays the sequential monitor. The equivalence tests compare this replay against the slower Torch reference.

## Primary estimand and retention rule

For each stream ID, average the predictable-minus-fixed detection indicators equally across the four harm doses, then average over stream IDs. Resample whole stream IDs for a two-sided 95% paired bootstrap interval (10,000 replicates). Retain the candidate only if:

1. The lower interval limit for the macro detection gain is greater than +0.02.
2. The upper interval limit for the paired label-count difference is at most zero.
3. Every simultaneous one-sided 95% upper limit in the independent four-cell null calibration is at most 0.05.

The independent calibration is `outputs/delayed_history_predictable_selected_calibration_2000/`; its metrics and manifest checksums are verified before the confirmation starts. If any gate fails, report the negative result and stop this candidate for the registered design. Do not tune on confirmation seeds.

Report dose-specific detection, onset reach, pre-onset alarms, labels, events processed, both delay scales, and evaluator-known expected harm exposure. Dose-specific intervals are descriptive and do not override a failed primary gate. The experiment covers iid event records, a fixed action pair, complete queried labels, and deterministic outcome-independent delays only. It does not establish validity under serial dependence, informative delay or missingness, adaptive action changes, or interventions that alter outcomes. The estimator and bounded-factor construction are standard; no novelty or general superiority claim is permitted.

No figure is required. Any research figure must use PaperBanana.

## Reproduction

```powershell
uv run python scripts/confirm_delayed_history_predictable_bounds.py --streams 2000 --seed 27604027 --device cuda --output outputs/delayed_history_predictable_confirmation_2000
uv run pytest tests/test_delayed_history_predictable_bounds.py tests/test_delayed_feedback.py -q
```
