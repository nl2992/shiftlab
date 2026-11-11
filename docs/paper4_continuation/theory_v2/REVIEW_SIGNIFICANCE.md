# Review 3: scientific significance of the causal-safety premium Γ programme (theory_v2)

**Date:** 2026-11-10. **Reviewer:** Reviewer 3 (scientific significance). Fresh-context Opus 5.5 subagent acting as a
skeptical ICML/NeurIPS/ICLR theory reviewer.
`review_independence: same-family` · `acceptance_status: provisional`.
**Rubric:** ARIS `research-review` (`.agents/skills/research-review/SKILL.md`). Its Codex/GPT reviewer backend is
unavailable (BL-1), so this is the native same-family substitute. Format: Summary, Strengths, Weaknesses, Questions,
Score, then a mock-review "what would move toward accept". The HKUSTDial `idea-evaluator` skill was invoked natively on
the strongest candidate (§6).
**Novelty status:** `PRIOR_ART_AUDIT.md` did not exist when this review was finished. Novelty judgements below are
therefore **provisional**. They rest on `PRIOR_ART_SOURCES.md` (WP F retrieval, verdict vocabulary only) and on
`NOVELTY_AUDIT_SURVIVORS.md`.

**Files read in full or in the sections cited:**
- theory_v2: `MASTER_PLAN.md`, `THEOREM_PROOF_AUDIT.md` (§0–1, §7–9, lead verification), `MULTILABEL_ZERO_PREMIUM.md`
  (§0–2 header, §8, follow-up F.1–F.4, lead verifications), `REVIEW_S0.md` (§0–1, §4), `STOCHASTIC_POSITIVE_PREMIUM.md`
  (§0–1, §3, §5–8, lead verification), `STRUCTURAL_CHARACTERIZATION.md`, `ENGINEERING_COMPLETION.md` (E1–E4),
  `PRIOR_ART_SOURCES.md` (§0, §3, §5–7), `RESEARCH_LEDGER.md`;
- background: `CAUSAL_SAFETY_PREMIUM_THEORY.md` (§0–1, §4–8, F5), `NOVELTY_AUDIT_SURVIVORS.md`,
  `PAPER_SKELETON_CHECK.md`, `IDEA_EVALUATION_C.md`, `docs/paper4/publication/PUBLICATION_DECISION.md`.

I re-ran no computation. Every number below is quoted from those files. Where I derive something myself, I say so.

---

## 1. Summary of the submission (as a reviewer would reconstruct it)

The package studies a finite-horizon two-law switching game. A hidden two-state Markov chain emits Bernoulli labels. A
learner chooses when to query a label (budget B, delay d, cost c) and when to promote a challenger (switch cost k).
Risk is the probability of a first promotion. It is calibrated either against the IID Ber(1/2) null (`V*_IID`) or
against every adaptive causal null with `p_t ∈ [0,1/2]` that sees the full history (`V*_causal`). The object is the
**causal-safety premium Γ = V*_causal − V*_IID ≥ 0**: the economic price of certifying against the adaptive null
instead of the IID null.

**Claimed results and their audited status:**

