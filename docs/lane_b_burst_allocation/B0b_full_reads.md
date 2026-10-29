# B0b: Full-text extraction for three burst-allocation references

Date of extraction: 2026-10-28. Scope: exact statements only. Nothing here is interpreted beyond the text.

**Extraction caveat.** Each PDF was downloaded with WebFetch, saved locally, and converted with `pdftotext` (Poppler). Greek letters, some subscripts, and some inequality or Theta symbols are lost or garbled in that conversion. Where a symbol was unreadable, the text is marked `[garbled]`, and the reading used by the WebFetch summarizer is given separately. Quotes are copied from the converted text and may need checking against the original PDF before any citation.

Local extraction files (outside the repository): `C:/Users/nigel/zc_pdf_out/geng_raw.txt`, `C:/Users/nigel/zc_pdf_out/zc.txt`, `C:/Users/nigel/zc_pdf_out/discern.txt`.

---

## Verification summary

| # | Paper | Verification level | URLs actually read |
|---|---|---|---|
| 1 | Geng, Bayraktar, Lai, arXiv 1309.5396 | **Full text read** (PDF, all sections incl. Appendices F and G converted; two-column layout so some reading order is approximate) | https://arxiv.org/pdf/1309.5396 (converted with pdftotext). Also https://arxiv.org/html/1309.5396 via WebFetch, summarized only (used for cross-check). |
| 2 | Zhang and Cheung, "Piecewise-Stationary Bandits with Knapsacks", NeurIPS 2024 | **Full text read** (NeurIPS proceedings PDF, sections 1-5 and appendix lemmas/proofs converted). **arXiv id: NOT FOUND.** | https://proceedings.neurips.cc/paper_files/paper/2024/file/65ae674df2fb642518ae8d2b5435e1b8-Paper-Conference.pdf (converted with pdftotext). Also https://proceedings.neurips.cc/paper_files/paper/2024/hash/65ae674df2fb642518ae8d2b5435e1b8-Abstract-Conference.html (abstract only). |
| 3 | DISCERN, arXiv 2609.17560 | **Full text read for Sections 3, 4.2, 5 (Theorems 4-9, Corollary 10, Lemma 3), and the Section 6.1 Table 1 caption.** Section 8 and Appendix B proofs were read only through the WebFetch HTML summary, not verbatim. Math symbols garbled in PDF conversion. | https://arxiv.org/pdf/2609.17560 (converted with pdftotext). Also https://arxiv.org/html/2609.17560 via WebFetch (two chunks, summarized only). |

Title note for 2609.17560: the PDF metadata gives the title "Pay Only for Disagreement: Certified No-Regression Verdicts for Model Updates with Matching Label-Complexity Bounds" by Vishnu Bindu Balachandran (arXiv 2609.17560v1). The name "DISCERN" appears in the body as the system/tool name.

---

## 1. Geng, Bayraktar, Lai, "Bayesian quickest change-point detection with sampling right constraints" (arXiv 1309.5396)

**Verification: full text read (PDF).**

### 1.1 Model (Section II, Eq. (1))

Verbatim: "{X_k} are i.i.d. with pdf f_0(x) before the change-point Λ, and i.i.d. with pdf f_1(x) after Λ."

Change-point prior (Eq. (1)): "The change-point Λ is modeled as a geometric random variable with parameter ρ", with P(Λ = 0) = π_0 and, for λ ≥ 1, P(Λ = λ) = (1 − π_0)ρ(1 − ρ)^{λ−1} as extracted [garbled in the exponent/constant, reconstructed].

So observations are i.i.d. conditional on regime (before and after Λ). Observations are Z_k, with the observation Z_k depending on X_k and the sampling decision δ_k.

### 1.2 Sampling-right process and constraint (Section II, Eqs. (2)-(3))

Verbatim from the paper: "We assume that the observer initially has N sampling rights, and her sampling rights are consumed when she takes observations and are replenished randomly." Replenishment process: "Let ν = {ν_1, ν_2, ..., ν_k, ...} ... where ν_k is the amount of sampling rights collected by the observer at time slot k." "We assume that {ν_k} is i.i.d. over k."

Capacity and update, Eq. (2): **N_k = min{C, N_{k−1} + ν_k − δ_k}**, with N_0 = N.

Admissible set, Eq. (3): **U = {δ : N_k ≥ 0, k = 1, 2, ...}**.

