"""Writes docs/paper1_scale25/baseline_fidelity.csv (14 published-method adapters + 4 new paper-formula ports).

Every field is a statement made in docs/paper1_scale25/05_BASELINE_FIDELITY.md. paper_verified = the arXiv/PMLR page
(or PDF text) was opened in this workstream on 2026-11-09; code_verified = the repository page was opened.
"""

import csv
from pathlib import Path

OUT = Path(__file__).resolve().parents[3] / "docs/paper1_scale25/baseline_fidelity.csv"
COLS = [
    "panel_id", "registry_names", "source_citation", "paper_verified", "venue_status", "author_code",
    "code_verified", "original_problem_and_feedback", "what_the_adapter_changes",
    "hparam_space_and_selection", "parity_evidence", "fidelity_class", "guarantee",
    "matched_cutoff_wrapper_safe", "notes",
]  # fmt: skip
R: list[dict] = []


def add(**k):
    R.append({c: k.get(c, "") for c in COLS})


add(
    panel_id="A01",
    registry_names="qiu_delayed_movement",
    source_citation="Qiu, Jacobsen, Esposito, Zhang. Parameter-free Dynamic Regret: Time-varying Movement Costs, Delayed Feedback, and Memory. arXiv:2602.06902",
    paper_verified="yes (abs page)",
    venue_status="arXiv comments: v2 listed as ICML 2026 (28 pages); not independently confirmed on PMLR",
    author_code="none listed on arXiv page",
    code_verified="n/a",
    original_problem_and_feedback="Unconstrained online convex optimisation, comparator-adaptive dynamic regret, time-varying movement costs; delay and memory reduced to movement costs. Full information, no label acquisition, no budget, continuous actions.",
    what_the_adapter_changes="Replaces the OCO learner by a blocked fixed-share Hedge over two models on importance-weighted differences, block L=max(delay+1,T/20), hand-set eta and share; ignores c_s; uses public delay.",
    hparam_space_and_selection="none (single default)",
    parity_evidence="none possible (no code; the paper's algorithm is not implemented)",
    fidelity_class="inspired heuristic",
    guarantee="none transferred",
    matched_cutoff_wrapper_safe="yes",
    notes="Name overstates fidelity; report as Qiu-style Hedge adapter.",
)
add(
    panel_id="A02",
    registry_names="gong_zhang_paid_obs",
    source_citation="Gong, Zhang. The Cost of Information: Phase Transitions in Contextual Bandits with Paid Observations. ICML 2026, PMLR 306:36013-36044",
    paper_verified="yes (PMLR page; full-text pdftotext: Algorithms 1-2, Theorem 3.2, switching-cost discussion located)",
    venue_status="PMLR v306 (ICML 2026) confirmed",
    author_code="none (PMLR page links only the proceedings metadata repo)",
    code_verified="yes",
    original_problem_and_feedback="Adversarial contextual bandit with paid observation of actions, regret = learning loss + observation cost; free-observation budget with a phase transition; meta-controller (Alg. 2) selects algorithms by budget regime; EXP4-style importance-weighted estimators (Alg. 1). Switching cost appears only as a technique/analogy to bandits with switching costs. No delay, no deployment payback rule.",
    what_the_adapter_changes="The whole decision rule is a repo invention: discounted importance-weighted point-estimate payback (T-t)*s_hat/den > c_s with symmetric switch-back; paced disagreement acquisition; uses public delay for the discount and normaliser.",
    hparam_space_and_selection="default untuned; tuned family in A03/A04",
    parity_evidence="none possible (the source has no payback rule)",
    fidelity_class="inspired heuristic",
    guarantee="none",
    matched_cutoff_wrapper_safe="yes",
    notes="Equivalent to a point-estimate economic switcher: the right ablation for the quantile hurdle, not a comparison to the paper.",
)
for pid, nm, sel in (
    ("A03", "gongT_w100_m10", "synthetic-dev winner (D3 seeds, in-sample)"),
    (
        "A04",
        "gongT_w800_m20",
        "real-dev winner on 14 exposed pilot streams (grid edge W=800, m=20)",
    ),
):
    add(
        panel_id=pid,
        registry_names=nm,
        source_citation="as A02",
        paper_verified="yes",
        venue_status="as A02",
        author_code="none",
        code_verified="yes",
        original_problem_and_feedback="as A02",
        what_the_adapter_changes="A02 plus window gamma=1-1/W and an additive margin m on c_s",
        hparam_space_and_selection=f"grid W in {{100,200,400,800}} x m in {{0,5,10,20}} = 16; selected: {sel}",
        parity_evidence="none possible",
        fidelity_class="inspired heuristic",
        guarantee="none",
        matched_cutoff_wrapper_safe="yes",
        notes="Dev-tuned; the untuned Qiu/CAMS/MP/MS/LLM/VMin/ARW entries get no tuning (asymmetry, see 05 section 6).",
    )
