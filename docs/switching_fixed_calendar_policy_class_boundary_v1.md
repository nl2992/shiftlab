# Fixed-calendar policy class: source-equivalence boundary

**Date:** 2026-10-29. **Status:** synthesis of existing primary-source audits; the candidate
policy class is not a novelty claim.

## Scope

The registered six-cell result certifies that, for its finite parameter grid, a fixed opportunity
calendar attains the unrestricted causal-game value to at most `1.6e-10`. The remaining comparison
is therefore among policies that may skip calendar opportunities, choose deployment actions,
and randomize their robust evidence rules. This note determines what that comparison does and does
not establish against known method classes. It adds no new source or theorem beyond the audits
linked below.

## Policy-class relation

For any fixed finite horizon, a fixed calendar and bounded label delay give a finite controlled
experiment. The learner's physical state may include time, incumbent, remaining query rights,
pending outcomes, and its released observation history. An unconstrained HMM-only optimizer is an
ordinary finite-horizon belief-state POMDP. With a terminal false-promotion constraint under one
known null law, it is a chance-constrained POMDP. With adaptive sensor/query choice, stopping, and a
sampling cap, it is a constrained sequential experiment. These are established formulations; the
existing audits cover utility-aware sensing/stopping, usage-constrained testing, RAO*, and
constant-horizon CC-POMDP approximation.

ShiftLab's exact version is stricter than any one of those reductions: the objective is expected
cost under a recurrent HMM, while safety is worst-case reachability under a separate causal null
whose adversary sees pending outcomes hidden from the learner. Exact history augmentation gives a
finite robust partially observed game; it does not give a compact state or an efficient algorithm.
The fixed-calendar restriction removes query-event timing as a degree of freedom, but does not
change this information asymmetry or turn the robust constraint into a standard single-kernel
chance constraint. The sequence-form LP is an exact small-instance oracle. Robust FSC search and
verification are available generic tools, but the audited source gives local optimization rather
than a utility approximation to this two-kernel oracle.

## Novelty decision

No source-audited equivalence currently proves that a published algorithm attains the exact
ShiftLab two-kernel contract. Conversely, no distinct acquisition mechanism or approximation
guarantee has been identified. Thus the fixed-calendar robust test/action class is a comparator
problem, not a methodological contribution: adding delay queues, a budget counter, a risk state,
or a hidden HMM mode is state augmentation. A claim becomes defensible only with a structural
compression/approximation theorem preserving the causal-null reachability risk and bounding
economic cost against the full-history oracle, or a growing-family separation from the strongest
resource-matched sequential-control method.

This outcome does not authorize efficacy sweeps or real-data work. G1 remains active only for that
specific structural theorem/separation; G2-G5 remain held. If the next source-level or mathematical
attempt again yields only state augmentation or a generic controller, revise or stop this
algorithm hypothesis rather than rebranding the benchmark.

## Audited boundaries

- [`switching_episode_composition_grid_protocol_v1.md`](switching_episode_composition_grid_protocol_v1.md)
  and [`switching_calendar_exact_cert_protocol_v1.md`](switching_calendar_exact_cert_protocol_v1.md):
  registered comparison and exact six-cell timing certificate.
- [`switching_monotone_risk_ccpomdp_reduction_v1.md`](switching_monotone_risk_ccpomdp_reduction_v1.md):
  standard chance-constrained POMDP scalarization and its monotonicity limitation.
- [`switching_robust_fsc_reduction_audit_v1.md`](switching_robust_fsc_reduction_audit_v1.md):
  exact history augmentation, robust FSC prior art, and lack of a compression guarantee.
- [`switching_ccpomdp_approximation_audit_v1.md`](switching_ccpomdp_approximation_audit_v1.md),
  [`switching_risk_search_active_test_audit_v1.md`](switching_risk_search_active_test_audit_v1.md),
  and [`switching_usage_constrained_sequential_testing_prior_audit_v1.md`](switching_usage_constrained_sequential_testing_prior_audit_v1.md):
  established constrained planning and active sequential-testing ingredients.
- [`switching_information_risk_contract_v1.md`](switching_information_risk_contract_v1.md):
  statistical evidence and current-regime economic forecast must remain separate; historical
  evidence does not certify value after a reversal.
