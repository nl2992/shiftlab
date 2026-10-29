# Belief compression with exact causal-null risk: candidate screen

**Date:** 2026-10-28. **Status:** source-level screen and theorem boundary; no algorithm claim.

## Candidate

For a known two-state alternative HMM, replace unrestricted alternative-history dependence by a
grid over its posterior belief, while carrying time, incumbent action, remaining query rights,
pending labels, and explicit finite-controller memory. Optimize the controller's expected cost on
the HMM and verify its promotion probability exactly against the full-history causal conditional
null. The desired theorem would bound the cost gap to the unrestricted alpha-safe policy while
preserving the same alpha and pathwise budget.

This is a possible route to a scalable policy, not a selected method. The deployment forecast
under the alternative and the causal-null safety game remain distinct kernels. A belief grid for
the first must not silently average or approximate the second.

## Primary-source boundary

- Lovejoy, [*Computationally Feasible Bounds for Partially Observed Markov Decision Processes*](https://doi.org/10.1287/opre.39.1.162), *Operations Research* 39(1), 1991, develops finite belief grids and upper/lower value bounds for approximate POMDP policies. That occupies generic belief discretization and value-loss bounds.
- Osogami, [*Robust Partially Observable Markov Decision Process*](https://proceedings.mlr.press/v37/osogami15.html), ICML 2015, gives robust belief updates/value iteration under convex uncertainty sets. Robust belief planning is established.
- Cubuktepe et al., [*Robust Finite-State Controllers for Uncertain POMDPs*](https://ojs.aaai.org/index.php/AAAI/article/view/17401), AAAI 2021, optimize finite-memory policies for robust reachability/reward and provide a separate exact verification step. Their controller optimization is local, and their model is a single uncertain POMDP.
- Khonji et al., [*Approximability of Constant-horizon Constrained POMDP*](https://ijcai.org/proceedings/2019/775), give an FPTAS for a fixed stochastic kernel at constant horizon. This does not give a polynomial-in-horizon approximation for our robust causal-null opponent family.

The audited statements close “belief grid + finite controller + risk verification” as a generic
combination. They do not directly establish the desired two-kernel approximation theorem: reward
is evaluated under a known recurrent HMM, while promotion risk is maximized over a causal
history-adaptive null with delayed visibility. This mismatch is an open comparison obligation,
not evidence of novelty.

## The theorem obstacle

For a fixed finite controller, the causal-null promotion risk can be evaluated exactly on the
product of controller memory, time, action, remaining budget and pending queue; see
`switching_fsc_risk_compression_v1.md`. This protects risk for that controller but does not
compare its value with the unrestricted policy.

For the alternative HMM, belief-grid POMDP bounds can approximate reward when the policy is
represented on the approximate belief state. In the switching problem, an unrestricted optimal
policy can also use history to allocate its single global type-I risk allowance. Merging histories
with similar HMM beliefs may therefore change which promotions are feasible under the causal null.
Keeping the full risk-relevant controller memory avoids that error but may retain exponential
history size. The existing monotone-event reduction is insufficient: a registered exact
counterexample shows that monotone promotion can have zero economic value when signed reversal
evidence matters.

The exact aliasing construction in
`switching_alt_belief_risk_alias_counterexample_v1.md` makes this failure quantitative. Two
alternative histories map to the same current HMM belief, but a full-history safe policy obtains
net value `128/125`, while any current-belief-only policy is bounded by `14/25` at the same
`alpha=1/10` and fixed query calendar. The gap is caused by allocating false-promotion risk
across histories that the alternative belief merges. Storing the first label repairs this
two-event example, so it is a
counterexample to posterior-only compression, not to every finite-memory approximation.

Thus the missing result is not an ordinary POMDP belief-grid bound. It must control the loss from
compressing alternative beliefs **and** show how the compressed controller preserves or
conservatively approximates the global causal-null risk for the full nonmonotone policy class.
No such bound has been derived. A bound only against the best policy in the same quantized class,
or a finite-state risk verifier without a full-oracle value guarantee, fails G2.

## Gate decision

Do not implement posterior-only compression as the proposed algorithm or run an efficacy grid.
Continue G1/G2 only if a concrete projection theorem can be stated with (i) exact event-time and release semantics,
(ii) pathwise budget including pending requests, (iii) risk at most `alpha` under the original
causal null, (iv) an explicit utility gap to the full-history robust sequence-form oracle, and
(v) runtime/memory scaling that improves on that oracle. Test the theorem on the certified
`T=6, B=3, d=1` oracle bracket before moving to a wider synthetic family. If the bound inherits
the generic history explosion or applies only to a restricted certificate engine, reject this
candidate and revise the hypothesis rather than present compression as novelty.

## Follow-up decision: reject one-bit generalization from the current cells

The exact alias construction is repaired by storing the first label, and the registered six-round
feasible oracle controller also has a compact description. These facts do not support a general
small-memory approximation claim. In the six-round controller, promotion evidence and post-switch
rollback evidence are distinct state variables: the former governs whether to install the model,
while the latter reacts to subsequent outcomes and regime reversal. The full-history oracle bracket
certifies the optimum on that one finite instance, but its compact feasible controller was distilled
post hoc from that same instance. Neither result compares an independently designed memory-limited
optimizer with the full oracle across growing horizons or budgets.

The candidate therefore fails its next G2 step as currently formulated. Do not extend the one-bit
example into a memory-scaling theorem or run a broad efficacy grid. A viable resubmission must give
an explicit family of instances, a proved lower or upper bound on risk-relevant memory, and a
policy-construction theorem preserving the original causal-null risk while bounding economic value
loss against the unrestricted oracle. It must also compare that result with existing robust FSC and
constrained-POMDP methods. Keep evidence for current-regime benefit separate from safety memory:
the causal-null likelihood-ratio gate controls false promotion under the stated null, but historical
promotion evidence cannot certify continued benefit after a reversal; rollback needs its own current
regime evidence and contract.

Recheck on 2026-10-28: the exact posterior-alias checker, the independent rational LP-certificate
verifier, and the delayed-FSC risk-recursion checker all pass. This confirms the narrow cell results,
not the missing approximation theorem. G1/G2 remain open and G3/G4 remain gated.
