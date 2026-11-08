# Novelty audit

No new-algorithm finalist exists, so no new-method novelty claim is made.

| Item | Closest prior (evidence level) | Status |
|---|---|---|
| EQSDp / Wald payback switching | Regol et al. ICML 2025 UPF (read: arXiv HTML Secs. 1–7, App. A.1–A.3); Wan et al. 2023; Chick et al. 2017; *The Challenger* arXiv 2512.18390 (snippet only) | NOVEL-INTEGRATION; the Beta quantile is not new (UPF quantile rule) |
| Change-point-cut evidence (screened, failed) | GLR-klUCB (Besson et al. JMLR 2022), CUSUM-UCB, ADSWITCH, BOCPD (snippets) | KNOWN components; no gain |
| BCR (failed) | Model Picker (Karimi et al. 2021, ported from author code); successive elimination / racing; switching-cost bandits | no claim |
| Gap-Mix evidence | Markov sequential testing; Sethi et al. overlap noted in `docs/gaver/40_PRIOR_ART_CHECK.md` (snippet level) | unresolved; scoped finding only |
| PAVE | value-of-information acquisition; `episode_front` matches it | no claim |

Open audit actions before any paper: full-text reads of *The Challenger*, Gong–Zhang and Qiu et al.
(to describe precisely what the adapters omit), and the Sethi et al. Markov testing paper.
