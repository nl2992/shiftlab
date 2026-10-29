# Causal-null constraint generation: development result

2026-10-29. **Decision:** keep this standard separation method as a comparison
baseline; it did not improve the original solver on the registered small cells.
No methodological novelty, synthetic efficacy or real-data result is claimed.

## What ran

The frozen protocol is `CAUSAL_CUTS_PROTOCOL_V1.md`. The diagnostic builds the
unmodified first-promotion learner and null sequence forms, then iteratively solves
an alternative-cost master LP with selected null-response constraints. At each
iteration it solves a full null best-response LP and adds the resulting pure
response if the risk constraint is violated. For the recovered behavioral policy,
it independently computes the exact-rational causal-null risk and scales its
root activation against the never-promote policy when necessary. That activated
mixture respects the request cap and has exact risk at most alpha. Results,
including every iteration, are in `causal_cuts_development_v1.json`.

The executed source is preserved byte-for-byte as
`causal_cuts_executed_source_v1.txt` and matches the SHA-256 in the result file.
The runnable script `scripts/research_risk_approx/screen_causal_cuts.py` differs
only by a subsequent lint annotation on the broad exception handler, which was
intentionally used to preserve failed diagnostic cells. The implementation
materializes the full learner and null trees and is not an independently
optimized large-scale constraint-generation library.

## Results

| T | Status | Added null cuts | Reference LP objective | Best verified safe cost | Master solve time total | Separation time total | Reference solve time |
|---|---|---:|---:|---:|---:|---:|---:|
| 5 | numerical convergence | 26 | 2.399234375 | 2.399234375 | 0.151 s | 0.080 s | 0.014 s |
| 6 | numerical convergence | 51 | 2.88176875 | 2.88176875 | 0.558 s | 0.182 s | 0.017 s |
| 7 | 64-cut limit | 64 | 3.3712896875 | 3.4141142857 | 1.315 s | 0.290 s | 0.029 s |

The timing columns are sums of solver-call wall times from one run. They exclude
policy recovery, exact-rational risk/cost evaluation, Python overhead, and the
shared tree construction, so they are not a complete performance benchmark. The
reference was solved after building the same tree. At T=7, the final master
objective was 3.3415481994 and the final recovered policy had null risk about
0.2938 before safe activation; the best earlier activated policy cost
59747/17500. The difference from the reference is a development comparison,
not an independent certified optimality gap.

All iterations returned pure endpoint null responses with zero recorded opponent
flow residual. Their response-LP risk agreed with the independently evaluated
exact-rational recovered-policy risk to within 2.8e-16; all root-activated
policies had risk at most 1/10. T=5 and T=6 finished at the numerical objective
and rational recovered-policy cost of the reference. T=7 hit its registered
cut limit. A numerical restricted-master objective is not a rigorous lower
bound without exact cost coefficients and dual-residual verification; therefore
no certified anytime gap is reported. The reference LP objectives are numerical,
not new exact optimality certificates.

## Interpretation and next step

This concrete screen supplies evidence against generic null-cut generation as an
immediate speedup here. It also illustrates why approximate optimization and
safety verification are different: every root-repaired incumbent is safe, but
its economic gap can remain substantial. Standard sequence-form double-oracle
methods already cover the general cutting-plane mechanism; an improved method
must provide an additional structural or computational result.

Continue the goal with a candidate that attacks the full pre-promotion tree or
produces a more informative bound/certificate. A rigorous rational master lower
bound and an implicit best response would be necessary before claiming a useful
anytime gap or asymptotic advantage. Existing synthetic and real-data efficacy
and strong-baseline gates remain unmet.
