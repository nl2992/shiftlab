# Theorem registry

Statuses: PROVED · FORMALLY CHECKED · NUMERICALLY VERIFIED · EMPIRICALLY SUPPORTED · CONJECTURED · FALSIFIED ·
PRIOR ART · BLOCKED · NOT STARTED.

| ID | Statement | Status | Evidence |
|---|---|---|---|
| P4-1 | Causal recursion and surcharge identity | PROVED; NUMERICALLY VERIFIED; PRIOR ART (Krale et al. 2025) | `docs/paper4/theory/01` |
| P4-2 | FCG correctness (`L <= V* <= U`, finite termination) | PROVED; PRIOR ART (scheme) | `docs/paper4/theory/01` §4 |
| P4-3 | Monotone-event IID reduction | PROVED (repo, 2026-10-28) | `docs/switching_monotone_promotion_reduction_v1.md` |
| C-1 (review) | Z1 holds; restate via condition W; "(M) necessity open" FALSE: TP2+MLR fails at B=1 (Γ=39/32000, lead-verified) | PROVED (Z1); FALSIFIED (TP2+MLR⇒Γ=0 at B=1) | `CAUSAL_SAFETY_PREMIUM_REVIEW_CORRECTIONS.md` |
| C-1 | Lemma R (value-level: monotone Lagrangian minimisers for all λ ⇒ Γ=0); Theorem Z1 (B=1, TP2, MLR, (M) P_A(Y_τ=1)≥1/2 ⇒ Γ=0) | PROVED (agent); NUMERICALLY VERIFIED; proof review pending (WP G). General TP2+MLR ⇒ Γ=0 FALSIFIED at B=2 (Γ=657/5000000, lead-verified). Multi-label Lemma U CONJECTURED (1,200 symmetric persistent cells Γ=0) | `CAUSAL_SAFETY_PREMIUM_THEORY.md` |
| C-2 (review) | C3 as stated FALSE for 2k<g≤3k−2c; corrected Γ = α·min{(g−k)/2−c, g−2k} (lead-verified e=1/4: 0.005 not 0.0075); certificate multipliers fixed | CORRECTED; NUMERICALLY VERIFIED | `CAUSAL_SAFETY_PREMIUM_REVIEW_CORRECTIONS.md` |
| C-2 | Theorem C3: alternating chain t=1, B=1, d=1, T even ≥4 ⇒ Γ = α[(g−k)/2 − c], g=(1−2e)², T-invariant (odd T: Γ=0) | PROVED (agent); exact closed form checked 324/324 (agent) and at T=4,6 by lead vs FCG and reference; proof review pending. Not growing in T | `CAUSAL_SAFETY_PREMIUM_THEORY.md` |
| C-3 | Repair bound Γ ≤ (1−q)(C0 − V*_IID); monotone-restriction bound (tight on C3 family) | PROVED; repair bound loose by O(T); monotone bound is a corollary of the existing coupling lemma → NO-GO standalone | `CAUSAL_SAFETY_PREMIUM_THEORY.md` |
| C-4 | Adaptivity gap | IID: best calendar = adaptive in 13/13 cells; causal: single-calendar gap 5.797e-4 in one cell, closed exactly by private mixing over calendars → value of randomisation, NOT label-adaptive design → NO-GO (not new) | `CAUSAL_SAFETY_PREMIUM_THEORY.md` |
| B-1 | Implicit policy-column generation | NO-GO computational for HMM alternatives (pricing state = public tree: 65/65, 236/236, 848/848, 91/91); calendar-restricted pricing gives invalid LBs (8/10 cells above V*) | `IMPLICIT_LEARNER_OPTIMIZATION.md` |
| B-1S | Theorem B1-S: static (exchangeable) alternative ⇒ exact IID-row pricing on keys (t, last d−1 query bits, n1, n0), ≤ T·2^(d−1)(B+1)(B+2)/2 keys; L = V*_IID; certified V* whenever mixture risk ≤ α (49/49 cells, T up to 24) | PROVED (agent); NUMERICALLY VERIFIED (lead: 5 cells equal reference V* exactly); PRIOR ART (sufficient statistic + Dantzig–Wolfe + monotone reduction); static regime is degenerate shift | `IMPLICIT_LEARNER_OPTIMIZATION.md` |
| B-2 | Grid-refinement certificate L ≤ V* ≤ U | NO-GO prior art; LB stalls at IID optimum on reversal cells (C2 2.4002 vs 2.4419); kept as baseline | same |
| B-3 | Certified distillation | NO-GO prior art/computational (coupling product contains teacher tree); v1–v3 students collapsed to never-promote (recorded failures) | same |
| B-4 | Dual / first-promotion stopping reduction | NO-GO prior art/correctness (stopping on (belief,budget,t) false under alias counterexample) | same |
| D-1..D-4 | Fallback candidates | NOT STARTED | — |
| C-5 | Lemma U (multi-label zero premium): TP2 + (M) ⇒ Γ = 0 | CONJECTURED; NUMERICALLY VERIFIED (0 counterexamples in 12,060 cells satisfying (M)); proof gap: interior subtree exchange | `CAUSAL_SAFETY_PREMIUM_THEORY.md` § Follow-up |
| C-6 | Theorem N1: exact Γ for B=1, any HMM, α ≤ 1/2: Γ = α(2·max_τ g_z0(τ) − r_c)⁺ | PROVED (agent); matches certified Γ in 2,000/2,000 random cells; reproduces 39/32000 | same |
| C-7 | Theorem S1: static alternative ⇒ W ⇒ Γ = 0 for B=1 (any prior, d, c, k, α) | PROVED (agent); static general B,d CONJECTURED (5,592 + 49 cells Γ = 0) | same |
| C-8 | Lemma Zc: promotion event monotone in queried labels in query order ⇒ causal risk = IID risk (strictly larger class than tape-monotone) | PROVED (agent); 0 violations in 1,233 plans | same |
| C-9 | "TP2 or (M) violated ⇒ Γ > 0" | FALSIFIED (Γ>0 in only 6.6% of TP2-violating B=1 cells; 1.3% of (M)-violating B≥2 cells) | same |

