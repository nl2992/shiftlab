# SOTA registry (WP1c) — Challenger, Gong–Zhang, ASI, Sethi, WATCH, PPRM + in-repo comparators

Written 2026-11-07 by the WP1c agent. Machine-readable mirror: `registry/sota_registry.yaml`.
Honesty conventions: **READ** = text actually retrieved and parsed this session; **UNVERIFIED** = not read or
only inferred; "URL resolves" = HTTP 200 on the URL only, repository contents NOT inspected. Quoted fragments
are <15 words. Notation follows the papers; formulas are transcribed, never reconstructed from memory.

Fidelity tiers: `AUTHOR_NATIVE`, `PAPER_RECONSTRUCTION`, `COMMON_CONTRACT_PORT`, `CONCEPTUAL_PROXY`,
`NOT_IMPLEMENTED`. Comparable outputs: alarm / certificate / label_allocation / retraining / promotion / rollback.

## Reading status

| Paper | Source read | Coverage |
|---|---|---|
| C Challenger arXiv 2512.18390 | arXiv HTML, chars 0–219 249 of 219 249 fetched in three windows | Secs 1–5 + appendix tables read via summariser; **the final ~19 k chars (bibliography/EC tail) not read**; Algorithm 1–3 conditions confirmed by a second targeted fetch. Summariser, not raw text: formula transcriptions carry that risk. |
| D Gong & Zhang PMLR v306 gong26i | PMLR page + PDF (pdftotext, raw PDF downloaded) | Secs 1–5 read incl. Alg 1–3 text, Thm 2.1/2.2/3.1/3.2/4.1, experiments. Appendix (Algs 4–6, proofs) **not read**. Math symbols are garbled by pdftotext (η, ε, Θ̃); constants marked UNVERIFIED where garbled. |
| E ASI Zrnic & Candès arXiv 2403.03208 | arXiv HTML, first 100 000 of 151 584 chars | Estimators, sampling rules, Prop 1–2, Thm 1–2, optimal rules, experiments read. **Appendix assumptions 1–3, App. C non-asymptotic/time-uniform results, Secs 8.4–8.5 not read.** |
| F Sethi et al. v306 sethi26a | PMLR page + PDF (pdftotext) | Secs 1–5 main text, Alg 1, Thm 3.3/4.1/4.4, Cor 5.1, Prop 3.1/4.3 read; appendix proofs only grepped (no full read of B.3). |
| WATCH v267 prinster25a | PMLR page + PDF (pdftotext) | Secs 2–3 (CTM background, WCTM, Thm 3.1, Props 3.2–3.3), results summary read; appendix D–F skimmed by grep only. |
| PPRM v306 zhang26g | PMLR page + PDF (pdftotext) | Secs 1–5 (SRM background, PPRM estimators, Thm 3.2, Lemma 3.3, experiments list) read; appendices A–C not read. |

Code availability (verified by HTTP only): see per-entry. **No entry claims AUTHOR_NATIVE.**

---

## C. The Challenger — GSE / OSE / LSE  (arXiv 2512.18390)

