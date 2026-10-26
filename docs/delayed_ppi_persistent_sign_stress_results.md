# Delayed PPI persistent-sign and informative-delay stress results

**Status: completed diagnostic screen, 2026-10-25, CUDA.** The run uses 2,000 independent seeds per sign-persistence level, three outcome-dependent delay profiles, and two established monitors. These are zero-proxy PPI increments under an exact 480-label cap. The frozen design is in [`delayed_ppi_persistent_sign_stress_protocol.md`](delayed_ppi_persistent_sign_stress_protocol.md); all stream rows, summaries, checksums, and the environment manifest are in [`outputs/delayed_ppi_assumption_stress_2000_registered/`](../outputs/delayed_ppi_assumption_stress_2000_registered/).

## Findings

| Sign persistence `rho` | Empirical lag-1 correlation | Fixed-start mixture alarms | Full-stream alarms | Interpretation |
| ---: | ---: | ---: | ---: | --- |
| 0.00 | 0.000 | 31/2,000 (1.55%; 97.5% one-sided upper 2.19%) | 49/2,000 (2.45%; upper 3.23%) | IID implementation/calibration control stays below 5%. |
| 0.50 | 0.500 | 145/2,000 (7.25%; upper 8.48%) | 138/2,000 (6.90%; upper 8.10%) | Marginal mean is zero, but the conditional-mean null fails. |
| 0.90 | 0.900 | 1,449/2,000 (72.45%; upper 74.40%) | 830/2,000 (41.50%; upper 43.70%) | Strongly predictable signs drive frequent threshold crossings. |
| 0.98 | 0.980 | 1,967/2,000 (98.35%; upper 98.86%) | 1,408/2,000 (70.40%; upper 72.39%) | The monitor is not calibrated for this conditional-mean-violating process. |

The monitor assumption is `E[Z_t | F_(t-1)] <= 0`, not merely `E[Z_t] <= 0`. In this Markov-sign generator, `E[Z_t | Z_(t-1)] = rho Z_(t-1)`. Thus the `rho>0` alarm fractions are stress diagnostics under a violated null, not false-alarm estimates against the theorem and not evidence of monitor failure under its stated assumptions. The result establishes that a marginally balanced but serially predictable outcome generator cannot be used as the null calibration for this e-process. The fixed-start mixture is an established convex mixture; its larger alarm fraction at high `rho` does not make it preferable.

Outcome-dependent delays changed alarm availability but not the event-time alarm or query schedule for any paired stream. With fixed 12-event delays, an alarm becomes available 12 events after its event-time crossing when that queried label blocks the prefix. In the `positive_fast` profile, conditional mean wall-time delay among alarms was smaller; for the full-stream monitor at `rho=0.90`, it was 0.13 events versus 12.00 under `fixed12` and `positive_slow`. This is operational latency behavior, not extra evidence: delay and non-arrival never enter the monitor. All three profiles had exactly the same event-time alarms, label counts, and schedules within each seed.

All 48,000 stream-monitor rows were present with unique keys. The mean request count was 472.55 and no stream exceeded 480. Every delayed label was represented by a finite availability time, event-time evidence was evaluated in prefix order, and query schedules matched across monitor and delay-profile pairs. The independent CUDA implementation used `NVIDIA GeForce RTX 4060 Laptop GPU`.

## Scope and next step

This screen tests a zero-proxy, fixed-propensity special case. It does not calibrate the full history-adaptive querying policy under outcome-dependent delay, and it does not provide a dependence-aware replacement. The event-prefix proof permits arbitrary finite outcome-dependent delays when the event-time conditional-mean null is valid and delays are not used to choose an action or evidence increment. Persistent signs require either a defensible conditional-null model, a different estimand, or a proof-backed dependence-aware method. The next experiment should first test informative-delay latency in the existing adaptive PPI replay under a valid IID conditional null, then isolate persistent-sign data as an explicit alternative/model-misspecification stress rather than relabeling it a null.

No figure was planned or generated.
