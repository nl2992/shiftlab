# Prior-Art Spot Check: Gap-Mix, PAVE, FreshCheck

Date of check: 2026-11-06. Scope: existence and abstract-level claims for ten named works, plus overlap risk with the three candidate modules. This is a spot check, not an exhaustive novelty search. No full-text reading was done unless stated.

## Method and verification levels

- Tool: WebSearch (standard mode), plus WebFetch on arXiv abstract pages where noted.
- ABSTRACT = arXiv abstract page fetched and read (summary by WebFetch, not verbatim).
- SNIPPET = existence and bibliographic details confirmed from search result titles and descriptions only. Abstract claims at this level are paraphrases of search summaries and should be re-checked before citing.
- Full-text reading was not done for any entry. Theorem statements were not checked.

## Overlap scale

- HIGH: same problem setting and same core mechanism; a reviewer would expect a comparison.
- MEDIUM: shares a mechanism or a sub-problem; needs a positioning sentence.
- LOW: adjacent framing only; no comparison required beyond citation.
- NONE: no overlap found.

---

## 1. Drift2Act (Drift-to-Action Controllers)

- Title: "Drift-to-Action Controllers: Budgeted Interventions with Online Risk Certificates" (method name: Drift2Act)
- Authors: Ismail Lamaakal, Chaymae Yahyati, Khalid El Makkaoui, Ibrahim Ouahbi, Yassine Maleh
- Year / venue: 2026. Workshop paper, CAO Workshop at ICLR 2026 (per arXiv comments). Not a main-track ICLR paper.
- URL: https://arxiv.org/abs/2603.08578 (arXiv:2603.08578, submitted 9 Mar 2026)
- Verification level: ABSTRACT
- Abstract claims: Treats drift monitoring as budgeted decision-making. A sensing layer infers drift types from unlabeled signals; an "active risk certificate" uses a few delayed labels from a recent window to form an anytime-valid upper bound on current risk. The bound gates actions: recalibration or adaptation below a threshold, abstain/handoff and rollback or retraining above it, with cooldowns. Authors report results on WILDS Camelyon17, DomainNet and a synthetic stream with label delay.
- Overlap with Gap-Mix: MEDIUM. Both use anytime-valid bounds from delayed labels under a label budget; Drift2Act's bound is a risk upper bound, not a Markov-dependent gap-based evidence process.
- Overlap with PAVE: MEDIUM. Both select which labels to pay for under a budget and tie the choice to a downstream action; Drift2Act's query rule is a recent-window certificate, not a decision-value query.
- Overlap with FreshCheck: MEDIUM. Both escalate to rollback on adverse evidence; Drift2Act's rollback is a gated action, not a reset of promotion evidence.
- Note: Drift2Act is the authors' own method name. The arXiv title is different, so search with the title, not "Drift2Act" alone.

## 2. Gong & Zhang, "The Cost of Information"

- Title: "The Cost of Information: Phase Transitions in Contextual Bandits with Paid Observations"
- Authors: Xueping Gong, Jiheng Zhang
- Year / venue: 2026. ICML 2026, PMLR vol. 306, pp. 36013-36044.
- URL: https://proceedings.mlr.press/v306/gong26i.html ; ICML poster https://icml.cc/virtual/2026/poster/63917
- Verification level: SNIPPET (proceedings and poster pages seen; full text not read)
- Abstract claims: Learner pays to observe actions each round; regret includes learning loss plus observation cost. In the adversarial setting, a near-optimal algorithm shows a worse regret rate than cost-free contextual bandits even for small costs. Threshold effect: free observation budgets below a threshold lower total cost without changing the regret rate; above it, the cost-free rate is recovered.
- Overlap with Gap-Mix: LOW. Bandit regret with paid observations; no Markov dependence or sequential change evidence.
- Overlap with PAVE: HIGH. Paid observation with a cost-aware regret objective and a budget threshold is close to a label-request governor's cost trade-off. PAVE differs by delayed arrival, pending-label tracking and a finite horizon with a hard budget, which this bandit setting does not model. Must be cited and compared.
- Overlap with FreshCheck: NONE found.

## 3. Sethi et al., sequential testing with Markovian data

