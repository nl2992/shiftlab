# CPC-Pay prior-art audit (adversarial, 2026-11-07)

Method: WebSearch only (no page fetch tool used). **Evidence level for every entry is SNIPPET-ONLY** (search-result summaries/abstract-level; no method section READ). Claims in the (a)-(f) table about internals therefore come from standard knowledge of these papers plus snippets, and are flagged where uncertain. Nothing here is a completed prior-art conclusion; a full-text read of the top 4 rows is still required.

## Sources seen (URL, evidence level)
| Ref | Work | URL | Level |
|---|---|---|---|
| GLR-klUCB | Besson, Kaufmann, Maillard, Seznec, JMLR 2022 | https://www.jmlr.org/beta/papers/v23/20-1384.html ; https://arxiv.org/abs/1902.01575 | SNIPPET-ONLY |
| CUSUM-UCB | Liu, Lee, Shroff, AAAI 2018 | https://arxiv.org/pdf/1711.03539 | SNIPPET-ONLY |
| M-UCB | Cao, Wen, Kveton, Xie, AISTATS 2019 | https://proceedings.mlr.press/v89/cao19a.html | SNIPPET-ONLY |
| ADSWITCH | Auer, Gajane, Ortner, COLT 2019 | https://proceedings.mlr.press/v99/auer19a.html | SNIPPET-ONLY |
| CTS | Mellor & Shapiro, AISTATS 2013 | https://arxiv.org/abs/1302.3721 | SNIPPET-ONLY |
| Switching-cost bandits | Dekel, Ding, Koren, Peres, STOC 2014 | https://arxiv.org/abs/1310.2997 | SNIPPET-ONLY |
| UPF | Regol et al., ICML 2025 | https://proceedings.mlr.press/v267/regol25a.html ; https://arxiv.org/abs/2505.14903 | SNIPPET-ONLY |
| CARA | Mahadevan & Mathioudakis, cost-effective retraining | https://arxiv.org/abs/2310.04216 | SNIPPET-ONLY |
| RCCDA | resource-constrained drift adaptation | https://arxiv.org/pdf/2505.24149 | SNIPPET-ONLY |
| Learning-debt retraining | cost-sensitive Bayesian retraining (2026) | https://arxiv.org/html/2604.06438v1 | SNIPPET-ONLY |
| Retrain policy study | empirical study, budget/latency (2026) | https://arxiv.org/pdf/2608.19488 | SNIPPET-ONLY |
| The Challenger | Digalakis et al., optimal stopping for replacing incumbent | https://arxiv.org/abs/2512.18390 | SNIPPET-ONLY |
| Model Picker | Karimi et al., AISTATS 2021 | https://arxiv.org/pdf/2010.09818 | SNIPPET-ONLY |
| CAMS | Contextual Active Model Selection | https://arxiv.org/html/2207.06030v4 | SNIPPET-ONLY |
| Switching cost as hypothesis test | arXiv 1808.09686 (inaction band = confidence interval) | https://arxiv.org/pdf/1808.09686 | SNIPPET-ONLY (title only) |
| Ranking by Lifts | champion->challenger switching cost in A/B tests | https://arxiv.org/pdf/2407.01036 | SNIPPET-ONLY |
| Delayed/partial-label drift survey | Waikato | https://researchcommons.waikato.ac.nz/items/cb76efe3-148d-49a8-b406-b1a6531e599f | SNIPPET-ONLY |

Not found/unverified: Wan et al. 2023 and Chick et al. 2017 originals (a search did not return them; only a secondary mention of "Wan et al. 2023" with hurdle cost in arXiv 2608.12949). Not searched: ADWIN-bandit variants, river/scikit-multiflow champion-challenger code, Monitored-UCB-with-delays, label-budgeted drift detectors beyond the survey.

## Q1/Q2: feature table (Y = present, P = partial/not core, N = absent; from snippets + background knowledge, unverified in full text)
| Work | (a) CP-cut/restart | (b) economic switch-cost payback w/ remaining horizon | (c) reversible switch, 2 fixed models | (d) hard paid label budget | (e) delayed labels | (f) disagreement-only labels |
|---|---|---|---|---|---|---|
| GLR-klUCB | Y (Bernoulli GLR, restart UCB indices) | N (regret objective, no switch cost) | P (arms, not fixed-model deploy) | N | N | N |
| CUSUM-UCB / M-UCB | Y | N | P | N | N | N |
| ADSWITCH | Y (checking phase, restart episode) | N | P | N | N | N |
| CTS (BOCPD+TS) | Y (BOCPD run-length) | N | P | N | N | N |
| Dekel et al. switching-cost bandits | N | P (unit switch cost, T^{2/3} regret, no payback rule) | Y | N | N | N |
| Regol UPF | N (forecasting, not cut) | Y (retrain cost vs. delta-quantile cost) | N (retrain, not 2-model reversible) | N | P | N |
| CARA / RCCDA / learning-debt | N | P-Y (cost-aware thresholds) | N | P (RCCDA resource budget) | N | N |
| The Challenger (2512.18390) | N | Y (optimal stopping, switch cost) | N (one-way) | P (data-acquisition cost) | N | N |
| Model Picker / CAMS | N (adversarial/stationary-ish) | N | P (selection, no deployment cost) | Y (label budget) | N | P (queries on informative/disagreement-ish instances) |
| Ranking by Lifts (2407.01036) | N | P-Y (champion->challenger cost) | N | N | N | N |
| **CPC-Pay** | Y | Y | Y | Y | Y | Y |

