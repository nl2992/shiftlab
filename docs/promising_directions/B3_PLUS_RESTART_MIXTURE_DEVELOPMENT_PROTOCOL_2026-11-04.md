# Frozen development protocol: restart-mixture acquisition sentinel

**Registered:** 2026-11-04, before implementation and execution. **Status:** model-specific development screen only.

## Hypothesis

P7s's settled-state gate saves labels but can keep issue propensity at `.05` after a true reversal while its discounted mean still reflects the earlier good regime. An anytime likelihood-mixture warning may restore P3b-rate acquisition before that slow mean changes sign, while a calibrated false-wake probability limits extra stable-state spend.

## Fixed comparator and implementation contract

Compare four policies on common generated streams and common issue-time uniforms:

1. P7s, unchanged settled-state acquisition;
2. P7s-RM, settled-state acquisition with a restarted likelihood-mixture warning;
3. Cao-L, unchanged label-history control;
4. Cao-Hybrid, unchanged hybrid control.

All methods use the existing P3b paired evidence and promotion/rollback action code, `T=2000`, per-episode request cap `B=200` charged at issue, delay `d=50`, disagreement probability `.30`, query price `.05`, switching price `5`, and the existing three scenarios (stationary-positive, reversal at event 1000, benign covariate shift at event 900). P7s-RM changes only query acquisition. The restart-mixture trigger cannot promote or roll back directly.

## Frozen P7s-RM rule

Use the existing P7s settings, including `settled_floor=0`, `persist_gamma=.97`, and the same budget pacer. While the challenger is deployed and the existing recent signed mean declares the state settled, use an audit propensity `q_audit=.20` unless the reversal warning has crossed. On crossing, restore at least P3b's current budget-paced propensity (the maximum of that propensity and `.20`) through the rest of that deployment segment. Outside the settled state, follow P7s unchanged. Stop querying when the hard cap is exhausted.

For queried post-promotion disagreements, let `U_i=1` indicate a label favoring rollback. Under the model used for this registered synthetic screen only, `U_i` is IID Bernoulli(.30) while the challenger remains beneficial and Bernoulli(.70) after reversal. Use the likelihood ratio for `.70` against `.30`. Let `B=200` be the number of candidate queried-label onset indices. Maintain a uniform mixture over all `B` possible onset positions, assigning factor one to components before their start and multiplying by the likelihood ratio from their start onward. The mixture resets on each deployment switch and uses only labels already released; fixed delay preserves release order. Restore the active query rate the first time the mixture wealth reaches `1/eta=20`, where `eta=.05`. The existing paired e-process remains the sole deployment gate.

Under the no-reversal IID `.30` model, this mixture is a nonnegative martingale, so the chance of a false acquisition wake is at most `.05` per deployment segment by Ville's inequality. This is a model-specific acquisition-cost statement only. It is not the certificate for an action and it is not valid under the repository's broader conditional-mean null without additional assumptions.

## Seed split and primary readout

Use 200 seeds per scenario starting at `21261108`, disjoint from all earlier B3+ Cao development outputs at seed base `20261108`. No parameter tuning is permitted on this block. Primary outputs are paired net cost and rollback delay/probability in the reversal scenario. Also report stable and benign-shift net cost, query counts by half, false wake frequency, and cap violations. Bootstrap intervals are descriptive development uncertainty, not a formal stochastic guarantee.

Continue to a new theory/prior-art gate only if P7s-RM's paired reversal cost is lower than both Cao controls and its rollback probability is no worse than the better Cao control, while stable-positive cost is below P3b and no scenario has a cap violation. Otherwise close this candidate. Passing this small screen would justify at most another registered development step; it would not establish SOTA or novelty.

## Prior-art caveat

Restart mixtures, sequential change detection, and controlled sensing are established. The nearest sources are Cao (2026), *The First-Order Value of Free Covariates in Budgeted Risk Monitoring*, and Veeravalli, Fellouris & Moustakides (2024), *Quickest Change Detection With Controlled Sensing*. This pilot tests whether the specific restart-mixture signal improves the paired-utility/hard-cap/delayed-reversible contract. It cannot support a broad new-method claim by itself.

## Post-run implementation note (not part of the pre-run rule)

The development runner did not latch `q>=.20` through the full deployment segment. It applies the warning-driven minimum while the signed-mean state remains settled; when that state is no longer settled, it follows P7s's existing budget-paced acquisition rule. The findings report treats this as an implementation-specification deviation and evaluates only the coded controller. A latched variant is a different candidate and must use a fresh protocol and seed block.
