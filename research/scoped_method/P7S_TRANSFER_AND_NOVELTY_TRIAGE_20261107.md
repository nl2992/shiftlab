# P7s candidate triage: transfer and prior-art gates (2026-11-07)

## Question

Can the existing B3+ settled-decision acquisition rule supply the missing Failure Atlas repair
claim, or is it a route to more evidence without first resolving its safety and novelty gaps? This
is a read-only reconciliation of committed experiments and targeted literature. No new method,
dataset, holdout, or outcome was opened.

## What the method changes

P7s reduces post-promotion label acquisition to the propensity floor while its recent paired-loss
signal says the challenger remains ahead; its paired certificate and promotion logic are inherited
from P3b. The stated target is redundant post-promotion certificate maintenance on persistent-gain
streams. Its intended trade-off is less label cost in exchange for slower detection of a reversal.
See `docs/promising_directions/B3_PLUS_METHOD.md` and the frozen implementation/protocol in the
B3+ artifacts.

## Existing evidence

- In the B3+ selected five-case table, P7s is below P3b on each case and below the fixed-sample P6
  on four of five. The two powered episode-level cases are Rialto (16 episodes; P7s 98.42 vs P3b
  103.73 and P6 122.91) and OpenML-LDPA (32; 478.82 vs 483.25 and 506.51). P7s is above P6 on
  weather. The result is an exposed, selected-case evaluation; OpenML-LDPA's event order is
  inferred and mostly tracks recorded-person changes. Source: `docs/promising_directions/
  B3_PLUS_FIVE_CASE_STUDIES.md`.
- That positive case table is not a matched comparison against the full Failure Atlas panel.
  In the fresh Failure Atlas validation, P7s has 8% promotions under the dependent Markov null
  (`rho=.8`) and 12% under the stronger dependent null, against a registered certification bound
  of 9.36%; it is marked **not certified**. None of the repair candidates that passed the
  certification criterion beat the strongest certified published competitor on the primary
  alternative regimes. Source: `docs/failure_atlas_v2_flq/results/validation_synthetic.md`,
  `validation_summary.json`, and the registered gate in `docs/failure_atlas_v2_flq/protocol.md`.
- P7s is not a repair for the two frozen primary mechanisms in the scoped-method brief. It
  economizes labels after promotion; it does not solve late-improvement blindness, and its own
  reduction in rollback sampling is the exposed risk. It should not be relabeled as a rollback
  improvement.

## Targeted prior-art boundary

The exact combination of a paired switching certificate and a post-promotion floor remains to be
checked against a broader literature search, but the underlying objective—budgeted sampling to
monitor a deployed model, adapting label collection over time, and trading monitoring cost against
drift detection—is established. MLDemon explicitly chooses costly labels under a budget for
post-deployment performance monitoring ([Ginart et al., AISTATS 2022](https://proceedings.mlr.press/v151/ginart22a.html)). Stream-based active learning with verification latency uses a dynamic high/low labeling budget around detected drift ([Castellani et al., 2022](https://arxiv.org/abs/2204.06822)). A later clinical-monitoring study proposes sampling-weighted surveillance and retraining after model deployment ([Kim et al., 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12278811/)). These works differ in estimand and setting, so they do not by themselves prove equivalence to P7s; they do rule out a broad novelty claim based only on reducing deployed-model monitoring labels.

## Decision and next gate

**Do not advance P7s as the missing method contribution.** There is credible scoped economic headroom
against P3b and P6 on existing data, but the complete baseline/safety evaluation contradicts a
certified SOTA claim, and the real cases are exposed and selected. A positive selected-case mean is
not sufficient to overrule the registered dependent-null failure.

The smallest evidence-changing next step, if this candidate is ever reconsidered, is not another
dataset screen: first define a monitoring-rate rule that preserves the stated error contract under
the target feedback assumptions, then freeze and test it against the full certified Failure Atlas
panel. Only a candidate that clears that synthetic safety and novelty gate could justify an
untouched real-source protocol. The current recovery brief's no-holdout gate remains in force.

## Reproduction pointers

- B3+ method, protocol, and selected-case results: `docs/promising_directions/B3_PLUS_METHOD.md`,
  `B3_PLUS_PROTOCOL.md`, `B3_PLUS_RESULTS.md`, `B3_PLUS_FIVE_CASE_STUDIES.md`.
- Full Failure Atlas validation: `docs/failure_atlas_v2_flq/results/validation_synthetic.md`,
  `validation_real.md`, `validation_summary.json`.
- Current bounded decision: `research/scoped_method/RECOVERY_STATUS.md`, Phases 9–11.
