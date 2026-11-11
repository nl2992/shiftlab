# P4: Prior art for the two-regime premium statement (S-1 / S-2)

**Date:** 2026-11-11. **Step:** P4 of `SALVAGE_PLAN.md`. **Reviewer:** fresh-context Opus 5.5 novelty reviewer.
**review_independence:** same-family. **acceptance_status:** provisional.
**Method:** HKUSTDial `deep-research` (frozen questions, adversarial search perspectives, every source verified
before use, read status recorded). ARIS `novelty-check` protocol with its Codex reviewer slot unavailable; I
substitute as the reviewer and judge under its verdict limits. Searches were run serially, without sub-agents.
**Untrusted downloads:** saved in the new directory
`/private/tmp/claude-501/-Users-nigelli-Desktop-ICML-Shift-lab--claude-worktrees-shiftlab-methods-strategy-dba13e/06bf436b-d27c-42d6-9116-89f769a07352/scratchpad/p4_sources/`
(`modak.pdf`, `fauss.pdf`, `safe.pdf`). Only `pdftotext` was run on them; nothing was executed.
**Not redone:** the sources and verdicts already in `PRIOR_ART_SOURCES.md` and `PRIOR_ART_AUDIT.md` stand unless
a row below changes them.

**Read-status vocabulary.**
- FULL: the full text was retrieved and the named sections read.
- ABSTRACT: the abstract or landing page was read, through a fetch-tool summary.
- SNIPPET: search-result text only.
- MEMORY: not retrieved in this step.

## 0. Frozen research questions

- **Q1.** Is there a published result saying that the price of certifying against all history-adaptive nulls
  p_t ≤ 1/2, instead of IID(1/2), is bounded below by a constant fraction of the value of information, uniformly in
  the horizon, for mixing hidden-Markov alternatives with scarce labels? Is there one saying the price vanishes for
  deterministic chains or abundant labels?
- **Q2.** Do the asymptotic "adaptivity buys nothing" results quantify a finite-horizon gap or a mixing-dependent
  constant? Do they apply to this problem at all?
- **Q3.** Does any "price of robustness" result in robust MDPs, ambiguity or e-values give a two-regime
  (persist / vanish) characterisation of a robust-minus-nominal value gap?

## 1. Candidate statement under test (from `SALVAGE_PLAN.md`)

- **S-1.** Symmetric anti-persistent chain with t ∈ (1/2, 1), odd delay d, labels scarce (B ≤ B̄). Then
  ρΓ = Γ/(C₀ − V*_IID) ≥ c(t, e, d, α) > 0 for every T ≥ T₀.
- **S-2.** At t = 1, ρΓ → 0 as T → ∞ at fixed B (Thm A), and sup_T ρΓ → 0 as B → ∞ (Thm V).
- Here Γ = V*_causal − V*_IID: the constrained optimal cost under the sup over adapted nulls, minus the cost under
  the IID(1/2) null.

## 2. Close sources: theorem, assumptions, attempted reduction, difference, classification

### 2.1 Modak, Bakshi, Dey, Prabhakaran, "Sequential Adversarial Hypothesis Testing", arXiv:2511.10181v1 (13 Nov 2025)

**Read status:** FULL. I read §1–3, Thm 1, and the converse proofs of Thms 1–3 (Thm 3 is §7). I read §8
(Discussion) and the Appendix A statement of Thm 4. This supersedes the "fetch-summary only" status in
`PRIOR_ART_AUDIT.md`.

**Setting (§2).**
- Finite alphabet. H0: P and H1: Q are closed, convex, disjoint sets of single-letter distributions, mutually
  absolutely continuous (A1–A2).
- Under each hypothesis an adaptive adversary picks the law of X_t from the set, as a function of x^{t−1}.
- Tests are a stopping time plus a decision. Performance is measured by error exponents normalised by the
  worst-case expected stopping time.

**Results.**
- **Thm 1.** The achievable region is E0·E1 ≤ D(q₁*‖p₁*)·D(p₀*‖q₀*), where (p₀*, q₀*) = argmin D(p‖q) and
  (p₁*, q₁*) = argmin D(q‖p) over P × Q.