* Authors: not shown in the fetched text; an in-repo note (`origin/research/continuation-2026-11-04:docs/budgeted_switching_research_goals.md`) cites "Digalakis et al. (arXiv:2512.18390)". UNVERIFIED against the paper header.
* **Setting.** Incumbent f_I on feature set I trained on N_0 samples; challenger f_C on enlarged features C ⊃ I trained on a slowly growing full-feature sample. Horizon T, batch n per step, N_t = t·n; decision epochs T_D ⊆ {1..T}; actions switch / discard / continue (retraining at epochs). Gap G(t) = E[ℓ(f_C^{(t_k(t))})] − E[ℓ(f_I)] (a gain; sign convention positive = challenger better). Costs C_pre = C_post = c·n; one-off switching cost c_s ≥ 0.
* **Values.** V_switch(t) = −c·n·T − c_s + n(T−t)G(t); V_discard(t) = −c·n·t; ΔV(t) = −c_s + n(T−t)(G(t)−c). Discounted (β): V^β_switch(t) = −Σ_{τ≤t}β^τ c n − β^t c_s + Σ_{τ>t}β^τ n{G(t)−c}. Oracle V_ORACLE = max{0, max_t V_switch(t)}.
* **Algorithms** (δ_k = γ/√(ρN_{t_k}); holdout fraction ρ).
  GSE: V^LB/UB_switch = V_switch(t_k, Ĝ_k ∓ δ_k); switch if V^LB_switch>0; if V^UB_switch<0 then (switch if ΔV^LB>0 else discard); else continue; last epoch: switch iff ΔV̂>0. OSE: evaluate once at t_OSE; switch iff ΔV̂>0. LSE (w=3, monotonicity-corrected least-squares slope) / LSEc (w=2, confidence-adjusted slope 2δ_k/((1−ρ)ΔN) if latest gap decreased, else [(Ĝ_k+δ_k)−(Ĝ_{k−1}−δ_k)]/((1−ρ)ΔN)): stop at k when max{V̂_switch(t_k),V̂_discard(t_k)} ≥ max_{k'>k} V^UB_switch(t_{k'}) with Ĝ^UB(t_{k'}) = Ĝ_k + (1−ρ)(N_{k'}−N_k)ŝ_k; then switch iff ΔV̂>0.
* **Assumptions / guarantees.** Thm 3.1 (exact finite-horizon rule under T_D = T, deterministic G): switch optimal iff max_t (T−t)G(t) ≥ cT + c_s/n; stopping rule picks argmax. Prop 3.2 under G(t)=g*−g0 N_t^{−α}: t† ~ (g0αT/(g* n^α))^{1/(1+α)}. Thm 3.4 meta-regret O(T^{2/3}√log T) assuming finite VC dimension, ERM, ℓ∈{−1,1}, (C1) w₂T^{2/3} ≤ t_ALG ≤ w₃T^{2/3}√log T and (C2) consistent switching w.h.p. Prop 4.2: OSE with t_OSE ≍ T^{2/3} satisfies (C1),(C2) w.p. ≥ 1−2/T. Prop 4.4: LSEc with geometric epochs t_k = Λλ^{k−1} satisfies (C1),(C2) w.p. ≥ 1−2/T. Remark 4.1: γ = √(8 log(2K/η)) gives uniform |Ĝ−G| ≤ δ_k w.p. ≥ 1−η (Hoeffding + union).
  **Null / filtration:** none — an *economic* (regret-vs-oracle) guarantee, not a hypothesis test. In the null registry: `null_class: economic_regret`, no false-promotion control. Must NOT be scored with marginal/conditional-null false-promotion metrics.
* **Native experiments.** Lending Club (Kaggle), 705 302 loans 2014-05→2017-04, |I|=7, |C|=29, N_0=189 250, challenger sequential sample N_te=163 400 (35 900 reserved), β=0.95, c_acq=0.0025, c_s=0, geometric schedule 500→127 500 (×2, 8 epochs), 30 sample paths, 90 % CIs; E.1 LR (c_train=0.075, oracle switch ≈ epoch 4), E.2 LightGBM (c_train=0.005, oracle ≈ epoch 6); GSE γ=1.92, LSEc γ=0.1, LSE w=3, OSE at epochs 1/4/last. Metric: realised value vs oracle (regret). Numerical results tables **not retrieved** (page window ended in Sec 5.2 on first fetch; second window gave parameters only).
* **Code:** none found in the HTML (searched windows 100k–219k for repo/data-availability: none; first 100k summarised without a URL). Dataset URL given: kaggle `ethon0426/lending-club-20072020q1`. **Not downloaded.**
* **Comparable output in ShiftLab:** `promotion` / replacement-timing (one-shot switch vs discard of a candidate whose gap is learned over time). Not an alarm, not a certificate. Relevant to RAR's retrain-timing economics only through the "wait vs act" structure; native setting (monotone learning curve, no drift, no delayed labels) differs from RAR's repeated drift response.
* **Tier:** `PAPER_RECONSTRUCTION` (implemented: `src/shiftlab/sota/challenger/`, tests `tests/d2a_rar/test_challenger.py`; reproduction notes in `BASELINE_REPRODUCTION.md`).

