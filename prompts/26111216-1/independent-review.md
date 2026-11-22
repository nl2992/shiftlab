# Independent audit of the B=3 uniform-premium proof

**Reviewer verdict:** REVISE the initial proof note; ACCEPT the mathematical route after incorporating the explicit derivations in `local-proof.md`.

The reviewer found no counterexample or fatal mathematical gap. The proposed `T0=16` and `c_star=0.18` survive. The witness's earlier claim that its limiting branch value equals `G0+2v1` was inaccurate; it is corrected in the current proof note. The corrected lower bound is unaffected.

**Review independence:** separate fresh agent, adversarial derivation, same model family; not independent-model or external review. The reviewer did not edit project files.

**Audited scope:** stationary symmetric HMM, latent correlation `rho=-r`, `a=sqrt(g)`, `B=3`, `d=1`, `c=k=0`, `alpha=1/10`, `r in (1/200,1/100)`, `g in (2/5,1/2)`, every deterministic adaptive learner plan and randomized mixtures.

## Obligation ledger

| Obligation | Verdict |
|---|---|
| Agreement with first-promotion game and release-before-action timing | Valid |
| Dual-null admissibility | Valid |
| Adaptive-history likelihood formulas | Valid with explicit prefix argument |
| Pending labels at promotion | Covered because `d=1` |
| Marginal information-value identity | Valid |
| Arbitrary adaptive post-promotion timing | Valid by finite-horizon Bellman induction |
| Posterior envelope including three-label interaction | Valid |
| Uniform rational constants | Valid |
| IID witness for finite horizon | Valid after correcting its limit sentence |
| Extension from deterministic plans to mixtures | Valid by linearity against fixed nulls |

## Key independent checks

For a fixed transcript of `m` query labels with `z` zeros, the null mixture has
`Q(h)=2^-m(4-m+2z)/4`; each query schedule is determined along the fixed transcript, so it introduces no additional probability factor. The critical coefficient uses `D_1=1` exactly; applying the generic three-label bound to `m=1` would lose the `1.61` margin.

The adaptive continuation bound follows from
`F_t(x)=sum_{j=0}^{T-t}(a rho^j x)^+` and the one-query identity
`E[(a rho^j psi_S(x))^+]-(a rho^j x)^+ = gr^j/2 (1-|x|/a)^+`.
Backward induction yields `W_b(t,x)<=F_t(x)+b v1`, `v1=gr/(2(1-r))`.

For the posterior envelope, the three-label numerator includes the four-spin term
`g^2 s1 s2 s3 rho^(u2-u1+v-u3)`. The reviewer verified the exponent, denominator bound, and summed remainder. No missing interaction or sign/gap error was found.

At the closed endpoint `r=1/100, g=1/2`, exact normalized values are:

- `G0/(gr)=10000/9999`
- `G1/(gr)=100/9999`
- `v1/(gr)=50/99`
- `E/(gr)=5060200/197970201 < 0.026`
- Maximum causal coefficient `5360/3333 < 1.61`
- Maximum IID coefficient `6700/3333 < 2.02`

The endpoint bounds apply throughout the rectangle because the normalized envelope terms increase in `r,g` and the common denominator remains positive.

For the fixed IID witness querying at times 1, 5, 8 and promoting at time 2 iff `Y1=0`, the reviewer verified
`zeta_T/(gr) >= 2-(r^4+r^3)/2 > 1.99` for `T>=9`; thus `T0=16` is conservative. Its exact infinite-horizon value is `G0+v1(2-r^4-r^3)`, not `G0+2v1`.

## Final reviewer disposition

After incorporating the detailed induction, prefix likelihood calculation, posterior expansion, endpoint arithmetic, and corrected witness into `local-proof.md`, the reviewed bounds imply
`Gamma >= 0.38 alpha gr` and `rho_Gamma >= 0.38/2.02 = 19/101 > 0.18`.

This is a `B=3, d=1, c=k=0` theorem only. It does not establish a general-budget theorem, novelty claim, or empirical conclusion.

## Final pass on the revised proof note

After reviewing the revised `local-proof.md`, the reviewer requested and confirmed four wording fixes: describe the fixed witness as a risk-`1/2` pure plan mixed with never-promote; write `D_* >= 0.98995`; specify backward induction simultaneously over query budgets; and state explicitly that the Bellman value allows all rollback/re-promotion schedules. Those changes are present. **Final verdict: ACCEPT** for the stated B=3 theorem, including `T0=16` and `c_star=0.18`.