for pid, nm, sel in (
    ("A05", "upf_d0.95_m50", "synthetic-dev winner"),
    ("A06", "upf_d0.8_m50", "real-dev winner"),
):
    add(
        panel_id=pid,
        registry_names=nm,
        source_citation="Regol, Schwinn, Sprague, Coates, Markovich. When to retrain a machine learning model. ICML 2025, PMLR 267:51369-51404; arXiv:2505.14903",
        paper_verified="yes (arXiv abs + PMLR page; equations from the earlier repo audit that read the HTML)",
        venue_status="PMLR v267 confirmed (ICML 2025)",
        author_code="none (PMLR page links only the proceedings metadata repo)",
        code_verified="yes",
        original_problem_and_feedback="Retrain-or-keep at each step by comparing delta-quantiles of remaining-horizon cost including retraining cost; forecasts a bounded performance metric with a regression forecaster and a Beta model (Eqs. 3, 15-20); full period data, no label budget, no delay, one-directional.",
        what_the_adapter_changes="Keeps the Eq. 16-20 decision structure (strict delta-quantile of switch-cost-to-go vs keep, backward recursion) but: two frozen models, reversible, IPW period cells on disagreement rounds, weaker regressor (arm and time only), added HT variance, periods of m rounds (T multiple of m), warm-up of 3 periods, label price ignored.",
        hparam_space_and_selection=f"delta in {{.5,.8,.95}} x m in {{50,100,200}} = 9; selected: {sel}",
        parity_evidence="T2 maths port exists (needs torch); T3 adapter has 11 unit tests; no author code to run",
        fidelity_class="common-contract adaptation",
        guarantee="none (nested quantiles not coherent; Prop. 3.1 as printed is false per repo ledger)",
        matched_cutoff_wrapper_safe="yes",
        notes="Single most important comparator for the quantile claim. arXiv abstract says 7 datasets (earlier repo notes said 6).",
    )
for pid, nm, sel in (
    ("A07", "chalgse_l1.0_g0.2", "nominal/synthetic default"),
    ("A08", "chalgse_l0.9_g0.3", "real-dev winner"),
):
    add(
        panel_id=pid,
        registry_names=nm,
        source_citation="Digalakis Jr, Perignon, Saurin, Sentenac. The Challenger: When Do New Data Sources Justify Switching Machine Learning Models? arXiv:2512.18390 (v2 16 Jul 2026)",
        paper_verified="yes (abs page this session; algorithm details from the earlier audit that read 100k of 219k chars of the HTML)",
        venue_status="no venue listed",
        author_code="none",
        code_verified="yes (page lists none)",
        original_problem_and_feedback="Finite-horizon optimal stopping: a challenger trained on a growing dataset with a power-law learning curve; per-sample cost c, one-time switching cost c_s; irreversible; algorithms GSE (Hoeffding half-width), OSE (one-shot near T^{2/3}), LSE (local learning-curve slope; the headline algorithm of the v2 abstract). No label budget, no delay, no paired disagreement evidence.",
        what_the_adapter_changes="Irreversible Hoeffding-lower-bound payback on EQSDp's discounted evidence clock with EQSDp's pacing; learning-curve machinery dropped; LSE not implemented.",
        hparam_space_and_selection=f"lambda in {{1,.97,.9}} x gamma in {{.1,.2,.3,.45}} = 12; selected: {sel}",
        parity_evidence="none; no dedicated test file",
        fidelity_class="inspired heuristic",
        guarantee="none",
        matched_cutoff_wrapper_safe="yes",
        notes="Closest published relative of payback with a confidence bound; shares the payback inequality -c_s + n(T-t)(G-c).",
    )
