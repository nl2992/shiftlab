# Focused novelty review: arbitrary fixed-budget theorem M11

**Date:** 2026-11-13. **Recommendation: PROCEED. Novelty score: 6/10.** No exact prior statement was identified. M11 clears this early novelty screen; this is not a publication-readiness or correctness verdict.

**Inputs:** `B_GENERAL_FIXED_PREMIUM_PROOF.md`, M11 in `MIXING_PREMIUM_THEOREM.md`, the original game definitions, and the primary sources below. The existing mathematical audit is recorded separately. **Assurance:** a separate reviewer was started with no inherited conversation (`fork_turns=none`), requested `gpt-6-astra`, effort `xhigh`. Its initial call hit a provider usage limit; after resumption it completed the review and returned PROCEED, 6/10. Actual model identity was not exposed by the tool, so acceptance remains provisional. Trace: `.aris/traces/novelty-check/2026-11-13_run01/`.

## Proposed contribution and core claims

For every finite query budget `B>=1`, the stationary symmetric anti-persistent HMM admits an explicit open parameter region in which replacing fair-IID-null promotion control by control against all admissible conditional nulls removes a strictly positive fraction of the optimized value of information, uniformly over all `T>=3B`. The learner can choose query times adaptively, randomize privately, and continue querying and changing actions after first promotion.

1. **Strict separation after optimizing both learner problems.** Constraint nesting gives only `Gamma>=0`. M11 supplies a positive lower bound for the optimized difference. The nearest general frameworks are minimax sequential testing and null-mixture duality; neither source below supplies this decision-value separation.
2. **Every finite budget, with explicit uniformity in horizon.** M11 proves `forall B exists r_0(B)>0 forall r in (0,r_0(B)) forall T>=3B`, with `rho_Gamma>=3/[8(B+2)]`. The same positive `r` stays fixed while `T` grows. This is a substantive extension beyond enumerated small-budget cases or continuity at a fixed horizon.
3. **A simultaneous, explicitly bounded budget range.** On `0<r<1/1056`, every `B<=Bbar(r):=floor((1056r)^(-1/4))` and `T>=3Bbar(r)` has `rho_Gamma>=3/[8(Bbar(r)+2)]`. This quantitatively recasts the local theorem; it is not a common positive bound over unbounded budgets on a fixed rectangle.
4. **A concrete certificate controlling adaptive continuations.** The combination of the query-ordinal null mixture with the uniform HMM continuation envelope is the proof-specific step. Mixtures, Bellman bounds, HMM filtering, and budgeted value of information are established tools and should be credited as such.

## Closest primary sources and exact differences