Causality (verbatim): "the observer cannot take an observation at time slot k if she has no sampling right at that time slot."

**Limited case (Section III).** Verbatim: "We first consider a special case that p_0 = P(ν_k = 0) = 1, that is, other than the initial sampling rights, there will be no additional sampling rights arriving at the observer. Hence she can take at most N_0 = N observations from the sequence {X_k}." This is a hard pathwise cap with no replenishment.

**Stochastic case (Section IV).** Replenished by i.i.d. ν_k, capacity C, pathwise constraint N_k ≥ 0 (Eq. (3)). Not an expectation constraint.

### 1.3 Sampling policy

**Limited case.** Verbatim (Remark 1 / Theorem 1 context): "the only scenario in which the observer may stop sometime after an observation is taken occurs when she has exhausted all her sampling rights." Theorem 1 gives the optimal next-sampling decision via a minimizer over the posterior, so the sampling times are data-adaptive. Theorem 2 (verbatim fragment): "For each n ... V_n(·) is a concave function of π and V_n(1) = 0. Furthermore, the optimal stopping rule for the N sampling right problem can be given as a threshold ..." Remark 3: "We notice that τ is a threshold rule if N < ∞, but it is not a threshold rule if N = N in Theorem 2." [garbled, approximate wording].

**Stochastic case, optimal (Theorem 4, Eq. (30)).** Verbatim: "The optimal sampling strategy for (P2) is given as **δ_k = argmin_{δ_k ∈ {0,1}} E[V(Λ, N_k) | ..., δ_k]**" (display partly garbled). The stopping rule (Eq. (31)) is given as τ = inf{k ≥ 0 : 1 − π_k ≤ c_k + E[W(k, N_k, π_{k+1})]} [garbled]. Section IV-B says verbatim: "The optimal solution for the stochastic sampling problem has a very complex structure."

**Stochastic case, low-complexity rule (Eq. (42), Section IV-B).** Verbatim from abstract and Section IV-B: "the sampling rule is to take observations as long as the observer has sampling rights left and the detection scheme is a threshold rule." Greedy rule (verified in raw text, Section IV-B): δ̃_k = 1 if N_{k−1} + ν_k ≥ 1, and δ̃_k = 0 if N_{k−1} + ν_k = 0 [symbols partly garbled]. Stopping rule, Eq. (33) (verbatim): **τ̃ = inf{k ≥ 0 | π_k ≥ 1 − α}**, described in the text as "she takes observations as long as she has sampling rights left, and she declares that the change has occurred when the posterior probability exceeds a pre-designed threshold." The sampling rule depends only on the rights process (N_{k−1}, ν_k), not on observed data.

**Adaptivity.** The optimal policy is data-adaptive (a function of the posterior π_k, N_k and the replenishment). The greedy policy is data-independent.

### 1.4 Proposition 2 (Section III-B) and uniform sampling

Uniform policy and threshold stopping (verbatim): "the observer adopts a sampling strategy δ = {ς, 2ς, ...}, i.e., she takes observations every ς symbols, and she adopts a stopping rule τ = inf{nς : π_{nς} ≥ 1 − α, n ≥ N}." "The performance of this uniform sampling strategy serves as an upper bound of the performance of the N sampling right problem."

**Proposition 2 (Asymptotic Upper Bound), verbatim:** "As α → 0, if the number of sampling rights satisfies

N ≥ |log α| / (|log(1 − ρ)| ς)  [garbled placement of ς; the layout reading is N ≥ |log α| / (|log(1−ρ)|·ς) for some constant ς < ∞]

then ADD(π, N, τ, δ) ≤ |log α| ς / (D(f_1 ‖ f_0) + |log(1 − ρ)| ς) · (1 + o(1))."

Symbol note: "(26)" is the number label for the condition on N, and the upper bound is the displayed inequality in the Proposition.

Remark 4 (verbatim): "However, this result brings little information since this ADD can be achieved by any sampling strategy with the threshold rule ..."

Remark 5 (verbatim): "One can notice from (26) that N → ∞ when α → 0 for any given ς. However, this is different from the classic Bayesian quickest detection. ... (26) cannot guarantee the observer can achieve the false alarm constraint at her last sampling right if she takes sample at every time instance. It guarantees only that one can achieve the false alarm constraint by the uniform sampling with interval ς."

