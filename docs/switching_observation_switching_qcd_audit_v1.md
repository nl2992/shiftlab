# Observation-switching costs in quickest change detection: prior-art audit

**Date:** 2026-10-28. **Status:** source-level scope audit; no novelty claim.

## Primary-source scope

Lau and Tay, “Asymptotically Optimal Sampling Policy for Quickest Change Detection with
Observation-Switching Cost,” IEEE Transactions on Signal Processing 69 (2021), 1332–1346;
arXiv:1912.11693v4. The cached primary PDF is recorded with byte count and SHA256 in
`switching_source_manifest_v18.json`.

Inspected the formal model and criteria in Section II, the GLR-CuSum definition, Lemma 2,
Proposition 1 and Theorem 1, the open-loop design reductions in Sections V-A and V-B, and the
two-stage observation-dependent design in Section VI. The authors assume an i.i.d. pre-change
law and one i.i.d. post-change law from an unknown deterministic onset, known conditional models
under each sampling action, and a permanent change. They jointly choose a sampling policy and
stopping rule to minimize Lorden worst-case average detection delay subject to an average
run-length-to-false-alarm constraint and an average observation-switching-cost constraint.

For an open-loop finite-window policy with support in one recurrence class, the GLR-CuSum has
asymptotic WADD approximately `log(gamma)/I`, with information rate equal to the stationary
average conditional KL divergence. Theorem 1 establishes existence of an asymptotically optimal
open-loop sampling policy. Propositions 3 and 5 reduce the sufficient window size to zero for
equal sampling switch costs and one for unequal costs. Section VI also provides an
observation-dependent two-stage policy and proves its asymptotic false-alarm and switching-cost
constraints. The objective and guarantees are asymptotic as the ARL threshold tends to infinity.

## Consequence for our novelty screen

The broad claim that a method newly couples adaptive acquisition and sequential change detection
under sampling costs is occupied. The paper even handles observation-dependent sampling after
evidence arrives, so adding an evidence-triggered query burst is not enough by itself.

The theorem does not directly reduce to the ShiftLab contract. It uses immediate observations,
an infinite-horizon permanent single change, known pre/post likelihood models, an average
run-length false-alarm criterion, and average switching costs for the *sampling mode*. It has no
pathwise finite total-label cap, fixed release delay, repeated reversible deployment decisions,
policy-switch economics, or robust conditional-null anytime promotion event. These are exact
comparison obligations, not evidence of novelty. The remaining G1 target must be a proved finite-
sample economic performance or approximation result for recurrent reversible switching under
the ShiftLab risk and budget contract, relative to scalable sequential-design compositions and
the exact finite causal oracle.

The source does not resolve whether such a narrower result is new. Do not cite the model
mismatches alone as the contribution. No algorithm or experiment follows from this audit.