- **Thm 2.** Under the constraint sup P(τ > n) < ε, the region is a rectangle.
- **Thm 3.** Under the error-probability constraint, the region is also a rectangle.
- **Converses.** Every converse fixes an **i.i.d.** adversary: "Fix p̂_i(.) = p₀* for all i" (§5B and the proofs of
  Thms 2–3). This is the precise sense in which adaptivity buys nothing: the region is attained against i.i.d.
  adversaries.
- **Thm 4 (App. A).** The fixed-length tradeoff, again asymptotic.
- **§8.** The authors state that they "focused on the first-order asymptotics" and that second-order asymptotics
  are future work. The paper has **no finite-n statement, no mixing constant, and no hidden-state alternative**.

**Attempted reduction.** Set P = {Ber(p): p ≤ 1/2}. The alternative would have to be an adversarial convex set Q
of per-step laws. In our problem it is one **fixed** hidden-Markov law P_A. Its predictive q_t is history-dependent
and is *not* worst-case for the tester.

**Exact difference, and a correction to the salvage plan.** The zero-gap statement compares adaptive and i.i.d.
adversaries when *both* hypotheses are worst-case convex sets. It does not cover IID(1/2) versus adapted p_t ≤ 1/2
against a fixed dependent alternative. Here the asymptotic exponent gap is **not** zero. The following is my own
derivation, consistent with `GENERAL_B_PREMIUM.md` Lemma A:
- Against P_A, the best i.i.d. null member is Ber(1/2), because the stationary marginal is 1/2. Its Stein rate per
  label on a fixed calendar is E_π KL(Ber(q)‖Ber(1/2)) = log 2 − H̄ (H̄ is the entropy rate of the labels).
- The adapted null p_t = min(q_t, 1/2) leaves only the rate E_π[1{q>1/2} KL(Ber(q)‖Ber(1/2))].
- For the symmetric chain the law of q is symmetric about 1/2, so this is **exactly half** the IID rate.
- So on fixed calendars the adaptive null halves the exponent. Only adaptive query timing (re-timing, Thm A) can
  recover it.
- The sentence in `SALVAGE_PLAN.md` §"Interpretation", "consistent with zero asymptotic exponent gaps for adaptive
  adversaries", cites Modak et al. for something they do not prove. It should be replaced with: "consistent with
  the exponent being halved on fixed calendars and recovered by re-timing; Modak et al./Brandão et al. concern a
  different (doubly worst-case) model".

**Classification: PROVED DISTINCT.** The model differs (fixed dependent alternative, budget, delay, decision
cost), and the paper has no finite-horizon or mixing-dependent quantity. It is the right citation for the
contrast "first-order asymptotics only; finite-horizon open". It is not a citation for "zero gap here".

### 2.2 Brandão, Harrow, Lee, Peres, "Adversarial hypothesis testing and a quantum Stein's Lemma for restricted measurements", arXiv:1308.6702 (ITCS 2014; IEEE Trans. Inf. Theory 66(8):5037–5054, 2020)

**Read status:** ABSTRACT. Its theorem is also restated in Modak et al. §1 (FULL).

**Statement.**
- Fixed-length test, n samples, convex sets P and Q, and an adversary that sees past samples.
- The Stein exponent is min_{p∈P, q∈Q} D(p‖q), the same as for a non-adaptive adversary.
- The result is asymptotic only.

**Reduction.** Same obstruction as §2.1: the alternative is worst-case, not a fixed HMM, and there is no finite-n
gap.

**Classification: PROVED DISTINCT.**

### 2.3 Fauß, Zoubir, Poor, "Minimax optimal sequential hypothesis tests for Markov processes", Ann. Statist. 48(5):2599–2621 (2020), arXiv:1811.04286v2

**Read status:** FULL. I read §2.3 eq. (2.6), the remark after Thm 6, and §7.1–7.2 in this step. Thms 1–9 were
already read by WP F.

**Statement.**
- Rectangular uncertainty on conditional laws given a Markov statistic θ_n (2.6).
- Least-favourable laws depend on the data through the likelihood ratios z, "even in the case where the X_n are
  independent".
