# Delayed PPI fixed-start mixture: development protocol

**Status: frozen before execution.** This is a development-only monitor comparison; it is not an independent power confirmation or a new validity theorem. It tests whether a fixed mixture over prespecified start times improves late-onset detection while retaining the existing delayed, predictable-bound PPI setup.

## Registered design

Use 60 paired streams with seeds 20310000–20310059. Each stream has 1,200 source and 2,400 target events, a 480-request hard label cap, alpha 0.05, materiality margin 0.05, propensity support `[0.05, 0.80]`, and feedback delays uniform on 0–12. The latent target scale follows a two-state Markov regime with flip probability 0.05 and amplitudes `{0.55, 1.0}`. The learner does not observe the regime. Signs are independent conditional on regime. For each onset fraction `{0.25, 0.50, 0.75}`, the conditional sign probability changes from 0.5 to `0.5*(1 + 0.20/A_t)`, yielding conditional mean harm 0.20 and outcomes in `[-1,1]` after onset. Target contexts, outcomes, query uniforms, and delays are shared within each paired policy comparison.

Compare two query policies—uniform and the already-selected `evidence_a0p025_p0p5_eventwise`—with two monitors:

1. The existing full-stream `PredictableBoundMeanEProcess`.
2. A fixed equal-weight mixture of eight `PredictableBoundMeanEProcess` components started at event indices `(0, 300, 600, 900, 1200, 1500, 1800, 2100)`.

At each event, all active components receive the same event-order-resolved PPI increment and its predictable bound. The mixture is `sum_j w_j E_j(t)` for fixed `w_j=1/8`; a component remains at one before its registered start. Each component is an e-process under the same eventwise conditional-mean null, predictable-bound and filtration assumptions, so the fixed convex mixture is also an e-process by linearity. This argument does not cover a changed filtration, a misspecified conditional null, outcome-informative querying, or unresolved event-order updates.

## Endpoints and development gate

Report post-onset detection, pre-onset alarms, alarm event and wall delay, queried labels, events processed, cap and event-prefix checks, for every onset × query × monitor cell. The primary descriptive contrast is the paired difference in post-onset detection between the start mixture and full-stream monitor under evidence-directed querying, equally weighted over the three onset fractions. Also report each onset-specific paired difference. Use a seed-cluster percentile bootstrap interval for description and the exact paired discordance table; do not interpret unadjusted grid p-values as confirmatory evidence.

The start mixture may advance only if its pooled descriptive detection difference is positive, the 95% seed-bootstrap interval lower endpoint is above zero, it has no higher mean label use, and all cap/prefix invariants pass. This development rule only nominates a fixed monitor for separate independent null calibration and disjoint confirmation. If it fails, retain the negative result and do not calibrate or confirm this monitor on the basis of this grid. There is no candidate search over start locations or weights in this run.

## Reproduction

`uv run shiftlab-dive-delayed-evidence-ppi-start-grid --seeds 60 --seed-offset 20310000 --device cuda --output-dir outputs/delayed_evidence_ppi_start_mixture_grid_60`
