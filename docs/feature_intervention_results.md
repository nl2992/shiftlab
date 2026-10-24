# Feature-dependent promotion and rollback: development results

## Decision

The feature-cost integration is technically working, but this screen does **not** show a net-utility
improvement over continuing with the incumbent. In the deliberately harmful-reversal profile,
rollback consistently reduces losses relative to promotion-only, yet accumulated harm before rollback
leaves the integrated policy worse than `continue`. Keep the branch as a validated baseline
integration and proceed only to independently calibrated mechanism confirmation; do not call it a
successful end-to-end intervention policy or claim novelty.

## Implementation and run

The frozen candidate/incumbent pair now runs against feature-dependent costs through the existing
stage-separated `CertifiedPromotionRollback` logic and the `DecisionRequest` /
`PolicyDecision` / `DecisionFeedback` stream contract. The paired-cost support is `M=5`, so the
promotion and rollback factor bounds use `M/q + k/H`; the original Bernoulli benchmark retains its
default `M=1`. Both action costs are identified by queried binary outcomes under this simulator's
non-performative outcome model. The evaluator's probabilities and expected costs stay outside the
learner replay.

The CUDA development grid used 30 paired streams per scenario and each of four `(q, budget)` cells,
including an exact least-favourable rollback-null scenario, with 400 shadow events and 400 deployment events per stream. The same outcome seeds and query
uniforms were used across cells. It produced 2,880 method-stream rows, and every row respected its
pathwise label cap. Exact command:

```powershell
uv run shiftlab-dive-feature-intervention-grid `
  --seeds 30 `
  --seed-offset 76102024 `
  --horizon 400 `
  --query-rates 0.40 0.80 `
  --budget-rates 0.20 0.40 `
  --device cuda `
  --output-dir outputs/feature_intervention_grid
