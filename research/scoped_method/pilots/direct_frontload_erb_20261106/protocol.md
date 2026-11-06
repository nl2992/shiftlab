# Direct front-loading plus E_rb screen (development only)

Protocol document for the one previously missing composition check; it is not a new method or confirmation experiment. The file was not committed or checksummed before execution, so pre-run registration timing cannot be independently verified. Treat this as a development protocol description, not an auditable preregistration.

## Question

Does combining E_rb with the already registered front-loaded, correctly ranged Gated acquisition policy produce useful economic headroom over each component and never-switch, under identical information and cost contracts?

## Frozen matrix and run

Use the existing registered simulator regimes: `F0_better` (persistent improvement), `V_late_600` (delayed persistent improvement), `F3_reversal_800` (improvement followed by reversal), and `F0_null` (no improvement). Use 20 fresh paired seeds per regime, seed base `2026110618`, horizon/regime settings unchanged, delay as registered, hard label budget 200, label price 0.05, switching cost 5, and nominal alpha 0.05. Every method receives the same generated loss stream, feedback delay, budget, and policy-visible information.

Compare `E_rb:gated_adaptive_range+front` against `E_rb:gated_adaptive_range`, `gated_adaptive_range+front`, `rmm:gated_adaptive_range+RMM`, and `CONTROL_never_switch`. The first three are component or applicable certified/restart comparators; never-switch is the feasible economic reference. RMM has a different error guarantee (and is labeled as such), so its cost is descriptive, not a matched-safety comparison.

## Outcomes and decision rule

Primary outcome is paired net deployment cost (predictive loss + 0.05 per requested label + 5 per deployment switch). Report mean paired differences and two-sided paired t intervals by regime. Also report loss, labels, switches, first promotion, rollbacks, and null promotion frequency. The 20-seed null rate is only a pilot diagnostic and cannot validate a 0.05 guarantee.

A development signal requires at least 5 cost units of mean savings over **both** the strongest component comparator and never-switch in `F0_better` or `V_late_600`, with the paired interval below zero; no more than 5 units mean harm versus never-switch in `F3_reversal_800`; and no repeated false promotion in `F0_null`. These thresholds are frozen before outcomes. Failure ends this combination search. Passing only merits separately frozen confirmation; it does not support a novelty claim because both mechanisms are established components.

## Reproduction

Runner: `PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py --kind synthetic --regimes F0_better,V_late_600,F3_reversal_800,F0_null --policies E_rb:gated_adaptive_range+front,E_rb:gated_adaptive_range,gated_adaptive_range+front,rmm:gated_adaptive_range+RMM,CONTROL_never_switch --seeds 20 --seed-base 2026110618 --workers 1 --out research/scoped_method/pilots/direct_frontload_erb_20261106/run`