## D. Gong & Zhang — Contextual bandits with paid observations (ICML 2026, PMLR 306:36013–36044)

* Title: "The Cost of Information: Phase Transitions in Contextual Bandits with Paid Observations".
* **Setting.** Adversarial contextual bandit, finite A and finite policy class Π, T rounds; non-oblivious adversary (Assumption 2.1). Each round: context x_t, cost vector {c_t(a)}; learner plays a_t via a policy and picks an observation set O_t ⊆ A, **paying c_t(a) for each a∈O_t and seeing ℓ_t(a)**; loss of a_t may be unobserved. Regret R(T) = E Σ(ℓ_t(a_t) − ℓ_t(π*(x_t))) + E Σ_t Σ_{a∈O_t} c_t(a).
* **Algorithm 1** (extends Seldin et al. 2014): policy weights w_t(π) ∝ exp(−η_t Σ_{s<t} ℓ̂_s(π(x_s))); q_t(a) = (1−γ)Σ_{π:π(x_t)=a} w_t(π)/Σw + γ/|A|; observation prob **p_t(a) = min{1, ε_t q_t(a)/c_t(a)}** (garbled in extraction: the symbol multiplying q_t(a) is a learning-rate-type ε_t — UNVERIFIED which); importance-weighted ℓ̂_t(a) = 1{a∈O_t}ℓ_t(a)/p_t(a). Thm 2.1: regret ≤ (ln|Π| term)/η_{T+1} + (Σ_t η_t Σ_a c_t(a)q_t(a) term) + 2γT (exact constants garbled in pdftotext; UNVERIFIED); with uniform cost c: R(T)=O((c|A| ln|Π|)^{1/3} T^{2/3} + √(T ln|Π|)). Thm 2.2 lower bound Ω(max{√(T ln|Π|), (c|A| ln|Π|)^{1/3}T^{2/3}}).
* **Free budget B** (Sec 3): Thm 3.1 lower bound with phase transition at B₀ = Θ̃(c^{−2/3}|A|^{1/3}(ln|Π|)^{1/3}(ln|A|)^{−1/3}T^{2/3}) (rendering garbled: UNVERIFIED exact exponents); below B₀ regret ≈ (c|A|ln|Π|)^{1/3}T^{2/3} − cB, above ≈ T√(|A|ln|Π|/(B ln|A|)). **Algorithm 2 meta-controller**: if B ≥ 1.5·c^{−2/3}(|A|ln|Π|)^{1/3}T^{2/3} run Alg 4 (budget allocation with p_t(a)=B/(|A|T), η_t ∝ √(B/(|A| ln|Π|))/T-type), else run Alg 6 (running budget B_t decremented by observations; excess observations still paid). Thm 3.2 matches the lower bound. Algs 4–6 are in the appendix — **not read**.
* **Alg 3 (oracle-efficient, stochastic realisable setting):** Assumption 4.1 realizability E[ℓ_t(a)|x_t]=f*(x_t,a); inverse-gap-weighting q_t(a)=1/(|A|+γ_t(f̂_t(x_t,a)−f̂_t(x_t,a_t*))) off the greedy action; p_t(a)=min{1, ε_t√(q_t(a)(1−q_t(a)))... /c_t(a)} (garbled; UNVERIFIED), online squared-loss regression oracle with Reg_Sq(T). Thm 4.1 regret ≤ Reg(T) + 3(Reg_Sq)^{1/3}(Σ_tΣ_a c_t(a))^{2/3}-type + 2√(T Reg_Sq) (garbled; UNVERIFIED).
* **Native experiments.** Synthetic: T∈{2k..40k}, d∈{2,4,8}, |A|∈{3,5,10}, |Π|∈{10,20,40}, Gaussian L2-normalised contexts, costs U(0.01,0.5), losses U(0,1) or linear+noise; 50 runs; cumulative regret (incl. cost). Baseline table (d=10,|A|=5,T=10 000, c=0.5): linUCB 5003.32±1.04, Tucker et al. 2023: 3697.13±26.80, Alg 3: 2899.75±48.80.
* **Code:** none listed on the PMLR page; no URL in the PDF text (grep). Tucker et al. 2023 (linear contextual bandit with costly observations) is the only prior competitor named; its code status UNVERIFIED.
* **Comparable output:** `label_allocation` — a per-round, per-action observation probability under a price. Mismatch with ShiftLab: no delay, no release clock, no alarm/promotion semantic, adversarial regret against best fixed policy. Valid use: (i) native comparator on its own game; (ii) common-contract adaptation = "price-aware label-request propensity" p_t = min(1, κ_t q_t/c) with q_t the controller's own propensity. Closed forms must not be invented beyond the above.
* **Null:** none (regret). **Tier:** `NOT_IMPLEMENTED` (spec: `baselines/GONG_ZHANG.md`).

