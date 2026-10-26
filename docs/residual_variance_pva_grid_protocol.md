# Residual-variance PVA hyperparameter development protocol

## Question and scope

This alternative-only development screen asks whether the previously observed low detection rate for the residual-variance stress test is sensitive to the prior strength, prior mean, prior second moment, or stake cap of the existing predictable-variance adaptive e-process (PVA). It compares 81 fixed PVA parameter settings with the fixed-stake bounded-mean process and the uniform eight-start fixed-stake mixture. It does not propose a new betting process, establish a literature gap, or select a confirmatory winner.

## Registered design

The primary screen uses the existing `residual_variance` synthetic scenario at severities 1.5, 3.0, and 4.5; query rates 0.80 and 1.00; 60 fresh seeds per cell beginning at 31,304,000; stream length 2,400; and 16 features. Each stream is generated once and reused across query-rate arms. Each method within an arm receives the same Bernoulli query schedule, prediction-powered-inference (PPI) increments, support bound, event horizon, and hard label-cost budget. The PVA grid is the Cartesian product of prior strength `{1, 4, 16}`, prior mean `{0, 0.05, 0.10}`, prior second moment `{0.05, 0.25, 0.75}`, and maximum stake `{0.25, 0.50, 0.80}`.

When CUDA is available, synthetic stream generation and the configuration-by-stream PVA recursion run on the GPU. CPU is retained as a supported execution path. The scalar established PVA implementation is the numerical reference for tests.

## Outcomes and summaries

The stream-level record contains the first threshold crossing, whether it occurred at or after the simulator's evaluator-only material-harm onset, any pre-onset crossing, peak and terminal log e-values, number of queried labels, processed events, budget, realized spend, and evaluator-only expected excess cost. A detection is a crossing at or after the known onset; a crossing before onset is recorded separately. These are descriptive power outcomes on alternatives. They are not false-alarm-rate estimates. Report macro detection over six severity-by-query-rate cells, minimum cell detection, total pre-onset crossings, mean peak evidence, mean events, and mean queried labels.

## Analysis safeguards

The candidate parameters are fixed for an entire stream, and each stake is computed before the next increment. Thus, under the same bounded-increment and conditional-mean null assumptions as the existing PVA, the predictable betting argument is unchanged. This does not validate the PPI conditional-mean assumption under arbitrary delayed or selectively observed feedback. The alternative-only parameter search is subject to selection optimism. A candidate cannot be promoted based on this screen: it requires a separately specified null calibration and disjoint harm-confirmation seeds, with multiplicity and policy-selection effects addressed. No synthetic oracle fields enter the learner's process updates.

## Reproduction and artifacts

From the repository root, run:

```powershell
uv run python -m shiftlab.dive.residual_variance_pva_grid --device cuda
```

Use `--device cpu` when CUDA is unavailable. Optional `--seeds`, `--seed-offset`, `--n`, `--d`, and `--output-dir` arguments are recorded in the output manifest. The runner refuses to overwrite a nonempty output directory. It writes stream-level and cell/method summaries in CSV and Parquet, `results.md`, a source/environment manifest, and SHA-256 checksums. The manifest pins this protocol and the relevant source files.
