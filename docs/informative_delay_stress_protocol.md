# Informative-delay power and latency stress test

**Status:** frozen development protocol; descriptive only. It is not a false-alarm calibration, confirmation, or algorithm novelty test.

## Question

The event-prefix argument establishes false-alarm control from a valid event-time process under its conditional-mean null. It does not say how outcome-dependent response times affect detection delay, label use, or the adaptive query path. This screen measures those operational effects.

## Registered design

- Generate iid event streams on CUDA when available (CPU remains supported); use 30 independent seeds per scenario and a horizon of 2,400 events.
- Use the existing fixed paired policy and proxy, the existing 20% hard query cap, history-only query propensity with `q_min=0.05`, and the fixed-stake mixture e-process. Compare its globally fixed support bound with the eventwise bound predictable from the selected propensity.
- Reuse each scenario's generated contexts, query uniforms, and outcome uniforms across bound modes and delay profiles. Bound-mode policies may diverge after different evidence histories; this remains a paired system comparison.
- Include the exact marginal null, strict-negative control, and the four existing boundary-harm doses.
- Compare a fixed 12-event delay with two evaluator-side informative profiles. `positive_fast` assigns delay 1 to a queried positive paired-cost contrast (harm evidence) and 12 to a negative contrast. `positive_slow` reverses those assignments. A queried label's contrast is generated only after its request is selected, and the contrast and delay assignment remain evaluator-only until arrival.
- The learner commits increments only through the contiguous event-time prefix. It does not use delay values, missingness, or pending status as direct evidence. Query choices can still react to the evidence prefix that becomes available at each event.

## Outcomes and interpretation

Report post-onset detection, event-time and wall-time delay, onset reach, labels spent, processed prefix length, average response delay by contrast sign, and evaluator-known exposed harm. Check every requested label arrives exactly once, no query cap is exceeded, every committed row belongs to the resolved prefix, and all eventwise increments respect their registered support bounds.

The 30-seed null counts are software diagnostics only. Do not use them to estimate or certify a nominal 5% error rate. The event-prefix proof supplies the stated error guarantee only when the event-time conditional-mean null and predictable support conditions hold given the full history used by querying. Informative delays can alter operational power and wall-clock delay without invalidating that pathwise guarantee. This experiment does not test serial dependence, policy adaptation, selective non-arrival, or a monitor that uses latency as evidence.

No figure is required for this screen. If one is later requested, use PaperBanana; do not substitute another visual generator.

## Reproduction

```powershell
uv run python scripts/validate_delayed_history_predictable_bounds.py --streams 30 --horizon 2400 --seed 27804027 --delay 12 --delay-profile fixed --device cuda --output outputs/informative_delay_fixed_30
uv run python scripts/validate_delayed_history_predictable_bounds.py --streams 30 --horizon 2400 --seed 27804027 --delay 12 --delay-profile positive_fast --device cuda --output outputs/informative_delay_positive_fast_30
uv run python scripts/validate_delayed_history_predictable_bounds.py --streams 30 --horizon 2400 --seed 27804027 --delay 12 --delay-profile positive_slow --device cuda --output outputs/informative_delay_positive_slow_30
```
