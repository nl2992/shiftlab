# Next-method novelty audit

Literature sweep: [NEXT_METHOD_NOVELTY_lit.md](NEXT_METHOD_NOVELTY_lit.md) (subagent, WebSearch
snippets only; **no method section was read**, so every external claim below is provisional).
Earlier audit of the base rule: [novelty_audit.md](novelty_audit.md) (EQSDp = NOVEL-INTEGRATION;
Regol et al. ICML 2025 UPF is the closest prior).

## No finalist, so no final-algorithm audit

The directive's six questions apply to a selected finalist. None was selected (no candidate
passed the development gate), so the questions are answered per candidate family only, to
record why each would or would not have been defensible.

| Candidate | Inherited components | Closest complete prior | What would differ | Did the difference matter? |
|---|---|---|---|---|
| A1/A3/A4 adaptive discounting | forgetting factors, multi-scale monitoring | adaptive-forgetting estimators; ADWIN (Bifet–Gavaldà 2007) | coupling to the payback hurdle | no: +1.2 to +3.2 vs tuned Wald |
| A5/A6 change-point evidence | BOCPD (Adams–MacKay 2007), Bernoulli GLR | **GLR-klUCB** (Besson et al., JMLR 2022): GLR cut + restart + confidence index; CTS (Mellor–Shapiro 2013) | payback test instead of a bandit index; budgeted, delayed, disagreement-only labels; the post-change suffix is kept | no: tie or worse |
| B1 asymmetric hysteresis | confidence-bound switching | asymmetric thresholds (standard) | separate promotion and rollback levels | no |
| D1 ambiguity bursts | decision-value acquisition | earlier D2 decision-at-stake clause, GAVE-R; Model Picker (Karimi et al. 2021) | trigger on point-estimate vs bound disagreement | no (tie) |
| S label-free sentinel | drift-detector-triggered retraining (common MLOps practice) | detector-triggered retrain/reset | an alarm resets evidence and buys labels but never switches by itself | weakly (−1.2 n.s.) |
| E ESS-adjusted Wald | variance inflation for AR(1) / effective sample size (classical; Newey–West family) | the same correction in any sequential mean test | applied inside the economic switching hurdle | small: −0.8 mixed; −12 vs a mis-tuned Wald on dependent streams |
| F Bayes-filter payback | BOCPD, hazard-discounted horizon | Bayesian finite-horizon switching (Bayraktar–Ludkovski spirit) | — | no (tie); used as a benchmark |
| G OPE-selected switchers | IPW off-policy evaluation, algorithm selection (Corral-type model selection) | online model/algorithm selection via OPE | decision-independent pacing makes the shadow costs exactly IPW-estimable | no (4.21 vs 4.37) |

## New prior flagged for the base EQSDp/Wald rule

*The Challenger* (Digalakis et al., arXiv 2512.18390; SNIPPET-ONLY) frames replacing an
incumbent model as optimal stopping with a switching cost and data-acquisition cost. It is
one-way (no rollback) per the snippet. It must be read in full before any claim about the
base rule, alongside Regol et al. 2025.

## Verdict

No new algorithmic primitive or coupling survived the evidence bar. The defensible novelty
status of the programme's method is unchanged from the earlier audit: **EQSDp/Wald-LCB economic
switching = NOVEL-INTEGRATION**, with the Beta quantile ≡ Wald bound. The new evidence adds a
structural claim, not a novelty claim: the integration is frontier-efficient against 12 adaptive
alternatives on this contract.
