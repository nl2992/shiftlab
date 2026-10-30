# Prior-art reduction matrix (continuation item 2)

Date: 2026-10-30. Branch: `claude/bold-cray-xcy73f` (from sprint tip 71ad2b3).
Host probe: arxiv.org, proceedings.mlr.press, archive.ics.uci.edu, data.binance.vision answered 200;
s3.amazonaws.com 307; `d37ci6vzurychx.cloudfront.net` (NYC TLC) and `www.nyc.gov` 403 -> `BLOCKED_EXTERNAL_ACCESS`
for the frozen NYC-taxi manifest (not probed further, not bypassed).

## Evidence limits (read first)
The PDF endpoints returned undecodable bytes. Each paper was read through arXiv HTML, of which only the first
~39k characters (of 135k-220k) came back verbatim; the rest is a tool-generated summary. Appendices were not read.
Theorem-level evidence below is therefore **partial**; "(summary)" marks items not verified verbatim.
Re-verification route: LaTeX source `https://arxiv.org/src/<id>` or PMLR PDF. No verdict below is final until then.

## Per-paper entries

| Paper | Estimand / null | Information & budget | Statistic & bet | Theorem (as read) | H2c ingredient contained? | Verdict |
|---|---|---|---|---|---|---|
| PPRM, Zhang et al., ICML 2026, arXiv 2602.02229 | H0: running mean risk R̄_t <= R_0 + eps_tol for all t; loss bounded in [0,1]; no shift assumptions | n_0 calibration labels (i.i.d.), R_0 *estimated* with upper bound U_0 (PPI + betting bound, Einbinder et al., App. A.2 unread); per step n_t>0 labelled + N_t unlabelled; delay not in read text | PP estimate R^U + rectifier with predictable eta_t (PPI++ style); lower CS = conjugate-mixture empirical-Bernstein (Howard et al.), not a Kelly/ONS bet; alpha split delta_S+delta_T | Lemma 3.1 unbiasedness for predictable eta_t (verbatim); Thm 3.2 type-I <= delta_S+delta_T (summary only) | PP increment with predictable tuning: **yes**. IPW weight Q/q for active labelling: not seen. Bet chosen from a second statistic's history: not seen (eta_t uses own sliding window). Discounted Kelly: not seen | **composition** (PP + CS ingredient known); second-statistic bet unresolved pending appendix |
| Podkopaev & Ramdas, ICLR 2022, arXiv 2110.06177 | H0: R_T <= R_S + eps_tol (also relative form); bounded loss; time-uniform | labelled source holdout (estimated U_S = R^_S + eps, alpha split delta_S+delta_T), target labels possibly delayed/batched | betting or CM-EB lower CS with predictable lambda (summary) | Prop. 1 (verbatim): type-I <= delta; Ville | Supervised baseline for bounded cost: **yes, directly**. No PP, no second statistic | **known** (baseline, item 3) |
| Shin-Ramdas-Rinaldo, e-detectors, arXiv 2203.03532 | change detection, ARL >= 1/alpha | none specific | SR/CUSUM e-detectors, plug-in predictable parameters, mixtures | Thm 2.4 (verbatim): E_inf N* >= 1/alpha | SR threshold / ARL-only guarantee matches repo's finding | **known** |
| Betting on Predictions, Tenzer-Tolochinsky-Romano, arXiv 2605.28533 | H0: theta_Y = null (marginal) or conditional theta_{Y|x}; hypothesis testing, not drift of a deployed model's risk | i.i.d. labelled n + unlabelled N per step + M null datasets; delay not addressed | soft-rank e-statistic on classifier imputations; gamma_t by AdaGrad; mixture weights by EG across component e-statistics (cross-statistic history -> weights) | Prop 3.1/3.2, Cor 3.3 (informal), Thm 3.4 TV-robustness | Mixture-weight dependence on other statistics' history exists, but weights not bets, and no PP/IPW increment | **unresolved** (not the same object; closest on "other statistics' past informs this one") |
| Hsu & Shekhar, arXiv 2607.17409 (LLM evaluation) | CS for mean correctness over N questions | active querying q_t predictable, binary labels, prior-model predictions p^_t | AIPW-type betting increment 1+lambda(Phi-m), Phi = mean p + (Z-p_I)/(N q(I)); lambda maximises expected log growth (oracle p* / plug-in) | Prop 4.1, 4.2 verbatim; practical plug-in CS reported heuristic (summary) | **IPW/AIPW increment + predictable bet + growth-optimal bet: yes**. No monitoring of drift, no tolerance term, no second-statistic bet, no discounting seen | **known** for the IPW-betting engine; **composition** for H2c |
| Kilian-Cortinovis-Caron, arXiv 2505.18000 | CS for argmin of risk (estimating equation) | labelled + unlabelled stream | asymptotic CS by mixtures; control variates; no betting | Thm 1-5 asymptotic CS | no betting e-process | **known**, not a close prior (asymptotic, no e-process) |
| Active risk-controlling prediction sets | -- | -- | -- | -- | -- | **unresolved**: arXiv ID not located; "I cannot confirm this." |

