# Eventwise-propensity-bound scout development under abrupt context drift

**Status:** frozen 2026-10-25 before execution. This exploratory matched-seed screen tests a mathematically motivated support-bound refinement after the global-bound scout showed very sparse promotion on the prior positive-signal drift grid. No confirmatory claim will be made from these development seeds.

## Bound and assumptions

For a frozen scout-selected policy map, let (G_t) be the paired decision-cost improvement on event (t), with (|G_t|\le C=5). The uniform query probability (q) is fixed for each budget cell and chosen before the monitored stream. The direct-IPW increment is

\[
X_t=\frac{I_tG_t}{q}-\kappa,
\qquad |X_t|\le \frac{C}{q}+\kappa,
\]

where (I_t) indicates a queried label and \(\kappa\) is the per-deployment-event switching charge. Under the stated conditional-mean null, (E[G_t\mid\mathcal F_{t-1}]\le0), independent randomized querying gives (E[X_t\mid\mathcal F_{t-1}]\le0). For any fixed stake (\lambda\in(0,1]), (1+\lambda X_t/B_t\) is nonnegative with conditional expectation at most one when (B_t=C/q+\kappa) is predictable. A fixed mixture of these processes remains an e-process. This replaces the current conservative (C/q_{\min}+\kappa), where (q_{\min}=q/2), and halves the leading range term in these uniform-query cells.

The implementation is deliberately restricted to the uniform query policy. Do not use this normalization with propensities selected from current covariates under a null stated only conditionally on the past; the filtration must include what determines (q_t), and the corresponding conditional null must hold. The DGP used here has a conditional-on-context null at zero signal, but this positive-signal screen is for utility, not calibration.

## Frozen development grid

- 60 matched development seeds, 20268100–20268159, disjoint from earlier scout development, null calibration, and confirmation blocks.
- The same 24 cells as the preceding drift screen: prevalence pairs 0.10→0.90, 0.50→0.50, and 0.90→0.10; signal strengths 0.05 and 0.10; proxy errors 0 and 0.25; and 20%/40% hard label caps.
- Compare rank, nested-volume, the existing minimum-propensity-bound scout, and the eventwise-propensity-bound scout on each matched stream. Both scout variants use the same selector, candidate map, query uniforms, certification e-process, switching charge 0.05, FN cost 5, FP cost 1, and split.
- Primary exploratory contrasts are eventwise-bound scout minus minimum-bound scout, rank, and nested-volume in evaluator-known future net decision gain. Report equal-cell means and seed-cluster bootstrap 95% intervals, plus each cell and method's promotion rate, utility, processed events, and labels.
- Require all four method rows per stream and budget, unique cell/seed/method keys, positive propensities, and no hard-cap violations. Save Parquet streams/cells/contrasts, protocol and source hashes, environment, and report.

This screen may identify an operating region for fresh null calibration. It does not validate the new bound's false-promotion rate and does not license a confirmatory claim. If power improves, calibrate the eventwise-bound variant on a disjoint 24-cell zero-signal drift family before any independent positive-signal confirmation. No figure is planned; use PaperBanana for any figure.

## Reproduction

```powershell
uv run shiftlab-dive-scout-drift-development `
  --compare-eventwise-bound --seeds 60 --seed-offset 20268100 --n 3200 --d 16 --device cuda `
  --protocol docs/scout_context_policy_eventwise_bound_development_protocol.md `
  --output outputs/scout_context_policy_eventwise_bound_development_60
```
