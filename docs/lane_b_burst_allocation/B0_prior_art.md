# B0 prior-art pre-screen: evidence-responsive hard-budget allocation under unknown bursts

**Date:** 2026-10-28. **Status:** pre-screen, not an exhaustive novelty search.

**Verification levels used:**
- *Abstract+*: arXiv abstract plus a fetch-tool extraction of the HTML/ar5iv page. The fetch tool summarises pages, so it does not give verbatim theorem text.
- *Abstract*: abstract only.
- *Lane A*: Lane A's audit read, not redone.

No source below was read in full by me. Theorem-level claims are marked as extracted, not independently verified.

## Test applied

A source triggers EXIT only if it provides all four of:
- (a) a data-adaptive sampling rule under a **hard pathwise** budget;
- (b) a **time-uniform / anytime** false-alarm guarantee under a **composite or mean-type** null;
- (c) **delay guarantees in both regimes**: harmless pre-change bursts, where spending wastes budget, and harmful post-change bursts, where throttling delays detection;
- (d) **delayed labels**.

## Source table

| Source | Model | Budget type | Sampling adaptivity | Null and guarantee | Delay result | Label delay | Harmless-burst regime | Level |
|---|---|---|---|---|---|---|---|---|
| Banerjee-Veeravalli DE-CuSum, 1211.3729 | Minimax QCD; iid pre/post, known densities (per Hou et al.'s description) | Average: fraction of time observed before the change | Yes: skip length is a function of the CUSUM statistic | FAR = 1/E[tau] (ARL). Not anytime, and known likelihoods | WADD asymptotically optimal as FAR goes to 0 for fixed duty cycle | No | Implicit only: off-periods save budget when the statistic is low. There is no burst model; iid pre-change data is assumed. | Abstract (and Hou's restatement) |
| Banerjee-Veeravalli on-off, 1105.1361 | Bayesian (Shiryaev) QCD, known densities | Average number of pre-change observations, handled by a Lagrangian | Yes: two-threshold rule on the posterior | PFA bound | Asymptotically matches Shiryaev as PFA goes to 0 | No | Same as above | Abstract+ |
| Hou-Bidkhori-Banerjee RDE-CUSUM, 2412.20207 | QCD, known pre-change density f, composite post-change family with a least-favourable member | PDC = limsup of the average pre-change duty cycle, conditioned on no false alarm. **The page states there is no per-path cap.** | Yes: M_{n+1} = 1{D_n >= 0}, where D_n is a (truncated) CUSUM statistic. Skipped steps drift up by mu. | FAR = 1/E[tau]. Theorem 4.2: FAR <= alpha for A = abs(log alpha). **Pre-change law known**, so not a composite or mean null. | Thm 4.1 converse, Thm 4.4 upper bound, Thm 4.5 asymptotic robust optimality as alpha goes to 0, for each fixed beta | Not addressed | Handled only through an average-duty-cycle constraint. No burst or non-iid pre-change model. | Abstract+ with extracted theorem statements |
| 2509.14186 and 2610.16055 (multi-experiment QCD with unknown post-change model) | Choose one of several costed experiments per step | Average fraction of time each experiment is used before the change | Adaptive (not stated in the abstract) | ARL to false alarm; known pre-change | Asymptotic WADD | No | No | Abstract |
| Geng-Bayraktar-Lai, arXiv 1309.5396 (IEEE TIT 2014) | Bayesian QCD, geometric prior, **known f0, f1**, iid | **Hard pathwise: at most N samples on every path** (limited sampling right) | Yes: next sampling gap minimises a posterior-dependent cost (Thm 1). The stop rule is a posterior threshold, with an exception once all N rights are used. | PFA = P(tau < Lambda) <= alpha (Lagrangian). Bayesian and known-likelihood, so not anytime and not composite. | ADD converse (Eq. 32). Prop. 2: uniform sampling with gap varsigma achieves the matching rate when N >= abs(log alpha) / (abs(log(1-rho)) * varsigma). First order as alpha goes to 0. | Not addressed | **Not modelled.** Remarks 9-10 note that aggressive pre-change sampling can deplete rights, but argue the penalty is negligible as alpha goes to 0. | Abstract+ (ar5iv first 100k of 138k characters read via the fetch tool) |
| Ren-Johansson-Shi et al. censoring and adaptive-censoring QCD (1411.3107, 1503.04999) | CUSUM with a censoring sensor, minimax | Average energy or communication cost before the change | Yes: censoring depends on the statistic | ARL | Asymptotic WADD | No | No | Search snippet only |
| Gopalan et al. Bandit QCD, 2107.10492; Xu-Mei-Moustakides; Zhang-Mei; Kartzman et al. 2601.22561 | Multi-stream QCD, probe a limited set of streams per step | Per-step cap on the number of streams, not a total budget | Yes | ARL or false-alarm rate, known models | Lower bound and order-optimal rules | No | No | Search snippet only |
| Huang-Veeravalli, finite-horizon QCD, 2511.12803 | Finite-horizon QCD; extended to a sub-Gaussian, unknown-mean-type family | **No sampling budget** | Not applicable | P(false alarm before the horizon). Partly nonparametric. | Latency quantile; universal lower bound; order-optimal detectors | No | No | Abstract+ |
| Shin-Ramdas-Rinaldo e-detectors (NEJSDS 2024) | Nonparametric, composite null, anytime ARL via Ville | None (all data observed) | None | Anytime ARL control for supermartingale mixtures | Prop. 2.14 delay bound for iid likelihood ratios | No | Not applicable | Lane A (cheng and change-point baseline audits); I did not re-read it |
| Lau-Tay 1912.11693 | GLR-CUSUM plus observation-switching cost | Long-run average switching cost | Yes (two-threshold, observation-dependent) | ARL, known distributions | Asymptotic WADD | The audit says there is no delayed-label queue | No | Lane A |
| Cheng et al., ICML 2023 | Oblivious adversarial K-action losses | **Hard total observation count B** | Importance-weighted uniform batch sampling | Expected regret, not a safety event | Minimax Theta(T sqrt(K/B)) | No | Not applicable | Lane A |
| Gong et al., ICML 2026 (paid observations) | Contextual bandits, paid observation | Cost penalty plus a free-observation allowance | Yes | Regret | Phase transitions in the budget | No | Not applicable | Lane A |
| Prabhu et al. (sequential multi-hypothesis, controlled sensing) | Composite hypotheses | Expected stopping time plus switching cost | Yes | Per-parameter error <= alpha; asymptotic optimality | Expected cost / log(1/alpha) | No | Not applicable | Lane A |
| DISCERN, Balachandran, 2609.17560 (single author, v1, unreviewed) | Paired incumbent vs candidate risk difference; labels bought only on disagreements | **Not a hard cap.** Label counts appear only as a bound (Thm 7). The pi_min floor is a rate floor. | Routing is any **predictable** rule. It may depend on the past and on judge scores, but not on the current label. | **Thm 4: anytime-valid confidence sequence, mean-type, under any stopping and any routing rule.** Base theory is iid; a running weighted average under drift; windowed restarts. | Thm 7 label complexity of order rho^2/eps^2; Thm 8 for any adaptive labeler; Thm 9 for pairing-blind schemes | **Not covered.** Labels arrive right after routing. | Not analysed. The paper says the disagreement rate "does not order updates by harm." | Abstract+ with extracted theorem statements (about 100k of 162k characters read) |
| Drift2Act, 2603.08578 (ICLR 2026 workshop) | Drift to action controller with an active risk certificate | Budget not formalised in the abstract | Yes | Claims an "anytime-valid upper bound U_t". The abstract reports empirical results only. | None in the abstract | **Yes, delayed labels in the evaluation protocol** | No | Abstract (matrix flags a full read as pending) |
| Li-Kadambi-Saidi, Active Sequential Two-Sample Testing (2301.12616) | Two-sample test with queried labels | Fixed label budget | Yes | Anytime-valid p-value | None for change detection | No | No | Search snippet only |
| MLDemon (2104.13621) | Performance estimation with a label budget | Budget on labels | Yes | Minimax rate optimal up to logs | Estimation error, not detection delay | No | Not a delay analysis | Search snippet only |
| Non-stationary BwK, Liu-Jiang-Li, 2205.12427 | Stochastic with global variation budget | Hard resource knapsack | Yes | Regret vs a dynamic benchmark | No detection delay | No | No | Abstract+ |
| Immorlica et al. Adversarial BwK; Celli et al. 2202.13710 | Adversarial or best-of-both-worlds BwK | Hard budget | Yes (primal-dual) | Competitive ratio O(log T) vs a static benchmark, with a matching lower bound; constant ratio when the budget is linear in T | None | No | The objective is reward, not detection | Abstract+ |
| Zhang-Cheung, Piecewise-Stationary BwK, NeurIPS 2024 | Stage changes; inventory-reserving algorithm | Resource knapsack | Yes | Competitive ratio O(log(eta_max/eta_min)) vs a **dynamic benchmark**, with a matching lower bound | No detector or false-alarm guarantee | No | **Reserve for a future stage with higher reward-per-consumption.** This is structurally the burst-allocation intuition, with the stage value known from the reward feedback. | Abstract+ |
| Online knapsack / budget pacing (Shi et al. 2207.04690; Lu et al. primal-dual pacing) | Allocation of a budget over arrivals | Hard budget | Yes (dual-multiplier or threshold) | Competitive ratio or regret | None | No | Objective is reward | Abstract / search snippet |
| Searched ("label-efficient drift detection"; 2511.02452, IUPM AISTATS 2025, ADAL-R, ADWIN-based budget raising) | Drift detection with active labelling | Heuristic budgets | Yes | Empirical only | None | Mostly no | Empirical | Search snippets only |

