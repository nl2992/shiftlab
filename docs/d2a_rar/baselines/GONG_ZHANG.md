# Implementation spec — Gong & Zhang (ICML 2026) paid observations in contextual bandits

Status: NOT_IMPLEMENTED. Spec by WP1c agent, 2026-11-07. Source: PMLR page + PDF

**UPDATE 2026-11-07 (WP1d): status IMPLEMENTED; tier `PAPER_RECONSTRUCTION` (Algs 1-6) and `COMMON_CONTRACT_PORT` (label acquisition).** Code `src/shiftlab/sota/gong_zhang/`, tests `tests/d2a_rar/test_gong_zhang.py`,
port `src/shiftlab/bench/contract/adapters_gong_zhang.py`. The 'Status' line above is superseded WP1c text.
**Reading coverage (WP1d):** full PDF; constants read from RENDERED PAGE IMAGES (pp. 4, 6, 7, 29, 30), including appendix Algs 4-6 and Alg 7 (statement only). Not read in detail: proofs C.1-D.2, App. B (unknown costs analysis), App. E Alg 8 (feedback graphs). No author code listed.
**Constants that were UNVERIFIED in this spec, now resolved from the page images:**
(1) p_t(a) = min{1, SQRT(eta_t q_t(a) / c_t(a))}: the printed rule has a square root (the spec had none). Alg 3: p_t(a) = min{1, sqrt(q_t(1-q_t) / (eta_t c_t(a)))}, eta_t in the denominator.
(2) Thm 2.1: eta_t = 1 / ( ( sum_{s<=t} sqrt(sum_a c_s(a)) / ln|Pi| )^{2/3} + sqrt(t / ln|Pi|) ), gamma = 1/T (not 1/sqrt(T)).
(3) Alg 2 line 2: eta_t = (1/T) sqrt(B / (|A| ln|Pi|)); line 5: eta_t = c^{-1/3}|A|^{-1/3} ln^{2/3}|Pi| t^{-2/3}; threshold 1.5 c^{-2/3}(|A| ln|Pi|)^{1/3} T^{2/3} (confirmed).
(4) Alg 4: p_t(a) = B/(|A|T) from Alg 5 (exact B observations; counts m or m+1 per action). (5) Alg 6 pays (|O_t| - B_t) c for the excess. (6) Alg 3: inverse-gap weighting q_t(a) = 1/(|A| + gamma (fhat(a) - fhat(a*))), gamma = sqrt(|A|T / (Reg + log(2/delta))), eta_t = (sum sqrt(sum_a c_s(a)) / Reg)^{2/3} + sqrt(t/Reg).
**Printed-formula inconsistency found:** Alg 2 line 2 puts ln|Pi| in the DENOMINATOR; balancing ln|Pi|/eta + eta |A| T^2 / B (Lemma 2.1 with p = B/(|A|T)) gives eta = (1/T) sqrt(B ln|Pi| / |A|). Both are implemented (`eta_form='printed'|'balanced'`); see the reproduction table.
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

---

## Implementation and reproduction record (WP1d, 2026-11-07)

### Tiers
`src/shiftlab/sota/gong_zhang/core.py` (Algs 1, 3, 4, 5, 6 and the Alg 2 meta-controller): **`PAPER_RECONSTRUCTION`**. `port.py` + `adapters_gong_zhang.py`: **`COMMON_CONTRACT_PORT`**.
Not implemented: Alg 7 (unknown costs, UCB), Alg 8 (feedback graphs).

### Conditions of the native guarantees
Adversarial contextual bandit, finite A, finite Pi (Algs 1/4/6), uniform cost c for Algs 2/4/6, losses in [0,1], immediate observation. Alg 3: realizability f* in F and an online squared-loss regression oracle with regret Reg_Sq(T) (the constant in
our ridge oracle's Reg_Sq = d ln(T/d) is OURS). The regret bounds belong to that game and **do not transfer to the contract** (non-adversarial drift, delayed labels, hard label cap, switch costs); the port invents no guarantee.

### COMMON_CONTRACT_PORT mapping (ours)
|A| = |Pi| = 2 (serve incumbent / candidate; constant policies); one label = both shadow losses; per-action probability min{1, sqrt(eta_t q_t(a)/c_q)} combined as 1 - prod(1-p_a) and importance-weighted by 1/p; exponential weights on released losses; switch when q_cand > 1/2;
the contract hurdle h is added to the candidate's IW loss. Regime from Alg 2's threshold; the sufficient-budget regime uses uniform pacing p_t = (B - used)/(T - t + 1) instead of Alg 5's pre-drawn subset (so that the declared propensity is audit-verifiable); the label cap is hard.

### Reproduction vs paper (own synthetic instances; the generator is only described in prose)
| Item | Paper | Here | Status |
|---|---|---|---|
| IW estimator unbiased; expected cost = sum p c | Lemma C.1 | MC 2e5 draws within 4 SE | MATCH |
| Alg 5: exactly B observations, P(a in O_t) = B/(|A|T) | Prop E.1 | exact count; marginals within 0.03 (3000 draws) | MATCH |
| c -> 0 recovers full information | Remark 2.1 | n_obs = |A|T | MATCH |
| Paid-regret exponent T^{2/3} | Thm 2.1 / 2.2 | Alg 1, |A|=3, |Pi|=10, c=.3, T = 500..4000: regret 149, 256, 411, 644 (5 reps); local slopes 0.78, 0.68, 0.65 | CONSISTENT with 2/3 (loose) |
| Free-budget phase transition (Fig. 1), T=2000, |A|=3, |Pi|=10, c=.3, threshold ~ 1012, 6 reps | T^{2/3}-type minus cB below B0; ~ B^{-1/2} above | below B0: R(0) - R(300) = 90 = cB (same learning regret, free observations); above, eta='balanced': R(2000) ~ 125, R(3000) ~ 102, R(6000) ~ 71 (R(6000)/R(2000) = 0.57 vs sqrt(1/3) = 0.58) | QUALITATIVE MATCH |
| Same with eta='printed' (Alg 2 line 2 as printed) | monotone decrease expected | R(1000) ~ 124 (Alg 6) -> R(2000) ~ 226 (Alg 4) -> R(6000) ~ 151: regret jumps UP at the threshold | **DISCREPANCY**: printed eta in Alg 2 line 2 looks typographically inconsistent; one small instance only |
| Table 2: Alg 3, d=10, |A|=5, T=10000, c=.5 | 2899.75 +- 48.80 (linUCB 5003.32, Tucker et al. 3697.13) | 5 reps: mean cost-inclusive regret 3004.8 (sd 88.8), observation cost 1510.6; ridge oracle, Reg_Sq = d ln(T/d) | within ~3.6 % of the paper mean; instance details (loss generation, regret baseline, Reg constant) are our guesses; linUCB/Tucker NOT implemented |
| Fig. 2-3 sweeps (T up to 40000, 50 reps), Alg 1 timing table | reported | NOT reproduced | NOT REPRODUCED |

The threshold and Table-2 rows were run once from scratch scripts (see BASELINE_REPRODUCTION.md for the recipe); the other rows are checked by CPU tests, which are smoke/consistency checks, not confirmatory evidence.
