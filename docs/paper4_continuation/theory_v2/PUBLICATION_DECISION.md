# Paper 4 theory_v2 — publication decision

**Date:** 2026-11-11. **Branch:** `research/paper4-causal-premium-theory-2026-11-10` (HEAD at writing `95e6151d`).
**Decision owner:** lead (Opus 5.5). Reviews are same-family / provisional (BL-1). Outcomes are main-track only
(`AGENTS.md` publication-outcome rule).

## Decision: **NO-GO — existing results too narrow**

No substantial new theorem survived correctness and novelty review. The proved results that pass correctness review
are confined to one label (N1, SP1, Z1/W) or to static evidence with free labels (S0). Each reduces to known
machinery (LP duality over mixed plans, sequential stochastic domination, single-observation composite testing,
geometric sums). The only general-budget direction the data supported, a relative premium that grows with budget,
was examined in a bounded theorem attempt. Where it could be analysed (deterministic alternation), the relative
premium was proved to vanish as horizon or budget grows (Thm A, Thm V; unreviewed). The rise seen at T ≤ 10 is a
finite-resource effect.

## Answers to the directive's ten questions

| # | Question | Answer |
|---|---|---|
| 1 | Are Z1 and C3 correct? | **Z1: yes** (re-audited; sharpened to W*). **C3: the original formula is wrong**; C3′ is wrong at T = 2; the correct form C3″ is proved and verified (468/468 cells; odd T ⇒ Γ = 0 now proved) |
| 2 | What is already prior art? | Lemma R/R′, Zc, P and S1: LP duality over mixed plans (Walraven–Spaan) plus sequential stochastic domination (Doerr §1.8; Strassen). The B = 1 results are single-observation composite tests combined by an LP over query times (Karlin–Rubin-type MLR, cited from memory). The definition of Γ is an instance of Fauß–Zoubir–Poor's rectangular history-adaptive null families; the gap to the IID point is not studied there. General-B mechanisms reduce to Fauß–Zoubir–Poor, Waudby-Smith–Ramdas betting and Ville's inequality. See `PRIOR_ART_AUDIT.md`, `GENERAL_B_PREMIUM.md` T4 |
| 3 | Is the multi-label zero-premium conjecture true? | **No.** Symmetric stationary persistent ⇒ Γ = 0 fails for every α (CE-12, α = 25/32) and at practical α (CE-14: Γ = 1.28e-4 at α = 5/16; Γ > 0 down to α = 21/128). TP2 + M_marg ⇒ Γ = 0 fails as well |
| 4 | Smallest counterexample; strongest surviving restricted theorem? | Smallest at α ≤ 1/2 with B = 4: T = 8, B = 4, d = 2, t = 1/4, e = (1/1000, 999/1000), stationary prior, c = k = 0 (lead-verified). Strongest surviving restricted theorem: **S0**, static alternative with free labels (c = 0) ⇒ Γ = 0 for any T, B, d, k, α (reviewed; minor corrections). Static with c > 0 and B ≥ 2 is an open lemma (S+; no counterexample in about 42k cells) |
| 5 | Can the positive premium be extended to stochastic HMMs? | **Yes at B = 1:** SP1 gives an exact closed form for symmetric anti-persistent chains with t ∈ (1/2, 1], any d, c, k (reviewed: 2,420/2,420 adversarial certified cells; one corollary corrected at T = d + 1). Positive iff d is odd and costs are small; it decays like r^d. **At B ≥ 2:** only identity bounds; "even d ⇒ Γ = 0" fails at B = 2 (CE-15); Γ is non-monotone in B and in k |
| 6 | Is there a structural characterisation linking both sides? | A qualitative one. Score monotonicity of P_A(y)G(y)⁺ organises every positive cell found into four mechanisms: exchangeable evidence (free, proved), sign-reversing evidence (priced, exact at B = 1), correlated coin, and persistence flip penalty (witnesses only). It is a taxonomy, not a theorem: sufficient, not necessary (50/103 non-monotone cells still have Γ = 0), and not proved exhaustive (`STRUCTURAL_CHARACTERIZATION.md`) |
| 7 | Does it establish a new mathematical result? | No new result at main-track level. The non-routine content is short: S0's G/D induction, SP1's shared-window case analysis and odd-d parity, the B = 1 ceiling Γ ≤ (C₀ − V*_IID)/2, and Thm A/V (unreviewed). Each is a specialisation of known machinery |
| 8 | Are the assumptions natural and practically meaningful? | Partly. α ≤ 1/2, the adaptive null class and static exchangeable evidence are natural. B = 1 is a degenerate budget; free labels (S0) is a convenience assumption; anti-persistence with odd release lag (the proved positive driver) has no practical motivation in the files |
| 9 | Significant enough for ICML/NeurIPS/ICLR? | **No.** The significance review scored it 3/10 as it stands. The one result that could change this (a non-vanishing relative premium as T, B grow) was attempted and points the other way at deterministic alternation |
| 10 | What remains unproved or unsupported? | Lemma S+ (static, c > 0, B ≥ 2). A lower bound on the relative premium for t < 1 (conjectured to vanish too, unproved). Independent review of Thm A, Thm V and Lemma A. Mechanisms M2/M3 as theorems. Exactness of fixed-calendar values for T − B ≥ 5 (they are upper bounds there). The (T, B) = (9, 6) cell in the general-B grid did not certify. All evidence is synthetic with T ≤ 14; there is no real-data or deployment-stream evidence |

## Closure of the mandatory work packages

| WP | Outcome | Evidence |
|---|---|---|
| A | Verified: all prior proofs survive; C3′ corrected to C3″ | `THEOREM_PROOF_AUDIT.md` |
| B | Conjecture falsified (incl. α ≤ 1/2); restricted theorem S0 proved; irreducible lemma S+ stated | `MULTILABEL_ZERO_PREMIUM.md`, `REVIEW_S0.md` |
| C | SP1 proved (B = 1); B ≥ 2 bounds only; relative-premium scaling measured; general-B attempt negative | `STOCHASTIC_POSITIVE_PREMIUM.md`, `REVIEW_SP1.md`, `RELATIVE_PREMIUM_SCALING.md`, `GENERAL_B_PREMIUM.md` |
| D | Qualitative characterisation; no unified theorem | `STRUCTURAL_CHARACTERIZATION.md` |
| E | Root-mixture verified; A3 read (no FCG gain); FCG kept as the reference oracle; ledgers reconciled | `ENGINEERING_COMPLETION.md` |
| F | Every result reduces to known mechanisms | `PRIOR_ART_SOURCES.md`, `PRIOR_ART_AUDIT.md` |
| G | Three review roles completed (correctness ×3, novelty, significance) | `REVIEW_REPORT.md` and `REVIEW_*.md` |
| H | No manuscript (no main-track candidate survived); `tech-paper-template` / `pre-submission-reviewer` not run for that reason | this file |

**Not done, with reasons:** a cross-family review (BL-1, no backend loaded); a manuscript (decision is NO-GO).