## E. Active Statistical Inference — Zrnic & Candès (ICML 2024, arXiv 2403.03208)

* **Setting.** i.i.d. unlabeled X_i; labels revealed at cost; budget E[n_lab] ≤ n_b; black-box predictor f; target M-estimand θ* = argmin E ℓ_θ(X,Y). Batch (fixed f, π) and sequential (f_t, π_t updated) variants.
* **Estimators.** Mean: θ̂^π = (1/n)Σ[f(X_i) + (Y_i−f(X_i))ξ_i/π(X_i)], ξ_i~Bern(π(X_i)); Var = (1/n)(Var(Y)+E[(Y−f)²(1/π−1)]). M-estimation: L^π(θ) = (1/n)Σ[ℓ^f_{θ,i} + (ℓ_{θ,i}−ℓ^f_{θ,i})ξ_i/π(X_i)]. Sequential: Δ_t = f_t(X_t)+(Y_t−f_t(X_t))ξ_t/π_t(X_t), θ̂=(1/n)ΣΔ_t.
* **Sampling rules.** π_η(x)=η u(x), η̂=max{η∈H: ηΣu(X_i) ≤ n_b}; mixed π^{(τ)}=(1−τ)π+τ n_b/n (τ=0.5 sequential default); sequential π_t(x)=min{η_t u_t(x), n_{Δ,t}}_{[0,1]} with n_{b,t}=t n_b/n, n_{Δ,t}=n_{b,t}−n_{lab,t−1}. Uncertainty u: regression — model of |f−Y|; classification — u=K/(K−1)(1−max p_i), binary u=2 min{p,1−p}. Oracle rule π_opt ∝ √E[(Y−f)²|X] (mean).
* **Guarantees (asymptotic):** Prop 1/Thm 1 (batch) and Prop 2/Thm 2 (sequential) give √n(θ̂−θ*) → N(0,Σ*), CI coverage 1−α asymptotically, under smoothness (Ass 1), Lindeberg (Ass 2–3), π̂ convergence / variance convergence conditions. **Appendix assumptions and the non-asymptotic/time-uniform variants (App. C) not read.** Unbiasedness requires π_t predictable and π_t>0 (needed for IPW) — stated as my reading of the estimator; confirm in App.
* **Native experiments.** Pew 2020 survey (XGBoost; savings >85 %/~25 % vs classical/uniform Biden), ACS PUMS California 2019 income~age+sex (≈80 %/>60 %), AlphaFold proteomics odds ratio (>75 % vs classical); α=0.1; 1000 batch / 100 sequential trials; metric: coverage + CI width vs n_b, "budget saved".
* **Code:** https://github.com/tijana-zrnic/active-inference — URL resolves (HTTP 200); contents not inspected.
* **Comparable output:** `label_allocation` (+ an unbiased risk estimate / CI, i.e. a weak `certificate`). Not a controller: no actions, no delay. Streaming/monitoring variant in ShiftLab requires time-uniform CIs, which this paper's *asymptotic* CLT does not supply — ShiftLab's PPI e-process adapters (`sota_search/published_baselines.py`) are the anytime-valid counterparts.
* **Null:** estimation (no test). **Tier:** `NOT_IMPLEMENTED` (spec: `baselines/ASI.md`); `CONCEPTUAL_PROXY` exists in-repo (`src/shiftlab/dive/active_inference.py`, HEAD; relation to the paper UNVERIFIED).