- §7.1 Corollary 3: the least-favourable laws maximise a policy- and state-dependent f-similarity. The authors
  relate the existence of capacity-type (data-independent) LFDs to single-threshold procedures.
- §7.2 Corollary 4: the constrained minimax value is finite iff sup_λ ρ_λ(1, θ₀) − Σλ_k α_k < ∞.

**Reduction.** V*_causal is an instance of this kind of minimax value, with K = 1 constraint and the run-length
cost replaced by an HMM decision cost.

**Difference.**
- §7 discusses **when** least-favourable laws are data-dependent. It never compares the minimax value with the
  value at a nominal member (Γ).
- It has no horizon or mixing asymptotics and no label budget.

**Classification: PARTIAL OVERLAP** for the object, as already recorded. **PROVED DISTINCT** for S-1/S-2.

### 2.4 Grünwald, de Heide, Koolen, "Safe Testing", arXiv:1906.07801v5 (2023)

**Read status:** FULL for §1 and §2 Thm 1 and Cor. 2. Later sections were skimmed via grep.

**Statement (Thm 1).**
- For an alternative Q and a convex null hull {P_W0}, E* = q/p₀* is the GRO e-variable.
- Its growth rate is sup_E E_Q log E = inf_W0 D(Q‖P_W0) = D(Q‖P₀*), where P₀* is the reverse information
  projection (RIPr).
- The paper's examples are i.i.d. or exchangeable models, not predictable conditional-law nulls.

**Reduction (own derivation, not in the paper).**
- The adapted family {p_t ≤ 1/2 predictable} is convex.
- By the chain rule for KL, the RIPr of P_A onto it is per-step: p_t = min(q_t, 1/2).
- Labels with q_t ≤ 1/2 therefore contribute 0 to D(P_A‖P₀*). This is the "zero labels are free" mechanism, and
  for symmetric chains it gives the halved KL.

**Difference.**
- Thm 1 gives the optimal growth rate. It does not give an optimal **constrained decision value** at finite T.
- It does not compare against the IID(1/2) null.
- It says nothing about mixing or budget.

**Classification: PARTIAL OVERLAP** for the halving mechanism. That mechanism is a routine consequence and should
be cited, not claimed. **PROVED DISTINCT** for S-1.

### 2.5 Saha & Ramdas, "Huber-robust likelihood ratio tests for composite nulls and alternatives", arXiv:2408.14015 (IEEE Trans. Inf. Theory, accepted per arXiv v8)

**Read status:** ABSTRACT.

**Statement.**
- e-value tests remain valid when each observation's conditional law lies in an ε-TV ball around the null, which
  is adaptive contamination.
- When LFDs exist, the test achieves the optimal growth rate. Otherwise the growth rate tends to the KL as ε → 0.

**Reduction.** This is another "robust against an adaptive null" price, measured in growth rate.

**Difference.**
- The robustness set is a TV ball, not a one-sided p ≤ 1/2 set.
- The price is characterised only qualitatively, in the limit ε → 0.
- It is asymptotic, with no HMM alternative, budget, or finite-T decision value.

**Classification: PROVED DISTINCT** at the abstract level. The full text was not read.

### 2.6 Sethi, Sagar, Agrawal, Basu, Karthik, "Asymptotically Optimal Sequential Testing with Markovian Data", arXiv:2602.17587v3 (2026)

**Read status:** ABSTRACT.

**Statement.**
- One-sided, α-correct sequential tests for an ergodic finite-state Markov chain, with a composite null set of
  transition matrices.
- A non-asymptotic, instance-dependent lower bound on the expected stopping time, tight as α → 0.

**Difference.**
- The null is a set of time-homogeneous chains, not history-adaptive conditional laws.
- There is no IID-versus-adaptive comparison, no label budget, and no decision value.
- The non-asymptotic part is a lower bound on stopping time, not a robust-minus-nominal gap.

**Classification: PROVED DISTINCT.** It is the most recent Markov-data sequential-testing neighbour and should be
cited as context.

