# Research ledger (SHIFTLAB SOTA synthetic search)
- Branch `research/shiftlab-sota-synthetic-search-2026-10-29`, start SHA 0b1ce99. Synthetic only; CRSP/real data untouched.
- Registries: `outputs/sota_search/registry_*.sqlite` (append-only; failures recorded).
- Falsified: S01 (cost e-process weaker than Brier); X1 median criterion; BD on the Brier parent.
- Not supported on held-out: BD marginal; HG rule at 20% labels on G2.
- Open: Q2, Q3, G3/G4, CIs over worlds, literature novelty check, stress tests.

- 2026-10-31 dependence sprint (branch research/shiftlab-dependence-gates-2026-10-31): Gate A PASS (null-class mismatch), Gate B FAIL for marginal guarantee under persistence (Theorem B1 + oracle ceiling), Gate C UNRESOLVED general / KNOWN fully-observed. LRV heuristic EMPIRICAL_ONLY (does not transfer). Final: F NO_GO. See docs/dependence_sprint/12_FINAL_PUBLICATION_DECISION.md.
