# Controller quality-gap diagnosis and repair

2026-10-30. Previous turn: progress (matched sequence-form comparison committed). This continuation diagnoses the exposed reference policy, registers an added-class ablation and executes exact feasibility/cost checks. Goal remains active; no novelty or independent confirmation claim.

## Mechanism extracted from the reference

At5 events/budget4/delay1, the rationally recovered sequence-form policy activates an evaluation branch with probability2/5, otherwise stays at incumbent. On the evaluation branch it queries until either the first zero arrives (abandon) or3 successive ones arrive (promote). After abandonment it never resumes querying. This policy uses no action reversal on reachable histories; internal post-label randomization is not needed beyond the root choice. That is more specific than attributing the previous gap generically to a larger policy class.

The original streak family resets its positive streak after a zero and can keep querying. It can spend label fees on paths where promotion is no longer economical. The first result motivating this repair was already exposed; this study is explicitly development.

## Registered ablation

Retain original32 controllers. Add30 abort-on-first-zero controllers and30 cumulative-positive-count controllers with the same starts{1,2,3}, strides{1,2}, thresholds1..5.92 total declared policies, optimized with the same exact2-policy root-mixture enumeration and sufficient risk constraint. Null is full-history adaptive positive probability<=1/2; alternative IID4/5; alpha1/20; query1/100; switch1/10. Same four horizons/budgets/delays, same clocks as the preceding comparison.

For each selected component in each ablation, independently embed its finite memory in the full-history game. Exact expected metrics and exact causal-null risk match the compact recursion. Historical streak-only values reproduce exactly. No fresh sequence-form solve is mislabeled as independent evidence: the verified comparator-policy costs are read from the original result, whose hash is frozen.

| Cell H/B/d | Original class cost | With abandonment | With cumulative count only | Verified reference policy |
|---|---:|---:|---:|---:|
|4/3/1 |617/200 |7657/2500 |617/200 |7657/2500 |
|4/3/2 |617/200 |617/200 |617/200 |617/200 |
|5/4/1 |180256/46875 |23653/6250 |180256/46875 |23653/6250 |
|5/4/2 |771/200 |771/200 |771/200 |771/200 |

Abandonment closes both previously nonzero gaps; cumulative counting does not. At4/3/1 mix never-deploy weight4/5 with threshold2 abandonment weight1/5. At5/4/1 mix never-deploy weight3/5 with threshold3 abandonment weight2/5. Both exactly reach risk upper1/20. For threshold3/delay1, component null risk is exactly1/8; expected query count under the alternative is1+p+p². The analytical cost5p+.01(1+p+p²)+p³(.1−2(2p−1)) agrees with the independent recursion at p=.8. A zero permanently disables querying even if a previously pending positive arrives; sunk query charges are retained.

## What this establishes and does not

The1.6114% failure of the original class was attributable to an omitted standard evaluation-stopping option in these exposed cells. This strengthens the baseline and closes that particular implementation deficiency. It does **not** overturn the historical failure of the original class, prove unrestricted global optimality, or establish a new acquisition mechanism. Exact matching to a verified feasible reference policy is not a certified lower bound on all feasible policies. No large-instance scalability or new matched-quality speedup is measured in this repair.

Early abandonment, root mixing, finite-controller search and delayed label accounting are established techniques. A paper cannot claim novelty from adding this option after inspecting the optimal trace. A future quality study must freeze this enriched class before new overlap cells, derive a valid unrestricted lower certificate, and charge construction/search/runtime at matched tolerance. Alternative regimes can make zero-after-positive behavior informative differently; no universal abandonment rule is asserted.

## Verification and provenance

17 relevant tests pass, including new absorbing-abandonment/promotion checks and exact analytical cost/risk, plus prior independent LP and sequence-form checks. All selected policies in the4×4 ablation table pass exact full-history cost/risk embedding. Ruff0.17.1 check/format passes. Registration/source/comparator hashes precede the repair run. Source snapshots preserve code used. All jobs terminal; no reserved real data or external jobs used.

Artifacts: controller_abandonment_registration.json and controller_abandonment_results.json; script test_controller_abandonment.py is an experiment runner, while tests/test_controller_abandonment.py contains unit checks. Runner refuses overwrite. These92 policies are not added to the monitor combination count. Next substantive work remains prospectively matched quality validation and robust-FSC/two-law source mapping, alongside a new mechanism beyond already tested known ingredients. Exhaustive objective remains incomplete.
