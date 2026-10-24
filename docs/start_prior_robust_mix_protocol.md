# Robust fixed-mixture start-prior development protocol

## Status and question

This is a development screen, not a confirmatory study. It asks whether shrinking the confirmed
nominal-horizon Beta(2,1) start prior toward the uniform eight-start prior can improve worst-onset
detection while preserving calibration on independent null streams.

For each query rate, let `w_late` be the eight-bin prior induced by Beta(2,1), and let `w_unif` be
uniform. Evaluate the five frozen mixtures

    w_rho = rho * w_late + (1 - rho) * w_unif,
    rho in {0, 0.25, 0.50, 0.75, 1}.

Each vector is nonnegative and sums to one. Since every start-specific process is a nonnegative
supermartingale under the same eventwise conditional-mean null and filtration, each fixed convex
mixture remains a supermartingale. Choosing `rho` after this development block does not invalidate
a later procedure if it is frozen before an independent monitor stream. No within-stream adaptive
reweighting is introduced.

## Development alternatives and objective

Cross query rates `{0.10, 0.25, 0.50}`, harm-onset fractions `{0.20, 0.60, 0.80}`, and paired-cost
increases `{0.12, 0.24}`. Use 500 paired streams in each of the 18 cells, 3,000 prediction events,
materiality margin 0.02, contrast amplitude 0.60, and independent uniform label delays on
`{0, ..., 6}`. CUDA generates streams. Reuse the same outcomes, query masks, and delays across all
five priors within a cell and seed.

The selection objective is the **maximin onset/severity-group detection rate**: first average the
detection indicator over the three query rates within each of the six `(onset, harm increase)`
groups, then maximize the minimum of those six group rates. Ties within numerical precision prefer
the smaller `rho` (more uniform weighting). Report the macro rate and all cell rates descriptively;
do not perform confirmatory inference or call the selected prior a winner from this screen.

Use alternative seeds 20290000–20290499 in each cell. These do not overlap earlier committed prior
studies.

## Null calibration screen

Cross stationary and benign-variance-shift controls with query rates `{0.10, 0.25, 0.50}`. Use
1,000 seeds per scenario from 20291000–20291999. Generate each seed once and apply all five fixed
mixtures to the same queried labels. Report exact one-sided Clopper–Pearson upper bounds with
simultaneous 95% Bonferroni coverage over 30 `(scenario, query rate, rho)` cells. This is calibration
evidence for the listed simulator controls, not a proof or the independent confirmation of the
selected prior.

## Confirmation gate

Only if a nonuniform `rho` improves the maximin group rate over both endpoints in this development
screen, and its null screen passes the prespecified 5% simultaneous-bound criterion, freeze that
single `rho` and run a separate confirmation on a fresh seed block. Confirmation must use a
seed-clustered primary interval, cellwise paired tests with Holm adjustment, and a separate null
calibration block. If no interior blend improves the maximin rate, stop this branch and keep the
simple priors as comparators.

## Reproduction

```powershell
uv run shiftlab-dive-start-prior-robust-mix --device cuda --streams-per-cell 500 --null-streams 1000 --alternative-seed-offset 20290000 --null-seed-offset 20291000 --output-dir outputs/start_prior_robust_mix_development
```

No figure is prespecified for this table-based development screen. Any later visual must use
PaperBanana and be checked against the validated analysis output.
