# Target-scout contextual policy null calibration protocol

**Status:** frozen 2026-10-24 before execution. The target-scout rule passed its
development gate on two disjoint development blocks. This study evaluates only
false-promotion behavior under registered aggregate-null synthetic streams; it
does not establish confirmatory power or external validity.

## Question and null

Calibrate the exact two-stage target-scout selection and holdout-certification
rule in `src/shiftlab/dive/budgeted_promotion.py`. The scout selects one action
per learner-visible context on the first half of the monitor, then freezes that
map. The second half tests its aggregate paired decision-cost gain with the
existing fixed-mixture e-process at alpha 0.05. Scout labels are excluded from
certification. The pathwise query-dollar cap covers both stages.

For every registered context, the target outcome probability is exactly the
FN/FP decision threshold, so each candidate has zero gross expected gain over
the incumbent. The null for the certification-stage process is therefore
`E[increment_t | F_(t-1)] <= 0`: zero switching charge is the least-favorable
boundary; the registered 0.05 charge makes selected actions weakly harmful.
Outcomes and query randomization remain stochastic, so this is not an
identical-policy or zero-variance control.

## Frozen design

- 1,000 independent matched seed IDs, 20261300–20262299, reused across
  registered cells only for pairing. They are disjoint from every scout
  development seed block (ending at 20261259).
- Nine learner/evaluator context profiles: latent prevalence 0.10/0.50/0.90
  crossed with learner-proxy misclassification 0/0.10/0.25.
- Two switching charges: 0.00 (least-favorable boundary) and 0.05 (the
  development/deployment setting).
- Two realized hard query caps: 20% and 40%. This yields 36 prespecified
  profile × charge × cap cells. All cells use signal delta 0.00, `n=3,200`,
  `d=16`, FN cost 5, FP cost 1, uniform direct-IPW queries, fixed-mixture
  certification, and alpha 0.05.
- Report the promotion count/rate and exact one-sided Clopper–Pearson upper
  limit in each cell. Use Bonferroni cell alpha 0.05/36 for simultaneous 95%
  coverage. A cell passes only with all 1,000 trials, no cap breach, and its
  simultaneous upper limit at most 0.05. Overall calibration passes only if
  all 36 cells pass.
- Do not tune the e-process, candidate family, bound, query probabilities,
  alpha, context rule, or selection split using these results. The calibration
  is tied to the stated IID generator, known positive propensity, bounded
  paired-cost increments, predictable fixed candidate map during
  certification, and the aggregate history-conditional null.

This finite simulation complements the supermartingale/optional-stopping
argument; it does not replace it. It does not cover serial dependence, delayed
or selectively observed labels, unregistered contexts, misspecified costs,
or live deployment. If calibration fails, stop this rule for the registered
claim and investigate the failure before changing anything. If it passes,
freeze a separate confirmation protocol with a disjoint seed block and the two
development utility contrasts as primary endpoints.

## Reproduction

```powershell
uv run shiftlab-dive-scout-calibration `
  --seeds 1000 --seed-offset 20261300 --n 3200 --d 16 --device cuda `
  --protocol docs/scout_context_policy_null_calibration_protocol.md `
  --output outputs/scout_context_policy_null_calibration_1000
```

No figure is planned. Any figure added later must be made with PaperBanana.
