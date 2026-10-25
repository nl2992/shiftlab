# Fitted context-nested promotion grid: development results

**Status:** exploratory development screen; neither calibration nor confirmation.
The design was frozen in [the protocol](contextual_budgeted_promotion_grid_protocol.md)
before this run. The seed-level metrics, aggregate tables, cellwise contrasts,
report, and checksummed manifest are versioned under
`outputs/context_budgeted_promotion_grid_30/`.

## Design and integrity checks

The CUDA run used 30 matched seeds in each of 27 settings (`n=3,200`), crossing
latent context prevalence 0.10/0.50/0.90, target probability displacement
0/0.05/0.10 around the FN=5/FP=1 decision threshold, and proxy error
0/0.10/0.25. It compared pooled candidate-rank alpha with nested equal and
validation-volume alpha under uniform direct-IPW monitoring and shared 20% and
40% hard label caps. The RTX 4060 was available and used for synthetic
generation. No figure was generated.

The run produced 4,860 seed-level method rows and 162 aggregate rows. There were
no hard-cap violations. The zero-signal condition produced zero promotions and
zero pointwise-null crossings in every cell and method. Because each cell has
only 30 seeds, zero crossings gives an exact one-sided 95% upper bound of 9.5%
for 0/30 if treated singly (the two-sided Wilson interval displayed by the
ordinary summary has upper endpoint 11.4%); neither bound establishes the
registered 5% calibration requirement.

At the 40% cap, mean label use was 631.6 of 640 and the mean processed monitor
fraction was 0.984. Averaged over all nine prevalence/error settings, no method
promoted at signal 0 or 0.05. At signal 0.10, promotion rates and mean
evaluator-known future net gains were:

| Allocation | Promotion rate | Mean future net gain |
|---|---:|---:|
| Pooled rank | 7.8% | 10.012 |
| Nested equal | 5.9% | 9.220 |
| Nested volume | 7.0% | 10.039 |

## Registered macro contrasts

At the 40% cap, the primary estimand equally averages the 18 positive-signal
prevalence/error settings. The simultaneous 97.5% paired-bootstrap intervals
for the two primary comparisons were:

| Contrast | Mean net-gain difference | Simultaneous interval |
|---|---:|---:|
| Nested volume − pooled rank | +0.014 | [−1.938, +1.998] |
| Nested volume − nested equal | +0.410 | [−0.773, +1.744] |

Neither result clears the predeclared +1 practical-utility margin. Nested volume
had higher mean net gain than pooled rank in only 1 of the 18 positive-signal
settings. The largest cellwise contrast was prevalence 0.90, signal 0.10, and
zero proxy error: nested volume exceeded pooled rank by 23.16 cumulative units
(unadjusted 95% interval [4.96, 44.33]), with promotion rates 33.3% versus
23.3%. This cell was identified after scanning the grid; its interval is
descriptive and cannot support a confirmatory claim. Nested volume versus
nested equal in this same cell was inconclusive (difference +9.28; unadjusted
95% interval [−5.88, 28.23]).

The broad development result is therefore negative for a general performance
advantage: standard nested alpha spending remains a valid, implemented option
under the registered assumptions, but the fitted-model grid does not show a
robust improvement over pooled rank. The standout common-context, high-signal
cell is a hypothesis for a newly frozen study, not evidence to select a winner.

## Interpretation and next step

The current e-process divides each small candidate-rank allocation across
contexts, which can make evidence arrive too slowly at finite horizons. One
mathematically valid alternative is to use the independent validation slice to
freeze a single context-specific composite challenger (one candidate or
incumbent fallback per context), then test that one fixed policy on the shadow
monitor with a single global alpha budget. Conditional on the validation
history, the selected policy is predictable; an e-process valid for its
bounded history-conditional paired-net-gain null retains its error guarantee.
This is sample-split policy selection combined with an established e-process,
not a novelty claim. A new protocol should compare this rule with pooled rank
and the two nested rules on fresh development seeds, retain the zero-signal
controls, and account for the context-dependent deployment cost. Only a
predeclared design that clears the +1 margin should proceed to independent
null calibration and disjoint confirmation.

Reproduce the registered run with:

```powershell
uv run shiftlab-dive-budgeted-context-grid develop `
  --seeds 30 --seed-offset 20261025 --n 3200 --d 16 --device cuda `
  --output outputs/context_budgeted_promotion_grid_30
```
