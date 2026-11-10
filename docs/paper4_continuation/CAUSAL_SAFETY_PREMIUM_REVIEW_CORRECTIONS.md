# Corrections to `CAUSAL_SAFETY_PREMIUM_THEORY.md` (WP G proof review, 2026-11-10)

**Reviewer:** fresh-context Opus 5.5 subagent, read-only. `review_independence: same-family`,
`acceptance_status: provisional`. Scratch scripts are under the session scratchpad `review_C/`.
Corrections marked ✔ were **re-computed independently by the lead** with FCG and the exact reference solver
(`scratchpad/verify_g.py`). This file supersedes the affected statements; the original document is left unchanged.

| Claim | Review outcome | Correction |
|---|---|---|
| Lemma R (lines 47–75) | HOLDS. LP strong duality over mixtures, Kuhn, and the pathwise coupling are all valid | none |
| Z1 proof | HOLDS as stated (TP2 + MLR + (M), B=1). 6,000 random cells satisfying the hypotheses all give Γ = 0 | Restate with the weaker condition **(W)**: `P1(τ)·G1(τ,s) ≥ P0(τ)·G0(τ,s)` whenever `G0 > 0`, for all `τ ≤ T−d`, `s ≥ τ+d`. TP2 + (M) ⇒ W is a corollary. W held in 1,126 grid cells (all Γ = 0) and failed in all 105 cells with Γ > 0. W is **not necessary**: it fails for odd-T C3 cells, where Γ = 0 |
| "(M) necessity OPEN" (lines 125–127, §6 table line 404, framing at line 146) | **FALSE.** TP2 + MLR without (M) gives Γ > 0 already at **B = 1** | ✔ Cell T=5, B=1, d=2, t01=1/2, t10=0, emissions (3/20, 3/5), prior 0, c=k=0, α=1/10: **Γ = 39/32000** exactly; U equals the reference. Larger example: T=6, emissions (1/100, 7/10), otherwise the same: Γ = 589/64000 (reviewer only) |
| Theorem C3 causal dual certificate (lines 234–241) | **GAP / arithmetic error** when c > 0 | Use `μ_I = G1`, `μ_0 = (g−k)/2 − c`; then all checks hold |
| Theorem C3 statement | **FALSE in the regime** `2k < g ≤ 3k − 2c` | ✔ Correct form (even T, `g > 2k`, `c ≤ (g−k)/2`, `α ≤ 1/2`): **Γ = α · min{(g−k)/2 − c, g − 2k}**. Example e=1/4, k=1/10, c=0, α=1/10: true Γ = 0.005 at T=4 and T=6; the original formula gave 0.0075. Side conditions `T ≥ 4` and `G1 ≥ 2c` are unnecessary (formula holds at T=2) |
| C3 odd T, Γ = 0 | NUMERICALLY VERIFIED (T = 5, 7), unproved | none |
| Lemma H, C4 bounds 1 and 2 | HOLD | none |
| C5 "single-calendar gap = value of private randomisation" | **GAP: overgeneralised** from one cell (asym7) | Restrict the wording to that cell. The NO-GO verdict stands |
| `c2_search.py` (M) check | Bug: checks the marginal over all t ≤ T instead of τ ≤ T−d, which inflates the count of (M)-violating cells | Recorded; affects only the descriptive counts |

**Reviewer's strength assessment (accepted by the lead).**
- Lemma R and Z1/W are a characterisation *proposition*, not a standalone theorem contribution.
- C3 is a separation *example*.
- The B=1 counterexample shows anti-persistence is not needed for Γ > 0.
