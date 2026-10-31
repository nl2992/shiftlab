# 02 Prior art and novelty audit (Agent B)

Date: 2026-10-30. Scope: programme "From Detection Power to Deployment Value".
This is a bounded audit, not a completed novelty review. Verification levels:
FULL_TEXT = full text extracted and the relevant sections read this session; ABSTRACT = official abstract page only;
SEARCH_SNIPPET = web-search summary only; LOCAL = taken from earlier repo notes (not re-opened here); UNVERIFIED = not read.
No novelty verdict rests on an ABSTRACT, SEARCH_SNIPPET, LOCAL or UNVERIFIED row alone, except where marked provisional.
Theorem-direction assessments (Section 3b) are the auditor's own analysis, not citations.

Local notes already covering related ground (not repeated): docs/closest_prior_work.md, docs/chugg_group_betting_paper_to_code_audit.md,
references/novelty_audit.md, references/closest_competitors.md, docs/research_refinement_v1/PRIOR_ART_AND_NOVELTY_MATRIX.md, docs/switching_*_prior*.md.

## 1. Per-paper table

| # | Work | Level | Problem / target | Information and feedback | Guarantee | Resources / intervention | Metrics, data | Hypotheses established? | Code | Comparator feasibility |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Zhang, Cai, Yu, Simeone, PPRM, ICML 2026 (PMLR v306 pp. 154241-154262) | FULL_TEXT | Detect harmful shift: running risk R-bar_t (mean of R_s) exceeds source risk R0 + tol; H0: R-bar_t <= R0+tol for all t. Loss bounded in [0,1]. | Per-round i.i.d. batch from P_t; labeled subset plus unlabeled data with synthetic labels; labels immediate (no delay, no action-dependent outcome). Source calibration i.i.d. from P0. | Thm 3.2: P_H0(exists t: alarm) <= delta_S + delta_T for any predictable reliance sequence lambda_t (PPI unbiasedness Lemma 3.1, CM-EB bounds). Appendix A.4 gives an approximate detection-delay improvement condition in a stationary binary-risk regime (Prop A.1). | Label scarcity only. No intervention model; "retraining may be initiated" is mentioned, never simulated. Compute overhead in App D.5. | Detection delay, type-I error; image classification, LLM-as-judge, wireless channel equalization. Baselines: Ideal PPRM, SRM, URM (Schirmer). | None. Optimizes detection delay only; no decision-cost evaluation. It is raw-power evidence, i.e. the premise H5 challenges; it does not test H1-H6. | None listed on page. | Predictive-risk monitor: FORMULA_ADAPTATION to paired decision cost (repo has docs/pprm_paired_decision_benchmark.md; its null is a running-mean null, weaker than an eventwise conditional null). Not VERIFIED_REPRODUCTION. |
| 2 | Xu, Karampatziakis, Mineiro, Active anytime-valid RCPS, NeurIPS 2024 (arXiv 2406.10490) | ABSTRACT (+LOCAL) | Sequential risk-controlling prediction sets with an active label policy under expected-label budget; betting wealth process. | Labeler queries by covariate; label reveals loss immediately. | Anytime-valid risk control; optimal label policy/predictor characterization; regret linking estimation error to wealth. Theorem statements NOT read. | Label budget. No intervention. | Utility vs labels, simulated and real. | None. | No repo link on arXiv page. | FORMULA_ADAPTATION of the active-labeling + betting engine only; theorem scope UNVERIFIED. |
| 3 | Liu, Xia, Stevens, Chen, Contextual Active Model Selection (CAMS), NeurIPS 2024 (arXiv 2207.06030v4). Note: Karampatziakis is NOT an author. | FULL_TEXT of first ~100k of ~198k chars of HTML (setting, theorems, baselines, datasets); appendix tail unread | Per-round choice among k pretrained models with label queries under budget b. | Contexts arrive; a query reveals the 0-1 loss of ALL k models (full information on query); no feedback otherwise. Stochastic and adversarial streams. | Thm 1: constant pseudo-regret w.p. 1-delta (needs unique best policy, Delta>0, p_min>0); Thm 3: O(sqrt(T log|Pi*|)) adversarial regret; query-complexity Thms 2, 4. | Label cost via budget; model selection is the action; NO switching cost, NO delay. | Cumulative 0-1 loss vs query cost; CIFAR10, DRIFT gas, Vertebral, HIV, CovType; baselines RS, MP, QBC, IWAL, CQBC, CIWAL. | None. No change detection or monitor-power notion. A no-monitor comparator class (select continuously instead of detect-then-switch). | github.com/xuefeng-cs/Contextual-Active-Model-Selection (from paper text; not run) | SOURCE_INSPIRED as a mandatory continuous-selection baseline; no reproduction attempted. |
| 4 | Lamaakal, Yahyati, El Makkaoui, Ouahbi, Maleh, Drift2Act, arXiv 2603.08578 (CAO Workshop at ICLR 2026) | FULL_TEXT (pdftotext; main text and selected appendices) | Drift monitoring as constrained control: belief over drift type -> action in {recalibrate, TTA, abstain, rollback, retrain}, gated by an anytime-valid upper certificate U_t(delta) on windowed risk. | Delayed labels (fixed d=50 in main table), random window sampling under label budget B_lab. | Thm 1 / Thm A.2: P(exists t: R_t > U_t) <= delta; requires UNIFORM random sampling within the window (Condition A). Corollary: no unsafe prediction without certificate violation. NO optimality or value guarantee for the controller; belief/gain-table control is heuristic. | Explicit action costs, cooldowns, label budget (Tables 2-3). | Total cost, safety violations, detection delay T_det, recovery time, worst-group accuracy; Camelyon17, DomainNet, SyntheticDrift-CIFAR. Baselines: alarm-only, adapt-always TTA, retrain-on-schedule, selective prediction, no-certificate ablation. | Motivates H2/H4 informally ("detection often ends at an alarm"). Reports T_det next to cost but never varies detector power under a fixed controller, so does not test H1 or H5. Gain table G(d,a) is calibrated offline on synthetic episodes with ground-truth risk. Workshop paper. | None found on arXiv page. | Whole controller: NOT_IMPLEMENTED / SOURCE_INSPIRED. Certificate: FORMULA_ADAPTATION. Baselines (alarm-only, adapt-always, schedule) are cheap and mandatory. |
| 5a | Podkopaev and Ramdas, ICLR 2022 (arXiv 2110.06177) | ABSTRACT (+ PPRM paper description, FULL_TEXT) | Sequentially test whether risk increases beyond source + tol; time-uniform CS. | Labels after prediction or in delayed batches. | Time-uniform type-I control. | None. | Simulated and real data. | No. | Not checked. | FORMULA_ADAPTATION (SRM), trivial. |
| 5b | Shin, Ramdas, Rinaldo, E-detectors (arXiv 2203.03532) | ABSTRACT | Nonparametric sequential change detection from sums of e-processes started at each time; SR and CUSUM-style e-detectors. | Bounded or sub-Gaussian data, no i.i.d. required. | Nonasymptotic ARL bound; near-optimal delay bounds for sub-Gaussian / sub-exponential. | None. | Basketball example. | No. | Not checked. | FORMULA_ADAPTATION (e-detector on paired-harm increment); must re-derive from the full paper. |
| 5c | Waudby-Smith and Ramdas, betting CS (arXiv 2010.09686) | ABSTRACT | Time-uniform CS for bounded means by betting. | Bounded observations. | CS coverage, variance-adaptive. | None. | - | No. | Not checked. | FORMULA_ADAPTATION. |
| 5d | Page 1954 CUSUM; Lorden 1971; Pollak 1985; Shiryaev / Roberts SR; Page-Hinkley | UNVERIFIED (originals not opened) | Classical QCD, minimax (Lorden, Pollak) and Bayesian (Shiryaev). | - | Optimality under likelihood-ratio models. | - | - | See 3(a). | - | CUSUM, SR, Page-Hinkley: FORMULA_ADAPTATION. |
| 5e | Veeravalli and Banerjee, QCD survey (arXiv 1210.5552) | ABSTRACT | Bayesian and minimax QCD; optimal and asymptotically optimal solutions. | - | - | - | - | Abstract does not state a decision-cost conclusion. | - | n/a |
| 6a | Mahadevan and Mathioudakis, Cost-Effective Retraining / Cara (arXiv 2310.04216; KBS 2024 per search snippet) | FULL_TEXT (arXiv HTML, summarized by fetch tool; not independently re-read) | Retrain vs keep per batch; strategy cost = staleness cost + retrain cost kappa; Cara-T/CT/P. | Batches; staleness estimated by kernel-weighted similarity; no delay. | No formal guarantee. Empirical comparison to a retrospective DP oracle. | Retrain cost kappa; no label cost. | Strategy cost, SCPE vs oracle, accuracy; Gauss, Circle, CovCon, Electricity, Airlines, Covertype; baselines NR, Markov, ADWIN, DDM. | Partial empirical support for H4/H6: cost-aware rule beats ADWIN/DDM in cost with fewer retrains. | "Supplementary material"; not located. | SOURCE_INSPIRED (threshold / cumulative-staleness rules easy to re-implement; not a verified reproduction). |
| 6b | Regol, Schwinn, Sprague, Coates, Markovich, When to retrain a machine learning model (UPF), ICML 2025 / PMLR 267 (arXiv 2505.14903) | FULL_TEXT (abstract, intro, related work, problem setup; Prop 3.1 located, proofs and results tables skimmed) | Retraining schedule minimizing retrain cost + average performance over a horizon; forecast performance with uncertainty (UPF). | Few labeled examples per step; shift unknown. | Prop 3.1: upper limit on optimal number of retrains from performance bounds. | Retrain cost; oracle schedule via DP. | Cost-area over cost-ratio range vs oracle; 7 datasets; baselines Cara, ADWIN, FHDDM, KSWIN, offline RL. | States that shift detection "cannot account for the cost trade-off" and that detector-triggered retraining recommends retraining "far too often" when retraining is costly; supported empirically. Close to H4 and to H1 in the high-retrain-cost regime; no controlled detector-power sweep. | "Supplementary"; not located. | SOURCE_INSPIRED (UPF); ADWIN/FHDDM/KSWIN trigger baselines cheap and mandatory. |
| 7a | Bifet, Classifier concept drift detection and the illusion of progress, ICAISC 2017 (DOI 10.1007/978-3-319-59060-8_64) | ABSTRACT only (full text inaccessible) | Methodology critique: evaluating detectors by replacing a classifier at each signal is flawed; a non-detector can improve accuracy via temporal dependence. | - | - | - | - | Supports a caution about confounded evaluation, NOT the claim "better detection => worse decisions". | - | Methodological lesson only. |
| 7b | Ahmed et al., label-free monitoring/TTA audit, Frontiers in AI 2026 | LOCAL | Monitor / model-selection inversion on intrusion data. | - | Propositions on blindness. | - | - | Close in spirit to H4 for label-free monitors. | - | Not a comparator. |
| 8a | Thomas, Theocharous, Ghavamzadeh, HCPI, ICML 2015 (PMLR v37 pp. 2380-2388) | SEARCH_SNIPPET | Batch RL with a probabilistic guarantee that a proposed policy beats a lower bound at confidence 1-delta. | Logged trajectories, importance sampling. | High-confidence safety test. | Needs more data than naive improvement. | Gridworld, mountain car, marketing. | No. | - | FORMULA_ADAPTATION / UNVERIFIED (candidate-promotion safety test). |
| 8b | Swaminathan and Joachims, CRM/POEM (arXiv 1502.02362) | ABSTRACT | Learning from logged bandit feedback with variance-aware bound. | Propensity-scored logs. | Variance-regularized bound. | - | - | No. | - | Not needed. |
| 8c | Waudby-Smith, Wu, Ramdas, Karampatziakis, Mineiro, Anytime-valid OPE for contextual bandits (arXiv 2210.10768) | ABSTRACT | Time-uniform CS for off-policy value with time-varying logging policy and dependent contexts. | Logged bandit feedback; weights need not be bounded. | Time-uniform CS, nonparametric. | - | - | No. | - | FORMULA_ADAPTATION, only if the study has bandit-type feedback. |
| 8d | Off-policy CS (ICML 2021); WATCH (ICML 2025); Prediction-powered e-values (ICML 2025); Conformal Policy Control; RCCDA (NeurIPS 2025); Schirmer et al.; Amoukou et al. | LOCAL | See docs/closest_prior_work.md | | | | | | | Tracked in local notes at their stated levels. |

