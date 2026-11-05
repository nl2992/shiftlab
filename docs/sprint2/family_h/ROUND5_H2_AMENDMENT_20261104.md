# H2 Round-5 post-development follow-up protocol

Registered before the follow-up run. H2 was selected on the 20-seed development screen, so this is
post-development evidence on fixed simulator regimes and previously exposed real sources; it is not
independent confirmation.

## Question and scope

Does H2's adaptive observation spacing retain its dependence-null behavior with 1,000 Monte Carlo
replicates, and does the development-screened economic pattern persist across fresh policy seeds on
the tested simulator regimes and all 14 available real loss sources? The real data have no causal
change labels; their results are descriptive fixed-stream replays.

## Locked settings

All runs use the committed H2 implementation, T=2,000, B=200, label cost .05, switch cost 5, alpha
.05, and paired loss streams/randomization seeds. No threshold or policy changes are made.

1. **Synthetic follow-up:** 100 seeds, base `2026110801`, on
   `F0_better,F9_bursty_better,F1_late_800,F3_reversal_800,F5_dep_better_r8,
   S_dep_better_r95,F0_null,F5_dep_null_r8,F5_dep_null_r95`. Policies:
   `H2,D2,A5b,H1,H2-iid_space,H2-gateonly,gated_adaptive_range+front,
   CONTROL_never_switch`. Primary economic contrasts are paired H2 minus D2 and H2 minus A5b.
   H1/H2-iid_space/H2-gateonly are mechanism ablations; the adaptive-range host and never-switch
   are additional references. Report mean net cost, paired 95% t intervals, promotion, labels,
   decision delay, and runtime.
2. **First-order Markov null follow-up:** 1,000 seeds, base `2026110802`, on
   `F0_null,F5_dep_null_r8,F5_dep_null_r95,P_markov_null_r98`; policies
   `H2,H2-iid_space,H2-gateonly,D2,A5b`. Report episode-level promotion proportions with Wilson
   intervals and labels/cost. H2's nominal V2 scope is the stationary first-order Markov null;
   this does not test its real twin-null behavior or out-of-class validity.
3. **Real replay:** 3 paired policy seeds, base `2026110803`, on all nine cached Atlas sources and
   five timestamped fresh UCI sources. Policies `H2,D2,A5b,gated_adaptive_range+front,
   CONTROL_never_switch`. Report per-dataset mean costs and equal-dataset paired contrasts with a
   source-cluster bootstrap; no causal shift labels, independent-source claim, or row-level
   significance claim.

All three are post-development follow-ups, not pre-registered confirmatory tests. The simulator seed
bases are separate by round as specified in `docs/sprint2/SPEC.md`. No optional stopping or reruns
based on results are allowed; failures and incomplete outputs must be retained and explained.

## Reproduction

Commands and generated summaries will be added to `docs/sprint2/REPRODUCIBILITY.md` when the runs
finish. Raw records and manifests belong under gitignored `outputs/sprint2/round5/`.
