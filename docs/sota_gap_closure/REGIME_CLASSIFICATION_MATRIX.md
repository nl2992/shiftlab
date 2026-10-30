# Regime classification matrix
Ground truth (evaluator-side Monte Carlo, 30k samples per regime; G4: 60k). Harmful = decision-cost increase of the fixed deployed policy >= 0.10 (G4: >= 0.03 on its [0,1] loss scale). Discrepant = joint-law RBF MMD^2 vs the source >= 0.02.

| generator | regime | discrepancy_MMD2 | predictive_dBrier | decision_harm | class |
|---|---|---|---|---|---|
| G3/G5 regime | none delta=0 FN=5 | 0.0000 | 0.0000 | 0.0000 | benign / null |
| G3/G5 regime | concept delta=2 FN=5 | 0.0041 | 0.0991 | 0.2408 | harmful, little discrepancy |
| G3/G5 regime | cov_benign delta=3 FN=5 | 0.3000 | 0.0014 | 0.0036 | benign discrepancy |
| G3/G5 regime | prior delta=1.5 FN=5 | 0.0061 | 0.0349 | -0.0109 | benign / null |
| G3/G5 regime | cost delta=0 FN=20 | 0.0000 | 0.0013 | 0.2330 | harmful, little discrepancy |
| G4 finance | signal loading beta=1 | 0.0000 | 0.0000 | 0.0000 | benign / null |
| G4 finance | signal loading beta=0.3 | 0.0036 | -0.0230 | 0.0522 | harmful, little discrepancy |
| G4 finance | signal loading beta=-1 | 0.0349 | 0.1156 | 0.1479 | harmful + discrepant |
| G1 | G1 cov_benign d=3 | 0.2996 | 0.0023 | -0.0010 | benign discrepancy |
| G1 | G1 concept d=2 | 0.0041 | 0.0991 | 0.2408 | harmful, little discrepancy |
| G2 | G2 concept d=2 | 0.0041 | 0.0891 | 0.2086 | harmful, little discrepancy |
| G2 | G2 cov_benign d=3 | 0.3164 | 0.0959 | 0.2192 | harmful + discrepant |

The three dimensions disagree by construction: `cov_benign` (large discrepancy, no harm), `cost` regimes (no discrepancy at all, harm from a changed decision cost), `concept` (small discrepancy, large predictive and decision harm), G2 `cov_benign` (the nonlinear term turns a nuisance shift into harm). Per-step curves for the G1/G2 schedules are in `outputs/sota_search` code (`generators.truth`); for G3/G4 the per-seed truth arrays are `(S,T)` lookups of these regime effects through the simulated regime path.