## 2. Hypothesis status against what was read

| Hyp | Closest evidence | Status |
|---|---|---|
| H1 detector ranking reversal under fixed controller | Regol 2025 (detector-triggered retraining over-triggers when retrain cost is high; ADWIN/FHDDM/KSWIN lose to cost-aware UPF); Mahadevan 2024 (cost-aware rules beat ADWIN/DDM). These compare detectors against different decision rules; they do not hold the controller fixed and sweep detector power. Bifet 2017 is about evaluation confounds. | PARTIALLY_NEW. Qualitative fact is folklore; the controlled-reversal protocol was not found. |
| H2 actionability determines conversion | Drift2Act asserts it informally; it never isolates actionability. | PARTIALLY_NEW (informal precedent). |
| H3 small headroom => small monitoring value | Follows from the ceiling; Regol Prop 3.1 is a close relative. | TRIVIAL_COROLLARY as a statement; empirical headroom decomposition is the contribution. |
| H4 alarm validity != economic usefulness | PPRM, SRM, e-detectors give only type-I / delay guarantees; Regol; Drift2Act motivation; Ahmed et al. | ESTABLISHED qualitatively; quantification is not. |
| H5 resource-efficient monitoring beats higher raw power | Not found. PPRM, Xu et al., CAMS improve power per label but are judged by power or utility proxies, not decision cost. | POTENTIALLY_NEW (absence of search hits is not proof). |
| H6 simple methods competitive | Mahadevan (threshold on staleness), Regol, Drift2Act ablations. | ESTABLISHED in spirit; must be shown in this setting. |

