# Cycle 7: frozen execution and analysis contract

2026-11-01. Registered before cycle-7 validation seed use. Supplements Amendment 8;
does not change DSS gap 4, its spec or any acceptance margin. Development pilot results
were seen when this operational specification was written. This is fresh-seed validation
after development, not preregistration before all exploratory work or final confirmation.

## Inputs and comparisons

- T=1000; seeds [290000,290200), paired by seed across cells and methods.
- Primary cells: exactly the five family-1 IDs used by the frozen tuning script and
  the eleven reproduced family-3 shared failures in cycle 5.
- Neighbours: every adjacent level on one axis returned by the existing `fa.neighbours`;
  96 unique neighbours, 102 unique cost cells including the 16 failures. Preserve each
  parent's neighbour list, including neighbours that are other primary cells.
- Primary comparator registry: episode_geo, episode_equal, episode_front,
  allonset_edetector, online_fwer_spending, markov_lr_gate, thinned_hedged_gate.
  C1/C2 are excluded by Amendment 8. The four nongated R6 adaptations are supplementary
  on the primary cells and null grid; they cannot enter the safety-matched A1 comparator.
  These are scoped repository adaptations, not verified faithful reproductions of every
  named source. Carry the registry's implementation/contract limitations in the report.
- Frozen DSS `5b5c77b635e5`; no-delay-switch `fa0ffe73cf61`; gap-1
  `92b5f9740faa`; uniform `99ccbdfde7ab`. Run all four on primary cells and nulls.
  Neighbours need DSS and the seven primary baselines; ablations there are not required.
- Nulls: full cycle-6 dependence grid, 32 configurations. A3 uses its registered 18-cell
  subset; rho=.95 and B/T=.5 are additional stress tests. Fixed-delay release only.
- Record cost/round, loss, query and switch costs, requested labels, switches, any
  promotion, any correctly timed promotion and any false promotion. Oracle regimes
  are used only to score decisions after each run.

## Analysis locked before validation

Select the lowest-mean-cost primary baseline independently in each cost cell on the
same 200 seeds. This favours the comparator. All intervals are paired t 95% intervals,
unadjusted; they are not simultaneous confidence statements.

- A1: require at least 8/16 cell-wise upper CI bounds below -.01, and the upper CI
  bound of the equal-cell-weight mean difference below zero. Aggregate within each seed
  across cells first, then form the interval across 200 independent seeds; do not treat
  cells sharing seeds as independent replicates.
- A2: for each parent failure, average its neighbours' paired cost differences within
  seed, using each neighbour's own best baseline. Every parent's upper CI must be <+.01.
  Also report the aggregate over unique neighbours descriptively.
- A3: every registered rho=0 null and every rho=.5, B/T<=.1 null must have DSS point
  false-promotion frequency <=.15. At rho=.8 compare against the lowest null false-
  promotion frequency among the seven primary baselines per cell, with cost tie-break;
  require difference <=.05 for the historical relative test. Also report the absolute
  .15 check separately; relative success cannot support a dependence-safe claim.
  Report Wilson per-cell 95% intervals for all null estimates, including adverse cells.
- A4 primary: the uniform-acquisition ablation of the whole acquisition component must
  remove at least half of the aggregate A1 cost gain: mean(cost_uniform-cost_DSS) >=
  .5*mean(cost_best-cost_DSS), with positive candidate gain. Report a paired interval
  for the corresponding half-gain contrast. This threshold is the registered point rule;
  the interval is uncertainty, not an added post-hoc threshold. Report the same calculation
  for each new-rule ablation. A primary A4 pass alone attributes benefit to acquisition;
  it does not establish that the new gap/delay rules caused the cost gain or are novel.
  Gap-1 safety differences are a separate diagnostic, not a cost gain.
- A5: carry forward the scoped positioning audit of the unchanged rule, conditional on
  A1-A4, and its absence-search limits. Do not promote this to proof of novelty.
- Accept only if all A1-A5 pass; otherwise preserve a failed cycle-7 verdict, distinguish
  supported narrower claims, and record the next bounded action. No automatic gap retuning.
  Only a passing candidate permits a new, separately registered confirmation protocol.

## Execution and integrity

`scripts/run_atlas_cycle7_validation_v1.py` freezes a manifest with all cell definitions,
neighbour memberships, methods, spec IDs, seeds and SHA256s of code/protocol inputs before
starting a worker. Restart refuses changed inputs or mismatched records. Each completed
seed chunk is appended once, with the manifest digest and exact seeds. Partial writes are
detected. Only complete seed sets can produce acceptance verdicts. Source hashes supplement
Git HEAD because the workspace already contains uncommitted earlier research work.

Smoke runs use [180000,180002), never validation seeds. Alarm caching is a computational
change only and must match uncached decisions, query masks and costs on smoke streams.
Run relevant tests, then the full resumable evaluation. No downloads or licensed-data use.
Report elapsed time and preserve the raw records, manifest, complete tables and machine-
readable verdicts. A provisional native result-to-claim review follows completion;
external cross-family experiment-audit availability must be stated honestly.
