# 01 Prior-art matrix (Paper 3 programme)

Date: 2026-11-09. Reviewer: adversarial literature/novelty reviewer (single model family; see `01_REVIEWER_VERDICTS.md`).
This is a bounded audit, not an exhaustive survey. A failed search is not evidence of novelty. Nothing here claims a novel result.

Read-depth labels (honest): **PDF-SKIM** = full PDF downloaded and text-extracted this session, only model/theorem statements and named sections read (not proofs); **ABSTRACT** = landing page abstract only; **SNIPPET** = web-search result text only; **UNRETRIEVED** = no usable content; **R** = relied on an earlier ShiftLab primary-text audit (file cited), not re-read. Per-source notes: `lit_raw/`.

## 1. Source table and verification of the user's triage claims

User label vocabulary (from `00_USER_PRIOR_ART_TRIAGE.md`): covered / conditional / unverified / supported. Column "User claim status" says whether I could verify the *occupancy claim* ("Covers") against the primary source.

| # | Source (bib key) | Retrieval / depth | What the source actually does (as read) | User occupancy claim status | Corrections / caveats |
|---|---|---|---|---|---|
| 1 | Atan & van der Schaar, arXiv 1602.03600 (`atan2016costly`) | PDF-SKIM (v2, 21 Oct 2017) | Contextual MAB with costly observations: learner picks observation set and action; Sim-OOS / Seq-OOS; sublinear regret | **supported** (joint costly observation + online decision + sublinear regret) | v2 header reads "Under review by AISTATS 2018"; stationary-context assumptions not fully extracted. No delay, no hard cap, no risk constraint seen. |
| 2 | Chick, Forster, Pertile, JRSS-B 79(5):1439 (`chick2017bayesian`) | ABSTRACT (OUP page, 100k of 152k chars) + R | Bayesian sequential experiment, delayed endpoint, adoption benefit minus sampling cost, stopping boundaries vs delay | **supported** | **DOI: rssb.12225 is correct.** `rssb.12201` (used in `docs/g1_deadline_aligned_acquisition_kill_v1.md` l.43) is Jiang-Lu-Song-Davidian, an unrelated treatment-regime paper. |
| 3 | Cheng, Zhou, Ji, ICML 2023 (`cheng2023feedback`) | ABSTRACT + PDF extracted + R | Switching-cost online learning with total observation budget B; regret ~ T sqrt(K/B); best-fixed-action comparator | **supported** | oblivious adversary; no delay; no risk event. |
| 4 | Reyzin, Saha, Wu, UAI 2026 (`reyzin2026costly`) | ABSTRACT + PDF-SKIM + R | Expert advice with per-expert observation fees, paid every round, immediate feedback; m-EXP3, m-ELIM | **supported** | Not a hard cap; fixed-expert comparator. |
| 5 | Goebel et al., AAAI-26 (`goebel2026budgeted`) | SNIPPET only (publisher page bot-blocked) | Finite horizon, 2-10 label budget, Hedge for sparse-label regression with episodic priors | **unverified** (metadata only) | Method and assumptions UNRETRIEVED. |
| 6 | Huzaifa et al., WISE-ATTA, arXiv 2609.37687 v3 (`huzaifa2026wise`) | PDF-SKIM Sec 1-3; GitHub page summary | Budget-paced temporal label allocation (confidence proxy, quantile threshold, budget debt) + drift-based sample choice; ImageNet TTA | **supported** (when to spend scarce supervision) | README says WACV 2027; code not inspected. No economic or safety layer seen. |
| 7 | Lamaakal et al., Drift2Act, arXiv 2603.08578 (`lamaakal2026drift2act`) | PDF-SKIM Sec 4 + Thm 1 statement; R (d2a_rar) | Belief over drift types + active anytime-valid window-risk certificate from uniform random delayed labels gating costed interventions | **supported** | Unpaired window risk; workshop paper; Thm 1 is for the sampled window and the proof was not in the extracted text. |
| 8 | Sadeghian et al., RAR, arXiv 2611.02251 (`sadeghian2026rar`) | ABSTRACT + R | Retrain/Alert/Rollback state machine with canary; empirical protocol; does not dominate | **supported** (costs, rollback) | No theorem claimed. Abstract: removing canary raises utility on 11/13 streams. |
| 9 | Gui, Li, Ji, ATTA, ICLR 2024 (`gui2024atta`) | PDF-SKIM (Thm 1-2) | Active learning in TTA; VC bound; SimATTA | supported (scarce supervision in TTA) | The user's triage lists it only in the coordinator's mandatory list. |
| 10 | Regol et al., ICML 2025 (`regol2025retrain`) | PDF-SKIM Sec 3-4 | UPF: Beta forecasts of the model-by-time performance matrix; retrain by quantile of predicted cost; Prop 3.1 bounds number of optimal retrains | **supported** (uncertainty-aware future retraining economics) | Labels assumed present; no query budget; no certificate. The "forward economic certificate" gap is real in my read, but this is a negative-existence statement from one paper. |
| 11 | Gafni, Iyengar, Zeevi, ICML 2026 (`gafni2026cost`) | ABSTRACT + R | Multi-change-point piecewise-IID mean tracking, ATC, minimax lower bound, squared error, full observation | **supported** | No purchased labels, no actions. |
| 12 | Lindon & Kallus, ICML 2026 (`lindon2026design`) | ABSTRACT + R | Design-based CS for delayed outcomes; arm-specific event-time filtration; IPW error not a martingale under any filtration | n/a (not in user table) | Located paper; arXiv 2603.25971. Relevant to pending-label filtrations. |
| 13 | Lopes et al., Sensors 25(9):2787 (`lopes2025cusum`) | SNIPPET only | Meta-model maps series characteristics to CUSUM hyperparameters | **unverified** (metadata only) | MDPI 403, PMC blocked. Authors unknown to me. |
| 14 | Sow et al., CPAL 2024, PMLR 234 (`sow2024meta`) | ABSTRACT | Online meta-learning with task-switch and shift detectors, sublinear task-averaged regret | **supported** at abstract level | Venue is Conference on Parsimony and Learning, not a generic ML venue. Full text UNRETRIEVED. |
| 15 | Chen et al., LEAF, IJCAI-25 (`chen2025leaf`) | ABSTRACT | Two-stage meta-learning for concept drift in online time-series forecasting | supported at abstract level | Forecasting adaptation, not a monitoring/acquisition controller. |
| 16 | Liu et al., TPAMI 2026 (`liu2026tpami`) | **UNRETRIEVED** | unknown | **unverified** | Do not rely on this row; IEEE page returned nothing; search found no matching paper. |
| 17 | Digalakis et al., The Challenger, arXiv 2512.18390 v2 (`digalakis2025challenger`) | PDF-SKIM (Thm 1-2) + R | Irreversible adopt/discard of a challenger; exact finite-horizon stopping; meta-regret n^(2/3) under finite VC, ERM, consistency conditions; sunk evaluation cost | n/a (coordinator list) | Includes data-accumulation-vs-evaluation trade-off in-model; central for candidate E. |
| 18 | Cerqueira et al., KDD'26, arXiv 2606.07789 (`cerqueira2026framework`) | ABSTRACT | Drift-detector benchmark + leave-one-dataset-out hyperparameter protocol | n/a (found by me) | Occupies the LODO *protocol* for detector configs (candidate D). Method section unread. |
| 19 | Podkopaev & Ramdas 2022; Timans et al. UAI 2025; Balachandran DISCERN arXiv 2609.17560; Zhang-Wu-Qian arXiv 2609.13714; Karampatziakis OCS 2021; Conformal Policy Control ICML 2026; Sethi ICML 2026 | R only (repo matrix `docs/research_refinement_v1/PRIOR_ART_AND_NOVELTY_MATRIX.md`; `docs/closest_prior_work.md`; d2a_rar ledger) | certification / promotion / paired monitoring / Markov tests | n/a | Not re-opened here. Zhang-Wu-Qian is ABSTRACT-ONLY in the repo. |

