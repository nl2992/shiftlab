# P6 late-prior transfer screen — frozen protocol (2026-11-07)

## Purpose and status

This is one bounded test of whether an already validated finite-horizon start-prior shape transfers
to P6's Markov-SUI detector under ShiftLab's label-budgeted model-switching contract. The weighting
rule is standard prior mixing and is **not** a novelty claim. This screen may support a scoped
empirical result only if it improves P6's late-change deployment economics against strong matched
comparators and clears its registered null/adverse checks. It does not open any real or locked data.

## Candidate

`P6_LRMD_Beta20` uses the existing `P6_LRMD_U` architecture and code paths, changing only the
predeclared start weights over its full 20-start label-clock grid. Start j is opened after queried
disagreement outcome `1 + 10j`, for j=0,...,19. Its fixed weight is the Beta(2,1) mass in equal bins,

`w_j = ((j+1)/20)^2 - (j/20)^2 = (2j+1)/400`.

The weights sum to one. They are fixed before observing any evaluation stream, are not renormalized
over starts that happen to be observed, and do not depend on a realized query count. The SUI
components, threshold, alpha allocation, acquisition, rollback, and deployment logic remain as in
P6_LRMD_U. Use the existing contract: T=2000, B=200, label cost 0.05, switch cost 5, alpha=0.05,
and the regime's registered feedback delay. All methods receive the same evaluator-generated stream
and query budget.

## Frozen methods

Candidate and parent: `P6_LRMD_Beta20`, `P6_LRMD_U`, `M_LRMD_SUI`.

Published certificate-policy comparators: `gated_deployment`, `gated_adaptive_range`,
`gated_adaptive_range+front`, `discern_style`, `discern_design_floor`,
`SMCS+retain-incumbent`, and `choe_ramdas_eb+front`. Xu's acquisition-only adapter is reported
separately as `xu_acquisition_only`; it is not Xu et al.'s published risk certificate.

Matched restart and robust/fast-selector references: `rmm:gated_deployment+RMM`,
`E_srr:gated_deployment` (e-CUSUM), `E_srrSR:gated_deployment` (e-SR),
`E_glr:gated_adaptive_range` (uncertified Bernoulli GLR), `P7s_settled`, `QSG`,
`qiu_delayed_movement`, `model_selector_causal`, `cams_adapter`, and `CONTROL_never_switch`.
SR/CUSUM/GLR false-promotion rates are described as empirical; their published guarantees differ
from P6's anytime false-promotion target.

## Evaluation registry and decision rule

* Primary synthetic cell: `F1_late_1200` (late improvement begins at the registered 1200-event
  point), on 100 paired seeds with seed base `2026110714`.
* Secondary/adverse cells on the same frozen seed block: `F1_late_800`, `W_late_1000`,
  `S_late_1500`, `F0_better`, `F3_reversal_800`, and `S_reversal_400`.
* Null checks: `F0_null`, `F5_dep_null_r8`, and `F5_dep_null_r95`, 1,000 seeds with seed base
  `2026110715`. Null rows are not used to change the weights.
* Primary metric: paired difference in net deployment cost `J(candidate)-J(comparator)` at identical
  horizon, pathwise label budget, label cost, switch cost, delays, and information access.
  Report predictive loss, label expenditure, switching expenditure, promotion time, rollback, and
  false-promotion rates with exact or Wilson intervals as appropriate.
* The primary direct comparison is against the pre-existing strongest certificate-policy port on
  this target, `gated_adaptive_range+front`, and against the uniform-start parent `P6_LRMD_U`.
  Report paired 95% intervals. Also report all other prelisted baselines; do not select a new
  comparator using these evaluation outcomes.
* Development advancement requires both primary paired 95% intervals to be below -5 net-cost units
  and a Wilson upper bound no greater than 0.0936 on `F0_null`, `F5_dep_null_r8`, and
  `F5_dep_null_r95`. Report every other cell regardless of direction. Failure ends this candidate
  lane; no weight tuning or replacement prior follows from these outcomes.

## Data integrity and interpretation

Synthetic oracle truth is evaluator-only. Preserve the frozen run source hashes, manifest, and raw
records under the ignored output tree. This screen is a finite synthetic transfer test under the
simulator's stated Markov-SUI assumptions, not evidence of real-world transfer. No real data is
opened before the gate passes and a separate real-source registry/protocol is frozen.

The closest prior art already includes arbitrary weighted e-detectors and Markov transition-change
detectors; see `docs/sprint2/novelty/NOVELTY.md` and Shin, Ramdas & Rinaldo (2022),
https://arxiv.org/abs/2203.03532, and Saha & Ramdas (2026),
https://arxiv.org/abs/2607.28322. Any positive result must be framed as an empirical economic
advantage in this deployment contract, not as a new mixture construction.