## F. Sethi et al. — Asymptotically Optimal Sequential Testing with Markovian Data (ICML 2026, PMLR 306:109294–109330)

* **Setting.** Ergodic finite-state chain (P,μ), time-homogeneous, **consecutive** observations X_1,X_2,…. H0: P∈𝒫 vs H1: P∈𝒬, 𝒫∩𝒬=∅ (composite vs composite, compact classes). α-correct power-one test = stopping time τ with sup_{P∈𝒫,μ} P[τ<∞] ≤ α and P_Q[τ<∞]=1.
* **Algorithm 1.** Counts N_x, N_{x,y} from consecutive pairs; Q̂_t(x,·) = empirical rows (uniform if N_x=0); β_t = Σ_x log(e(1+N_x/(m−1))) (symbols garbled — UNVERIFIED form); threshold log(1/α)+(m−1)β_t; statistic L_t = inf_{P∈𝒫} Σ_{x:N_x>0} N_x KL(Q̂_t(x,·)‖P(x,·)); reject when L_t ≥ threshold. Remark 4.2: exp(L_t−(m−1)β_t) is upper bounded by a nonnegative supermartingale ⇒ e-process. Surrogate (Prop 4.3, Pinsker-type via Poisson equation): L̃_t = inf_P sup_g (E_{Q̂_t}[g]−E_P[g])²/(2‖ψ_{P,g}‖²…) — conservative, α-correct, larger stopping time.
* **Guarantees.** Thm 3.3 non-asymptotic lower bound E_Q[τ] ≥ log(1/α)/D^{M}_{inf}(Q,𝒫) − 2C_Q/(min_i π_i) (π = stationary of Q; C_Q from Prop 3.1 via pseudo-spectral gap); D^M(Q,P)=Σ_i π(i)KL(Q(i,·)‖P(i,·)). Thm 4.1: Alg 1 is α-correct and limsup_{α→0} E_Q[τ]/log(1/α) ≤ 1/D^M_inf(Q,𝒫). Thm 4.4: two-sided version. **Filtration:** natural filtration of {X_n}. **Null:** `conditional-on-chain` composite null on 1-step kernels; an anytime-valid test of the *model class*, not of risk or economic harm.
* **Native experiments.** MCMC misspecification (target π∈Δ_5, α=0.05, Q_good∈𝒫 vs Q_bad∉𝒫: statistic grows at slope D^M_inf; no false rejections in 100 runs — boundary conservative); linear-MDP structure testing (null = linear kernels PM,π=ΦMΘ…); appendix runs vary m, α, ρ (Tables 2–3, Figs 5–7). Metrics: statistic trajectories, mean stopping time vs log(1/α), runtime/step.
* **Code:** https://github.com/Alhad-Sethi/Sequential-Markovian-Testing — URL resolves (HTTP 200) and is listed on the PMLR page; contents not inspected.
* **Comparable output:** `alarm` (power-one test of a transition-class null). Treat as a *dependence-aware evidence engine*, not a decision rule. Relation to ShiftLab: the Markov-LR gate (`atlas_dependence_baselines.MarkovLREProcess`, `MarkovLRGate`) tests a different (binary-loss-regime) null with a generic mixture; Sethi's Alg 1 targets general finite-state chains.
* **Exact-gap P^{g}:** see `baselines/SETHI.md` — **not covered** by the paper's theory as stated; only the constant-gap case (thinning) and an exogenous-i.i.d.-gap augmentation reduce to it.
* **Tier:** `NOT_IMPLEMENTED` (spec: `baselines/SETHI.md`).

