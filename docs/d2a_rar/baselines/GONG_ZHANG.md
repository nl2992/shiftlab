# Implementation spec — Gong & Zhang (ICML 2026) paid observations in contextual bandits

Status: NOT_IMPLEMENTED. Spec by WP1c agent, 2026-11-07. Source: PMLR page + PDF
(`https://raw.githubusercontent.com/mlresearch/v306/main/assets/gong26i/gong26i.pdf`), main text read;
appendix (Algs 4–6, proofs) **not read**. Code: none listed. pdftotext garbled Greek symbols and fractions, so
**before coding, re-read Algs 1, 3, 4, 6 from rendered page images** (do not trust the constants below marked UNVERIFIED).

## Native game (Suite A)
Adversarial contextual bandit; finite A, finite Π (Alg 1) or realizable class F with online squared-loss
regression oracle (Alg 3); horizon T; per-round cost vector c_t(a) ∈ (0,1]-scale known before acting; observation set
O_t ⊆ A chosen by the learner; pay Σ_{a∈O_t} c_t(a); see ℓ_t(a) only for a ∈ O_t. Regret
R(T) = E Σ_t(ℓ_t(a_t) − ℓ_t(π*(x_t))) + E Σ_t Σ_{a∈O_t} c_t(a). Native experiments: T∈{2000,5000,10000,20000,40000},
d∈{2,4,8}, |A|∈{3,5,10}, |Π|∈{10,20,40}, L2-normalised Gaussian contexts, c ~ U(0.01,0.5), losses U(0,1) (Alg 1) or
linear+N(0,1) noise (Alg 3), 50 reps; comparison d=10,|A|=5,T=10000,c=0.5 vs linUCB (5003.32±1.04) and Tucker et al. 2023
(3697.13±26.80), paper's Alg 3 = 2899.75±48.80 — use as the first reproduction target (record discrepancies).

## Algorithms to implement
**Alg 1 (exponential weights over policies, paid importance-weighted observation).** For round t:
1. weights w_t(π) = exp(−η_t Σ_{s<t} ℓ̂_s(π(x_s))).
2. q_t(a) = (1−γ) Σ_{π:π(x_t)=a} w_t(π)/Σ_π w_t(π) + γ/|A|; sample a_t ~ q_t.
3. **p_t(a) = min{1, ε_t q_t(a)/c_t(a)}**, where ε_t is the learning-rate-type parameter in the pseudo-code (symbol lost in
   extraction; the paper's suggested schedule is ε_t = ... with η_t = min{...} built from Σ_s Σ_a c_s(a) — UNVERIFIED).
4. a ∈ O_t independently w.p. p_t(a); ℓ̂_t(a) = 1{a∈O_t}ℓ_t(a)/p_t(a).
Parameters in Thm 2.1: γ = 1/√T (appears as "γ = 1/√T" in text, UNVERIFIED); uniform cost ⇒ rate O((c|A|ln|Π|)^{1/3}T^{2/3}+√(T ln|Π|)).
Lower bound Thm 2.2: Ω(max{√(T ln|Π|), (c|A|ln|Π|)^{1/3}T^{2/3}}).

**Alg 2 (meta-controller, free budget B ≤ |A|T, uniform cost c):** if B ≥ 1.5·c^{−2/3}(|A|ln|Π|)^{1/3}T^{2/3} → Alg 4 with
p_t(a) = B/(|A|T) (budget pre-allocated across rounds by Alg 5, appendix) and η_t ∝ √(B/(|A|ln|Π|))/√T-type; else Alg 6 with η_t = c^{−1/3}|A|^{−1/3}ln^{1/3}|Π| t^{−2/3}
and a running budget B_t (excess observations beyond B_t are still paid). Phase transition at
B₀ = Θ̃(c^{−2/3}|A|^{1/3}(ln|Π|)^{1/3}T^{2/3}). **Algs 4–6 are in the appendix: read before implementing.**

**Alg 3 (oracle-efficient):** f̂_t from regression oracle; greedy action a_t* = argmin f̂_t(x_t,·); inverse-gap weighting
q_t(a) = 1/(|A| + γ_t(f̂_t(x_t,a) − f̂_t(x_t,a_t*))) for a ≠ a_t*, remainder on a_t*; observation prob
p_t(a) = min{1, (scale_t)·√(q_t(a)(1−q_t(a)))/(ε_t c_t(a))}-type (garbled — UNVERIFIED); update oracle with {(x_t,a,ℓ_t(a))}_{a∈O_t}.

## Evaluation contracts
1. **Native comparator (Suite A):** reproduce the cumulative regret (loss + paid cost) curves/table above before any ShiftLab use.
2. **Common-contract adaptation (Suite B, COMMON_CONTRACT_PORT, label as such, never as the paper's guarantee):**
   map "observe action a" → "request label for the round-t item at price c_q"; q_t = the host controller's own
   propensity (or uniform), use p_t = min(1, κ_t q_t/c_q) with κ_t from the paper's schedule on the remaining budget;
   importance-weight released losses 1/p_t. Must respect label release/pending clocks of BENCHMARK_CONTRACT — the paper has **no delay**.
   Document explicitly that regret bounds do **not** transfer (non-adversarial drift, delayed labels, non-stationary optimal arm).
3. Logged quantities: cumulative loss, cumulative observation cost, #observations, budget use, regret vs best fixed policy (native).

## Tests (CPU, small)
Observation probabilities in [0,1]; E[ℓ̂]=ℓ (Monte-Carlo unbiasedness, tolerance by SE); expected paid cost = Σ p_t(a)c_t(a);
budget never exceeded in Alg 4 path; c→0 recovers full-information behaviour (p_t=1); regret exponent ≈ 2/3 on a
small grid (loose); meta-controller picks Alg 4 vs 6 on the threshold.

## Honest limits
No fictitious closed forms: every constant marked UNVERIFIED must be read from the PDF before use. Guarantee is adversarial
regret in a bandit game; no null, no certificate, no delayed labels.
