# Prior-art audit for the SOTA expansion (EQSDp comparators)

Date: 2026-11-08. Branch `research/qsg-methods-search-2026-11-07`. Read-only; no experiments, no code downloaded or run.
Contract: T=2000 events, two models deployed one at a time, label cost c_q=0.05, hard budget B=200, label delay d, switch cost c_s=5,
objective J = sum loss + c_q N_q + c_s N_s. EQSDp (`scripts/qsg_methods_search/eqs_d.py`): reversible payback rule, Beta lower quantile
(gamma=0.2) of per-event advantage on discounted (lambda=0.9) disagreement-only labels, times disagreement rate times (T-t), versus c_s.
No false-promotion guarantee. Current status: NOVEL-INTEGRATION only.

Labels. **VERIFIED** = primary page (arXiv abs/html, PMLR) opened this session; the fetch tool summarises pages, so statements are checked against
summaries, not raw PDF bytes. **VERIFIED-REPO** = stated by the repo's own earlier audit or a competitor docstring/ledger (file cited), not re-opened
here. **SNIPPET-ONLY** = search snippet only. **NOT-OPENED** = background knowledge, nothing seen this session.
Tier language follows `docs/sota_fidelity` (T1 author-parity port, T2 audited maths port, T3 common-contract adapter).

Sources read first: `docs/qsg_methods_search/novelty_audit.md`, `docs/qsg_methods_search/sota_comparator_matrix.md`,
`origin/claude/shiftlab-methods-strategy-dba13e:docs/sota_fidelity/{LEDGER,REPORT}.md`, and the docstrings of the competitor files named per family.

## 0. Cross-cutting facts

- No family below is native to the ShiftLab contract (two frozen models, hard-capped paid labels, delay, per-switch charge, reversible deployment, net-cost objective).
  Every comparison is a T3 adapter on the shared simulator or a heuristic. The ledger rule applies: name results "<method>-style adapter (T3)", never "<method>".
- Author-parity tests for CAMS, Model Selector, Model Picker, SMCS and variance-min are silently skipped because `vendor_sota/` is empty
  (VERIFIED-REPO: REPORT.md finding 4). Their T1 claims are currently unverified. Restoring clones downloads third-party code and needs user go-ahead.
- Code URLs and SHAs below come from repo docstrings (VERIFIED-REPO) unless stated. None of the arXiv abs pages I opened lists a repository link
  except CAMS.

## S1. Gong and Zhang, paid observations

1. Xueping Gong, Jiheng Zhang, "The Cost of Information: Phase Transitions in Contextual Bandits with Paid Observations", ICML 2026, PMLR 306, pp. 36013-36044,
   https://proceedings.mlr.press/v306/gong26i.html. VERIFIED (PMLR page). No arXiv id on the page.
2. Objective: regret including learning loss plus observation spending; adversarial contextual bandit. VERIFIED (abstract).
3. Feedback: learner chooses which actions to observe, each costs; a free-observation budget with a phase transition; meta-controller over budget regimes;
   abstract connects to switching costs and knapsack bandits. Delay not stated. Minimax guarantees. VERIFIED (abstract only; full text unread).
4. Code: none listed on the PMLR page (VERIFIED). Repo: none.
5. Exact reproduction: No. The abstract defines no payback rule; policy classes and minimax regret do not map to a two-model net-cost problem.
6. Adaptations: repo `gong_zhang_paid_obs` (`scripts/failure_atlas_v2_flq/r6_policies.py`) is a discounted importance-weighted point-estimate payback rule
   `(T-t)*s_hat/den > c_s` with switch-back; docstring says "adaptations, not reproductions: the source guarantees do not transfer" (VERIFIED-REPO, novelty_audit Note A).
   `gongT_w100_m10` is a 16-config tuned variant. Needed: rename "Gong-Zhang-style paid-observation adapter"; read the full text.
7. Meaningfulness: meaningful only as a heuristic baseline. It is effectively the point-estimate economic switcher, i.e. the right ablation for the quantile hurdle, not a comparison to the paper.

## S2. Qiu et al., delayed movement

1. Hao Qiu, Andrew Jacobsen, Emmanuel Esposito, Mengxiao Zhang, "Parameter-free Dynamic Regret: Time-varying Movement Costs, Delayed Feedback, and Memory",
   arXiv:2602.06902 (page comment "v2: ICML 2026"). VERIFIED (abs page).