## WATCH — Prinster, Han, Liu, Saria (ICML 2025, PMLR 267:49830–49859)

* **Setting.** Pretrained model, calibration set Z_{1:n}, test stream; detect "any unexpected change" with weighted-conformal test martingales (WCTM) while adapting to mild covariate shift and diagnosing cause (extreme covariate vs concept shift).
* **Method.** Generalised weighted-conformal p-values p^{w̃}; Thm 3.1: p-values are i.i.d. Uniform(0,1) under a customised null H0(f̂) with a correct weight vector; betting function h_ε(p)=1+ε(p−0.5), ε∈{−1,0,1}; composite-jumper mixture (Vovk et al. 2022); WCTM M̃_t = ∏ h(p_i) mixed. Prop 3.2: P_{H0(f̂)}(∃t: M̃_t/M̃_0 ≥ c) ≤ 1/c (Ville). Prop 3.3: Shiryaev–Roberts ARL control E_{H0}[τ] ≥ c. WATCH: secondary X-CTM on the covariate marginal triggers online density-ratio estimation (classifier) once exceeding a threshold; main WCTM then adapts weights; root-cause analysis by parallel WCTM/X-CTM.
* **Null:** H0(cs) = Y|X invariant, covariate density ratio w(x) = g_X/f_X **correctly estimated** (the p-value validity is conditional on that weight model; the paper itself notes a modified Thm 3.1 for covariate-shift only). Not a risk/harm null; unlabeled-only X-CTM part needs no labels, but the WCTM concept-shift part uses labels (conformal scores).
* **Experiments.** Real-data suites incl. CIFAR-10-C, MNIST-C, UCI (Bike Sharing), MEPS and others; metrics average detection delay (200 seeds), false alarm control, anytime-valid vs ARL criteria (Table 1). Exact dataset list not fully read.
* **Code:** https://github.com/aaronhan223/watch (listed on PMLR page) — URL resolves (HTTP 200); contents not inspected.
* **Comparable output:** `alarm` + cause label (concept vs covariate). Native alarm is on distributional change, which AGENTS.md says is a sentinel, not evidence of harm. **Tier:** `NOT_IMPLEMENTED` (no WATCH adapter found in repo; grep for `weighted_conformal|WCTM` not run exhaustively — UNVERIFIED).

## PPRM — Zhang, Cai, Yu, Simeone (ICML 2026, PMLR 306:154241–154262)

