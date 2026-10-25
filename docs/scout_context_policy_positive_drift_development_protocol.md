# Target-scout positive-signal development grid under abrupt context drift

**Status:** frozen 2026-10-25 before execution. This is an exploratory, matched-seed development grid following the passed abrupt-shift null calibration. It evaluates utility after the context distribution changes; it is not an independent confirmation.

## Question and estimand

When the context prevalence changes between policy selection and certification, does the target-scout selector improve evaluator-known future net decision gain over rank-only and nested-volume alpha allocation? The scout sees labels and contexts from the first half of the target monitor, freezes its context-specific candidate map, then certifies that map on the second half. Certification outcomes are not used to revise the map. The primary estimand is the equal-cell mean paired difference in `expected_postpromotion_net_gain` over the untouched deployment slice.

## Frozen grid

- 60 matched development seeds, 20268000–20268059, disjoint from all earlier scout development, calibration, and confirmation seed blocks.
- Three pre/post prevalence pairs: 0.10→0.90, 0.50→0.50, and 0.90→0.10.
- Two positive context signal strengths (0.05, 0.10), two proxy-error rates (0, 0.25), and two hard label-budget rates (0.20, 0.40), for 24 cells.
- Compare rank, nested-volume, and target-scout policies on the same generated stream and query uniforms. Use FN cost 5, FP cost 1, switching cost 0.05, uniform positive-propensity direct-IPW queries, global bounded-mixture certification, n=3,200, and d=16.
- Primary contrasts: scout minus rank and scout minus nested-volume. Report paired per-cell estimates and equal-cell-weighted seed-cluster bootstrap 95% intervals. The intervals are descriptive because this block is used for development; no hypothesis test or novelty claim is made.
- Enforce complete method rows, unique cell/seed/method keys, positive query support, and the realized hard cap. Store all per-stream evaluator-expected and realized utility metrics, a cell summary, contrasts, protocol hash, source hashes, and environment.

At positive signal, the conditional mean may differ by context; therefore this grid measures selection and deployment utility and is not a null calibration. The separate 24-cell zero-signal drift calibration remains the false-promotion evidence. If the development pattern motivates a follow-up, freeze the selected primary contrasts, cells, margin, and seed block before running a disjoint confirmation. No figure is planned; use PaperBanana for any figure.

## Reproduction

```powershell
uv run shiftlab-dive-scout-drift-development `
  --seeds 60 --seed-offset 20268000 --n 3200 --d 16 --device cuda `
  --protocol docs/scout_context_policy_positive_drift_development_protocol.md `
  --output outputs/scout_context_policy_positive_drift_development_60
```