2. Objective: comparator-adaptive dynamic regret in unconstrained OCO with time-varying movement costs, O~(sqrt((M^2+M P_T)(T+sum lambda_t))). VERIFIED.
3. Feedback: full-information OCO; delay and memory reduced to time-varying movement costs. No label acquisition, no budget, no discrete model choice. VERIFIED (abstract).
4. Code: none on the page (VERIFIED).
5. Exact reproduction: No. Continuous-action OCO learner, not a two-model replacement.
6. Adaptations: repo `qiu_delayed_movement` is a blocked fixed-share Hedge on IW differences (VERIFIED-REPO novelty_audit Note A), not the paper's algorithm.
   Rename "Qiu-style Hedge adapter"; read the algorithm box before claiming more.
7. Meaningfulness: heuristic baseline only (delay- and movement-aware online learner).

## S3. Regol et al., UPF ("When to retrain a machine learning model")

1. Regol, Schwinn, Sprague, Coates, Markovich, ICML 2025, PMLR v267 (https://proceedings.mlr.press/v267/regol25a.html), arXiv:2505.14903.
   VERIFIED-REPO (novelty_audit row 1 and sec. 7: HTML read twice; LEDGER: PMLR PDF + arXiv v1).
2. Objective: retrain-vs-keep each step by comparing delta-quantiles (delta=0.95) of total remaining-horizon cost including a retraining cost (Eqs. 3, 15, 16);
   Beta-modelled performance from a regression forecaster. VERIFIED-REPO.
3. Feedback: each period's full data available; no label budget, no delay, no rollback; one-directional retraining. App. A.1: quantile rule beats the point-estimate
   rule (delta=0.5) significantly on 5 of 6 datasets. VERIFIED-REPO.
4. Code: none found (PMLR links none; OpenReview not opened because of a bot challenge, so "no code" is unverified). VERIFIED-REPO (LEDGER).
5. Exact reproduction: T2 native port exists (`src/shiftlab/dive/upf_retraining.py`, needs torch). Not possible under our contract: no forecaster inputs in the sprint streams.
6. Adaptations: `upf_style_switch_timing_T3` on `origin/claude/shiftlab-methods-strategy-dba13e`
   (`scripts/promising_directions/sota/competitors/upf_style_switch_timing.py`): period length locked before runs, IPW cells on disagreement rounds,
   sigma = residual MSE + mean Horvitz-Thompson variance, reversible recursion (Eqs. 17-20), Eq. 16 strict quantile comparison. Switches on 8/20 null seeds (descriptive).
   Never label it "UPF". Prop. 3.1 as printed is false (corrected bound in LEDGER).
7. Meaningfulness: meaningful as a common-contract comparison (T3). The single most important comparator for the quantile claim.

## S4. Model Picker (Karimi et al.)

1. Mohammad Reza Karimi, Nezihe Merve Gurel, Bojan Karlas, Johannes Rausch, Ce Zhang, Andreas Krause, "Online Active Model Selection for Pre-trained Classifiers",
   AISTATS 2021, PMLR 130:307-315, https://proceedings.mlr.press/v130/reza-karimi21a.html, arXiv:2010.09818. SNIPPET-ONLY (search listing of the PMLR page; not opened).
2. Objective: identify the best of k pre-trained classifiers with few queries; selective sampling, best model with high probability at any round. SNIPPET-ONLY.
3. Feedback: immediate labels on queried points, query budget, no switching charge, no delay; action each round sampled from the posterior (VERIFIED-REPO: model_picker.py docstring).
4. Code: `DS3Lab/online-active-model-selection` (SNIPPET-ONLY, via ar5iv listing). Docstring ports from `vendor_sota/model_picker` (gitignored, SHA not stated).
5. Exact reproduction: No under our contract (native stream port exists, T1-pending-parity; no delay, no switch charge, posterior-sampled actions).
6. Adaptations: `ModelPickerDeploymentAdapter`: delayed labels via `observe`, IPW by issue-time propensity, hard cap, argmax-recommendation deployment (all marked `# ADAPTER:`).
   Binary case reduces to disagreement sampling.
7. Meaningfulness: heuristic baseline only. Matrix: 64-100% null promotion and 5-11 switches (VERIFIED-REPO).

## S5. Model Selector (Okanovic et al.)

1. Patrik Okanovic, Andreas Kirsch, Jannes Kasper, Torsten Hoefler, Andreas Krause, Nezihe Merve Gurel, "All models are wrong, some are useful: Model Selection with Limited Labels",
   arXiv:2410.13609 (VERIFIED). AISTATS 2025, PMLR v258 per docstring/LEDGER (VERIFIED-REPO; the arXiv page lists no venue).
2. Objective: pool-based label-efficient choice of the best pretrained classifier; greedy expected-posterior-entropy query; final pick = best labelled accuracy.
   Abstract: up to 94.15% labelling-cost reduction. VERIFIED.
3. Feedback: immediate oracle, fixed pool, no delay, no switch charge. VERIFIED-REPO.
4. Code: `RobustML-Lab/model-selector@6aa57e57` (VERIFIED-REPO; registered as `model_picker` inside that repo). Not on the arXiv page.
5. Exact reproduction: native pool port exists (T1-pending-parity). Not for a stream: the simulator can label only the current event.
6. Adaptations: `model_selector_causal` (T3 record gate; with 2 models and 2 classes it is paced disagreement sampling). Record-gate rounding bug fixed (1e-12 tolerance).
7. Meaningfulness: heuristic baseline only. Best of the M2 churn group (matrix), but an acquisition rule, not a switching rule.

## S6. CAMS (Liu et al.)

1. Xuefeng Liu, Fangfang Xia, Rick L. Stevens, Yuxin Chen, "Contextual Active Model Selection", arXiv:2207.06030 (v4, Feb 2025). VERIFIED for title/authors/abstract.
   NeurIPS 2024 per ledger (VERIFIED-REPO; the arXiv page names no venue).
2. Objective: online contextual model selection with sparse label queries; regret and query-complexity analysis, adversarial and stochastic. VERIFIED.
3. Feedback: unlabeled context, learner predicts and requests labels sparingly; immediate labels; "never defines a switching cost" (VERIFIED-REPO docstring).
4. Code: https://github.com/xuefeng-cs/Contextual-Active-Model-Selection (VERIFIED, on arXiv page); pinned `6cbcc62f` = upstream HEAD (VERIFIED-REPO).
5. Exact reproduction: No. Author policy training is absent from the repo (advice matrices only); paper-vs-code gaps (eta, u_t floor) recorded in the ledger.
6. Adaptations: `CAMSDeploymentAdapter`: argmax of w_t with incumbent tie-keeping, delayed labels, hard budget, switch charge (adapter choices). KNN policy is ours.
7. Meaningfulness: heuristic baseline only.

## S7. DISCERN (Balachandran 2026)

1. Vishnu Bindu Balachandran, "Pay Only for Disagreement: Certified No-Regression Verdicts for Model Updates with Matching Label-Complexity Bounds",
   arXiv:2609.17560 (v1, 22 Jul 2026, 32 pp.), no venue listed. VERIFIED.
2. Objective: certified paired risk-difference audit; Safe(eps) or Regression verdicts from an anytime-valid CS; label cost order rho^2/eps^2. VERIFIED (abstract).
3. Feedback: zero-label tier from unlabeled traffic; audited tier labels sampled disagreements under any label-routing rule; finite-sample validity, composition across promotions.
   Delay and a concrete cap: not stated on the page. VERIFIED.
4. Code: none on the page; docstring says no author code obtainable (VERIFIED-REPO, certificate_stops.py).
5. Exact reproduction: No. It is a verdict protocol, not a net-cost policy; no author code.
6. Adaptations: `discern_style` (`certificate_stops.py`), `discern_design_floor(+front)` (`strong_hosts.py`, pi_min=.25, c=4), plus QCE variants. Shared paced disagreement acquisition; stops on the
   certificate; ignores c_s and horizon (VERIFIED-REPO). Strongest port `discern_style+QCE+front` (alt mean 382, matrix).
7. Meaningfulness: common-contract comparison only as "certificate-gated promotion"; report cost and false-promotion rate together (it pays for a guarantee EQSDp does not claim).

## S8. SMCS (sequential model confidence sets)

1. Sebastian Arnold, Georgios Gavrilopoulos, Benedikt Schulz, Johanna Ziegel, "Sequential model confidence sets", arXiv:2404.18678 (v4, 22 Jan 2026).
   A JRSS-B listing (DOI 10.1093/jrsssb/qkag066) appeared in search, unconfirmed on the journal site. arXiv: VERIFIED (search page); venue SNIPPET-ONLY.
2. Objective: time-uniform confidence set of not-yet-rejected models via e-processes (extends Hansen et al. MCS). VERIFIED (search summary).
3. Feedback: full losses of all models, anytime-valid inference; no deployment policy, no costs ("not a model-switching policy", VERIFIED-REPO).
4. Code: author R replication repo, commit `ab0944e7` (VERIFIED-REPO). `vendor_sota/` empty, so parity tests skip.
5. Exact reproduction: inference part only (pairwise conditional null, product e-process, closure principle). Sim3 formulation blocked (needs `pracma`, `NlcOptim`).
6. Adaptations: `SMCS+retain-incumbent` (retain until the incumbent leaves the set; B3+ pacer). Nothing in SMCS prescribes this.
7. Meaningfulness: heuristic baseline only. Slow promotion; with front-loading fails the rho=.8 null at .22 (matrix).

## S9. Xu, Karampatziakis, Mineiro

1. Ziyu Xu, Nikos Karampatziakis, Paul Mineiro, "Active, anytime-valid risk controlling prediction sets", NeurIPS 2024, arXiv:2406.10490. VERIFIED (abs page states NeurIPS 2024).
2. Objective: anytime-valid RCPS under adaptive collection; active labeling policy within an expected-proportion budget, predictor-assisted variance reduction. VERIFIED.
3. Feedback: budget is an expected proportion, not a hard cap; no delay, no switching. VERIFIED (abstract).
4. Code: `neilzxu/active-rcps@a67f85d6` (VERIFIED-REPO); not on the arXiv page.
5. Exact reproduction: No. The repo takes only the acquisition rule (Player.py:177 etc.) as a component; no prediction sets.
6. Adaptations: `xu_acquisition_only(+front)`. For 0/1 paired loss on disagreement it reduces to disagreement-gated uniform sampling (their "oblivious" arm). Validity of the evidence is ShiftLab's, not theirs.
   `xu+front_only` is the only front-loaded host that stays safe at rho=.8 (.08) (matrix).
7. Meaningfulness: heuristic baseline only.

## S10. MOPE / off-policy confidence sequences, adaptive range

1. Nikos Karampatziakis, Paul Mineiro, Aaditya Ramdas, "Off-policy Confidence Sequences", arXiv:2102.09540. VERIFIED (title/authors/abstract; "gated deployment").
   ICML 2021 per the repo docstring (VERIFIED-REPO); the arXiv page lists no venue.
2. Objective: time-uniform off-policy value confidence sequences, used for safe upgrade of a production policy. VERIFIED.
3. Feedback: logged contextual-bandit data with bounded importance weights, anytime validity; no label cost, no switching cost. VERIFIED-REPO.
4. Code: MOPE author repo pinned `a4b8584`, parity unchecked (VERIFIED-REPO, matrix).
5. Exact reproduction: No (no parity check, different setting).
6. Adaptations: `gated_deployment`, `gated_adaptive_range(+front)` (`strong_hosts.py`, wmax_t = 1/q_t; ordering defect fixed 2026-11-05). Uniform pacing under a binding budget fails (F0_better 427 vs never-switch 418).
7. Meaningfulness: common-contract comparison for the "certified gate" family; not economic.

## S11. Wald-LCB switching (textbook)

1. No single source. NOT-OPENED.
2. Objective: switch when the (1-gamma) lower confidence bound on paired advantage exceeds a threshold or payback hurdle.
3. Feedback: user-defined; no native contract.
4. Code: none needed.
5. Exact reproduction: not applicable (a design choice, not a paper).
6. Adaptations: required by novelty_audit sec. 5 item 2: point estimate minus z*sqrt(p(1-p)/n_eff) (Wald) and a Hoeffding LCB, same gamma, discounting and payback form,
   to test whether the Beta form matters.
7. Meaningfulness: common-contract comparison. The most dangerous ablation (the "any uncertainty-scaled hurdle works" objection).

## S12. Economic replacement / horizon-pays (Wan et al.; Chick et al.)

1. Wan, Liu, McQueen, Hains, Song, KDD 2023, arXiv:2304.00420 (VERIFIED-REPO, ECON_CHECK #1). Chick, Forster, Pertile, JRSS-B 2017, DOI 10.1111/rssb.12225 (VERIFIED-REPO against DP v2 only).
2. Objective: launch iff posterior-mean effect x horizon x N exceeds a hurdle (Wan Sec. 5.2.4 Eq. 1); Bayesian sequential trial with delayed responses, adopt iff P*Z > I (Chick). VERIFIED-REPO.
3. Feedback: one-shot launch, no rollback, no discounting; Chick has delayed responses and a hard maximum sample size. VERIFIED-REPO.
4. Code: none known.
5. Exact reproduction: No (conceptual rules).
6. Adaptations: in repo `EconomicReplacement` (`controls.py`: point estimate, `min_obs`, additive `margin`), `economic_replacement`, tuned `econF_mo5_m5` (front-loaded).
   Ancestor of the D4 ablation. Missing: scaled-margin and dwell-time variants (novelty_audit sec. 5 item 3).
7. Meaningfulness: common-contract comparison; the strongest simple baseline (the margin ablation only ties it, VERIFIED-REPO).

## E1. e-SR / e-detectors (Shin, Ramdas, Rinaldo)

1. Jaehyeok Shin, Aaditya Ramdas, Alessandro Rinaldo, "E-detectors: A Nonparametric Framework for Sequential Change Detection", NEJSDS 2 (2024) 229-260, arXiv:2203.03532. VERIFIED-REPO (docstring, ledger).
2. Objective: anytime-valid change detection with ARL control (alarm when e-SR / e-CUSUM crosses 1/alpha). VERIFIED-REPO.
3. Feedback: streaming bounded observations with a pre-change mean bound; no cost, budget or switching. VERIFIED-REPO.
4. Code: `shinjaehyeok/stcp@c9ff9a6`, `stcpR6@9eaafb4`, read never executed (VERIFIED-REPO).
5. Exact reproduction: T2 audited port; the NBA Plus-Minus alarm (game 378) reproduced; T1 not claimed.
6. Adaptations: `two_sided_esr_label_clock` (T3, start at every label, restart at switch), `esr_rmmbets_fullalpha`, `rmm:LRMD_k1`. Misses late changes once the budget is exhausted; loses to never-switch on reversal.
7. Meaningfulness: common-contract comparison (cost plus false alarms), but it is a detector. E_rb minus e-SR on reversal is +1.90 [-1.01, +4.80] (REPORT).

## E2. Shekhar and Ramdas, ICML 2024

1. Shubhanshu Shekhar, Aaditya Ramdas, "Reducing sequential change detection to sequential estimation", ICML 2024, PMLR 235:44628-44642, arXiv:2309.09111v2. VERIFIED-REPO.
2. Objective: reduce change detection to confidence sequences; stop when the repeated CSs have empty intersection. VERIFIED-REPO.
3. Feedback: streaming bounded data, ARL >= 1/alpha; no cost, no label budget; delay bounds vacuous at B=200. VERIFIED-REPO.
4. Code: `sshekhar17/SCDtoCS@c3a7ece`; deviates from the paper (first-observation skip, uncapped lambda). VERIFIED-REPO.
5. Exact reproduction: T2 core only; T1 unavailable.
6. Adaptations: `shekhar_ramdas_rcs_t3` (paper rule) and `_anyexcl` (composite-null-safe), Remark 2.5 level spending. The joint-emptiness rule false-alarmed on 100% of constructed drifting-within-null streams; `any_excludes` gave 0% (REPORT).
7. Meaningfulness: heuristic baseline only (a detector, not a cost rule).

## E3. Han, Huang, Wang, ARW (ICML 2024)

1. Han, Huang, Wang, "Model Assessment and Selection under Temporal Distribution Shift", ICML 2024, PMLR 235:17374-17392, arXiv:2402.08672. VERIFIED-REPO.
2. Objective: adaptive rolling window (Goldenshluger-Lepski-style bias/variance proxy) for model assessment and two-model comparison under drift. VERIFIED-REPO.
3. Feedback: batched periods of labelled data; no delay, no switch margin, no sequential validity. VERIFIED-REPO.
4. Code: `eliselyhan/ARW@c48f830`, no licence; re-implement from the paper only. VERIFIED-REPO.
5. Exact reproduction: T2 core from printed equations; constant sets `theory` and `paper_experiments`.
6. Adaptations: `han_arw_label_clock` (T3), default `theory`, margin 0; flips on noise (17-21 switches on null). A margin-tuned variant only if tuned on development seeds.
7. Meaningfulness: heuristic baseline only; the nearest nonstationarity-aware window for the discounting ablation.

## O1. Online LLM Picker

1. Alessandro Turrin, Patrik Okanovic, Torsten Hoefler, Nezihe Merve Gurel, "Which LLM to pick? Online Active Model Selection for Large Language Models", arXiv:2610.01592 (v1, 1 Oct 2026), no venue. VERIFIED.
2. Objective: stream-based annotation selection to identify the best of 130+ LLMs under a limited budget; up to 71.67% annotation savings, up to 2.51x lower regret. VERIFIED (abstract).
3. Feedback: streaming prompts, similarity-based loss, budget as an expected proportion, no switch cost. VERIFIED-REPO (docstring).
4. Code: none on the page; docstring: none located. `eps` in eta_t unrecoverable (BLOCKED), `1e-8` is ours.
5. Exact reproduction: No (ported from paper text, Eq. 10).
6. Adaptations: `online_llm_picker` with exact-agreement loss and an imposed hard cap. At m=2 it queries every disagreement in burn-in and spends the budget early (tested).
7. Meaningfulness: heuristic baseline only.

## O2. Variance-minimising IPW (not Sawade)

1. The `variance_min.py` docstring names Hara et al., ACML 2024 / Machine Learning 2024 (VERIFIED-REPO); I did not open it. Sawade et al. (active risk estimation) was not checked and is not what the repo ports.
2. Objective: query distribution that minimises the variance of a pool LURE estimator for model comparison (Eq. 8).
3. Feedback: whole pool visible, no delay, no switching.
4. Code: clone `33f6fab5` (VERIFIED-REPO).
5. Exact reproduction: native pool port only; the streaming versions are not the published method.
6. Adaptations: `variance_min_ipw`. With 2 classes the score equals 1[disagree], so it collapses to disagreement sampling with a 1% floor on agreements.
7. Meaningfulness: heuristic baseline only (acquisition).

## New literature search (11 searches and 14 fetches this session)

I found no paper that combines a label budget, delayed labels, switching cost, reversible deployment and a quantile payback rule.

### N1. "The Challenger" (found)

1. Vassilis Digalakis Jr, Christophe Perignon, Sebastien Saurin, Flore Sentenac, "The Challenger: When Do New Data Sources Justify Switching Machine Learning Models?",
   arXiv:2512.18390 (v1 20 Dec 2025, v2 16 Jul 2026), cs.LG; no venue on the page. https://arxiv.org/abs/2512.18390. VERIFIED (abs page; first 100k of 219k characters of the HTML read).
2. Objective: finite-horizon optimal stopping. V_switch(t) = -c n T - c_s + n(T-t)G(t), V_discard(t) = -c n t; incremental value -c_s + n(T-t)(G(t)-c). Same payback form as EQSDp. VERIFIED.
3. Feedback: a challenger trained on a growing full-feature dataset with a power-law learning curve; per-sample cost c, one-time switching cost c_s. No label budget, no delayed labels in the text read.
   Irreversible ("once the challenger is adopted or discarded, the process stops"). Algorithms: GSE (Hoeffding-type half-width delta_k = gamma/sqrt(rho N), switch once the bound shows positive value),
   OSE (one-shot at about T^{2/3}, point estimate), LSE/LSEc (local learning-curve slope, optimistic). No quantiles. Guarantee: O(T^{2/3} sqrt(log T)) regret against a full-foresight oracle for T^{2/3}-scale stoppers. VERIFIED.
4. Code: none on the page. VERIFIED.
5. Exact reproduction: No (it models a challenger learning curve; ours are frozen models with paired labels).
6. Adaptations: map G(t) to the discounted paired advantage times disagreement rate; keep the n(T-t)(G-c) payback and a Hoeffding half-width; drop learning curves.
7. Meaningfulness: heuristic baseline only.
   **Verdict: add as a comparator, yes.** Sketch `challenger_gse`: n_eff = discounted count of disagreement labels, G_hat = mean advantage, delta = g0/sqrt(n_eff) (g0 tuned on development seeds);
   switch when (T-t)*rho_hat*(G_hat - delta) > c_s; no switch-back. Add `challenger_ose` (decide once at t about T^{2/3}, point estimate) and a reversible `challenger_gse_rev` to separate reversibility from the bound.
   It is the closest published relative of "payback with a confidence bound" and must be cited. It does not subsume EQSDp (no budget, delay, paired evidence or reversal).

### N2. Dekel, Ding, Koren, Peres, "Bandits with Switching Costs: T^{2/3} Regret", STOC 2014 (arXiv 1310.2997)
Minimax regret Theta~(T^{2/3}) for adversarial bandits with switching costs, versus sqrt(T) under full information. SNIPPET-ONLY (not opened). No label cost, no delay.
**Verdict: no** (adversarial regret theory; cite for context). Batched or blocked Hedge is already covered by `qiu_delayed_movement`.

### N3. Cesa-Bianchi, Dekel, Shamir, "Online Learning with Switching Costs and Other Adaptive Adversaries", arXiv:1302.4387
Theta~(T^{2/3}) with bandit feedback and Theta(sqrt(T)) with full information under switching costs. VERIFIED (abs page; no venue listed there, NeurIPS 2013 is from my memory, NOT-OPENED).
**Verdict: no** (no delay, no label budget, regret objective).

### N4. Dong and Tan, "Adversarial Combinatorial Bandits with Switching Costs", IEEE Trans. Inf. Theory, arXiv:2404.01883
Batched algorithms, lower bound Omega~((lambda K)^{1/3}(TI)^{2/3}). VERIFIED (abs page). **Verdict: no** (combinatorial arms, adversarial regret, no delay or label cost).

### N5. Delayed feedback and switching costs, separately
Wu and Wager, "Thompson Sampling with Unrestricted Delays", arXiv:2202.12431; Teymourian and Yang, "Simple fixes that accommodate switching costs in multi-armed bandits", EJOR 320(3) 2025, 616-627. Both SNIPPET-ONLY.
Two searches found no stochastic-bandit paper with both switching costs and delay (absence is not proof). **Verdict: no** for Wu-Wager; Teymourian-Yang is a possible low-priority heuristic (interval-based TS/UCB) but needs a reward-to-paired-advantage mapping and has no label budget.

### N6. Label-efficient prediction and budgeted online selection
Cesa-Bianchi, Lugosi, Stoltz (2005) was not retrieved; Mitra et al. arXiv:1910.08805 cites it (SNIPPET-ONLY). A 2025-2026 search for budgeted online model selection with switching cost returned only CAMS, Model Selector, Model Picker. **Verdict: no.**

### N7. MLDemon (arXiv 2104.13621, AISTATS 2022) and Podkopaev-Ramdas "Tracking the risk of a deployed model" (arXiv 2110.06177)
Monitoring under a small expert-label budget; decide when to buy labels or whether a shift hurts, not when to replace. SNIPPET-ONLY. **Verdict: no** for switching; at most an acquisition-side baseline.

### N8. Champion-challenger grey literature
SAS Model Manager and ModelOp pages describe champion-challenger testing as a procedure; titles only (SNIPPET-ONLY). No switching-cost payback rule or label budget seen. **Verdict: no.**

## Summary table

| Family | Citation / venue | Native objective | Native feedback | Code | Exact repro possible? | Comparison meaningfulness |
|---|---|---|---|---|---|---|
| S1 Gong-Zhang | Gong, Zhang; ICML 2026 (PMLR 306) | regret + observation cost | chosen paid observations, free budget; delay not stated | none listed | No | Heuristic baseline only |
| S2 Qiu | Qiu et al.; arXiv 2602.06902 (ICML 2026) | dynamic regret, OCO, movement cost | full-info OCO, delay as movement cost | none | No | Heuristic baseline only |
| S3 Regol UPF | Regol et al.; ICML 2025 (PMLR 267), arXiv 2505.14903 | delta-quantile of horizon cost incl. retrain cost | full period data, no budget/delay/rollback | none found | T2 yes; contract no | Common-contract comparison (T3 adapter exists) |
| S4 Model Picker | Karimi et al.; AISTATS 2021 (PMLR 130), arXiv 2010.09818 | best model, few queries | immediate labels, no switch cost | DS3Lab/online-active-model-selection (snippet) | No (parity skipped) | Heuristic baseline only |
| S5 Model Selector | Okanovic et al.; arXiv 2410.13609, AISTATS 2025 | label-efficient pool selection | immediate oracle, fixed pool | RobustML-Lab/model-selector@6aa57e57 | No | Heuristic baseline only |
| S6 CAMS | Liu et al.; arXiv 2207.06030, NeurIPS 2024 (ledger) | contextual online selection | immediate labels, no switch cost | xuefeng-cs/Contextual-Active-Model-Selection@6cbcc62f | No | Heuristic baseline only |
| S7 DISCERN | Balachandran; arXiv 2609.17560, no venue | certified no-regression verdict | labelled disagreements | none | No | Common-contract comparison (certificate-gated) |
| S8 SMCS | Arnold et al.; arXiv 2404.18678 (JRSS-B per listing) | time-uniform model set | full feedback inference | R repo @ab0944e7 | Inference only | Heuristic baseline only |
| S9 Xu et al. | NeurIPS 2024, arXiv 2406.10490 | anytime-valid RCPS, active labeling | expected-proportion budget | neilzxu/active-rcps@a67f85d6 | No (component) | Heuristic baseline only |
| S10 MOPE | Karampatziakis et al.; arXiv 2102.09540 | off-policy confidence sequences | logged data, bounded weights | repo @a4b8584, parity unchecked | No | Common-contract comparison (certified gate) |
| S11 Wald-LCB | none | LCB on advantage | user-defined | n/a | n/a | Common-contract comparison (required ablation) |
| S12 Horizon-pays | Wan et al. KDD 2023; Chick et al. JRSS-B 2017 | mean payback > hurdle | one-shot; delayed responses | none | No | Common-contract comparison (strongest simple baseline) |
| e-SR | Shin et al.; NEJSDS 2024, arXiv 2203.03532 | ARL-controlled detection | stream, no cost | stcp@c9ff9a6 | T2 only | Common-contract comparison (detector) |
| Shekhar-Ramdas | ICML 2024 (PMLR 235) | detection via CSs | stream, no cost | SCDtoCS@c3a7ece (deviates) | T2 only | Heuristic baseline only |
| Han ARW | ICML 2024 (PMLR 235) | adaptive window comparison | batched labelled periods | ARW@c48f830 (no licence) | T2 only | Heuristic baseline only |
| Online LLM Picker | Turrin et al.; arXiv 2610.01592 | online active LLM selection | expected-proportion budget | none | No | Heuristic baseline only |
| Variance-min IPW | Hara et al. (per docstring) | variance-minimising query | pool, no delay | clone @33f6fab5 | Pool only | Heuristic baseline only |
| N1 The Challenger | Digalakis et al.; arXiv 2512.18390 | optimal stopping, payback + confidence bound | growing data, irreversible, no label budget | none | No | Heuristic baseline only; add |

## Novelty implications for EQSDp

- The Challenger (arXiv 2512.18390) writes the same finite-horizon payback inequality, -c_s + n(T-t)(G-c) > 0, and puts a confidence bound on G in GSE. "Payback with a confidence bound" is therefore published.
  It is irreversible, has no label budget, delay or paired evidence, and uses Hoeffding half-widths, not Beta quantiles. The hurdle itself cannot be EQSDp's claim.
- Regol et al. already show a conservative horizon-cost quantile beating the point-estimate rule on 5 of 6 datasets (VERIFIED-REPO). "Uncertainty-aware beats point estimate" is not ours;
  only the narrower claim against point-plus-tuned-margin, with reversibility, discounting and budgeted disagreement-only delayed labels, remains open.
- Status stays NOVEL-INTEGRATION: the contribution is the combination and the ablation evidence, not a new decision principle or a guarantee.
- The repo's Gong-Zhang and Qiu comparators are adapters; "beats Gong-Zhang" or "beats Qiu" must not be written. Use "beats a tuned Gong-Zhang-style point-estimate payback adapter" and "a Qiu-style Hedge adapter".
- Before any quantile-specific claim, run the Regol-style T3 (S3), Wald and Hoeffding LCB hurdles and scaled-margin and dwell-time rules (S11, S12), and Challenger-style GSE/OSE (N1). If a Hoeffding LCB matches EQSDp, the Beta form is not the contribution.
- The guarantee-bearing families (S7, S8, S10, e-SR, Shekhar-Ramdas) offer false-promotion control that EQSDp lacks. Report cost and false-promotion rate together; the claim is a cost-versus-validity trade-off, not dominance.
- All comparisons are T3 adapters on synthetic streams; no author-native reproduction exists and T1 parity is pending for five families.
- Absence of a hit in 11 searches does not prove novelty; N2-N8 are abstract- or snippet-level. Not searched: real-options learning (Keller-Rady, Moscarini-Smith), Deng's Bayesian A/B papers, the EJOR 2025 full text.
