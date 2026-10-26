# Adaptive delayed PPI under outcome-dependent response times

**Status: frozen before execution; independent null calibration for a registered synthetic design.**

## Question and null

Does the existing history-adaptive PPI pipeline retain its finite-sample false-escalation control when queried labels have outcome-dependent response times, provided response time is not used to select the current query or construct evidence? The target is a stationary IID stream with randomized `X_t ∈ {-1,+1}` and `E[Z_t | X_t]=0.35 X_t`, so `E[Z_t | G_(t-1)] = 0 <= epsilon=0.05`. The source-trained proxy uses source data only. The current propensity is selected from the prior committed event prefix before the current target outcome and query coin. This satisfies the registered population conditional-mean null; no conditional-on-current-context null is asserted.

## Frozen design

- Use 250 fresh seeds, 20410000–20410249, 2,400 target events, 1,200 source events, alpha 0.05, and the pathwise 480-label cap. Generate streams on CUDA when available; retain a CPU path.
- Compare query rules `uniform_eventwise` and `evidence_a0p025_p0p5_eventwise`, each crossed with `full_stream` and the equal-weight fixed-start mixture at events 0, 300, ..., 2,100. Each complete monitor/query combination chooses its own history-predictable propensities; continue through the full horizon after alarms.
- Cross each arm with `fixed12`, `positive_fast`, and `positive_slow` delays. For a queried positive paired-cost contrast, delays are `(12, 0, 12)` respectively; for a queried negative contrast, delays are `(12, 12, 0)`. Delay is generated only after the query and outcome. It is never visible to the propensity or monitor before arrival.
- Process labels only through the contiguous event-time resolved prefix and drain all finite delays. Every arm uses shared per-seed source/target streams and query random numbers where its own adaptive path permits; changing the delay can change later adaptive propensities, so path equality across delay profiles is not required.

## Gate and reporting

There are 12 complete-policy cells. Compute exact one-sided Clopper–Pearson upper limits at cell alpha `0.05/12`; the calibration gate passes only if every upper limit is at most 0.05, every expected row exists with a unique key, all caps hold, all labels resolve, and all 2,400 registered event updates are processed. Report alarm rate, exact limits, mean labels/events, alarms' event and wall delays, and delay-sign latency. Passing is finite evidence for these IID source/target generators and this delay design, not a proof, power comparison, or real-world guarantee. A failed gate means this frozen policy family does not advance under this calibration block; do not tune on these seeds.

No visual is planned. Use PaperBanana for any future research visual.

## Reproduction

```powershell
uv run shiftlab-dive-delayed-ppi-adaptive-informative-calibrate --device cuda --output-dir outputs/delayed_ppi_adaptive_informative_delay_250
```
