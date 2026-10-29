# Early promotion-pruning development protocol v1

Registered 2026-10-29 before constructing or running the early-pruning adapter.
Starting branch revision: 0ac61bc. This is a deterministic computational and
correctness diagnostic; it does not support an efficacy or novelty claim.

## Comparison and scope

Compare the existing unmodified `FirstPromotionDecomposedGame` with a new adapter
that applies the epsilon=0 dominance rule from `PROMOTION_DOMINANCE_RESULTS_V1.md`
inside the alternative-tree build, before calling the exact continuation DP.
Keep the original pre-promotion information sets, request timing, null-response
tree and numerical LP. Mark every prohibited promotion realization variable with
an exact zero bound in the LP; an arbitrary placeholder coefficient is permitted
only for a variable constrained to zero. An independent full-history evaluator
must check every returned policy's causal-null risk and alternative cost.

Registered HMM cell: transition probabilities 1/4, emissions 1/20 and 19/20,
prior 1/2, B=3, delay=1, alpha=1/10, query fee 1/100 and switch fee 1/10.
Evaluate T in {5,6,7,8}; 200,000 builder nodes and 60-second LP limits as in the
reference. For each cell use three fresh-process repetitions per algorithm,
alternating execution order by repetition. Record raw elapsed build, solve and
policy-evaluation time, peak sampled process RSS and measurement interval, learner
and null sequence counts, builder nodes, continuation cache size, skipped calls,
recovered expected cost, full causal-null risk, solver residuals and code hashes.
Record failures and limits rather than dropping them. Timing is exploratory and
machine-dependent; no median or ratio is evidence of an asymptotic rate.

Correctness gates: exact policy risk <=1/10; pathwise action/query rights enforced
by the same available choices; finite recovered costs agree within 1e-7 between
algorithms; costs agree with each method's LP objective within 1e-7. T=6 must
also agree with cost 461083/160000. Run targeted tests for zero budget,
unavailable feedback, fixed delay 2, the reference T=6 case, and behavior at
marked and unmarked histories; preserve the original reference code. Test that
null search never observes the HMM state or pending feedback through the pruning
rule. If a check fails, retain the evidence and do not claim safety or speed.

Use exact rational arithmetic for marking; distinguish LP numerical tolerances
from exact worst-case recovered-policy risk. Output to a new, non-overwriting
`docs/risk_preserving_approx/early_pruning_development_v1.json`. This is not a
registered confirmatory experiment, a synthetic efficacy comparison or a real
sequence study. No seeds, real data or historical output modifications.
