# Prior art and novelty matrix

**Part 1 (B1) recorded 2026-10-28, loop tick 3.** It verifies the repository's existing
bibliography against primary sources and adds the closely related uncited papers found along the
way. **Part 2 (B2)**, a systematic fresh search through 2026-10-27 plus full reads of the papers
flagged below, follows in a later tick.

**Method.** Three Sonnet subagents (monitoring, certification, intervention) followed ARIS
`novelty-check` Phases A–B. They confirmed each paper's identity from its primary page and read the
method and theorem statements where accessible. Every row carries a verification level:
- FULL: the method and theorem sections were read;
- PARTIAL: the setting, null, assumptions and theorem statements were read, but not the proofs;
- ABSTRACT-ONLY;
- UNVERIFIED.

The lead (Opus) independently fetched the arXiv pages of the four uncited papers that matter most
(Section 3). **Rule applied:** no novelty judgment rests on an ABSTRACT-ONLY or UNVERIFIED row.
ARIS's novelty-check uses permissive verdict limits ("crowded-but-deltaed is PROCEED"). The brief's
stricter test, "could a reviewer get this by combining two existing algorithms?", governs here
whenever the two disagree.

**Cross-model check:** not run in this tick. ARIS novelty-check's Phase C (Codex) is deferred to
B2, after the full reads.

## 1. Verdicts on the brief's combination test

| Candidate contribution | Two-algorithm combination that already yields it | Verdict | What remains open (not established by anything read) |
|---|---|---|---|
| **Q1:** paired decision-harm monitoring with selective labels (Paper 1 as built) | DISCERN's disagreement-only labelling with a predictable propensity and an anytime-valid CS (Balachandran 2026, Thms 4–5) **plus** a published betting engine (Timans et al. UAI 2025 GRAPA, whose eventwise conditional bounded-mean null equals ShiftLab's after an affine map; or Xu / PPE) | **Yes: reject a novelty claim** (consistent with checkpoint B) | (i) An eventwise null under drift; DISCERN guarantees a weighted-average target with windowed restarts. (ii) **Action-dependent outcomes**, where only the chosen action's loss is observed; DISCERN, Timans, PPE and Xu all assume the label identifies the paired cost. (iii) Delayed feedback combined with gating. |
| **Q2:** statistically controlled promotion with adaptive information acquisition and switching costs | OCS gated deployment (Karampatziakis et al. 2021; the repo's "MOPE") or Waudby-Smith certificates; HCPI-style splitting for candidates; alpha-spending (OPI / AnyRank) for multiplicity; Digalakis et al.'s explicit switching-cost switch/continue rule; PPE / active e-processes for label acquisition. **Newly found:** Zhang, Wu and Qian (2026), slice-wise non-regression with incumbent fallback over a candidate library | **Yes for the generic version** (consistent with the 2026-10-26 NO-GO) | A certificate on the **future net benefit of the selected replacement over a post-switch horizon**, net of switching cost, when the improvement **need not persist**, under delayed and adaptively acquired feedback. Every certificate read bounds a historical or running-average value. The search was bounded. |
| **Q3a:** a costed continue/query/promote/retrain/fallback rule | **Drift2Act** (Lamaakal et al. 2026; uncited): a costed menu of no-op, recalibrate, query, retrain with cooldown, rollback and abstain, gated by an anytime-valid label-budgeted risk certificate with label delay; or Regol/CARA cost-aware retraining plus Conformal Policy Control's safe-reference fallback | **Yes: reject** | A paired-harm estimand (Drift2Act uses unpaired predictive risk), and **validity that holds through selection and the intervention itself**. Drift2Act's validity across model-changing interventions appears unaddressed; that is a subagent inference and needs a full read. ShiftLab has no such proof either. |
| **Q3b:** burst-robust allocation of a finite label budget over time for a gated monitor (exit-ledger M8) | A heuristic pacer is a routine combination of Xu active betting, an RCCDA-style virtual queue and DE-CuSum on/off control. ShiftLab's `DisagreementPacer` already is one. | **Yes for a heuristic.** No theorem-level precedent was found for the trade-off between a hard finite budget and an unknown burst count. | A minimax or regret statement for that trade-off. **Caution:** M4, a related observation-control idea, failed its registered pre-screen against an onset-informed temporal baseline. |

**Overall B1 reading.** Every broad framing in the brief's unifying question is already covered
by a combination of published methods: detection, certification, costed intervention and limited
information. What survives is narrow and technical:
- action-dependent (bandit) feedback in paired-harm monitoring;
- a persistence-aware certificate on future net benefit after promotion;
- validity of evidence through the intervention it triggers;
- a theorem for finite-budget allocation under bursts.

Phase C must test whether any of these supports a paper.

## 2. Corrections to the repository's bibliography (record only; no historical file edited)

| Item | Repository says | Primary source says | Where |
|---|---|---|---|
| Jang et al. ICML 2022 | "Sequential Predictive Two-Sample and Independence Testing" | Title is "Sequential Covariate Shift Detection Using Classifier Two-Sample Tests" (subagent-verified from PMLR) | `docs/closest_prior_work.md` |
| Amoukou et al. | "2024 preprint" | Accepted at NeurIPS 2024 | `docs/closest_prior_work.md` |
| DE-CuSum | arXiv 1105.1361 | arXiv 1211.3729 | intervention and monitoring audits |
| RCCDA guarantee | Update-frequency and cost guarantees | Theorem 5.3 needs a zero-error gain estimator | `docs/closest_prior_work.md` |
| Exit ledger M8 | DE-CuSum "already address[es]" burst allocation | DE-CuSum assumes known likelihoods and a rate constraint, not a hard finite budget with unknown bursts. **The ledger's statement is too strong**; M8's exclusion should rest on Paper 3 scope, not on prior coverage. | `docs/algorithm_search_exit_ledger.md` §1 |
| "RADAR" in the brief | No reference given | **The user confirmed on 2026-10-28** that RADAR is Zheng, Wiberg and Zhu, "Deciding When to Decide: Testing Operational Suboptimality Under Distributional Shift", arXiv 2608.29465 v1 (29 Aug 2026, no venue listed). RADAR is the method name (lead-fetched). It tests the incumbent decision's regret against the re-optimized decision, with latent preferences inferred by inverse optimization. Its guarantees are **asymptotic**, not finite-sample or anytime-valid. The acronym expansion in Appendix A row 18 is a subagent reading and has not been lead-checked. | `BRIEF.md` |

## 3. Uncited, closely related papers (lead-fetched identity)

| Paper | Identity check | Relevance | Status |
|---|---|---|---|
| Balachandran, "Pay Only for Disagreement" (DISCERN), arXiv 2609.17560, 2026-07-22, v1, single author | Lead-fetched | The source of gating; certified no-regression verdicts with label complexity ρ²/ε², valid under any stopping rule, across repeated promotions | Cited in phase docs but **absent from the manuscript draft and `closest_prior_work.md`**. FULL except the Thm 7–9 proofs. |
| Lamaakal et al., "Drift-to-Action Controllers" (Drift2Act), arXiv 2603.08578, 2026-03-09 | Lead-fetched | Closest Q3 prior art: costed intervention menu, delayed labels, anytime-valid risk certificate, rollback | **Uncited.** PARTIAL; needs a full read in B2. |
| Zhang, Wu and Qian, "Certifying Model Upgrades with Slice-Wise Non-Regression and Incumbent Fallback", arXiv 2609.13714, 2026-09-12 | Lead-fetched | Close Q2 prior art: search/evaluation separation, paired evaluation, exact incumbent fallback, candidate library, Learn-then-Test | **Uncited.** ABSTRACT-ONLY; needs a full read. |
| Zhou, Li and Zhu, "Safe Meta-Policy Design with Risk Control", arXiv 2610.10393, 2026-10-07 | Lead-fetched | Update scheduling under a budget on harmful updates; asymptotic analysis, no high-probability guarantee per the abstract | **Uncited.** ABSTRACT-ONLY |

The subagent parts list further uncited items, mostly ABSTRACT-ONLY or UNVERIFIED: E-FairDrift,
2605.20270, 2609.04388, 2605.06479 and others. **Open check:** the monitoring subagent saw
AI-review pages alleging a scaling mismatch in PPRM (Zhang et al. ICML 2026). ShiftLab implements
that bound. The claim is unverified and must be checked against the paper itself in B2, not
against the review page.

## 4. B2 work list

1. Full reads, with proof sections where they bear on validity: Drift2Act, Zhang–Wu–Qian 2026,
   DISCERN Thms 7–9, Zhou–Li–Zhu 2026, PPRM (the scaling question), Waudby-Smith OPE CS, Wang 2026.
2. Systematic search through 2026-10-27, run separately for each surviving narrow gap in Section 1
   (ARIS research-lit; arXiv, OpenReview, PMLR, NeurIPS 2025/2026, ICML 2026, AISTATS 2026,
   UAI 2026).
3. ARIS novelty-check Phase C: a Codex cross-model verdict on the four narrow gaps, sent as a
   dossier file.

---

# Appendix A. Monitoring cluster (Q1) (subagent matrix; identities in Section 3 lead-checked, others subagent-checked)

## B1 Prior-art verification: Q1 sequential monitoring of model/policy harm

Date of check: 2026-10-28. Repo read-only. Method: read repo records first, then pulled primary PDFs (arXiv, PMLR/GitHub mlresearch, NeurIPS proceedings, Frontiers) and read the setting, null, assumption and theorem statements with pdftotext. Local text copies are in `scratchpad/pdf/`. Quotes are avoided; everything is paraphrase.

Verification levels: FULL = method and theorem/validity statements read in the PDF (proof appendices skimmed or not read); PARTIAL = setting, null, assumptions and theorem statements located and read, but not the whole body; ABSTRACT-ONLY = abstract/metadata only; UNVERIFIED = not accessed. No novelty judgment rests on an ABSTRACT-ONLY row.

Shared ShiftLab target for the last column: paired decision harm `R_t(pi_t) - R_t(pi_ref)` (eventwise conditional null on the paired cost Z_t), with selectively queried labels.

### 1. Bibliographic corrections found in the repo

1. **Jang et al. ICML 2022 is mis-titled** in `docs/closest_prior_work.md` (row "Sequential Predictive Two-Sample and Independence Testing"). The PMLR v162 jang22a record is *Sequential Covariate Shift Detection Using Classifier Two-Sample Tests* (Jang, Park, Lee, Bastani; pp. 9845-9880). The title the repo gives belongs to a different Podkopaev-Ramdas line of work; I did not verify that paper here.
2. **Amoukou et al. is not just a "2024 preprint"**: arXiv 2412.12910 states it was accepted at NeurIPS 2024.
3. **Banerjee & Veeravalli**: the repo's G0 list names arXiv 1105.1361 for DE-CuSum. 1105.1361 is the Shiryaev-based two-threshold on-off algorithm (*Data-Efficient Quickest Change Detection with On-Off Observation Control*). DE-CuSum itself is in arXiv 1211.3729 (*Data-Efficient Quickest Change Detection in Minimax Settings*, submitted to IEEE-TIT Nov 2012; no journal ref listed on arXiv).
4. **Timans et al.** is UAI 2025, PMLR 286, pp. 4204-4226 (arXiv 2506.16416 per search results); repo identity is correct.
5. **RADAR** is cited in `docs/research_refinement_v1/BRIEF.md` line 75 with no reference anywhere in the repo. Best match found is below (row 18); this match is my inference, not something the repo states.
6. Third-party "Pith" pages for Timans and PPRM carry AI-generated referee-style critiques (a scaling mismatch in PPRM; a guarantee critique for Timans). I did not verify these and did not use them. Worth a human check against the PPRM threshold comparison, since ShiftLab implements that bound.

### 2. Comparison matrix

Columns: Paper | Year/Venue/id | Exact problem | Assumptions | Guarantees | Feedback contract | Intervention costs | ShiftLab comparator | Remaining gap | Verification.

| # | Paper | Year/Venue/id | Exact problem | Assumptions | Guarantees | Feedback contract | Intervention costs | ShiftLab comparator | Remaining gap vs paired decision harm under selective labels | Verif. |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Podkopaev & Ramdas, *Tracking the risk of a deployed model and detecting harmful distribution shifts* | ICLR 2022; arXiv 2110.06177 (v4 May 2022) | Sequential test of H0: target risk of one fixed predictor <= source risk + tol (Eq. 1); also running-risk null (Eq. 2) and relative tolerance (Eq. 3) | Bounded loss; target either iid or only independent (running-risk null); source holdout gives an upper bound | Prop. 1: split alpha between source UCB and target CS, time-uniform type-I control for all three nulls | Labels revealed after prediction, or delayed batches (abstract, Remark 2: minibatches). No selective sampling | None (alarm may trigger retraining; not modeled) | Predictive-risk monitor `SRM` inside PPRM audit; Timans replay covers the eventwise variant (not Podkopaev itself) | One model, running-average risk null, no paired reference policy, no selective labels, no cost of acting. Delay of labels in batches is covered, so "anytime-valid under delayed labels" is not ours | FULL (body; appendix proofs not read) |
| 2 | Prinster, Han, Liu, Saria, *WATCH* | ICML 2025, PMLR 267 | Online monitoring of any unexpected change point via weighted conformal test martingales; adapt to mild covariate shift, flag concept/extreme covariate shift | Null H0(f-hat) is an approximation of the weighted exchangeability; Thm 3.1 weighted-conformal p-values iid uniform under it; weights from density-ratio assumptions; concept shift assumes Y given X invariant under the null | Thm 3.1 (exact validity under the assumed null), Prop. 3.2 anytime false-alarm control (Ville), Prop. 3.3 ARL bound for SR | Every point comes with a true label (conformal scores). No selective or delayed labeling | None | None (matrix row: "not comparable as-is") | Targets distributional/conformal null, not a decision-cost mean. Cannot be scored as decision-harm detection without a score and null bridge, as the repo already states | PARTIAL (abstract, setup, Thm/Props 3.1-3.3 statements) |
| 3 | Zhang, Cai, Yu, Simeone, *Prediction-Powered Risk Monitoring (PPRM)* | ICML 2026, PMLR 306 (arXiv 2602.02229) | Anytime-valid lower bound on running predictive risk of one fixed model vs a source upper bound plus tol, using synthetic labels plus a few true labels | Bounded loss; positive labeled and unlabeled batch each round; independent, same-round distribution; predictable eta_t; Assumption-free about the predictor | Lemma 3.1 (unbiasedness), Thm 3.2 (type-I control by reduction to the SRM lemma), Lemma 3.3 (variance-optimal eta) | Per-round small labeled batch plus separate unlabeled batch (batch design, not event-level selective queries; no propensity) | Only compute cost (App. D.5) | `src/shiftlab/dive/pprm_risk_monitor.py`: faithful predictive-risk path, source bound checked vs ConfSeq; adaptation (not faithful) is `PPIBlockConfidenceSequence`. Frozen synthetic confirmation: PPRM 7/300 detections | Predictive risk, one model, no reference policy, no replacement certification. Does not treat Horvitz-Thompson queries with propensity; separate-pool assumption fails under selective gating | PARTIAL |
| 4 | Schirmer, Jazbec, Naesseth, Nalisnick, *Monitoring Risks in Test-Time Adaptation* | NeurIPS 2025; arXiv 2507.08721 | Monitor running risk of an online-updated model sequence p_1..p_t vs source risk + tol; supervised and label-free routes | Bounded loss; label-free route needs Assumption 1 (proxy-separation between test FPR and source FPR plus test FNR); Prop. 1 lower bound; authors note it can fail during warm-up and with static source model and still needs a labeled test stream to check | Time-uniform lower CS on the running risk (supervised), valid lower bound under Assumption 1 (unsupervised) | Supervised: labels per step; unsupervised: features only plus source calibration labels | None | Not implemented; repo audit excludes it from the numeric frontier (no TTA task) | Predictive risk of adapted model; no paired reference, no cost, no selective labels | PARTIAL |
| 5 | Amoukou, Bewley, Mishra, Lecue, Magazzeni, Veloso, *Sequential Harmful Shift Detection Without Labels* | NeurIPS 2024; arXiv 2412.12910 | Extend Podkopaev-Ramdas by replacing the label error with a learned error-estimator proxy; sequential mean and quantile tests | Assumption 4.1: proxy false-discovery probability in production no more than at source (time-uniformly); authors say it holds only approximately empirically (App. A) | Thm 4.2 under Assumption 4.1 (false-alarm control); bias-corrected variant if violated | Label-free at test time; labels only at source | None | Not implemented as a comparator (scope reference only) | Predictive harm via proxy; proxy assumption can be violated under shift; no paired policy cost | PARTIAL |
| 6 | Timans, Verma, Nalisnick, Naesseth, *On Continuous Monitoring of Risk Violations under Unknown Shift* | UAI 2025, PMLR 286, 4204-4226 | Detect violation of a bounded risk level by testing-by-betting; null E[z_t given F_{t-1}] <= theta for all t | Bounded z in [0,1]; predictable betting; no assumption on shift type; calibration iid data for source risk in the iid variant | Lemma 4.1 (valid wealth process), Lemma 4.2 (false-alarm guarantee), Prop. 4.5 (worst-case detection delay) | z_t revealed each step (full feedback); no selective labels or delays | None for acting (motivates costly alarms only) | `official approx_grapa/grapa` replayed, wealth max error 0 and 1.86e-7; registered comparison found no adjusted advantage over ShiftLab fixed-stake mixture | The eventwise conditional bounded-mean null is the SAME null the repo uses for paired cost after an affine map. So with full feedback and one policy pair Paper 1 reduces to Timans on Z_t. Only selective/delayed feedback and policy-pair identification remain | PARTIAL (setup, lemmas, Prop 4.5 located) |
| 7 | Csillag, Struchiner, Goedert, *Prediction-Powered E-Values (PPE)* | ICML 2025, PMLR 267; arXiv 2502.04294 | Replace a valid e-value by a proxy-corrected e-value using a few labels with known propensity | Bounded base factor in [a,b]; q_t >= 1 - a/b positivity; predictable propensity and proxy; Lipschitz for power result | Thm 2.1 (valid e-value), Assumption 2.5 and Prop. 2.6 for sequential use; power Thm 2.2 | Selective labels with known predictable propensity, cheap proxy on every unit | Label budget only via q (no intervention costs) | `src/shiftlab/dive/prediction_powered_evalues.py`; null 0/1,000, +12.5 pp over fixed-mixture | Repo adaptation to paired cost is valid only if both action costs are identified from the observed label; paper makes no policy-pair claim | PARTIAL (statements; repo audit corroborated) |
| 8 | Balachandran, *Pay Only for Disagreement: Certified No-Regression Verdicts for Model Updates (DISCERN)* | arXiv 2609.17560 v1, 22 Jul 2026; single author; no peer-reviewed venue listed (PDF carries a JMLR-style template) | Paired risk difference delta = E[loss(g)-loss(f)] for candidate vs incumbent; certify no-regression with labels bought only on disagreements | iid stream (drift only in Sec. 5.7); prediction-determined loss (Assumption 1: same prediction implies same loss); routing probability predictable, in [pi_min,1], and must not depend on the label | Lemma 3 (HT increment conditionally unbiased, bounded by B/pi_min); Thm 4 (anytime validity, EB CS); Thm 5 (any predictable routing, including adversarial); Thms 7-9 (rho^2/eps^2 label complexity and matching lower bounds); per-slice (Sec. 5.4); promotion chains (Sec. 5.5); under drift only a weighted-average target, windowed restart as repair (Sec. 5.7, 6.5) | Both models' predictions observed free on all traffic; label requested at unit cost on a sampled disagreement. No delayed labels, no bandit or counterfactual outcomes | Label cost only (also notes shadow-scoring compute). No cost of switching or acting | `gated_monitor_*` results and A3 `discern_gated_eb` are a "DISCERN-style adaptation (no official code)". Repo already calls gating "not our contribution" | **Closest prior work to Paper 1 as stated here.** Remaining: eventwise conditional (not weighted-average) null under drift; non-prediction-determined or action-dependent outcomes; delayed feedback; betting engine instead of EB. The first is a change of target, the others are untested extensions | FULL (setting, protocol, Lemma 3, Thms 4-5, drift, limitations; proofs of Thms 7-9 not read) |
| 9 | Xu, Karampatziakis, Mineiro, *Active, anytime-valid risk controlling prediction sets* | NeurIPS 2024; arXiv 2406.10490 | Anytime-valid RCPS with active labeling under a budget; predictable label probability q_t(x), betting e-process | Assumption 1 monotone risk; iid stream (authors say they mainly consider iid); bounded risk; propensity floor | Thms 1-2 anytime-valid risk control with predictor and probabilistic labels; Prop. 5 / Cor. 1 optimal q and predictor; Thm 3 regret | Selective labels with predictable propensity | Label budget; no action costs | Formula-level transfer audited in `docs/xu_active_betting_paper_to_code_audit.md` (comparator, no results) | Single-model risk control on iid data; paired decision harm, drift and gating on disagreement not treated | PARTIAL |
| 10 | Chugg, Cortes-Gomez, Wilder, Ramdas, *Auditing Fairness by Betting* | NeurIPS 2023 | Sequential test of equality of group conditional means by betting; multi-group via parallel games (Appendix B) | Group membership observed; bounded predictions; null mu_0 = mu_1 | Time-uniform type-I control; union bound over groups | Per-step observation; no selective labels | None | Per-stratum wrapper in `stratified_harm_eprocess.py`, audited as a standard composition (no novelty claim) | Different null (equality of group means, not per-stratum paired excess cost). Stratum-wise composition is a union-bound/average of existing betting games | PARTIAL (null, game, Appendix B pointer read; repo audit says full read) |
| 11 | Shin, Ramdas, Rinaldo, *E-detectors* | arXiv 2203.03532 v4 (2023); journal version not checked | Nonparametric sequential change detection by e-detectors; SR and CUSUM from sequences of e-processes | Pre-change class composite null; nonnegative baseline increments | Def. 2.2 E[M_tau] <= E[tau]; Prop. 2.3 mixtures; Defs 2.6-2.12 SR/CUSUM and e-SR/e-CUSUM | Full observations | None | `horizon_edetectors.py` with finite-horizon calibration instead of ARL threshold | Detection of change in a conditional mean; not tied to a policy pair or selective labels | PARTIAL (definitions read) |
| 12 | Banerjee & Veeravalli, DE-CuSum | arXiv 1211.3729 (minimax); arXiv 1105.1361 (Shiryaev on-off) | Quickest change detection with an observation-cost constraint using an on-off sampling policy | Known pre/post distributions (parametric; Hou-Bidkhori-Banerjee 2412.20207 relaxes to a family with least-favorable member) | Asymptotic optimality as false-alarm rate goes to zero; ADD-vs-observation-cost tradeoff | Choose whether to observe (observation control, not label request with propensity) | Observation cost is in the objective | Skipped events factor 1; DE-CuSum drift-during-skip "not implemented" per repo | Parametric likelihood-ratio theory, no unknown-mean nonparametric e-process validity under selective HT labels; DE-CuSum ideas are an obvious source for WP3 intensity rules (repo says so) | ABSTRACT-ONLY for 1211.3729; ABSTRACT-ONLY for 1105.1361 (first page read) |
| 13 | Jang, Park, Lee, Bastani, *Sequential Covariate Shift Detection Using Classifier Two-Sample Tests* | ICML 2022, PMLR 162, 9845-9880 | Online classifier two-sample test for covariate shift in a stream | Covariate shift (labels not used); FPR bound under their online scheme | FPR bound for online discriminator | Unlabeled covariates | None | Not implemented (discrepancy baseline; MMD used instead) | Distributional detector; says nothing about harm | ABSTRACT-ONLY |
| 14 | Ahmed, Rahaman, Roy, Alam, *The dashboard says "perfect"* | Frontiers in AI 9, 8 Oct 2026, doi 10.3389/frai.2026.1928858 | Audit of label-free monitoring and TTA on CIC-IDS2017/2018 in both directions, 16 variants | No labels from target year; three seeds; ATC, agreement, Mondrian conformal abstention | Propositions 1-2 (confidence-threshold blindness; agreement blindness under correlated collapse); no sequential guarantees | Label-free | No formal cost model | Scope comparator only (`label_free_temporal_audit_prior_work.md`) | Failure analysis of label-free predictive monitors; no anytime validity, no paired cost. Relevant to ShiftLab because disagreement gating inherits the correlated-collapse blind spot (Prop. 2) | PARTIAL (summary of 100k of 114k chars; text not hand-read) |
| 15 | Karampatziakis, Mineiro, Ramdas, off-policy confidence sequences | ICML 2021 (arXiv 2102.09540) | Time-uniform CS for contextual-bandit policy value; gated deployment | Valid importance weights, predictable logging | CS validity | Bandit feedback | Gated deployment, no cost model | Not a comparator in Q1 | Policy-value estimand under bandit feedback; closest to "incumbent vs candidate with action-dependent outcomes" | ABSTRACT-ONLY here (downloaded; DISCERN cites it as closest mechanism) |
| 16 | Prinster et al., Conformal Policy Control | ICML 2026, PMLR 306 | Safe reference policy regulates new policy | Bounded loss, calibration | Finite-sample risk control | Calibration data | Risk tolerance | None | Q2/Q3 comparator, not a monitor | ABSTRACT-ONLY here |
| 17 | Zhou et al. (arXiv 2605.07002) | 2026 | Adaptive subgroup auditing with anytime guarantees | n/a | n/a | n/a | n/a | Repo audit `novelty_audit.md` reads it | Relevant to stratified monitor, not re-verified | UNVERIFIED (not accessed by me) |
| 18 | Zheng, Wiberg, Zhu, *RADAR: Regret-based Assessment of Decision Adequacy and Risk* (title: *Deciding When to Decide: Testing Operational Suboptimality Under Distributional Shift*) | arXiv 2608.29465 v1, 29 Aug 2026; no venue listed (template looks AAAI-style) | Test whether the incumbent optimized decision's optimality gap under the new distribution exceeds tolerance; infers latent preferences by inverse optimization; two-sample and sequential changepoint tests | Known objective form, unknown preference parameter; regularity Assumptions D.1-D.7, local inverse-stability D.6, conditional CLT D.7 | Asymptotic level and power (Thms 3.2-3.3); sequential extension with window-level asymptotic validity (Assumption B.1). **Not anytime-valid, not finite-sample** | Full samples from both regimes | Switching cost enters via a tolerance calibration only | None | Decision-relevance of shift is established as a goal. Estimand is regret to the re-optimized decision, not a frozen reference policy; no selective labels | PARTIAL (abstract, intro, Thm 3.2/3.3 statements, Algorithm 1) |

Note on row 18: the repo cites "RADAR" without a reference. I found no other 2025-2026 monitoring paper by that name that is relevant (a 2024 IoT concept-drift framework with the same acronym is unrelated). If the repo meant a different paper, mark RADAR "not identified".

### 3. Cluster verdict

**Question: could a knowledgeable reviewer obtain ShiftLab's Paper 1 results (paired-cost gated monitoring with published betting engines) by combining two existing algorithms without a substantive new insight?**

**Yes, for the results as currently implemented and measured.** Specifically:

1. **Estimand and null.** The eventwise conditional bounded-mean null on a paired cost, after an affine map, is Timans et al. (UAI 2025) on z_t = deployed-minus-reference cost. The paired risk-difference estimand itself is DISCERN's delta (Eq. 2). So the target is covered by Timans plus DISCERN, and the repo's own replay found no adjusted advantage over official GRAPA under full feedback.
2. **Selective labels.** Gating on disagreement, HT-weighting with a predictable routing probability, and an anytime-valid CS or e-process is DISCERN (Lemma 3, Thms 4-5), which is itself assembled from Karampatziakis et al. 2021 and Xu et al. 2024. Replacing its empirical-Bernstein CS with a betting engine is the combination "DISCERN gating + Xu/PPE betting" or "DISCERN gating + Timans GRAPA". The repo's own regime map (R2, R3) already predicts a tie with "gated HT + adaptive bets", and the stated mechanisms M5 (gating) and M6 (engine) are labeled not-ours.
3. **Proxy correction.** PPE gives the proxy-corrected e-value under selective labels with positivity floor; the repo's paired-cost PPE arm is a direct transfer.
4. **Detection/stratification.** SR/CUSUM horizon e-detectors are Shin-Ramdas-Rinaldo; per-stratum betting is a union-bound or average over Chugg-style games.

So the two-algorithm composition "DISCERN-style gating + (Timans GRAPA or Xu/PPE betting)" reproduces the current Paper 1 pipeline. Without a theorem or regime where this composition provably fails, I would expect a reviewer to say yes.

**What could still be a substantive insight (not established by anything I read):**
- A null stronger than DISCERN's weighted-average target under drift: DISCERN states its unrestarted CS miscovers a moving running-average target (6.4% smooth drift, 15.9% adversarial bursts per its Table 2) and only repairs with windowing. An eventwise conditional-mean null with HT gating is valid under drift by construction (Timans-style), but that is a short argument, not yet a contribution. Needs a proof that Lemma-3-type unbiasedness holds under the repo's filtration with adaptive gating.
- Identification when outcomes are action-dependent. DISCERN's support identity needs Assumption 1 (same prediction implies same loss), and PPE audit says paired cost is identified only if the label reveals both action costs. Real bandit-style or selective-outcome feedback (only the chosen action's reward observed) is outside DISCERN, Timans, PPE, and Xu. This is the only gap that is a different feedback contract rather than a different engine; nothing I read solves paired pi_t vs pi_ref there except the off-policy confidence-sequence line (Karampatziakis et al.), which needs valid importance weights.
- Delayed or out-of-order labels with gating: Podkopaev-Ramdas covers delayed batches for predictive risk; DISCERN does not treat delay. The combination is still likely routine.
- A reviewer should be told plainly that rows 8, 6 and 7 cover the three ingredients, and that DISCERN is a single-author arXiv v1 (not peer reviewed, July 2026), so its validity claims are not independently vetted. I read its Lemma 3 and Thm 4 statements only; proofs and the experimental results are unchecked.