- Title: "Asymptotically Optimal Sequential Testing with Markovian Data"
- Authors: Alhad Sethi, Kavali Sofia Sagar, Shubhada Agrawal, Debabrota Basu, P. N. Karthik
- Year / venue: 2026 (arXiv v1 posted 19 Feb 2026; ICML 2026 poster listed). Math.ST listing on arXiv; later revisions exist (search snippet mentions v3 dated 12 Jun 2026, not checked).
- URL: https://arxiv.org/abs/2602.17587 ; ICML page https://icml.cc/virtual/2026/poster/63309
- Verification level: ABSTRACT (WebFetch) for v1 content; ICML listing SNIPPET.
- Abstract claims: One-sided alpha-correct sequential testing for an ergodic finite-state Markov chain, null on a transition-matrix set P versus alternative Q. Non-asymptotic instance-dependent lower bound on expected stopping time under the alternative, asymptotically tight as alpha goes to 0, depending on stationary distribution and transition structure. A test attains the bound. Applications: MCMC misspecification and linearity tests in MDPs.
- Important: the abstract does NOT mention e-processes, e-values or anytime-valid testing, and does not name the test statistic (GLR or otherwise). Whether its optimal test is likelihood-ratio based is unverified and should be checked in the full PDF.
- Overlap with Gap-Mix: HIGH. Same setting (sequential evidence under Markov dependence, optimal stopping time). Gap-Mix's distinct claims would have to be the use of realised gaps between actively queried labels, delayed/sparse feedback and the restart mixture. This is the closest threat and must be positioned explicitly.
- Overlap with PAVE: LOW.
- Overlap with FreshCheck: LOW.

## 4. Gafni, Iyengar & Zeevi, cost of learning under multiple change points

- Title: "The Cost of Learning under Multiple Change Points"
- Authors: Tomer Gafni, Garud Iyengar, Assaf Zeevi (Columbia)
- Year / venue: 2026. ICML 2026, PMLR vol. 306, pp. 32542-32580.
- URL: arXiv:2602.11406, https://arxiv.org/abs/2602.11406 ; ICML https://icml.cc/virtual/2026/poster/60699
- Verification level: SNIPPET (arXiv and ICML pages in results; abstract not fetched)
- Abstract claims (from search summary): Noisy samples with unknown mean shifts, evaluated by cumulative regret rather than detection. Argues classical detect-then-estimate methods can fail catastrophically because contaminated post-change data is used later. Proposes Anytime Tracking CUSUM (ATC), claimed nearly minimax-optimal in regret; non-uniform cost means small or short shifts need not be detected.
- Overlap with Gap-Mix: MEDIUM. Restart-style CUSUM logic and the cost of missed changes are close to Gap-Mix's restart mixture; the regret objective and full-information sampling differ.
- Overlap with PAVE: LOW.
- Overlap with FreshCheck: LOW. Its contamination point is relevant to whether promotion evidence should be discarded, but it is not a keep/rollback procedure.

## 5. WATCH

- Title: "WATCH: Adaptive Monitoring for AI Deployments via Weighted-Conformal Martingales"
- Authors: Drew Prinster, Xing Han, Anqi Liu, Suchi Saria
- Year / venue: 2025. ICML 2025, PMLR vol. 267, pp. 49830-49859.
- URL: https://arxiv.org/abs/2505.04608 (v4, 25 Aug 2025) ; ICML https://icml.cc/virtual/2025/poster/45832
- Verification level: SNIPPET (titles, descriptions, ICML and arXiv pages seen; abstract not fetched)
- Abstract claims (from search summary): Weighted-conformal test martingales extend conformal test martingales beyond exchangeability for monitoring deployed models. Aims: detect harmful shifts faster than tracking risk, adapt to benign shifts to avoid false alarms, and separate input from concept shift. Reports improvements over baselines on real data.
- Overlap with Gap-Mix: LOW. Martingale changepoint monitoring with no label-budget or Markov component.
- Overlap with PAVE: LOW.
- Overlap with FreshCheck: MEDIUM. Monitoring after deployment with a decision on harmful versus benign shift; FreshCheck's keep/rollback step is an action layer WATCH does not define.

## 6. PPRM (prediction-powered risk monitoring)

