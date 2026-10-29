# Exact restricted-master certificates: development results v1

2026-10-29. **Result:** exact arithmetic independently verifies two lower/upper
brackets for the original two-law risk-constrained problem. The T=7 bracket is
still too wide to establish a useful near-optimal method. These certificates do
not establish novelty, a speed advantage, or the requested synthetic/real-data
baseline win.

## Registered procedure

`CAUSAL_CUT_CERT_PROTOCOL_V1.md` was committed before the run. The generator
`scripts/research_risk_approx/generate_cut_certificate.py` reruns the registered
T=6/7 null-response cutting process; it saves the selected pure null strategies,
master duals, and the best root-repaired feasible behavioral policy. It reconstructs
first-promotion objective coefficients using exact fractions, including the exact
alternative-HMM continuation DP, then compares them with the numerical builder.
The discrepancy was below the registered 1e-10 threshold.

For a master with constraints `C x <= alpha`, flow `E x=e`, and nonnegative
realization x, let numerical dual proposals be rationalized as `lambda` for the
flow constraints and `mu<=0` for the cuts. Exact coefficient arithmetic gives

    L = e'lambda + alpha sum(mu_i)
        - sum_j max(0, (E'lambda+C'mu)_j - c_j).

Every learner realization x_j lies in [0,1]; subtracting each positive residual
therefore yields a valid lower bound even when the rationalized dual is not exactly
feasible. Each cut is verified to be a pure feasible null sequence-flow strategy,
so the restricted master is a relaxation of the original robust problem. The
upper witness is a saved recovered policy, mixed at the root with a no-promotion
policy; its causal-null risk is at most activation times its exactly evaluated raw
risk. This is a bound even if the null observes public actions that reveal the
mixture. Costs and activation are exact fractions.

The separate verifier `scripts/research_risk_approx/verify_cut_certificate.py`
rebuilds the reference game, objective and null-response cuts, checks every flow,
dual sign and residual using fractions, reconstructs the saved policy and
re-evaluates its cost and worst-case causal-null risk **without an optimizer**.
It shares coefficient-reconstruction helpers with the generator; it is an
independent certificate check, not an independent implementation of the HMM or
first-promotion model. Certificate checksums cover the complete signed payloads.

## Verified bounds

| Horizon | Cuts | Verified lower bound L | Verified feasible upper U | Rigorous U-L |
|---|---:|---:|---:|---:|
| 6 | 51 | greater than 2.881768749998 | 461083/160000 = 2.88176875 | < 2e-12 |
| 7 | 64 | greater than 3.341548199412 | 59747/17500 = 3.414114285714... | < 0.072566086303 |

The decimal lower values above are rounded downward, and the decimal gap bounds
are rounded upward. Exact rational values, behavior records and all null responses
are in `causal_cut_certificate_t6_v1.json` and `causal_cut_certificate_t7_v1.json`.
The verifier reports each root-repaired risk bound as 1/10. T=6's result is
consistent with the existing historical near-exact oracle certificate. At T=7,
the best saved safe policy is worse than the reference solver's numerical recovered
cost 10788127/3200000; the verified interval does not prove where the optimum lies
inside it. The 64-cut cap remains binding. Neither result certifies a general
algorithmic rate or computational improvement.

## Decision

The diagnostics close the specific gap in the earlier cut screen: its lower-bound
idea can be made mathematically checkable for these finite cells. However, the
current method still builds the full learner and null game, and T=7 remains far
from the exact reference at the registered stop. Its response generation and
certificate construction are established optimization techniques, not a new method.
Continue the research toward a stronger safe candidate and a genuinely cheaper
risk/optimization representation; do not claim that the user's requested
synthetic and real-data comparisons have been met.