### 4. Related 2025-2026 papers not cited in the repo (grep over docs, papers, references)

| Paper | id / venue | Relevance | Verification |
|---|---|---|---|
| Zheng, Wiberg, Zhu, RADAR (*Deciding When to Decide*) | arXiv 2608.29465, Aug 2026 | Decision-adequacy shift test; asymptotic, regret-to-reoptimized estimand | PARTIAL |
| Lamaakal et al., *Drift-to-Action Controllers: Budgeted Interventions with Online Risk Certificates* | arXiv 2603.08578, CAO Workshop at ICLR 2026 | Combines active delayed-label queries in a window, an anytime-valid upper bound on windowed predictive risk (uniform sampling within the window required, Thm 1), and cost-aware action selection with budgets and cooldowns. Overlaps Paper 3's "monitoring plus cost-aware intervention" framing. Appendix D CS construction not read; the "anytime-valid across windows" claim is the authors' | PARTIAL |
| Dwivedi & Kurmi, *E-FairDrift* | ICML 2026 Hypothesis Testing Workshop poster (OpenReview ssSX2oud7D) | Subgroup e-processes, e-BH, inverse-audited e-processes under sparse labels; overlaps the stratified monitor (WP2) | ABSTRACT-ONLY |
| Shawn, *PACE: Anytime-Valid Acceptance Tests for Self-Evolving Agents* | arXiv 2606.08106, Jun 2026 | Paired incumbent-vs-candidate betting e-process on discordant cases as a commit gate. The repo cites it in `comparator_applicability_audit_v1.md` and `sota_fidelity_matrix.md` (so not uncited), but note it is single-author arXiv and sits next to DISCERN | ABSTRACT-ONLY |
| Kotawala, *Resolution Diagnostics for Paired LLM Evaluation* | arXiv 2605.30315, ICML 2026 Hypothesis Testing Workshop | Paired-Bernoulli mixture e-process for model comparison; low direct relevance | ABSTRACT-ONLY |
| Li, *Who Drifted: the System or the Judge?* | arXiv 2606.15474, Jun 2026 | Betting e-processes with a human anchor set at a steady interleave; relevant to label-budget and attribution framing | ABSTRACT-ONLY |
| Oda, *What Changed? Drift Detection with Real, Virtual, and Incomparable Diagnosis* | arXiv 2609.27865, Aug 2026 | Typed drift alarms, betting e-process variant; low relevance to paired harm | ABSTRACT-ONLY |
| Hou, Bidkhori, Banerjee 2412.20207 and Lubenia & Banerjee 2509.14186 | arXiv, Dec 2024 and Sep 2025 | The repo lists them for G0 but I could confirm only their abstracts (cost-constrained experiment design for QCD) | ABSTRACT-ONLY |
| Musgrove et al. (2023) | cited inside DISCERN as prior discordant-pair labeling work | Prior adjudication-saving evidence without a sequential guarantee; not fetched | UNVERIFIED |

Also uncited and worth noting: a Pith AI review page for PPRM (see section 1 item 6) and the search-surfaced D3M disagreement-based monitor (not fetched; UNVERIFIED).

### 5. Consequences for the novelty matrix

- Mark Paper 1's "gated paired-cost monitoring with published engines" as **already covered by composition** of Timans + DISCERN (+ Xu/PPE). Narrow any claim to the items in section 3, each of which still needs a proof or an experiment against the composed incumbent.
- Add DISCERN to `docs/closest_prior_work.md` and `papers/shiftguard_unified/novelty_audit.md` (the repo mentions it in protocol and supplement files but not in the two main novelty tables I read).
- Fix the Jang title, Amoukou venue and DE-CuSum id.
- Do not claim comparison to RADAR or Drift2Act beyond scope; neither shares the estimand or an exact feedback contract.
- Limits of this check: Podkopaev (full), DISCERN (full excluding lower-bound proofs); all others are statement-level reads. Chugg, Xu, Shin and PPE were not read proof by proof. No code was run.

# Appendix B. Certification cluster (Q2) (subagent matrix; identities in Section 3 lead-checked, others subagent-checked)

## B1: Q2 certification of a replacement policy / incumbent-challenger switching (prior-art verification)

Verified 2026-10-28. Method: repo records read first (docs/closest_prior_work.md, papers/shiftguard_unified/{novelty_audit, sota_fidelity_matrix, comparator_applicability_audit_v1, comparator_scope_decision_v1, decision_costed_shift_prior_work_audit_v1, challenger_switching_fidelity_audit, certification_exponent_fidelity_audit, opi_applicability_audit_v1, mope_obd_applicability_audit, opi_mope_matched_protocol_v1}.md). Then primary pages (arXiv/PMLR) and, where the PDF text could be extracted with pdftotext, the actual text. Extracted texts are in scratchpad/txt/. Verification level is my own: FULL = read the setting, assumptions and theorem statements relevant here; PARTIAL = read abstract, setting and key sections but not every theorem or proof; ABSTRACT-ONLY = abstract and bibliographic page only. No novelty judgment below rests on an ABSTRACT-ONLY item alone.

Common frame for the "Remaining gap" column. The target is the certified net benefit of a selected replacement under shift, with multiple adaptive candidates, delayed feedback, switching costs, and non-persistent improvement. "Gap" means what the paper does not provide for that target.

### 1. Per-paper table

#### 1.1 Off-Policy Confidence Sequences (OCS / MOPE)
- Identity: Karampatziakis, Mineiro, Ramdas. ICML 2021, PMLR 139:5301-5310 (arXiv 2102.09540). Identity confirmed on the PMLR page and the arXiv PDF.
- Exact problem: time-uniform confidence sequences (CS) for contextual-bandit off-policy value V(pi); Section 5.3 "Gated Deployment" gives a CS for V(pi) - V(h). The candidate pi is staged while the incumbent h collects data. pi replaces h when the lower CS crosses 0, and is discarded when the upper CS crosses 0 (Theorem 4).
- Assumptions: "The contextual bandit data is iid. The policy pi is absolutely continuous with respect to behavior policy h" (reproducibility checklist). Rewards in [0,1], bounded importance weights (wmax) for the betting construction. The staged policy is fixed in advance.
- Guarantees: coverage uniformly over time, valid at arbitrary stopping times, nonasymptotic and nonparametric.
- Feedback contract: logged bandit feedback. The incumbent is the logger, so V(h) = E[r]. Propensities are known.
- Intervention costs: none modelled. Safety is argued as "no regret from deploying a worse pi".
- ShiftLab comparator: YES, with the official code. Pinned MOPE (n17s/mope, commit a4b8584...) is run unmodified in the registered IID matched comparison (opi_mope_matched_protocol_v1.md, src/shiftlab/dive/open_bandit_mope.py, certification_exponent_one_step.py harness). One exploratory OBD replay ended with an empty confidence set (mope_obd_applicability_audit.md).
- Remaining gap: single fixed candidate. IID, so no shift. No candidate selection, no delay, no switching cost, no statement about post-switch performance. The CS is on the historical value, not on the future.
- Verification level: FULL (setting, Thm 4, gated section and checklist read in PDF text).
- Quote: none needed.

#### 1.2 Anytime-valid off-policy inference for contextual bandits
- Identity: Waudby-Smith, Wu, Ramdas, Karampatziakis, Mineiro. arXiv 2210.10768 (v3, 15 Aug 2024). The repo cites the ACM/IMS J. Data Science 2024 version (doi 10.1145/3643693). I did not check the journal page.
- Exact problem: CS for OPE quantities when the logging policy is predictable and may change, and contexts may be dependent or drifting. Targets include time-varying mean rewards and the reward CDF.
- Assumptions: the repo audit records that the target policy is predictable and absolutely continuous w.r.t. the logger, that contexts and rewards are exogenous (not driven by past actions), and that the estimand is the running average of conditional policy values. The abstract confirms that dependent contexts, drifting contexts and changing loggers are allowed, and that bounded importance weights are not required.
- Guarantees: CS valid at arbitrary stopping times.
- Feedback contract: logged bandit, known propensities.
- Intervention costs: none.
- ShiftLab comparator: NO direct implementation found in src/shiftlab/dive. It is cited as the closer OBD reference in mope_obd_applicability_audit.md.
- Remaining gap: the running-average estimand is a historical average, not a forward-looking net benefit, and there is no switching or selection logic. It handles drift in the observed record, but does not address whether the improvement persists after a switch.
- Verification level: ABSTRACT-ONLY by my own reading (abstract page). The repo audit documents a primary-source reading, which I did not independently re-read. Marked PARTIAL only through that secondary record.

#### 1.3 High Confidence Policy Improvement (HCPI) and Seldonian variants
- Identity: Thomas, Theocharous, Ghavamzadeh. ICML 2015, PMLR 37:2380-2388. Confirmed on the PMLR page and the PDF.
- Exact problem: batch RL; return a policy only if its performance exceeds a user-set lower bound rho- with probability at least 1-delta, otherwise "No Solution Found". An incremental variant (DAEDALUS) repeats this.
- Assumptions: MDP/POMDP with stationarity ("we must assume that the future will somehow reflect the past"). Trajectories from known behavior policies. Importance-sampling HCOPE bounds (concentration inequality; t-test and BCa variants are only "semi-safe").
- Guarantees: per-iteration safety, P(returned policy has rho < rho-) <= delta. The paper states that selecting and testing on the same data causes multiple-comparisons error, and avoids it by splitting data into Dtrain (candidate search) and Dtest (one safety test). The guarantee over many iterations needs a further correction (their text: it applies "over multiple iterations").
- Feedback contract: logged trajectories from known behavior policies, a batch or incrementally growing set.
- Intervention costs: none. Safety threshold only.
- ShiftLab comparator: NO (excluded for data reasons, comparator_applicability_audit_v1.md). The sample-split pattern is the repo's "fixed sample split" baseline and the structural template of Target-Scout (sota_fidelity_matrix.md line 35-37).
- Remaining gap: stationarity assumed. No shift, no delay, no switching cost, no anytime-valid stopping. The split-then-test pattern for one adaptive candidate per round is established prior art, so it is not a ShiftLab novelty.
- Verification level: PARTIAL (setting, split design, incremental scheme read; theorem proofs not read).
- Seldonian variants (Thomas et al., Science 2019, "Preventing undesirable behavior of intelligent machines"): UNVERIFIED. I did not fetch it. I know it generalizes the candidate-selection plus safety-test template to arbitrary user-defined constraints. The repo does not cite it. Treat that as a gap in the repo's citations to verify.

#### 1.4 Conformal Policy Control (CPC)
- Identity: Prinster, Fannjiang, Park, Cho, Liu, Saria, Stanton. ICML 2026, PMLR 306:99772-99824. Confirmed on the PMLR page and the PDF.
- Exact problem: use a safe reference policy pi_0 as a regulator. Conformal calibration on pi_0's data chooses a bound on the likelihood ratio pi_t/pi_0 so that the optimized policy pi_t respects a declared risk tolerance. This is a sequential or multi-round setting with a feedback-loop covariate shift (the agent's own deviation).
- Assumptions: Assumption 1, a safe initial policy with controlled risk. Assumption 2, access to each optimized policy. Theorem 4.6: bounded losses [0,B], mutual absolute continuity, existence of the control parameter, and relative replace-one stability of the estimator. Policy likelihoods are computable in closed form. The Discussion says the guarantees "depend on the stability of the context distribution" and that, if it shifts, recalibration may be needed.
- Guarantees: finite-sample (expected loss under the deployed policy <= target risk + a stability term). It is a risk-control guarantee on the deployed policy, not a certified net improvement.
- Feedback contract: outcomes from the safe policy (or chosen-action feedback). Known densities.
- Intervention costs: none. The policy is interpolated toward pi_0 to limit risk.
- ShiftLab comparator: NO. Excluded for task mismatch (comparator_applicability_audit_v1.md). Mandatory scope comparison only.
- Remaining gap: controls the risk of the deployed interpolation, with no certificate that the candidate beats the incumbent and no promotion decision. Context-distribution shift is flagged as a limitation. No delay, no switching cost.
- Verification level: PARTIAL (setting, assumptions, Theorem 4.6 and Discussion read; appendix proofs not read).

