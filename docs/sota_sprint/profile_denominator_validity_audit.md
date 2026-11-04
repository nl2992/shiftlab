# Profile-denominator prototype: validity audit and disposition

**Date:** 2026-11-04. **Status:** numerical-certification obligation identified; candidate quarantined. This is a code-reading audit, not a demonstrated numerical counterexample. It does not alter the registered A5b results or claim a new method.

## Finding

`A5b-profile-first` must not be treated as an independently validated monitor in its current implementation. The intended construction replaces a factorwise composite-null likelihood upper bound for the first started component with a tighter prefix profile bound plus suffix factorwise bounds. The code's mathematical decomposition appears consistent for that first component: it starts at query 1; checkpoints profile the entire observed prefix; and `profile_partial` accumulates the suffix since the last checkpoint. Later starts continue to use the original factorwise bound. I found no reset mismatch in this path.

The unresolved obligation is finite-precision certification:

1. `profile_null_upper` obtains lower bounds on the supremum with floating-point scalar optimization and computes upper bounds using floating-point endpoint powers, log sums, bisection, tangents, and a fixed `1e-10 * n` allowance. I found no proof that this allowance dominates all floating-point error. The source's exact-arithmetic relaxation may be sound, but the implemented floating-point return value has not been certified as outward-valid.
2. The `max_boxes` fallback returns `max(global_ub, best + tol)`. Given valid box upper bounds, the heap's unresolved maximum and the pruning invariant make this a plausible conservative fallback; I found no basis to call it an underbound. It does not certify the requested tolerance when the cap is reached, but tolerance failure alone does not invalidate an upper bound.

The current limitation is lack of a numerical error certificate for the claimed upper bound, not a demonstrated state-reset bug or a demonstrated timeout underbound. The optimizer can hit its `max_boxes` cap and fail its requested accuracy, while still plausibly returning a conservative value under the exact-arithmetic proof assumptions.

## Scope

- The standard `A1b`/`A5b` path sets `profile_stride=0`; it does not call this optimizer. Their previously reported results and validity argument are unaffected by this prototype audit.
- The only factory entry that enables it is `A5b-profile-first` (`scripts/sota_sprint/fam_a.py`). Its exploratory screen already failed the retention rule and was about 63 times slower than A5b (`profile_denominator_dev_protocol.md`).
- No result from the prototype may be described as independently verified, anytime-valid in finite-precision implementation, safe, or SOTA based on the current code. Its 20-seed screen is development evidence only. The mathematical validity question remains unresolved rather than disproved.

## Why this is not the remaining novelty lead

Even if a certified optimizer were built, the registered integrated screen did not improve either late regime, was noisy on one dependent alternative, and materially increased runtime. Tightening a likelihood denominator is not itself a new statistical construction. The remaining value is an implementation audit lesson: certified e-values require fail-closed numerical upper bounds, and runtime optimizations need their own validity proof.

## Disposition

Quarantine the profile path from future validation. Do not promote its implementation-level validity claim without resolving the numerical certificate. If the line is ever reopened, require all of the following before running efficacy experiments:

1. a proof that each returned value is an outward-valid upper bound in exact arithmetic;
2. directed rounding or an explicit analytic rounding-error envelope for all floating-point operations;
3. timeout behavior that is shown to retain a valid coarse upper bound even when the requested tolerance is unmet;
4. direct property checks against exact/rational likelihood maxima on small cases, including boundary values, varied gaps, resets, and long all-equal paths;
5. a measured end-to-end cost/power improvement that clears the already registered comparator panel on fresh streams.

## Provenance

- Implementation: `scripts/sota_sprint/markov_profile.py` and `fam_a.py` in local checkout `de9aaaa3` plus uncommitted local research changes.
- Development protocol and negative outcome: [`profile_denominator_dev_protocol.md`](profile_denominator_dev_protocol.md).
- Core A5b validity scope and distinction: [`family_a/RESULTS.md`](family_a/RESULTS.md).

