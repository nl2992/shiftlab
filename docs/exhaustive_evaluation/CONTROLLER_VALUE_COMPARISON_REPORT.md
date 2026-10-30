# Matched finite-class versus unrestricted controller reference

2026-10-30. Previous turn: progress (exact finite-class synthesis pilot committed). Four registered overlap cases completed. Goal remains active; this is a negative quality-gate result, not a new planner.

## Matched information and economics

Both evaluators use positive-label probability4/5 under the IID alternative, action costs4/5 versus1/5, query fee1/100, switch fee1/10, horizon4/5, budget3/4 and delay1/2. Null is full-causal-history probabilities in[0,1/2]; first-promotion risk bound1/20. The sequence-form game's RegimeModel has prior1=1, zero transitions and emission1=4/5, exactly matching the class recursion; hidden emission0 is unreachable. No oracle features enter the policy.

Class:30 streak/start/stride controllers plus never/always, exact per-policy risk/cost and optimal2-policy root mixture under its sufficient convex risk bound. Unrestricted reference is the existing CausalSwitchingGame sequence-form LP: it may randomize at learner information sets and reverse actions, with the same losses/fees and first-promotion constraint. This is a genuine larger policy class, not the author robust-FSC solver. Model differences are not hidden by comparing different estimands.

For each selected class component, an independent adapter embeds the policy in the full-history game. Its exact forward cost and causal-null risk match the compact recursions. The LP policy is separately rationally recovered and its risk verified, with root activation repair if necessary. All four repaired policies have exact risk1/20 here; no repair changes the displayed costs.

## Results

| Horizon/budget/delay | Exact finite-class feasible cost | Exact recovered unrestricted-policy feasible cost | Class excess versus that policy | Class search / unrestricted seconds |
|---|---:|---:|---:|---:|
|4/3/1 |617/200=3.085 |7657/2500=3.0628 |.7248% |.0068/.0670 |
|4/3/2 |617/200=3.085 |617/200=3.085 |0 |.0185/.0676 |
|5/4/1 |180256/46875≈3.84546 |23653/6250=3.78448 |1.6114% |.0241/.4344 |
|5/4/2 |771/200=3.855 |771/200=3.855 |0 |.0275/.2872 |

The5/4/1 cost difference is exactly5717/93750. Because the recovered policy is a verified feasible competitor, this establishes that the finite-class returned value exceeds **some feasible policy** by1.6114%. Any unrestricted optimum is no larger than that competitor's cost. Therefore the class cannot meet a1% relative-to-optimum tolerance in that cell, even without treating the numerical LP objective as a certified lower bound. The relative gap to the actual optimum could be larger.

The numerical objectives agree with these recovered feasible values to solver tolerance. Equality of feasible values in two cases does not prove exact optimality unless a lower bound is certified. No formal unrestricted lower certificate is produced here. Thus these are exact feasible-policy comparisons plus numerical optimization evidence, not certified two-sided value intervals.

The class is faster on these tiny cells, but violates the proposed quality tolerance in one registered case. Single-run wall-clock ratios on tiny problems are not a scalable matched-quality speed claim. The full-history LP built1559 nodes for horizon4 and9429 for horizon5. No larger case was silently attempted or restarted; node cap200000 and native LP time limit60seconds were retained.

## Verification and provenance

14 relevant tests pass: random-family root-mixture versus independent LP, analytic alternative costs, risk DP/product LP agreement, existing sequence-form optimality/information checks. All4 selected-component embeddings pass exact risk and cost assertions during the run. Ruff0.17.1 and diff checks pass.

The first lint pass identified closure-variable style issues and an unused recovered-policy binding. The experiment nevertheless ran synchronously and all exact assertions passed. Its executed source is retained byte-for-byte as value_executed_compare_controller_value.py.txt, matching the registration hash. The current source binds closure variables explicitly and renames the unused variable; it was linted afterward. No outcomes/parameters changed and no experiment rerun is presented as new evidence. Manifest distinguishes executed and current code.

Artifacts: controller_value_comparison_registration.json, controller_value_comparison_status.json, controller_value_comparison_results.json. Source snapshots/hashes preserved. The command python scripts/exhaustive_evaluation/compare_controller_value.py now refuses overwrite. No reserved real outcomes or paid/remote solvers used.

## Disposition

Reject a matched1%-quality efficiency claim for this streak-class synthesis pilot. It is useful finite-class engineering, not a new approximation method. Enlarging the controller class could close the observed gap but must charge search/construction cost and compare at the same value tolerance; replacing the comparator with a weaker class would not resolve the failure.

Next substantive step: inspect recovered optimal action/query policies to locate what this class cannot express, then determine whether adding that structure reduces to known finite-state synthesis. Native robust-FSC execution/model mapping, CPOMDP reduction and certified lower certificates remain open. A missing solver dependency does not establish a novel residual. Keep the overarching goal active and preserve this failed gate.