| Source and inspected scope | Overlap | Difference from M11 |
|---|---|---|
| Fauß et al., [Minimax Optimal Sequential Hypothesis Tests for Markov Processes](https://arxiv.org/html/1811.04286v2), 2020 version; formulation and §§2.5, 7.1 | Conditional-law uncertainty, least-favorable distributions, and minimax sequential design. | Its objectives concern run length and testing errors. It does not give a hard-query-budget lower bound comparing two optimized cumulative decision-value problems. |
| Koolen & Grünwald, [Log-optimal anytime-valid E-values](https://ir.cwi.nl/pub/33120/33120.pdf), 2022; Theorem 5 and surrounding discussion | Primal–dual representation by mixtures of stopped null distributions. | The objective is expected log evidence. M11's particular mixture must bound history-dependent decision value and remaining queries after first promotion. The mixture-duality principle itself is not new. |
| Ramdas, Ruf, Larsson & Koolen, [Testing exchangeability: Fork-convexity, supermartingales and e-processes](https://doi.org/10.1016/j.ijar.2021.06.017), 2022; null geometry and power separation | Stronger sequential null requirements can destroy testing power, including against Markovian alternatives. | This rules out a broad claim that the existence of a robustness/power tradeoff is new. It does not quantify M11's optimized finite-budget HMM decision-value gap. The current causal null is not the fork-convex hull of the singleton fair-IID null. |
| Modak et al., [Sequential Adversarial Hypothesis Testing](https://arxiv.org/html/2511.10181v1), 2025; problem, Theorems 1–3 | History-adaptive adversaries choose single-letter laws under both hypotheses; asymptotic error-exponent regions. | Both hypotheses are worst-case convex sets. M11 has one fixed dependent HMM alternative and measures decision value at fixed budget. It is not an immediate specialization of their exponent theorem. |
| Clerico et al., [Time-sensitive anytime-valid testing](https://arxiv.org/html/2605.06521v1), 2026; objective, Bellman representation, §9 | Rewards assigned to rejection times and optimal sequential control. | M11's payoff also depends on history and decisions after promotion, with a remaining label budget. Their general composite-null projection question remains open; M11 supplies a model-specific certificate rather than solving that general question. |
| Corenflos, [An iterated-logarithm price of anytime validity for log-optimal e-processes](https://arxiv.org/html/2611.11874v1), November 2026; regret definition, dual lower bound, main result | Explicit horizon-dependent validity premium and null-mixture lower bounds. | It compares one e-process with fixed-horizon log-optimal e-variables in a Gaussian setting. M11 changes the null family while both sides already constrain ever-promotion risk, and measures cumulative decision value. |
| Sethi et al., [Asymptotically Optimal Sequential Testing with Markovian Data](https://proceedings.mlr.press/v306/sethi26a.html), ICML 2026; publication abstract | Markov dependence, non-asymptotic stopping-time bounds, and asymptotic optimality. | Observed-chain transition testing differs from hidden-state utility under selectively queried delayed labels; no corresponding premium result appears in the stated contributions. |
| Krause & Guestrin, [Optimal Value of Information in Graphical Models](https://arxiv.org/pdf/1401.3474), JAIR 2009; formulation and adaptive-plan budget constraints | Budgeted adaptive observation plans, filtering, and decision-theoretic VOI in graphical models. | There is no conditional-null promotion constraint or comparison with an IID-constrained optimum. Budgeted HMM information acquisition itself is established. |
| Udupa & Fu, [Information-Driven Active Perception for k-step Predictive Safety Monitoring](https://arxiv.org/html/2603.23450v1), March 2026; formulation and objective | HMM monitoring with sensor-query budgets. | Its target is conditional entropy of future safety. It does not quantify the decision-value cost of strengthening null validity. |

The review also screened Taga et al.'s [ICML 2026 horizon-aware betting](https://proceedings.mlr.press/v306/taga26a.html), recent robust sequential-testing preprints, and robust-POMDP work. No exact M11 statement was found. Searches included arXiv and ICML/NeurIPS/ICLR proceedings, with explicit 2025–2026 and recent-six-month queries. Search absence is not proof of absence; this was a focused review rather than exhaustive citation-graph coverage.

## What the budget dependence does and does not establish

The theorem's quantifiers are nontrivial: every chosen finite budget has a nonempty region and a positive lower bound for arbitrarily long horizons. The corollary also supplies one bound simultaneously over a range of budgets at a fixed `r`.

The region is very small. These are values of the proved sufficient bounds, not experiments:

| B | Admissible upper radius r_0(B) | Relative-premium lower bound |
|---:|---:|---:|
| 3 | `1/13840` (about `7.23e-5`) | `3/40 = 0.075` |
| 6 | `1/168448` (about `5.94e-6`) | `3/64 = 0.046875` |
| 10 | `1/1158144` (about `8.63e-7`) | `1/32 = 0.03125` |

Here `r` is the magnitude of negative one-step hidden-state correlation. Thus the extension operates near independence, with `r_0(B)` of order `B^-4`. The proved relative bound is of order `B^-1`; neither exponent is shown sharp. As `r` tends to zero at fixed `B`, the proof's IID upper bound implies that available absolute decision value tends to zero. A positive fraction of that value is meaningful mathematically, but it does not imply a large total-loss or per-round effect. Along a growing-budget sequence, a lower bound that tends to zero does not prove that the actual premium tends to zero.

M11 complements the stronger B<=6 constants on the larger M10 rectangle. It does not replace them. It fixes `alpha=0.1`, `d=1`, and zero query and switching costs; its open set is in `r,g`, not the full parameter space. The theorem establishes sufficient persistence conditions, not a sharp label-scarcity threshold or a characterization of all mixing chains.

## Positioning and recommendation

**Recommended verifiable claim:** “For every finite observation budget, an explicit weakly anti-persistent hidden-Markov family exhibits a positive decision-value cost of conditional-null robustness uniformly over all sufficiently long horizons, even under adaptive query timing and unrestricted post-promotion continuation.”

The mixture used in the proof chooses a query position to force to zero. It does not need to react to previously observed label values. Therefore the theorem establishes the cost of requiring validity for the causal-null family; it does not isolate the added value of outcome-adaptive adversary reactions. Both optimization problems already control the probability of ever promoting, so “price of anytime validity” is an inaccurate description of this comparison. “Causal” here refers to information/timing restrictions, not identification of causal effects.

**PROCEED, 6/10.** The new result is an explicit local separation theorem across arbitrary finite budgets. No named source was found to contain it. Its remaining publication challenge is scientific significance beyond a local constructed family; the narrow region, vanishing absolute opportunity near independence, and fixed costs/delay/risk level should be stated plainly. This review does not change `SALVAGE_PLAN.md` or the publication decision.