- Title: "Prediction-Powered Risk Monitoring of Deployed Models for Detecting Harmful Distribution Shifts"
- Authors: Guangyi Zhang, Yunlong Cai, Guanding Yu, Osvaldo Simeone
- Year / venue: arXiv 2026 (2602.02229, submitted 2 Feb 2026). ICML 2026 venue NOT CONFIRMED: searches found only the arXiv record and aggregator pages. Do not cite as ICML 2026 unless the accepted-paper listing is found.
- URL: https://arxiv.org/abs/2602.02229 ; html https://arxiv.org/html/2602.02229v1
- Verification level: SNIPPET (aggregator summaries; one aggregator mentions a v2 replacement; abstract page not fetched)
- Abstract claims (from search summary): Semi-supervised risk monitoring using prediction-powered inference, with a small labelled set correcting predictions on unlabelled data; tighter bounds than supervised risk monitoring; threshold test against an upper bound on nominal risk with assumption-free finite-sample false-alarm control; experiments on image classification, LLM and telecom tasks.
- Overlap with Gap-Mix: MEDIUM. Harmful-shift monitoring with a labelled-subset correction and finite-sample false-alarm guarantee is close to a sequential evidence claim, but PPRM is not Markov-dependent and is not sequential in the e-process sense per the summary.
- Overlap with PAVE: MEDIUM. Labelled-subset allocation for risk estimation is adjacent to deciding which labels to request.
- Overlap with FreshCheck: LOW.

## 7. The Challenger

- Title: "The Challenger: When Do New Data Sources Justify Switching Machine Learning Models?"
- Authors: Vassilis Digalakis Jr, Christophe Pérignon, Sébastien Saurin, Flore Sentenac
- Year / venue: arXiv December 2025 (2512.18390, cs.LG / stat.ML). Also an HEC Paris working paper (HAL hal-05562736; SSRN 5946174). No peer-reviewed venue confirmed.
- URL: https://arxiv.org/abs/2512.18390
- Verification level: SNIPPET
- Abstract claims (from search summary): Incumbent versus challenger model with new data sources arriving over time; switching framed as optimal stopping with data, retraining and switching costs. Three methods: one-shot, greedy sequential, and look-ahead sequential. On a credit-scoring dataset, look-ahead performs best and approaches a full-foresight oracle.
- Overlap with Gap-Mix: LOW.
- Overlap with PAVE: MEDIUM. Costed acquisition of new data with look-ahead is adjacent to PAVE's query valuation, though acquisition here is of features, not delayed labels under a hard budget.
- Overlap with FreshCheck: MEDIUM-HIGH for the incumbent/challenger switch framing. It addresses when to switch, not what evidence to keep after promotion, so FreshCheck's distinct claim is the post-switch evidence reset.

## 8. Lau & Tay, quickest change detection with observation-switching cost

- Title: "Asymptotically Optimal Sampling Policy for Quickest Change Detection with Observation-Switching Cost"
- Authors: Tze Siong Lau, Wee Peng Tay
- Year / venue: arXiv 2019 (1912.11693, first submitted Dec 2019, revised to Jan 2021). Library record lists IEEE Transactions on Signal Processing, 2021.
- URL: https://arxiv.org/abs/1912.11693
- Verification level: SNIPPET (arXiv and library records; abstract not fetched)
- Abstract claims (from search summary): QCD where each step selects an action from a permitted set and switching has a cost, with an average switching-cost constraint. GLR CuSum stopping with a designed sampling policy is asymptotically optimal; policy design is a quadratic program; window size one suffices for finite windows. Related earlier work: Ren, Johansson and Shi, "Quickest Change Detection With Observation Scheduling" (IEEE TAC 2017), not checked beyond the search summary.
- Overlap with Gap-Mix: MEDIUM-HIGH. Sampling-policy design with switching cost and a GLR-type stopping rule is close to Gap-Mix's use of realised gaps between queried labels. Gap-Mix's distinct element must be Markov-dependent evidence with delayed labels.
- Overlap with PAVE: LOW-MEDIUM. Sampling under cost constraints, but on observation actions rather than label requests with delayed arrival.
- Overlap with FreshCheck: LOW.

## 9. Zrnic & Candès, Active Statistical Inference

