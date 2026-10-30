# Source-level update: algorithms, assumptions and exact residuals

2026-10-30. Primary sources inspected during this turn; this is not a claim of exhaustive completed reproduction.

## Supervised PR

[Primary full text, Appendix E](https://arxiv.org/html/2110.06177v4) specifies PM-EB endpoints, predictable lambda, variance estimate and cap .5. The new `pr_empirical_bernstein` implements those formulas on uniformly queried bounded cost losses. Source reference risk is shared with candidates; simulated estimated cases use an independent Hoeffding source bound. Delayed publication/hard stopping are wrappers. A fixed conditional cost-null gives the needed negative drift; a weighted predictable bound must not silently be described as the identical running-average null for arbitrary nonstationarity. Full original experiment reproduction remains open.

## Published PPRM

[Primary full text, sections 3.1–3.3](https://arxiv.org/html/2602.02229v1) defines nonempty labelled batches, separate unlabelled batches, a prediction-powered risk estimate, affine normalization, a mixture empirical-Bernstein boundary and predictable eta fitted on historical labelled/unlabelled data. The older local `pprm` betting engine is not that algorithm.

New implementation follows equations 19/22/27 for a declared batch size 5, one uniformly selected labelled point, hard synthetic labels, eta clipped to [0,1], window 32 and a 32-point geometric discrete lambda mixing distribution. A distribution with atoms makes the integral a finite sum; this is an explicit choice, not reproduction of an unspecified numerical implementation. Its eta variance uses individual historical unlabelled values, not the variance of batch means. Exact finite-population testing verifies unbiasedness of the batch estimate. Delayed publication is batch-end-plus-delay. Query costs are charged when each request is issued.

Full original experiments, author code, and the paper's source-side PPI betting bound have not been reproduced. Source calibration is deliberately shared externally for matched tests. Do not call this complete VERIFIED_REPRODUCTION or infer a general published-method win from this different batch contract.

## Active RCPS

[Primary full text Appendix A](https://arxiv.org/html/2406.10490v2) and author commit `a67f85d603df2bb3e32ef007f445191923ebd990` give the fixed-target increment/bet and learned conditional-variance-based label policy with a dual budget update. Only the fixed-target FTL complement-risk component has author-code parity. The full learned variance/query policy is still required; simple uncertainty allocation is not a substitute. Expected label budget differs from hard pathwise budget.

## Compact controllers and robust FSC prior art

[Primary publisher PDF](https://cdn.aaai.org/ojs/17401/17401-13-20895-1-2-20210518.pdf) and [author repository](https://github.com/LAVA-LAB/ipomdp_cvx), cloned at `0cc828d25a2a66597947135f53ded27ef92827bf`, are accessible now. Paper sections “Finite memory”, “Assumptions” and the verification step explicitly use memory-product models and robust verification. Thus fixed-controller product-state evaluation alone is known machinery; a tree-versus-product timing win does not settle novelty.

Do not declare exact identity of the full synthesis formulations: the paper treats interval-model instantiations with graph-preserving assumptions, while ShiftLab's unrestricted causal null can choose endpoint zero after seeing pending outcomes and optimizes alternative cost under a separate law. Once a public deterministic controller is fixed, J's full visible product state makes that null response an ordinary finite-horizon adversarial reachability computation. A residual claim needs a new synthesis/value-gap theorem or irreducible computational result, not merely the extra application variables. Current G1 remains unresolved; no controller-synthesis efficacy is claimed.

Author code imports Storm/Gurobi; dependencies and model mapping need a bounded portability audit. Retrieval success is not execution success. Other baseline families in BASELINE_COVERAGE.md remain incomplete.