## theory_v2 status update (2026-11-10, appended; rows above unchanged)

| ID | Statement | Status after theory_v2 | Evidence |
|---|---|---|---|
| R / R′ / Zc / P | Lagrangian reduction; query-order coupling; promote only at q > 1/2 | PROVED (re-audited); PRIOR ART in substance (LP duality + sequential stochastic domination) | `theory_v2/THEOREM_PROOF_AUDIT.md`, `PRIOR_ART_AUDIT.md` |
| Z1 / W / W* | B=1 zero premium | PROVED (re-audited; W* sharpening) | same |
| N1 | Exact Γ, B=1, any HMM, α ≤ 1/2 | PROVED (independent re-implementation 1,905/1,905); α ≤ 1/2 necessary | same |
| N1-cap | Γ ≤ (C₀ − V*_IID)/2 at B=1 | PROVED (elementary corollary; lead-verified) | `theory_v2/REVIEW_SIGNIFICANCE.md` |
| C3″ | Alternation: Γ = α·min{(g−k)/2−c, g−2k} (even T ≥ 4); α((g−k)/2−c) at T=2; odd T ⇒ 0 | PROVED; C3′ FALSIFIED at T=2 (CE-13) | `THEOREM_PROOF_AUDIT.md` |
| S0 | Static alternative, c = 0, any T,B,d,k,α ⇒ Γ = 0 | PROVED (reviewed, minor corrections) | `MULTILABEL_ZERO_PREMIUM.md`, `REVIEW_S0.md` |
| S+ | Static, c > 0, B ≥ 2 ⇒ Γ = 0 | CONJECTURED (0 counterexamples, ≈42k cells); irreducible lemma stated | `MULTILABEL_ZERO_PREMIUM.md` |
| Z2 / U-M | Symmetric stationary persistent (or TP2 + M_marg) ⇒ Γ = 0 | FALSIFIED for every α (CE-12) and at α ≤ 1/2 (CE-14, B ≥ 4) | same |
| SP1 | Exact closed-form Γ, symmetric anti-persistent, B=1, any d,c,k | PROVED (reviewed; SP1-D corrected at T=d+1, CE-18) | `STOCHASTIC_POSITIVE_PREMIUM.md`, `REVIEW_SP1.md` |
| SP1 corollaries | even d ⇒ 0 (B=1); open region for odd d; horizon-uniform lower bound; decay r^d; mixing limit | PROVED (B=1); "even d ⇒ 0" FALSIFIED at B=2 (CE-15) | same |
| Struct | Four-mechanism characterisation | PROVED components + NUMERICALLY VERIFIED taxonomy; not a theorem | `STRUCTURAL_CHARACTERIZATION.md` |
| G-A | t=1, d=1, c=k=0, T ≥ 2B: Γ ≤ (1−2e)(B+1); ρΓ → 0 as T → ∞ at fixed B | PROVED (agent, unreviewed); Γ constant 0.032 in T at B=2 lead-verified | `theory_v2/GENERAL_B_PREMIUM.md` |
| G-V | t=1: Γ ≤ ((1−2e)/2)(K_α + T·π_B); sup_T ρΓ → 0 as B → ∞ at fixed α | PROVED (agent, unreviewed) | same |
| G-R | Causal-risk recursion for fixed-calendar events; pattern risk 2^−#ones; fixed calendars not WLOG for V*_causal | PROVED / NUMERICALLY VERIFIED; PRIOR ART in substance | same |
| Decision | theory_v2 publication decision | main-track NO-GO (too narrow) | `theory_v2/PUBLICATION_DECISION.md` |
| M1 | Mixing chain, B=1, odd d, α ≤ 1/2: ρΓ α-free, uniform in T, lim (1−r)/2 (k=c=0) | PROVED; reviewed (accepted) | `theory_v2/MIXING_PREMIUM_THEOREM.md`, `REVIEW_MIXING.md` |
| M2 | VOI nondecreasing in T, ≤ α·U_B; ρΓ → 0 iff Γ/α → 0 | PROVED; reviewed (accepted) | same |
| M3 | First-label relaxation lower bound on Γ (symmetric stationary family) | PROVED; reviewed (accepted; scope corrected) | same |
| M4 | B=2, k=0, odd d, small c, T ≥ T₀: liminf ρΓ ≥ (1−r)/(2(3+r)) | PROVED; reviewed (accepted with corrections) | same |
| M5 | ρΓ ≤ 1 − H_∅/S_I | PROVED; reviewed (accepted) | same |
| M-gen | General B: ρΓ bounded below uniformly in T | CONJECTURED; B=3,4 data still falling at T=12 | `MIXING_SCALING.md` |
| Salvage | Locked-criteria outcome | OPEN (neither CONDITIONAL GO nor NO-GO applies) | `theory_v2/PUBLICATION_DECISION.md` |
