# Exact-gap Markov SUI with sparse starts: development protocol v1

**Registered:** 2026-11-04 after reviewing the separate dense-start screen; uses disjoint seeds.
Development only, not confirmation or a novelty/SOTA claim.

## Change from the first screen

The first screen used a start at every queried label and gave the SUI candidate an equal prior
over about 100 starts, while the existing Markov gate uses at most eight starts. Its null screen
had no false promotions, but its cost was worse than all three comparators, with a large loss on
the mandatory adverse cell. This second screen changes only the predeclared start prior to eight
fixed, evenly spaced label indices (the same order of multiplicity as the existing Markov gate).
The alternative and null likelihoods, rectangular upper bound, evidence threshold, policy, cells,
metrics and comparator set stay fixed. The start prior is selected as a matched multiplicity
control, not tuned to seed outcomes.

## Frozen run

- Seeds `[720020,720040)`, 20 paired streams per cell. Seed fields were checked against existing
  `outputs/failure_atlas_v1*/records.jsonl`; none overlap this block.
- Methods: `episode_front`, `markov_lr_gate`, `gap_envelope_rho08`, `gap_markov_sui`.
- Same four alternative cells, eight null-twin cells, horizon, fixed calendar, cost and rollback
  definitions as `failure_atlas_gap_markov_sui_development_protocol_v1.md`.
- Sparse start indices are `unique(linspace(0, n_calendar_labels-1, min(n_calendar_labels,8)))`;
  weights are equal over the complete fixed start set, with unit capital before activation.
- Source hashes and the paired raw records are saved in the run manifest and output directory.

## Advance rule

Use the same screening criteria as the first protocol: at most 3/20 false promotions in every
null cell; paired equal-cell cost 95% intervals below zero versus both `markov_lr_gate` and
`episode_front`; and adverse-cell upper paired 95% cost difference at most `+.01` versus the
lower-cost reference. This small screen can reject the candidate; it cannot validate a claim.
