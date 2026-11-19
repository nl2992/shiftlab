# Claims from the B=3 horizon extension

**Date:** 2026-11-11  
**Verdict:** partial  
**Review:** fresh Codex reviewer requested as `gpt-6-astra` / `ultra`; the host did not report a reviewer model identity. Same-family, provisional. Evidence pre-check verified all five cited value/source pairs; this verifies existence, not mathematical support.

## Intended claim

For B=3 in an explicit open family of symmetric stationary anti-persistent models with t<1, rho_Gamma remains bounded away from zero as the horizon grows.

## What the evidence supports

The six certified B=3 extension cells at t in {2/3, 3/4}, e=1/10, d=1, c=k=0, alpha=1/10, T=13–15 all have Gamma>0. The corrected rho intervals are in `results/wpM_b3ext_rho_corrected_v1.json`. At T=15, rho is approximately 0.143701674 for t=2/3 and 0.125479616 for t=3/4. The associated T=12 values are approximately 0.145420284 and 0.148754586.

## What the empirical evidence does not support

These finite cells do not establish a positive liminf or a uniform-in-T lower bound. The t=3/4 sequence declines through T=15. Separately, the independently reviewed theorems in `MIXING_PREMIUM_THEOREM.md` establish uniform B=3 through B=6 bounds on a small open parameter rectangle; M10 combines them with B=1,2 into a common `B<=6` bound. These mathematical claims do not follow from the finite cells. B>=7 and growing-budget behavior remain unresolved; one in-region certified cell and a focused novelty review are still pending, so the overall publication decision remains open.

## Corrective note

The first B=3 extension runner divided both rho endpoints by the lower VOI endpoint. The corrected sidecar widens float endpoints outward and uses the recorded Gamma width to upper-bound the missing IID-value interval. The correction changes the T=15 lower endpoints by less than 1e-12; Gamma positivity and the decision do not change. Both B=3 and B=4 runners now compute rho from the separate L_IID and U_IID bounds directly.

## Next evidence

The B=4, T=13 cells timed out at 1,800 s each. A corrected one-worker retry with a 3,600 s per-cell cap timed out at t=2/3; t=3/4 did not run. Treat this as incomplete compute, not a premium value. The B=2 T=17 t=9/10 cell is still running. Any general-budget asymptotic claim still requires a proof controlling all adaptive query schedules and a reviewed uniform bound.

## Addendum — independently reviewed B=3 through B=6 theorems (2026-11-12)

The result-to-claim scope is updated by proofs, not by the numerical extension. Theorem M6 proves
`rho_Gamma(T)>=19/101` for every `T>=16` on `r in (1/200,1/100)`, `g in (2/5,1/2)`, `B=3`, `d=1`, `c=k=0`,
`alpha=1/10`. Theorem M7 on the same rectangle proves `rho_Gamma(T)>=13/84` for `B=4`, and M8 proves
`rho_Gamma(T)>=40/303` for `B=5`; M9 proves `rho_Gamma(T)>=13/118` for `B=6` when `T>=20`. Proofs and independent
same-family audits are in `B3_UNIFORM_PREMIUM_PROOF.md` through `B6_UNIFORM_PREMIUM_PROOF.md`. B>=7 and growing-B uniformity remain open, so
the locked general-budget GO/NO-GO criteria remain unchanged.

## Addendum — reviewed B=2 theorem, T=16 extension (2026-11-12)

`results/wpM_b2_t16_v1.json` contains three additional certified cells at the same symmetric stationary setting,
with `alpha=1/10`, `d=1`, `c=k=0`. The corrected rho intervals are:

| t | T=12 | T=15 | T=16 | T=17 |
|---|---:|---:|---:|---:|
| 2/3 | 0.200440828 | 0.200073153 | 0.200048796 | — |
| 3/4 | 0.145846679 | 0.143812709 | 0.143581991 | — |
| 9/10 | 0.210096788 | 0.173359151 | 0.151422863 | 0.143668573 |

These cells support finite-horizon positivity and all are above half their T=12 baselines. From T=16 to T=17 the
t=9/10 rho lower endpoint falls 5.12% and Gamma falls 3.55%. T=17 remains below the reviewed M4 threshold `T0=37`;
these data do not establish a trend limit or replace M4's theorem. Exact T=17 output is
`results/wpM_b2_t17_t9_v1.json`.