#### 1.5 Multiple-policy High-confidence Policy Evaluation
- Identity: Dann, Ghavamzadeh, Marinov. AISTATS 2023, PMLR 206:9470-9487. Confirmed.
- Exact problem: estimate returns of K given target policies to accuracy epsilon with high confidence, using as few online samples as possible. Samples are reused across policies via an "expected disagreement" overlap measure and a coupled roll-out strategy.
- Assumptions: tabular finite-horizon layered MDP, deterministic rewards in [0,H]. The main result holds under a sampling-oracle assumption that generalizes a generative model, and a pre-processing phase replaces the oracle when no generative model exists.
- Guarantees: (epsilon, delta) PAC estimates for all K policies, with sample complexity scaling with overlap instead of K. It is a fixed-accuracy design, not time-uniform.
- Feedback contract: the algorithm controls data collection (on-policy rollouts). It is not logged-bandit feedback.
- Intervention costs: none.
- ShiftLab comparator: NO. Scope comparator only.
- Remaining gap: fixed policy set, a stationary MDP, no promotion rule, no shift, no costs.
- Verification level: PARTIAL (abstract, setting and introduction read; proofs not read).

#### 1.6 MOPE
Not a separate paper. In the repo "MOPE" is the code name of the OCS gated-deployment method (n17s/mope repository), see 1.1. The repo identifies it so in mope_obd_applicability_audit.md and opi_mope_matched_protocol_v1.md. No other citation exists.

#### 1.7 OPI (Anytime-valid Optimal Policy Identification)
- Identity: Molitor, arXiv 2606.17515v1, 16 Jun 2026, stat.ME, 15 pages. Not peer reviewed at the version checked.
- Exact problem: given a finite policy class Pi and logged contextual-bandit data from an externally determined predictable logger, maintain a candidate set S_t that retains every optimal policy uniformly over time, and stop when the unique optimum is separated.
- Assumptions (my reading of the introduction plus the repo audit): rewards in [0,1], known predictable logger propensities, target-policy support, time-invariant policy values nu(pi), predictable reward model. Union bound over the class, alpha/(2m) per one-sided endpoint is the correct allocation (the repo audit documents that the author code uses alpha/m and fits the reward model on the whole stream; I did not verify this independently).
- Guarantees: P(Pi* subset S_t for all t) >= 1-alpha. Sample complexity scales with log|Pi| and the minimal gap.
- Feedback contract: logged bandit, known propensities, analyst cannot steer collection.
- Intervention costs: none.
- ShiftLab comparator: YES. src/shiftlab/dive/anytime_policy_identification.py (independent implementation, alpha/(2m)) and the matched IID benchmark opi_mope_matched_protocol_v1.md.
- Remaining gap: stationary values by assumption, so no shift or non-persistence. Fixed finite class (not adaptively generated candidates). Identification of the best policy, not promotion against an incumbent with a switching cost. No delay and no label acquisition.
- Verification level: PARTIAL (abstract, introduction and contributions read in PDF text; theorem proofs and the stationarity statement taken from the repo audit).

#### 1.8 Wang 2026, "The Certification Exponent"
- Identity: Rui Wang, arXiv 2610.24345v1, submitted 17 Oct 2026, 62 pages, "Submitted to JMLR". Preprint.
- Exact problem: sequential certification that a fixed target policy improves on a known, possibly history-dependent logging policy from logged episodes. Defines K* as the minimum KL divergence from the observed logged law to an admissible null.
- Assumptions (abstract plus repo audit of the source): known logger, bounded rewards, logged-tree environment class, coverage conditions. Soundness is uniform over the class.
- Guarantees: any delta-sound certifier needs E[tau] >= log(1/delta)/K*. A plug-in Kelly certifier matches this asymptotically as delta tends to 0 when 0 < K* < infinity. Coverage trichotomy: impossible, finite rate, or constant. A cushion certifier for large trees.
- Feedback contract: logged episodes, known propensities.
- Intervention costs: none.
- ShiftLab comparator: YES, adaptation. A labeled context-free two-arm binary specialization in src/shiftlab/dive/certification_exponent_one_step.py (nine tests pass). The matched run had not produced artifacts at the time of the repo record. The paper's full multi-step algorithm is not reproduced and no author code exists (certification_exponent_fidelity_audit.md).
- Remaining gap: single fixed candidate, stationary logged law, no delay, no cost, no shift. It is an instance-optimal sample-complexity result for the certifying step alone.
- Verification level: PARTIAL (abstract and bibliographic page read by me; theorem content from the repo audit, which read the LaTeX source).

#### 1.9 Digalakis et al., "The Challenger"
- Identity: Digalakis Jr, Perignon, Saurin, Sentenac. arXiv 2512.18390 (v1 20 Dec 2025, v2 16 Jul 2026). Preprint, CC BY 4.0.
- Exact problem: incumbent versus a challenger trained on newly available features. The challenger improves with accumulated full-feature data (power-law learning curve). At each epoch choose switch, discard or continue.
- Assumptions: bounded gain in {-1,1}, ERM training, finite VC dimension for the meta-regret theorem (Theorem 2), power-law learning curve, decision on the prescribed T^(2/3) time scale. The value model includes data cost, a one-time switching cost and discounted per-sample gains net of operating cost.
- Guarantees: meta-regret O(T^(2/3) sqrt(log T)) against a full-foresight oracle. GSE uses a Hoeffding bound plus a union bound over finite decision epochs (text line ~800). The paper itself notes that this "does not imply that GSE satisfies the meta-regret conditions". It is a finite-epoch bound, not anytime-valid.
- Feedback contract: full-feedback (paired challenger vs incumbent gain on the same validation samples, shared labels), repeated random splits.
- Intervention costs: YES, explicit data, retraining and a one-time switching cost, and irreversible action ("once the challenger is adopted or discarded the process ends").
- ShiftLab comparator: NO (primary-source audited, not reproduced; challenger_switching_fidelity_audit.md). Scope comparator.
- Remaining gap: a single challenger and a single irreversible switch, with improvement driven by a learning curve and no population shift. Experiments mention a distribution-shift sensitivity, but no theory for it. Costed switching with a statistical certificate is therefore established prior art in the single-challenger setting.
- Verification level: FULL on the parts needed (setting, switching-cost model, Theorem 2 conditions, GSE bound read in PDF text).

#### 1.10 AnyRank
- Identity: Badithela et al., "AnyRank: Reliable Anytime Policy Ranking via Sequential Testing", arXiv 2610.14603 (v1 10 Oct 2026, v2 16 Oct 2026), CoRL 2026.
- Exact problem: rank multiple policies from costly hardware trials, with partial rankings available at any time, graphical FWER allocation across pairwise tests, and adaptive allocation of trials to hard-to-separate pairs. Optional priors (experts, held-out tests, simulator or world-model rollouts) improve efficiency without breaking validity.
- Assumptions: i.i.d. tasks drawn from D, one shared bounded real-valued metric, a fixed policy set for the ranking family.
- Guarantees: anytime-valid FWER <= alpha for the ranking family.
- Feedback contract: the evaluator controls which policy is run on a fresh task (active trial allocation). It is not logged feedback.
- Intervention costs: only a trial-count cost in the allocation objective E[T] + lambda E[F].
- ShiftLab comparator: YES, adaptation. scripts/reproduce_anyrank_shiftguard.py and verify_anyrank_shiftguard_pilot.py, protocol v2. v1 results are invalid (protocol v1). The star-shaped pilot is not a full ranking reproduction, and the repo labels AnyRank a scope comparator, not a required mean-cost baseline.
- Remaining gap: i.i.d. stationary trials, a distributional-ordering target (not mean net benefit), no switching cost, no delay, no shift.
- Verification level: PARTIAL (abstract, setup and contributions read).

#### 1.11 Conformal Policy Selection (CPS)
- Identity: Cao, Gao, Saar-Tsechansky, Yin, arXiv 2610.22930v1, 16 Oct 2026, stat.ME.
- Exact problem: choose which individuals should receive a fixed target policy, by testing whether each individual's outcome under the policy exceeds a threshold. Weighted conformal p-values correct for behavior-to-target shift, then selection plus pruning.
- Assumptions: i.i.d. calibration tuples from P, test tuples i.i.d. from Q (covariate and treatment shift through the policy ratio), propensity or outcome model correct (double robustness in the asymptotic result).
- Guarantees: finite-sample FDR control among selected units. Doubly robust asymptotic guarantee.
- Feedback contract: logged observational data with known or estimated propensities. Per-unit selective deployment, not a whole-policy promotion.
- Intervention costs: none.
- ShiftLab comparator: NO (scope comparator, different estimand).
- Remaining gap: unit-level FDR, not net benefit of a whole replacement. Not sequential, no delay, no cost.
- Verification level: PARTIAL (abstract, introduction and setup read).

#### 1.12 CABAI
- Identity: Kanarios, Zhang, Ying, "Cost Aware Best Arm Identification", arXiv 2402.16710 (v1 Feb 2024, v2 Jul 2024). The repo cites the RLC 2024 / RLJ version. I did not check the RLJ page.
- Exact problem: identify the arm with highest reward while minimizing expected testing cost. Testing and implementation phases have different objectives (cost for testing, reward for implementation). Lower bound plus CTAS (asymptotically optimal) and the simpler Chernoff Overlap heuristic.
- Assumptions: stochastic arms with per-arm cost distributions, fixed-confidence identification (read in the introduction; I did not read the lower-bound proof).
- Guarantees: asymptotic optimality of CTAS, and optimality of CO in simplified two-arm models.
- Feedback contract: the learner chooses which arm to sample (active), reward and cost both observed. Not logged.
- Intervention costs: per-sample experiment costs. No switching cost in the implementation phase.
- ShiftLab comparator: NO (repo: do not adapt to common-label data; comparator_scope_decision_v1.md).
- Remaining gap: stationary arms, no shift, no delayed feedback, no incumbent safety constraint.
- Verification level: PARTIAL.

#### 1.13 Anytime-valid A/B testing / always-valid inference used by the repo for promotion
- The repo's promotion machinery rests on betting-based confidence sequences and e-processes (Waudby-Smith and Ramdas; Howard et al. 2021; the Lindon reference in docs/theory_targets.md and docs/delayed_event_prefix_validity.md), and on prediction-powered e-values (Csillag et al., ICML 2025) and active anytime-valid risk-controlling prediction sets (Xu et al., arXiv 2406.10490, cited in docs/xu_active_betting_paper_to_code_audit.md and novelty_audit.md). Johari et al. "Always valid inference" (Operations Research 2022) is not cited in the repo files I searched (the string "always-valid" appears only in challenger_switching_fidelity_audit.md).
- Verification level: UNVERIFIED by me for Johari et al. and the Howard et al. CS line. Xu et al.: I did not fetch it. The repo has a paper-to-code audit (docs/xu_active_betting_paper_to_code_audit.md) that I did not read here. This cluster is background for the certificate engine, not a competing result.

#### 1.14 Target-Scout's closest prior work (as recorded)
- The repo records it as "project-specific", a scout split to select a candidate and context, then certification on disjoint held-out feedback with hard query budgets (sota_fidelity_matrix.md line 37). Its closest priors are the Thomas 2015 train/test split pattern (1.3), generic sample-split-then-test with multiplicity control, and fixed-confidence best-arm identification (CABAI 1.12, OPI 1.7, AnyRank 1.10). The repo's own wording: it "is not a new general-purpose guarantee". Its confirmation is synthetic IID, with +8.76 and +6.67 expected net gain over fixed split and pooled rank (97.5% intervals above the +1 margin).
- Not independently verified: the classical selective-inference and sample-splitting literature (not fetched). Verification level: UNVERIFIED for classical sources, PARTIAL for the repo's own framing.

### 2. Could a knowledgeable reviewer obtain "statistically controlled policy promotion with adaptive information acquisition and switching costs" by combining two existing algorithms?

Reasoned answer: YES for the generic combination, NO for the specific target in the Q2 charter. Two compositions work:

1. Karampatziakis et al. (OCS gated CS, or its time-varying extension by Waudby-Smith et al.) as the certificate, plus Thomas et al. 2015 style train/test splitting to generate a candidate. Add multiplicity by alpha-allocation over a finite candidate bank, as OPI (Molitor) or AnyRank do, or by the budget-splitting rule that Zhang, Wu and Qian (arXiv 2609.13714) state for finite candidate libraries.
2. Switching cost is then a one-line change. Certify a lower confidence bound on (gain minus amortized switching cost) above zero, which is the economic decision of Digalakis et al. with the CS replacing their finite-epoch Hoeffding bound. Adaptive information acquisition (which labels to buy) is available from prediction-powered e-values (Csillag) and active anytime-valid RCPS (Xu et al.), which the repo already uses.

A reviewer would see that each of the four features is already covered by a named paper, and that gluing them requires only predictability bookkeeping and alpha-spending. I therefore expect a reviewer to class a generic "controlled promotion with query budgets and a switching-cost margin" as a combination, consistent with the repo's own NO-GO for a new unified algorithm (decision_costed_shift_prior_work_audit_v1.md section 3).

What the combination does NOT give, and the single most specific remaining gap:

> A certificate whose target is the future net benefit of the selected replacement over a post-switch horizon when the improvement need not persist. Every certificate above (OCS, Waudby-Smith, OPI, Wang, HCPI, 2609.13714) bounds a historical or running-average value under stationarity or exogenous drift. Digalakis does extrapolate to the future, but only through a power-law learning-curve model and without shift. The missing piece is a valid bridge from evidence collected before the switch, under delayed and adaptively acquired feedback, to a guarantee on realized net gain after the switch net of the switching cost, together with an explicit persistence (or change-rate) condition and a stated failure mode when the improvement decays.

This is a research target, not an established result, and I did not find a paper that does it in my bounded search (not exhaustive). Adaptive acquisition itself is not the gap, since the active/PPI e-process literature covers it. Multiple candidates are not the gap either, since the multiplicity literature above covers a prespecified or alpha-spent bank. Candidates generated adaptively from the same data stream that is also used for certification (data-dependent bank growth) is a secondary open question, partly addressed by the split designs.

### 3. Closely related 2025-2026 papers the repo does NOT cite (grep of docs/ and papers/ by arXiv id)

| Paper | What it addresses | Relevance | Verification |
|---|---|---|---|
| Zhang, Wu, Qian, "Certifying Model Upgrades with Slice-Wise Non-Regression and Incumbent Fallback", arXiv 2609.13714, 12 Sep 2026 | Separates candidate search from independent paired evaluation, returns the exact incumbent if certification fails, finite-sample guarantees for one frozen candidate, a finite library, and a prespecified order, using intersection-union and Learn-then-Test. Notes that a no-detected-harm gate releases harmful candidates 99.7% of the time in one 32-slice setting. | Very close to the Q2 gate (promote or keep incumbent, multiplicity over a candidate library). It is fixed-sample and stationary. | PARTIAL (arXiv abstract page only, so it is close to ABSTRACT-ONLY; no theorem read) |
| Zhou, Li, Zhu, "Safe Meta-Policy Design with Risk Control", arXiv 2610.10393, 7 Oct 2026 | Plans an update schedule (path in a DAG, dynamic programming) that maximizes expected cumulative value subject to an expected budget on updates that perform worse than the policies they replace. | Very close to "multiple sequential candidate updates with an incumbent-harm budget". It is an expected-count constraint, asymptotic, offline planning from historical trajectories. | ABSTRACT-ONLY (the page lacked full text; the claims about switching cost are from the abstract and are unconfirmed) |
| Khosravi, Huo, "Conformal Selective Acting", arXiv 2605.20270, 18 May 2026 | Per-round anytime e-process wrapper for online-updated (RLVR) LLM streams, predictable updates, pathwise validity under adversarial shift settings. | Relevant on anytime-valid deployment gating of an updating model under shift. Target is selective risk, not promotion net benefit. | ABSTRACT-ONLY |
| Fernandez-Barrios et al., "Candidate Comparability Before Promotion", arXiv 2609.04388, 3 Sep 2026 | Empirical study: a drift alarm does not justify promoting a retrained challenger, and promotion conclusions depend on challenger construction and evidence. | Empirical support for keeping alarms and promotion separate, and a likely citation for the ShiftLab framing. Not a guarantee. | ABSTRACT-ONLY |
| Joshi, Wang, Hassani, Dobriban, "Risk-Controlled Post-Processing of Decision Policies", arXiv 2605.06479, 7 May 2026 | Choose a policy that agrees with a baseline as much as possible subject to a chance constraint on loss, threshold structure, calibration-based finite-sample method under exchangeability. | Related to CPC and the safe-fallback layer. Not sequential, not a promotion test. | ABSTRACT-ONLY |
| Bongers, Oliehoek, Spaan (2026), anytime-valid OPE for RL, mentioned in a CWI news piece | Extends anytime-valid OPE to reinforcement learning. | Only a secondhand mention; contents unconfirmed. | UNVERIFIED |

Already in the repo (so not listed above): PACE 2606.08106 and the "Pay Only for Disagreement" certified no-regression paper 2609.17560 (cited in the monitor protocols under docs/, not in comparator_applicability_audit_v1.md beyond PACE; cross-reference before claiming it is uncited), Xu et al. 2406.10490, Timans et al. (PMLR 286), WATCH, PPRM, Molitor OPI, Wang, Digalakis, AnyRank, CPS, CABAI.

### 4. Limits of this verification
- The search was bounded: three web searches plus the repo grep. "Not found" does not mean absent.
- Four of the five 2025-2026 additions are abstract-only. They must be read in full before any prior-art conclusion about them is written into the novelty matrix.
- The Waudby-Smith and Wang theorem-level assumptions rest on the repo's earlier primary-source audits, not on my re-read.
- Seldonian (Science 2019), Johari et al. (always-valid inference), and the classical selective-inference sources were not fetched.

# Appendix C. Intervention and allocation cluster (Q3) (subagent matrix; identities in Section 3 lead-checked, others subagent-checked)

## B1: Prior-art verification, Q3 intervention and resource allocation under shift

Date: 2026-10-28. Repo read-only. Method: repo records first, then primary pages and PDFs (text extracted with pdftotext into the scratchpad folder `b1/`). WebFetch summarises pages with a small model, so theorem statements below were checked against extracted PDF text where I have it; where I only have a summary, the level is lowered. Search of the repo for uncited papers covered `docs/*.md` and `papers/shiftguard_unified/*.md` only (an earlier recursive grep timed out on OneDrive); code and other folders were not scanned for citations.

Verification levels: FULL = full text read for problem, assumptions, theorem statements; PARTIAL = main text read, proofs/appendices or parts unread; ABSTRACT-ONLY = abstract/landing page or search summary; UNVERIFIED = search snippet only.

### 1. Per-paper records