| Result | Content | Status (from files) | Depth (reviewer's view) |
|---|---|---|---|
| Lemma R, R′, Zc | Monotone promotion events have causal risk equal to IID risk; a monotone Lagrangian support gives Γ = 0 | PROVED; audit calls them "routine corollary of LP duality, Kuhn and monotone coupling" | Routine |
| Z1 / W / W\* | B = 1 zero premium under TP2 + (M) | PROVED | Routine (one exchange of two numbers) |
| **N1** | Exact Γ = α(2 max_τ g_z0(τ) − r_c)⁺ for B = 1, any HMM, α ≤ 1/2 | PROVED; 1,905/1,905 cells in an independent implementation; α ≤ 1/2 shown necessary | Elementary but a complete characterisation within B = 1 |
| S1 | Static ⇒ Γ = 0 at B = 1 | PROVED | Routine |
| **S0** | Static alternative, c = 0, any T, B, d, k, α ⇒ Γ = 0 | PROVED with minor corrections (`REVIEW_S0.md`) | Reviewer 1: "roughly 80% routine reductions", one elementary induction |
| **SP1** | Closed-form Γ for symmetric stationary anti-persistent chains, B = 1, any d, c, k; zero for even d; ~ r^d decay | PROVED (same-family, Lemmas W, K, Pre not independently reviewed); 5,400/5,400 certified cells | Specialisation of N1 with clean algebra |
| Counterexamples | TP2+MLR ⇒ Γ=0 false (B=1 and B=2); symmetric stationary persistent ⇒ Γ=0 false at B ≥ 4, down to α = 21/128; "even d ⇒ Γ=0" false at B ≥ 2; Γ non-monotone in B, α, k | Certified in exact rationals and re-computed by the lead | Most interesting scientific content |
| WP-D taxonomy | Four mechanisms M0–M3, organised by score monotonicity of s(y) = P_A(y)G(y)⁺ | PROVED components + NUMERICALLY VERIFIED taxonomy; explicitly "not a unified theorem" | Qualitative |

Experiments are exact certified computations on synthetic cells with T ≤ 10 (most T ≤ 8) and B ≤ 7.

---

## 2. Strengths

1. **The question is well posed and honest.** Γ is defined as a value gap between two constrained optimisation
   problems over the same learner class. It is ≥ 0 by construction, and it is computed with certified bounds
   (`L_causal − U_IID > 0` in exact rationals). WP F found no source that computes the gap between an IID-calibrated and
   an adaptive-null-calibrated optimal sequential design (`PRIOR_ART_SOURCES.md` §7, query (ii)). The closest objects
   are minimax sequential tests over rectangular families (Fauss–Zoubir–Poor 2020), which compute the robust value but
   not the gap to a nominal member.
2. **The B = 1 theory is complete.** N1 is an exact formula for every HMM at α ≤ 1/2. The scope is shown sharp: N1
   fails for α > 1/2 in 40 red-team cells. It is verified by an independent implementation (1,905/1,905). SP1 makes it
   interpretable: parity in d, geometric decay `r^d`, T-saturation, and the non-intuitive "switching cost can raise Γ".
3. **Verification discipline is unusually high.** There are independent re-implementations, exact rational
   certificates, a lead re-computation of every headline counterexample, and corrections recorded rather than hidden
   (C3′ → C3″, the false "tape ⊂ z" claim, the old root-mixture defect in E1).
4. **The negative results are scientifically informative.** The natural conjecture "persistence (TP2) + balanced
   marginals ⇒ IID calibration is free" is false once B ≥ 4, at practical α (CE-B2: Γ > 0 at α = 9/32, 5/16, 1/2;
   symbig: down to α = 21/128). The mechanism is identified concretely: persistence lowers the likelihood of histories
   with isolated flips, so the Neyman–Pearson leaf ranking is not an up-set. This is a real "the intuition is wrong"
   finding.
5. **My own corollary of N1 suggests the premium is not negligible relative to the information value.** It follows
   from N1 as stated and is not in the files. Since `r_c ≥ max_τ g_z0(τ)`, we get
   `Γ = α(2 max g_z0 − r_c)⁺ ≤ α·max g_z0 ≤ α·r_IID/2 = (C_0 − V*_IID)/2`. So at B = 1 the premium can be up to half
   the IID value of the label-driven plan, but never more. That is a clean, interpretable ceiling a paper could state.
   Nobody has checked whether it is attained.

## 3. Weaknesses

**W1. Significance and audience (MAJOR).** The setting is a stylised two-state HMM with Bernoulli labels, one
promotion decision and tiny horizons. The question "what does adaptive-null certification cost?" is relevant in
principle to anytime-valid inference, safe deployment and model-promotion gates. As posed, however, it speaks to a
narrow robust-sequential-decision audience. Nothing connects Γ to a decision an ML practitioner makes: for example,
"use an e-process gate instead of an IID-calibrated gate, and lose at most X". The research charter's Paper 1–3
framing (decision harm under shift) is not linked to any data.

**W2. Absolute magnitudes are small (MAJOR for the "economic price" framing).**
- CE-C2a: Γ = 1.314e-4 against `V*_IID ≈ 1.676`, about 0.008%.
- CE-B1: Γ ≈ 2.09e-3 against `V*_IID ≈ 1.017`, about 0.2%.
- The largest reported value at α ≤ 1/2 is 0.052 (T = 9, B = 6).
- SP1 values are `Γ/α ≈ 0.1` at α = 1/10.
- B ≥ 2 positive cells are rare in random persistent grids: 2/1,200 asymmetric TP2 cells, and 53/5,142 symmetric
  cells in the hull-targeted scan.
