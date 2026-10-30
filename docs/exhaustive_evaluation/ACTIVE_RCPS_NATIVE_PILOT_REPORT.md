# Native learned-query baseline pilot

2026-10-30. Previous turn: progress (stricter CUSUM comparison committed). This continuation runs the six original active-RCPS simulation arms on3 seeds with200 labels each, audits the source/paper mapping and verifies an optimizer transport primitive. Goal remains active.

## Completed experiment

Pinned author commit a67f85d603df2bb3e32ef007f445191923ebd990; original test_once function AST executed unchanged. Declared repairs: inactive-branch syntax repair in a separate compatibility copy, and modern NumPy/Torch return conversion. All original Python sources and compatibility copies were checked. All registered source hashes still match after execution. No original author files were edited.

Registration: author_rcps_pilot_registration.json. Terminal status: author_rcps_pilot_status.json. Results: author_rcps_pilot_results.json. Elapsed runtime241.99seconds on this host; not a controlled hardware benchmark. Each arm uses200 labels per seed. This is much smaller than the author CLI defaults and cannot reproduce the full paper's statistical findings.

The native analytical feasible threshold is beta*=1−sqrt(.1)=.683772. Lower certified beta is better provided it remains feasible. Means below are descriptive across3 seeds:

| Original arm name | Mean actual certified beta | Mean processed observations | Mean query probability |
|---|---:|---:|---:|
| oblivious | .868687 | 637.3 | .3000 |
| label all | .845118 | 200.0 | 1.0000 |
| optimal | .865320 | 1980.0 | .1000 |
| learned | .841751 | 2001.3 | .1003 |
| cv only | 1.000000 | 681.7 | .3000 |
| cv + learn_var | .851852 | 2059.7 | .1000 |

Every terminal certified risk is below.05 on these seeds (largest.026987), but3 trajectories cannot validate an anytime5% guarantee. The original curve's reported beta is a different grid entry from the actual certified beta; both are preserved in results. No superiority interval or selected winner is asserted from3 seeds.

The learned arm's improved threshold relative to uniform querying comes with substantially more processed events at equal labels. In this native task, extra unlabeled covariates/control-variate updates are allowed. In a finite deployment horizon with query/switching cost, that is a different information/utility comparison. Do not translate the threshold difference into a cost saving for ShiftLab.

## Why a source-as-written baseline alone is insufficient

ACTIVE_RCPS_CONTRACT_AUDIT.md records two precise source/paper differences: the named learned variance object is trained against raw risk; the normalization loss has a different derivative from the paper's displayed maximization objective. The normalization gradient was verified by running the actual source class with a fixed variance predictor, not inferred from the pilot alone. The published PDF AppendixA.2 confirms the displayed normalization objective and residual-variance fitting. Neither difference invalidates risk inference by itself, and no author intent is inferred.

Therefore, benchmarking only this source path risks comparing against a weak implementation. The next matched experiment must retain both source-as-written behavior and an explicitly labeled paper-formula adaptation. No silent repair and no new-method claim from fixing baseline fidelity.

## Implementation advance and next run

A vectorized NumPy COCOB component matches the author-vendored Torch optimizer exactly on200 replayed gradient updates (7 independent rows ×13 coordinates), including zero/masked gradients and large scale changes. MIT attribution/license is retained. See cocob_component_parity.json. This is a validated optimizer component, not yet a full learned-query implementation.

Next runnable slice: complete the native predictor/query transport with delay1 parity, then add hard caps and fixed-delay queues that freeze bet/propensity/prediction at issue. Test source-as-written versus paper-formula/residual-variance variants, fixed-query control and the tuned FTL/CUSUM baselines. Use the same finite horizon/outcomes, charge pending labels and report total cost. Only after native-trace parity and chronology checks should independent efficacy runs begin. Continue the remaining published-family inventory; this pilot does not close exhaustive comparison or novelty.

No new combinations are counted from this reproduction or optimizer port; the prior1836 effective configurations remain the current sweep count. Reserved real windows remain closed. No paid or remote jobs launched.
