# HKUSTDial idea-evaluator: "The price of full-history causal safety" (WP C)

Skill: `idea-evaluator` (HKUSTDial), invoked natively on 2026-11-10. The evidence is `CAUSAL_SAFETY_PREMIUM_THEORY.md`
(lead-verified numerically: C3 at T=4 and T=6, CE-6) and `LITERATURE_NOTES.md`. The proofs have not yet been reviewed
(WP G is in progress).

## 1. First impression

- **Paper type:** New Setting (theory). The paradigm is theoretical derivation plus exact computation, so the STEM
  framework applies.
- **One-sentence story:** calibrating a promotion gate against an i.i.d. null instead of the full adaptive null is
  free exactly when the economically optimal promotion events are monotone in evidence; reversal-predictive regimes
  carry a strictly positive, computable price.

## 2. Fatal-flaws audit

| # | Flaw | Severity | Defense |
|---|---|---|---|
| 1 | **Significance / narrowness.** The proved zero-premium theorem (Z1) needs B=1. The proved positive family (C3) is a single hand-built alternating chain with Γ constant in T. Observed premiums are small (1.3e-4 to 4.2e-2). A main-track reviewer will call this a special case. | MAJOR (not CRITICAL: fixable if the multi-label Lemma U is proved and the positive side generalises) | Prove Lemma U (the multi-label swap) or find its counterexample. Turn Γ > 0 into a condition-based theorem (a violation of (M) or of TP2 ⇒ Γ > 0, with a magnitude bound) rather than one family. |
| 2 | **Novelty (F1).** Monotone and threshold optimality under TP2/MLR is classical (Krishnamurthy tutorial arXiv:1512.03873, read; Lovejoy 1987, not re-read). The repo already proves monotone event ⇒ causal risk = IID risk. Z1 may be "known structure + known coupling". | MAJOR | Retrieval (`LITERATURE_NOTES.md` Q1/Q2) found no constrained, delayed-observation, adaptive-null comparison: "no directly overlapping work retrieved under these keywords", which does not prove novelty. The delta must be the *constrained Lagrangian* plus *delayed, budgeted sensing* plus the *adaptive-null* gap, stated precisely. |

No CRITICAL flaw, so the evaluation continues.

## 3. Lifecycle and capability

| Aspect | Input | Assessment |
|---|---|---|
| Category | Foundational theory | Long lifecycle; low competition risk |
| Capability | Exact solver + certificates exist; theory agent produced proofs | Green for computation; Yellow for proof generality (Lemma U is open) |
| Fit | — | **Yellow** |

## 4. Five-dimension radar

| Dimension | Score | Evidence | Lift |
|---|---|---|---|
| Higher | 5 | No accuracy gain claimed; the value is characterisation | — |
| Faster | 6 (mechanism-based, not yet confirmed) | Where Γ = 0 provably holds, the IID LP plus a 56–72-state verifier certifies the optimum without the null tree. FCG-fast's T=10 speed-up (unattributed) rides on this | A primitive-condition test that *predicts* Γ = 0 before solving |
| Stronger | 7 (mechanism-based) | Identifies when i.i.d.-calibrated gates are unsafe or suboptimal under adaptive nulls (CE-6 shows TP2 + MLR is not enough) | Necessity of (M); magnitude bound |
| Cheaper | 5 | No grounds given | — |
| Broader | 4 | Specific to two-law switching with a 2-state HMM | Connect to anytime-valid sequential testing (Q2 literature) |

## 5. Paradigm-shift probe

| Probe | Answer | Rationale |
|---|---|---|
| First principles | Yes | Challenges the hidden assumption that i.i.d.-null calibration is the right gate design target |
| Elephant in the room | No | — |
| Technology cycle | No | — |
| Hamming | No | Γ is small on the tested cells |

Disruptive potential: none to possible.

## 6. Feasibility

| Risk | Level | Mitigation |
|---|---|---|
| Compute | Low | Exact small cells take minutes |
| Data | Low | Synthetic only |
| Engineering | Low | Harness exists |
| Timeline / proof | **High** | Lemma U may be false. Bound the effort: one exhaustive counterexample search at T ≤ 6, B ≤ 3, then a proof attempt |

## 7. Verdict

**Accept with Revisions**: worth pursuing only as a scoped theory note, pending the validation step. In its current
form (B=1 plus one family) it does not meet a main-track bar.

Top three actions:
1. Prove or refute Lemma U (multi-label zero-premium) with an exhaustive search over symmetric and asymmetric TP2 cells.
2. State and test the necessity direction: (M) or TP2 violated ⇒ Γ > 0 generically, with a magnitude bound.
3. Finish the WP G proof review of Z1 and C3 before any further investment.
