# Residual-variance context-stratified monitor development protocol

**Status:** frozen before the development run. This screen is exploratory and cannot establish a false-alarm guarantee, confirm a winner, or support a novelty claim.

## Question and estimand

Does a fixed, learner-visible near-boundary context split improve detection of conditional paired decision-cost harm relative to pooled bounded-mean monitors in the existing residual-variance synthetic scenario? The context is `boundary` when `abs(x1 - 0.9*x2) <= 0.3`, and `non_boundary` otherwise. It is computed from current features before the label is observed and is held fixed throughout the stream.

The stratified procedure tests the intersection null that each context's conditional mean of paired cost minus the registered global margin (0.10) is nonpositive. It controls familywise crossing probability by Bonferroni alpha splitting across the two fixed contexts, provided the bounded conditional-mean null holds at the context-specific update times. This is a different claim from the pooled population-average null: one subgroup may be harmful while another offsets it. Results must report both subgroup and population-average evaluator costs and must not describe a subgroup alarm as evidence that the population-average cost is harmful.

## Frozen development design

- Use the existing train-only frozen logistic risk proxy and `residual_variance` generator at severities 1.5, 3.0, and 4.5.
- Use query rates 0.8 and 1.0, 60 matched seeds beginning at 31,305,000, stream length 2,400, and 16 features. The new seed block is disjoint from the preceding PVA prior/stake screen.
- Compare a pooled fixed-stake mixture, a pooled uniform eight-start mixture, and a two-context Bonferroni-stratified fixed-stake mixture. All methods share the same stream, PPI increments, query mask, support bound, event horizon, and hard label-cost budget.
- Report post-onset detection, pre-onset alarms, first crossing, context support, subgroup and population means, labels, spend, and processed horizon. These alternative-only counts are descriptive, not calibration.
- Use CUDA for synthetic generation when available. Keep process updates CPU-compatible. Save CSV and Parquet metrics, a report, exact source/protocol hashes, environment, and checksums. Do not generate a figure; if a figure is later requested, use PaperBanana and verify it against the saved metrics.

## Advancement rule

This grid only diagnoses whether fixed context stratification is promising enough to justify a fresh independent null calibration. Do not tune the context threshold on this seed block. Any follow-up must separately calibrate the two-context intersection-null procedure on fresh stationary and benign-nuisance streams, then run a disjoint confirmation on positive alternatives. The process is a Bonferroni family of standard bounded-mean e-processes; no new validity theorem is claimed. PPI validity additionally requires immediate randomized feedback, known positive propensity, a proxy formed without current outcomes, the common deterministic increment bound, and the stated conditional-mean null.

## Reproduction

```powershell
uv run shiftlab-dive-residual-variance-context-grid --device cuda
```
