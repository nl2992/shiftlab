# Theorem status

| Statement | Status | Where |
|---|---|---|
| Causal-null recursion `v(h) = max{v(h0), (v(h0)+v(h1))/2}` | PROVED; PRIOR ART (Krale et al. 2025, Theorem 3) | `theory/01` §2 |
| Surcharge identity `R_causal - R_IID = sum 2^-t [v(h0)-v(h1)]_+` | PROVED; NUMERICALLY VERIFIED (276 events, three routes); PRIOR ART (algebra) | `theory/01` §2 |
| Monotone-hull bound `R_IID <= R_causal <= P(A_up)` | PROVED (coupling); NUMERICALLY VERIFIED | audit note; checker |
| Marginal-average randomised certificate is valid | FALSIFIED (3/4 vs 1/2) | checker; counterexample library E |
| Value-sensitive safe pruning (risk monotone; loss `<= delta P(reach S)`) | PROVED; PRIOR ART (branch-and-bound); empirically useless at the registered tolerances | `../risk_preserving_approx/PAPER4_VALUE_SHIELD_DECISION_V1.md` |
| Lemma 1: risk is linear for a fixed null strategy | PROVED (standard sequence form) | `theory/01` §4 |
| Lemma 2: the supremum is attained at deterministic endpoint strategies | PROVED | `theory/01` §4 |
| FCG correctness: `L_K <= V* <= U_K`, strict cuts, finite termination | PROVED; NUMERICALLY VERIFIED on 9 cells | `theory/01` §4; `experiments/04` |
| FCG polynomial iteration bound | NOT CLAIMED (worst case `|N_ext|`, exponential) | — |
| Verifier-centred structural complexity theorem | Abandoned. A width parameter equals known product / Myhill–Nerode size, and verification is not the bottleneck | `theory/01` §3 |
| IID-tightness: when is the IID optimum causal-safe? | **EXPLAINED by existing theorem** in all 6 IID-safe cells. The HiGHS IID optimum is a two-plan root mixture, and both plans have monotone promotion events. Contrast cells C2, C3 and C6 each carry one non-monotone plan (weight 0.4, G-violation 0.4). This holds for the returned LP vertex only. Other optimal vertices were not tested | `experiments/results/iid_tightness_v1.json` |
