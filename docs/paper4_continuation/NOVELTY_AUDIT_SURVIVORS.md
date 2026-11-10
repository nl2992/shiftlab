# WP E — Source-grounded novelty audit of surviving results

**Method.** This follows the ARIS `novelty-check` protocol, but with a substitution: its reviewer slot (Codex/GPT)
is **BLOCKED** (BL-1). Sources come from `LITERATURE_NOTES.md` (HKUSTDial deep-research method; read status recorded
per source) and the primary texts the lead read: Krale et al. pp. 1–9; Bošanský et al. pp. 829–831; and the
existence and abstract of Krishnamurthy arXiv:1512.03873. Classifications: PROVED EQUIVALENT, PROVED DISTINCT,
PARTIAL OVERLAP, COUNTEREXAMPLE TO REDUCTION, UNRESOLVED.

## Surviving results (after WP G corrections)

| ID | Result | Status |
|---|---|---|
| R | Lemma R: value-level monotone-Lagrangian ⇒ Γ = 0 | PROVED, reviewed |
| Z1/W | B=1 zero premium under condition W (TP2 + (M) ⇒ W) | PROVED, reviewed |
| N1 | Exact Γ formula for B=1, any HMM | PROVED (agent); 2,000/2,000 cells |
| S1 | Static alternative ⇒ Γ = 0, B=1 | PROVED (agent) |
| Zc | Query-order monotone promotion class ⇒ causal = IID risk | PROVED (agent) |
| C3′ | Corrected separation family `Γ = α·min{(g−k)/2−c, g−2k}` | Corrected, NUMERICALLY VERIFIED |
| U | Multi-label zero premium (TP2 + (M) ⇒ Γ = 0) | CONJECTURED (12,060 cells) |
| B1-S | Tree-free certified `V*` for a static alternative | PROVED (agent); lead-verified |

## Comparisons

| Result | Closest source (read status) | Relation | Classification |
|---|---|---|---|
| R | Constrained-MDP Lagrangian/LP duality (Altman; *memory, unverified*) + repo monotone coupling lemma | Composition of a standard duality step and an existing repo lemma | PROVED EQUIVALENT (to the standard steps) |
| Z1/W | Krishnamurthy tutorial (existence and abstract read; theorem statements per the literature agent): monotone threshold stopping for *unconstrained, undelayed* TP2 stopping POMDPs | Z1 is a constrained, delayed, B=1 case. The exchange compares two numbers (reviewer). MLR preservation under a TP2 kernel is textbook | PARTIAL OVERLAP (the setting is not covered; the mechanism is standard) |
| N1 | No source found for an exact robust-vs-nominal premium in single-query sequential designs (Q2(c)) | Elementary enumeration of the four single-query strategies | UNRESOLVED as novelty; mathematically elementary |
| S1 | Neyman–Pearson / likelihood-ratio monotonicity (standard) + repo coupling | Static exchangeable case | PROVED EQUIVALENT in substance |
| Zc | Repo monotone reduction (tape-monotone) | Strictly larger class via query-order coupling; same proof technique | PARTIAL OVERLAP (an extension of an in-repo lemma) |
| C3′ | Bertsimas–Sim price of robustness (static; per the literature agent) | Sequential, adaptive-null analogue with an exact value. One hand-built family | UNRESOLVED as novelty; the reviewer and the idea-evaluator both call it an *example* |
| U | No source found (Q2(c)) | Unproved | Not assessable until proved |
| B1-S | Walraven & Spaan column generation (read by the literature agent, §§ theorems) + sufficient statistics + repo reduction | A standard combination | PROVED EQUIVALENT |

## Conclusion

No surviving result is both proved and source-distinct at the level of a main-track contribution. The best
candidate is the **characterisation of the causal-safety premium Γ** (R, Z1/W, N1, Zc, C3′, plus the falsification
of TP2 + MLR ⇒ Γ = 0 at B=1). Its setting appears uncovered (Q2(c), searched one to three times per sub-topic, so
absence is not proof). Its mechanisms, however, are standard, and its general multi-label statement (U) is unproved.

**Classification of the programme's best result: UNRESOLVED novelty / PARTIAL OVERLAP; not main-track as it stands.**
