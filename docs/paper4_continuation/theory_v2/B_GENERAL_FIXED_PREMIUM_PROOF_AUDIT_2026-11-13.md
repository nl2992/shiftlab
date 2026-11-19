# Adversarial audit: arbitrary fixed-budget premium bound

**Date:** 2026-11-13  
**Proof under review:** `B_GENERAL_FIXED_PREMIUM_PROOF.md`  
**Reviewer route:** fresh native Codex subagent, requested `gpt-6-astra`, `ultra`; actual model-family identity is not exposed by the runtime.  
**Assurance:** same-family review; acceptance is provisional. This is not cross-family review or formal proof-assistant verification.

## Verdict

**PASS.** The reviewer found no FATAL, CRITICAL, MAJOR, or MINOR mathematical issue and no remaining unjustified step, conditional on the explicit assumptions in the candidate. The reviewer matched the query visibility, release-before-action timing, first-promotion objective, and null class to the existing game. A separate fresh-context arithmetic/witness check also found no issue in the bounds and constants.

The candidate statement is:

For every integer `B >= 1`, let `H_B = 6 B^3 + 3 B + 2` and
`r_0(B) = 1 / (16 (B+2) H_B)`. In the stationary symmetric anti-persistent HMM with `d=1`, `c=k=0`, `alpha=1/10`, `2/5 < g < 1/2`, and `0 < r < r_0(B)`, for every `T >= 3B`,

```text
Gamma(T) >= alpha g r * 3(B+1) / (8(B+2)),
rho_Gamma(T) >= 3 / (8(B+2)).
```

The radius depends on `B`; this is not a common-radius or common-positive-constant result for unbounded `B`. The proof also gives a simultaneous finite range `B <= floor((1056r)^(-1/4))` for `0 < r < 1/1056`, with the corresponding weaker common-in-range bound.

## Review obligations and findings

- **Adaptive cylinders and posterior expansion:** Valid after fixing the independent learner seed and a realized label-history leaf. Query times are fixed on that cylinder; adaptive decisions add no likelihood factor. Even-spin moments and odd-subset posterior terms apply at those fixed times. Emission factors are positive, hence `D_m > 0`.
- **Density and posterior remainders:** The reviewer verified `delta_B <= 2 B^2 r` and `P_B <= 2 B r + 4 B^3 r`, with uniform convergence under `B^2 r < 1/288`.
- **Bellman envelope and same-step query:** The posterior identity `E|psi_S(x)| = max(|x|,a)` holds for every `x` in `[-1,1]`. Backward induction handles all remaining query budgets, a query on the promotion step, rollback, and re-promotion.
- **Continuation and leaf bounds:** Multiplication by `D_m` removes the posterior denominator; the correction terms sum to `H_B r`. The causal mixture denominator is positive for every relevant cylinder, and its treatment of a not-yet-released query is correctly marginalized.
- **Risk averaging:** First-promotion leaves are disjoint. Averaging the deterministic-seed bound does not assume that each seed is separately feasible; it uses only the overall mixture risk, which is at most `alpha` under each admissible null.
- **IID witness:** The witness release times are distinct, its first and subsequent information increments are valid, and its last counted release is within `T >= 3B`. Root mixing with never-promote gives IID risk `alpha`.
- **Constants, edge cases, and division:** The reviewer checked the maxima defining `C_B` and `I_B`, the two remainder allowances, `B=1`, positivity of the IID value, and the final ratio division. No counterexample was found.
- **Finite-budget corollary:** Floor-boundary equality is covered: every allowed `B` satisfies `r <= 1/(1056 B^4) <= r_0(B)/2 < r_0(B)`, and `T >= 3 Bbar(r)` implies `T >= 3B`.

## Model alignment

The reviewer checked the candidate against the repository sources:

- `docs/paper4_continuation/CAUSAL_SAFETY_PREMIUM_THEORY.md` defines the matching objective, hard pathwise query budget, first-promotion risk, and learner classes.
- In `src/shiftlab/dive/causal_switching_game.py` around lines 86–88, labels are released before the next action; around lines 142–147, the null move is keyed on the public next history, including the chosen query.
- `src/shiftlab/dive/first_promotion_decomposition.py` around lines 93–113 encodes the release and observation convention used by the proof.
- The reviewer found no additional substantive model assumption beyond the assumptions stated in the candidate.

## Counterexample pass

The reviewer checked consecutive and separated adaptive queries, all-one and zero-ending leaves, promotion before any label release, same-step promotion/query, arbitrary rollback, unsafe individual private-seed components, `B=1`, minimum permitted horizon, and equality at the floor boundary. No counterexample was found.

## Scope and remaining work

This review supports the **theorem under its stated model**. It does not certify a numerical cell, establish novelty, or settle the publication decision. The B=3, T=16 cell at `r=0.008`, `g=0.49` (inside the M6/M10 rectangle) timed out at 3,600 seconds; it is outside M11's much smaller B=3 radius `r<1/13840`, so it is not a numerical check of M11. The locked decision remains open; retain the `B`-dependent radius and do not claim a uniform positive constant over unbounded budgets or an outcome-reactive-adversary premium.

The independent review was run in a fresh agent context but used the same Codex family. Cross-family review remains unavailable in this checkout, so the locked independent-review criterion should still be treated as provisional until that limitation is resolved.
