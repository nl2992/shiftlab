# AnyRank adaptation for the ShiftGuard candidate-policy benchmark

**Status:** frozen development protocol; not an independent confirmation.

## Question and estimand

Can a conservative full-information policy-ranking procedure identify a candidate whose downstream reward distribution dominates the incumbent within a context, under the same query cap and generated streams used by the fixed-split and Target-Scout selectors?

The task uses the existing `candidate_context_heterogeneity` generator, asymmetric false-negative/false-positive costs (5 and 1), its fixed candidate bank, uniform outcome queries at rate 0.40, and a pathwise cap of 40% of the target monitor. An observed binary outcome scores every frozen candidate action on that event. This is full-information paired evaluation after acquisition; it does not claim the label savings of AnyRank's active per-policy trial allocator.

Within each of two learner-visible contexts, the official AnyRank sequential graphical routine receives the queried-event reward vector for the incumbent and all non-incumbent candidate policies. The hypothesis family is the star of comparisons between each candidate and the incumbent. Rewards equal one minus the realized decision cost, including the existing switching cost amortized over the deployment horizon for a changed policy, divided by the largest possible event cost including that amortized switch charge. Thus every input lies in [0, 1]. Candidate models and context rules are fixed before the target monitor. Evaluator-only outcomes and oracle expected losses are used only after selection to score future utility.

The tested relation is the official routine's tie-aware ranking relation (`inference_mode="ranking"`) over its bounded reward distributions, with its published 11-point threshold grid. This is stronger than ordering policies by mean reward: a certified strict stochastic-dominance ordering implies a mean ordering for bounded rewards, while a mean-improving policy without that dominance may remain unresolved. This adaptation can therefore be conservative and is not a replacement for a mean-cost test. It is a reference-comparison adaptation, not AnyRank's full all-pairs ranking. If several challengers are certified above the incumbent, the procedure selects the one with the largest observed mean reward; the simultaneous tests support its improvement over the incumbent, but do not certify it as the globally best challenger.

The 0.05 familywise error budget is divided equally between the two contexts (0.025 each); within each context AnyRank starts with equal alpha over the candidate-versus-incumbent hypotheses and a fully connected, equal-weight recycling graph. Transitive closure is disabled. A challenger is eligible only when the returned pairwise relation establishes its strict superiority over the incumbent. If none qualifies, the context retains the incumbent. The global best policy is not identified by this star family.

The methods share generated features/outcomes, frozen candidates, query uniforms, costs, monitor window, hard label ceiling, and evaluator-only common holdout `[monitor_end, n)`. AnyRank processes the same queried prefix as the existing Target-Scout implementation. Comparisons are descriptive development results; the 3-seed pilot is not powered for superiority or null calibration. A separate large null-calibration protocol would be required before making an empirical FWER claim for this adaptation.

## Pilot run

Use CUDA for stream generation and the official CPU AnyRank sequential tests. Run three matched seeds in a zero-signal control and three in a positive-signal cell at prevalence 0.50 and proxy error 0.10, using fresh seed IDs 20310000–20310005. Compare AnyRank with pooled fixed-mixture certification, source-validation fixed-split certification, Target-Scout, and no intervention on those same streams. Stop after these six streams; do not expand the grid or tune from this pilot.

**Protocol adjustment before observing AnyRank outcomes:** a full all-pairs ranking of the 13-policy bank was timed and interrupted after more than five CPU minutes in its first context, with no result or efficacy metric observed. The study question is candidate promotion versus the incumbent, not a complete ordering of every candidate. The frozen pilot therefore uses AnyRank's official graphical procedure on the 12 prespecified candidate-versus-incumbent hypotheses per context. This narrows the tested claim to the actual intervention decision and substantially reduces irrelevant pairwise work. It remains an explicit adaptation; the full AnyRank policy-ranking result is not claimed.

Metrics are per-seed promotion and context-selection rates, total queried labels, evaluator-known expected and realized post-promotion net gain, harmful-promotion indicator, and pairwise ranking completion. Report every seed and the run manifest. AnyRank code and dependency versions/hashes are recorded. The source repository is MIT-licensed, but its `statistical-comparison-core` and `sequentialized-barnard-tests` dependencies are CC BY-NC 4.0; keep their code external and use this experiment for non-commercial academic research only.

## Known limitations

This pilot does not test serial dependence, adaptive or outcome-dependent querying, delayed feedback, policy-induced outcomes, or deployment shift after certification. The generator is IID and labels are queried independently of outcomes. Utility includes the project's declared synthetic cost and switching-cost convention; it is not observed revenue. The pilot does not establish external validity, novelty, or superiority. A non-selection is an inconclusive ranking result, not evidence of equal policies.