## 2. Findings on the user's triage itself

1. The "NOT NOVEL AS GENERIC PROBLEMS" verdict is supported by sources 1-8, 10 at the level I read them.
2. Two bibliographic corrections: (a) Chick DOI (above); (b) Lindon-Kallus actual title (row 12). Also WISE-ATTA's repo attributes it to WACV 2027 while arXiv v3 lists no venue.
3. Three triage rows could not be verified against primary text: Goebel (metadata only), Lopes (metadata only), Liu (nothing). Their "Covers" cells should be read as UNVERIFIED.
4. Items the triage did not list but which matter: Cerqueira KDD'26 (LODO protocol), Digalakis (data-vs-evaluation trade-off), DISCERN / Zhang-Wu-Qian (certification of a candidate).
5. Repo kill records override: `g1_deadline_aligned_acquisition_kill_v1.md` (deadline alignment = POMDP VOI), `switching_current_regime_evidence_v1.md` (no future-value certificate after unrestricted reversal), `switching_mechanism_screen_v1.md` (bounded-drift age envelope already derived internally), `switching_action_matched_adaptive_acquisition_v1.md`. I did not re-verify these internal documents' proofs.

## 3. Mechanism-by-source occupancy grid (coarse)

Y = source contains the mechanism in its own setting; p = partially / adjacent; - = not seen.

| Mechanism | Atan | Chick | Cheng | Reyzin | WISE | Drift2Act | RAR | Regol | Challenger | Gafni | Lindon |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Jointly choose what to observe and act | Y | Y | p | p | p | Y | - | - | p | - | - |
| Hard total label cap | - | p (max n) | Y | - | Y (fraction) | Y | - | - | - | - | - |
| Label delay | - | Y | - | - | - | Y | Y | - | - | - | Y |
| Switching / retrain cost | - | Y (adopt) | Y | - | - | Y | Y | Y | Y | - | - |
| Reversal / rollback | - | - | Y | - | - | Y | Y | p | - | - | - |
| Time-uniform safety certificate | - | - | - | - | - | Y (unpaired) | - | - | - | p | Y (counterfactual) |
| Future-payback (post-switch) certificate | - | - | - | - | - | - | - | p (forecast only) | p (oracle only) | - | - |
| Cross-stream transfer of controller | - | - | - | - | - | - | - | p (offline history) | - | - | - |
