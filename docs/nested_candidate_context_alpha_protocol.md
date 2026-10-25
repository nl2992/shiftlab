# Nested candidate-by-context alpha allocation protocol

**Status:** Frozen protocol for a gate-level development screen and independent
familywise calibration. A separate confirmation is required before retaining a
performance claim.

## Question

Does splitting a validation-rank candidate error budget across learner-visible
contexts improve the net value of a repeated-candidate promotion gate under a
hard label cap, relative to (a) the same candidate-rank spending with one global
test per candidate and (b) equal rather than pilot-volume context weights?

The experiment isolates the gate. Its 13 candidates are frozen synthetic utility
processes, not fitted classifiers. This is an implementation and allocation
benchmark, not evidence that an end-to-end classifier controller has improved.

## Allocation and validity

Candidate order is fixed using fully labelled validation outcomes before shadow
monitoring. Candidate rank `r` receives `alpha_r = alpha / [r(r+1)]`; the finite
13-candidate sum is below `alpha`. A separate outcome-free pilot records proxy
context counts `n_g`. The equal rule uses `v_g=1/2`; the volume rule uses
`v_g=(n_g+1/2)/(n_0+n_1+1)`. Nested tests use `alpha_{r,g}=alpha_r v_g`, so
`sum_{r,g} alpha_{r,g} <= alpha` conditional on the pre-monitor validation order
and pilot counts. The rank-only comparator tests each candidate on the pooled
stream at `alpha_r`.

Each context test updates only on that observed context. The fixed-stake mixture
uses direct inverse-propensity estimates under outcome-independent uniform
querying, with a predictable support bound based on the declared minimum query
probability and known switching charge. It is valid for the context-conditional
bounded-mean null when candidate gains are observed only after a successful
query. This does not establish validity for adaptive covariate-dependent
querying, delayed feedback, context drift, action-dependent outcomes, or a
misspecified support bound. Pilot-volume allocation is predictable and uses
context IDs only; evaluator latent context and potential gains never determine
the weights.

For each context, the controller selects the earliest validation-ranked
candidate whose context test crosses. The global comparator selects the earliest
ranked candidate with a pooled crossing. All methods share the generated
candidate gains, query random numbers, and pathwise label budget. Utility is
scored on a separately generated deployment segment, including one switching
charge per promoted context and the realized label cost.

## Registered synthetic grid

- Candidates: 13; validation/monitor/deployment horizons: 200/400/400.
- Profiles: exact-zero nondegenerate null, strict-negative control,
  homogeneous benefit, two context specialists, and benefit reversal after
  shadow monitoring.
- Latent context-1 prevalence: 0.10, 0.50, 0.90.
- Proxy misclassification: 0, 0.05, 0.10.
- Query probability: 0.80, independent of current outcomes.
- Hard monitor label caps: 20% and 40%; monitoring stops immediately after the
  cap is spent.
- Development: 200 streams per profile/prevalence/proxy-error/cap cell, seed
  root `1124202026` (cells are separated by 1,000,019).
- Null calibration: 2,000 streams per null/profile/cell, exact one-sided
  Clopper–Pearson upper limits with simultaneous Bonferroni correction across
  108 profile/prevalence/error/cap/method cells. Every upper limit must be at
  most 5%, and every pathwise cap must hold. Calibration seed root
  `2124102026`, disjoint from development.

The primary development contrast is nested volume versus rank-only in the
specialist profile, averaged equally over the registered prevalence, proxy-error
and cap settings. Nested equal is the predeclared allocation ablation. The
development grid selects no winner. If a candidate rule clears a practical
utility margin of +1 realized unit per 400-event deployment stream against both
comparators, the independent confirmation uses 2,000 streams in each specialist
profile/prevalence/proxy-error/cap cell at seed root `3124302026`. It reports a
hierarchical paired bootstrap that resamples streams within each of the 18
settings and weights settings equally. Its two-sided intervals use 97.5% coverage
per contrast, giving at least 95% simultaneous coverage across the two primary
comparisons; both lower limits must exceed +1.0 for retention. Bootstrap seed is
`9982303019`. Confirmation is conditional on the separately passing calibration
manifest and shares no data-generation seed block with development or calibration.

## Interpretation limits and visuals

The current simulator provides bounded candidate-level utility increments and
does not generate fitted model predictions, observed binary labels, selective
feedback, or source-grounded intervention costs. A favorable result motivates
integration into the existing fitted 13-candidate hard-budget controller; it
does not establish that integration's efficacy. Weighted Bonferroni composition
and fixed-stake e-processes are established tools; no novelty claim follows.

Any research visual for this experiment must be produced with PaperBanana. The
protocol and metrics are tabular, so the initial screen does not require a
figure.