A reviewer will read this as "IID calibration is almost free, except in contrived regimes". The relative bound in
Strength 5 helps only if it is attained in natural cells.

**W3. The theorems are either routine or restricted (MAJOR; this is the core issue).**
- R, R′, Zc, Z1, S1 and P are routine by the audit's own labels (`THEOREM_PROOF_AUDIT.md` §9).
- N1 is an enumeration of four single-query design types ("compares two numbers").
- SP1 is algebra inside N1 for one symmetric family.
- S0 is the only multi-label positive statement, and its hypotheses (static θ, exchangeable labels, free queries) are
  the case where the adaptive null *obviously* has nothing to exploit. Reviewer 1 rates it 80% routine.
- **No theorem covers B ≥ 2 for any non-static alternative.** That is exactly where the interesting phenomena (M3)
  live. `PAPER_SKELETON_CHECK.md`'s CRITICAL chain break ("Challenge 2 answered only for B = 1") is therefore
  narrowed by S0 but not removed.

**W4. Assumption naturalness.**
- *B = 1 (N1, SP1):* degenerate for budgeted sensing. One label makes every policy a choice among four designs.
  Reviewers will treat it as a toy, and SP1's own data show B = 1 conclusions do not transfer: even d ⇒ Γ = 0 fails at
  B = 2, and Γ is non-monotone in B.
- *Static + free labels (S0):* natural as a sanity anchor (stationary A/B evidence), but it is the trivial end of the
  spectrum. The c > 0 extension (Lemma S+) is open, though 0 failures in roughly 42,000 cells.
- *Symmetric stationary chains:* reasonable as a canonical family. Persistent ones *refute* the zero-premium
  conjecture; anti-persistent ones are proved only at B = 1. Anti-persistence with odd release lag (the M1 driver) is
  a regime ML deployments rarely exhibit, and the package offers no evidence that it occurs.
- *α ≤ 1/2:* natural.
- *Null class `p_t ∈ [0,1/2]`, adapted to the full history including pending labels:* natural (rectangular,
  conditional-mean type; `PRIOR_ART_SOURCES.md` §3.3, §5.4).
- *Reversible promotion:* used essentially by SP1 (§7, "reversibility"). An irreversible variant was not analysed.

**W5. The structural characterisation is a taxonomy, not a theorem (MAJOR).** WP-D says so itself (§4–5): no
necessary-and-sufficient primitive condition for B ≥ 2, M2 and M3 identified from witnesses only, and no claim that
the four mechanisms are exhaustive. The organising quantity, score monotonicity of `P_A(y)G(y)⁺`, is textbook
Neyman–Pearson (`CAUSAL_SAFETY_PREMIUM_THEORY.md` §7 says so). It does explain every positive cell found, and that is
useful. But a theory reviewer will see "sufficient condition = NP region is an up-set" as the expected statement, and
WP-B shows it is not even necessary (50/103 flagged cells still have Γ = 0).

**W6. Matching bounds.**
- *B = 1:* exact (upper = lower).
- *B ≥ 2:* only the identity sandwich `Γ(1) − [V_c(1) − V_c(B)] ≤ Γ(B) ≤ Γ(1) + [V_I(1) − V_I(B)]`, and the
  monotone-restriction bound (tight on the C3 family, loose by a factor 2 elsewhere). The repair bound is Θ(T)-loose.
- There is no lower bound on Γ for any multi-label family, and no rate in T, B or mixing beyond B = 1.

**W7. Experiments (MAJOR for main track, acceptable for a theory note).**
- Everything is synthetic, exact and small (T ≤ 10). There are no learned models, no real or semi-synthetic deployment
  stream, and no asymptotics.
- The exact solver scales poorly; FCG is prior art per `PUBLICATION_DECISION.md`.
- The certified numerics are excellent as *falsification* instruments but say nothing about whether Γ matters at
  realistic horizons.
- Some scans hit time caps: 5,142/5,400 sym cells, and 4/16 cells of the symbig shard 0, with shards 1–2 not run.
  This is fine for existence claims but not for frequency claims.