### 2.7 Robust MDP rectangularity and conservatism (Wiesemann–Kuhn–Rustem 2013; Goyal–Grand-Clément 2022; Ou–Bi review arXiv:2404.00940)

**Read status:** META/ABSTRACT, as in `PRIOR_ART_SOURCES.md` §5.4. Search snippets in this step: the Ou–Bi review
says rectangular sets are "noted for their conservatism"; a non-rectangular reward-uncertainty paper
(arXiv:2309.01107) bounds the gap through visitation frequencies; a policy-gradient paper bounds approximation
error by a "measure of non-rectangularity".

**Reduction.** Γ is a gap between a rectangular robust value and the value at one nominal member.

**Difference.**
- The known quantified gaps are robust-versus-non-rectangular (computational relaxation) or reward-regularisation
  identities.
- None is a horizon-uniform lower bound driven by mixing, and none has the persist / vanish dichotomy.
- I found no robust-MDP paper that states a constant-fraction-of-VOI price.

**Classification: PROVED DISTINCT**, at abstract/snippet depth.

### 2.8 Bertsimas & Sim, "The Price of Robustness", Oper. Res. 52(1):35–53 (2004)

**Read status:** META, as in `PRIOR_ART_SOURCES.md` §5.1.

The model is a static LP with a budget of uncertainty. **PROVED DISTINCT.**

### 2.9 Ambiguity and information acquisition: Epstein & Ji, "Optimal learning under robustness and time-consistency", Oper. Res. 70(3):1317–1329 (2022), arXiv:1708.01890; Auster, Che, Mierendorff, arXiv:2208.14121

**Read status:** SNIPPET/ABSTRACT.

**Content.**
- Epstein–Ji: closed-form robust optimal stopping, including robust sequential testing of two simple drift
  hypotheses for a Wiener process. The model uses rectangular, time-consistent multiple priors and a sampling cost.
- Snippet: "sensitivity analysis" overstates the robustness value of sampling.
- Auster et al.: the dynamics of experimentation under ambiguity without rectangularity.

**Difference.**
- These are continuous-time Brownian models with ambiguity in the decision maker's own preferences.
- They do not compare against a fixed nominal null calibration, and they have no hidden-Markov mixing, label
  budget, or horizon-uniform price fraction.

**Classification: PROVED DISTINCT.** Epstein–Ji is the closest economics neighbour for "robust sequential testing
with sampling cost" and should be cited.

### 2.10 Imprecise Markov chains (Škulj & Hable, Metrika 2013, DOI 10.1007/s00184-011-0378-0; arXiv:1602.08901)

**Read status:** SNIPPET.

**Content.** Coefficients of ergodicity and the convergence rate of upper transition operators. Perturbation
bounds and the "degree of imprecision" for uniquely convergent imprecise chains.

**Relation.**
- The causal null is a local credal set [0, 1/2] per node (an imprecise probability tree; see the De Cooman–Hermans
  row in `PRIOR_ART_AUDIT.md`).
- Mixing-dependent *imprecision* bounds exist there, but for long-run upper expectations of the chain itself.
- They do not cover a constrained decision value against a precise alternative.

**Classification: PROVED DISTINCT.** This is a conceptual neighbour if S-1 is proved via mixing.

## 3. Searches run (all with no hit stating S-1 or S-2)

- Adaptive adversary + finite horizon + Markov alternative.
- "price of robustness" + sequential + VOI + mixing.
- Robust testing for HMM / composite Markov null exponents.
- e-process + predictable conditional-mean null + Markov alternative + halved growth.
- "price/cost of adaptivity" + sequential testing.
- Adversarial active / controlled-sensing testing with composite null.
- Robust constrained POMDP + label budget + delayed labels.
- Rectangular vs non-rectangular value gap + mixing.
- Imprecise Markov chain precise-vs-imprecise gap.
- Ambiguity + value of information + sequential sampling.

Absence of a hit is not proof of absence. Second-order asymptotics of adversarial or composite sequential testing
(the direction Modak et al. §8 leaves open) is the most likely place for an unseen overlap. I found none.

