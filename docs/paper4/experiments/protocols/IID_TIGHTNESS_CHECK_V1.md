# IID-tightness check: is the IID-relaxed optimum's safety explained by monotonicity?

**Registered:** 2026-11-10, before any code for this check. Development only; synthetic cells
already exposed in `FCG_DEV_PROTOCOL_V1.md` and `FCG_SCALE_PROTOCOL_V2.md`. No new cells.

## Question

In every T=10 cell (S1, S2, S3) and in the persistent cells C1, C4, C5, the IID-relaxed LP optimum `x_IID`
(FCG iteration 0) has exact causal risk equal to its IID risk (1/10). The repository theorem
`docs/switching_monotone_promotion_reduction_v1.md` gives `R_causal = R_IID` for any upfront mixture supported on
pure plans with coordinatewise-increasing promotion events. Does that theorem explain the observed tightness?

## Measurements per cell (C1–C6, S1–S3)

1. Solve the IID LP, as in FCG-fast iteration 0, to obtain `x_IID`. Recompute the exact `R_causal` and `R_IID` of the
   recovered behavioural policy.
2. Count the randomised information sets: behavioural probabilities outside `{0, 1}`, with tolerance `1e-9`.
3. Compute the average promotion function `G(y) = sum of x_sigma` over first-promotion sequences reached on the
   potential tape `y`, for all `2^T` tapes. This is the decomposed learner tree only, following tape bits at
   queried events.
4. Test monotonicity of `G`. Record the maximum cover violation `max (G(y) - G(y + e_t))` over all `y` with
   `y_t = 0`, and the number of violating covers.
5. **Sufficient test.** If there are at most 12 randomised information sets, enumerate the pure plans of the
   product (Kuhn) decomposition with positive weight and test each plan's promotion event for
   monotonicity. Otherwise record "not enumerated".

## Interpretation (locked)

| Observation in an IID-safe cell | Conclusion |
|---|---|
| Every pure plan in the product decomposition is monotone | **EXPLAINED** by the existing theorem. Nothing new |
| `G` is not monotone (violation > 1e-9) | **NOT EXPLAINED** by the existing theorem. This is a candidate new phenomenon and a theorem target |
| `G` is monotone, but some product-decomposition plan is non-monotone, or the decomposition was not enumerated | **UNRESOLVED**. Another decomposition might be monotone |

The anti-persistent cells C2, C3 and C6 are IID-unsafe, so they are the contrast group. There the
expectation is non-monotone `G` or non-monotone plans. If instead they show monotone `G` *and* monotone
plans, the checker contradicts the theorem and must be debugged before any conclusion.