**W8. Review independence.** Every proof review is same-family. SP1's Lemmas W, K and Pre have had no independent
review, and `REVIEW_SP1.md` does not exist. This does not change significance, but it caps acceptance status.

## 4. Questions for the authors

1. Is the ceiling `Γ ≤ (C_0 − V*_IID)/2` at B = 1 (Strength 5) attained in SP1 cells? If it is, the headline becomes
   "certifying against an adaptive null can cost up to half the value of the information you buy". That is far more
   compelling than absolute Γ.
2. How does `Γ(B,T)` behave as T and B grow together in the symmetric persistent family? Does `Γ / (C_0 − V*_IID)`
   tend to 0, to a constant, or does it grow? The CE-B2 / symbig trend (onset α falling with B) hints at a scaling law.
3. Does an e-process or test-supermartingale gate, which is safe by Ville, come close to `V*_causal`? If it does, Γ
   measures the price of *any* adaptive-null-valid gate, and the paper connects to the SAVI literature.
4. Is there a natural deployment mechanism (label delay structure, periodic drift) that produces anti-persistence with
   odd lag, or is M1 a mathematical curiosity?
5. Does Γ survive irreversible promotion?

## 5. Score

| Version | Score (1–10) | Confidence (1–5) | One-line rationale |
|---|---|---|---|
| Main track, as it stands | **3 (reject)** | 4 | Well-verified but routine or B = 1-restricted theorems; a taxonomy instead of a multi-label theorem; tiny synthetic magnitudes; narrow audience |
| Best realistic version | **5 (borderline reject)**, up to 6 if Q1 and Q2 both resolve positively | 3 | A general-B theorem with matching rates plus a SAVI connection would make it a legitimate but niche theory paper |
| Workshop (e.g. a theory workshop on safe or anytime-valid decision-making) | Acceptable as is, with SP1's independent review done | 3 | Clean question, exact B = 1 answer, surprising falsification of the persistence conjecture |

**What would move toward accept (mock-review form):** a multi-label theorem, in priority order:
1. a Θ-tight scaling law for Γ/(information value) in the symmetric persistent and anti-persistent families as T and
   B → ∞;
2. a necessary-and-sufficient primitive condition for Γ = 0 at general B, even within symmetric chains;
3. proof of Lemma S+.
Plus one experiment on a non-toy stream showing a non-negligible relative premium.

## 6. HKUSTDial idea-evaluator output (strongest candidate)

**Candidate evaluated:** "The price of adaptive-null certification: an exact B = 1 characterisation (N1 + SP1), a
multi-label zero-premium theorem for exchangeable evidence (S0), and a certified refutation of the persistence ⇒ free
conjecture, organised by four score-monotonicity mechanisms."

### 6.1 First impression
- **Paper type:** New Problem/Setting (theory). The method is derivation plus exact computation, so the STEM framework
  applies.
- **One-sentence story:** certifying a promotion policy against an adaptive history-dependent null instead of the IID
  null is free exactly when evidence is exchangeable; it carries an exact, computable price whenever a negative label
  predicts a favourable future; and, contrary to intuition, persistence does not make it free.

### 6.2 Fatal-flaws audit (early gate)

| # | Flaw | Severity | Defense |
|---|---|---|---|
| 1 | **Insufficient significance / restrictive scope.** Every non-routine exact theorem is B = 1 or static-with-free-labels. The multi-label phenomenon (M3) is witnessed, not proved. Absolute Γ is ≤ ~0.2% of value in the multi-label witnesses (W2) | MAJOR for a workshop note; effectively CRITICAL for main track unless a general-B theorem is added | Prove a scaling law for Γ relative to the information value at general B (§7), or reposition as a short note |
| 2 | **Novelty (F1), provisional.** Retrieval (`PRIOR_ART_SOURCES.md`) finds the null family reducing to rectangular robust sets (Iyengar; Nilim–El Ghaoui; Fauss–Zoubir–Poor Thm 6) and the zero-side mechanisms reducing to NP/TP2 structure (Krishnamurthy). No retrieved source computes Γ. This is "no directly overlapping work retrieved under these keywords", searched 1–3 times per sub-topic. `PRIOR_ART_AUDIT.md` not yet available | MAJOR (unresolved) | Await the novelty reviewer. Position as "the gap to a nominal member of a rectangular family", which WP F did not find stated |