No single work seen covers more than 2-3 of the six columns. Union coverage is complete only by combining (GLR-klUCB cut) + (payback rule: Wan/Chick/Regol) + (Model Picker-style budgeted labels).

## Q3: is "restart evidence at detected change, then confidence bound for decision" standard?
Yes. GLR-klUCB (Bernoulli GLR change test, restart, then klUCB bound) and CUSUM-UCB/M-UCB do exactly this restart-then-bound pattern; CTS does the BOCPD analogue. CPC-Pay's GLR cut and BOCPD variant are not new components.

What differs (precise, and only this):
1. **Windowed cut, not global restart.** CPC-Pay keeps the estimated post-change suffix (cut at argmax split) rather than discarding all evidence; GLR-klUCB restarts from empty (with a possible partial-restart variant). Small difference; the suffix-keeping idea is common in CUSUM-style estimators (unverified for GLR-klUCB specifics).
2. **Decision functional.** The bound feeds a *finite-horizon payback test* `(2*LCB-1)*r_hat*(T-t) > c_s`, not an index for arm pulling. Payback rules are inherited (Wan/Chick/Regol); the combination with a change-cut window is the candidate delta.
3. **Label acquisition regime.** Labels only on disagreements, paced to a hard budget, with fixed delay; evidence variable is z on disagreements only. Model Picker has budgeted queries but no deployment switching cost or change cuts.
4. **Deployed model is not the sampled arm.** In bandits the sampled arm and the played arm coincide; here labels are free-of-choice relative to the deployed model (observed under both). This makes the problem closer to a full-information 2-expert problem with costly labels and switching than to a bandit, so the bandit regret theory does not transfer directly (and nobody has proven anything for CPC-Pay either).

## Q4: most dangerous reviewer objection
"This is GLR-klUCB/ADWIN-style detection with a Wald bound plus the Wan/Regol payback rule; each piece is known, and a simple sliding window or discounted/fixed-window LCB with the same payback rule is equivalent." Also: a naive "retrain when ADWIN fires, switch if sample mean better" champion-challenger baseline.

Neutralising experiments (all pre-registered, same label budget, delay, c_s, disagreement pacing):
- Ablate cut -> (i) fixed sliding windows (several lengths, plus best-in-hindsight length), (ii) discounted counts, (iii) ADWIN-cut + same payback, (iv) global restart a la GLR-klUCB. CPC-Pay must beat the best tuned-per-stream window in a pre-specified proportion of streams, or the cut is not earning its keep.
- Ablate payback -> plain LCB>0.5 without horizon/c_s; and Regol-UPF-style quantile rule fed the same labels.
- Include an oracle-switching-time reference to report regret gap, and stationary streams to show false-switch cost is controlled (Type-I-like check at the chosen c).
- Include a Model-Picker-style label allocation baseline under same budget to separate label-acquisition value from decision rule.

## Q5: verdict
**NOVEL-INTEGRATION** (not a novel component; weakly so). Every ingredient is known; the specific six-way combination (change-cut evidence + horizon payback + reversible 2-model switching + hard budget + delay + disagreement-only labels) was not found in the sources checked, but the search is shallow (snippets only, no ADWIN/river/MLOps-code or 2026 drift-label-budget survey read), so absence is weak evidence. If the ablations above show a tuned sliding window matches CPC-Pay, downgrade to KNOWN.

Positioning sentence (non-overclaiming): "We study a deployment decision with paid, delayed, disagreement-only labels and a switching cost, and evaluate a standard change-point-cut evidence window combined with a finite-horizon payback test against tuned sliding-window, ADWIN, and quantile-retrain baselines; we do not claim new detectors, bounds or regret guarantees."

## Closest priors
1. GLR-klUCB (Besson et al. 2022): same GLR cut + restart + bound mechanism; lacks economic payback, budget, delay, disagreement labels.
2. Regol et al. ICML 2025 (UPF): cost-aware sequential retrain decision with a quantile; lacks change cut, reversible two-model, label budget.
3. Model Picker / CAMS: budgeted label queries for model choice; lacks switching cost and change handling.
4. Dekel et al. 2014: switching cost theory; lacks drift detection and payback rule.
