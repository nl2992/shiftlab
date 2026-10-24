# Frozen center-prior validation protocol

## Status and question

This protocol was written after the development screen selected `center_beta_2_2`, before any
fresh validation outcomes were inspected. It asks whether the fixed Beta(2,2) prior over eight
start positions improves the existing uniform eight-start mixture. This is a comparison between
two established e-process mixtures, not a claim of a new sequential-testing method.

The center prior is the mass of Beta(2,2) on eight equal-width bins of normalized start time:
`[0.04296875, 0.11328125, 0.16015625, 0.18359375, 0.18359375, 0.16015625, 0.11328125, 0.04296875]`.
The reference assigns `0.125` to each start. Both are fixed before each stream and are convex
mixtures of the same bounded-mean e-process components, preserving the component mixture's
conditional-mean validity under its registered filtration.

## Fresh blocks and conditions

Null calibration uses seeds `20274000–20275999` for each of the stationary and benign variance-shift
controls, crossed with query rates `0.10`, `0.25`, and `0.50`. Alternative confirmation uses the
disjoint seed block `20276000–20277999` in each of 12 cells: the same query rates, onset fractions
`0.20` and `0.60`, and expected paired-cost increases `0.12` and `0.24`. Each stream has 3,000
prediction events, a materiality margin of `0.02`, amplitude `0.60`, and outcome-independent delays
uniform on `{0, ..., 6}`. CUDA is the requested stream-generation device; monitor evaluation is on
CPU. No data-dependent tuning is performed on these blocks.

## Analysis frozen in advance

For each of the 12 null cells (two scenarios × three query rates × two methods), report the false
escalation count and rate. Give one-sided exact Clopper–Pearson upper bounds with Bonferroni
simultaneous 95% coverage over all 12 cells. These Monte Carlo rates check the implementation and
simulator; the mathematical guarantee still depends on the eventwise bounded conditional-mean null,
predictable query selection, and delays that are independent of current outcomes.

For each alternative cell, pair center and uniform alarms on the same generated stream. Report
detection rate, paired discordances and the exact two-sided McNemar test. Apply Holm correction across
the 12 cellwise tests. Report event and wall-time delay among detections, treating nondetections as
censored rather than assigning a finite delay. The primary practical effect is the macro-cell
detection difference; cellwise tests show where that average comes from. Do not select a new prior or
change the weights based on this confirmation block.

Retain the center prior only if it has higher macro-cell detection and the Holm-adjusted paired
comparison favors it without a material loss in the weakest registered cell, while both methods
remain compatible with the simultaneous null bounds. Otherwise keep the uniform mixture. Any further
prior search requires another disjoint development/confirmation split.

## Reproduction

From the repository root:

```powershell
uv run shiftlab-dive-start-prior-validation --device cuda --null-streams 2000 --alternative-seeds-per-cell 2000 --null-seed-offset 20274000 --alternative-seed-offset 20276000 --output-dir outputs/start_prior_validation
```

The runner writes per-stream Parquet and CSV data, cell summaries, exact test results, an environment
and code-hash manifest, and a report. No figure is required for this table-based test. If a visual is
later useful, create it with PaperBanana as requested by the project owner.
