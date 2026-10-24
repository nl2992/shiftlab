# Delayed-feedback decision-harm benchmark

**Status:** completed development pilot, not a preregistered or confirmatory study.

## Question

When queried labels arrive after the prediction event, how does preserving event order affect
decision-harm monitoring, and how does the paired-cost monitor compare with a source-risk / target-risk
confidence-bound procedure on the same feedback?

This is an implementation and comparator study. Podkopaev and Ramdas (2022) already develop
sequential risk monitoring when labels are delayed or released in batches. The pilot therefore does
not treat delayed feedback as a novelty claim. The source/target comparator applies that paper's
confidence-bound architecture to a bounded transform of the paired decision-cost contrast, using
this repository's CM-EB target lower confidence sequence and a fixed-sample Hoeffding source upper
bound. It is not a full reproduction of their implementation.

## Design

The committed defaults in `DelayedBenchmarkConfig` use 30 paired seeds (`20261024`–`20261053`),
3,000 source and 3,000 target events, independent Bernoulli label querying at probability 0.5, and
an anytime threshold of 0.05. Each stream is run under two label-delay schemes with equal mean delay:
fixed three event-time units, and a discrete uniform delay from zero through six units. Query
randomization and delays are generated independently of outcomes. The same underlying source,
target outcomes and query mask are used across delay schemes for a seed.

The three worlds are:

- **Stationary null:** paired cost contrast is `±0.60` with equal probability throughout.
- **Benign variance shift:** after 40% of the target horizon, contrast amplitude falls from `0.60`
  to `0.25`, keeping its conditional mean at zero.
- **Boundary harm:** after 40% of the horizon, the probability of a `+0.60` contrast rises to 0.70,
  so expected contrast rises by 0.24, equivalent to a 0.12 increase on the normalized `[0,1]` risk
  scale. The margin is 0.02 on the paired-contrast scale.

Both monitoring methods see the same queried outcomes. The paired-cost e-process updates on queried
contrasts and tests the eventwise null
`E[C_t | F_(t-1)] <= 0.02`, with known support `[-1,1]`. The source/target risk comparator maps
`C` to `(C + 1) / 2`, computes a fixed source-risk upper bound with Hoeffding at alpha/2, and
compares it with a target CM-EB lower confidence sequence at alpha/2 plus half the contrast-scale
margin. The source sample is independent of target outcomes. Both monitors stop updating after
their first alarm for reported evidence counts, while the simulated shared label schedule continues
through the fixed horizon to make stream-level comparisons possible. `no_query_hold` spends zero
labels and never alarms; it is a resource-floor reference, not a label-matched monitor.

All delayed labels are passed through `EventOrderBuffer`. It releases the contiguous resolved query
prefix in event order. An alarm's wall time is the arrival time at which its full evidence prefix
becomes available; event delay and wall delay are reported separately. A monitor with no alarm has
right-censored delay and is not assigned a numeric delay.

## Reproduction

From the repository root in PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m shiftlab.dive.delayed_benchmark --device cuda --output-dir outputs/delayed_feedback_development
```

The run uses CUDA for random stream generation and CPU for the sequential confidence-bound updates.
The `auto` and `cpu` options are available. The manifest records the resolved device, package and
hardware environment, full configuration, metric checksum and hashes of the benchmark, buffer and
confidence-sequence implementation.

## Pilot findings

The development run detected 30/30 boundary-harm streams with the paired-cost e-process and 23/30
with the source/target risk confidence-bound comparator, under both delay schemes. The discordant
paired outcomes were seven e-process-only detections and no risk-CS-only detections; the unadjusted
two-sided exact McNemar p-value is 0.0156. Median event detection delays were 1,010.5 events for the
paired e-process and 1,342 for the source/target risk CS. Under uniform delays, median wall delays
were 1,013.5 and 1,348 events, respectively. No method escalated in either null control in any
30-seed cell. These are development results, not confirmatory evidence: zero false alarms in 30
independent streams has a one-sided exact 95% upper bound of about 9.5%. The repeated fixed and
variable-delay outcomes reuse each seed's same underlying target stream and must not be counted as
60 independent streams.

The risk-CS comparator's later detections are consistent with its running target-risk lower bound
including the pre-change portion of the stream. This is a benchmark finding under the chosen
synthetic design; it does not show that the paired e-process dominates risk monitoring generally.

## Assumptions and limits

The paired e-process's Ville guarantee requires the registered bounded support and its eventwise
conditional-mean null to hold for the queried event sequence, with query probabilities chosen
without observing the current outcome. The risk-CS comparator requires bounded losses, an
independent fixed source sample, a valid source upper bound, and a valid target lower confidence
sequence under the declared feedback filtration. In this synthetic design, query inclusion and
delay are independent of outcomes and the buffer preserves target event order. A pending later
label can postpone an alarm until the missing earlier label arrives; the pilot records this latency.

The pilot does not test outcome-dependent delays, serial dependence, adaptive model updates,
policy-induced outcomes, unknown cost bounds, repeated candidate promotion, or alternatives whose
harm onset is selected after seeing outcomes. Its 30-stream null cells do not calibrate the nominal
error rate. The methods test different null formulations (eventwise conditional paired harm versus
source-to-running-target risk increase), so the power comparison is informative for this simulator
but is not an apples-to-apples claim about general procedures. No new algorithm or novelty claim is
made.

The metrics, report and manifest are in
[`outputs/delayed_feedback_development/`](../outputs/delayed_feedback_development/). No plot is
included because project guidance requires PaperBanana for visuals and no PaperBanana tool is
available in this session.

## Next milestone

Before any confirmatory power comparison, freeze the target estimand and align both methods to the
same null as far as their theory allows. Run at least 2,000 independent streams per nondegenerate
null cell to assess false escalation, using disjoint seeds from power evaluation. Then use an
independent alternative seed block and report exact binomial intervals, paired detection contrasts,
censored event/wall delays, query count, processed-prefix length and pending-label latency. Add
outcome-dependent delay only as a clearly out-of-guarantee stress test. Reproduce the published
Podkopaev–Ramdas method more faithfully before treating its comparator row as a literature-grade
baseline.