**Does the paper claim uniform sampling is first-order optimal?** No. Proposition 2 is an upper bound for the uniform-sampling strategy under condition (26). The paper states the uniform strategy "serves as an upper bound" and does not claim first-order optimality for it. First-order optimality is claimed for the greedy rule in the stochastic model (Theorem 6, Section IV-B).

### 1.5 Remarks 9 and 10 (Section IV-B), verbatim

**Remark 9:** "Since there is no penalty on the observation cost before the change-point, one may expect the observer to take observations as early as possible for the quickest detection purpose, and hence expect the greedy sampling strategy to be exactly optimal. However, taking observations too aggressively before the change-point will affect how many sampling rights the observer can use after the change-point, although there is no penalty on the observations cost before the change-point. Theorem 4 shows that the optimal sampling strategy should be a function of k, N_k and π_k. Intuitively, an observer will save the sampling rights for future use when she has little energy left (N_k is small) or when she is pretty sure that the changepoint has not occurred yet (π_k is small). To use the greedy sampling at the very beginning may reduce the observer's sampling rights at the time when the change occurs, hence increase the detection delay. Therefore, the greedy sampling strategy is only first order asymptotically optimal but not exactly optimal."

**Remark 10:** "In our recent work [17], we also show that the greedy sampling strategy is asymptotically optimal for the non-Bayesian quickest change-point detection problem with a stochastic energy constraint. ... Before the change-point, the greedy sampling might not be the best strategy, but the penalty incurred by this sub-optimality in terms of the detection delay is at most C (the finite sampling right capacity of the observer), which is negligible when the detection delay goes to infinity."

Remark 8 (verbatim): "The above theorems indicate that N_0 does not affect the asymptotic optimality ... However, the sampling right capacity C could affect the average detection delay since p̃ is a function of C and α."

### 1.6 False-alarm criterion and delay criterion

**PFA** (verbatim definition): "PFA(π, N, τ, δ) = P(τ < Λ)." Constraint PFA ≤ α.

**ADD** (verbatim definition): "ADD(π, N, τ, δ) = E[(τ − Λ)^+], where x^+ = max{0, x}."

Problem (P1): minimize ADD subject to PFA ≤ α. Lagrangian (P2) form uses cost c·(τ − Λ)^+ + 1{τ < Λ}.

### 1.7 Delay results

- Classic Bayesian lower bound (Section III-A, Eq. (32) region): ADD ≥ |log α| / (D(f_1‖f_0) + |log(1 − ρ)|)·(1 + o(1)) [garbled, reconstructed from the layout text].
- Limited-rights threshold rule (Eq. (28), Section III-B): ADD = |log α| / |log(1 − ρ)| · (1 + o(1)) is the order result quoted by the paper; Remark 4 says it "brings little information."
- **Theorem 5 (lower bound, stochastic model), verbatim opening:** "As α → 0, inf_{δ ∈ U, τ} ADD(π, N, τ, δ) ≥ |log α| / (p̃ D(f_1‖f_0) + |log(1 − ρ)|)·(1 + o(1))", with p̃ = E[μ̃*] (Proposition 3 in Appendix F: "E[μ̃*] exists, and 0 < E[μ̃*] ≤ 1"). Proof assumes N_0 = C and uses Theorem 1 of [12] (Lemma 2 in Appendix F).
- **Theorem 6 (achievability), verbatim:** "If (36) and (37) hold, then (δ̃, τ̃) is asymptotically optimal as α → 0." The displayed achievability (Eq. (38), verbatim as extracted): ADD(π, N, τ̃, δ̃) = |log α| / (p̃ D(f_1‖f_0) + |log(1 − ρ)|)·(1 + o(1)) [garbled; matches the Theorem 5 lower bound]. Conditions (36)-(37): E[T̃(λ)] < ∞ and E[T̃(Λ)] < ∞ in the r-quick-convergence form; Remark 7 says these are "r-quick convergence" and "averager-quick convergence" [12], and that (36)-(37) are the r = 1 cases. Appendix G proof: the stopping rule τ̃* = inf{k ≥ 0 : R_k ≥ log((1−α)/α)} with threshold b ≈ |log α|, bounding E[(τ̃* − Λ)^+] ≤ b/q_d·(1 + o(1)). The appendix ends: "hence τ̃* is asymptotically optimal."