## Closest sources and where each stops

1. **Geng-Bayraktar-Lai (1309.5396).**
   - It is the only source with a hard pathwise budget and an adaptive posterior-driven sampling rule.
   - Everything else in its model is classical: known f0 and f1, iid data, a geometric prior, a Bayesian PFA.
   - It proves nothing about a pre-change burst. Its Remark 9 acknowledges the depletion mechanism and then dismisses it asymptotically.
   - It has no anytime validity, no composite null, no label delay.
2. **DE-CuSum and RDE-CUSUM (1211.3729, 2412.20207).**
   - They give an evidence-responsive on-off rule with a delay-optimality theorem.
   - The budget is an average duty cycle, so there is no pathwise guarantee that the budget survives a burst.
   - The false-alarm guarantee is ARL with a known pre-change density.
   - Neither addresses delayed feedback.
3. **DISCERN (2609.17560).**
   - It supplies the anytime-valid, mean-type validity engine with predictable routing, which is exactly the validity half of the Lane B target.
   - It is not change detection, has no hard cap, no delayed labels, and no delay analysis.
   - It explicitly declines to order updates by harm from disagreement.

Zhang-Cheung is close for the structure of the allocation problem rather than for detection. It is the main risk for the separation result (see below).

## Verdict: PASS (with combination risk)

