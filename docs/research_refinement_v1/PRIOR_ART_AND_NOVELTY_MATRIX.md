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
| "RADAR" in the brief | No reference given | The best match is Zheng, Wiberg and Zhu (arXiv 2608.29465), with asymptotic, not anytime-valid, guarantees. **Identity is inferred and unconfirmed;** ask the user which RADAR is meant. | `BRIEF.md` |

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