```

## Primary results

| Query rate | Label cap | Harmful reversals rolled back | Net utility vs continue under reversal | Rollback gain vs promotion-only (paired 95% seed interval) | Persistent-benefit rollback | Net utility vs continue under persistent benefit |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.40 | 20% | 14/30 | -108.88 | +31.67 [18.58, 45.19] | 0/30 | +398.35 |
| 0.40 | 40% | 23/30 | -101.43 | +39.13 [27.44, 51.15] | 0/30 | +397.84 |
| 0.80 | 20% | 11/30 | -103.60 | +36.96 [19.56, 55.08] | 0/30 | +398.35 |
| 0.80 | 40% | 28/30 | -65.22 | +75.34 [63.96, 85.50] | 0/30 | +396.75 |

All four cells promoted the frozen candidate in 30/30 harmful-reversal and persistent-benefit
streams. The harmful-reversal row had deployment gain turn from positive in shadow to negative in
deployment. More rollback monitoring improved utility relative to promotion-only, but the method
still lost 65.22 expected cost units on average against keeping the incumbent in the most informative
cell. The persistent-benefit case isolates the monitoring charge: the 80%/40% method lost 2.69
units relative to promotion-only because it paid for rollback-stage labels despite observing no
rollback.

On the exact marginal-zero stationary and benign-nuisance controls, the gated method falsely
promoted 0/30 streams in every cell. These small counts are not a false-alarm calibration. In the
boundary-local-harm profile, the candidate was non-improving during shadow and beneficial only after
the phase transition; the gate promoted 0/30 streams. This is a safe but opportunity-costly outcome
under the frozen pre-deployment certification design. The unconditional-promotion comparator
benefited in hindsight from future outcomes and was classified as an unsafe promotion under the
shadow null.

## Interpretation and limits

The paired grid suggests the expected resource trade-off: at the fixed cap, stronger propensity
does not uniformly improve rollback because it can exhaust labels earlier, while the 80% propensity
with a 40% cap gave the strongest reversal rollback rate. No setting in this development grid
achieved positive net utility against `continue` under harmful reversal. A sequential rollback test
can limit how long harm persists after evidence arrives; it cannot make shadow benefit predict a
later, unobserved reversal. Promotion evidence, future-shift uncertainty, query expense, and fallback
timing therefore remain separate decision quantities.

The 30-stream null counts cannot establish the nominal error rate. The new `rollback_boundary`
profile sets the population candidate gain to `-k_rollback/H` during deployment while shadow gain
remains positive; it is included to calibrate rollback at its least-favourable registered null. The
independent calibration protocol additionally includes persistent benefit as a second rollback-null
control. The simulator assumes immediate
independent labels, fixed known propensities, a frozen candidate, identifiable paired costs, bounded
costs, and a fresh deployment phase satisfying its rollback null conditional on promotion history.
No results here cover adaptive candidate construction, delayed or selective feedback, dependence,
action-dependent outcomes, real datasets, or application-calibrated intervention costs.

## Reproducible artifacts

Combined Parquet metrics, per-cell metrics/manifests, seed-paired contrasts, and the generated
summary are in [`outputs/feature_intervention_grid/`](../outputs/feature_intervention_grid/). The
protocol and exact assumptions are in [`feature_intervention_protocol.md`](feature_intervention_protocol.md).
No figures were generated because PaperBanana was unavailable in the active environment; no other
visual generator was substituted.

## Independent calibration and confirmation

After the development grid, the selected mechanism-test cell (`q=.80`, 40% cap) passed the frozen
four-cell calibration on 2,000 fresh streams per cell, seed offset `77102024`. Simultaneous one-sided
exact Clopper–Pearson upper limits used Bonferroni cell alpha `.05/4`:

| Error cell | Events / streams at risk | Observed rate | Simultaneous upper limit | Gate |
| --- | ---: | ---: | ---: | --- |
| False promotion, stationary | 9 / 2,000 | 0.45% | 0.917% | Pass |
| False promotion, benign nuisance | 9 / 2,000 | 0.45% | 0.917% | Pass |
| False rollback, least-favourable boundary | 11 / 2,000 | 0.55% | 1.050% | Pass |
| False rollback, persistent benefit | 0 / 2,000 | 0.00% | 0.219% | Pass |

Every calibration stream respected the hard label cap. The eventwise bound is `M/q+k/H`, with
`M=5`; the rollback-boundary DGP sets expected deployment gain exactly to `-k_rollback/H`. This
supports the gate's error control under these four registered iid synthetic cells and the frozen
immediate-label assumptions. It does not establish arbitrary-filtration or real-world validity.

The disjoint confirmation used 2,000 fresh streams per alternative, seed offset `78102024`, after
the calibration manifest passed. The promotion-rollback procedure rolled back 1,790/2,000 harmful
reversals (89.5%), at mean deployment event 166.88. Its expected net utility exceeded
promotion-only by 71.19 units (paired 95% seed-cluster bootstrap interval [69.66, 72.70]). However,
its net utility versus `continue` was **-69.38** (95% interval [-70.87, -67.90]). This confirms that
rollback limits exposure compared with leaving the candidate deployed, but does not make this
intervention policy beneficial against retaining the incumbent.

Under persistent benefit, rollback occurred on 0/2,000 streams; rollback-stage monitoring reduced
expected net utility by 2.683 units versus promotion-only (95% interval [-2.692, -2.674]) because
labels cost money. Net utility against `continue` remained +396.75 units, driven by the candidate's
strong persistent benefit. Under the future-only boundary-harm profile, promotion occurred in
11/2,000 streams (0.55%) while shadow gain was exactly zero; those promotions incurred monitoring
cost and the gated method's utility contrast versus `continue` was -0.968 (95% interval
[-2.168, +0.432]). The gate otherwise declined to deploy, so the later benefit was not captured.

The frozen primary mechanism-retention rule passed: rollback-versus-promotion-only's lower interval
endpoint was positive, and all label caps were respected. The separate end-to-end net-utility rule
did not pass under harmful reversal because `continue` remained better. The supported conclusion is
therefore limited to calibrated rollback evidence reducing loss versus promotion-only in this
simulator. No claim of a successful end-to-end controller or algorithmic novelty follows.
Calibration and confirmation artifacts, manifests, and reports are in
[`outputs/feature_intervention_calibration_2000/`](../outputs/feature_intervention_calibration_2000/)
and [`outputs/feature_intervention_confirmation_2000/`](../outputs/feature_intervention_confirmation_2000/).
