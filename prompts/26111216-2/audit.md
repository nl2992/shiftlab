# B=4 proof-orchestrator audit

Status: `ACCEPTED` for the stated B=4 theorem after incorporating reviewer-requested derivations.

## Notation scorecard

- **Core semantic objects retained:** same stationary symmetric HMM, promotion-risk objective, `VOI_X`, `Gamma`, and `rho_Gamma` as the project source.
- **Undefined symbols:** none intended; all B=4 symbols are introduced in `local-proof.md` or source-defined.
- **Symbol collisions:** latent correlation is denoted `rho=-r`; relative premium is `rho_Gamma`; query signs are `s_i`.
- **One-use definitions:** `delta`, `D_*`, `E_m`, and `D_m` are local envelope terms and are each defined at first use.
- **Maximum parallel representations:** one exact transcript-density formula for each label count; exact values live in the companion rational script/output.
- **Maximum alias-chain depth:** 1.
- **Maximum active nonstandard symbols:** 10 (`r,g,a,D_m,Q,delta,D_*,E_m,G_y,v1`).
- **Top-down derivation structure:** PASS — reduce the relative premium to two dual upper bounds and one explicit IID witness, then verify exact coefficients.

## Review and limitation

The independent adversarial review is `independent-review.md`. It accepts `rho_Gamma>=13/84>0.15` for every `T>=16` on the stated B=4 open rectangle. This does not establish general-budget uniformity; B>=5 and growing-B behavior remain open.