add(
    panel_id="A09",
    registry_names="cams_adapter",
    source_citation="Liu, Xia, Stevens, Chen. Contextual Active Model Selection. arXiv:2207.06030 (v4 9 Feb 2025); NeurIPS 2024 per repo ledger",
    paper_verified="yes (abs + HTML: Figure 1 pseudocode, Eq. 4, Theorems 1-4)",
    venue_status="arXiv page lists no venue; NeurIPS 2024 is the repo ledger's statement, unverified here",
    author_code="github.com/xuefeng-cs/Contextual-Active-Model-Selection (1 commit, no licence shown; task scripts + advice matrices, policy training absent)",
    code_verified="yes (repo page)",
    original_problem_and_feedback="Online contextual active model selection: context x_t, choose a model, optionally query the label; hard query budget b is native (C_t<=b); exponential weights over policies Pi* = Pi + constant policies; stochastic branch recommends argmax, adversarial branch samples; immediate labels; no switching cost.",
    what_the_adapter_changes="Constant policies only (streams have no features), so the contextual part is unused; delayed labels via issue-time E and u_t; argmax deployment (the paper's stochastic recommendation); query 0 in the agreement region and when a class mass rounds to 0 (code); eta=sqrt(P/t) (code) vs sqrt(ln m/t) (paper).",
    hparam_space_and_selection="none",
    parity_evidence="This WS: E(y_hat,w) equals the repo weighted_entropy_query for two classes (test); the gaps in eta, agreement floor and rounding are asserted by tests. Author code not run.",
    fidelity_class="common-contract adaptation",
    guarantee="none transferred",
    matched_cutoff_wrapper_safe="yes",
    notes="Paper-formula variants cams_paper / cams_paper_gated added (P03/P04).",
)
add(
    panel_id="A10",
    registry_names="model_selector_causal",
    source_citation="Okanovic, Kirsch, Kasper, Hoefler, Krause, Gurel. All models are wrong, some are useful: Model Selection with Limited Labels. arXiv:2410.13609 (v2 24 Oct 2024); AISTATS 2025 per repo ledger",
    paper_verified="yes (abs page)",
    venue_status="arXiv page lists no venue; AISTATS 2025 is the repo ledger's statement, unverified here",
    author_code="github.com/RobustML-Lab/model-selector (4 commits, no licence shown)",
    code_verified="yes (repo page)",
    original_problem_and_feedback="Pool-based: choose a small set of informative unlabeled examples (greedy expected-posterior-entropy), then pick the model with best labelled accuracy; immediate oracle, fixed pool, no switching cost, no stream.",
    what_the_adapter_changes="Pool replaced by a sliding record gate over eligible disagreements (window 50) with pacing ceil(B(t+1)/T); labelled-set-accuracy deployment; probability reported as 1; with 2 models and 2 classes it reduces to paced disagreement sampling.",
    hparam_space_and_selection="none",
    parity_evidence="native pool port exists; author-parity tests skip (vendor dir empty); not re-verified this session",
    fidelity_class="inspired heuristic",
    guarantee="none",
    matched_cutoff_wrapper_safe="NO (pool.pop at request time; a vetoed request must be re-inserted)",
    notes="Tests the deployment rule, not the sampling idea.",
)
add(
    panel_id="A11",
    registry_names="model_picker_adapter",
    source_citation="Karimi, Gurel, Karlas, Rausch, Zhang, Krause. Online Active Model Selection for Pre-trained Classifiers. AISTATS 2021, PMLR 130:307-315; arXiv:2010.09818",
    paper_verified="yes (PMLR + arXiv abs; Algorithm 1 and Eq. 1 read from the PDF text)",
    venue_status="PMLR 130 confirmed (AISTATS 2021)",
    author_code="github.com/DS3Lab/online-active-model-selection (195 commits; licence not shown; src/methods/model_picker.py)",
    code_verified="yes (repo page; function described by the fetch tool, arithmetic matches the port; file not executed)",
    original_problem_and_feedback="Stream of unlabeled examples, k pre-trained classifiers; sample I_t ~ w_t as the prediction, recommend argmax w_t; query with probability q_t=max{v,eta_t} (v=max_c Var); importance-weighted loss; eta_t=sqrt(ln k/(2t)); immediate labels; the paper has no hard budget (the code only stops recording); no switching cost.",
    what_the_adapter_changes="Delayed labels (issue-time q_t), hard cap by the simulator, deploys the paper's recommendation argmax w_t (incumbent on ties) rather than sampling I_t.",
    hparam_space_and_selection="none (tuning_par=1.0)",
    parity_evidence="This WS: a paper-formula implementation agrees with the repo port on eta_t, w_t, q_t over random inputs and replays the native trajectory exactly (tests); author code read via fetch (formulas match) but NOT executed",
    fidelity_class="common-contract adaptation",
    guarantee="none transferred (Theorem 1 is for sampled predictions with immediate labels)",
    matched_cutoff_wrapper_safe="yes",
    notes="Argmax deployment is the paper's own recommendation output, so the adapter is closer to the source than earlier audits implied; the source action rule (sampling) is cost-infeasible (P02).",
)
add(
    panel_id="A12",
    registry_names="online_llm_picker",
    source_citation="Turrin, Okanovic, Hoefler, Gurel. Which LLM to pick? Online Active Model Selection for Large Language Models. arXiv:2610.01592 (v1 1 Oct 2026)",
    paper_verified="yes (abs page)",
    venue_status="no venue listed",
    author_code="none",
    code_verified="yes (page lists none)",
    original_problem_and_feedback="Stream of prompts, 130+ LLMs, similarity-based loss, limited annotation budget (expected proportion); identify the best or a near-best model; no switching cost, no delay stated.",
    what_the_adapter_changes="Exact-agreement 0/1 loss; hard cap; eps=1e-8 in eta_t is ours (unrecoverable from the text); with 2 models the variance score carries no instance information.",
    hparam_space_and_selection="none",
    parity_evidence="formulas quoted from the paper full text by an earlier session; not re-verified here; 13 unit tests",
    fidelity_class="common-contract adaptation",
    guarantee="none",
    matched_cutoff_wrapper_safe="yes",
    notes="Burns budget early at m=2 (queries every disagreement in burn-in).",
)
add(
    panel_id="A13",
    registry_names="variance_min_ipw",
    source_citation="Hara, Matsuura, Honda, Ito. Active Model Selection: A Variance Minimization Approach. Machine Learning 113 (2024), doi:10.1007/s10994-024-06603-1",
    paper_verified="partial (search listing of the Springer / mlanthology pages; the paper was not opened)",
    venue_status="CORRECTION: earlier repo audits wrote 'ACML 2024 / Machine Learning 2024'. The journal record is Machine Learning vol. 113; the repo README says it appears at ACML 2024 (journal track)",
    author_code="github.com/sato9hara/active-model-selection (MIT licence, 2 commits)",
    code_verified="yes (repo page)",
    original_problem_and_feedback="Pool-based: query distribution minimising the variance of a LURE estimator of the loss difference between models (active testing framework); no delay, no switching cost.",
    what_the_adapter_changes="Streaming score 1[disagree]+eps, running-mean normaliser, rate B/T, Horvitz-Thompson estimator instead of LURE; class_prior [.5,.5]; deploy argmin HT loss; no cost awareness.",
    hparam_space_and_selection="none",
    parity_evidence="4 author-parity tests skip (the author code needs numba)",
    fidelity_class="inspired heuristic",
    guarantee="none",
    matched_cutoff_wrapper_safe="yes",
    notes="Class docstring: NOT the published method.",
)
add(
    panel_id="A14",
    registry_names="han_arw_label_clock",
    source_citation="Han, Huang, Wang. Model Assessment and Selection under Temporal Distribution Shift. ICML 2024 (PMLR 235); arXiv:2402.08672",
    paper_verified="yes (arXiv abs + repo README)",
    venue_status="arXiv page: 26 pages, 6 figures, 4 tables, no venue; repo README states ICML 2024",
    author_code="github.com/eliselyhan/ARW (32 commits; ARW.py has ARWME (Alg 1) and tournament_selection (Alg 3); no licence shown)",
    code_verified="yes (repo page)",
    original_problem_and_feedback="Batched periods of labelled data under temporal shift; adaptive rolling window (Goldenshluger-Lepski bias/variance proxy) for generalisation error at one target time; pairwise comparison in a single-elimination tournament; no selective sampling, no delay, no switching cost.",
    what_the_adapter_changes="One period per delivered label in delivery order, pairwise comparison with tie to incumbent, margin 0, shared pacer, no IPW.",
    hparam_space_and_selection="none (theory constants)",
    parity_evidence="T2 mathematical port from printed equations; author code (Alg 1 ARWME) not run; 15 unit tests",
    fidelity_class="common-contract adaptation",
    guarantee="none (no false-promotion guarantee; the oracle inequality is for one fixed t)",
    matched_cutoff_wrapper_safe="yes",
    notes="Flips on noise at margin 0 (13+ switches); its -14.2% panel gap reflects missing cost awareness, not an estimator fault.",
)
add(
    panel_id="P01",
    registry_names="mp_paper_recommend",
    source_citation="as A11",
    paper_verified="yes",
    venue_status="as A11",
    author_code="as A11",
    code_verified="yes",
    original_problem_and_feedback="as A11",
    what_the_adapter_changes="Delay (IW at release), simulator hard cap, incumbent kept on exact ties; everything else is Algorithm 1 as printed (no tuning constant).",
    hparam_space_and_selection="none",
    parity_evidence="14 tests in scripts/paper1_scale25/baselines/test_paper_ports.py: paper formulas vs author-code port; identification sanity check",
    fidelity_class="source-faithful (decision rule and constants as printed; feedback adaptations declared)",
    guarantee="none transferred",
    matched_cutoff_wrapper_safe="yes",
    notes="New in this workstream.",
)
add(
    panel_id="P02",
    registry_names="mp_paper_sample",
    source_citation="as A11",
    paper_verified="yes",
    venue_status="as A11",
    author_code="as A11",
    code_verified="yes",
    original_problem_and_feedback="as A11",
    what_the_adapter_changes="as P01 but acts by I_t ~ w_t exactly as Algorithm 1; pays c_s on every draw change.",
    hparam_space_and_selection="none",
    parity_evidence="as P01; sf_311 smoke (3 episodes x 2 seeds): about 140 switches, net about 1159 vs about 476 for P01",
    fidelity_class="source-faithful (action rule as printed)",
    guarantee="none transferred",
    matched_cutoff_wrapper_safe="yes",
    notes="Infeasible under c_s=5: a fidelity reference, not a competitive baseline.",
)
add(
    panel_id="P03",
    registry_names="cams_paper",
    source_citation="as A09",
    paper_verified="yes",
    venue_status="as A09",
    author_code="as A09",
    code_verified="yes",
    original_problem_and_feedback="as A09",
    what_the_adapter_changes="Constant policies only; delay via issue-time z_t; the paper's z_t=max{1/sqrt(t),E} including the agreement region; eta=sqrt(ln m/t); argmax recommendation; hard budget by the simulator.",
    hparam_space_and_selection="none",
    parity_evidence="tests: E equals the repo for two classes; paper-vs-code gaps asserted",
    fidelity_class="source-faithful (stochastic branch, constant policies; contextual part absent)",
    guarantee="none transferred",
    matched_cutoff_wrapper_safe="yes",
    notes="Spends about 1/sqrt(t) of the budget on agreement events (paper rule).",
)
add(
    panel_id="P04",
    registry_names="cams_paper_gated",
    source_citation="as A09",
    paper_verified="yes",
    venue_status="as A09",
    author_code="as A09",
    code_verified="yes",
    original_problem_and_feedback="as A09",
    what_the_adapter_changes="as P03 but buys only on disagreement events (contract adaptation).",
    hparam_space_and_selection="none",
    parity_evidence="as P03",
    fidelity_class="common-contract adaptation",
    guarantee="none transferred",
    matched_cutoff_wrapper_safe="yes",
    notes="",
)
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(R)
print(len(R), "rows ->", OUT)
