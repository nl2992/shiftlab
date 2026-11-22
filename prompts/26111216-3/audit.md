# B=5 proof-orchestrator audit

Status: `ACCEPTED` for the stated B=5 theorem after the independent final pass.

## Notation scorecard

- **Core semantic objects retained:** project HMM, first-promotion event/risk, `VOI_X`, `Gamma`, and `rho_Gamma` definitions.
- **Undefined symbols:** none intended; local symbols are defined in `local-proof.md`.
- **Symbol collisions:** latent correlation `rho=-r`; relative premium `rho_Gamma`; `s_i` are label signs.
- **One-use definitions:** `delta_m`, `D_*`, and `E_m` are local envelope bounds, defined at use.
- **Maximum parallel representations:** one even-subset transcript-density expansion and one odd-subset posterior expansion.
- **Maximum alias-chain depth:** 1.
- **Maximum active nonstandard symbols:** 11 (`r,g,a,rho,D_m,delta_m,D_*,E_m,G_y,v1,Q`).
- **Top-down derivation structure:** PASS — target follows from one fixed null mixture, pathwise continuation bounds, and one feasible IID witness.

## Independent review and limitations

The reviewer is recorded in `independent-review.md`; it accepted after confirming the Bellman induction, first-promotion leaf sum, same-step pending-query convention, and witness definition. This is same-family adversarial review, not external or cross-family review. The theorem covers B=5 only on the stated rectangle; B>=6 and growing-B behavior remain open.
