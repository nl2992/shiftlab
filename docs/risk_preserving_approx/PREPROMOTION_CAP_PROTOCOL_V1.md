# Pre-promotion acquisition cap: structural screen protocol v1

Registered 2026-10-29 at starting revision `9eabe0b` before implementation or
execution. This is a deterministic approximation-class diagnostic, not a
confirmatory experiment or a novelty claim.

## Definition and mathematical target

Let the original total query budget be B. Define a restricted class in which at
most m<=B queries may be requested before or on the first-promotion event; if
there is no promotion, this cap holds through the horizon. After promotion, the
controller may use any remaining rights up to the original total pathwise cap B,
including rollback and re-promotion. The pre-promotion cap must not use unreleased
labels or change the original causal-null opponent's information. Let V_m denote
its risk-constrained optimum. V* <= V_m and the classes are nested in m; V_B=V*.

For any full-policy pi, couple a modified policy to pi until it would request
its (m+1)th pre-promotion label (including a request at the promotion event).
At that instant stay on the incumbent, stop requesting, and never promote. If
promotion occurs earlier, continue following pi under the full remaining budget.
The modified policy is feasible for the restricted class, never adds promotion
under any causal null, and preserves the hard pathwise cap. Under bounded
nonnegative decision/query/switch costs, its incremental alternative cost on the
truncation event is at most T, because its future incumbent-only loss is at most
T and the original future cost is nonnegative. Therefore for a full optimum pi*
(or an approximating sequence):

    0 <= V_m - V* <= T P_alt_pi*(a (m+1)th request at or before first promotion).

This is a conditional a-priori bound, not a computable practical rate: the event
probability under pi* is unknown without further structural analysis. A checked
lower certificate L for V* and an independently verified safe restricted policy
with cost U instead give an a-posteriori gap U-L. Both formulations compare
against the original unrestricted oracle; this fixed split is a standard restricted
policy class, not a new method claim. Existing first-promotion decomposition and
budget-split prior work must be included in any eventual novelty comparison.

## Frozen screen

Use the registered exact HMM family: transition rates 1/4, emissions 1/20 and
19/20, prior 1/2; B=3, d=1, alpha=1/10, query fee 1/100 and switch fee 1/10.
Run T in {5,6,7,8} and m in {0,1,2,3}. Compare to the unmodified full-budget
first-promotion oracle with the same parameters and 200,000 builder-node and
60-second LP limits. Fix all cells before execution; do not selectively rerun or
retune. Record all failures, LP objectives, raw and root-repaired exact-rational
policy cost/risk, maximum allowed pre- and total requests, learner/null sequence
counts, builder nodes, continuation-cache size, build/solve wall time and source
hashes. A single run per cell is exploratory; no runtime or memory advantage is
claimed from it alone. A later repeated fresh-process protocol with a verified
worker-memory sampler is required for such a claim.

Check each recovered policy's exact full causal-null risk; if it is above alpha
from numerical recovery, use the explicit root-safe activation with the
never-promote policy and report both. Check feasibility, chronological semantics
and post-promotion full-budget availability in targeted tests. Costs should be
nonincreasing in m up to numerical tolerance, and m=B should match the reference
within 1e-7; differences are recovered-policy comparisons, not exact optimality
certificates. Compare T=6 and T=7 safe costs with independently reverified
`causal_cut_certificate_t6_v1.json` and `_t7_v1.json` lower bounds. Do not infer a
T=8 full-oracle certificate from reduced-only completion.

Store results in new `prepromotion_cap_screen_v1.json` with unique file creation,
registered code/protocol hashes and all cells including failures. No new seeds,
real-data rows, reserved holdouts or historical result files are touched.