- Title: "Active Statistical Inference"
- Authors: Tijana Zrnic, Emmanuel Candès
- Year / venue: 2024. ICML 2024 (oral), PMLR vol. 235, pp. 62993-63010.
- URL: https://proceedings.mlr.press/v235/zrnic24a.html ; arXiv 2403.03208 ; ICML https://icml.cc/virtual/2024/oral/35546
- Verification level: SNIPPET (proceedings and ICML pages in results)
- Abstract claims (from search summary): Uses a model to choose which unlabelled points to pay to label under a budget, with valid confidence intervals and tests for any black-box model; narrower intervals than non-adaptive collection; generalises prediction-powered inference. Reports sample savings (over 80% in one summary); these numbers are from secondary write-ups and not checked against the paper.
- Overlap with Gap-Mix: LOW.
- Overlap with PAVE: MEDIUM-HIGH. Budgeted, model-driven label acquisition with valid inference is close to PAVE's query valuation. PAVE differs in valuing queries by decision value, delayed arrival, pending-label tracking and a horizon. Needs a direct comparison.
- Overlap with FreshCheck: NONE.

## 10. Csillag, Struchiner & Goedert, Prediction-Powered E-Values

- Title: "Prediction-Powered E-Values"
- Authors: Daniel Csillag, Claudio Jose Struchiner, Guilherme Tegoni Goedert
- Year / venue: 2025. ICML 2025, PMLR vol. 267, pp. 11493-11514.
- URL: https://proceedings.mlr.press/v267/csillag25a.html ; arXiv 2502.04294 ; ICML https://icml.cc/virtual/2025/poster/43872
- Verification level: SNIPPET
- Abstract claims (from search summary): Extends prediction-powered inference from Z-estimation to e-value constructions; any e-value-based procedure gets a prediction-powered counterpart; inherits anytime-validity and post-hoc validity; covers hypothesis tests and confidence sequences.
- Overlap with Gap-Mix: MEDIUM. Directly relevant if Gap-Mix's sequential evidence uses labelled and unlabelled data or any PPI correction. Without that, LOW. The Markov-dependent case is not covered by the summary.
- Overlap with PAVE: LOW-MEDIUM.
- Overlap with FreshCheck: LOW.

---

## Not found

None of the ten works was NOT FOUND. Two caveats instead:
- PPRM: ICML 2026 venue not confirmed (arXiv only).
- Sethi et al.: the paper exists, but the abstract does not confirm the e-process framing the Gap-Mix description assumes.

## Closest threats per module

| Module | Rank | Work | Overlap | Why |
|---|---|---|---|---|
| Gap-Mix | 1 | Sethi et al. (arXiv 2602.17587) | HIGH | Same Markov sequential-testing setting and optimal stopping; no e-process in abstract, so the distinction must be stated |
| Gap-Mix | 2 | Lau & Tay (arXiv 1912.11693) | MEDIUM-HIGH | Switching-cost sampling with GLR CuSum; closest match to the realised-gap sampling idea |
| Gap-Mix | 3 | Gafni et al. (arXiv 2602.11406) | MEDIUM | Restart-style CUSUM under multiple changes; closest to the restart mixture |
| PAVE | 1 | Gong & Zhang (ICML 2026, v306) | HIGH | Paid observations with cost-aware regret and budget threshold |
| PAVE | 2 | Zrnic & Candès (ICML 2024, v235) | MEDIUM-HIGH | Budgeted model-driven label acquisition with valid inference |
| PAVE | 3 | The Challenger (arXiv 2512.18390) | MEDIUM | Costed look-ahead acquisition timing |
| FreshCheck | 1 | Drift2Act (arXiv 2603.08578) | MEDIUM | Rollback escalation gated by an anytime-valid risk bound |
| FreshCheck | 2 | WATCH (ICML 2025, v267) | MEDIUM | Post-deployment monitoring with harmful versus benign shift separation |
| FreshCheck | 3 | The Challenger (arXiv 2512.18390) | MEDIUM-HIGH | Incumbent/challenger switch framing; FreshCheck's distinct claim is the post-switch evidence reset |

## Action items for the branch

- Read the full text of Sethi et al. to check whether the optimal test is likelihood-ratio or e-process based. This decides whether Gap-Mix's Markov claim survives.
- Read the full text of Gong & Zhang and Zrnic & Candès before any PAVE comparison claim.
- Check the accepted-paper list for PPRM before citing it as ICML 2026.
- Search specifically for "post-promotion evidence reset", "fresh evidence after deployment" and "restart e-process Markov" for FreshCheck and Gap-Mix; this check did not cover those phrasings exhaustively.
