# HKUSTDial tech-paper-template: can the safety-premium result carry a paper?

Skill: `tech-paper-template` (HKUSTDial), invoked natively on 2026-11-10. Inputs are the surviving results after WP G
corrections (`NOVELTY_AUDIT_SURVIVORS.md`).

## 1. Paper type

- **Type:** New Problem/Setting paper.
- **Rationale:** the contribution would be the *question* "what does full-history adaptive-null safety cost
  relative to i.i.d. calibration?" plus its characterisation, not a new algorithm. The algorithm (FCG) is prior art.

## 2. Thinking template

| Stage | Content |
|---|---|
| Research background | Model-promotion gates calibrated against an i.i.d. null; deployed systems face adaptive, history-dependent label processes; budgeted, delayed labels |
| Limitation 1 | Sequential and anytime-valid tests (e-processes, confidence sequences) control error under adaptive nulls, but the *economic* cost of that control relative to i.i.d. calibration in constrained sensing is not quantified (`LITERATURE_NOTES.md` Q2(c); not found ≠ absent) |
| Limitation 2 | Monotone/threshold structure (TP2/MLR) covers unconstrained, undelayed stopping only (Krishnamurthy tutorial) |
| Our Goal | Characterise exactly when i.i.d. calibration is free (Γ = 0) and what it costs otherwise (Γ > 0) |
| Challenge 1 | The optimal constrained policy is randomised and may be non-monotone in labels |
| Challenge 2 | Delayed, budgeted, adaptive querying breaks the textbook TP2 exchange arguments |
| Challenge 3 | Γ must be computed and certified exactly to test conjectures |
| Module A (C1) | Lemma R (value-level monotone Lagrangian ⇒ Γ = 0) + Zc (query-order monotone class) |
| Module B (C2) | Z1 under condition W (B=1); N1 exact Γ for B=1; **multi-label case: unproved (Lemma U)** |
| Module C (C3) | Certified exact solver (FCG + exact dual) as a measurement instrument; 27,648-cell exhaustive search |
| Contribution 1 | Formulation of Γ and Lemma R/Zc (Sec. 3) |
| Contribution 2 | Exact single-query theory: Z1/W, N1, S1; the B=1 counterexample to TP2+MLR ⇒ Γ = 0 (Sec. 4) |
| Contribution 3 | Separation family C3′ and the exhaustive empirical map of Γ (Sec. 5) |

## 3. Self-consistency checks

- **Check 1, Limitations → Goal: PASS.** The goal addresses both limitations.
- **Check 2, Goal → Challenges: PASS.** The challenges arise from characterising Γ in this model.
- **Check 3, Challenges → Methodology: FAIL (CRITICAL).** Challenge 2 is answered only for **B = 1**. The general
  multi-label case, which is the case that matters for budgeted sensing, has no proved module (Lemma U is
  conjectured). That leaves a challenge without a fix.
- **Check 4, Methodology → Contributions: FAIL (CRITICAL for main track).** Contribution 2 is exact but limited to a
  single query, where the reviewer notes the exchange "compares two numbers". Contribution 3 is one hand-built family
  plus numerics. The contributions promise a characterisation the methodology delivers only in the degenerate
  single-query case.

## 4. Severity summary

- **Findings:** 2 CRITICAL, 1 MAJOR (novelty partial overlap, `NOVELTY_AUDIT_SURVIVORS.md`), 0 MINOR.
- **Verdict:** the skeleton **does not hold together as a main-track paper.** It holds together only as a
  characterisation *section* or a short note scoped to B=1 plus empirical evidence for B ≥ 2.
- **Top fixes (each is a research task, not a writing task):**
  1. Prove Lemma U (interior subtree exchange) or find its counterexample.
  2. Give a Γ > 0 lower bound for general B beyond one family.
  3. Settle novelty by reading the e-process / anytime-valid cost literature in full.

## 5. Next suggested skill

Do **not** run `intro-drafter`. Address the CRITICAL chain breaks first.
