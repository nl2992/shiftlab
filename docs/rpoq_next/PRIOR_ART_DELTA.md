# Prior-art delta (provisional)

**Source-access limit:** primary papers could not be fetched (see charter). The two newest mandatory sources (Pro-Active Inference, arXiv:2610.34681; Active Multiple-PPI, arXiv:2605.08429) are **unread**. Nothing here is a novelty claim.

| Closest prior | Overlap with Candidate A | Remaining difference | Status |
|---|---|---|---|
| ASI, Robust ASI (code read; repo audit for the papers) | Label-probability design under a budget; the active-to-uniform path | They optimize estimator variance; A optimizes a growth surrogate with per-context bets | Distinct objective, but under a common bet the two coincide (derived) |
| e-PS (arXiv:2609.26651, repo audit) | Allocating samples among unresolved hypotheses by estimated e-value growth | Setting differs (multiple testing vs one monitor with contexts); the mechanism is the same family | Overlaps; direct comparison would be required |
| Repo's myopic exact mixture-growth rule | One-step expected log-growth allocation | A adds per-context bets, SNR concentration, the bet-cap term | Same family; that rule failed its own screen |
| Stratified / subgroup e-process composition (repo M1–M3, Chugg-style) | Per-stratum evidence | A adds learned concentration on the best stratum | Known caveat: changes the detected alternative |
| Active subgroup selection / best-arm style testing | Concentrating samples where signal is strongest | — | Likely the closest family; not searched beyond the repo's audits |

**Delta, stated narrowly:** a growth-based (not variance-based) allocation with per-context Kelly bets, evaluated under delay and a hard cap, with its failure condition characterized. **This is not shown to be new, and the real-data evidence is negative.**

## Update 2026-10-30 (web-search scan, snippet level; see `SOURCE_UPDATE.md`)
- **Hsu and Shekhar (arXiv:2607.17409)**: "growth-oriented querying" maximizing the worst-case one-step expected log-increment for confidence sequences from test supermartingales, plus mixtures with uniform exploration, and a finding that uniform can sometimes beat adaptive rules. This is the closest prior art for Candidate A and for the hybrid in Candidate B. **Candidate A's core idea is not new.**
- **Sfyraki and Wang (arXiv:2604.18569, ICLR 2026)**: uniform querying at least as effective as uncertainty-exploiting policies in sequential active PPI mean estimation. Corroborates our negative CRSP results.
- Pro-Active Inference and Active MPPI are estimation methods; the unread-source flag for them is replaced by a snippet-level status.
