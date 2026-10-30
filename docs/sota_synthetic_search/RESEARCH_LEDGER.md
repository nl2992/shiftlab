# Research ledger (SHIFTLAB SOTA synthetic search)
- Branch `research/shiftlab-sota-synthetic-search-2026-10-29`, start SHA 0b1ce99. Synthetic only; CRSP/real data untouched.
- Registries: `outputs/sota_search/registry_*.sqlite` (append-only; failures recorded).
- Falsified: S01 (cost e-process weaker than Brier); X1 median criterion; BD on the Brier parent.
- Not supported on held-out: BD marginal; HG rule at 20% labels on G2.
- Open: Q2, Q3, G3/G4, CIs over worlds, literature novelty check, stress tests.

## 2026-10-30 continuation (`research/hg-validation-and-novelty-2026-10-30`)
- Validity counterexample + uniform-cap repair (docs/hg_validation/02_*).
- Paired inference: gains within-world distinguishable from 0; G2/20% fails frozen +0.05 (doc 03).
- Adaptive-betting comparators: ONS matches HG power at higher benign FA; frontier on dev pool favours HG at low FA (doc 04).
- G3 frozen confirmation: HG beats parent (+.050/+.131); niche vs ONS not confirmed (doc 05).
- Dependence stress: strong autocorrelation breaks all, HG worse than parent (doc 06).
- Real data: CRSP replay DK worse than parent (docs 15, 16 on the earlier branch). No benchmark beaten on real data.
- Open: G5, rest of G6, Q2, Q3, published-method reproductions, adaptive-discount fix, frozen final study.
