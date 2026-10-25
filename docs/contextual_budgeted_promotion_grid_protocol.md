# Fitted context-nested promotion development grid

**Status:** Frozen development design, 2026-10-24. This screen is for diagnosing
power and utility; it is not a calibration or confirmation experiment.

## Question and methods

When does context-nested candidate alpha allocation improve fitted-model
promotion utility over pooled candidate-rank spending, and how does the result
change with context prevalence, decision signal, and proxy error? Compare the
same 13 validation-ranked fitted policies using (1) pooled rank spending,
(2) rank spending split equally over two contexts, and (3) rank spending split
by outcome-free validation context volume. All methods share the same stream,
candidate family, queried labels, and hard label cap.

The two nested methods use the registered composition
`alpha_{k,g}=alpha_k v_g`, where the candidate-rank weights are frozen on the
pre-monitor validation outcomes and context weights are either one half each or
smoothed validation feature proportions. Each context e-process updates only on
events assigned to that context. The context is a noisy binary feature supplied
before outcomes; latent membership is evaluator-only. This is weighted
Bonferroni composition of the existing fixed-mixture e-process, not a new
sequential test.

## Controlled DGP

Generate features and the training/validation labels from the existing
stationary `iid_regression` source process. Define latent context 1 as
`X[0] >= Phi^{-1}(1-p)`, giving target prevalence `p`. A learner-visible proxy
feature is created by independently flipping latent context with probability
`e`; this proxy replaces an otherwise unused feature at index `d-1`. From the
first monitor event (the 25% validation boundary) through deployment, labels
are Bernoulli with probability `1/6 + delta` in latent context 1 and
`1/6 - delta` in context 0. Here `1/6 = FP/(FN+FP)` for the fixed FN=5, FP=1
costs, so `delta=0` makes both actions equal in expected cost at every event;
the switching charge then makes every candidate's net gain nonpositive. For
`delta>0`, the two latent contexts lie on opposite sides of the decision
threshold. The candidate policies remain frozen from source training and
validation. The evaluator alone uses latent membership and target probabilities
to score expected utility.

## Frozen factorial and analysis

- `n=3,200`, `d=16`, 30 development seeds per cell; seed root `20261025`.
- Latent context prevalence `p`: 0.10, 0.50, 0.90.
- Absolute probability shift `delta`: 0, 0.05, 0.10.
- Proxy misclassification `e`: 0, 0.10, 0.25.
- Uniform acquisition, direct IPW, fixed-mixture e-process, alpha 0.05.
- Common realized label caps: 20% and 40% of the monitor horizon.
- Primary utility outcome: evaluator-known cumulative future net decision-cost
  gain after deployment, including exposure-prorated switching cost.
- Primary contrasts: paired nested-volume minus pooled-rank and nested-volume
  minus nested-equal mean utility. Report a cellwise paired 95% bootstrap
  interval and an equally weighted macro-average over the 18 positive-signal
  cells with simultaneous 97.5% intervals for the two primary contrasts.
- Secondary outcomes: promotion and future-harm rates, pointwise-null crossings,
  queried labels, processed horizon, and actual feature-proxy prevalence.

Common seeds and separate deterministic random-number streams for source data,
context corruption, target outcomes, and query decisions provide paired
comparisons. The development grid does not select a winner for confirmatory use.
The existing +1 cumulative utility margin is the minimum practical effect for
considering a fresh confirmation design. Any such design must use a disjoint
seed block and first pass independent null calibration under both the exact
copy and zero-signal controls. The current 30-seed pilot results and this grid
must not be pooled with calibration or confirmation data.

## Assumptions and limitations

The validity claim is conditional on bounded decision-cost increments, the
registered global support bound, predictable fixed policies and context rules,
uniform outcome-independent querying, and no action-dependent outcome process.
Proxy error is independent of target outcome noise conditional on latent group.
This controlled simulator tests power of fitted source-trained candidates under
a single abrupt context-conditional target shift. It does not establish validity
under serial dependence, delayed or selectively observed labels, adaptive
contexts, or changing context definitions. No visual is planned; if one is
added, use PaperBanana.

Reproduce the development grid with:

```powershell
uv run shiftlab-dive-budgeted-context-grid develop `
  --seeds 30 --seed-offset 20261025 --n 3200 --device cuda `
  --output outputs/context_budgeted_promotion_grid_30
```
