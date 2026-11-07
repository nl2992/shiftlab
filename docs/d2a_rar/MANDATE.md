# Mandate (user brief, 2026-11-07) — condensed faithfully; formulas preserved

Objective: discover, implement and rigorously evaluate novel algorithmic improvements to SOTA methods
for deploying, replacing, monitoring and rolling back predictive models under costly, limited, delayed
feedback. Goal: defensible ICML methods paper. Narrow well-defined win regions are acceptable; minor
original mechanisms are acceptable if convincingly demonstrated against strong comparators. Nothing may
be fabricated (results, superiority, novelty, code availability).

## Phase 0 — understand prior ShiftLab work
Read AGENTS.md, docs/research_charter.md, protocols, Failure Atlas; branches main,
research/gave-r-2026-11-06, origin/claude/sweet-lovelace-pznpjq, corrected SOTA-comparator branches;
docs/gaver/{90_SUMMARY,10_GAPMIX_RESULTS,20_PAVE_RESULTS,30_FRESHCHECK_RESULTS,50_INTEGRATION_RESULTS}.md.
Import negative findings into a persistent failure ledger. GAVE-R (development only): Gap-Mix beat a
valid Markov-LR comparator in a declared dependence class but failed outside it; PAVE narrow positive at
long delays; FreshCheck did not beat strong rollback comparators; integration interaction negative.
Do not repeat these constructions without a new mechanistic hypothesis.

Mandatory P2 correction: the Atlas sometimes measured marginal-null false promotions for methods whose
guarantees are conditional-null. For d_t = l(I(X_t),Y_t) - l(C(X_t),Y_t) distinguish
- conditional null H0cond: E[d_t | F_{t-1}] <= 0
- marginal null H0marg: E[d_t] <= 0
- absolute-risk requirement R_t <= tau
- economic decision objective (expected deployment value after all costs).
Create a machine-readable null-assumption registry for every baseline and proposed method.

## Phase 1 — reproduce strongest methods first
Each baseline: paper, source status, method spec, evaluation contract, reproducibility record.

