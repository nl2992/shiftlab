# EIA-930 F8 CAMS learning-rate follow-up

**Purpose:** a bounded development-only test of whether CAMS's convergence schedule can be adjusted
to close the observed F8 replay gap. The EIA 2022–2023 outcomes are already development data; this
follow-up is exploratory and cannot serve as confirmation.

## Hypothesis

In the 11 fixed EIA BAs with an F8 rare-informative profile, CAMS's default
`eta_t = sqrt(P/t)` may learn the better constant model too slowly. Multiplying that schedule by a
fixed scale may reduce prediction loss before the horizon ends. The three scales `{1.5, 2, 3}` are a
small, frozen development grid; no further values will be tried in this follow-up. This is a
published-method hyperparameter adjustment, not a novelty claim. CAMS itself was the best method
in the preceding full panel.

## Data and method contract

Use the same all-matching-BA panel, 2021-only fitted models, 2022–2023 development timestamps,
contiguous 2,000-event blocks, delayed one-hour labels, `B=200`, label price `.05`, switch cost `5`,
and `alpha=.05` from the preceding frozen protocol. Reconstruct the model pair and require exact
agreement with the committed profile artifact before running any policy. No 2024+ rows are allowed.

The candidate variants change only CAMS's learning rate to `s * sqrt(P/t)` for `s` in `{1.5, 2, 3}`.
All other code, advice, query probability, deployment mapping, costs and feedback behavior are
identical to `cams_adapter`. Include native published `cams_adapter` and the author-code `CAMS-MAX`
adapter as matched comparators. Pair random seeds within episode and preserve the full metrics from
the same simulator. Compare against the already frozen complete baseline panel; CAMS is the
prespecified primary comparator because it was its lowest-cost method.

## Analysis and stop rule

Report each scale's mean cost decomposition and candidate-minus-CAMS contrast by BA, plus
episode-clustered paired 95% intervals and an equal-BA hierarchical interval. Select the scale with
the lowest equal-BA mean on development solely for a later holdout test. A development signal
requires at least 5 cost units saved per episode versus CAMS, a paired interval below zero in at
least 8 of 11 BAs, and a hierarchical interval below zero. If no scale clears the gate, stop this
F8/CAMS-adjustment lane; do not inspect 2024+ for it.

The 11 BAs are correlated subclusters under one provider. The cost contract is hypothetical
Failure Atlas units, not market utility. EIA historical revisions and simulated feedback remain
limitations. CAMS and CAMS-MAX do not provide the registered conditional-null guarantee, and this
stream has no known-null episodes. A positive development signal would permit, but not prove, a
separate frozen confirmation using untouched chronology and an independent provider/domain. Any
positive adjusted-CAMS result would remain a standard hyperparameter adaptation unless a targeted
prior-art audit established a distinct contribution.

## Reproduction

```bash
uv run python scripts/sota_sprint/eia930/run_f8_cams_eta_followup.py
uv run python research/scoped_method/pilots/eia930_f8_cams_eta_followup_20261107/analyze.py
```
