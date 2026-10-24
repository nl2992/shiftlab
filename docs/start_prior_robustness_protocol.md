# Fixed-prior robustness screen

## Purpose

The center Beta(2,2) prior showed a modest advantage under one query-horizon specification and
uniform delays from zero through six. This frozen development screen tests whether that result holds
when the monitor's planned horizon differs from the realized horizon and when feedback delay changes.
It also compares the other fixed Beta priors screened during development. These remain standard fixed
convex mixtures; the screen does not claim a new method.

## Methods and design

Compare the uniform Beta(1,1), early Beta(1,2), late Beta(2,1), center Beta(2,2), and edge
Beta(0.5,0.5) start-time priors, plus full-stream bounded betting. Each prior remains fixed for the
entire stream. For expected horizon multiplier `h`, the eight component start locations are
`round(h * q * n * k/8)`, `k=0,...,7`, where `q` is the label query probability and `n=3,000`.
Multipliers are `{0.5, 1.0, 1.5}`. Values above one intentionally place later components beyond
the expected stream horizon; this measures misspecification cost rather than changing weights after
seeing evidence.

Alternative cells cross query rates `{0.10, 0.25, 0.50}`, onset fractions `{0.20, 0.60, 0.80}`,
paired-cost increases `{0.12, 0.24}`, all three horizon multipliers, and four delay laws: fixed zero,
uniform `{0,...,6}`, uniform `{0,...,12}`, and fixed twelve. There are 216 cells and 200 paired
streams per cell using seeds `20278000–20278199`. Stream outcomes and query uniforms are shared
across priors and delay laws; an independent delay-uniform stream is transformed to each delay law.

Null calibration crosses stationary and benign-variance-shift nulls, query rates `{0.10,0.25,0.50}`,
the three horizon multipliers, and four delay laws. It uses 500 streams per cell from seeds
`20280000–20280499`. Report one-sided exact Clopper–Pearson upper bounds with simultaneous 95%
Bonferroni coverage across every method/null cell. These 500-stream bounds are screening diagnostics,
not final certification.

## Analysis

For alternatives, report detection rate, pre-onset escalations, and conditional event/wall delay.
Compare each nonuniform prior and full-stream betting with uniform using exact paired two-sided
McNemar tests per cell; apply Holm correction across the complete family of method-by-cell tests.
Summarize macro detection separately by delay law and horizon multiplier. Do not tune priors or
select a final method on these robustness seeds. Any candidate emerging from this screen needs a
new null calibration and disjoint alternative confirmation before being used as the default.

The e-process guarantee still assumes bounded contrasts, an eventwise conditional-mean null, a
predictable query process, and feedback delays independent of current outcomes. Delay severity and
horizon mismatch affect empirical power and latency; they do not relax these assumptions.

## Reproduction

```powershell
uv run shiftlab-dive-start-prior-robustness --device cuda --seeds-per-cell 200 --null-streams 500 --alternative-seed-offset 20278000 --null-seed-offset 20280000 --output-dir outputs/start_prior_robustness
```

The runner writes per-stream Parquet/CSV metrics, null and alternative summaries, paired tests,
environment and code hashes, and checksums. This is a table-based experiment; if a visual is useful,
make it with PaperBanana as requested by the project owner.
