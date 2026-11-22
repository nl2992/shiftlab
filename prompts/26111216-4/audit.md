# B=6 proof-orchestrator audit

Status: `ACCEPTED` for the stated B=6 theorem after independent review.

## Notation scorecard

- **Core semantic objects retained:** project HMM, causal-null class, promotion event/risk, `VOI_X`, `Gamma`, and `rho_Gamma`.
- **Undefined symbols:** none intended; local terms are defined in `local-proof.md`.
- **Symbol collisions:** latent correlation is `rho=-r`; relative premium is `rho_Gamma`; labels and signs are distinct.
- **One-use definitions:** `delta_m`, `D_*`, and `posterior_error(m)` each define one local bound.
- **Maximum parallel representations:** one even-subset density formula and one odd-subset posterior formula.
- **Maximum alias-chain depth:** 1.
- **Maximum active nonstandard symbols:** 12 (`r,g,a,rho,D_m,delta_m,D_*,E_m,G_y,v1,Q,W`).
- **Top-down derivation structure:** PASS — two pathwise upper bounds plus one risk-scaled IID witness imply the target.

## Scope

The review is `independent-review.md`. It accepts `rho_Gamma>=13/118>0.10` for `T>=20` on the stated B=6 open
rectangle, conditional on the project game semantics. It does not establish B>=7 or growing-budget uniformity.