* **Setting.** Deployed model monitored over t=1,2,…; labeled batch D_t (n_t>0) plus unlabeled batch D̃_t (N_t inputs); auxiliary predictor f_p gives synthetic labels ỹ = argmax_c f_p(x̃)[c]. H0: R̄_t ≤ R_0 + tol ∀t vs H1: ∃t R̄_t > R_0 + tol, where R̄_t is the running (time-averaged) risk.
* **Method.** PPI++ estimates R̂_0^PP = (λ_0/N_0)Σℓ(f(x̃),ỹ) + (1/n_0)Σ[ℓ(f(x),y) − λ_0 ℓ(f(x),ỹ)] and the analogous R̂^PP_t (Eqs 17–19); predictable λ_t (Lemma 3.1 unbiasedness); optimal λ_t* = Cov(u,ũ_L)/((1+n_t/N_t)Var(ũ_U)) (Lemma 3.3), estimated on a sliding window L (Eq 27). Lower bound L_t^PP = R̂̄_t^PP − w_t^PP with conjugate-mixture empirical-Bernstein (CM-EB) w_t = u(V_t^PP)/t, V_t^PP = Σ(R̂^PP_{t'}−R̂̄^PP_{t'−1})²; upper bound U_0^PP on the source risk (betting-based, Einbinder et al. 2025). Alarm 1[L_t^PP > U_0^PP + tol]. Thm 3.2: P_{H0}(∃t: alarm) ≤ δ_S + δ_T, "assumption-free finite-sample" given predictable λ_t.
* **Null:** time-averaged-risk excess ≤ tol (a **marginal-type, absolute-ish** null over the running mean risk, no conditioning on the past); per the MANDATE P2 correction it must be scored on its own null, not on conditional excess-cost false promotion.
* **Experiments.** Image classification (Gaussian-noise severities; ResNet-32; binary and squared losses), LLM QA under prompt shifts (t=200, various f_p), telecommunications decoder monitoring (appendix); baselines Ideal PPRM, SRM (Podkopaev & Ramdas 2022), URM (Schirmer et al. 2025); metric average time-to-alarm.
* **Code:** none listed on the PMLR page. **ShiftLab already has PPRM adapters** (below) — their conformance to the ICML-2026 text (Eqs 17–27, CM-EB, U_0 betting bound) was not audited this session.
* **Comparable output:** `alarm` (risk-excess), with a lower-bound `certificate` on running risk. **Tier of in-repo adapters:** `COMMON_CONTRACT_PORT`; paper reconstruction of the ICML text: not done.

## A/B. Drift2Act and RAR

Stubs only — see `docs/d2a_rar/baselines/DRIFT2ACT.md` and `docs/d2a_rar/baselines/RAR.md` (written by the other WP1 agents). Registry rows are in the YAML with `tier: SEE_BASELINE_DOC`.

---

## In-repo comparators (found with `git grep` over all refs)

Refs searched: all local and `origin/*` branches (`git for-each-ref`, 60 refs). "HEAD" = this worktree (`main@7354480a`).

