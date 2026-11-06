# Bounded method specification for a possible follow-up

## Status

Not implemented, not evaluated, and not a novelty claim. This specification records the smallest candidate implied by the rollback evidence, so a later experiment cannot be described vaguely or tuned after seeing its outcome.

## Rule under test

At initial promotion, reserve a prespecified number of the pathwise label budget for post-promotion rollback evidence. On each released queried label, update a mirrored one-sided sequential process for whether the fallback model is better than the incumbent on the queried population. A rollback can occur only if (a) the prespecified evidence threshold is crossed and (b) a predictable cost-to-go estimate says the expected remaining predictive-loss reduction exceeds query and switching costs. Re-promotion/rollback cycles spend a prespecified alpha sequence (e.g. alpha_j=alpha_rb/2^j). The reserve is enforced when queries are issued, not retroactively.

## Information and assumptions

The policy may read past and current predictions, released queried labels, pending feedback metadata, remaining label budget, current deployment and elapsed horizon. It may not read unreleased labels, future outcomes, evaluator regime labels or labels of unqueried events. For any conditional error statement, state the exact filtration and require the per-release null condition, predictable query probability, bounded loss increment, and a release-time process compatible with the test. Informative or outcome-dependent release delays need an explicit model. The cost-to-go estimate itself does not inherit a sequential guarantee merely because its evidence process does.

## Frozen comparison needed

Use E_rb as-is, E_rb with matched rollback alpha, proposed gate, two-sided SR/CUSUM, and no rollback. Equalize horizon, start grid where applicable, pathwise query budget, label costs, switch costs, feedback releases, policy-visible information and initial model. Primary estimand is paired net deployment cost; report predictive loss, label expenditure, switch expenditure, promotion/rollback timing and correctly specified null error separately.

## Rejection conditions

Reject the modification if matched alpha or two-sided SR/CUSUM explains its benefit; if it exceeds its null error criterion; if the reserve is not respected pathwise; or if a practical advantage disappears after all costs. A pass on one synthetic reversal regime alone would still not establish novelty, fresh synthetic robustness, or real-data confirmation.
