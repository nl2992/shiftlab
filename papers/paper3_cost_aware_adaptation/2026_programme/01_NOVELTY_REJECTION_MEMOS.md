# 01 Novelty rejection memos (adversarial, per candidate)

Reviewer stance: write the strongest honest rejection first. Classification vocabulary: ALREADY_COVERED / NARROW_OPEN_QUESTION / POTENTIALLY_NEW_ALGORITHM / POTENTIALLY_NEW_THEOREM / EMPIRICAL_BENCHMARK / UNVERIFIED. User-triage label: covered / conditional / unverified / supported. "Occupied" below means "occupied in the sources I read, at the depth recorded in `01_PRIOR_ART_MATRIX.md`". Internal ShiftLab documents are cited as evidence of what the repo already derived or killed; I did not re-prove them.

Common contract (MANDATE.md): two frozen policies, paired loss Z_t, hard pathwise label cap B with pending reservation, delay d, query price c_q, switch cost k, optional compute and retrain cost, reversible deployment, conditional-null false-promotion control.

---

## A. Joint action-conditioned value of information (QVOI / risk-envelope two-law / dual price / learned continuation / ranking-reversal lookahead)

**Mechanism.** Choose (a_t, q_t, u_t) from the observed history by (A1) a one-step-lookahead value of a query that accounts for the pending queue, (A2) a two-law (null-law vs alternative-law) risk envelope that keeps the global false-promotion probability <= alpha while optimizing expected net cost, (A3) a Lagrange price on label budget/risk, (A4) a learned continuation value behind an external gate, (A5) a lookahead that anticipates ranking reversals.

**Nearest sources.** Atan & van der Schaar 2016 (joint observation+action, regret); Chick-Forster-Pertile 2017 (delayed, costed, adopt/continue Bellman); Cheng-Zhou-Ji 2023 (hard observation budget + switching cost, minimax); Drift2Act 2026 (budgeted interventions + anytime certificate + delay); Reyzin et al. 2026 (cost-adaptive allocation). Internal: `g1_deadline_aligned_acquisition_kill_v1.md`, `switching_two_law_game_duality_v1.md`, `switching_constrained_control_prior_v1.md`, `switching_ccpomdp_approximation_audit_v1.md`.

**What differs vs mere state augmentation.** The queue of pending releases, remaining budget, current deployment and risk spent are all observable state; the Bellman recursion on that state is textbook controlled-POMDP/CPOMDP. The global alpha-risk constraint is *not* a local Bellman threshold, which is why the repo moved to a constrained/sequence-form game. That moves A2 from "state augmentation" to "constrained POMDP with a non-additive risk event", but constrained POMDPs with such constraints are an established formulation (repo audits), so the only possibly new object is a tractable approximation with a proved gap.

**Classification.** NARROW_OPEN_QUESTION for the tractable-approximation-with-bound reading of A2; ALREADY_COVERED for A0, A1, A3, A5 as generic control. User label: **covered** (generic) / **conditional** (A2 guarantee). Empirical headroom is refuted by repo data (MANDATE "settled findings": fixed calendar exactly optimal at alpha .05, B<=4; joint planner gap 0.7-1.2% at alpha .10, B=4; 12 mechanisms tie tuned Wald).

**Shortest kill (reduction to prior).** Augment the state with (posterior, deployment, pending-release queue, budget, risk-spent); the problem is a finite-horizon (C)POMDP; any heuristic is bounded by its exact oracle, and the oracle is at most 1.2% better than a calendar plus tuned Wald in the cells already run. Hence A = {Chick-style Bellman} + {state augmentation} + {empirically negligible headroom}.

