# Codex screen of C0 candidate RLS (round 1)

`codex exec --sandbox read-only`, xhigh, worktree `7b5f7db`, 2026-10-29. Verbatim:

**NARROW. C1 has a plausible forecasting advantage, but T-RLS is not correct as written and G1/G2 remain open.**

1. **Comparator and prior art**

   `D_post` is legitimate as a restricted class of reactive detection controllers. It is too restrictive to establish novelty against equally informed recurrence-aware methods. Known-model planners need not wait for post-change labels.

   Its literal definition also has a loophole: switching **one round before** a predicted boundary can satisfy the requirement using a label from the departing segment. Define the restriction behaviorally before proving anything.

   **I found no verified published theorem giving RLS’s exact bound under hard budget, delay, and causal-null promotion.** Closest verified methods:

   - **Oh, Meetoo Appavoo and Gilbert, “Periodic Bandits and Wireless Network Selection,” ICALP 2019 — Periodic EXP4:** already learns periodic schedule comparators; its theorem lacks this budget/delay/safety contract. [Primary source](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ICALP.2019.149)
   - **Cheng, Zhou and Ji, ICML 2023, Theorem 2:** hard observation budget plus switching costs, against a fixed action; no delayed release or promotion constraint. [Paper](https://proceedings.mlr.press/v202/cheng23f/cheng23f.pdf)
   - **Waeber, Frazier and Henderson, “Bisection Search with Noisy Responses,” 2013, Theorem 5.1:** geometric localisation of a fixed target using freely chosen query locations. That theorem does not establish chronological cross-recurrence localisation. [Paper](https://people.orie.cornell.edu/shane/pubs/BisectionSearch.pdf)
   - **Hayashi, Kawahara and Kashima, ACPD, ACML 2019:** arbitrary-input black-box localisation; the paper explicitly excludes time as the input. [Paper](https://proceedings.mlr.press/v101/hayashi19a/hayashi19a.pdf)

   Thus: unresolved equivalence, **not established novelty**. Schedule experts and a duration-aware forecasting controller are mandatory competitors.

2. **Theorem target**

   Linear savings across recurrences are plausible **after learning**, when forecasting error is consistently below reactive latency. The stated theorem has several defects:

   - **Wrong jitter geometry:** independent dwell errors give  
     \(b_j=\phi+jL+\sum_{i\le j}\xi_i\). Phase uncertainty accumulates without resynchronisation. This differs from bounded boundary jitter \(b_j=\phi+jL+\eta_j\).
   - **Future information in the bound:** replace final `M` in every boundary’s error term with probes **released before that decision**, and sum those errors. Include period-estimation error.
   - **Chronological bisection is unproved:** an updated posterior median can already be in the past. Waiting for its next recurrence costs calendar time, potentially whole cycles.
   - **Reactive lower bound needs repair:** `1/(2r)` assumes a particular random-phase periodic schedule; adaptive recurrence-aware sampling need not pay it. Account for skipped segments, finite dwell lengths and economically optimal nonswitching.
   - **Certification:** distinguish labels from calendar time, include budget-exhaustion/noncertification probability, and specify divergence against the null. Segment-law KL alone does not establish certification time.
   - **Costs:** charge both learner and oracle switches. `Sk` is not automatically excess regret.
   - **No proved “iff” transition:** jitter width alone cannot determine the crossover; its law, budget, learning cost and verification power matter. The recurrence-break guarantee likewise needs detection-power and remaining-budget assumptions.

   **Matching lower-bound obligation:** prove an all-policy minimax bound under the same causal null and costed comparator, combining phase-identification information, fresh unpredictable jitter, certification power and hard-budget scarcity. For a suitable nondegenerate jitter subfamily, \(\Omega(S\Delta\min\{\sigma,d\})\) is plausible. A support bound alone does not give that pointwise floor. Certification requires a power target, e.g. an information requirement involving \(\mathrm{kl}(1-\beta,\alpha)\).

3. **C3 and real-data arithmetic**

   - **C3:** the constant-sum identity is correct for gross losses over a coupled interval **before the first informative feedback arrives**. It does not extend automatically until “decisive evidence.” Constant sum yields a minimax floor, not proof that the existing gated rule attains it. Rejecting C3 because it changes G1’s risk event is sound; the broader minimax dismissal is overstated.
   - **Binance:** arithmetic correct: KL approximation `0.0006803`, and `log(20)/KL = 4,404`. **Interpretation incorrect:** this is an expected evidence scale, not a hard minimum. Under the same iid Gaussian approximation, 3,428 labels give about **70% power** for a fixed one-sided 5% test. This is illustrative, not validation under the repository’s causal null. Dependence, selective opportunities and the actual budget remain unresolved.
   - **OPSD:** opposite half-window averages establish **neither one change point nor detectable recurrence**. Half-specific variances are unavailable. Even `log(20)/0.08` is approximately **37**, not 35. Treat these as descriptive signal diagnostics.

4. **Required narrowing and kills**

   First fix **known period, latent offset, explicit emission law and one precise jitter model**. Prove causal localisation and promotion validity before opening a prototype efficacy grid.

   Kill C1 if a contract-matched schedule learner or duration-aware controller attains the same rate by standard composition. Otherwise require a predeclared practical net-cost advantage, causal-null validity, and a fixed noninferiority margin on broken-recurrence controls. A two-SE rule is insufficient. Frozen real-task relevance remains unestablished; K4 does not prove impossibility.

Reviewed worktree `7b5f7db`; no files edited and no `data/` reads.