**Garbled items.** The displayed exact forms of Eqs. (36), (37), (47), (48) and the Theorem 5 right-hand side denominators are only partly legible in the conversion. The text above is the best reading of them. The WebFetch HTML summary read the same Theorem 5 denominator as p̃D(f_1‖f_0) + |log(1−ρ)|, which matches.

---

## 2. Zhang and Cheung, "Piecewise-Stationary Bandits with Knapsacks", NeurIPS 2024

**Verification: full text read (NeurIPS proceedings PDF).** arXiv id: **NOT FOUND** after two WebSearch queries and the NeurIPS pages. Searches returned only the NeurIPS proceedings, mlanthology, and aggregator pages. No arXiv id is linked.

Author list (PDF): Xilin Zhang and Cheung Wang Chi, Department of ISEM, National University of Singapore. Note: the NeurIPS proceedings index lists the authors in a different order.

### 2.1 Model (Section 2.1)

- Horizon T rounds, arms K plus null arm a_null. Round t the decision maker (DM) picks a_t ∈ K ∪ {a_null} and observes "a noisy outcome vector (R_t(a_t), C_t(a_t)) ∈ [0,1]^2 as the bandit feedback."
- Null arm: R_t(a_null) = C_t(a_null) = 0 with certainty.
- Budget: "The DM is endowed with B ≤ T units of the resource."
- Objective and constraint (verbatim): "maximize the total reward, with the constraint that the total resource consumption is at most B with certainty." Hard constraint: Σ_t C_t(a_t) ≤ B with certainty.
- Piecewise stationarity (verbatim): "the planning horizon T is partitioned into L stationary pieces {t_0 = 1, ..., t_1}, {t_1 + 1, ..., t_2}, ..., {t_{L−1}+1, ..., t_L = T}. On each stationary piece l, we have (r_t, c_t) = (r^(l), c^(l)) for all t ∈ {t_{l−1}+1, ..., t_l}."
- Unknown to DM: T, L, change rounds t_1..t_{L−1}, and the values of (r^(l), c^(l)) and their realized outcomes.
- Mean-value notation: r_t = {E[R_t(a)]}_{a∈K}, c_t = {E[C_t(a)]}_{a∈K}.
- Non-anticipation (verbatim): "An online algorithm is non-anticipatory in the sense that X_t depends only on B and {(R_s(a_s), C_s(a_s)), X_s}_{s<t}."

**Observation type.** Bandit feedback: only the chosen arm's (R_t, C_t) is revealed. Changes are not observed.

**Assumption 2.2 (verbatim as extracted):** "For all a ∈ K, l ∈ {1, ..., L}, there exist known constants η_min, η_max ∈ (0, 1] such that η_min ≤ r^(l)(a), c^(l)(a) ≤ η_max [symbol garbled; reading from the layout text]." Section 2.2: "While η_min can be as small as 0 generally, we argue that this assumption is mild."

### 2.2 Benchmark (Section 2.1)

Dynamic program DP (verbatim structure): maximize E[Σ_t R_t(a) X_t(a)] subject to Σ_t C_t(a) X_t(a) ≤ B (in expectation of the stochastic variables as written), X_t ∈ {0,1}.

Fluid approximation FA: decision variables x_l(a) ∈ [0,1], with the l-th piece weighted by (t_l − t_{l−1}):
max Σ_l (t_l − t_{l−1}) Σ_a r^(l)(a) x_l(a)  s.t.  Σ_l (t_l − t_{l−1}) Σ_a c^(l)(a) x_l(a) ≤ B, Σ_a x_l(a) ≤ 1, x_l(a) ≥ 0.

Verbatim (Section 2.1): "we define a fluid approximation FA of DP, where R_t and C_t are replaced by their respective expectations, and the decision variables are fractional." **Lemma 2.1 (verbatim): "opt(FA) ≥ opt(DP)."** (proof in Appendix C.1).

**Benchmark is dynamic.** opt(FA) is computed with the piece-specific (r^(l), c^(l)), i.e., it uses the change points. Section 1 (verbatim fragment): "Our performance guarantee is based on a dynamic benchmark that upper bounds the optimum, different from existing works on adversarial Bwk ... who compare with the stationary benchmark."

**Target guarantee form (Section 2.1):** Σ_t R_t(a_t) ≥ (1/CR)·opt(FA) − Reg, with CR a competitive ratio and Reg sublinear in T.