## 3. Critical assessment

(a) Is "better detection does not imply better decisions" known? Yes in three senses, none equal to the programme's claim:
1. Decision-theoretic: in Bayesian QCD the optimal rule trades delay against false-alarm cost (Shiryaev formulation; UNVERIFIED from originals, the Veeravalli-Banerjee abstract only confirms a Bayesian formulation exists). A smaller delay at equal ARL need not be Bayes-better when action costs differ. A counterexample is easy; a deployment-cost benchmark is not provided.
2. Empirical: Regol et al. and Mahadevan-Mathioudakis report detector-triggered retraining being cost-inefficient.
3. Methodological: Bifet 2017 says classifier-accuracy evaluation of detectors is confounded; this is a different claim.
So the slogan cannot be claimed as novel. Novelty must come from (i) a controlled design fixing controller, intervention cost and delayed feedback while varying detector power and label usage at matched ARL, (ii) a decomposition of value into headroom x conversion x timing, (iii) conditions under which ranking is preserved.

(b) Theorem directions (auditor's own analysis; closest known item named):

| Thm | Statement | Closest | Status |
|---|---|---|---|
| T1 | Monitoring dominance (ARL, delay) does not imply decision dominance: counterexample | Bayesian QCD cost trade-off (unverified original); Regol empirical | TRIVIAL_COROLLARY as a bare counterexample; PARTIALLY_NEW only if tied to delayed-feedback / label-cost structure with reversal at calibrated ARL under a fixed controller. |
| T2 | Online value <= dynamic hindsight headroom | DP oracle lower bounds on cost (Mahadevan, Regol); hindsight regret benchmarks (CAMS) | TRIVIAL_COROLLARY (by definition of oracle). Value lies in the measurable decomposition. |
| T3 | Delay x persistence bounds on realizable switching gain | Regol Prop 3.1 (bound on number of worthwhile retrains); e-detector delay bounds (Shin et al.) | PARTIALLY_NEW if it composes a detector delay bound with a persistence / switch-cost model into a gain bound; ingredients exist, composition not found. |
| T4 | Sufficient conditions (stochastic dominance of alarm times + monotone persistent benefit) under which better monitoring implies better decisions | Standard stochastic-ordering arguments; no monitoring-to-decision statement found | UNKNOWN / PARTIALLY_NEW. Proof likely short; value is in sharpness (necessity, counterexamples when persistence or monotonicity fails). Search not exhaustive. |

(c) Missing mandatory baselines (include, or exclude with a stated reason):
- Never-act, always-act (adapt-always), scheduled retraining (Drift2Act, Mahadevan).
- Oracle-change-time trigger and retrospective DP oracle (Mahadevan, Regol).
- Cost-aware threshold / cumulative-staleness rule (Cara-T/CT) and forecast-based UPF.
- Classical triggers: CUSUM, Shiryaev-Roberts, Page-Hinkley, ADWIN, DDM/FHDDM, KSWIN.
- E-detectors on risk (Shin et al.), SRM, PPRM as the label-efficient variant.
- Label allocation: uniform/random, uncertainty / QBC (CAMS baselines), Xu et al. active policy.
- Continuous model selection without a monitor: CAMS.
- Bayesian posterior-threshold (Shiryaev) rule with decision costs, as the decision-theoretic anchor.
- For promotion / rollback certification (only if feedback is bandit-type): anytime-valid OPE and an HCPI-style safety test.

## 4. Novelty matrix

| Item | Closest work | Status |
|---|---|---|
| H1 reversal under fixed controller | Regol 2025; Mahadevan 2024 | PARTIALLY_NEW |
| H2 actionability | Drift2Act (informal) | PARTIALLY_NEW |
| H3 headroom bound | Regol Prop 3.1; DP oracles | TRIVIAL_COROLLARY |
| H4 validity != usefulness | PPRM, SRM, e-detectors; Regol | ESTABLISHED (qualitative) |
| H5 efficiency beats raw power | none found | POTENTIALLY_NEW |
| H6 simple competitive | Mahadevan; Regol | ESTABLISHED in spirit |
| T1 | Bayesian QCD (unverified) | TRIVIAL_COROLLARY |
| T2 | DP oracle bounds | TRIVIAL_COROLLARY |
| T3 | Shin et al. delay + Regol Prop 3.1 | PARTIALLY_NEW |
| T4 | none found | UNKNOWN |
| Paired decision-harm e-process under delay | local matrix (Q1: reject novelty claim) | not re-audited |

## 5. Comparator fidelity matrix

| Comparator | Class | Reason |
|---|---|---|
| PPRM | FORMULA_ADAPTATION | Theorem read; predictive-risk estimand; no code; adapt to paired cost with explicitly weaker null |
| SRM | FORMULA_ADAPTATION | Abstract + PPRM description; code not checked |
| E-detector (SR / CUSUM) | FORMULA_ADAPTATION | Abstract only; re-derive from paper before use |
| Xu et al. active RCPS | FORMULA_ADAPTATION (labeling) / INAPPLICABLE_CONTRACT (prediction sets) | Target is RCPS, not monitoring |
| CAMS | SOURCE_INSPIRED | Code exists, not run; label-on-query reveals all-model losses, differing from paired-cost availability |
| Drift2Act | NOT_IMPLEMENTED (whole); FORMULA_ADAPTATION (certificate) | No code; gain table needs ground-truth episodes; certificate requires uniform random sampling |
| Cara | SOURCE_INSPIRED | Details beyond HTML summary unread; code not found |
| UPF | SOURCE_INSPIRED / UNVERIFIED | Method details not read |
| ADWIN, DDM, FHDDM, KSWIN, CUSUM, SR, Page-Hinkley | FORMULA_ADAPTATION | Standard; record library versions |
| HCPI, anytime-valid OPE | UNVERIFIED / FORMULA_ADAPTATION | Only abstracts or snippets read |

No row is VERIFIED_REPRODUCTION: no external code was run in this audit.

## 6. Most promising gap (provisional)

A controlled monitoring-to-value study: fix the controller and intervention costs, sweep detector power and label allocation at matched ARL, decompose realized value into headroom x conversion x timing, give a sharp preservation condition for monitor ranking (T3/T4), and test H5. Closest threats: Regol et al. (ICML 2025) and Drift2Act, neither of which has the fixed-controller power sweep or a monitor-ranking theorem.

## 7. Not read / limitations

Originals for Page, Lorden, Pollak, Shiryaev, Page-Hinkley; Bifet full text; Zliobaite ROI; Xu et al. theorems and experiments; full texts of Podkopaev-Ramdas, e-detectors, betting CS, HCPI; Cara code; UPF method; Drift2Act experiments in detail. Only a handful of searches were run; absence of a paper is not evidence of absence. Summaries of Cara, CAMS and the Xu et al. abstract come from the fetch tool's summarization and were not independently re-read.

## 8. References actually opened

- https://proceedings.mlr.press/v306/zhang26g.html and https://raw.githubusercontent.com/mlresearch/v306/main/assets/zhang26g/zhang26g.pdf (PDF text extracted and read)
- https://arxiv.org/abs/2603.08578 and https://arxiv.org/pdf/2603.08578 (PDF text extracted and read)
- https://arxiv.org/abs/2406.10490 (abstract page)
- https://arxiv.org/html/2207.06030v4 (first ~100k of ~198k chars)
- https://arxiv.org/html/2310.04216 (Cara)
- https://arxiv.org/pdf/2505.14903v1 (UPF; text extracted, selectively read)
- https://arxiv.org/abs/2110.06177 ; https://arxiv.org/abs/2203.03532 ; https://arxiv.org/abs/2010.09686 ; https://arxiv.org/abs/2210.10768 ; https://arxiv.org/abs/1210.5552 ; https://arxiv.org/abs/1502.02362 (abstract pages)
- https://www.springerprofessional.de/en/classifier-concept-drift-detection-and-the-illusion-of-progress/12328150 (abstract only)
- Search snippets only, not opened: https://proceedings.mlr.press/v37/thomas15.html ; https://arxiv.org/abs/2509.14186
- Local repo notes listed at top (read; their cited sources not re-opened).