A. Drift2Act (highest priority) — "Drift-to-Action Controllers: Budgeted Interventions with Online Risk
Certificates", https://arxiv.org/html/2603.08578 (read Secs 3-5, Alg 1 App B, CS derivation App D).
 A1 belief over D={none,covariate,concept,subgroup}: b~_t(d)=sum_{d'} T_{d'd} b_{t-1}(d');
    b_t(d) ∝ p(z_t|d) b~_t(d).
 A2 certificate U_t(δ)=R^_t + rad(n_t,δ), rad = sqrt(log(π² n²/(6δ))/(2n)) (Hoeffding + summable
    allocation); gate U_t(δ) <= τ else fallback/escalation. Audit exact conditions (uniform random
    sampling from window, bounded means); do NOT assert validity under serial dependence, informative
    selection or arbitrary delayed sampling.
 A3 utility U_t(a) = Δ_t(a) − λ c(a) − γ Viol_t(a), Δ_t(a)=sum_d b_t(d) G(d,a); a_t = argmax over
    feasible actions s.t. label budget sum k_t <= B_lab and intervention cooldowns.
 Reproduce sensing/belief, windowed active auditing, exact certificate+gate, low-cost actions,
 abstention/handoff, retraining, rollback scheduling; delayed labels, cooldowns; native tasks/metrics
 (WILDS Camelyon17, DomainNet, synthetic streams where available). Separate theoretical guarantees from
 empirical claims. Look for author code; else label `PAPER_RECONSTRUCTION`.
 Primary host for Q2 and Q3.

B. RAR — "Retrain, Alert, or Rollback? A Three-Response Decision Framework for Production ML Under
Concept Drift", https://arxiv.org/html/2611.02251 (Secs 3-5, Algs 1-2). States: Serving, Canary-1,
Canary-2, Alert-Hold-Soft, Alert-Hold-Hard. Objective U(π;S)=Σ 1{ŷ_t=y_t} − C_r N_r − C_a N_a − C_b N_b.
 Retrain gates: (1) detector-confirmed drift; (2) label fraction l_t(W_train) >= θ_L (default 0.7);
 (3) Â_pre(t) − Â_cur(t) >= θ_R. Earliest eligible retrain t̂_d + τ + ceil(θ_L W_train) − 1.
 Canary: stage 1 routes fraction p_1 until W_1 labelled routed obs; stage 2 full traffic until W_2;
 old model retained for rollback. Rollback causes: canary failure, data corruption, sanity checks; hold
 state depends on cause. Latency L ≈ max(L_D, τ+θ_L W_train) + (τ + W_1/p_1) + (τ + W_2).
 Limitation: gates don't directly optimise intervention costs -> compare against the paper's
 cost-aware binary baseline, not only unmodified RAR. Reproduce native streams, staged canary, detector
 burn-in, shadow scoring, label-frontier semantics. Find Sec 10 reproducibility artifact; else
 paper-faithful tested implementation. Primary host for Q2/Q3 (canary, retraining economics, delayed
 rollback).

C. The Challenger — https://arxiv.org/html/2512.18390. GSE, OSE, LSE. Value −cnT − c_s + n(T−t)G(t);
 relative to discarding: −c_s + n(T−t)(G(t)−c). Native setting: evolving challenger trained on gradually
 available data — not identical to RAR's repeated drift-response setting.
D. Gong & Zhang ICML 2026, paid observations in contextual bandits,
 https://proceedings.mlr.press/v306/gong26i.html — paid-observation algorithm, free-budget phase
 transition, budget-adaptive meta-controller. Native comparator where feasible + designated
 common-contract adaptation. No fictitious closed forms or guarantees.
E. Active Statistical Inference, Zrnic & Candès ICML 2024, https://arxiv.org/html/2403.03208 —
 prediction-assisted IPW mean estimation; read exact estimator/sampling assumptions before a streaming
 variant. Acquisition/inference comparator, not a full controller.
F. Sethi et al. ICML 2026, https://proceedings.mlr.press/v306/sethi26a.html — α-correct sequential
 tests for ergodic finite-state Markov chains H0∈P vs H1∈Q. Reproduce/adapt under actual assumptions;
 keep ShiftLab Markov-LR, restart, fixed-spacing comparators. Determine whether using P^{g_i} is
 subsumed by existing theory.
Supporting: WATCH (ICML 2025, https://proceedings.mlr.press/v267/prinster25a.html), PPRM (ICML 2026,
https://proceedings.mlr.press/v306/zhang26g.html), ShiftLab H2c, PPRM adapters, RMM, E_rb, Page-CUSUM,
certified deployment gates. Specify which output is comparable (alarm, certificate, label allocation,
retraining, promotion, rollback).

## Phase 2 — benchmark
Suite A native reproduction (original datasets/actions/costs/horizons/feedback/metrics; reproduce a
subset of published numbers first; record discrepancies). Suite B common operational contract:
state S_t=(m_t,b_t,Q_t,H_t, monitor state, available labels); actions query/continue/switch/retrain/
alert/rollback/abstain (method-specific subsets explicit);
J(π)=Σ l_t(π) + c_q N_q + c_s N_s + c_r N_r + c_b N_b + c_a N_a + c_h N_h (charged only for performed
actions; no double counting switch vs retrain; preregistered cost vector; our contract, not a paper's).
Simulator musts: no label before release; explicit request/observation/release/deployment/retrain
clocks; pathwise budget enforcement; pending-label accounting; no future drift identities/labels/eval
losses to policy; identical paired streams/seeds; separate statistical-null truth vs evaluator-only
economic truth; informative missingness & adaptive selection handled; full audit logs; tests that fail
on leakage, budget errors, cost inconsistencies.
Fidelity tiers: AUTHOR_NATIVE, PAPER_RECONSTRUCTION, COMMON_CONTRACT_PORT, CONCEPTUAL_PROXY.

## Phase 3 — questions
Q1 gap-aware evidence: g_i = t_i − t_{i−1}; exact-gap Markov P^{g_i}, envelopes, onset mixtures,
gap-aware statistics. State filtration, transition model, stopping restrictions, parameter
uncertainty, null; the observation mechanism may carry information. Compare vs published Markov tests,
valid Markov-LR, fixed-gap/thinning, restart mixtures w/o gaps, compatible conditional-null certifiers.
Success = more power / lower delay / lower cost at comparable validity.
Q2 decision-valued labels: VOQ_t = Ê[J_t|wait] − Ê[J_t|query] − c_q (ShiftLab proposal). Features:
expected release time, pending inventory, remaining horizon, P(advantage survives to release), budget
shadow prices, certification improvement, value of earlier promotion/rollback, reusable uncertainty,
costs of wrong decisions / unnecessary verification. First replace only the label-request policy inside
an unchanged host. Compare vs Drift2Act active auditing, uniform, front-loaded, ASI-inspired, paid-obs
bandit adaptations, DSS/straddle, PAVE, pending-cap and deadline heuristics. If it doesn't beat a simple
pending cap / fixed schedule: record negative and stop.
Q3 integration: factorial J00 host, J10 +Q1, J01 +Q2, J11 both;
I = (J00 − J11) − [(J00 − J10) + (J00 − J01)]; positive favours synergy. No synergy claim if combo ≈ best
single. Report negative interactions.

## Phase 4 — prior art before substantial implementation
arXiv, PMLR, OpenReview, NeurIPS, JMLR, stats/econometrics, GitHub. Topics: decision-aware active label
acquisition; VOI under delayed feedback; controlled sensing / costly sequential testing; Markov tests
with irregular/adaptive observations; restart-mixture detection; prediction-powered sequential
monitoring; cost-sensitive model replacement; staged deployment/canary; rollback with delayed outcomes;
meta-controllers allocating info+intervention budgets. Per candidate: closest paper+link, overlapping
mechanism, claimed novelty, assumption/guarantee differences, required comparator, status KNOWN /
HIGH_OVERLAP / PLAUSIBLY_DISTINCT / UNVERIFIED. Failed search ≠ novelty.

## Phase 5 — <= 100,000 structured candidate identities (not experiments)
Start from `research/autoresearch_2026_11_07/` scaffold (NOT found on any ref as of 2026-11-07 — build it).
Families: actual-gap evidence; Markov transition uncertainty/envelopes; restart/mixture allocation;
conditional vs marginal objective selection; adaptive query propensities; VOI acquisition; pending-aware
budgets; deadline-aware querying; hazard/regime duration; risk- and cost-aware promotion; cost-aware RAR
Gate-2/3; canary exposure/verification; Drift2Act certification scheduling; action-specific risk
thresholds; predictable stake sizing; replacement economic thresholds; fresh post-switch evidence;
reversal-aware rollback; cooldown/hold release; state-dependent intervention pricing; subgroup safety;
predictive surrogates/control variates; coupled info/intervention budgets; learned/analytic
meta-controllers. Fields: candidate_id, parent_id, host, research_question, scientific_hypothesis,
mechanism, closest_prior_art, target_null, assumptions, configuration, predicted_win_region,
predicted_failure_region, complexity, required_baselines, falsification_test. Dedup by mechanism and
behavioural signature; prioritise documented failure modes over hyperparameter sprawl.

## Phase 6 — autoresearch-style loop (karpathy/autoresearch program.md spirit, not its single-metric rule)
Stage A preflight: source/config hashes, API compat, null eligibility, leakage/release/budget/cost tests,
dedup, reject unsupported adaptations; invalid -> INVALID. Stage B: <= 300 s active compute per
experiment, fixed timeout; frozen light dev suite = correct null + adverse dependence/sampling stress +
one alternative + neighbouring/negative control; shared seeds, fixed workload; log everything; initial
budget 200 experiments then checkpoint review. Stage C: <= ~20 promoted; more seeds/regimes/baselines/
ablations; paired CIs; separated cost components; validity under claimed null; power/delay; robustness;
strongest SOTA host + simple controls. Stage D: <= ~3 frozen finalists; preregister implementation/
version, primary metric/region, baselines+selection, data/seeds/periods, null, confidence, multiplicity
correction, accept/reject, negative controls; untouched sources where possible; never tune on failed
confirmation and relabel.

## Phase 7 — standards
Primary metric J subject to safety constraints. Secondary: false promotion under correct null, safety
violations, power/delay, regret vs admissible oracle, label use/pending utilisation, unnecessary retrain,
canary overhead/rollback latency, compute, robustness. Keep on credible reproducible Pareto improvement
over strong applicable comparator; never compare invalid-aggressive vs valid-conservative as equal. A
narrow claim must survive: strong SOTA comparison, simpler controls, mechanistic ablation, statistical
test, negative/neighbouring controls, independent confirmation, prior-art review. No fixed % bar.

## Phase 8 — ledger
Append-only machine-readable: timestamp, candidate ID, git commit, method/host/fidelity tier, data
hashes, seed group + exposure status, hardware/runtime, null class + assumptions, pre-registered
predictions, results + uncertainty, baseline-relative results, counterexamples, prior-art status,
decision KEEP/DISCARD/CRASH/INVALID/DUPLICATE/UNVERIFIED/CONFIRM. Benchmark definitions and holdout eval
are read-only for method agents; agents must not share holdout outcomes.

## Phase 9 — deliverables (in docs/d2a_rar/)
SOTA_REGISTRY.md, BENCHMARK_CONTRACT.md, BASELINE_REPRODUCTION.md, PRIOR_ART_LEDGER.md,
FAILURE_ATLAS_CORRECTED.md, CANDIDATE_REGISTRY (machine-readable), AUTORESEARCH_PROGRAM.md,
EXPERIMENT_LEDGER, PARETO_AND_ABLATION_REPORT.md, CONFIRMATION_PROTOCOL.md, CONFIRMATION_RESULTS.md,
METHODS_PAPER_DECISION.md. Exit: METHODS_CANDIDATE / BENCHMARK_ONLY / NEGATIVE_RESULT. Never manufacture
a positive result.