No source provides (a)-(d). Each condition fails in at least one place:

| Requirement | Nearest source | What it lacks |
|---|---|---|
| Evidence-responsive rule | DE-CuSum, RDE-CUSUM, Geng | Yes, but each is tied to known (or least-favourable) likelihoods |
| Hard pathwise budget | Geng (N rights), Cheng (B count), BwK | Geng is the only one combined with detection. Its model is Bayesian, known-likelihood and iid. |
| Anytime / Ville validity, mean-type null | DISCERN (confidence sequence), e-detectors | Neither restricts or adapts sampling to a hard cap with a delay analysis. e-detectors observe everything. |
| Delay bounds in both burst regimes | None | Nobody models harmless pre-change bursts. Geng's Remarks 9-10 only argue the pre-change depletion cost is negligible as alpha goes to 0. |
| Delayed labels | Drift2Act (empirical, workshop) | No theorem for delay or false alarm. Not in any detection-delay result. |

**Precise residual (the conjunction nobody gives):** a sampling rule that
- uses a **hard pathwise** budget,
- keeps **anytime (Ville-type) validity under a composite mean-type null** while the rate is predictable from past wealth,
- is analysed against a **burst model in which pre-change disagreement bursts are harmless and post-change bursts are harmful**, with delay bounds in both regimes,
- under **delayed labels** (budget charged at request).

