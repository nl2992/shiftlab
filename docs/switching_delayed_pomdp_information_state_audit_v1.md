# Delayed POMDP information state: novelty boundary

**Date:** 2026-10-29. **Status:** source-level audit of the economic-law compression route; not a
reduction of the full two-law safe-switching problem.

## Primary result inspected

Subramanian, Sinha, Seraj and Mahajan, “Approximate Information State for Approximate Planning
and Reinforcement Learning in Partially Observed Systems,” *Journal of Machine Learning Research*
23 (2022), 1–83. I inspected the finite-horizon information-state definition and Theorem 5 and
proof (which establish exact Bellman recursion from a sufficient information state), plus the
delayed-POMDP example in Section 2.4. That example states that for a POMDP with delay `delta`, the
belief on the `delta`-step delayed state given delayed observations and controls, together with the
last `delta` controls, is an information state; its dynamic program is a special case of Theorem 5.
The official PDF is cached and hashed in source manifest v27.

## Consequence for ShiftLab

Under the known alternative HMM, finite known delay, and a finite horizon, a proposed controller
cannot claim novelty merely for retaining a regime belief, recent query/action history, a pending
label queue, remaining request budget and deployed model. These are the ordinary ingredients of a
delayed partially observed control state. For a fixed finite-state model, one can augment the hidden
state with pending outcomes/release clocks and the public budget/action variables, then maintain the
corresponding learner belief. This is a valid way to evaluate alternative-law utility; the cited
paper does not itself prove this ShiftLab-specific encoding or a risk guarantee for it.

That belief does **not** encode the separate causal-null objective. The null opponent sees pending
labels that the learner cannot see and may adapt each conditional label law to its full history.
Histories aliased by the alternative belief can therefore have different continuation risk, as the
repository's exact posterior-alias counterexample demonstrates. Nor does the cited single-law
information-state theorem enforce the shared-policy, worst-case any-promotion constraint. A scalar
remaining-risk augmentation alone is also already covered by the constrained-POMDP prior audit.

## Decision

Close “belief + delay queue + hard-budget/switch state” as a novelty claim. Keep it as the economic
state in any future prototype. The unresolved G1 object is a **risk-preserving information state**
for the learner's shared policy under the asymmetric null, with either (a) a value/risk approximation
bound against the full-history two-law oracle or (b) a growing-family lower bound showing why such
compression is impossible at a stated memory scale. Promotion validity and current-regime benefit
after reversal remain distinct; post-reversal value needs post-change evidence or an explicit
persistence model.

## Provenance

- Primary source: [JMLR volume 23, paper 20-1165](https://jmlr.org/papers/v23/20-1165.html),
  especially Theorem 5 and Section 2.4's delayed POMDP example.
- Cached PDF: `outputs/switching_source_audit_v1/subramanian_sinha_seraj_mahajan_jmlr22_approximate_information_state.pdf`.
- SHA256: `247D75B379D18F5355921A1CA2884551210927E7BFA6E9D6878E0EE24A8EC8F5`.
- Source inspection was checked against the cached PDF text and the official JMLR PDF. It is a
  selected theorem-scope audit, not an independent reproof of the paper's general theorem.