| Comparator | Where | Ref(s) containing it | Output | Null / validity note | Tier |
|---|---|---|---|---|---|
| H2c, HG, C1/C2, Kelly/ONS, Xu-query, Tenzer ports | `src/shiftlab/hgxh2c/baselines.py` (`hg`, `h2c`, `kelly`, `ons`, `xu_query`, `tenzer`, REGISTRY with notes DIFFERENT_NULL/EMPIRICAL_ALARM) | HEAD | alarm / promotion | prediction-powered cost betting; per-entry flags in file | H2c/HG are ShiftLab originals ("SOURCE_REPRODUCED" vs originals per file docstring); published ones `COMMON_CONTRACT_PORT` ("TASK_ADAPTED") |
| PPRM risk monitor | `src/shiftlab/dive/pprm_risk_monitor.py` (`PPRMRiskMonitor`, `PredictableReliance`, `source_risk_upper_bound_cm_eb/betting`) | HEAD + many | alarm | see PPRM above | `COMMON_CONTRACT_PORT`, ICML-text audit pending |
| PPRM/PPI/active-RCPS batch costs, detectors (MMD, C2ST, BBSD, CUSUM, Page–Hinkley, two-window, PR-CS, pp_eprocess, sr_edetector) | `src/shiftlab/sota_search/published_baselines.py`, `.../detectors.py` | `origin/codex/sprint2-leaderboards`, `origin/research/continuation-2026-11-04`, `origin/claude/sweet-lovelace-pznpjq`, `origin/claude/failure-atlas-v2-sota-195428` (NOT in HEAD) | alarm | mixed | `COMMON_CONTRACT_PORT` (port with source-commit citation) |
| RMM (RestartMixtureMonitor) + HorizonWeightedPacer, MixtureSRDetector | `scripts/failure_atlas_v2/restart_monitor.py` | `origin/codex/sprint2-leaderboards`, `origin/research/continuation-2026-11-04`, `origin/claude/sweet-lovelace-pznpjq`, `origin/claude/failure-atlas-v2-sota-195428` | alarm | restart-mixture of SR e-detectors | ShiftLab own / `PAPER_RECONSTRUCTION` of cited restart mixtures (not audited) |
| E_rb, SRR/GLR detector swaps, SlidingWindowCert | `scripts/sota_sprint/fam_e.py` (E_rb reference as given by the brief) ; GAVE port `src/shiftlab/gaver/erb_port.py` (`GridMixtureDetector`, `ErbMethod`, `TwoPhaseMethod`) | `fam_e.py`: `origin/codex/sprint2-leaderboards`, `origin/claude/sweet-lovelace-pznpjq`; `erb_port.py`: `origin/research/gave-r-2026-11-06` | alarm / rollback | E_rb details not audited here | `COMMON_CONTRACT_PORT` |
| Page-CUSUM | `src/shiftlab/dive/atlas_components.py`, `failure_atlas.py`, `src/shiftlab/gaver/freshcheck.py` | HEAD (atlas files); gave-r (freshcheck) | alarm | CUSUM, `EMPIRICAL_ALARM` (not anytime-valid) | `COMMON_CONTRACT_PORT` |
| Markov-LR, thinned-hedged gate | `src/shiftlab/dive/atlas_dependence_baselines.py` (`MarkovLREProcess`, `MarkovLRGate`, `ThinnedHedgedGate`, `build_dep`) | HEAD | promotion evidence | valid under its stated Markov class; "arbitrary gaps not claimed" (file comment) | ShiftLab original; relation to Sethi: different statistic |
| Gap-Mix (exact-gap, envelope) | `src/shiftlab/gaver/gapmix.py` (`EnvelopeStart`, `ExactGapStart`, `certified_null_sup_loglik`, `exact_loglik`) | `origin/research/gave-r-2026-11-06` | promotion evidence | beat Markov-LR in declared dependence class, failed outside (MANDATE) | development only |
| DSS / straddle | `src/shiftlab/dive/atlas_components.py` (`straddle` acquisition; `dss_spec`, `dss_ablations` on gave-r), `scripts/check_straddle_bound.py` | HEAD (`straddle`), gave-r (`dss_spec`) | label_allocation | — | ShiftLab own |
| PAVE | `src/shiftlab/gaver/pave.py` (`PaveMethod`, `PaveParams`), `integrated.py` | `origin/research/gave-r-2026-11-06` | label_allocation / promotion | narrow positive at long delays (MANDATE) | development only |
| FreshCheck | `src/shiftlab/gaver/freshcheck.py` | gave-r | rollback | did not beat strong rollback comparators | development only |
| episode_front | `src/shiftlab/dive/failure_atlas.py` (rule), `atlas_dependence_baselines._FrontGated` | HEAD | promotion | calendar + alpha spending + econ_ok + rollback | ShiftLab own |
| Two-phase persistence promotion | `src/shiftlab/dive/persistence_promotion.py` (`_two_phase_decisions`, `PersistencePromotionConfig`), `promotion_robustness.py` | HEAD | promotion | — | ShiftLab own |
| Certified deployment gates | `src/shiftlab/dive/controller.py`, `budgeted_promotion*.py`, `integrated_pipeline.py`, `scripts/evaluate_wilds_pace_gate.py` | HEAD | promotion | gates named in several modules; exact certified-gate API not audited | ShiftLab own |
| Active inference proxy | `src/shiftlab/dive/active_inference.py` | HEAD | label_allocation | relation to ASI UNVERIFIED | `CONCEPTUAL_PROXY` |

Not found by `git grep` this session: WATCH adapter, Drift2Act reproduction code (the continuation branch only has
docs: `origin/research/continuation-2026-11-04:docs/budgeted_switching_research_goals.md`,
`docs/g1_deadline_aligned_acquisition_kill_v1.md`), any Challenger/Gong–Zhang/Sethi implementation.
