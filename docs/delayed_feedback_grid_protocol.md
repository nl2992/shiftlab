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
changing its zero conditional mean. The paired e-process tests its eventwise conditional-mean null;
the risk-CS method tests source risk against running target risk. Thus their power rows are not
identical-null comparisons.

The exploratory design has 1,080 stream cells and 3,240 method rows. Event-time summaries use only
the fixed-delay copy so the same seed is not counted twice. The runner checks that alarms, detection,
false escalation and processed prefix are identical across delay copies. Wall-time summaries retain
both delay schedules and measure pending-label blocking.

## Reproduction

From the repository root in PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m shiftlab.dive.delayed_grid --device cuda --output-dir outputs/delayed_feedback_grid_development
```

The RTX 4060 is used for stream generation; the confidence-sequence updates run on CPU. The manifest
records configuration, hardware/software environment, event-time invariance, metric checksum and
source hashes. CPU mode remains available for smoke tests.

## Findings

Among the 30-seed event-time cells, detection ranged from 0/30 to 30/30 across budgets, onset and
effect sizes. In the strongest early-onset case (`q=0.50`, onset 20%, expected contrast increase
0.24), both monitors detected 30/30; median event delay was 734.5 for the paired e-process and 965
for the risk-CS comparator. At the same effect and onset with `q=0.10`, the paired e-process detected
7/30 and the risk-CS comparator 10/30, so the latter did better in this cell. For late onset (60%)
and the weaker 0.12 contrast increase, neither method detected any of the 30 streams at any tested
query rate. For late onset with 0.24 increase, the paired e-process detected 0/30, 5/30 and 17/30 at
query rates 0.10, 0.25 and 0.50; the risk-CS comparator detected 0/30 in all three cells. The paired
e-process therefore has a strong event-time advantage in some higher-budget cells, while the grid
also exposes low-power cells and a low-budget cell favoring the risk-CS comparator.

Neither method produced a false escalation in any 30-stream stationary or benign-shift cell. This
is only a smoke diagnostic: 0/30 has a one-sided exact 95% upper error-rate bound near 9.5%. The
grid is not large enough to establish the nominal 5% level or broad power superiority. Fixed and
variable delay outputs reuse the same seed outcomes; do not pool them as independent runs. The
invariance check confirms delay changes wall-clock availability but not event-time evidence when
the event order is preserved. This is a consequence of the simulation design and buffer, not a new
statistical result.

## Artifacts and next step

The row-level metrics, one-copy-per-seed event summary, wall-delay summary, report and manifest are
in [`outputs/delayed_feedback_grid_development/`](../outputs/delayed_feedback_grid_development/).
No figure is included: project guidance requires PaperBanana for visuals, and no PaperBanana tool is
available in this session.

Next, run independent null calibration on disjoint seeds for every retained query-rate/method
configuration, then evaluate the selected frozen candidates on disjoint alternatives. The restart
mixture for late onsets should be treated as another established e-process baseline and tested on
development seeds only; a fixed mixture over valid start-specific e-processes preserves Ville
validity, but its power and multiplicity cost must be measured. Do not infer a new method from these
exploratory grid outcomes.