Section 2.2 (verbatim): "In non-stationary bandits without resource constraints, the performance bound ... In our Bwk setting, due to the inventory constraint, achieving a sublinear-in-T regret is impossible without assuming a bounded global variation (see Appendix A.3)."

Limitation on L (Section 2.2, verbatim): "When L is not known, our result is meaningful only when L = o(T / η_min). When L is known, our result is meaningful when L = o(T · ...) (see Theorem 4.2)." [garbled; reading from the layout]

### 2.3 Inventory-reserving algorithm

**Full-feedback warm-up (Section 3, Algorithm 1 "IRES").** Verbatim: "At the start, the IRES reserves B/(2M) units of resource to each interval m ∈ {−M, ..., M − 1}, and each resource unit is reserved by exactly one interval." Per piece l, it solves an LP for guesses q ∈ {0, ..., M}, with guess η_min·q as Ratio^(l) guess; "as time progresses on l, we go round-robin on the choices of q_t ∈ {0, ..., M} for each round t". The round-t request is fulfilled with x_t = x^(l)(q_t) "if there remains enough reserved resource units for interval m_t", otherwise the DM selects a_null and rejects the request.

**Bandit-feedback algorithm IRES-CM (Section 4.1, Algorithm 2).** Adds change monitoring and exploration. Verbatim: "In each round t, we conduct exploration with probability ... (reflected in a Bernoulli random variable U(t) in Line 7), where ... is a confidence parameter and N is defined in (5). In an exploration round t, we uniformly sample an arm a ∈ K and pull it for N consecutive rounds." Estimates (r̂_t(a), ĉ_t(a)) are built from the most recent N exploration rounds of arm a. (Full pseudo-code is in Algorithm 2, which the conversion reflects only partially.)

### 2.4 Competitive-ratio theorem (Theorem 4.2), verbatim

"**Theorem 4.2.** For any given δ ∈ (0, 1), with probability at least 1 − 2|K| − ⌈log(max{η_min} L + T)⌉ δ [garbled], IRES-CM achieves a reward of at least

(1 − o(1)) / (log(η_max/η_min)·?) · opt(FA) − Õ(√(L|K|NT)) [garbled; the layout reads: (1 − o(1))/(104·log(η_max/η_min)) · opt(FA) − Õ(√(L|K|NT))] 

under Assumption 4.1, where o(·) hides multiplicative factors in terms of ... and Õ(·) hides multiplicative factors in terms of log(η_max/η_min), log(1/δ), (log|K| + 1). In particular, IRES-CM achieves a competitive ratio of O(log(η_max/η_min)) as long as L = o(T · η_min)."

Constant "104" is as extracted in the layout text; treat as [garbled] until checked against the PDF. The O(log(η_max/η_min)) CR claim is in the text.

**Assumption 4.1 (verbatim):** "min{B, opt(FA)} ≳ Ω̃(√(L|K|NT)), where Ω̃(·) hides multiplicative factors in terms of log(η_max/η_min), log(1/δ), (log|K| + 1)." [garbled sign; reading from layout]

**Remark 4.3 (verbatim):** "If the DM knows L, Assumption 4.1 can be relaxed to min{B, opt(FA)} ≳ Ω̃(√(L|K|NT))" [garbled].

**Full-feedback competitive ratio (Theorem 3.1).** Verbatim: "For any given δ ≥ 1, IRES achieves a reward of at least (1/(62·log(η_max/η_min)+1))·opt(FA) − ... under mild requirements that t_l − t_{l−1} ≥ M + 1 for all l ∈ L. In particular, IRES achieves a competitive ratio of O(log(η_max/η_min)) if B ≥ Ω(log(η_max/η_min))." [garbled]

### 2.5 Lower-bound theorem (Theorem 4.5), verbatim

"**Theorem 4.5.** Consider a fixed but arbitrary ε ≥ 1 [garbled], and set η_min = ε/3 [garbled; the text shows '�3', possibly ε/3 or ε^3], η_max = 1 for an arbitrary ε ∈ Z_{≥0} [garbled]. For any online algorithm, there exist an instance for which η_min ≤ r_t(a), c_t(a) ≤ η_max for all a ∈ K, t ∈ T, and that Σ_{t=1}^T R_t(a_t) / opt(FA) ≲ 1 / (log(η_max/η_min))."

