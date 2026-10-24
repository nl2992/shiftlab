# Multi-timescale discounted betting: development protocol

## Question

Can a monitor that forgets older increments adapt more quickly after an abrupt change in paired decision harm than the fixed-stake and cumulative predictable-Kelly baselines? The prior residual-variance screens show weak harm evidence at practical horizons; this candidate tests whether slowly updated betting stakes also contribute to the delay.

## Candidate and validity argument

For normalized PPI increments (R_t=X_t/B\in[-1,1]), a component with stake \(\lambda_t\in[0,1/2]\) chosen from its own past updates wealth by

\[
W_t=W_{t-1}(1+\lambda_t R_t).
\]

Under the eventwise conditional-mean null \(\mathbb E[X_t\mid\mathcal F_{t-1}]\le0\), \(\lambda_t\) is predictable and the factor is nonnegative with conditional expectation at most one. Each component is therefore a nonnegative supermartingale. A fixed convex mixture over starts and half-lives preserves this property, so the same Ville threshold applies. This argument requires the existing predictable propensity, PPI unbiasedness, support, filtration, and conditional-mean assumptions. Discounting changes the predictable stake schedule; it does not supply a new theorem or establish the assumptions for real feedback.

For each fixed start, the candidate maintains discounted mean and second moment from past normalized increments:

\[
m_t=\gamma m_{t-1}+(1-\gamma)R_{t-1},\qquad
v_t=\gamma v_{t-1}+(1-\gamma)R_{t-1}^2,
\]

with \(m_0=0\), \(v_0=0.25\), and \(\lambda_t=\min\{0.5,\max(0,m_t)/\max(v_t,\text{tiny})\}\). Three half-lives (16, 64, 256) and the same eight fixed start positions used by the uniform-start comparator are mixed with equal weights fixed before the stream. No current outcome, future label, or evaluator-only change metadata enters the stake.

This is a predictable-betting candidate and a combination of standard ingredients. We make no novelty claim. Its potential advantage is adaptation after a mean shift without discarding anytime validity.

## Locked development comparison

- Scenario: residual-variance / target-variance; severity 1.5, 3.0, and 4.5.
- Feedback rates: 0.80 and 1.00. All methods receive the same stream, query indicators, PPI increments, alpha, bound, and hard label-dollar cap within each paired cell.
- Fresh seed block: 60 seeds per cell, 31,303,026–31,303,085; \(n=2,400\).
- Methods: fixed-stake mixture, cumulative predictable Kelly, uniform-start fixed-stake mixture, and the fixed start × half-life discounted Kelly mixture.
- Primary summary: detection averaged equally over the six severity × feedback-rate cells, with seed-clustered paired bootstrap intervals versus fixed mixture and uniform-start fixed mixture. Cellwise outcomes, pre-onset alarms, delay, spend, labels, processed horizon, and budget adherence are also reported.
- This is an alternative-only development screen. Pre-onset counts are diagnostics, not null calibration. No candidate will be promoted without fresh nondegenerate null calibration and a disjoint alternative confirmation.

Run with:

```powershell
uv run python -m shiftlab.dive.residual_variance_discounted_betting --device cuda --seeds 60
```

The output directory is `outputs/residual_variance_discounted_betting/`, with per-stream Parquet/CSV, cell summaries, paired contrasts, and a manifest with code hashes and environment details. No figure is generated. If a figure is requested, use PaperBanana and derive it from these metrics.