**Which mismatches are substantive:**
- *Substantive*:
  - the pathwise budget versus the average duty cycle in the whole DE-CuSum family; under a pre-change burst, an average-rate rule can overspend and leave nothing for the post-change period;
  - the composite mean-type null versus known likelihoods;
  - the burst model, which is absent from every source (all assume iid pre-change data).
- *Contract mismatch only*: delayed labels alone. A fixed delay d on label release can be absorbed into existing arguments, as Lane A's baseline does, and adds roughly d to the delay. It is not novelty by itself.
- *Weak*: the ARL versus Ville distinction. e-detectors already supply anytime ARL. The novelty must come from sampling control under a hard cap, not from validity.

**Likely "combination" risks (do not overclaim):**
- Validity of a predictable `q_t` driven by past wealth is standard: DISCERN's Theorem 5 covers it, and Lane A's e-detector specialization already shows query-skipping preserves the supermartingale. If B2's validity proof is only this, it contributes nothing.
- DE-CuSum on-off control plus a Geng-style cap plus an e-detector is a two-line composition. The contribution must therefore be the **burst-model delay theorem**, i.e. the oblivious-rule lower bound and a matching evidence-responsive upper bound. Both are open as far as these sources show.
- **Zhang-Cheung and BwK threat to the B1 separation.** BwK with a dynamic benchmark has an Omega(log(eta_max/eta_min)) competitive-ratio lower bound for oblivious (non-reserving) policies when the stage value is unknown. Check whether the burst lower bound is a corollary of that. The difference to establish is that in Lane B the "reward" (harmfulness) is revealed only by purchasing labels, with a delay, and the objective is detection delay rather than reward.
- Lower bounds that oblivious schedules must lose in a regime: **none found.** The closest are Geng's uniform-sampling upper bound (a matching rate under known likelihoods, so uniform is near-optimal there) and the BwK dynamic-benchmark lower bound. This supports the claim that the E2 loss pattern lacks a published theorem, but it also warns that, under an iid pre-change model, uniform sampling is first-order optimal (Geng). The separation must therefore depend on non-iid pre-change bursts.

**Caveats on this screen:**
- No source was read in full. Several rows are search snippets only (Ren et al., Gopalan et al., MLDemon, Li et al., 2509.14186).
- The fetch tool paraphrases pages, so the theorem statements above are extractions, not quotations.
- DE-CuSum's own paper (1211.3729) could not be text-extracted; its details rest on its abstract and on Hou et al.'s restatement.
- Drift2Act's full text is unread. If it contains a formal anytime-validity proof with delayed labels, that row needs upgrading, though it still has no delay theorem.
- A full read of Geng et al. Section on limited sampling right (the remaining 38k characters), Zhang-Cheung's lower-bound proof, and DISCERN Theorems 7-9 is recommended before B1.

**Recommended next step (B1):** state the burst model so that uniform sampling is not near-optimal (non-iid pre-change bursts), and test the oblivious-rule lower bound on a finite instance. Compare against Zhang-Cheung's lower bound before claiming it is new.
