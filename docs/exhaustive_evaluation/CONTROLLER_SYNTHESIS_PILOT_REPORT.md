# Exact finite-class synthesis and robust-FSC execution audit

2026-10-30. Previous turn: progress (non-partitioned PFA formula/scope audit committed). This continuation executes a complete small controller-family search and checks its root mixture against an independent LP. Goal remains active; this does not validate a new planner.

## What was synthesized

74 deterministic controllers:72 combinations of query start{1,3,5,7}, stride{1,2,3}, positive-label streak{2,...,7}, plus never/always deploy. Controllers have public deterministic memory; all queries count immediately and all label releases precede the event decision. Null: full-history adaptive positive probabilities in[0,1/2]. Alternative: IID positive probability4/5, action0/1 expected losses4/5 and1/5, query fee1/100, switch fee1/10. This model-specific toy is not a real-data guarantee.

The existing exact causal-null verifier evaluates each policy. A separate finite-state recursion computes its exact rational alternative cost including queries and switches. Choose either a feasible deterministic controller or a convex root mixture satisfying the verified risk bound<=1/20. The optimization over the finite-class simplex needs at most2 nonzero policy weights, by standard LP extreme-point geometry; all feasible pairs are enumerated using rational arithmetic. This is known constrained randomization, not a new synthesis theorem.

Root randomization is hidden initially. The convex average of component worst-case risks is a sufficient risk bound even if Nature subsequently infers the component. It may be loose; optimality is only for this sufficient finite-class constraint, not every hidden-randomized feasible policy.

## Completed results

| Horizon / budget / delay | Best deterministic exact cost | Best root-mixture exact cost | Search runtime |
|---|---|---|---:|
|12 /6 /2 |1300479/156250 |32375911/3906250 |.066s |
|24 /12 /2 |153339779/9765625 |6457196039/439453125 |.394s |

At horizon12 mix streak5 with weight24/25 and streak4 with weight1/25. At horizon24 mix streak7 with16/45 and streak6 with29/45. Both select start1/stride1 and exactly spend the sufficient risk bound1/20. Root mixing improves cost within the family; finite-class optimization can recover gain that a deterministic-only comparison misses. Timings include enumeration/risk/cost/pair selection, but are a single-host diagnostic, not a controlled speed benchmark.

The12-event search visits3466 summed risk states and4379 alternative states;24-event search visits11222 and17843. These sums count each policy separately and do not imply reusable cross-policy state compression. The worst-case unrestricted sequence-form planner may find better policies; no unrestricted lower bound is computed here. Thus no useful gap certificate, approximation ratio or matched-quality end-to-end speedup is established.

Three new tests: exact2-policy optimization agrees with independent HiGHS simplex LP on20 random finite families; known never/always policies have exact analytical costs; the selected streak family has risk agreement with standard product-state LP at horizon24.14 relevant tests pass including existing risk verifiers. Ruff0.17.1 checks pass. Registration/source hashes precede execution; originals and earlier one-shot J diagnostic are unchanged.

## Published robust-FSC comparator

[Cubuktepe et al., Robust Finite-State Controllers for Uncertain POMDPs, AAAI2021](https://ojs.aaai.org/index.php/AAAI/article/view/17401) compute robust finite-memory controllers through optimization/linearization. The earlier SOURCE_FORMULA_AUDIT_V2.md already records full-text comparison and author revision0cc828d; its fixed-controller verification step is known machinery. This continuation inspects the pinned repo README, src/readme.md, CLI entry point and SCP imports; it does not repeat a complete proof audit.

The native CLI parses PRISM/DRN interval models, reachability or reward specs and a termination threshold. The current host lacks stormpy, gurobipy, pycarl, cdd and pipenv; SCP requires Storm parameter support plus those imports. Dependency discovery is directly recorded in controller_synthesis_pilot_results.json. No native author solver was executed. This is a local execution limitation, not a negative efficacy result, an inapplicability proof or evidence of novelty. Do not represent the SciPy product-state LP as that author synthesis pipeline.

More importantly, a faithful matched model still needs an explicit mapping: the learner cannot see pending labels, Nature can; safety is a worst-case null probability while utility is evaluated under a different alternative law. Giving the learner Nature's product-state information or averaging the laws changes the problem. Whether a robust-FSC formulation can encode the same asymmetric histories and two-law constraint, with what complexity/quality guarantees, remains unresolved. Missing dependencies do not resolve that mathematical question. Generic compact controllers plus a verifier/root mixture are already known techniques; the present pilot supplies no irreducible new delta.

## Disposition and next steps

Restrict CandidateJ's established result to fixed-policy exact risk verification and finite-class engineering. Continue only the residual synthesis/value-gap question; reject claims that tree-versus-DP timing or this toy family alone establishes a new planning algorithm. Compare against unrestricted exact sequence-form optima on tractable overlap cells before any quality claim; retain the distinction between a finite-class feasible upper value and a valid unrestricted lower bound. A source reduction may close the method claim without a large solver run.

Remaining work includes a genuinely matched robust-synthesis formulation, certified PFA-sentinel computation if used operationally, and a substantive acquisition/action coupling beyond the known mixtures and pacing already tested. The previous504-setting round remains negative globally. No need to rebrand root randomization as a new combination. This74-policy search is not added to the monitor-grid count.

Artifacts: controller_synthesis_pilot_registration.json, controller_synthesis_pilot_results.json; script pilot_controller_synthesis.py. Run command refuses overwrite. All reported exact costs are rational, LP validation is numerical. No reserved real windows, raw downloads, paid solver license, remote jobs or subagents were used.
