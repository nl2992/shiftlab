# Target-scout eventwise-bound null calibration under abrupt context drift

**Status:** frozen 2026-10-25 before execution. This independent null calibration evaluates the eventwise-propensity-bound scout variant after its development screen. It uses fresh seeds and the same abrupt context-prevalence family as the already passed minimum-propensity-bound calibration.

## Conditional null and bound argument

At zero signal, the outcome probability is the FN=5, FP=1 decision threshold at every event and context, including after the context prevalence changes. Thus for the fixed map selected during scouting, the paired expected decision-cost gain is zero eventwise. A positive switching charge makes the net gain nonpositive.

Under the registered uniform query policy, each budget cell has a fixed known query probability (q\in\{0.20,0.40\}\), independent of the current label. If the paired cost improvement satisfies (|G_t|\le C=5), then the direct-IPW event increment

\[
X_t=I_tG_t/q-\kappa
\]

has predictable support (B_t=C/q+\kappa). Under (E[G_t\mid\mathcal F_{t-1}]\le0), its conditional mean is nonpositive. Therefore each bounded betting factor (1+\lambda X_t/B_t), for fixed (0<\lambda\le1), has conditional expectation at most one, and their prespecified mixture is an e-process. This argument is specific to the uniform query path in this experiment. It does not authorize covariate-adaptive query probabilities under a null that conditions only on the past.

## Frozen design

- 1,000 independent seeds, 20269000–20269999, disjoint from all previous development and calibration blocks.
- Eventwise-propensity bound mode only; the conservative minimum-propensity mode has its own previously passed calibration.
- Three pre/post context-prevalence pairs: 0.10→0.90, stable 0.50→0.50, and 0.90→0.10.
- Cross each pair with proxy error 0 and 0.25, switching charges 0.00 and 0.05, and realized label caps 20% and 40%, for 24 cells.
- Preserve the scout selector, fixed-mixture certification, alpha 0.05, uniform direct-IPW querying, global decision-cost bound (C=5), (n=3,200), (d=16), and the scout/certification split.
- Require every stream to satisfy the evaluator-defined eventwise conditional null, have positive query support, and respect its realized cap. Each cell must contain at least 1,000 streams and have a one-sided exact Clopper–Pearson promotion-rate upper limit at most 0.05 using simultaneous 95% Bonferroni coverage (per-cell alpha 0.05/24). The family passes only if all cells pass.

Passing supports calibration under this registered DGP and query process. It does not establish power, generalize to adaptive propensities, or validate delayed/selective feedback. A disjoint positive-signal confirmation is allowed only if this calibration passes and the development analysis is frozen before opening confirmation results. No figure is planned; use PaperBanana for any figure.

## Reproduction

```powershell
uv run shiftlab-dive-scout-drift-calibration `
  --bound-mode eventwise_propensity --seeds 1000 --seed-offset 20269000 `
  --n 3200 --d 16 --device cuda `
  --protocol docs/scout_context_policy_eventwise_drift_null_protocol.md `
  --output outputs/scout_context_policy_eventwise_drift_null_1000
```