There is no data-refuted *core* mechanism. The refuted conjecture (persistence ⇒ free) was a hypothesis inside the
programme, and its refutation is itself a contribution. So there is no CRITICAL short-circuit at the idea level, and
the evaluation continues.

### 6.3 Lifecycle and capability match

| Aspect | Input | Assessment |
|---|---|---|
| Idea category | Foundational theory | Long lifecycle; low scooping risk in this exact formulation |
| Lifecycle | Not time-sensitive | Fine |
| Capability | Exact certified solver, independent re-implementations, agent proof capacity (B = 1 and S0 proved within one day) | Green for computation and falsification. **Yellow/Red** for the general-B proof, after two failed structural programmes (Lemma U, Z2) |
| Weekly effective hours | Not stated by the user | Cannot assess; note only |
| Fit | — | **Yellow** |

### 6.4 Five-dimension radar

| Dimension | Score | Evidence | Lift suggestion |
|---|---|---|---|
| Higher | 4 | No accuracy or effectiveness gain; Γ is a diagnostic quantity | Show a gate design that achieves `V*_causal` and quantify the gain over IID-plus-repair (repair bound is Θ(T)-loose; C4 item 3) |
| Faster | 5 | Γ = 0 regimes let the IID LP plus a 56–72-state verifier certify the optimum without the null tree (`PUBLICATION_DECISION.md`), but that speed-up is unattributed and FCG is prior art | A primitive test predicting Γ = 0 before solving; S0 gives this for static, free labels |
| Stronger | 6 (mechanism-based, partly data) | Certified evidence that IID-calibrated gates lose optimality, or need repair, under adaptive nulls even with persistent, balanced evidence (CE-B2 at α = 5/16). Exact B = 1 characterisation | Show the relative premium is non-negligible (Q1) |
| Cheaper | 5 | No grounds given | — |
| Broader | 4 | Two-state HMM, Bernoulli labels, single promotion | Connect to SAVI / e-process gates (Q3) and to rectangular robust MDPs |

The highest-ceiling dimensions are **Stronger** and **Broader**. A paper should emphasise them.

### 6.5 Paradigm-shift probe

| Probe | Yes/No | Rationale |
|---|---|---|
| First Principles | Yes | Challenges the implicit assumption that IID-null calibration of promotion gates is adequate under adaptive feedback, and refutes the natural "persistence makes it free" intuition |
| Elephant in the Room | No | Practitioners do not currently perceive this as a pressing problem; magnitudes found are small |
| Technology Cycle | No | — |
| Hamming's Rule | No | Solving it fully would refine gate design in a niche; it would not change the field |

Disruptive potential: **none to possible** (one yes).

### 6.6 Feasibility

| Risk | Level | Mitigation |
|---|---|---|
| Compute | Low for small cells; **High** for any scaling claim (exact solver) | Use the closed G/D recursions (S0) and the window DP (SP1) to reach large T analytically |
| Data | Low (synthetic) / **High** if a real stream is required | A semi-synthetic label-delay stream from existing Paper 1 data, with stated limitations |
| Engineering | Low | Harness exists and is audited (E1) |
| Timeline / proof | **High** | General-B results resisted two programmes. Bound the effort: one targeted asymptotic analysis in the symmetric family |

### 6.7 Verdict

**Accept with Revisions**, scoped to a workshop or short theory note, and worth pursuing toward main track only
pending the validation step below. As a main-track paper in its current form the verdict is **Reject and Pivot**.

Top three actions:
1. Prove or refute a **general-B scaling law** for `Γ / (C_0 − V*_IID)` in the symmetric stationary families
   (anti-persistent, d = 1, and persistent with B ≥ 4). This is the validation experiment.
2. Check whether the B = 1 ceiling `Γ ≤ (C_0 − V*_IID)/2` is attained in SP1. If it is, lead with the relative
   premium, not the absolute one.
3. Obtain an independent review of SP1 (Lemmas W, K, Pre), and wait for `PRIOR_ART_AUDIT.md` before any novelty
   claim.

## 7. Direct answers to the brief