Conclusion: the O(log(η_max/η_min)) competitive ratio is tight.

### 2.6 Hard instance in the lower-bound proof (Appendix C.6)

Setup (verbatim where readable): "We prove Theorem 4.5 by considering 2ℓ + 1 instances, which share the same K = {1} (one arm), B ∈ Z_{≥0} and T = B(2ℓ + 1). All instances have the null arm. All instances have deterministic outcomes, and they share the same consumption model C_t(1) = 1 for all t ∈ T. ... The horizon T is partitioned into 2ℓ + 1 pieces with equal length B." Instances are indexed n ∈ {−ℓ, ..., ℓ}, each with a reward function R^(n)(1) that is nonzero (a fixed value, with a base-ε power that depends on the piece index) on pieces up to piece n and equal to 0 on later pieces. The exact power/base in the reward values is [garbled] in extraction; the structure is as described. Instance n and n+1 differ in the reward on piece n+1.

Proof method (verbatim): "By the Yao's principle, the competitive ratio of an online algorithm is at most Σ_n p_n · E^(n)[Σ_t R_t^(n)(1) X_t(1)] / opt(FA^(n))" for distribution weights p_n with Σ p_n = 1. "opt(FA^(n)) = B·... − ..." [garbled]. The instances are crafted so that during piece j, instances −ℓ..j cannot be distinguished; the quantity B_j^(n) = E^(n)[Σ_{t ∈ piece j} X_t(1)] is the same for those n, and the proof sums these to bound Σ_j B_j ≤ B.

**Note.** Section 2.2 and Appendix C.5 also cite a lower-bound instance for Lemma 2.3 (two arms η_null, single arm, instances labelled by pieces with rewards −L, −L+1, ...). It is a separate instance; the description above is the Theorem 4.5 one.

---

## 3. DISCERN, arXiv 2609.17560 (PDF title: "Pay Only for Disagreement: Certified No-Regression Verdicts for Model Updates with Matching Label-Complexity Bounds")

**Verification: full text read for Sections 3, 4.2, 5 and 6.1 (PDF). Section 8 and the Appendix B proof text were read only through the WebFetch HTML summary.** Symbols garbled in conversion are marked [garbled].

### 3.1 Setting (Section 3, verbatim)

"Let (X_t, Y_t)_{t≥1} be an i.i.d. stream from an unknown distribution P over X × Y (drift is treated in Section 5.7). An incumbent model f and a candidate g map X to a prediction space A, and a loss ℓ: A × Y → [0, B] scores predictions." Paired difference D_t = ℓ(g(X_t), Y_t) − ℓ(f(X_t), Y_t) ∈ [−B, B], Δ = E[D_t]. "Δ > 0 means the candidate is worse (a regression) and Δ ≤ 0 means it is no worse."

"The auditor observes both predictions on every point for free, hence also the disagreement indicator A_t = 1{f(X_t) ≠ g(X_t)} with rate ρ = P(A_t = 1), and may request the label Y_t at unit cost." [the "=" vs "≠" symbol: the PDF shows "f (Xt) = g(Xt)" which is garbled; the Assumption 1 text says "whenever the two models make the same prediction, f(X_t) = g(X_t), they incur the same loss, so D_t = 0", so A_t is the disagreement indicator.]

**Assumption 1 (Prediction-determined loss), verbatim:** "The loss is a function of the prediction and label alone, ℓ(a, y), with no other dependence on the input. Its operative content is that whenever the two models make the same prediction, f(X_t) = g(X_t), they incur the same loss, so D_t = 0."

**Lemma 2 (Support identity), verbatim:** "Under Assumption 1, Δ = E[D_t A_t] and |Δ| ≤ B(1 − π_0) ... ≤ B ρ [garbled], where π_0 = P(D_t = 0)." [partly garbled; the layout reads "|Δ| ≤ B(1 − π_0)"; text "||Δ|| ≤ B·(1 − ...)"]

### 3.2 Routing and labelling model

**Lemma 3 (Conditional unbiasedness), verbatim:** "Let π_t be F_{t−1} ⊗ σ(X_t)-measurable [garbled; text reads 'Ft-1 (Xt)-measurable'] with π_t ≥ π_min > 0, and let L_t | F_{t−1}, X_t, Y_t ~ Bern(π_t) be drawn independently of Y_t given (F_{t−1}, X_t). Then the increment (4) satisfies E[Z_t | F_{t−1}] = Δ and |Z_t| ≤ B/π_min."