## What this does and does not say about H2c
- Contained in published work (verbatim evidence): PP-style estimator with predictable tuning (PPRM); IPW/AIPW betting increment with predictable sampling and log-growth bets (Hsu-Shekhar); tolerance/alpha-split monitoring of bounded risk (Podkopaev-Ramdas); SR/ARL (e-detectors).
- Not found in the read portions of any paper: a Brier (proxy) statistic's history choosing the discounted Kelly bet of the tested cost increment. That is the only candidate delta, and it is a bet-selection rule, i.e. the ledger's M6 "betting engine" class. Absence in ~20-30% of each text is **not** evidence of absence.
- Provisional reading: H2c = composition of known ingredients + a bet-selection heuristic. Do not claim methodology novelty.

## Decisions
- Item 3 baselines: supervised PR confidence sequence handles bounded costs as published (adapt, `FAITHFUL_ADAPTATION`); PPRM-style semi-supervised version is `SOURCE_INSPIRED` until Thm 3.2 / eta_t rule / q(lambda) are verified from LaTeX source.
- Next verification step: fetch `arxiv.org/src/2602.02229` and `2607.17409` (host open) to settle the unresolved cells; locate active-RCPS ID via search.
- NYC-taxi real data: `BLOCKED_EXTERNAL_ACCESS` (403 on CloudFront).

## Addendum 1 (iteration 1): verification from LaTeX sources
Sources: `arxiv.org/src/2602.02229` (formal_paper.tex) and `arxiv.org/src/2607.17409` (arXiv_v0.tex), read directly.

**PPRM (verified verbatim):**
- Thm "Type-I Error Guarantee of PPRM": for any predictable {eta_t}, P_H0(exists t: Phi_t^PP=1) <= delta_S + delta_T. Proof is one sentence: unbiasedness (Lemma, predictable eta_t) plus the SRM lemma. Estimand is the running mean of risks.
- Lower sequence: CM-EB conjugate mixture (Howard et al.) with V_t^PP = sum (R^PP_t' - Rbar^PP_{t'-1})^2. Source bound U_0^PP via the betting method of Einbinder et al. 2025.
- Not present anywhere in the tex: Kelly, discounting, importance weighting by labelling probability, delay model, or a second statistic choosing a bet (grep). eta_t is chosen by a variance-minimising plug-in on a sliding window.
- Consequence: the "second statistic's history chooses the bet" cell for PPRM moves from unresolved to **not present**. PPRM verdict stays **composition** relative to H2c (PP increment known; Q/q IPW, Kelly, Brier guidance not in PPRM).
- Observation (not verified further): PPRM's proof asserts unbiasedness of the running average suffices for the CM-EB bound; whether the conditional-mean structure needed by the sub-exponential CS holds when eta_t is data-dependent is **not checked here**. I cannot confirm this.

**Hsu & Shekhar (verbatim):**
- Uses Kelly / log-growth explicitly for querying (line "also known as the Kelly criterion") and for bets; predictable plug-in r_t = p^_{t-1} is stated to keep the e-value guarantees (Prop. validity proofs only need F_{t-1}-measurable r_t). This **contradicts** the earlier tool summary that called the plug-in CS "not valid"; the heuristic part is the grid-based CS set, not the e-values.
- Still no drift monitoring, tolerance term, discount, or Brier-guided bet.
- Verdict unchanged: **known** for AIPW + predictable + growth-optimal betting engine.

**Still unresolved:** Betting on Predictions (2605.28533, source not yet pulled), Podkopaev-Ramdas appendices, active RCPS (ID not located), Einbinder et al. 2025 (source bound, cited by PPRM).