| Question | Answer |
|---|---|
| Is the problem significant to the ML community? | **Moderately interesting, narrowly relevant.** The question is clean and, per retrieval, unstudied in this form. But the model is a stylised two-state switching game, and the measured premiums are small in absolute terms. Without a link to practical gates (e-processes, deployment streams) it is a niche robust-sequential-decision question, not a mainstream ML one |
| Is any theorem new or a routine corollary? | R, R′, Zc, Z1, S1 and P are routine (audit's own labels). N1 is elementary but is the only *complete* characterisation and plausibly new as a statement (provisional). SP1 is a closed-form specialisation of N1. S0 is a clean restricted proposition, about 80% routine. The newest scientific content is the certified **counterexamples** (persistence ⇒ free fails at B ≥ 4 and practical α) and their mechanism |
| Are the assumptions natural? | α ≤ 1/2, the adaptive null class and static exchangeable evidence are natural. B = 1 is degenerate for budgeted sensing, and conclusions provably do not transfer to B ≥ 2. Symmetric stationary chains are a reasonable canonical family, but anti-persistence with odd lag (the proved positive driver) lacks a practical motivation. Free labels (c = 0) in S0 is a convenience assumption |
| Stronger than special-case constructions? | **At B = 1, yes:** N1 covers every HMM, not a hand-built family, and supersedes C3. **At B ≥ 2, no:** the evidence there is witnesses plus identity bounds |
| Does it explain a meaningful phenomenon? | Partly. Score monotonicity of `P_A(y)G(y)⁺` organises every positive cell found, and M3 (persistence penalises isolated flips) is a genuine non-obvious explanation. But it is a taxonomy: not necessary (50/103), not exhaustive, and M2/M3 are unproved |
| Matching bounds / examples? | Exact at B = 1, with a sharp α ≤ 1/2 scope. None at B ≥ 2 beyond loose identity and monotone-restriction bounds. Examples are plentiful and certified |
| Are the experiments sufficient? | For falsification and verification, yes, and they are exemplary. For significance, no: all synthetic, T ≤ 10, no asymptotics, no deployment-like stream, some scans time-capped |
| Main track / workshop / neither? | **Not main track as it stands. A workshop paper or short theory note: yes**, after the SP1 independent review and with novelty claims held provisional |
| Single additional result that would most change the verdict? | A **general-B theorem giving tight (Θ) asymptotics of the relative premium Γ/(C_0 − V*_IID)** in the symmetric stationary families as T, B → ∞. It should show a non-vanishing relative premium under persistence (M3) or anti-persistence (M1), with a primitive controlling parameter. It would turn the taxonomy into a theorem, answer the "tiny Γ" objection, and remove the B = 1 restriction in one step |

## 8. Recommendation

**Main track: NO-GO, for the reason "too restrictive / routine corollary"** (directive §13 stop rules). The
contribution that is proved in general is routine (R, Zc, Z1, S1). The non-routine exact results are confined to
B = 1 (N1, SP1) or to static, free-label evidence (S0). The multi-label phenomenon is supported by certified
counterexamples and a taxonomy, not by a theorem. Novelty is **not** the NO-GO reason: retrieval found no source
computing Γ, but this stays provisional pending `PRIOR_ART_AUDIT.md`.

**Workshop or short theory note: CONDITIONAL GO.** The conditions are:
1. an independent review of SP1 (Lemmas W, K, Pre);
2. the novelty audit does not find Γ (or N1) in prior art;
3. claims are scoped exactly as in `STRUCTURAL_CHARACTERIZATION.md` §4–5: no general equivalence, the taxonomy
   labelled as empirical, and magnitudes reported with their relative size.

Upgrading to a main-track CONDITIONAL GO requires the §7 general-B asymptotic result.

## Lead check of the reviewer's B = 1 ceiling (2026-11-10)

From N1 (α ≤ 1/2): Γ = α(2g_z0 − r_c)⁺ with r_c ≥ g_z0 (g_z0 is one of the rays in r_c), so
Γ ≤ α·g_z0 ≤ α·r_IID/2 = (C₀ − V*_IID)/2. **PROVED (elementary corollary of N1).** At B = 1 the causal-safety premium
is at most half of the IID value of the information bought. Tightness in the SP1 family not checked.
