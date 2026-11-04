# Research candidate: anytime-valid switching across retrained challenger versions

**Status:** exploratory implementation and 50-seed synthetic screen completed; further independent
null and real-data validation is required. No validity or SOTA claim is established.

## Why this is the next method question

The local benchmark's real streams freeze the incumbent and challenger before evaluation, so they
cannot test a model that improves as it is retrained. The closest retrieved paper, Digalakis et al.,
studies repeated training and the economics of when to switch, with a real credit-scoring study, but
its abstract frames the result around learning-curve and sequential empirical evaluation rather than
an anytime-valid, hard-label-budget paired gate. Online active model selection already handles
selective labels for a fixed pre-trained model set. Delayed-outcome anytime inference has also been
studied for randomized treatment arms. The potential gap is their intersection: **promotion among
predictably produced model versions, with paired losses, delayed selectively purchased labels,
hard evaluation budget and replacement cost**. This is a hypothesis to test, not a novelty claim.

Relevant prior art:

* [Digalakis et al., *The Challenger* (2026)](https://arxiv.org/abs/2512.18390): repeated challenger
  training, switching economics and chronological credit scoring. Its abstract gives a near-oracle
  regret analysis for its own sequential evaluation procedure.
* [Karimi et al., *Online Active Model Selection for Pre-trained Classifiers* (AISTATS 2021)]
  (https://proceedings.mlr.press/v130/reza-karimi21a.html): selective label queries and high
  probability identification among fixed pre-trained classifiers.
* [Lindon and Kallus, *Design-Based Anytime-Valid Inference for Randomized Experiments with Delayed
  Outcomes and Staggered Entry* (ICML 2026)](https://proceedings.mlr.press/v306/lindon26a.html):
  anytime-valid inference under delayed outcomes and nonstationarity, with a treatment-assignment
  design and arm-specific event-time filtrations.
* [Sethi et al., *Asymptotically Optimal Sequential Testing with Markovian Data* (ICML 2026)]
  (https://arxiv.org/abs/2602.17587): composite Markov null testing; a binary fixed-gap port was
  screened locally and stopped for cost/power.

## Candidate construction

At predeclared or predictably chosen retraining times, produce challenger versions `v=1,2,...` using
only data available by the update time. At activation, freeze the currently deployed model `b(v)` as
the baseline for that version's promotion test. Version `v` is scored only on future events after
activation. For every label request, freeze and retain the challenger version, baseline version,
disagreement/covariates and query probability at issue time until delayed feedback is released.

Allocate version-level error budgets deterministically in advance, for example
`alpha_v = alpha / (v * (v + 1))`, so their sum is alpha. If version `v` is compared with more than
one baseline, split `alpha_v` over the version-baseline pairs with fixed summable weights. For one
pair, run a version-specific started e-process on post-activation paired outcomes and promote only
when that process crosses its allocated threshold. At a queried disagreement, let `Y=+1` favor the
challenger and `Y=-1` favor its baseline. A simple candidate is the fixed mixture
`E_n = sum_l pi_l product_{i<=n}(1 + lambda_l Y_i)` for predeclared `lambda_l` in `[0,1]` and
weights `pi_l` summing to one. An update time is predictable from the available history; labels
issued before it remain tagged to their original version/baseline even if they arrive later. Query
acquisition is shared across versions under one hard budget. Switching and retraining costs enter
the deployment objective, not the evidence threshold. A restart mixture within each version can
handle an unknown improvement time after activation, with its start weights included in that
version's alpha accounting.

## Validity target and limits

Initial target: for each activated challenger-baseline pair, at every future event opportunity,
conditional expected paired gain is nonpositive given the complete release-time history, current
disagreement and relevant observed covariates. Query randomization is predictable and conditionally
independent of the current label. This is a strong conditional null; a marginal mean null is not
enough when querying only disagreements. Under it, each factor `1+lambda Y` has conditional
expectation at most one, so the mixture is a nonnegative test supermartingale. If the pair's
activation is predictable and its test uses only fresh outcomes, Ville gives conditional crossing
probability at most `alpha_v`, even when the version was selected adaptively from past labels. A
union bound over the deterministically allocated versions gives at most `alpha` for any false
promotion. Version-baseline pairings, directions or extra adaptive choices require further fixed
alpha splits. Delayed feedback requires issue-time tagging and release-order updates; fixed
noninformative delay preserves issue order. This first theorem would **not** cover a Markov
marginal null, retraining on an event and reusing that event as certification evidence, outcome-
dependent delay, or false rollback. Those are separate extensions and must not be implied by an iid
result.

The initial proof obligation is to show that the chosen paired e-process remains a test
supermartingale after conditioning on the history that selected each challenger and baseline, and
that the union/started-mixture accounting remains valid under delayed releases. Every event must be
tagged `(challenger version, baseline version, issue time, release time, query propensity)`; pending
outcomes from an old pair cannot be relabelled after a deployment change. The version-level
allocation is enough only when each challenger is tested against one baseline; if the same version
is tested against multiple baselines, use a pair-level allocation such as `alpha_{v,b}=alpha*w_v*w_b`.
Training may use older queried labels, but those observations cannot be included in that version's
post-activation evidence. The null must be stated conditionally after the data-dependent training
history.

## Evaluation required before retention

1. Add a separate exploratory stream format with multiple frozen challenger versions and explicit
   activation times. Version `v` must be trained strictly before its scored suffix. Use real
   chronological features where possible, with all fitting, preprocessing and update choices frozen
   before policy runs. Keep the existing registered `fresh_real` validation unchanged.
2. Compare against RMM, best certified ports, Xu/active fixed-model selectors, and a non-validating
   learning-curve switching baseline from *The Challenger* if an auditable implementation is
   available. Include a one-shot frozen challenger and an always-retrain oracle only as diagnostics.
3. Score net loss, query spend, training/retraining cost, switch cost, promotion delay, and harmful
   promotions. Include no-improvement and degradation streams, not just a challenger that eventually
   wins.
4. First run a development screen only. Retain only if it improves paired net cost over both RMM and
   the strongest applicable published baseline on a predeclared family of model-update streams,
   without a null promotion spike. Then lock an independent protocol and run the full null validation.

## Main implementation risks

* A fixed candidate family is the current active-selection prior; repeated adaptive versions add a
  multiplicity and data-reuse problem.
* Evaluation labels used to train the next challenger cannot also count as fresh evidence for that
  version. Separate training and certification ledgers must make this visible.
* A candidate update can arrive while old-version labels are pending. The implementation must not
  relabel those outcomes to the new challenger or silently lose their error-budget accounting.
* If labels are purchased only for disagreements, the propensity correction must remain valid for
  each version, including the version identity fixed when the event was issued.
* Prior art may already cover a close subset. The claim must rest on the valid intersection and
  measured decision improvement, not on combining named components.

## Initial implementation and development screen

The current implementation is [`versioned_challenger.py`](../../scripts/sota_sprint/versioned_challenger.py)
and the runner is [`versioned_screen.py`](../../scripts/sota_sprint/versioned_screen.py). It uses a
fixed mixture of bounded sign bets, a deterministic equal alpha split across the two predeclared
versions, issue-time version/baseline tags, a hard shared budget with a per-version reserve, and
release-time updates. The paired synthetic screen (seed base `2026110906`, 50 seeds each) used a
worse first version from event 0, then either a better or equal-error second version at event 800.
T=2000, B=200, delay=24, incumbent error probability .40, first-version .46, and second-version
.25 (improvement) or .40 (null). This is an intentionally small development design; the 50-seed
null is only a diagnostic.

| scenario | policy | mean net cost | mean labels | promotion rate |
|---|---|---:|---:|---:|
| late improvement | version-indexed gate | 685.59 | 167.76 | .80 |
| late improvement | RMM on replaceable challenger slot | 780.78 | 200.00 | .32 |
| late improvement | front-loaded gated certificate | 810.18 | 189.22 | 0 |
| late improvement | A5b | 810.72 | 200.00 | 0 |
| late improvement | version-reset Model Picker | 631.80 | 54.32 | 1.00 |
| null | version-indexed gate | 810.53 | 198.12 | 3/50 promotions |
| null | RMM on replaceable challenger slot | 810.20 | 200.00 | 2/50 promotions |
| null | version-reset Model Picker | 812.32 | 97.62 | 50/50 promotions |

Paired cost difference for the version-indexed gate versus RMM was -95.19 [-115.86,-74.53] on
late improvement, and versus the front-loaded gated certificate was -124.59 [-143.59,-105.60].
The gate lost to the faster but unprotected version-reset Model Picker by +53.79 [+38.43,+69.15].
It promoted in 40/50 late-improvement seeds and 3/50 null seeds. These are synthetic exploratory
signals only. The first result suggests that a static gate can discard a weak first version before
a later retrained version arrives; version-indexed testing can reopen evidence for the new version.
The Model Picker result shows the value of fast selection and its corresponding null risk in this
construction. The small null count cannot verify the theorem or calibrated type-I error.

Next: run 1000 null seeds on the locked synthetic version schedule, audit issue/release pairing and
the hard cap, then build a chronological real stream with version activation based only on past
data. Do not retain this method as an SOTA result unless it still beats strong certified and active
selection baselines on held-out version schedules without a null-promotion excess.

### Locked 1000-seed null diagnostic (2026-11-04)

The predeclared null run completed for all 1000 seeds. The version-indexed gate promoted 26/1000 (2.6%, Wilson 95% CI [1.78%, 3.78%]), below the locked .06 point-rate and .07 upper-bound thresholds; mean query use was 199.22/200 (maximum 200), with mean net cost 810.22. RMM promoted 11/1000 and the front-loaded gate 2/1000. Thus the implementation passes this narrow diagnostic and can advance to chronological real-stream development. The high label spend limits its practical appeal, and the iid null does not establish adaptive conditional validity or real-data benefit. Protocol and interpretation are recorded in [`versioned_null_dev_protocol.md`](versioned_null_dev_protocol.md).

### Chronological real-data development screen

The first versioned real-data screen is recorded in [`versioned_real_dev_results.md`](versioned_real_dev_results.md).
Across five chronological UCI datasets, the gate beat RMM on four but lost badly on Beijing
(mean net-cost difference +8.54 vs RMM), beat the front-loaded certificate only on metro (mean
+8.29), and lost to version-reset Model Picker on four of five (mean +174.92). It used 22–200
certification labels and promoted on four datasets. The v2 models were retrained using 2,000 labels
from the preceding v1 evaluation block; those supervised training labels and costs were not charged.
This weakens any practical comparison further. The candidate fails the current retention criterion:
keep it as exploratory tooling, do not claim SOTA, and do not run confirmatory validation for this
version. A follow-up needs a predeclared allocation that curbs weak-version spend and includes
training cost in the objective.

A post-hoc 1:3 v1:v2 alpha and budget split on the same five streams changed net cost by a mean
of only -0.06 units (mean absolute change 1.32) versus the equal split. This sensitivity did not
rescue the candidate; see [`versioned_real_dev_results.md`](versioned_real_dev_results.md).

### Charged chronological follow-up (2026-11-04)

**Invalidated:** this run's v2 used every label through the end of the preceding scored window,
although it charged only 100 boundary-training labels. See the corrected provenance screen
[`versioned_real_provenance_fixed_results.md`](versioned_real_provenance_fixed_results.md).

The corrected provenance run is exploratory and remains exposed. It finds mean costs of 423.21 for
the version gate, 437.57 for the front certificate, 452.80 for RMM, and 413.80 for the version-aware
Model Picker. The gate wins against the certificate comparators on this five-stream panel and loses
to Model Picker on all five. This does not retain the method. Full accounting and per-dataset
results are in [`versioned_real_provenance_fixed_results.md`](versioned_real_provenance_fixed_results.md).

### Shared-budget rollback monitor

An opt-in rollback variant starts a fresh directional e-process after each promotion, splitting each
version's alpha allocation between promotion and rollback. In the corrected real-data screen it
changed mean cost by only −0.17 versus the promotion-only gate, while still losing to Model Picker.
The independent synthetic stress screen found weak rollback sensitivity. The conditional-null and
issue-time ledger remain exploratory; no confirmatory claim follows.

### Fresh-seed rollback stress screen and reserved-budget variant (2026-11-04)

The 100-seed/four-scenario stress screen found that the original dual monitor used almost all 200
labels but rolled back in only 4/100 degradation streams. A deterministic per-test reservation
then reduced null label use and false promotions, but cut late-improvement promotions from 64/100
to 29/100 and produced no rollbacks in any scenario. Both variants were worse than the original
promotion-only gate on late improvement and recovery. The rollback direction therefore fails the
current development-retention criterion; details are in
[`versioned_stress_screen_2026-11-04.md`](versioned_stress_screen_2026-11-04.md).