## 4. Verdict (under the novelty-check verdict limits)

| Item | Closest source | Classification |
|---|---|---|
| S-1 (mixing, B scarce ⇒ ρΓ ≥ c uniformly in T) | Modak et al. 2025 (first-order only); Fauß et al. 2020 §7; Sethi et al. 2026 | **Not found; PROVED DISTINCT from every source read** |
| S-2 (t = 1 ⇒ ρΓ → 0 in T or in B) | Re-timing ≈ active/controlled sensing (Chernoff 1959, META); betting test = Waudby-Smith–Ramdas | **PARTIAL OVERLAP in mechanism**; the statement itself is not found |
| Two-regime dichotomy as a whole | none | **Not found** |
| Halved exponent on fixed calendars ("zero labels free") | Grünwald et al. Thm 1 (RIPr) + KL chain rule | **PARTIAL OVERLAP**: routine, cite it |
| Plan's claim "zero asymptotic exponent gap for adaptive adversaries" applies here | Modak et al.; Brandão et al. | **Mis-citation**: their zero gap is for doubly worst-case convex sets. Against a fixed symmetric HMM, fixed calendars give a halved exponent (own derivation) |

**Recommendation: PROCEED WITH CAUTION.** No named paper contains S-1 or the dichotomy, so ABANDON is not
justified. The delta that a reviewer could verify in one sentence: *"for a fixed hidden-Markov alternative, the
finite-horizon price of calibrating against all adapted one-sided nulls rather than IID(1/2) is a horizon-uniform
constant fraction of the value of information under mixing and label scarcity, and vanishes for a deterministic
chain or abundant labels; existing adversarial-testing results are first-order asymptotic and doubly worst-case."*
The delta rests entirely on S-1 being proved. S-2 alone is mechanism-level known (re-timing plus a betting test).

## 5. What must be proved for the statement to count as new

1. **S-1 as a theorem, not as numerics.** An explicit c(t, e, d, α) > 0 and an explicit B̄, uniformly in T ≥ T₀,
   for an open set of t < 1. It must hold against **adaptive query timing**, since Thm A shows re-timing is exactly
   what kills the premium at t = 1. A calendar-only bound would reduce to the static halved-exponent fact (§2.4) and
   would not be new.
2. **The mechanism separating the regimes must be explicit.** One candidate is that under mixing the learner cannot
   predict, at query time, which labels will have q > 1/2, because the information decays like r^j; so re-timing
   cannot align labels. The constant should depend on t through r (or a mixing time) and degenerate as t → 1 in a
   way that matches Thm A. Otherwise the two halves are two separate facts rather than one characterisation.
3. **A correctly stated asymptotic contrast.** Replace the Modak/Brandão "zero gap" framing with the exponent
   statement that actually holds in this model:
   - halved on fixed calendars (§2.1 derivation);
   - (conjecturally) recovered by re-timing when T − B → ∞.
   Then show that the finite-horizon constant in S-1 does **not** follow from either exponent. If S-1's constant
   turned out to equal 1 − (re-timed causal exponent)/(IID exponent), it would be an asymptotic corollary, and the
   novelty would shrink to "first-order exponent of a controlled-sensing problem with a composite adapted null".
   That would have to be checked against the active-hypothesis-testing literature (Chernoff 1959; Naghshvar–Javidi
   2013), which has not been opened.
4. **Citations to add:**
   - Modak et al. 2025 (FULL) and Brandão et al. 2020, as the asymptotic, doubly-adversarial contrast;
   - Grünwald et al. Thm 1, for the RIPr / halving;
   - Fauß et al. §7;
   - Sethi et al. 2026;
   - Epstein–Ji 2022;
   - Saha–Ramdas.

**Limits of this review.**
- Same-family reviewer; no external review.
- Several sources were read only at abstract or snippet depth: §2.5–2.10, Brandão et al., Chernoff, and
  Naghshvar–Javidi.
- The own derivation in §2.1 (halved exponent) is short and was not checked numerically in this step. It agrees
  with Lemma A's bound KL(P_A‖Q*) ≤ B·I_e/2 at t = 1.
