# Delayed feedback with history-predictable PPI bounds

**Status:** development protocol, written before the full-horizon screen. This document does not register a confirmatory result or establish a new algorithm.

## Question

Does the previously studied history-only evidence-directed query policy, paired with the eventwise prediction-powered support bound, retain useful calibration and detection behavior when queried labels arrive after a fixed delay and the monitor can use only a contiguous event-time evidence prefix?

The comparison is between two complete monitor-query systems. Both use the same evidence-directed propensity rule, query random numbers, iid event streams, hard query budget, label delay, estimator and stakes. The fixed arm uses `B = M(2/q_min - 1)`. The predictable arm uses `B_t = M(2/q_t - 1)`. Their e-process histories and later propensities can diverge, so this does not isolate the bound on identical paths.

## Arrival-time filtration and validity conditions

For event `t`, let `Z_t` be the paired decision-cost contrast, `H_t` the pre-outcome proxy, `Q_t` the randomized label-request indicator, and `q_t` the request propensity. The eventwise estimate is

`Xhat_t = H_t + Q_t (Z_t - H_t) / q_t`.

The registered screen assumes iid event records, a frozen action pair, a proxy trained on an independent source sample, `|Z_t|, |H_t| <= M`, and the population null `E[Z_t | F_(t-1)] <= 0`. Query propensities depend only on previously committed monitor evidence and query spend; the current context, outcome, and query coin are excluded. Therefore `q_t` and `B_t` are predictable from past information. Conditional on that past, randomized correction gives `E[Xhat_t | F_(t-1)] = E[Z_t | F_(t-1)] <= 0`, and `|Xhat_t| <= M(2/q_t - 1)`. Every bounded betting factor consequently has conditional expectation at most one under the stated assumptions.

At wall time `s`, the learner sees current and past contexts and only labels whose registered delay has elapsed. In the experiment, delay `D` is fixed and independent of outcomes. The learner commits increments only when all preceding event indices are resolved. The registered empirical confirmation is therefore limited to iid events, fixed delay, complete queried labels, and a frozen action pair. The broader alarm-validity argument under arbitrary finite delays does not require the arrival-time wealth to be a supermartingale: it follows because every alarm based on a contiguous resolved prefix is also a crossing of the valid event-time process. That proof and its additional conditions are in [`delayed_event_prefix_validity.md`](delayed_event_prefix_validity.md). It does not establish power or latency under informative delays, or validity under a conditional null that omits information used by the query policy.

The hard label cap is reserved at request time, including labels still pending. The monitor stops enrolling new events after its first committed alarm or once the request cap is exhausted; already registered evidence is flushed in event order. Report event-time and wall-time detection delay separately. Treat alarms revealed during the final flush as wall-time detections, and count a harm onset not reached by an enrolled event as censored nondetection.

## Development design

- CUDA-generated iid synthetic streams; CPU remains supported for tests.
- Exact-zero and strict-negative controls, plus the four registered localized-harm doses.
- 20% query budget, `q_min=0.05`, `q_max=0.80`, and a 12-event fixed delay.
- Paired fixed-bound and eventwise-bound arms, sharing source training data and all generated random numbers within a scenario.
- A small development screen is diagnostic only. It cannot certify a 5% error rate. If behavior warrants continuation, freeze fresh-seed null calibration and separate alternative confirmation protocols before running them.
- Report request labels, committed events, alarms and both delay scales; verify requested label counts never exceed the hard cap and every stored increment respects its event-specific bound.
- Research figures must use PaperBanana. If it is unavailable, do not generate a replacement figure.

## Current implementation

`scripts/validate_delayed_history_predictable_bounds.py` implements the screen. It generates the same registered iid DGP used by the immediate-feedback study, delays the learner's access to queried outcomes, reserves request budget immediately, and releases evidence in event order. The script is intentionally labeled development-only. Its small smoke outputs are not a calibration result, confirmation, or claim of superiority.

## Reproduction

```powershell
uv run python scripts/validate_delayed_history_predictable_bounds.py --streams 30 --horizon 2400 --seed 27204027 --delay 12 --device cuda --output outputs/delayed_history_predictable_development_30
uv run pytest tests/test_delayed_history_predictable_bounds.py tests/test_delayed_feedback.py -q
```