**Minimal survival requirement.** One of: (i) a *tractable* controller with a proved constant-factor or additive gap to the exact constrained oracle on a family where the calendar is provably suboptimal by a margin >= 3% (meaningful, per the user's grading) and where tuned Wald fails; (ii) an exact separation theorem (a family of instances where every calendar-plus-threshold rule has regret Omega(.) that the controller avoids) with an executable counterexample. Absent (i) or (ii), classify A as baseline/ablation material only.

---

## B. Future payback certification (bounded drift, dwell time, (B,d,h,Delta,k) bounds)

**Mechanism.** Certify, time-uniformly and under optional continuation, that switching to the challenger will have positive net value over a horizon h: sum of future Z_t (net of switch cost k) > 0, using only labels already released, under an explicit persistence assumption (bounded drift rate, minimum dwell time, or bounded variation Delta of the mean of Z). Lower and upper bounds in (budget B, delay d, horizon h, variation Delta, cost k) on the achievable detection/regret.

**Nearest sources.** Chick et al. 2017 (stationary Bayesian payoff over remaining horizon); Challenger 2025 (switch rule vs oracle stopping; irreversible); Regol et al. 2025 (forecast of future model performance under uncertainty, no guarantee on forward value); Gafni et al. 2026 (multi-change-point cost-of-learning lower bounds, full observation); Lindon-Kallus 2026 (calendar-time CS under delay); Drift2Act (certifies *current* window risk only). Internal: `switching_current_regime_evidence_v1.md` (impossibility after unrestricted reversal), `switching_mechanism_screen_v1.md` (age-corrected Hoeffding envelope already derived; "not novel alone"), `switching_budget_delay_lower_bound_v1.md`, `switching_reversal_lp_certificate_v1.md`, `switching_asymmetric_timing_certificate_protocol_v1.md` (internal; not re-read). Non-stationary-bandit variation-budget literature (named from memory, **not fetched**) is the likely classical antecedent for Delta-type assumptions.

**What differs vs mere state augmentation.** The target is a *forward-looking functional* (future mean of Z) rather than a current-window risk. That is a genuinely different estimand from Drift2Act/Podkopaev-Ramdas, but obtaining it requires a persistence assumption; the assumption is where all the content lies. A bound that is a function of (B,d,h,Delta,k) is a quantitative restatement unless it comes with a matching lower bound. Adding delay d to a fixed-sample confidence set is state augmentation (age correction).

**Classification.** POTENTIALLY_NEW_THEOREM (conditional on matching lower bound and on novelty versus variation-budget results, which I did not retrieve). User label: **conditional**. Fatal exposure: the internal bounded-drift envelope is already derived and flagged "not novel alone".

**Shortest kill.** Z_t with bounded variation Delta over horizon h: a Hoeffding/empirical-Bernstein CS on a window of age-corrected labels bounds the current mean up to Delta*age; payback over h follows by adding Delta*h/2. Time-uniformity by stitching/union. Delay d adds an age term. So the certificate = prior CS + variation slack; the lower bound is a standard two-point (Le Cam) argument with changing means.

**Minimal survival requirement.** A *matching* (up to constants/logs) lower bound in at least three of (B,d,h,Delta,k) that is not implied by Cheng/Gafni-style bounds, together with (a) an explicit counterexample showing an optional-continuation failure of the naive batch rule (the B2 claim) and (b) a controlled simulation where the certificate is non-vacuous at realistic Delta and where a naive current-regime hurdle (B0) and a Bayes-known-model planner both lose economically. If only the upper bound is delivered, drop to ALREADY_COVERED (envelope + CS).

---

## C. Dependence-aware failure atlas and alarm-vs-economic ranking inversions

**Mechanism.** A taxonomy of failure modes of monitors/controllers under temporal dependence and non-i.i.d. shift, with a diagnostic showing that alarm-quality metrics (detection delay, false alarms, AUROC) order methods differently from net economic cost, plus an attributable repair.

**Nearest sources.** Ahmed et al. 2026 (Frontiers in AI; systematic audit of label-free monitoring/TTA failures on temporal shift, via `docs/closest_prior_work.md`, R); Cerqueira et al. KDD'26 (timing-aware drift-detector benchmark; ABSTRACT only); Podkopaev-Ramdas / Timans (validity under dependence; R); RAR 2026 (utility vs detector triggers, does not dominate); Regol et al. 2025 (detector-triggered retraining is dominated once costs are accounted for: their motivation). Internal: `failure_atlas_dependence_prior_art_v1.md`, MANDATE note that Failure Atlas v2 headline numbers need the DISCERN variance / psi_E fidelity fix and dependence-safety caveats.

**What differs vs state augmentation.** "Alarm metric vs cost ranking differ" is a known qualitative lesson (RAR, Regol). What could be new is a *causally isolated mechanism* (one factor toggled, others fixed) and a protocol that is source-faithful across several methods. That is design/measurement novelty, not a new algorithm.

**Classification.** EMPIRICAL_BENCHMARK. User label: **unverified** (novel benchmark) / **conditional** (needs a previously unreported isolated mechanism). Not a theorem.

**Shortest kill.** (1) Ahmed et al. + Cerqueira KDD'26 occupy "systematic audit of monitors under temporal shift with timing-aware evaluation". (2) Ranking inversion between detection metrics and economic cost is the stated motivation of cost-aware retraining papers. (3) Repo's own atlas numbers are currently not clean (fidelity fix pending), so any inversion headline is an unvalidated internal result.

**Minimal survival requirement.** After the fidelity fix: a pre-registered factorial where exactly one dependence factor (e.g., autocorrelation of loss differences or label-arrival clustering) is toggled, with >=3 source-faithful methods whose null validity is verified, demonstrating an inversion with a CI excluding 0 and an attributable repair that removes the inversion; plus at least one real stream (exploratory, dev-exposed per MANDATE).

---

## D. Cross-stream transfer of monitoring/acquisition/intervention parameters (learned controller, strict leave-family-out)

**Mechanism.** Learn a map from stream meta-features (or a recurrent encoder of the observed history) to controller parameters (thresholds, query rates, switch hurdles) using many streams; evaluate on held-out families at identical label cost; guard against negative transfer.

**Nearest sources.** Lopes et al. 2025 (meta-recommendation of CUSUM hyperparameters; SNIPPET only); Cerqueira et al. KDD'26 (leave-one-dataset-out hyperparameter protocol for drift detectors; ABSTRACT only); Sow et al. 2024 (online meta-learning with task-boundary detection); Chen et al. IJCAI 2025 (meta-learning for forecasting drift); Regol et al. 2025 (uses offline model/data history to forecast); Pattern Recognition 2023 meta-learned active-learning threshold (SNIPPET only; not in the mandatory list). Internal: `switching_transport_acquisition_candidate_v1.md` (not re-read), MANDATE "12 mechanisms tie tuned Wald".

**What differs vs state augmentation.** The parameter space here is the economic controller (query rate, hurdle, dwell), not detector hyperparameters. But the learning problem is hyperparameter meta-recommendation with a changed objective. The meta-feature is state augmentation.

**Classification.** EMPIRICAL_BENCHMARK (with a thin NARROW_OPEN_QUESTION on risk-preserving transfer). User label: **conditional** (needs LODO vs direct meta-recommendation, hierarchical pooling, per-domain tuning, expert tracking). Note: the LODO protocol itself is published (Cerqueira, abstract-level).

**Shortest kill.** If the controller family has a low-dimensional parameter vector (threshold, rate, hurdle), a transfer method is meta-recommendation of that vector (Lopes-type) evaluated under LODO (Cerqueira-type). Repo evidence that tuned-Wald ties 12 mechanisms implies that a per-family tuned threshold is near the achievable frontier, leaving little for transfer to add beyond tuning cost.

**Minimal survival requirement.** A strict leave-family-out result (disjoint families, parameters frozen before held-out access) where the transferred controller is within noise of per-domain tuning *at zero tuning labels* and beats a pooled single default by a meaningful margin (>=3% with CI excluding 0), together with a demonstrated negative-transfer case and its detector; ideally a bound on regret vs the best fixed parameter as a function of source-family diversity. GPU use is allowed but unnecessary for a low-dimensional map; a gradient-boosted or ridge baseline must be run first.

---

## E. (Reviewer-proposed) Dual-use labels: a challenger trained and certified from the same scarce labels under a joint label+compute budget

**Mechanism.** The label budget B funds both (i) training/fine-tuning a challenger and (ii) the evidence that certifies promotion. Labels used to fit the challenger make the challenger data-dependent, so a naive e-process on the same labels is invalid, while a hard split wastes labels. The question: given pathwise cap B, delay d, switch cost k and compute cost, choose the label allocation/schedule (train-only, certify-only, and prequential test-then-train labels) and the promotion rule so that (1) promotion is anytime-valid for the *final* frozen candidate being promoted, and (2) expected net cost is minimized. Compute enters as a second budget (each retrain consumes u).

**Nearest sources.** Digalakis et al. 2025 (Challenger): data accumulation for the challenger vs evaluation cost are *in the model*; irreversible; no hard label cap; no certificate. DISCERN arXiv 2609.17560 (R): certification of a *given* candidate with label cost, no training. Zhang-Wu-Qian arXiv 2609.13714 (ABSTRACT-ONLY, R): search/evaluation separation with incumbent fallback. Schirmer et al. NeurIPS 2025 (R via `closest_prior_work.md`): risk monitoring of online-updated models (the running-candidate analogue). Regol et al. 2025: retraining economics under limited data. Karampatziakis OCS 2021 / Conformal Policy Control (R): gating with a safe reference. Sample-splitting / cross-fitting / learn-then-test are classical (not fetched here).

**What differs vs state augmentation.** Adding counters n_train, n_cert to the state is state augmentation. What is *not* mere augmentation is the validity question: certification of a candidate whose training set overlaps the evidence. Prequential (test-then-train) evaluation is valid for the *running* predictable candidate sequence, but the object promoted is a frozen final model, which is not the object tested. That gap (running vs final candidate) is the open statistical content, if any.

**Classification.** NARROW_OPEN_QUESTION, with a possible POTENTIALLY_NEW_THEOREM if a validity/efficiency separation exists; currently UNVERIFIED because my retrieval for this specific combination was a single bounded search and several adjacent sources (DISCERN, Zhang-Wu-Qian, Schirmer) were not re-read. User label: **not in user's triage** (new); treat as **unverified**.

**Shortest kill.** (1) Prequential/test-then-train makes label reuse statistically free: evaluate candidate f_{t-1} (F_{t-1}-measurable) on label t, then train on it; the e-process is valid for the running sequence (Schirmer/Podkopaev-Ramdas-style predictable predictors). (2) Promote the last running model and certify *it* by continuing the e-process after promotion. Then E reduces to the existing "certify a predictable candidate" problem plus Challenger's data-vs-evaluation trade-off, and the allocation is a one-dimensional dynamic program (state augmentation).

**Minimal survival requirement.** One controlled separation: a synthetic family (with oracle truth held only on the evaluator side) where (a) prequential certification of the running candidate promotes a final candidate that is harmful with probability > alpha under a stated conditional null (i.e., an explicit counterexample to the "promote last running model" shortcut), or where it yields a certificate for the wrong estimand under shift; and (b) a valid split/cross-fit scheme restores validity and the optimal budget split beats both a fixed 50/50 split and always-train in net cost by >= 3% at CI excluding 0. If (a) fails, E collapses into Challenger + Schirmer and is classified ALREADY_COVERED.

---

## Cross-candidate summary

| Cand | Classification | User label | One-line kill | Residue that could survive |
|---|---|---|---|---|
| A | NARROW_OPEN_QUESTION (A2 only); rest ALREADY_COVERED | covered / conditional | augmented-state (C)POMDP + negligible headroom (<=1.2%) | tractable controller with proved gap on a calendar-suboptimal family |
| B | POTENTIALLY_NEW_THEOREM (conditional) | conditional | CS + variation slack; internal envelope exists | matching lower bound in (B,d,h,Delta,k) + optional-continuation counterexample |
| C | EMPIRICAL_BENCHMARK | unverified / conditional | Ahmed + Cerqueira occupy audits; atlas numbers unfixed | single-factor isolated inversion + repair, after fidelity fix |
| D | EMPIRICAL_BENCHMARK | conditional | meta-recommendation + published LODO; tuned-Wald ties | strict LOFO vs tuning, negative-transfer detector |
| E | NARROW_OPEN_QUESTION / UNVERIFIED | unverified (new) | prequential reuse is free; Challenger models data-vs-eval | running-vs-final candidate counterexample + budget-split separation |