Increment (Eq. (4), verbatim): **Z_t = (L_t / π_t) A_t D_t** (importance-weighted / Horvitz-Thompson), with c := B/π_min.

**Section 4.2 (verbatim routing rule):** "At each point with A_t = 1 the auditor requests the label with probability π_t, a predictable routing rule. It may depend on everything observed before t and on side information about X_t itself, including scores from a learned judge model, subject only to π_t ∈ [π_min, 1]. Routing may never consult the incoming label Y_t. This is the independence condition of Lemma 3, and it is the one deployment requirement."

Observation model: the auditor sees both predictions on every point (so A_t is free), and Y_t is revealed only when requested. Labels are drawn as Bernoulli L_t with probability π_t, so the **label budget is random, not a hard cap**. Theorem 8 is an expectation bound (E_{P_0}[N_lab]). Theorem 7's label bound is stated with "with probability at least 1 − 2δ_1" and does not say whether N_lab is a hard cap.

### 3.3 Validity and routing

**Theorem 4 (Anytime validity), verbatim:** "Run Tier 0 at level δ_0 and Tier 1 at level δ_1 with any predictable routing π_t ∈ [π_min, 1]. Then with probability at least 1 − (δ_0 + δ_1), simultaneously for all t ≥ 1: Δ ∈ [Δ_t^−, Δ_t^+] and Δ ∈ [Δ̄_t^−, Δ̄_t^+] [garbled bounds]. Consequently no false Safe(ε) or Regression verdict is ever issued, at any stopping time, under continuous monitoring."

**Theorem 5 (Routing robustness), verbatim:** "The conclusion of Theorem 4 holds for every predictable routing rule, including rules computed from an arbitrary (possibly adversarially wrong) judge model. Routing affects only the label budget and the certification time, never coverage."

### 3.4 Label-complexity upper bounds

**Proposition 6 (Tier-0 certification time), verbatim:** "If B ≤ ε/2, Tier 0 issues Safe(ε) after at most O((B/ε) log(1/δ_0) log log(B/ε)) unlabeled points, with zero labels."

**Theorem 7 (Labels to a verdict), verbatim:** "Let π_t ∈ [π_min, 1] and suppose the update is ε-benign, Δ ≤ ε/2. With probability at least 1 − 2δ_1, Tier 1 issues Safe(ε) by stream time

T⋆ = Õ( B² ρ L / (π ε²) + B L / (π_min ε) ) [garbled; the PDF text reads 'T = O(B²·[ρ/π]·L/ε² + B·L/(π_min·ε))' with symbols lost]

and the number of labels requested satisfies

N_lab = Õ( B² ρ² L / ε² + (π/π_min)(B ρ/ε) L ) [garbled].

Symmetrically, if Δ ≥ 2ε, a Regression verdict fires within the same bounds with ε replaced by Δ."

The text after the theorem: "The first term is the variance regime and dominates when ε ≪ B ρ, the second is the range regime of the empirical-Bernstein boundary and dominates for small ε. ... total label cost is O(B²ρ L/ε²)."

The uniform-labeling baseline (Eq. (5)): "gives the baseline cost N_lab^uniform = Õ(B² L/ε² + B L/ε)", and the savings ratio N_lab/N_lab^uniform = Õ(ρ/B) [garbled] "so the predicted savings ratio is N_lab / N_lab^uniform = Θ(ρ/B) [garbled], and the auditor pays only the disagreement fraction of the uniform bill."

### 3.5 Matching lower bounds (Section 5.3)

**Theorem 8 (Lower bound for adaptive auditors), verbatim statement:** "Fix B = 1, ε ∈ (0, 1/8], and ρ ∈ [2ε, 1/2] [garbled; reading from the layout and WebFetch summary]. There exist distributions P_0, P_1, both with disagreement rate ρ, with Δ(P_0) = 0 and Δ(P_1) = ε, whose unlabeled streams (X_t, f(X_t), g(X_t)) are identically distributed, such that any (ε, δ)-sound procedure that issues Safe(ε) with probability at least 1 − δ under P_0 must request

