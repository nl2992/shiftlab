# Theorem registry

Statuses: PROVED · FORMALLY CHECKED · NUMERICALLY VERIFIED · EMPIRICALLY SUPPORTED · CONJECTURED · FALSIFIED ·
PRIOR ART · BLOCKED · NOT STARTED.

| ID | Statement | Status | Evidence |
|---|---|---|---|
| P4-1 | Causal recursion and surcharge identity | PROVED; NUMERICALLY VERIFIED; PRIOR ART (Krale et al. 2025) | `docs/paper4/theory/01` |
| P4-2 | FCG correctness (`L <= V* <= U`, finite termination) | PROVED; PRIOR ART (scheme) | `docs/paper4/theory/01` §4 |
| P4-3 | Monotone-event IID reduction | PROVED (repo, 2026-10-28) | `docs/switching_monotone_promotion_reduction_v1.md` |
| C-1 | Lemma R (value-level: monotone Lagrangian minimisers for all λ ⇒ Γ=0); Theorem Z1 (B=1, TP2, MLR, (M) P_A(Y_τ=1)≥1/2 ⇒ Γ=0) | PROVED (agent); NUMERICALLY VERIFIED; proof review pending (WP G). General TP2+MLR ⇒ Γ=0 FALSIFIED at B=2 (Γ=657/5000000, lead-verified). Multi-label Lemma U CONJECTURED (1,200 symmetric persistent cells Γ=0) | `CAUSAL_SAFETY_PREMIUM_THEORY.md` |
| C-2 | Theorem C3: alternating chain t=1, B=1, d=1, T even ≥4 ⇒ Γ = α[(g−k)/2 − c], g=(1−2e)², T-invariant (odd T: Γ=0) | PROVED (agent); exact closed form checked 324/324 (agent) and at T=4,6 by lead vs FCG and reference; proof review pending. Not growing in T | `CAUSAL_SAFETY_PREMIUM_THEORY.md` |
| C-3 | Repair bound Γ ≤ (1−q)(C0 − V*_IID); monotone-restriction bound (tight on C3 family) | PROVED; repair bound loose by O(T); monotone bound is a corollary of the existing coupling lemma → NO-GO standalone | `CAUSAL_SAFETY_PREMIUM_THEORY.md` |
| C-4 | Adaptivity gap | IID: best calendar = adaptive in 13/13 cells; causal: single-calendar gap 5.797e-4 in one cell, closed exactly by private mixing over calendars → value of randomisation, NOT label-adaptive design → NO-GO (not new) | `CAUSAL_SAFETY_PREMIUM_THEORY.md` |
| B-1 | Implicit policy-column generation | NO-GO computational for HMM alternatives (pricing state = public tree: 65/65, 236/236, 848/848, 91/91); calendar-restricted pricing gives invalid LBs (8/10 cells above V*) | `IMPLICIT_LEARNER_OPTIMIZATION.md` |
| B-1S | Theorem B1-S: static (exchangeable) alternative ⇒ exact IID-row pricing on keys (t, last d−1 query bits, n1, n0), ≤ T·2^(d−1)(B+1)(B+2)/2 keys; L = V*_IID; certified V* whenever mixture risk ≤ α (49/49 cells, T up to 24) | PROVED (agent); NUMERICALLY VERIFIED (lead: 5 cells equal reference V* exactly); PRIOR ART (sufficient statistic + Dantzig–Wolfe + monotone reduction); static regime is degenerate shift | `IMPLICIT_LEARNER_OPTIMIZATION.md` |
| B-2 | Grid-refinement certificate L ≤ V* ≤ U | NO-GO prior art; LB stalls at IID optimum on reversal cells (C2 2.4002 vs 2.4419); kept as baseline | same |
| B-3 | Certified distillation | NO-GO prior art/computational (coupling product contains teacher tree); v1–v3 students collapsed to never-promote (recorded failures) | same |
| B-4 | Dual / first-promotion stopping reduction | NO-GO prior art/correctness (stopping on (belief,budget,t) false under alias counterexample) | same |
| D-1..D-4 | Fallback candidates | NOT STARTED | — |
