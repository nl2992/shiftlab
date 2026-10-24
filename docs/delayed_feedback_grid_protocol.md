# Delayed-feedback design grid

**Status:** completed exploratory development grid. No threshold or method was selected from these
outcomes; they require independent calibration and confirmation.

## Research question

How do query budget, harm onset and harm magnitude affect event-time detection and wall-clock delay
for the paired-cost e-process and the source/target risk-confidence-sequence comparator under delayed
labels? Does out-of-order feedback change event-time results when the monitor buffers evidence in
event order?

The delayed-label risk-monitoring problem is already addressed by Podkopaev and Ramdas (2022). This
grid is a comparison on a paired decision-cost simulator, not a novelty claim. The risk-CS baseline
uses the source-upper/target-lower architecture with this repo's CM-EB target bound and Hoeffding
source bound; it is not a full reproduction.

## Frozen grid

The committed `DelayedGridConfig` uses 30 seeds (`20262000`–`20262029`), 3,000 source and target
events, query rates `0.10`, `0.25`, and `0.50`, harm onsets at 20% and 60% of the stream, and
expected paired-cost increases `0.12` and `0.24`. Both stationary and benign-variance-shift controls
are included at every query rate. Delays are fixed at three time units or discrete uniform on
`{0, ..., 6}`; both have mean three. Within a seed and parameter cell, both methods share outcomes
and the query mask across the two delay conditions. The source-risk sample is independently drawn.

The world construction and monitor assumptions are detailed in
[`delayed_feedback_protocol.md`](delayed_feedback_protocol.md). In the grid, the expected contrast
increase determines the post-onset probability of a positive `+0.60` contrast, while the negative
contrast is `-0.60`. The benign control changes contrast amplitude from `0.60` to `0.25` without
changing its zero conditional mean. The methods are the Hoeffding paired-cost e-process, a fixed-
start bounded-mean betting process, an eight-start equal-weight mixture of that same betting
process, the source-risk / target-risk confidence-bound comparator, and no-query hold. The eight
start positions are fixed before outcomes at rounded fractions `0/8` through `7/8` of the expected
query horizon. For each start component, the process is one before its start and a valid e-process
afterward. Their fixed convex mixture is an e-process by linearity; the `log(8)` mixture penalty is
the price for unknown start time. This is an established construction and comparator, not a new
algorithm claim. The paired conditional-mean tests and source-to-running-target risk test do not
have identical nulls, so their power rows are not direct same-hypothesis comparisons.

The exploratory design has 1,080 stream cells and 5,400 method rows. Event-time summaries use only
the fixed-delay copy so the same seed is not counted twice. The runner checks that alarms, detection,
false escalation and processed prefix are identical across delay copies. Wall-time summaries retain
both delay schedules and measure pending-label blocking.

## Reproduction

From the repository root in PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m shiftlab.dive.delayed_grid --device cuda --output-dir outputs/delayed_feedback_grid_development
```

The RTX 4060 is used for stream generation; the sequential monitor updates run on CPU. The manifest
records configuration, hardware/software environment, event-time invariance, metric checksum and
source hashes. CPU mode remains available for smoke tests.

## Findings

In the late-onset (60%), weaker-effect (0.12) cells, the restart mixture detected 8/30, 16/30 and
27/30 as query rate increased from 0.10 to 0.50; full-stream betting detected 2/30, 4/30 and 5/30,
and the Hoeffding and risk-CS procedures detected none. With late, stronger harm (0.24), the restart
mixture detected 25/30, 30/30 and 30/30; full-stream betting detected 7/30, 24/30 and 30/30, while
the Hoeffding procedure detected 0/30, 5/30 and 17/30. The restart mixture also improved detection
over full-stream betting in early-harm cells, though at query rate 0.10 under early strong harm the
risk-CS comparator detected 10/30, full-stream betting 28/30, and the restart mixture 30/30. These
results support the fixed-start mixture as a promising baseline for late-onset alternatives, not a
novel contribution or a selected lead method.

False escalation was 0/30 for the restart mixture and Hoeffding procedure in every stationary and
benign-shift cell. The paired full-stream betting process had 2/30 false escalations in both null
scenarios at query rate 0.10 and 0/30 in the other cells. These small samples neither calibrate nor
disprove the nominal 5% guarantee: 0/30 has a one-sided exact 95% upper rate bound near 9.5%, and
2/30 is very uncertain. The subsequent independent 2,000-seed null calibration and disjoint primary
alternative confirmation are documented in
[`delayed_null_calibration_protocol.md`](delayed_null_calibration_protocol.md). Fixed and
variable-delay copies reuse the same seed outcomes and must not be pooled as independent runs. The
invariance check confirms that event-time evidence is unchanged by these outcome-independent delay
schemes when the event order is preserved; this is a simulation invariant, not a new validity theorem.

## Artifacts and next step

The row-level metrics, one-copy-per-seed event summary, wall-delay summary, report and manifest are
in [`outputs/delayed_feedback_grid_development/`](../outputs/delayed_feedback_grid_development/).
No figure is included: project guidance requires PaperBanana for visuals, and no PaperBanana tool is
available in this session.

The independent calibration and two disjoint primary confirmations are complete; see
[`delayed_null_calibration_protocol.md`](delayed_null_calibration_protocol.md) for the full results.
The restart mixture detected 933/2,000 and 895/2,000 late-onset weak-harm streams on the two blocks,
versus 100/2,000 for full-stream betting on each; both paired tests strongly favored the restart
mixture. The subsequent 12-cell, 2,000-seed-per-cell alternative grid found positive restart-mixture
detection gains in all cells, from 1.2 to 68.4 percentage points. Every cellwise exact McNemar test
remained significant after Holm correction (largest adjusted p=3.03e-6). The largest gain was for
late, weak harm at a 50% query rate; early strong-harm cells were near ceiling for both procedures.
These are results for registered synthetic settings. The restart mixture remains a standard e-process
construction, not a novelty claim or universal ranking. Full metrics, confidence intervals, paired
tests and log-scale tiny p-values are in
[`outputs/delayed_feedback_grid_confirmation_2000/`](../outputs/delayed_feedback_grid_confirmation_2000/).