E_{P_0}[N_lab] ≥ (ρ² / (4ε²)) · log(1/(2.4δ))   [garbled; the PDF text reads '2 1 / 4 2 log 2.4', and the WebFetch summary reads ρ²/(4ε²)]

labels, regardless of how adaptively it routes labels or stops."

Text after Theorem 8 (verbatim): "Together with Theorem 7, the label complexity of certified update auditing is settled at Θ(ρ/ε²) in the audited regime ρ ≥ 2ε, and at zero labels in the Tier-0 regime ρ ≤ ε/2." [Θ and ρ/ε² partly garbled in conversion; the reading was taken from the layout.]

**Theorem 9 (Lower bound for pairing-blind auditors), verbatim:** "In the setting of Theorem 8, call a procedure pairing-blind if it does not evaluate the model pair on unlabeled points. Its labeling decisions and verdict are measurable with respect to its own past labeled outcomes alone. This class prices exactly the standard practice of labeling sampled traffic without shadow-scoring it. Any (ε, δ)-sound pairing-blind procedure must request

E[N_lab] ≥ (ρ / (4ε²)) · log(1/(2.4δ))   [garbled; reading from the layout and the WebFetch summary]

labels. Uniform labeling with an empirical-Bernstein CS achieves this rate up to logarithmic factors."

**Corollary 10 (The value of pairing), verbatim:** "In the regime ρ ≥ 2ε, the ratio of optimal pairing-blind to optimal pairing-aware label complexity is Θ(1/ρ) [garbled; the PDF text reads '( 1/)' with the Theta symbol lost]. Observing both models' predictions on unlabeled traffic, a pure compute cost, cuts the human labeling bill by the inverse disagreement rate."

**Remark 11 (verbatim, part):** "The separation prices exactly one capability, observing the pair's agreement on unlabeled traffic. An auditor granted the disagreement indicators A_t on unlabeled points is by definition not pairing-blind."

### 3.6 Disagreement rate versus harm ordering

Section 6.1 (verbatim): "Disagreement rate alone does not order updates by harm, which is exactly why the promotion decision certifies Δ rather than reading off ρ."

Table 1 caption (verbatim): "The regressions show that ρ does not order updates by harm. Rank halving disagrees at ρ = 0.15 and truly degrades accuracy (Δ = 0.14), whereas the milder label corruptions disagree far less and carry a spectrum of harm."

Section 6.1 description of the zoo (verbatim): "Eleven update types produce the candidate, chosen so that the disagreement rate and the true harm vary independently across the zoo (Table 1). Seven are benign, with true risk difference essentially zero ..., and they span the disagreement range from ρ ≈ 0 to ρ ≈ 0.003. Four are genuine regressions (Δ > 0)..."

Section 5.2 (verbatim): "The first term is the variance regime and dominates when ε ≪ B ρ..." [as in 3.4 above].

### 3.7 Items not read verbatim

- Section 8 (Limitations and Scope): read only through the WebFetch HTML summary, which reports "Assumption 1 ... excludes losses that consult scores rather than predictions, with calibration error as the example" and "Our guarantee under drift is the weighted-average statement of Section 5.7". Not verified against the PDF.
- Appendix B proof text (B.2 for Theorem 5, B.5 for Theorem 7, B.6 for Theorem 8, B.7 for Theorem 9): read only through the WebFetch summary. Not verified verbatim.
- Section 5.7 (drift): not read.
- Proposition 12, 13, 14 (slices, sequence-level soundness, soft support identity) appear in the PDF text but were not extracted for this brief.

---

## Open items for the reviewer

1. Zhang and Cheung has no arXiv id in the search results. Cite the NeurIPS 2024 proceedings (DOI 10.52202/079017-1781 per the NeurIPS page). Confirm whether an arXiv version exists before citing one.
2. The Zhang and Cheung symbols listed as [garbled] (the constant "104" in Theorem 4.2, the form of η_min in Theorem 4.5, and the Assumption 4.1 sign) need checking against the PDF or a clean text export before quoting.
3. The Geng Proposition 2 display, Eqs. (36)-(37), (47)-(48), and the Theorem 5 denominator need checking against the PDF before quoting. The text above is a best reading.
4. DISCERN Theorem 7's exact symbols (ρ, π placement) and Theorem 8's ρ range need checking against the PDF or a clean export.
5. DISCERN Section 8 and Appendix B proofs were not read verbatim from the PDF.