#### 1.1 Regol, Schwinn, Sprague, Coates, Markovich, "When to retrain a machine learning model" (UPF)
- Year/Venue: ICML 2025, PMLR 267:51369-51404; arXiv:2505.14903. Identity confirmed on PMLR page.
- Exact problem: finite-horizon choice of which model index to use at each of T online steps; cost C = eN(1 + alpha * sum_t pe_{r(t),t}) with fixed relative retraining cost alpha (paper's "cost-to-performance ratio"), bounded loss, per-model per-period expected performance pe_{i,j}.
- Assumptions: sequence of fully labelled datasets D_t (offline window w=7, online T=8 in main runs); alpha, e, N known; decision at t uses only information before t (offline data plus past online data); performance forecast from low-data regression; paper itself says "primarily suited to gradual changes" (abrupt shifts open).
- Guarantees: none for the decision rule (empirical only). Proposition 3.1 (retrain-count bound) exists; repo's audit gives a counterexample (T=1, L=1, alpha=0.25); I re-read the statement in the PDF and it matches the repo's transcription. Not used by the rule.
- Feedback contract: per-period labels fully observed after the period; no delay, no selective labels (the repo adds delay assumptions on top).
- Intervention costs: single scalar retrain cost alpha in loss units; only {retrain, keep}; no query, no fallback, no promotion gate.
- Implemented in ShiftLab: adaptation (independent implementation, not code reproduction; `src/shiftlab/dive/upf_retraining.py`, `scripts/evaluate_upf_eia_frontier.py`). Repo records UPF does not dominate simple baselines on EIA.
- Remaining gap (a): no harm objective (predictive loss only), no paired reference policy, no anytime-valid false-promotion control, no query/fallback action. (b): none; labels are free and complete.
- Verification: FULL (PDF text read: setting, objective, Prop 3.1, limitations). Algorithm details beyond that rely on the repo's own implementation audit.

#### 1.2 Piaseczny, Shisher, Wang, Brinton, RCCDA
- Year/Venue: NeurIPS 2025 main track (identity confirmed on NeurIPS page); arXiv:2505.24149 (v3, Jan 2026; repo's arXiv id not recorded, this is it).
- Problem: choose binary update pi(t) each step under a time-averaged resource constraint (1/T) sum lambda(t) pi(t) <= lambda_bar; objective bounds time-averaged gradient norm under drift.
- Assumptions: L-smooth loss (A1), unbiased bounded-variance gradients (A2), KL drift between consecutive distributions <= delta (A3), loss in [0,B] (A4). Causal policy using only past inference losses.
- Guarantees: Thm 5.1 (gradient-norm bound), Cor 5.2 (O(sqrt(delta)) + O(sigma^2) floor), Thm 5.3 (constraint violation O(1/sqrt(T)) under a zero-error gain estimator). Authors name the estimator error as the main limitation; Thm 5.3 does not cover the implemented P/D estimator (repo notes this correctly in `rccda.py`).
- Feedback contract: an inference-batch loss each step (an unbiased estimate of f(theta_{t-1}, D_t)); labels apparently available immediately (not stated explicitly). No delay.
- Costs: abstract per-update cost lambda(t), constant in experiments; one action (update or not). Virtual queue Q(t+1) = max{0, Q + lambda pi - lambda_bar}; update iff V*G_hat >= cost threshold.
- Implemented: adaptation (`src/shiftlab/dive/rccda.py`, `scripts/evaluate_rccda_eia_frontier.py`).
- Gap (a): single action; resource constraint is on update count, not on harm; no test or error control. (b): the constraint is on model updates, not labels; labels are assumed free. A Lyapunov queue is a pacing mechanism that a reviewer will map directly onto label pacing (see Section 3b).
- Verification: PARTIAL (arXiv v3 HTML, first ~100k of ~223k chars incl. Thms 5.1-5.3 statements; proofs and later appendices unread).

#### 1.3 Mahadevan and Mathioudakis, CARA (cost-effective retraining)
- Year/Venue: arXiv:2310.04216, v1 Oct 2023; arXiv page lists no peer-reviewed venue (the repo labels it "paper", fine).
- Problem: choose Keep/Retrain per batch to minimise sum of staleness cost (loss of old model on current queries, relative to loss on the training batch) plus retraining cost, via an upper-triangular cost matrix C[t', t].
- Assumptions: offline phase with full history to tune parameters; online phase sequential; relative retraining cost known; batch stream.
- Guarantees: none stated; empirical closeness to a retrospective DP oracle.
- Feedback: labels for each batch available to compute staleness; two-phase offline/online protocol.
- Costs: staleness cost and retrain cost in common units; variants Cara-T (threshold), Cara-CT (cumulative), Cara-P (periodic), plus Markov, ADWIN, DDM, NR baselines.
- Implemented: adaptation (`src/shiftlab/dive/cara_retraining.py`, `scripts/evaluate_cara_eia_frontier.py`, `verify_cara_eia_frontier.py`).
- Gap (a): only keep/retrain; staleness is loss-based. (b): none.
- Verification: FULL (arXiv PDF text read: preliminaries, cost matrix, problem statement, variants, baselines).

#### 1.4 Löfström, "Conformal Repair on a Budget: An Empirical Protocol for Retraining Decisions"
- Year/Venue: COPA 2026, PMLR 329:576-591 (identity confirmed). Single author.
- Problem: after a conformal coverage failure under shift, pick the first sufficient action in a fixed order No-op < Scale < Recal < Intercept < Retrain subject to empirical coverage >= target and width <= budget.
- Assumptions: labelled shifted data (disjoint update, repair-calibration, selection, test splits); Gaussian linear regression in main experiments; order is "a fixed intervention convention rather than a measured runtime or monetary cost".
- Guarantees: none. Paper says the finite-sample selection is empirical; a formal guarantee would need select-then-recalibrate on a fresh sample. Population width calculation only.
- Feedback: all repair data labelled, no delay (delayed labels listed as a limitation); one chronological forecasting experiment.
- Costs: ordinal only.
- Implemented: no (repo's novelty_audit says so; I found no code reference).
- Gap (a): ordinal cost-ordered menu is exactly the "least costly sufficient action" pattern; target is coverage/width, not paired harm; no anytime validity. (b): none.
- Verification: FULL (16-page PDF text; contributions, selection rule, cost-order, limitations read).

#### 1.5 Rahman and Tabassum, "Modeling and Controlling Deployment Reliability under Temporal Distribution Shift"
- Year/Venue: arXiv:2604.02351v1, 1 Mar 2026; preprint, no venue.
- Problem: nine annual windows on LendingClub (1.35M loans); reliability state from AUC and ECE; policies static / periodic / rolling / DTRC (drift + reliability thresholds choose retrain, recalibrate, or both) / MORC (threshold sweep with a cost-volatility knee).
- Assumptions: outcome labels for each window available at decision; thresholds from candidate sets between year partitions and empirical percentiles; knee chosen retrospectively over the same horizon (confirmed in text lines on MORC grid: 69 configurations).
- Guarantees: none. Feedback: annual labelled batches, no delay (paper flags censoring as a limitation). Costs: no-op 0, recalibrate 1, retrain 5, both 6 (per the repo; matches the paper's action-cost table as quoted there).
- Implemented: no (scope comparator only, per repo's own audit).
- Gap (a): same keep/recalibrate/retrain pattern; no harm estimand or validity. (b): none.
- Verification: PARTIAL (arXiv PDF text read for policy definitions and thresholds; the repo audit's claim of internal threshold-provenance inconsistency was not independently re-derived).

#### 1.6 Zliobaite, Bifet, Holmes, Pfahringer, "Active Learning on Data Streams" (MOA)
- Year/Venue: 2011, Workshop on Applications of Pattern Analysis, PMLR 17:48-55 (the repo cites the PMLR page; the title in the PDF is "MOA Concept Drift Active Learning Strategies for Streaming Data").
- Problem: decide per instance whether to query its label under budget B (fraction of stream), while adapting to drift.
- Assumptions: instance-incremental stream, label returned right after prediction (no delay); no theory.
- Guarantees: none. Strategies: random (query w.p. B), fixed uncertainty, variable uncertainty, randomised variable uncertainty, split. States design goals "balance the labeling budget over time" and notice changes anywhere in the space.
- Costs: labels only; no action menu.
- Implemented: no (cited only; the repo's active-query code, e.g. `src/shiftlab/dive/query.py`, is different).
- Gap (a): no intervention. (b): heuristic pacing with uncertainty thresholds, no validity, no bound-inflation analysis, no harm monitor.
- Verification: FULL (8-page PDF).

#### 1.7 Korycki and Krawczyk, "Mining Drifting Data Streams on a Budget: Combining Active Learning with Self-Labeling"
- arXiv:2112.11019 (Dec 2021), preprint listing; seven hybrid active/self-labelling strategies, wrapper framework, tight-budget regime, labels assumed delayed-or-limited (intro notes that most work assumes immediate labels).
- Guarantees: none stated. Costs: label budget only.
- Implemented: no. Gap (a)/(b): no test, no harm, no validity; pseudo-labelling would break the repo's feedback contract anyway.
- Verification: PARTIAL (abstract, introduction, labelling-constraints section; strategy algorithms not read).

#### 1.8 Prinster et al., "Conformal Policy Control" (CPC), fallback aspect
- ICML 2026, PMLR 306:99772-99824 (identity confirmed; authors Prinster, Fannjiang, Park, Cho, Liu, Saria, Stanton). Code: samuelstanton/conformal-policy-control.
- Problem: deploy an optimised, untested policy while bounding deviation from a known-safe reference policy so a user-declared risk tolerance holds.
- Assumptions (Thm 4.6): E_0[L_0] <= alpha (safe policy risk), losses in [0,B], mutual absolute continuity, a relative replace-one stability condition on the chosen likelihood-ratio threshold. Authors state the guarantee depends on a stable context distribution ("if the context distribution begins to shift then recalibration may be necessary") and on computable policy likelihoods.
- Guarantee: marginal bound E[L(t)] <= alpha + a stability slack term; applies to the chosen policy, not just each candidate.
- Feedback: online, outcomes from deployed (mixed) policy; no label delay modelling.
- Costs: none (risk tolerance as constraint). The "fallback" is soft mixing with the reference under a likelihood-ratio cap, not a rollback after detected shift.
- Implemented: no (listed as a comparator in sota_fidelity_matrix; no CPC module found).
- Gap (a): no choice among retrain/query/continue, no test-time distribution change, no cost. (b): none.
- Verification: PARTIAL (Thm 4.6 statement and discussion read; proofs, appendix not).

#### 1.9 ADWIN and DDM (baselines)
- Appear in CARA's baseline set and in the repo as River adaptations (`scripts/evaluate_eia_drift_detectors.py`: yes/adaptation on EIA, per sota matrix). Primary papers (Bifet and Gavalda 2007; Gama et al. 2004) not fetched.
- Gap: error-rate change detectors; trigger retrain; no harm or cost objective.
- Verification: UNVERIFIED for the primary papers; CARA's text confirms their role as retrain-on-detection baselines.

#### 1.10 Selective labels and delay in sequential testing
- Lakkaraju, Kleinberg, Leskovec, Ludwig, Mullainathan, "The Selective Labels Problem", KDD 2017, pp. 275-284: outcome observed only for cases the decision-maker acted on; proposes "contraction" evaluation exploiting decision-maker heterogeneity. Verification: ABSTRACT-ONLY (search summary). Relevance: evaluation of a model against a human policy under selective labels; not sequential, not anytime-valid.
- Targeted searches (2024-2026) for anytime-valid inference with delayed or missing-not-at-random feedback found no paper combining these: closest are Podkopaev and Ramdas (delayed batches; already in repo), Xu, Karampatziakis, Mineiro, NeurIPS 2024 "Active, anytime-valid risk controlling prediction sets" (label-budgeted e-process; repo has formula-level transfer in `xu_active_betting.py`; ABSTRACT-ONLY here), Li et al. "Active Sequential Two-Sample Testing" (TMLR 2024; ABSTRACT-ONLY), Drift2Act (below). A negative search is not proof of absence; this is a limited search.

#### 1.11 Banerjee and Veeravalli, DE-Shiryaev and DE-CuSum
- 1105.1361 "Data-Efficient Quickest Change Detection with On-Off Observation Control" (Sequential Analysis 31(1), 2012; Bayesian, two-threshold DE-Shiryaev; ITA 2011 preliminary); 1211.3729 "Data-Efficient Quickest Change Detection in Minimax Settings" (submitted to IEEE Trans. IT; DE-CuSum). Identities confirmed on arXiv. The repo's DE-CuSum reference is the latter.
- Problem: stopping time plus on/off observation policy minimising detection delay s.t. false-alarm (ARL or probability) and fraction-of-time observed before change.
- Assumptions: i.i.d. pre/post-change densities f0, f1 known (non-Bayesian: unknown constant change point); skipped samples update the statistic by drift. Guarantee: asymptotic optimality as false-alarm rate to 0.
- Feedback/costs: observation cost per sample; no labels, no intervention menu. Statistic moves up during skips, which the repo correctly notes cannot be imported into an e-process (`docs/data_efficient_edetector_prescreen_protocol.md`).
- Implemented: no (the repo's M4 pre-screen is a predictable-intensity e-detector, not DE-CuSum; it failed its gates: 55% vs 100% detection).
- Gap (a): none. (b): DE-CuSum is the incumbent for "observation spending over time" but it treats a rate constraint with likelihood models and ARL; it does not treat a hard finite label count, an unknown burst count, bounded-outcome e-processes, or Horvitz-Thompson bound inflation (5/q). So the ledger's phrase that DE-CuSum "already addresses" M8 is true for the on/off sensing idea, not for the specific exhaustion-versus-inflation trade-off. Treat as conceptual prior art, not a theorem-level precedent.
- Verification: PARTIAL (both abstracts; 1211.3729 intro/problem setup; algorithm and theorem proofs not read; novelty_audit records an earlier independent pass over the descendants).

#### 1.12 Drift2Act (not in repo): Lamaakal et al., "Drift-to-Action Controllers: Budgeted Interventions with Online Risk Certificates"
- arXiv:2603.08578v1, 9 Mar 2026, no venue. (Section 4 below.) It is the most important finding of this pass.

### 2. Repo claims checked against sources
- closest_prior_work.md entries for RCCDA, Zliobaite, Korycki, CPC: consistent with what I read. RCCDA row understates that Thm 5.3 needs a zero-error estimator.
- novelty_audit.md on Löfström: accurate (first-sufficient-action in a prespecified order, empirical, no anytime guarantee). One addition: the paper itself says a formal guarantee requires select-then-recalibrate on a fresh sample, i.e. selection is separated from calibration, which is the same issue a certified action rule faces.
- upf_primary_paper_audit.md: Prop 3.1 text matches; the repo's setting (alpha, T=1) is a valid instance of the statement as quoted.
- algorithm_search_exit_ledger.md M8: see 1.11; also Section 3b below shows the "paced q collapses in bursts" problem is a standard queue/pacing design question with a Lyapunov precedent (RCCDA), so the M8 novelty gap is narrower than "no one has done this".

### 3. Verdicts on combination

#### (a) Costed continue/query/promote/retrain/fallback rule under a decision-harm objective
Answer: YES for a rule without end-to-end validity; NOT SHOWN for a rule whose guarantee covers the action choice.
- Drift2Act already has the action menu with costs: no-op 0, recalibrate 0.2, TTA 1.0, query labels 0.05*k, retrain 12.0 with cooldown, rollback 1.5 with cooldown, abstain/handoff 0.3, chosen by utility U(a) = gain - lambda*cost - gamma*violation, gated by an anytime-style risk certificate on sampled labels with a label-delay model and a total label ceiling B_lab. It lacks: a paired reference-policy harm (the certificate is predictive risk R_t <= tau), a promotion gate for a separately trained candidate, validity of the certificate across model-changing interventions (its theorem needs i.i.d. bounded losses from the current window; the text I read does not say what happens when windows mix pre- and post-intervention losses; this is my inference from the text, not a statement of the authors), and a guarantee on the action choice itself (gains G(d,a) are calibrated offline; the paper's own limitations say the certificate "gates" rather than certifies actions).
- Adding Regol or CARA (cost-aware retrain trigger) and CPC (safe-reference mixing) and Conformal Policy Selection/OPE confidence sequences (already in repo) to a harm monitor is a routine composition; a reviewer will say the menu and the costed rule are obtained by combining Drift2Act or UPF/CARA with Karampatziakis-style policy gates.
- What survives: (i) the estimand (paired excess cost against a predictable frozen/selected reference under stated feedback), (ii) a validity argument that survives intervention and selection with delayed, selectively observed labels. These are theory/estimand contributions, not "a rule". The repo's own status (sota matrix, novelty audit: NO-GO for a new unified algorithm) is consistent with this. A contribution claim should be framed on (ii) only if a proof exists; none exists in the repo today.

#### (b) Burst-robust allocation of a finite label budget for a gated anytime-valid monitor
Answer: YES for a heuristic pacer; NO for a rule with a proved or pre-screened advantage, but that is an open gap, not an established one.
- Components a reviewer would assemble: gated sampling from DISCERN-style disagreement (credited in ledger), a predictable query propensity q_t with Horvitz-Thompson or PPI e-factors (Xu et al.; repo `xu_active_betting.py`), and pacing from a queue/windowed controller (RCCDA virtual queue; Zliobaite/Castellani budget redistribution after drift; DE-CuSum on/off control). The repo's `DisagreementPacer` (200-event window, clipped to [0.10, 1]) is already this combination, and its documented failure under bursts (paced q falls, bound 5/q inflates; fixed q exhausts) is the problem M8 names.
- Nothing I found proves a pacing rule that is optimal or minimax for the exhaustion-versus-inflation trade-off in a gated e-process; Drift2Act's pacing is tiered (k_low=8, k_high=32, k_max=64) with no analysis, Castellani et al. redistribute after a detected drift (abstract only), DE-CuSum has asymptotics under known likelihoods. So the gap is real but narrow; it needs a derivation plus a pre-screen. Caution from the ledger's own evidence: M4 (evidence-following intensity) failed its pre-screen, so adaptive intensity is not automatically a win.
- Honest framing: a reviewer who sees "pace q to the remaining budget" will call it a known pacing heuristic. Only a theorem (e.g. a growth-rate or regret statement under bursty disagreement with hard budget) or a robust-design result makes it more than composition.

### 4. Drift2Act detail (not cited by the repo)
- Identity: arXiv:2603.08578v1, Lamaakal, Yahyati, El Makkaoui, Ouahbi, Maleh, 9 Mar 2026; cs.LG; no venue.
- Problem: pick interventions under label, compute and latency budgets and cooldowns while keeping risk certified under tau.
- Sensing: MMD^2, entropy shift, ECE drift; HMM-style belief over drift type fit on synthetic episodes.
- Certificate (Thm 1/A.2): uniform random label sampling from the recent window, i.i.d. losses in [0,1], rad(n,delta) = sqrt((1/2n) log(pi^2 n^2 / 6 delta)), union bound over sample sizes giving P(for all t, R_t <= U_t) >= 1-delta; gate U_t <= tau.
- Label delay: effective n shrinks while labels are pending; validity needs sampling not to depend on unobserved labels; no explicit delay-dependent bound (D.7).
- Limitations stated: validity requires uniform label sampling; fixed window N; small action space.
- Evaluation: WILDS Camelyon17, DomainNet, synthetic CIFAR drift; single-valued table, no variance visible; controller+certificate reports 0, 1, 0 violations at costs 24.6, 29.8, 21.2 versus adapt-always 3, 6, 4 violations at 58.0, 64.0, 52.0 (as shown in the page). Internal inconsistencies noted on the page: window definition and the Viol term differ between text and algorithm, and rollback/retrain priority is unstated.
- Verification: PARTIAL (two page fetches covering ~all 193k chars, summarised; proofs not independently checked; "not visible" items flagged by the reader are not asserted here).
- Implication: for both (a) and (b) it is the closest 2026 competitor and must be added to the novelty matrix and, if feasible, to the baselines (its certificate is a uniform-sampling confidence sequence on unpaired risk; ShiftLab's gated HT e-process should be compared on the same label budget).

### 5. Related 2025-2026 papers NOT cited in the searched repo files

| Paper | Date / venue | Why close | Verification |
|---|---|---|---|
| Lamaakal et al., Drift2Act, arXiv:2603.08578 | Mar 2026, preprint | Costed action menu + label-budgeted risk certificate + rollback/abstain | PARTIAL |
| Dasari, "When to Retrain: An Empirical Study of Retraining Policies for Streaming ML Under Concept Drift, Budget, and Latency Constraints", arXiv:2608.19488 | Aug 2026, preprint | Periodic vs error-threshold vs ADWIN under budget and deployment latency; 3,933 runs; finds incremental updating matters more than the trigger (with immediate labels) | ABSTRACT-ONLY |
| Katz, "Cost-sensitive retraining via posterior learning debt", arXiv:2604.06438 | Apr-May 2026, preprint | Retrain when expected predictive regret exceeds retraining cost; compares tuned CUSUM; synthetic Bayesian only; no guarantees | ABSTRACT-ONLY |
| Solozobov, "Evidence Sufficiency Under Delayed Ground Truth", arXiv:2604.15740 | Apr 2026, preprint | Label-latency "blind period" governance gate; proxy indicators; no formal guarantees | ABSTRACT-ONLY |
| E-SHIFT, "Anytime-valid sequential hypothesis testing for distribution shift in streaming learning systems", arXiv:2510.03839 | Oct 2025 | e-process shift detection (sentinel baseline, not harm) | UNVERIFIED (search snippet) |
| Choi, "Anytime-Valid Confirmation of Label-Shift Corrections", arXiv:2606.14028 | Jun 2026 | Sequential confirmation of a candidate correction with scarce target labels: close to promotion under sparse labels | UNVERIFIED (search snippet) |
| "Maintaining IoT Device Identification under Concept Drift via Budget-Aware Traffic Labeling", arXiv:2608.15465 | Aug 2026 | Burst-aware per-window labelling-rate scaling by running maximum non-conformity; no validity | UNVERIFIED |
| Castellani, Schmitt, Hammer, "Stream-based Active Learning with Verification Latency in Non-stationary Environments", arXiv:2204.06822 (ICANN 2022) | 2022 (older than window) | Delayed labels + drift-triggered dynamic budget redistribution; direct precedent for time-varying budget | ABSTRACT-ONLY |

Not new to the repo and not counted above: Hou, Bidkhori, Banerjee arXiv:2412.20207 (cited in novelty_audit; abstract confirms on/off control with a least-favourable post-change family), PPRM (cited), WATCH (cited). Xu et al. NeurIPS 2024 and Li et al. TMLR 2024 are implemented/mentioned in code and should be checked for citation in the manuscript bibliography (not verified here).

### 6. Recommendations to the matrix
1. Add Drift2Act as a Q3 row; reclassify the "costed action menu with certificate" idea as prior art (heuristic) and restrict any claim to the paired-harm estimand and intervention-robust validity.
2. Change the M8 ledger wording from "DE-CuSum literature ... already address it" to "DE-CuSum addresses rate-constrained sensing under known likelihoods; hard-budget burst allocation for e-processes has no theorem-level precedent found in a limited search".
3. Do not cite Löfström's order as a "cost"; it is explicitly ordinal. Do not present RCCDA Thm 5.3 as covering the practical estimator.
4. Items still needing full reads before any novelty statement: Drift2Act proofs (App. D), E-SHIFT, Choi 2026, Dasari 2026, Xu 2024 active RCPS, DE-CuSum algorithm and proofs, ADWIN/DDM primaries.

---

# Part 2 (B2): full reads, systematic search and cross-model novelty verdict

**Recorded 2026-10-28, loop tick 4.**

**Sources:**
- Three Sonnet subagents:
  - full reads of the four closest papers (Appendix D);
  - a search for G1 and G3 plus the PPRM check (Appendix E);
  - a search for G2 and G4 (Appendix F).
- Lead verification of the load-bearing items.
- **An independent cross-model review by Codex (`gpt-6.1-sol`, reasoning effort xhigh),** run
  read-only from `NOVELTY_DOSSIER_B2.md` following ARIS novelty-check Phase C. This is the first
  independent review in this refinement. Its full answer is Appendix G.

**Search limits** (from the subagents):
- WebSearch and WebFetch only. OpenReview, PMLR and Google Scholar were not queried directly.
- The UAI, ICML and COLT 2026 accepted-paper lists were not enumerated.
- Coverage of statistics journals is weak.

Codex searched independently and added nine papers (Section B2.4). "Not found" below is a search
conclusion, not proof of absence.

## B2.1 Gap verdicts

| Gap | Closest prior art after B2 | Two-algorithm test | ARIS verdict (Codex) | Lead reading |
|---|---|---|---|---|
| **G1.** Paired policy-harm monitoring under bandit feedback with delay | Waudby-Smith et al. arXiv 2210.10768 §3.1/§3.3 Prop. 4 (paired policy-value difference e-process with adaptive logging, running-average null; **primary PDF read**). Lindon & Kallus ICML 2026 (anytime-valid inference with treatment-dependent delayed outcomes, calendar-time cumulative reward; **lead-fetched**). Xu–Karampatziakis–Mineiro active risk control. | **Yes** for ordinary selective feedback (Waudby-Smith plus Xu). A harm margin is only a threshold shift. | PROCEED WITH CAUTION | **Reject as an anchor.** A section at most, unless a sharp result for informative, asynchronous feedback is specified. That has not been done. |
| **G2.** Certificate on future post-switch net benefit when improvement need not persist | Chandak et al. NeurIPS 2020 (SPIN; asymptotic bootstrap coverage); Shimizu et al. arXiv 2506.20417 (OPFV; future-value estimation; Codex-added); Chandak et al. NeurIPS 2022 (OPEN; action-dependent non-stationarity; Codex-added); Liu et al. 2023; Zhang–Wu–Qian arXiv 2609.13714 (fixed-n paired non-regression with fallback; **full main text**); Zhou–Li–Zhu arXiv 2610.10393 (offline schedule; plug-in or i.i.d.); DISCERN §5.7 (no fixed Δ under drift; **lead-verified**) | **Yes** for the natural form: a sequential difference CS, minus a known drift allowance, minus the switching cost | PROCEED WITH CAUTION | **Narrow.** It survives only as a *prospective-certifiability* theorem: conditions under which future benefit can be certified, with an attaining procedure and a lower bound. Without a transport restriction, two environments with identical histories can have opposite futures, so **the persistence assumption carries the result.** |
| **G3.** Evidence validity through the intervention it triggers | DISCERN Prop. 13 (promotion sequences; i.i.d. stream independent of the deployed model; **full**); Guo arXiv 2610.01751 (Evidence-Gated Research: moving incumbent, adoption-dependent future proposals, persistent e-values; **lead-fetched**); Feng et al. AISTATS 2024 (monitoring under performativity; asymptotic CUSUM; Codex-added); Valdrighi et al. arXiv 2610.08272 (performative selective labels; Codex-added); Drift2Act (per-window design-based certificates; **partial-high**) | **Yes** for the validity bookkeeping (PPE or Csillag plus DISCERN accounting). **No** for causal effects of the intervention on later states, populations or label availability. | PROCEED WITH CAUTION | **Reject the generic claim.** A causal version (a finite-sample regime comparison under intervention-induced feedback, with a randomized or sequentially exchangeable design) is possible but its estimand is not fixed. Pre-switch wealth cannot be reused as evidence about a different post-switch policy claim. |
| **G4.** Minimax allocation of a hard finite label budget for a gated anytime-valid monitor under unknown bursts | Cheng et al. arXiv 2609.29140 (hard-budget lower bounds covering adaptive policies, for a fixed evaluation cohort; **lead-fetched**); Efroni et al. ICML 2021 (Confidence-Budget Matching; hard query budgets under adversity; Codex-added); Zhang & Cheung NeurIPS 2024 (piecewise-stationary bandits with knapsacks, inventory reservation; Codex-added); Geng–Bayraktar–Lai IEEE TIT 2014 (Bayesian quickest detection with sampling-right constraints; Codex-added); Bayraktar–Kravitz; Xu et al. (expected budget, stationary); DE-CuSum; Sfyraki & Wang ICLR 2026 (uniform near-optimal when stationary) | **No established reduction** for the detection/budget frontier. The closest pair is Xu active betting plus Zhang–Cheung reservation, but cumulative reward and threshold crossing differ. **Caveat:** a theorem about log-wealth regret alone may reduce to constrained online learning, and that reduction must be checked first. | **PROCEED** | **Strongest survivor**, and outside Paper 1. The worst objection: the minimax problem either makes uniform sampling optimal or becomes an existing knapsack problem. It needs a fixed horizon or exposure model, an admissible burst class, request-time budget accounting, and a same-information comparator. A finite budget cannot support uniform detection of arbitrarily late, short harm. |

**Ranking (Codex, lead concurs):** G4 > G2 > G3 > G1.

**NO-GO reversal: none** (Codex and lead agree). The 2026-10-26 unified-algorithm NO-GO and the
2026-10-27 Paper 1 NO-GO both stand. G4 is a distinct Paper 3 theory question. G2 is a narrower
Paper 2 theory question. Neither revives a rejected algorithm.

## B2.2 Full reads of the four closest papers (Appendix D)

| Paper | Estimand | Validity scope | Gaps closed |
|---|---|---|---|
| Drift2Act (arXiv 2603.08578) | Unpaired absolute window risk of the deployed model | Thm A.2: Hoeffding plus union bound per window under uniform audit sampling; design-based; silent after intervention; action choice heuristic; no CIs reported | None. **Venue:** a subagent-reported ICLR 2026 workshop venue is unconfirmed (arXiv lists none); treat it as a preprint. |
| Zhang–Wu–Qian (arXiv 2609.13714) | Paired, per-slice, fixed-n | Finite-sample; selection by dev/cert split or a finite library with Bonferroni or a fixed order; no anytime validity, adaptive labels, delay or drift | None. **Direct prior art for any Paper 2 offline certificate.** |
| Zhou–Li–Zhu (arXiv 2610.10393) | Expected number of unsafe updates in an offline schedule | Plug-in in the main text; the appendix needs i.i.d. historical trajectories; assumes deployment does not affect data | None; the nearest G2 relative |
| DISCERN (arXiv 2609.17560) | Paired; disagreement-only labels | Anytime-valid under predictable routing. Thms 7–8 give matching ρ²/ε² label bounds; Thm 9 a Θ(1/ρ) saving; Prop. 13 unbounded promotions from one budget. **i.i.d., deployment-independent stream.** Under drift it covers only a traffic-weighted average, and windowed restarts miscover under bursts (§5.7, lead-verified). | G3 only narrowly. §5.7 and Table 2 disagree on what the drift CS guarantees; unresolved. |

## B2.3 PPRM scaling allegation: resolved

**There is no implementation error.** The paper's main-text eq. (21) mixes the radius on the
rescaled [0,1] loss with an unnormalized mean, which is a notation ambiguity. Appendix A.4
eqs. (45)–(49) are consistent. ShiftLab follows the consistent form: `src/shiftlab/dive/eprocess.py`
rescales by `1 + 2*max_reliance` before updating (line 490) and maps the lower bound back
(lines 446–452). The normalization was **lead-verified in code**. The code also matches eqs. (18),
(23) and (27) in `pprm_risk_monitor.py` (subagent-verified). The unverified AI-review page was not
used as evidence.

## B2.4 Prior art added by Codex (identity status)

| Paper | Identity | Relevance |
|---|---|---|
| Lindon & Kallus, "Design-Based Anytime-Valid Inference for Randomized Experiments with Delayed Outcomes and Staggered Entry", ICML 2026, PMLR 306:75193–75210 | **Lead-fetched** | G1 delay: event-time filtration makes per-arm IPW errors martingales |
| Guo, "Evidence-Gated Research: Statistically Controlled Model Adoption in Adaptive Search", arXiv 2610.01751 (2026-10-01) | **Lead-fetched** | G3: moving-incumbent adoption control with persistent e-values |
| Shimizu et al., "Off-Policy Evaluation and Learning for the Future under Non-Stationarity", arXiv 2506.20417 | Codex-reported | G2 future-value estimation |
| Chandak et al., "Off-Policy Evaluation for Action-Dependent Non-Stationary Environments", NeurIPS 2022 | Codex-reported | G2/G3 action-dependent non-stationarity |
| Feng et al., "Monitoring machine learning-based risk prediction algorithms in the presence of performativity", AISTATS 2024, PMLR 238:919–927 | Codex-reported | G3 identification under treatment selection |
| Efroni et al., "Confidence-Budget Matching for Sequential Budgeted Learning", ICML 2021, PMLR 139:2937–2947 | Codex-reported | G4 hard query budgets |
| Geng, Bayraktar & Lai, "Bayesian Quickest Change-Point Detection With Sampling Right Constraints", IEEE TIT 60(10), 2014 | Codex-reported | G4 finite-observation-budget detection |
| Zhang & Cheung, "Piecewise-Stationary Bandits with Knapsacks", NeurIPS 2024 | Codex-reported | G4 inventory reservation |
| Valdrighi, Valera & Raimundo, "Performative Prediction with Selective Labels", arXiv 2610.08272 | Codex-reported | G3 performative selective labels |

**Identity update (tick 5, Haiku fetch of primary pages):** Shimizu 2025, Chandak 2022, Feng 2024, Efroni 2021, Zhang & Cheung 2024 and Valdrighi 2026 MATCH on title and authors. Valdrighi carries an author-stated NeurIPS 2026 acceptance. The Zhang & Cheung author string came back garbled; confirm it before citing. Geng–Bayraktar–Lai is PARTIAL: arXiv 1309.5396 matches on title and authors, but the IEEE TIT 60(10) 2014 venue is unconfirmed.

## B2.5 Consequences for Phase C

1. **Q1 and Paper 1:** closed for method novelty. They feed the benchmark manuscript.
2. **The `q1_fallback` finding** (inventory §2.1) is still uncovered by the literature as an
   empirical observation, but it is a benchmark finding, not a method.
3. **G4** is the only gap that clears both the ARIS check and the stricter two-algorithm test.
   Before Phase C ranks it, check the log-wealth-regret reduction.
4. **G2** is viable only as a sharp prospective-certifiability theorem, and its persistence
   assumption is the main risk.
5. **Phase C** must therefore weigh at least:
   - path A, a benchmark paper absorbing Paper 1, the gating correction, the fallback dominance and
     the pacing finding;
   - G4 as a Paper 3 theory paper;
   - G2 as a Paper 2 theory paper;
   - G3 or causal monitoring as a path D option.

   It must be honest that none has yet shown a provable, non-vacuous theorem.

# Appendix D. Full reads of the four closest papers (subagent; lead-verified only where B2 says so)

## B2 full-text prior-art reads (novelty audit)

Method: PDFs from arxiv.org/pdf/<id> downloaded to scratchpad\pdfs\ and converted with pdftotext. Greek letters and some inequality symbols were lost in extraction, so I reconstructed them from context and the proofs; I flag the places where that matters. Repo untouched. "Not stated" means I did not find it in the sections read.

Gap key: G1 paired-harm monitoring under action-dependent (bandit) feedback; G2 persistence-aware certificate on future post-switch net benefit; G3 validity of evidence through the intervention it triggers; G4 theorem for finite-label-budget allocation under unknown disagreement bursts.

---

### 1. Lamaakal et al., Drift2Act, arXiv 2603.08578 (ICLR 2026 CAO workshop paper, 8 pages plus appendix)

**Read: PARTIAL-HIGH.** Main text Sections 1-7 in full. Appendix A (setup), B (algorithm), D (all of D.1-D.7, including Lemma A.1, Theorem A.2, Corollary A.3, Theorem A.4) and the baseline table in E. Also E.4-E.5 (episode construction, hyperparameters). Skipped: E.2-E.3 gain-table calibration details, Appendix F extra results.

**(a) Estimand.** Unpaired and absolute. The target is the mean loss of the deployed model over a recent window W_t (N=1024), compared with a fixed threshold tau. It is a historical window average, not a future post-switch value. There is no reference policy and no paired difference. Algorithm 1 lags the window by the label delay d: W_t = {t-d-N+1..t-d}. Section 4.1 defines the window ending at t, which is inconsistent with Algorithm 1. Main-text Theorem 1 also cites "Eq. (18)" for the certificate, which looks like a typo.

**(b) Feedback contract.** Labels are delayed by a fixed d=50 steps in the experiments. Labels are requested by uniform sampling within the window, under a label budget B_lab=3000. A label gives the deployed model's own loss only. Counterfactual losses of a candidate or rollback are not identified. The synthetic gain table G(d,a) is estimated from simulated one-step counterfactual rollouts, which are evaluator-side oracle information. Its use is not a feedback-regime statement.

**(c) Validity.**
- Guarantee: Theorem A.2. With probability at least 1-delta, for all t, R_t <= U_t. The construction is Hoeffding at each n with n-allocation delta_n = 6*delta/(pi^2 n^2), then a union bound over t with delta_t = 6*delta/(pi^2 t^2). Corollary A.3: with that probability, any step with U_t <= tau has R_t <= tau.
- Filtration: F_{t,n} = sigma(z_{1:t}, queried indices and losses). n_t may be data-dependent. Condition A requires uniform random sampling within W_t, independent of unobserved labels.
- The certificate is design-based. It is conditional on the window and its loss vector, and its only randomness is the audit sampling. So it does not need stationarity or i.i.d. data across time.
- Anytime-valid: yes over t and over n, but it is a loose Hoeffding plus union bound, not a martingale or e-process. The first-window cost is large: delta_1 is about 0.61*delta.
- (i) Candidate selection: not applicable. The certificate covers the deployed model only.
- (ii) Adaptive label acquisition: yes, provided sampling inside the window stays uniform. Uniform sampling is the "key condition". Selective or informed routing is excluded.
- (iii) Delayed labels: addressed informally in D.7. Delay only enlarges the radius, and validity holds if request times are predictable. No formal delayed-feedback filtration is given.
- (iv) Intervention changing the model or stream: the bound is on past-window risk of whatever the model's loss L_{t,i} refers to. The paper does not say which theta defines that loss. Formally it survives interventions because it is design-based. But it says nothing about risk after the intervention. The post-action risk "recovery" is only empirical.
- (v) Non-persistence: not addressed.
- The gate guarantees only "no predictions under certified-unsafe conditions", with probability 1-delta. There is no guarantee that any chosen action helps.

**(d) Costs.** Modeled explicitly: per-action costs (Table 2: recalibrate 0.2, TTA 1.0, retrain 12, rollback 1.5, label 0.05 per label, abstain 0.3), cooldowns (r_t=800, r_b=400), and a label budget. The safety gate is certified. Action selection is heuristic: a one-step receding-horizon utility with a belief-weighted gain table, with no optimality or regret theorem. The belief model (HMM over drift types) is fit on synthetic episodes made by the same generators used in evaluation, which is circular. The gain table also comes from that generator.

**(e) Experiments.** Camelyon17 (hospital-ordered), DomainNet (domain-ordered), SyntheticDrift-CIFAR. M=200 episodes, 5 seeds. Baselines: alarm-only, adapt-always TTA, retrain-on-schedule, selective-prediction-only, controller-without-certificate. Table 1 reports no variances or CIs, and no coverage column. The deployed-risk metric switches to selective risk under abstention, so a low violation count V could come partly from abstaining. Table 1 headline: V = 0 against 7-11 for the no-certificate ablation.

**(f) Gaps.**
- G1: leaves open. Unpaired, single deployed model, labels are model-own losses, no bandit feedback.
- G2: leaves open. Window-average past risk only.
- G3: leaves open, with a partial adjacent point. Design-based validity is robust to model changes, but there is no evidence about post-intervention performance and no treatment of the intervention's effect on later evidence.
- G4: leaves open. It gives validity under adaptive label counts plus a heuristic budget rule (raise n_t on drift evidence). It has no allocation theorem, no regret, and no treatment of unknown bursts.
- Relevance to Paper 1: this is a baseline-class "certified absolute-risk gate". It does not touch paired excess cost against a reference policy.

---

### 2. Zhang, Wu, Qian, "Certifying Model Upgrades with Slice-Wise Non-Regression and Incumbent Fallback", arXiv 2609.13714

**Read: FULL main text** (Sections 1-7, all of Table 1-3 and Figures 1-3 descriptions). Appendix A opening only (Hoeffding p-value validity). Appendices B-C (search settings, digits configuration) not read.

**(a) Estimand.** Paired and per-slice. D_s(theta) = q_s(theta) - q_s(theta_0), the difference in expected slice score between candidate and incumbent, evaluated on a fixed certification distribution P_s. It is a static population expectation, with no time index and no future post-switch value. The guarantee is on the release procedure: P(any slice has D_s < -tolerance_s) <= alpha, "unconditional repeated-sampling". The paper explicitly says it does not cover "future distribution shifts".

**(b) Feedback contract.** Full, immediate, offline. Both models are scored on the same independent certification examples; there are no deployed-action effects, no delay and no selectivity. Per-slice i.i.d. examples with a known paired-difference range W_s. The paper itself warns that clustered samples (shared documents, writers) break the i.i.d. assumption.

**(c) Validity.**
- Theorem 1: frozen candidate. Intersection-union test, release only if max_s p_s <= alpha. No K-fold penalty. Standard IUT.
- Theorem 2: finite library with levels alpha_j summing to alpha (Bonferroni or LTT style), or a frozen fixed-sequence order. Both are standard applications.
- Not anytime-valid. It is one fixed-n attempt. The paper says repair after failure "starts a new statistical attempt and requires new data or a predeclared valid sequential design", and that repeated releases are not certified.
- (i) Candidate selection: yes, but only if selection happens on development data (or via Theorem 2). Selecting on the certification data invalidates it (Figure 2: 97.5% false release at J=100 uncorrected).
- (ii) Adaptive label acquisition: not covered. n_s is fixed.
- (iii) Delayed labels: not stated, not covered.
- (iv) Intervention changing the stream: not modeled. Certification is offline and the guarantee ends at release.
- (v) Persistence: not addressed.
- Positive tolerance permits bounded degradation. Utility improvement is not itself certified ("requires an additional condition").

**(d) Costs.** No switching, retraining or label costs. Development evaluation cost is discussed qualitatively and not charged. The decision rule is certified for the safety constraint (non-inferiority IUT with exact incumbent fallback). Utility maximization is a development-split heuristic search (scalar grid, block grid). The fallback is the exact incumbent, so a failed certificate costs nothing in safety.

**(e) Experiments and baselines.** Synthetic binomial gate studies (20000 trials, exact Clopper-Pearson CIs, seed fixed). Gates: point estimate, no-detected-harm, exact IUT, simultaneous exact, Hoeffding IUT. Search inflation: uncorrected reuse, Bonferroni over candidates, fixed sequence, independent dev choice. A constructed 2-block geometry (scalar 21 and 441 versus block 21x21). Public sklearn digits, 5 seeds: every frozen proposal failed the gate and the incumbent was returned in all runs (underpowered, 35-37 examples per class). The follow-up extension reuses the same splits and is descriptive. One headline: no-detected-harm releases a harmful candidate in 99.7% of 32-slice trials, against 2.6% for exact IUT.

**(f) Gaps.**
- G1-G4: none closed. The paper is a clean offline, i.i.d., paired non-inferiority certificate with fallback and selection discipline.
- Direct prior art for Paper 2's offline certificate component: frozen candidate, paired evaluation, incumbent fallback, separating search from certification, IUT versus no-detected-harm. This must be cited and the novelty narrowed. It tests slice non-regression, not net benefit after costs, and says nothing about drift, persistence or label allocation.

---

### 3. Zhou, Li, Zhu, "Safe Meta-Policy Design with Risk Control", arXiv 2610.10393

**Read: PARTIAL-HIGH.** Main text Sections 1-6 in full, except the prose of Exp 2 (lost in extraction, so only the headline gain numbers were visible). Appendix B.3-B.6 (DP correctness, grid resolution, labeling alternative, uncertainty-aware extension including Assumption B.1 and Theorem B.1 summary) and the opening of Appendix C. Not read: C proofs in detail, Appendix D experiments.

**(a) Estimand.** Population value V(pi) of policies, a planning problem. An update is "unsafe" if V(new) < V(incumbent), which is a paired comparison in population value. The constraint is on the expected number of unsafe updates (the paper says it controls "frequency of harmful updates but not their magnitude"). The objective is expected average deployed value over a horizon T. It is an ex-ante expectation over future training data, not a realized-data post-switch certificate.

**(b) Feedback contract.** Potential-outcomes setting with i.i.d. covariates and potential outcomes (Assumption 1); assignments need not be independent. Policy values are estimated on held-out data by AIPW or similar. In the IST experiment treatment was randomized, so both counterfactual policy values are identified by design. The setting is explicitly offline: "deployment decisions do not affect the data-generating process". Full feedback is assumed, with no delay.

**(c) Validity.**
- Main-text Algorithm 1 is a plug-in dynamic program (resource-constrained shortest path), exact for the estimated, gridded problem. The authors state it has no finite-sample guarantee and name that as a limitation.
- Appendix B.6 extension: with Assumption B.1 (i.i.d. historical value vectors independent of the future vector, values in [0,1]) the upper-confidence edge costs give P(at least one unsafe future update) <= epsilon + delta. Its "anytime" refers to the number of historical trajectories N, not to online deployment adaptivity. The appendix says so explicitly.
- Schedules are fixed in advance. No adaptation to the realized stream.
- (i) Selection: not applicable. The schedule is predetermined, the candidate set is the training sequence.
- (ii) Adaptive labels: none.
- (iii) Delayed labels: none.
- (iv) Intervention: excluded by the offline assumption.
- (v) Persistence: Assumption 2 is only improvement in expectation, E[V(pi_t')] >= E[V(pi_t)], and a diffusion model for V.
- Asymptotics (Theorem 1, Corollaries 1-2): regret of order log(T/eps)/T and about T/log(T/eps) updates, under an Itô diffusion assumption. These are reduced-form, not distribution-free.

**(d) Costs.** The update count is endogenous. There is no explicit per-switch, retraining or label cost; unsafe-update probability is the price of switching, and value lost to delay is the objective. The decision rule is exactly optimal for the estimated problem and not an online certificate.

**(e) Experiments.** Synthetic (400 trajectories, T=60 checkpoints, three SNR regimes), Itô phase diagrams (theory versus simulation correlation 0.98-0.99), and International Stroke Trial bootstrap trajectories (500). Baselines: best periodic interval, equal-risk split, earliest-safe threshold. The paper attributes its gains to jointly choosing update timing and per-update risk. All methods share the same estimated rewards and safety costs.

**(f) Gaps.**
- G1: leaves open. Randomized-treatment, offline.
- G2: leaves open. It is the nearest relative (planning future updates under a risk budget) but it is an ex-ante plan from historical trajectories with a diffusion value model, not a data-driven persistence-aware certificate on realized net benefit.
- G3: leaves open. It assumes the feedback loop away.
- G4: leaves open. Nothing on label budgets.
- Relevance: strong prior art against any claim to "schedule updates under an expected-unsafe-update budget", and for count-of-harmful-updates as the risk metric.

---

### 4. Balachandran, DISCERN "Pay Only for Disagreement", arXiv 2609.17560 (JMLR-style, single author)

**Read: FULL for the claims asked.** Sections 1-9 in full, including Theorems 4-9, Corollary 10, Propositions 6, 12-14, Section 5.7 (drift), Section 6 (all tables, drift study), Section 8 limitations. Appendices A and B (all proofs of Lemma 3, Theorems 4, 5, 7, 8, 9, Propositions 12, 13). Not read: Appendix C-F (pre-registration, tolerance censoring, baseline sweep, reproducibility). The CS validity itself is cited, not reproved, from Waudby-Smith and Ramdas 2024.

**(a) Estimand.** Paired. Delta = E[loss(g(X),Y) - loss(f(X),Y)] for candidate g against incumbent f, on an i.i.d. stream from a fixed P. It is a traffic-average, backward-looking population quantity. Under drift the CS is claimed valid for the running weighted average of conditional means (Section 5.7), and a windowed restart gives per-window averages. There is no future post-switch value.

**(b) Feedback contract.** Both models are shadow-scored on all traffic, so the disagreement indicator A_t is free. Assumption 1 requires a prediction-determined loss, so D_t = 0 on agreements. One label gives both models' losses. Labels are requested on disagreements only, with probability pi_t in [pi_min, 1], predictable, and "routing may never consult the incoming label Y_t". Labels are not delayed in the model (delay not stated). The data stream does not depend on f or g's actions: (X_t, Y_t) i.i.d., with no performative feedback, no censoring of outcomes by the deployed action, and no bandit structure. Section 5.6 extends to Lipschitz score-reading losses. Judged or preference losses are outside the theory.

**(c) Validity.**
- Support identity (Lemma 2): Delta = E[D A], |Delta| <= B*rho, where rho = P(disagree).
- Tier 0: CS on A_t. Zero-label Safe(eps) when B * upper(rho) < eps.
- Tier 1: Horvitz-Thompson increments Z_t = A_t * (L_t/pi_t) * D_t with E[Z_t | F_{t-1}] = Delta (Lemma 3), range B/pi_min. Predictable-plug-in empirical-Bernstein CS.
- Theorem 4: with probability at least 1-(delta_0+delta_1), both CSs cover for all t simultaneously, so no false Safe or Regression verdict at any stopping time. Theorem 5: holds for every predictable routing, including an adversarial judge.
- Proofs (B.2) lean on the martingale form of the CS, where the tracked quantity is the predictable conditional mean (constant here). I checked B.1-B.2: the argument is sound for stationary Delta.
- Filtration: F_{t-1} plus X_t, with routing a function of pre-label information only.
- Anytime-valid: yes.
- (i) Candidate selection: one pair (f,g) per audit. Proposition 13 allows each k-th pair to depend on earlier data and verdicts, with fresh traffic per audit and Sum_k (delta_0(k)+delta_1(k)) <= delta_seq. Overlapping traffic is still sound by union bound. Concurrent multi-candidate libraries are not separately treated. Per-slice verdicts use delta/K (Proposition 12).
- (ii) Adaptive label acquisition: yes (any predictable routing and adaptive stopping). No hard budget cap is built into the guarantee; the pi_min floor and label counts are outcomes.
- (iii) Delayed labels: not stated.
- (iv) Intervention changing the deployed model or stream: the sequence of promotions is handled (Proposition 13), but only because the stream is assumed i.i.d. and independent of which model is deployed. Outcome dependence on the deployed model's actions is not covered.
- (v) Non-persistent improvement: not addressed. Safe(eps) certifies the audit-window average. The authors explicitly flag that the unrestarted CS miscovers under drift: 6.4% (smooth) and 15.9% (adversarial bursts), against a nominal 5%. The windowed restart gives 0.0001 and 0.065 in simulation, with no theorem for the windowed variant. There is also a tension I could not resolve. Section 5.7 says the CS is valid for a running weighted average, while the Table 2 caption describes the same experiment as "outside its guarantee". The exact target definition is not stated.

**Theorems 7-9 as stated (Greek symbols reconstructed from proofs).**
- Theorem 7 (upper bound): for Delta <= eps/2 and constant routing pi in [pi_min,1], Tier 1 issues Safe by stream time T* = O(B^2 rho L/(pi eps^2) + B L/(pi_min eps)), and N_lab = O(B^2 rho^2 L/eps^2 + range term). The proof (B.5) is a width calculation: solve radius <= eps/2, then a Chernoff bound on the number of labeled disagreements. Symmetric for regression with Delta >= 2*eps.
- Theorem 8 (lower bound): a two-atom, two-world construction for B=1 and a stated range of rho and eps. Any (eps,delta)-sound procedure that issues Safe w.p. at least 1-delta under P0 must request about rho^2 log(1/(2.4 delta))/(4 eps^2) labels in expectation. It is a lower bound for a stationary, i.i.d., known-structure two-point case. The "matching" claim is at rate level only; the paper says constants are unpinned in the window rho in (eps/2, 2 eps).
- Theorem 9 / Corollary 10: pairing-blind auditors need about rho/eps^2 labels. The ratio to pairing-aware is Theta(1/rho). Remark 11 admits this prices only the capability of shadow-scoring both models.
- Multi-promotion error budget: Proposition 13, delta(k) proportional to k^-2 covers an unbounded sequence, each audit costing only a log(1/delta(k)) factor more. It controls bio-creep family-wise. Alpha-investing adaptive budget is left open.

**(d) Costs.** Label spend is counted and minimized. Shadow-scoring compute is acknowledged as the traded resource but not priced. There are no switching or retraining costs and no promotion cost model. The decision rule (Safe or Regression) is certified; routing and judge use are heuristic accelerators that cannot break validity.

**(e) Experiments and baselines.** Pre-registered. 715 feature-space update pairs across four modalities and eleven update types (6,890 main streams). 70 LoRA fine-tune pairs on Pythia 160M-1.4B (classification only). Miscoverage 0.0002 (main battery) against nominal 0.05; power 0.986; zero false alarms; 56% of benign audits certify with zero labels at eps=1%. Median 327 labels versus 2,906 for uniform labeling in the audited band. Baselines are the author's own sequential adaptations: uniform labeling, PPI-style, active-testing with judge routing (no published method targets the paired delta). Drift study is synthetic only (smooth mixture, adversarial burst).

**(f) Gaps.**
- G1: leaves open. The stream is independent of the deployed action; both models are scored on every input. No bandit or selective-label feedback, so the counterfactual loss of the non-deployed policy is never in doubt.
- G2: leaves open. It certifies an audit-window average. Drift handling is a restart heuristic, with no certificate on post-switch net benefit and no persistence model.
- G3: PARTIAL, narrowly. Proposition 13 keeps evidence valid across an adaptive chain of promotions, but only for a stationary stream that does not respond to which model is deployed.
- G4: leaves open for the stated theorem, with a PARTIAL adjacent result. Validity under any adaptive routing is proven, and the label cost to a verdict is characterized for a stationary known rate. There is no finite-budget allocation theorem and nothing about bursts. Under adversarial bursts it miscovers (15.9%). Slice allocation is left to a uniform 1/K split.
- Relevance: DISCERN is the closest prior art to Papers 1 and 2. It already has paired anytime-valid evidence with adaptive labeling and a promotion-sequence budget. Paper 1 and Paper 2 novelty claims must be framed around the delta that DISCERN excludes: action-dependent feedback, policy-conditional (cost-weighted) excess loss, post-switch persistence, and non-stationarity.

---

### Cross-paper summary table

| Paper | Estimand | Anytime | Selection | Adaptive labels | Delay | Intervention-aware | Persistence | Costs | G1 | G2 | G3 | G4 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 Drift2Act | unpaired window risk of deployed model | yes (union bound) | n/a | uniform sampling only | informal | no (design-based, past only) | no | explicit, gate certified, actions heuristic | open | open | open (adjacent) | open (validity only) |
| 2 Slice non-regression | paired per-slice, static | no (one attempt) | yes, dev split or library | none | none | none | none | none | open | open | open | open |
| 3 Meta-policy | paired population value, ex-ante plan | no (N-anytime only) | n/a | none | none | offline assumption | expectation only | implicit via unsafe-update budget | open | open (nearest) | open | open |
| 4 DISCERN | paired risk diff, running average | yes | one pair per audit, sequence union | yes, predictable routing | not stated | stationary stream only | no (restart heuristic) | labels only | open | open | partial | open (partial adjacent) |

Caveats: extraction lost Greek symbols, so formula details in Theorems 7-8 are reconstructed from proofs and prose. Paper 1 and Paper 4 experiments are self-reported and not independently verified. I did not check the code or artifacts of any paper.

# Appendix E. G1 and G3 search, PPRM check (subagent; lead-verified only where B2 says so)

## B2: PPRM scaling check and G1/G3 literature search (cutoff 2026-10-27, run 2026-10-28)

Method note: search results come from WebSearch snippets (summaries by the search tool) plus my own WebFetch/PDF reads. Verification levels: FULL = I read the theorem/definition text in the primary PDF; PARTIAL = read part of primary text; ABSTRACT-ONLY = arXiv abstract page only. Search is not exhaustive; "open" below means "not found in the queries listed", never "proved open".

### TASK 1: PPRM scaling check

Primary source: Zhang, Cai, Yu, Simeone, "Prediction-Powered Risk Monitoring of Deployed Models for Detecting Harmful Distribution Shifts", PMLR v306 zhang26g (page https://proceedings.mlr.press/v306/zhang26g.html; PDF https://raw.githubusercontent.com/mlresearch/v306/main/assets/zhang26g/zhang26g.pdf, downloaded and read via pdftotext; arXiv 2602.02229 appeared in search results, not read). Equation numbers below are from the PDF. Two-column text extraction garbles some formulas; I read the surrounding prose and the Appendix A.4 equations (45)-(50) which extracted cleanly.

#### What the paper says
- Per-round estimate (18)-(19): R_t^PP = eta_t * mean(proxy_U) + mean(true_L - eta_t * proxy_L). Its support is [-eta_t, 1+eta_t] (Section 3.2 text).
- Section 3.2, eq (21): U_0^PP = R0hat + w_0^PP and L_t^PP = Rbar_t^PP - w_t^PP. Text: because the estimates lie in [-eta, 1+eta], "we first apply an affine normalization g_a(.), g_a(x) = (x+eta_max)/(1+2 eta_max) ... so each estimate lies in [0,1]". Then "With the rescaled loss, the correction term is w_t = u(V_t)/t", with V_t in eq (22) written as a sum of squared (R_t^PP - Rbar_{t-1}^PP) terms (notation does not carry a normalization symbol).
- Eq (23): alarm = 1[L_t > U_0 + tol]. Theorem 3.2, eq (24): P_H0(exists t: alarm) <= alpha_S + alpha_T, for any predictable {eta_t}; proof is "follows directly from Lemma 2.2" using unbiasedness (Lemma 3.1, eq 20).
- Appendix A.4 (eqs 45-50, delay analysis): X_t = (R_t + eta)/(1+2 eta) in [0,1] (45); mean (p+eta)/(1+2eta), threshold (delta_0+eta)/(1+2eta), margin delta/(1+2eta), variance v^PP/(1+2eta)^2 (46)-(48); and "the alarm condition for PPRM should therefore be written on the normalized scale as Xbar - u(V^X)/t > threshold_X" (49). Delay (50) = [delta/(1+2eta)]^... i.e. margin and variance both normalized.
- Eq (26)/(27): eta_t* = Cov(u, u~^L) / ((1 + n_t/N_t) Var(u~^U)); plug-in uses sliding window with ratio 1 + |H|/|H~|.

#### Is there a scaling inconsistency in the paper itself?
Finding: a presentational (notation) inconsistency in the main text, not a theorem error that I could detect.
- Eq (21) subtracts w_t (defined "with the rescaled loss", i.e. on the [0,1] scale) from Rbar_t (defined in eq 18 on the unnormalized scale). Read literally, the radius and the center live on different scales unless w_t is multiplied by (1+2 eta_max) (equivalently the center is normalized). The main text never states that conversion. Appendix eq (49) writes the alarm entirely on the normalized scale, which is the consistent form; so the intended construction is self-consistent but eqs (21)-(23) as printed are under-specified.
- A reader (or the AI review page the task mentions, which I did not use) who equates the printed eq (21) with an unnormalized-minus-normalized subtraction would see a factor (1+2 eta_max) mismatch. That is a valid reading of the typography, but resolving it with eq (45)-(49) removes it. I did not find any place where the proved statement (Theorem 3.2) requires the mismatched version; the proof is delegated to Lemma 2.2 and holds for any consistently-scaled bounded process.
- I cannot rule out other errors (for example in (52), which extracted garbled), so this is "no inconsistency found in the guarantee; one notational ambiguity found".
- Verification level: FULL for eqs (18)-(24), (45)-(50); PARTIAL for Lemma 2.1/2.2 (not re-derived).

#### Does ShiftLab match the paper?
Yes on scaling, with documented deviations. File:line (src/shiftlab/dive/):
- eprocess.py:429-430: support_width = 1+2*eta_max; normalized_threshold = (threshold + eta_max)/support_width. Matches eq (46).
- eprocess.py:491: normalized = (estimate + eta_max)/(1+2 eta_max). Matches eq (45).
- eprocess.py:445-454: lower bound computed on the normalized scale (sum/n - radius/n) and then mapped back with -eta_max + (1+2 eta_max)*normalized_lower, clipped to [0,1]. This is exactly the missing conversion in eq (21); the code is the consistent reading, so the paper's printed ambiguity does not reach the code.
- eprocess.py:496-497 and 440: alarm tested on the normalized scale (eq 49 form), log-crossing statistic against -log(alpha).
- pprm_risk_monitor.py:59-61: estimator eta*mean(proxy_U)+mean(true-eta*proxy_L); matches (18)-(19).
- pprm_risk_monitor.py:128-137: threshold = source_upper_bound + tolerance, passed to the sequence; matches (23).
- pprm_risk_monitor.py:208-210: eta = Cov / ((1 + n/N) Var(proxy_U)), clipped to [0, max_reliance]; ratio uses window sums, matching (27)-(28). Clipping at eta_max is consistent with the paper's "maximum permitted value".
- pprm_risk_monitor.py:249, 295: source values normalized by (v+eta_max)/(1+2 eta_max) and mapped back at :261, :315-318. Consistent.
Deviations (declared in code, not scaling errors): finite-mixture CM-EB test sequence instead of the paper's continuous mixture q(lambda) integral in eq (22) (eprocess.py:426-428, lambdas in (1e-4, 0.99)); source bound has both a CM-EB variant (pprm_risk_monitor.py:226-261, documented as a deviation, :236-239) and a betting variant (:264-320) following Appendix A.2/Einbinder et al.; alpha split 0.025/0.025 (default) satisfies alpha_S + alpha_T <= 0.05.
Caveat: I confirmed formulas by reading, not by executing numerical comparisons against the authors' code. The existing audit file papers/shiftguard_unified/pprm_paper_implementation_audit.md was only grepped, not reviewed in full.

### TASK 2: Literature search

#### Exact query list
G1 (12 queries incl. two "extended"):
1. anytime-valid off-policy evaluation sequential test policy degradation bandit feedback e-process
2. sequential off-policy monitoring policy regret harmful distribution shift contextual bandit confidence sequence
3. arXiv 2026 anytime-valid off-policy evaluation drift detection deployed policy reference policy importance weighting e-value
4. "off-policy" "confidence sequences" "doubly robust" sequential monitoring policy performance change detection
5. sequential test whether new policy outperforms baseline anytime-valid A/B testing contextual bandit logged data e-process "no worse than" policy
6. safe policy monitoring deployment off-policy evaluation distribution shift sequential detection ICML 2026 OR NeurIPS 2025 OR ICLR 2026
7. e-process change detection partial feedback decision loss monitoring counterfactual baseline policy anytime-valid
8. sequential change detection off-policy evaluation reward drift bandit logged data CUSUM e-detector
9. Chugg Ramdas "anytime-valid" off-policy OR "policy" sequential testing non-stationary adaptive data collection 2025 2026
10. monitoring deployed decision policy sequential detection of harm under bandit feedback "reference policy" counterfactual loss anytime-valid arXiv 2026 (extended)
G3:
1. post-selection inference after model update e-process anytime-valid adaptive retraining monitoring
2. performative prediction anytime-valid sequential test e-values intervention changes data distribution
3. e-values composition sequential interventions adaptive data collection model updated after alarm validity Ville inequality restart
4. safe anytime-valid inference adaptive retraining monitor triggers model update confidence sequence validity after intervention
5. sequential monitoring with feedback loop: alarm triggers retraining, subsequent e-process validity, closed-loop anytime-valid guarantee (extended)
6. e-detector restart after detection model retraining false alarm guarantee repeated monitoring average run length e-process nonstationary learner
7. "performative" "anytime-valid" OR "e-process" OR "confidence sequence" distribution shift induced by deployed model monitoring
Limitation: WebSearch is US web search with LLM-summarized snippets; I did not query OpenReview, PMLR, or Google Scholar directly by site; venue accepted-paper lists (NeurIPS 2025, ICLR 2026, AISTATS 2026, UAI 2026, COLT 2026) were not enumerated. Venue-specific search queries (6) returned no matching accepted papers, but that is weak evidence.

#### G1: off-policy sequential harm detection with only the deployed action observed

1. Waudby-Smith, Wu, Ramdas, Karampatziakis, Mineiro, "Anytime-valid off-policy inference for contextual bandits" (arXiv 2210.10768 v3, Aug 2024; ACM/IMS J. Data Science / TOMPECS 10.1145/3643693 per search; primary PDF downloaded and read).
 - Establishes: Section 3.3, Proposition 4. For policies pi1, pi2 and logged data (X_t, A_t, R_t) from a possibly adaptive logging policy h_t, Delta_t = V_t(pi1) - V_t(pi2); estimator uses importance weights w_t^(1) = pi1(A_t|X_t)/h_t(A_t|X_t) and w_t^(2) analogously, in the form omega_t = w1*R - (1 - w2(1-R)) with omega_t >= -1 and E[omega_t | H_{t-1}] = Delta_t (eqs 38-39). Weak null H0: running average Delta-bar_t <= 0 for all t (eq 37); an empirical-Bernstein e-process (eq 42) gives an anytime p-value p_t = min(1, 1/M_t); this is valid while the logging policy changes (history-adapted) and with time-varying values. Remark 3.1 states differences can also be handled directly (gated deployment where pi2 = logging policy h).
 - Verification: PARTIAL-to-FULL for Section 3.3 definitions and Prop 4 statement (text-extracted; the proposition's full formula garbled). I did not verify positivity/overlap assumptions beyond "policies absolutely continuous w.r.t. logging policies".
 - Closes? PARTIALLY CLOSES the core statistical machinery: a paired policy-value-difference e-process using only the logged action's outcome, valid under adaptive logging and a time-varying value difference. Not found in that paper: (a) harm framing (null "deployed no worse than reference" with a margin, rejecting for harm rather than lift); this is a sign/margin change I infer is easy but did not verify; (b) change/degradation detection against a frozen pre-shift baseline (the null is on average difference thus far, which is a running-average null, same type PPRM/ShiftLab use); (c) delayed/missing/selectively sampled feedback; (d) deterministic deployed policies (importance weights require overlap: pi_ref must be absolutely continuous w.r.t. h_t, so if the deployed policy is deterministic the reference counterfactual is not identifiable without extra randomization or a model); (e) unknown or estimated propensities; (f) decision-loss estimand under PPI-style synthetic labels. A novelty claim for G1 must therefore be framed beyond "e-process for paired policy value difference under bandit feedback", which exists.
2. Karampatziakis, Mineiro, Ramdas, "Off-Policy Confidence Sequences", ICML 2021 (PMLR v139 karampatziakis21a). ABSTRACT-ONLY (search listing; page not fetched). Martingale OPE confidence sequences; "gated deployment" is the stated application. Partially closes (lift of target over logging policy); same gaps as above.
3. Molitor, "Anytime-valid Optimal Policy Identification", arXiv 2606.17515 (Jun 2026, stat.ME). ABSTRACT-ONLY. Time-uniform sets for the optimal policy from logged bandit data. Not harm detection of a deployed policy against a reference; does not close G1.
4. Zheng, Wiberg, Zhu, "Deciding When to Decide: Testing Operational Suboptimality Under Distributional Shift", arXiv 2608.29465 (Aug 2026). ABSTRACT-ONLY. Two-sample and sequential changepoint tests for incumbent decision regret using inverse optimization; guarantees are asymptotic Type-I/power; abstract does not mention bandit/partial feedback or off-policy. Closest "decision harm under shift" neighbour; does not close G1 (full text not read; unverified whether partial feedback is treated).
5. Zhang et al. PPRM (ICML 2026) and Podkopaev and Ramdas (ICLR 2022, arXiv 2110.06177): predictive-risk monitoring, full labels (PPRM adds synthetic labels). Not decision harm and not partial feedback. Listed by search; PPRM FULL as in Task 1.
6. Timans et al., "On Continuous Monitoring of Risk Violations under Unknown Shift", UAI 2025 (arXiv 2506.16416). ABSTRACT-ONLY via search. Bounded-risk sequential test; not policy comparison.
7. Others surfaced and judged not relevant to G1 by title/snippet only: Choi arXiv 2608.08174; Han and Qu arXiv 2608.30502 (see G3); Saha and Ramdas arXiv 2607.28322 (non-partitioned e-detectors; abstract read, no off-policy content); arXiv 2606.15474 "Who Drifted: the System or the Judge?" (LLM-eval drift e-process; snippet only).
G1 status: the off-policy paired e-process machinery exists (Waudby-Smith et al. Prop 4); I did not find (in these 10 queries) a paper that frames it as harm monitoring of a deployed policy against an explicit frozen/predictable reference with margin, delayed/selective feedback, or detector baselines. Treat G1 as "partially closed; residual novelty = harm framing + feedback regime + identifiability conditions + evaluation", not as open.

#### G3: validity of evidence after the intervention it triggers

1. Han and Qu, "When the Martingale Never Stops Firing: Anytime-Valid Gating on Real Forecast Streams", arXiv 2608.30502 (31 Aug 2026, cs.LG). ABSTRACT-ONLY. Empirical closed-loop study: conformal test martingale gates a Kalman adapter; fires in every clean real-stream run; the alarm changes the learner whose scores the monitor reads; concludes null-calibration controls are needed. Documents the failure empirically; no formal post-update validity theory evident from the abstract. Does not close G3; supports the relevance of the gap.
2. Choi, "Anytime-Valid Evidence for Prespecified Predictive Corrections", arXiv 2608.08174 (Aug 2026, stat.ME). ABSTRACT-ONLY. E-process = cumulative log-score advantage of a prespecified correction over source predictive; claims validity under optional stopping and adaptively selected inputs; extensions to predictable tilts. This evaluates a correction chosen in advance, not evidence continuity after an alarm-triggered change to the stream. Does not close G3 (theorem hypotheses unread).
3. Saha and Ramdas, "Non-partitioned e-detectors for nonparametric sequential change detection", arXiv 2607.28322 (Jul 2026). ABSTRACT-ONLY (search snippet adds: proofs use only a restartable conditional e-process property, no independence; snippet not verified against full text). Restart-style guarantees do not depend on independence, which is relevant to composing monitors across restarts; no model-update intervention analysed. Partially relevant tool, not a closure.
4. arXiv 2608.12660 "Universality of e-detectors for ARL control" (authors not captured). ABSTRACT-ONLY. ARL control via thresholded e-detectors; snippet (not verified) says repeated alarms after restarts need counting e-detectors controlling expected false-alarm counts, bounding the mean time of the j-th false alarm below by j/lambda. Relevant to multi-alarm accounting, no retraining/closed-loop treatment.
5. Csillag et al., "Prediction-Powered E-Values", ICML 2025 (PMLR v267 csillag25a; arXiv 2502.04294). Snippet only. Predictive model and data-collection policy may change over the inference (predictable); validity holds because updates are history-adapted. Does not cover deployment-induced shift of the data distribution. Partially relevant to predictability condition (the pi_t predictable regime), not a closure.
6. Farran, PITMonitor, arXiv 2603.13156 (Mar 2026). ABSTRACT-ONLY: calibration monitor with mixture e-process; no post-alarm procedure stated.
7. Polson, Sokolov, Zantedeschi, "Bayes, E-values and Testing", arXiv 2602.04146 (v1 Feb 2026, v6 Mar 2026, math.ST). ABSTRACT-ONLY. Layers of representation/validity/decision; no composition result for e-values found in the abstract (a search snippet that implied misapplied composition could fail is not supported by the abstract I read; disregard it).
8. Waudby-Smith et al. 2210.10768 and Cook, Mishler, Ramdas (adaptive A/B, PMLR v236 cook24a; snippet only): CSs valid under adaptively changing assignment policies (predictable). This is the standard route when the intervention is a history-adapted policy: the monitor remains a test supermartingale for a fixed null on the adapted stream. Reading: if the intervention's effect on the stream is still a predictable function of history and the null is stated conditionally per round, validity can persist; if the null is a fixed marginal law and the intervention changes it, it does not. This is my analysis, not a cited theorem.
G3 status: not found in 7 queries, a theorem that gives anytime-valid evidence across alarm-triggered retraining/switching with composite nulls or alpha-spending across epochs, nor a performative + anytime-valid monitoring result. Closest items are empirical (Han and Qu) or about predictable adaptation (Csillag et al.; Waudby-Smith et al.; Cook et al.) or restart accounting (e-detector papers). Leaves G3 open relative to what I found; strength of evidence is moderate-to-weak (abstract-only for most items, no site-level OpenReview/PMLR/Scholar sweep).

#### Caveats
- Many 2026 arXiv items were verified only to abstract level; a theorem that closes G3 could sit in an unread full text.
- Search-tool summaries are LLM-generated; claims attributed to snippets (flagged above) are not verified.
- I did not read Waudby-Smith et al. proofs, and Prop 4's exact e-process (42) formula garbled in extraction.

# Appendix F. G2 and G4 search (subagent; lead-verified only where B2 says so)

## B2 literature search: G2 and G4 (cutoff 2026-10-27; run 2026-10-28)

### 0. Method and limits

- Search tool: WebSearch (a US-only web index that returns summaries) plus WebFetch. I did not query OpenReview, PMLR, Google Scholar or conference accept lists directly. Venue names appear only as search terms. "Not found" therefore means "not surfaced by these queries", not "does not exist".
- For papers that mattered I downloaded the arXiv PDF and read the text locally with `pdftotext`. Files are in `scratchpad/pdf/`. Because WebFetch could not parse PDFs, every FULL or PARTIAL label below comes from that local text, not from a web summary.
- Verification levels:
  - FULL: setting, assumptions and theorem statements read.
  - PARTIAL: setting and key theorems read or grepped, proofs not read.
  - ABSTRACT-ONLY: abstract or search summary only.
- No proofs were read anywhere. "FULL" means the statements, not the proofs.

### 1. Exact query list

#### G2 (future net benefit of a replacement; improvement need not persist)
1. Towards safe policy improvement for non-stationary MDPs Chandak NeurIPS 2020
2. certify future performance of model update under non-stationarity high-confidence guarantee arXiv 2026
3. high-confidence off-policy evaluation non-stationary forecasting future policy value
4. time-varying treatment effect anytime-valid confidence sequence decaying advantage
5. switching cost sequential decision certification model replacement anytime-valid net benefit
6. predictive policy improvement guarantee under drift safe model update forecast horizon
7. Seldonian non-stationary safe policy improvement follow-up forecast high-confidence 2024 2025 2026
8. prediction interval for future performance of deployed model under distribution drift conformal future time step guarantee
9. when to deploy updated model: confidence bound on future gain of retrained model over incumbent, retraining cost, drift, delayed labels
10. transfer of policy improvement over time off-policy evaluation temporal distribution shift confidence interval deploy later horizon
11. sequential test model promotion candidate versus incumbent drifting performance gap anytime-valid confidence sequence nonstationary difference
12. Waudby-Smith Ramdas confidence sequences for time-varying parameters drifting mean running average vs current value forecasting guarantee
13. NeurIPS 2025 OR ICLR 2026 non-stationary off-policy evaluation confidence interval future policy value safe deployment guarantee
14. ICML 2026 anytime-valid certificate model replacement deployment gated promotion drift improvement may not persist
15. UAI 2026 OR AISTATS 2026 safe model update certificate nonstationary delayed feedback e-process switching
16. arXiv 2026 "net benefit" model update post-deployment guarantee high-probability lower bound future cumulative gain minus retraining cost

#### G4 (theorem-level hard-budget label allocation under unknown bursts)
1. budgeted active sequential testing label budget e-process disagreement bursts minimax
2. data-efficient quickest change detection finite observation budget minimax optimal
3. active betting e-process label budget anytime-valid active sampling Xu
4. label budget change detection minimax regret hard budget exhaustion sequential testing unknown arrival of informative events
5. observation control sequential test budget constraint hard cap number of samples quickest detection sampling budget finite horizon
6. budget-constrained anytime-valid inference e-process online label allocation nonstationary
7. bandits with knapsack nonstationary budget regret bursty rewards online resource allocation unknown number of bursts
8. active learning with a hard labeling budget under distribution shift streaming selective sampling regret budget pacing guarantee
9. sequential testing with limited labels disagreement-triggered querying model comparison anytime-valid label complexity budget exhausted
10. COLT 2026 OR JMLR change detection with label budget active sequential hypothesis testing minimax budgeted e-process regret
11. Annals of Statistics OR JRSSB OR Biometrika sequential testing with sampling control budget on number of labeled observations anytime-valid optimal sampling policy

Direct fetches (not searches): arXiv abs 2512.18390; PDFs 2609.17560, 2010.12645 copy from UMass, 2603.08578, 2604.18569, 2609.26651, 2512.01423, 2609.29140, 1212.4717, 2412.20207, 2304.06808, 2406.10490, 2302.11725, 2506.20417, 2510.10232, 2607.00871, 2102.09540, 2603.25971, 2202.06374.

### 2. G2 findings

**Gap statement.** A certificate on the future net benefit of the selected replacement over a post-switch horizon, net of switching cost, when the advantage may decay, under delayed or adaptively acquired feedback.

| Paper (identity checked from primary page or local PDF) | What it establishes | Level | Effect on G2 |
|---|---|---|---|
| **Chandak, Jordan, Theocharous, White, Thomas, "Towards Safe Policy Improvement for Non-Stationary MDPs", NeurIPS 2020** (neurips.cc page; UMass PDF read) | A Seldonian algorithm that applies a sequential safety test to the **forecasted** future performance of a candidate. Assumption 1 requires performance to follow a smooth trend in a known basis. Assumption 2 is full support of the behaviour policies. Theorem 2 gives consistent coverage of the CI for ρ(π, k+δ) obtained by wild bootstrap, and holds **asymptotically as k→∞**, with independent trajectories and a Fourier basis. The paper says it reuses test data across consecutive tests and that this breaks independence. It makes no claim that the sequential tests together control error. | PARTIAL (setting, assumptions, Thm 1–2 read; appendix not read) | **Closest precedent for "certificate on a future value under drift". Partially closes.** Not covered: a finite-sample or anytime-valid guarantee, a switching cost, a net-benefit quantity that compares candidate and incumbent over a horizon, delayed or adaptively acquired labels, and any decay model beyond a smooth trend in a fixed basis. A baseline we must cite and beat. |
| **Liu, Chandak, Thomas, White, "Asymptotically Unbiased OPE when Reusing Old Data in Nonstationary Environments", arXiv 2302.11725 (AISTATS 2023)** | A regression-assisted DR estimator that reuses old data. It is asymptotically unbiased and asymptotically normal, with a large-sample CI for current and future policy values. Thm 2 is asymptotic. | PARTIAL (theorem headers and abstract; proofs not read) | Same family as Chandak. Asymptotic, a single policy rather than a paired net benefit, no switching cost. Leaves G2 open. |
| **Shimizu et al., "OPE and Learning for the Future under Non-Stationarity", arXiv 2506.20417 (KDD 2025)** | The OPFV estimator of a policy's value in a future period, using time features. Theorem 3.3 gives bias and variance. | PARTIAL (grep of theorem lines) | Point estimation with a bias analysis, not a certificate. No confidence guarantee found. Leaves G2 open. |
| **Digalakis, Pérignon, Saurin, Sentenac, "The Challenger", arXiv 2512.18390 v2 (Jul 2026)** | Switching an incumbent for a challenger when learning-curve gains are traded against retraining cost. Power-law learning curve, optimal evaluation time ∝ T^{1/(1+α)}, regret O(T^{2/3}√log T) against a foresight oracle. | ABSTRACT-ONLY (arXiv listing; PDF not read) | Models switching cost and a trend in the gain, but the guarantee is **regret, not a probabilistic certificate**. It needs a parametric learning-curve assumption. Leaves the certificate open. A full read is needed before relying on that, since the delta may be larger than the abstract suggests. |
| **Balachandran, DISCERN, arXiv 2609.17560, §5.7** | I read §5.7 verbatim. Under shift "there is no fixed Δ to certify". The CS covers the running weighted average of conditional means. A sliding-window restart gives "current-regime verdicts". Unrestarted miscoverage of a moving running-average target was 6.4% under smooth drift and 15.9% under adversarial bursts. | FULL on §5.7 (other sections only grepped) | The author states G2 as unaddressed. The windowed restart certifies the **past window**, not a post-switch horizon, and there is no switching cost. Supports the gap. |
| **Lamaakal et al., Drift2Act, arXiv 2603.08578 (ICLR 2026 CAO workshop)** | An anytime-valid UCB U_t on **current windowed risk** (Thm 1, Thm A.2 under adaptive querying with delay). The costed action rule is a **one-step heuristic utility** Δ̂−λc−Viol. | PARTIAL (Thm 1, A.2, §5.3, limitations read) | The certificate is on current risk, not future net benefit. It does not certify the effect of the intervention. Leaves G2 open. Its limitations section admits non-stationarity weakens window validity. |
| **Karampatziakis, Mineiro, Ramdas, Off-policy confidence sequences, arXiv 2102.09540 (ICML 2021)** | Time-uniform OPE CSs, with gated deployment as the application. | ABSTRACT-ONLY here (previously known; header read) | Stationary target. Does not close G2. |
| **Wu et al., Statistical Gödel Machines, arXiv 2510.10232 v2 (Sep 2026)** | An anytime-valid improvement certificate for adopting a modification, under a predictable summable error budget. The abstract states that the guarantee is for a "specified evaluation objective" and that it does not guarantee full future utility. Line 52 and the grep disclaim a "full future-utility comparison". | PARTIAL (abstract and disclaimers grepped) | Explicitly disclaims future utility. Supports the gap. |
| **Sengupta, SEA, arXiv 2607.00871** | An e-value drift gate for self-evolving agents. The gate is a drift test, not a future-benefit certificate. | ABSTRACT-ONLY plus grep | Not relevant to G2 beyond showing the gap is not addressed. |
| **Lindon & Kallus, arXiv 2603.25971 (v2, May 2026)** | Design-based anytime-valid CSs for the cumulative reward of each arm as a function of calendar time, robust to nonstationarity, with delayed outcomes and staggered entry. The estimand is the realized sample cumulative reward **up to time t**. | PARTIAL (abstract read) | Valid under nonstationarity and delay, but about **realized past** counterfactual reward, not a prediction of a future horizon, and no switching cost. A useful design-based tool for the delayed-feedback piece. Does not close G2. |
| **Choe & Ramdas, "Comparing Sequential Forecasters", Operations Research** (search summary only) | CSs for the time-varying mean score difference between two forecasters, with no stationarity assumption. | ABSTRACT-ONLY | Tracks a drifting paired gap in the **past**. A baseline for the paired comparison. Does not forecast. |
| Mineiro, arXiv 2512.21300 (Dec 2025; search summary) | A closed-form CS for the **average conditional mean** under drift. | ABSTRACT-ONLY | Same kind of target (a running average). |
| Regol et al., ICML 2025 "When to retrain"; Katz 2603.25480; Sima et al. 2026 (search summaries) | Decision-theoretic retraining rules. A risk-averse quantile rule is mentioned only in a vendor blog about Regol. | ABSTRACT-ONLY | Decision rules, not certificates. Not enough to close anything. |
| Haidar-Wehbe et al., "Holdout sets for safe predictive model updating", arXiv 2202.06374 | Holdout sizing so that an updated risk score is unbiased. Asymptotic optimality of adverse outcomes. | ABSTRACT-ONLY | Adaptive-feedback design, not a certificate. Relevant to the "feedback created by the deployed model" assumption. |

**G2 verdict: PARTIALLY CLOSED, narrowly open.** The forecasting idea is not new. Chandak et al. (2020) certify forecasted future performance under a smooth-trend assumption, and Liu et al. (2023) do so asymptotically for OPE. What I did not find, in 16 queries, is a **finite-sample or anytime-valid** certificate that is:
- paired candidate-versus-incumbent;
- net of a switching cost over a post-switch horizon;
- valid when the advantage can decay;
- valid under delayed or adaptively acquired feedback.

Three caveats weaken any "open" claim:
1. The Challenger paper is ABSTRACT-ONLY and handles switching cost and trending gains, so read it in full.
2. Chandak's unproved appendix and the exact condition for sequential-test validity are unread.
3. A paper combining a Chandak-style forecast with a Karampatziakis-style CS would only need a stated persistence assumption, so a reviewer could call G2 "Chandak plus an anytime-valid CS". The contribution must therefore be in the **persistence-robust** part (what can be certified when no trend model is assumed), not in the forecast.

### 3. G4 findings

**Gap statement.** A minimax or regret theorem for allocating a **hard** finite label budget over time when informative events (disagreements) arrive in unknown bursts, contrasting budget exhaustion with bound inflation.

| Paper | What it establishes | Level | Effect on G4 |
|---|---|---|---|
| **Xu, Karampatziakis, Mineiro, "Active, anytime-valid risk controlling prediction sets", arXiv 2406.10490** | Label policy via inverse-propensity-weighted betting. Budget is **in expectation**: a B fraction is labelled in expectation (line 482). Thm 3 gives a G-regret to the e-process wealth, in terms of estimation error of the optimal labelling policy and predictor. | PARTIAL (statements grepped) | The budget is expected, not hard, and the setting is stationary. No bursts, no exhaustion. Does not close G4. |
| **Sfyraki & Wang, "Revisiting Active Sequential Prediction-Powered Mean Estimation", arXiv 2604.18569 (ICLR 2026)** | Non-asymptotic data-dependent CI width bound (Thm 1, Thm 2). A no-regret FTRL choice of the query probability. Uniform querying at the budget limit appears near-optimal. | PARTIAL (statements grepped) | A no-regret result for query probability, but for a fixed i.i.d. mean with an expected budget. Suggests that burst-aware allocation may not beat uniform in the stationary case. Does not close G4. |
| **Banerjee & Veeravalli DE-CuSum, arXiv 1211.3729** and robust variant **Hou, Bidkhori, Banerjee, arXiv 2412.20207** | On-off observation control. Minimum delay subject to a **false-alarm rate** and an **average** observation cost before the change. Asymptotic optimality as the false-alarm rate goes to zero. | PARTIAL (abstracts read, including 2412.20207) | A rate or average constraint, known likelihoods, asymptotic. Not a hard cap with unknown bursts. Does not close G4, and agrees with the B1 correction of the exit-ledger wording. |
| **Bayraktar & Kravitz, "Quickest Detection with Discretely Controlled Observations", arXiv 1212.4717 (Sequential Analysis)** | A Bayesian continuous-time problem with a **finite number of observation rights**. Existence of optimal strategies, jump-operator algorithms, and convergence to Shiryaev as the number of rights → ∞. | PARTIAL (abstract and intro) | **Closest to a hard budget.** Assumes a Bayesian prior on a single change and a known post-change law, and gives no minimax or regret bound against unknown bursts. Partially relevant. Does not close G4. |
| **Cheng et al., "Sharp Limits for Honest Uncertainty in Hard-Budget Repeated Evaluation", arXiv 2609.29140 (Sep 2026)** | Matching upper and lower bounds on optimal expected CI width under a **hard budget** (M+t)K on a fixed grid of M tasks, including **adaptive hard-budget policies**. Rates Θ([M(t+1)]^{-1/2}) when every task is observed and Θ([M(t+M)]^{-1/2}) when omission is allowed. Disagreement certificates attain the rates. | PARTIAL (abstract, §1 and grep) | The only hard-budget minimax result involving disagreement that I found. It is for a **static** grid with independent tasks, no time or bursts, no sequential testing and no anytime validity. A methodological neighbour, not a precedent. Does not close G4, but must be cited and distinguished. |
| **Cai & Kandasamy, "Active Cost-aware Labeling of Streaming Data", arXiv 2304.06808 (AISTATS 2023)** | Streaming labelling with labelling cost B. Worst-case regret ~ B^{1/3} K^{1/3} T^{2/3} with matching lower bounds, for K discrete input distributions. | PARTIAL (abstract) | A **cost-penalised** (soft budget) streaming problem with a regret rate. Not an anytime-valid test and not a hard cap. Partially relevant for the proof technique. |
| **Li et al., Active Sequential Two-Sample Testing, arXiv 2301.12616 (TMLR 2024)** | Anytime-valid p-value with label budget, in two query modes. | ABSTRACT-ONLY | A budgeted active test with no minimax statement and no burst model. |
| **Lin, Ma, Ren, Wei, arXiv 2609.26651 (Sep 2026)** | e-value posterior sampling across hypotheses, with high-probability sample-complexity bounds in terms of e-process growth. | PARTIAL (abstract) | Allocates a sampling budget **across hypotheses**, not across time. Does not close G4. |
| **Kuang, Gang, Xia, arXiv 2512.01423 (v3, Sep 2026)** | Active e-values and p-values under an **exact computational budget**, with optimality for active e-values. | PARTIAL (abstract) | An exact (hard) budget across hypotheses, not over time with bursts. Does not close G4. |
| **Liu, Jiang, Li, Non-stationary Bandits with Knapsacks, NeurIPS 2022, arXiv 2205.12427** | Regret for BwK under a global variation budget. | ABSTRACT-ONLY | Hard budgets under nonstationarity for rewards, not for e-process inference. The variation budget is a candidate formalism for "number or size of bursts". |
| Balachandran, DISCERN | States that adaptive budget allocation, alpha-investing combinations and Neyman allocation across slices are "left open" (§ limitations, lines 1119–1130). | FULL on that paragraph | The author lists allocation as open. Supports the gap for his setting. |
| Lorden; Ram & Ramdas arXiv 2602.05272 (search summary) | CUSUM minimax and composite change detection. No budget. | ABSTRACT-ONLY | Background only. |

**G4 verdict: OPEN as a theorem-level statement, but adjacent results exist.** In 11 queries I found no paper stating a minimax or regret bound for hard-budget label allocation in sequential testing or change detection with unknown bursts. The nearest results are:
- Bayraktar & Kravitz (hard budget, Bayesian, no bursts);
- Cheng et al. (hard-budget minimax with disagreement, static);
- Xu et al. and Sfyraki & Wang (regret for query probability, expected budget, stationary);
- the nonstationary BwK literature (hard budget, bandit rewards, not inference).

A reviewer could assemble the result from a BwK pacing argument plus an e-process wealth bound. Whether that route actually yields a regret bound is not shown by anything I read.

Caveat: Sfyraki & Wang point toward uniform querying being near-optimal in the stationary case. A burst theorem would need a separating instance where uniform at the budget rate is provably suboptimal. The repository's M4 negative result (a related idea failed a pre-screen) is a warning of the same kind.

### 4. Search gaps to close before a final novelty claim

1. Read in full: Challenger (2512.18390), Chandak appendix, Liu et al. Theorem 2 conditions, Bayraktar & Kravitz, Cai & Kandasamy.
2. Check by direct browsing: the ICML 2026 and UAI 2026 accepted-paper lists, the NeurIPS 2026 list (found in search: "Optimizing Retraining Schedules via Learning Curves", poster 154395, ABSTRACT-ONLY) and the COLT 2026 list.
3. Query "BwK with change points" and "piecewise-stationary knapsack" (suggested by the BwK result, not yet run), and "restless or time-varying budget pacing e-process".
4. Query for G2 through the causal and clinical literature (dynamic or time-varying treatment-effect forecasting, "transportability over time"). Not run.
5. The Annals/JRSSB/Biometrika queries returned no relevant hit, but WebSearch coverage of those journals is weak.

# Appendix G. Independent cross-model review (Codex gpt-6.1-sol, xhigh, read-only, 2026-10-28; verbatim final answer)

G4 clears the novelty check. G1–G3 retain narrower research possibilities, but their broad formulations fail the project’s combination test. Neither existing NO-GO decision should be reversed.

I read the dossier, charter, novelty matrix, and relevant repository evidence notes, and searched primary literature across all four gaps. “No matching result found” below is a search conclusion, not proof of absence. This is a novelty assessment, not an independent verification of every cited proof. No files were modified.

G1. Bandit-feedback monitoring of paired policy harm

ARIS verdict: PROCEED WITH CAUTION.

The basic bandit-feedback contribution is already substantially covered. Waudby-Smith et al., Sections 3.1 and 3.3, explicitly construct inference for policy-value differences with adaptive logging and time-varying values. Their running-average null differs from the charter’s eventwise conditional null, but that distinction does not itself establish a new method. A known harm margin is a threshold adjustment. [Anytime-valid off-policy inference](https://arxiv.org/html/2210.10768)

The potentially substantive delta is efficient inference with informative delays or censoring, adaptive action and label acquisition, and a clearly identified event-population estimand. Lindon–Kallus already address treatment-dependent outcome delays, although their calendar-time cumulative-reward target and randomization setup differ. Thus “we additionally handle delay” is insufficient. [Lindon–Kallus](https://arxiv.org/html/2603.25971)

Two-algorithm test: YES for ordinary selective-feedback monitoring—Waudby-Smith et al.’s off-policy difference process plus Xu–Karampatziakis–Mineiro’s importance-weighted active-label construction. Their assumptions must be reconciled; their combination does not automatically handle outcome-dependent missingness. For finite delays, the repository’s resolved-prefix argument supplies a conservative implementation without a new testing engine. [Active anytime-valid risk control](https://arxiv.org/html/2406.10490)

Project verdict: Narrow the novelty claim to a specific delay/censoring result that improves materially on these constructions.

Provability: Plausible with known logging/query probabilities, overlap wherever the policies differ, and a justified observation mechanism. Predictability must refer to the actual information available when actions, queries, and bets are chosen. Deterministic deployment without reference-action support does not identify the contrast. Arbitrary informative missingness remains unidentified without additional assumptions.

Worst objection: “This is existing off-policy sequential inference with another importance weight and a shifted threshold.”

Paper-anchor or section: Section as currently formulated. A sharp result for informative, asynchronous feedback could become an anchor, but the dossier has not yet specified that result.

G2. Certification of future net benefit after switching

ARIS verdict: PROCEED WITH CAUTION.

The finite-sample prospective target remains potentially substantive. Chandak et al.’s SPIN already forecasts future policy performance, but its bootstrap coverage theorem is asymptotic. Shimizu et al.’s OPFV, missing from the dossier, also directly studies future policy evaluation under structured nonstationarity. Neither establishes the complete proposed certificate. [SPIN, Theorem 2](https://arxiv.org/html/2010.12645), [OPFV](https://arxiv.org/html/2506.20417)

Two-algorithm test: YES for the natural formulation with a known drift envelope—combine Waudby-Smith et al.’s sequential value-difference bound with Chandak et al.’s performance-drift bound. Transfer the historical bound forward, subtract the drift allowance, and subtract switching cost. This is my proposed reduction, not a claim that either paper states the combined theorem.

Project verdict: Narrow. The contribution must go beyond “confidence sequence minus drift allowance minus switching cost.” A sharp characterization of when prospective certification is possible, with an attaining procedure and meaningful lower bounds, could supply that distinction.

Provability: The decisive assumption connects the observed past to the post-switch horizon. With unrestricted future change, two environments can produce identical evaluation histories and opposite future benefits. A useful theorem therefore needs a defensible variation bound, structural forecasting model, or other transport restriction. A bound learned from past behavior alone cannot certify unrestricted future persistence.

The target must also distinguish expected future benefit from realized future gain; the latter needs an additional prediction-error allowance.

Worst objection: “Your persistence assumption does the substantive work; the certificate is routine once that assumption is granted.”

Paper-anchor or section: A simple drift-adjusted certificate is a section. A sharp, non-vacuous prospective-certifiability theorem could anchor Paper 2.

G3. Evidence validity through monitor-triggered intervention

ARIS verdict: PROCEED WITH CAUTION.

Separate two problems: preserving sequential validity under predictable updates, and identifying what an intervention does to subsequent counterfactual outcomes.

The first is substantially established territory. DISCERN handles adaptively selected promotion sequences with fresh evidence and error allocation. Guo’s recent Evidence-Gated Research explicitly handles moving incumbents and adoption-dependent future proposals under joint-history conditional-validity assumptions. It does not establish robustness to arbitrary intervention-induced deployment distributions. [DISCERN, Proposition 13](https://arxiv.org/html/2609.17560), [Evidence-Gated Research](https://arxiv.org/html/2610.01751)

Two-algorithm test: YES for validity bookkeeping—Csillag et al.’s sequential prediction-powered evidence construction plus DISCERN’s promotion-sequence error accounting. NO automatic solution follows for causal effects on subsequent states, populations, or label availability. [Prediction-Powered E-Values](https://arxiv.org/html/2502.04294)

Project verdict: Reject the generic novelty claim; retain a precisely defined causal version.

Provability: Plausible under an explicit randomized or sequentially exchangeable causal design, adequate support, and stated restrictions on carryover or environmental response. The theorem must derive the required conditional evidence property from those assumptions.

An existing process can remain valid for a global null covering predictably chosen policies. Its pre-switch wealth cannot simply become evidence about a different policy-specific claim after switching.

Worst objection: “You assume conditional validity after intervention instead of proving that your intervention and observation design preserve it.”

Paper-anchor or section: A composition or restart theorem is a section. A finite-sample result for a specified causal regime comparison with intervention-induced feedback could anchor a paper. As written, G3 has not fixed that estimand.

G4. Hard-budget allocation under unknown disagreement bursts

ARIS verdict: PROCEED.

This is the strongest surviving gap. I found no paper establishing the proposed combination of an irrevocable finite label budget, freely observed disagreement opportunities, unknown temporal bursts, anytime false-alarm control, and an optimal detection or evidence-quality trade-off.

The closest work is stronger than the dossier suggests. Cheng et al.’s hard-budget inference lower bounds already cover adaptive policies, although their target is a fixed evaluation cohort. Efroni et al. study hard query budgets and adverse contexts. Zhang–Cheung study inventory reservation under piecewise stationarity. These are serious comparators, not demonstrations that G4 is solved. [Cheng et al.](https://arxiv.org/html/2609.29140), [Confidence-Budget Matching](https://proceedings.mlr.press/v139/efroni21a.html), [Piecewise-Stationary BwK](https://proceedings.neurips.cc/paper_files/paper/2024/file/65ae674df2fb642518ae8d2b5435e1b8-Paper-Conference.pdf)

Two-algorithm test: NO established reduction for the proposed detection/budget frontier. The strongest attempted pair is Xu et al.’s active betting plus Zhang–Cheung’s inventory-reserving algorithm. It does not automatically yield detection-delay or fixed-horizon power guarantees: cumulative reward and threshold crossing are different objectives.

However, a theorem concerning only cumulative log-wealth regret might reduce to existing constrained online learning. That reduction must be checked before claiming an inference-specific contribution.

Project verdict: PROCEED with a theorem-centered Paper 3 formulation.

Provability: Plausible after fixing the horizon or exposure model, bounded losses, request-time budget accounting, an admissible burst/adversary class, and a comparator with the same information. Useful power requires enough signal-bearing opportunities relative to the budget. A finite budget cannot support uniform detection of arbitrarily late, arbitrarily short harm over an unrestricted infinite horizon.

Budget exhaustion must explicitly stop acquisition or evidence updates. It cannot coexist with a permanent positive sampling floor.

Worst objection: “Your minimax problem either makes uniform sampling optimal or becomes an existing knapsack problem after rewriting the reward.”

Paper-anchor or section: Potential ICML/NeurIPS anchor if it delivers a meaningful lower bound and an attaining allocation rule. Another pacer with empirical improvements is a section. The repository’s pacer failures motivate the question; they do not establish the proposed contribution.

Ranking: G4 > G2 > G3 > G1, ranked by the strongest defensible remaining contribution.

NO-GO reversal: NO for both the unified monitor/certify/intervene algorithm and the existing Paper 1 monitoring search. G4 clears this early gate as a distinct Paper 3 theory direction. G2 merits focused theoretical development under the narrower target above. Neither conclusion rehabilitates the previously rejected algorithms.

Additional prior art missing from the dossier, with confidence:

1. Michael Lindon and Nathan Kallus. 2026. “Design-Based Anytime-Valid Inference for Randomized Experiments with Delayed Outcomes and Staggered Entry.” ICML, PMLR 306:75193–75210. High confidence. Directly relevant to G1’s delayed counterfactual inference; it targets cumulative reward realized by calendar time, rather than unrestricted eventual outcomes. [Paper](https://proceedings.mlr.press/v306/lindon26a.html)

2. Tatsuhiro Shimizu, Kazuki Kawamura, Takanori Muroi, Yusuke Narita, Kei Tateno, Takuma Udagawa, and Yuta Saito. 2025. “Off-Policy Evaluation and Learning for the Future under Non-Stationarity.” arXiv:2506.20417. High confidence. Future-value estimation using recurring time features; its bias/variance results are not the proposed anytime prospective certificate. [Paper](https://arxiv.org/abs/2506.20417)

3. Yash Chandak, Shiv Shankar, Nathaniel D. Bastian, Bruno Castro da Silva, Emma Brunskill, and Philip S. Thomas. 2022. “Off-Policy Evaluation for Action-Dependent Non-Stationary Environments.” NeurIPS 35. High confidence on identity and relevance; moderate on complete theorem coverage. OPEN explicitly models active and hybrid nonstationarity through a higher-order stationarity assumption. [Paper](https://papers.nips.cc/paper/2022/hash/3bf80b34f731313b8292f4578e820c90-Abstract-Conference.html)

4. Jean Feng, Alexej Gossmann, Gene Pennello, Nicholas Petrick, Berkman Sahiner, and Romain Pirracchio. 2024. “Monitoring machine learning-based risk prediction algorithms in the presence of performativity.” AISTATS, PMLR 238:919–927. High confidence. Establishes identification conditions for conditional monitoring despite treatment selection; its CUSUM calibration theory is asymptotic, not the proposed paired-harm guarantee. [Paper](https://proceedings.mlr.press/v238/feng24b.html)

5. Yifan Guo. 2026. “Evidence-Gated Research: Statistically Controlled Model Adoption in Adaptive Search.” arXiv:2610.01751. High confidence on stated results. Explicit moving-incumbent adoption control, predictable evidence routing, and conditional-validity assumptions; “persistent” refers to declared environments, not unknown future shifts. [Paper](https://arxiv.org/html/2610.01751)

6. Yonathan Efroni, Nadav Merlis, Aadirupa Saha, and Shie Mannor. 2021. “Confidence-Budget Matching for Sequential Budgeted Learning.” ICML, PMLR 139:2937–2947. High confidence. Hard reward-query budgets, failures of greedy spending under adversity, and regret guarantees; a necessary G4 comparator. [Paper](https://proceedings.mlr.press/v139/efroni21a.html)

7. Jun Geng, Erhan Bayraktar, and Lifeng Lai. 2014. “Bayesian Quickest Change-Point Detection With Sampling Right Constraints.” IEEE Transactions on Information Theory 60(10), DOI:10.1109/TIT.2014.2341607. High confidence. Direct finite-observation-budget detection theory, under known pre/post densities and a Bayesian change-time model. [Author-hosted paper](https://faculty.engineering.ucdavis.edu/lai/wp-content/uploads/sites/38/2021/06/06862025.pdf)

8. Xilin Zhang and Wang Chi Cheung. 2024. “Piecewise-Stationary Bandits with Knapsacks.” NeurIPS 37. High confidence. Inventory reservation with competitive guarantees against a dynamic benchmark; closer to G4’s reserve-exhaustion issue than a generic pacing heuristic. [Paper](https://proceedings.neurips.cc/paper_files/paper/2024/hash/65ae674df2fb642518ae8d2b5435e1b8-Abstract-Conference.html)

9. Giovani Valdrighi, Isabel Valera, and Marcos Medeiros Raimundo. 2026. “Performative Prediction with Selective Labels.” arXiv:2610.08272. High confidence on setting and stated results. Addresses selective observation under deployment-induced distribution change through robust optimization and sensitivity assumptions; it does not supply the proposed sequential harm certificate. [Paper](https://arxiv.org/html/2610.08272)
