# Ledger (v2)
- ea09930: CI lint fixed (RNG-advancing draw kept so published CIs are unchanged); H1 gated ONS implemented and development-searched (17 configs × 2 label rates).
- H1 result: gated ONS is between HG and ONS; beats ONS at matched benign FA (+.10 to +.14 at cap .05, 10% labels); ties/mixed vs HG (+.003 to +.064). Carried forward: hard200, soft2, unc2, multi.
- H2 result: Brier-guided discounted Kelly on cost evidence: .153→.424 (10%), .354→.673 (20%) vs the cost parent at false alarms ≤ .03.
- H3a result: predictable-baseline ONS lowers strong-dependence false alarms to about the parent's level but loses about half the power. H3b/H3c not done.
- Not done: random/outcome-dependent delay, corrected misspecification test, hard-budget audit, G4–G6 generators, published-method reproductions, frozen confirmation, computational profiling, cross-method mechanism analysis, real data.
- Legacy exit condition remains recorded as unmet; it is not edited.
- G4 frozen confirmation: C1 PASS (H2c +.268/+.176 vs cost parent), C2/C3/C4 PASS, C2b/C3b FAIL (gated ONS does not beat HG). See CONFIRMATION_RESULTS.md.
- Real-data access: TLC and UCI hosts denied by the proxy (403); no data pulled. See REAL_DATA_ACCESS_STATUS.md.
- Runtime profile recorded (COMPUTATIONAL_RESULTS.md); no speed-up claim.
