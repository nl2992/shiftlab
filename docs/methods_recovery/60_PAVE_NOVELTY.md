# PAVE adversarial prior-art audit

Date 2026-11-08. Search-based audit; no code run. Source status: READ = method text read via fetch; ABSTRACT =
abstract/landing page only; SNIPPET = search-result summary only (not verified in full text). Several primary PDFs
(GP-BUCB, Castellani PDF) returned unreadable binary; claims about their internals come from abstracts or
secondary summaries and must be re-checked before citing.

## 1. PAVE mechanism as implemented (pave.py, integrated.py; docs gaver/20, MR/41, MR/42)

| Component | Exact content |
|---|---|
| Query rule | Per round t: request iff `V_0 - max(V_1,V_2) > kappa (V_0 - V_none)/K_0`; V_s = value of a deterministic label-calendar rollout whose first request is s in {0,g,2g} rounds later (follow-up gap g=ceil(H/B_rem) or g//4). Note: this is a calendar-shift rollout over a Normal-Kalman belief with closed-form expected opportunity loss sqrt(V)L(z), NOT a sampled Monte-Carlo rollout; the brief's "Monte-Carlo" wording should be corrected. |
| Value model | Normal belief on benefit mu of candidate over incumbent; variance drifts +q/round, Kalman cut at each label arrival; regret per round vs switch threshold h +/- s/R; minus c per label. Pre-promotion regret scaled by e-process reachability clip(0.1 x labels / log-wealth-needed, 0, 1). Heuristic, no validity role. |
| Pending-aware posterior | Pending labels add to posterior sample size n_pend and last-update time; never evidence. |
| Deadline | A label arriving at a=t+shift+d is valued with remaining horizon R=T-a+1 (near/after T is worthless). |
| Adaptive capacity | max pending = ceil(d B_rem / H_rem) (replaces fixed 2). |
| Gate | Active only if d >= 2T/(B+2) (DSS delay switch); otherwise engine's uniform calendar. Spend-pace cap ceil(0.1B)+floor(2Bt/T) inherited. |
| Tuning | kappa=0.1, q=0.03 (PAVE_TUNED), two scalars tuned on dev seeds. |
| Engine | e-process promotion gate (episode_front family) + economic check + rollback; unchanged; validity inherited as an assumption. |
| Evidence (dev only) | Doc 41, 27 long-delay cells x 60 seeds: PAVE vs best simple rule -2.22% [-2.81,-1.67]; vs uniform calendar -2.24%; hiding pending from rollout +4.21% worse; pending flag off +8.32% worse (confounded with capacity); no-deadline +9.46% worse; PAVE vs native episode_front -0.06% (tie). Doc 42 (pave_ef vs matched ef_dss) has no result recorded in the file as read. The brief's "-3.0%" and "4.6%" do not match doc 41 pooled numbers; reconcile before any claim. |

## 2. Sources audited

| # | Source | Status | URL |
|---|---|---|---|
| S1 | Desautels, Krause, Burdick, GP-BUCB (ICML 2012; JMLR 2014 adds GP-AUCB) | ABSTRACT/SNIPPET | https://arxiv.org/abs/1206.6402 |
| S2 | Ginsbourger, Le Riche, Carraro, Kriging Believer / Constant Liar (2010) | SNIPPET | https://hal-emse.ccsd.cnrs.fr/emse-00436126 |
| S3 | Snoek, Larochelle, Adams, practical BO, fantasized pending outcomes (2012) | SNIPPET (supplement) | https://arxiv.org/abs/1206.2944 |
| S4 | Wu & Frazier, parallel KG / q-KG (NeurIPS 2016) | SNIPPET | https://arxiv.org/abs/1606.04414 |
| S5 | Kandasamy et al., async parallel Thompson sampling (AISTATS 2018) | SNIPPET | https://arxiv.org/abs/1705.09236 |
| S6 | Wu & Wager, Thompson sampling with unrestricted delays (2022) | READ (HTML) | https://arxiv.org/abs/2202.12431 |
| S7 | Joulani, Gyorgy, Szepesvari, online learning under delayed feedback (ICML 2013) | READ (ar5iv) | https://arxiv.org/abs/1306.0686 |
| S8 | Frazier-Powell-Dayanik KG (SICON 2008); Ryzhov-Powell-Frazier online KG (OR 2012) | SNIPPET | https://pubsonline.informs.org/doi/10.1287/opre.1110.0999 |
| S9 | Castellani, Schmitt, Hammer, stream AL with verification latency (PRopagate + drift-dependent budget) | READ (arXiv HTML v2) | https://arxiv.org/abs/2204.06822 |
| S10 | "Forgetting and simulating" AL with latency (MLJ, doi 10.1007/s10994-021-06099-z; authors unverified) | SNIPPET | https://link.springer.com/doi/10.1007/s10994-021-06099-z |
| S11 | Zliobaite 2010 "Change with delayed labeling: when is it detectable?"; Grzenda-Gomes-Bifet delayed-label evaluation (DMKD 2019) | SNIPPET | https://research.tue.nl/en/publications/change-with-delayed-labeling-when-is-it-detectable/ |
| S12 | Chick, Forster, Pertile, Bayesian decision-theoretic sequential experimentation with delayed response (JRSSB 2017) | ABSTRACT + first 100k chars | https://academic.oup.com/jrsssb/article-abstract/79/5/1439/7041089 |
| S13 | Naghshvar & Javidi, active sequential hypothesis testing (AoS 2013); Chernoff 1959 | ABSTRACT/SNIPPET | https://arxiv.org/abs/1203.4626 |
| S14 | Active sequential two-sample testing (Li et al.) | SNIPPET | https://arxiv.org/abs/2301.12616 |
| S15 | Anytime-valid active risk-controlling prediction sets (budget-optimal labelling policy for e-process growth) | SNIPPET only; authors not verified | https://chatpaper.com/paper/80022 |
| S16 | Drift2Act (arXiv 2603.08578, 2026) | ABSTRACT | https://arxiv.org/abs/2603.08578 |
| S17 | Lindon & Kallus, delayed outcomes in online experiments (arXiv 2603.25971, 2026) | SNIPPET | https://arxiv.org/abs/2603.25971 |
| S18 | Delayed-response Bayesian trial designs, imputation/predictive probability (Cai-Liu-Yuan; Yoshimoto arXiv 2405.14166) | SNIPPET | https://arxiv.org/abs/2405.14166 |

Excluded: Komiyama et al. fixed-budget BAI (DOT is "delayed optimal tracking", not data delay). Not found: any KG/EVSI
method combining pending-aware lookahead with a hard label budget and horizon; any delay-aware label-budget rule for
model monitoring tied to an e-process. Absence after one search per topic is not proof of absence.

## 3. Which PAVE components are known

| PAVE component | Closest prior | Verdict |
|---|---|---|
| VoI / lookahead sampling | KG family (S8); Chick KG* approximation (S12); Chernoff/Naghshvar-Javidi (S13) | KNOWN |
| Pending-aware posterior (in-flight observations shrink variance, no outcome used) | GP-BUCB (S1), believer/liar (S2), Snoek fantasies (S3), q-KG (S4), Chick "pipeline subjects" (S12), PRopagate imputed labels (S9) | KNOWN across fields |
| Horizon truncation / deadline value | Finite-horizon delayed-response DP with pipeline (S12); finite-horizon online KG (S8) | KNOWN in principle; as an explicit arrival-time-dependent heuristic not found, but implicit in S12's DP (partial text) |
| Delay-adaptive capacity ceil(d B_rem/H_rem) | In-flight count G* ~ delay x rate in S7 (analysis quantity, not a control rule); worker caps in S1/S5 | Little's-law rate-matching; no direct prior as an acquisition cap; reviewer will call it trivial |
| Long-delay gate | Not found as a label-budget rule | Engineering gate reused from DSS |
| Drift-triggered / front-loaded budget | S9 (b_high=4b after drift then b_low=b/2) | KNOWN; PAVE does not claim it; doc 41: front-loading never helped |
| Predictable query policy + e-process validity | S14, S15 | KNOWN pattern; PAVE has no proof |

## 4. Closest complete prior methods

| Rank | Method | Overlap | Lacks relative to PAVE |
|---|---|---|---|
| 1 | Chick-Forster-Pertile (S12) | Finite horizon, pending outcomes inform the posterior, stop/continue, sampling cost, terminal adoption decision | No hard label budget with pacing; no anytime-valid error control; no rollback monitoring; Gaussian fixed-delay trial; full text not fully read |
| 2 | GP-BUCB / q-KG (S1, S4) | Pending-aware posterior, VoI-style batch choice | Optimisation regret, not promotion-decision value; no deadline; no budget pacing |
| 3 | Castellani PRopagate + drift budget (S9, READ) | Same niche: stream, verification latency, budget, pending labels | One-step confidence utility; no value rollout, deadline, capacity cap, promotion gate |
| 4 | Anytime-valid active tests (S14, S15) | Budgeted label policy with e-process validity | No delay |

No single prior method found combining pending-aware VoI rollout + deadline + delay-scaled capacity + e-process gate + hard budget.

## 5. What is plausibly new

- The integration: value defined as regret of a downstream promotion/rollback decision, with a reachability factor tying label count to e-process wealth needed, pending and past-deadline labels in one rollout, hard budget, predictable query rule, e-process evidence engine unchanged.
- Empirical decomposition in the long-delay regime (rollout pending-info -4.2%, deadline -9.5%, capacity/pending flag -8.3%) not present in any source read.
- Not new: every ingredient. The capacity rule, the least novel part, carries a large share of the gain (gap between nopendinfo 4.2% and flag 8.3%).

## 6. Strongest reviewer objection and neutralising experiments

Objection: "This is constant liar + deadline cutoff + a rate-matching cap on a hand-built Normal model with two tuned scalars. Against the matched engine it gains ~2% on dev seeds, ties native episode_front (-0.06%), loses in large-budget (b0.1) and on0.3 cells, and the best simple deadline rule is within 0.02% of uniform. No validity theory."

Neutralising experiments (pre-register before running):
1. Doc 42 amended rule: `pave_ef - ef_dss` <= -2% with 95% CI excluding 0, fresh seeds. If this fails, verdict falls to KNOWN-by-simple-rule.
2. In-engine prior-art baselines on the same belief: (a) constant-liar/GP-BUCB-style pending-aware rule without deadline or capacity; (b) Castellani drift-dependent schedule; (c) Chick-style one-step KG* with pipeline count. PAVE must beat the best by >= 2% with CI excluding 0.
3. Freeze kappa, q; evaluate on unseen delays (e.g. 75, 150), large-budget cells, other cost grids.
4. Null screen under dependence rho in {0,.5,.8}; report as screen, not validity.

## 7. Verdict

NOVEL-INTEGRATION, weak and conditional on experiments 1 and 2. Components KNOWN; no complete prior method found; evidence dev-only.

Positioning sentence: "We adapt known pending-aware value-of-information ideas (in-flight observations in the posterior, finite-horizon truncation, delay-scaled concurrency limits) to budgeted label acquisition for an e-process promotion gate, and report a small, regime-specific cost reduction over matched label calendars in the long-delay regime; we make no validity or optimality claim for the acquisition rule."

Do not claim: first delay-aware acquisition, new pending-aware posterior, or new deadline logic.

## 10-line summary
1. PAVE = calendar-shift value rollout on a Normal-Kalman belief (closed-form, not MC) with pending, deadline, capacity, long-delay gate.
2. Closest prior: Chick-Forster-Pertile 2017 (delayed-response Bayes sequential design, pipeline subjects); only partly read.
3. Pending-aware posterior: KNOWN (GP-BUCB, kriging believer, Snoek fantasies, q-KG, PRopagate).
4. VoI lookahead and finite-horizon value: KNOWN (KG, Chick, Chernoff-type).
5. Delay-scaled capacity: rate-matching, no direct prior but trivial; least novel and drives much of the 8% gain.
6. Castellani 2022 (READ): same niche, but one-step utility, no deadline, cap, rollout or promotion gate.
7. Anytime-valid active testing exists (snippet-only); delay not combined.
8. Objection: constant liar + deadline cutoff; PAVE ties native episode_front; best simple rule within 0.02% of uniform.
9. Decisive tests: doc 42 pave_ef vs ef_dss, prior-art baselines in-engine, frozen parameters, fresh delays.
10. Verdict NOVEL-INTEGRATION (weak, conditional); brief's -3.0%/4.6% differ from doc 41 (-2.24%/4.21%): reconcile.
