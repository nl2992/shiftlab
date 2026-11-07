# RAR baseline specification (WP1b)

**Paper.** *Retrain, Alert, or Rollback? A Three-Response Decision Framework for Production ML Under Concept Drift*, arXiv:2611.02251v1, https://arxiv.org/html/2611.02251.
**Code:** `src/shiftlab/sota/rar/` (config, components, controller, harness, streams). **Tests:** `tests/d2a_rar/test_rar.py`. **Reproduction script:** `scripts/d2a_rar/rar_repro.py`, `rar_summarize.py`.

## Source status and fidelity tier

| item | status |
|---|---|
| Author code / artifact | **Not obtainable.** Sec. 10 states the harness, analysis scripts and data pipeline are archived at Zenodo under *reserved* DOI 10.5281/zenodo.22829389, "made public on acceptance", available to editor/reviewers "on request". No public URL, no GitHub link, no stated licence. Not cloned (nothing to clone). |
| Repo search | `git grep` over all refs for canary/rollback/alert-hold/three-response found only ShiftLab's own `CertifiedPromotionRollback` (`src/shiftlab/dive/controller.py`, a certified-promotion design, different mechanism) and positioning docs. Nothing portable. |
| **Fidelity tier** | **PAPER_RECONSTRUCTION** (not AUTHOR_NATIVE). |
| Text actually read | Abstract, Secs 1-6 (through H6, Table 1-3, 5, 9-11 summaries), glossary/defaults, Sec 10 reproducibility. The page fetch was summarised by a model in two passes; Algorithm 1/2 listings were condensed, not read verbatim. Treat section numbers below as approximate. |

## What is implemented (paper element -> code)

- **State machine** (Fig. 1): Serving, Canary-1, Canary-2, Alert-Hold-Soft, Alert-Hold-Hard (`controller.py`). Serving->Canary-1 on admitted retrain; Canary-1->Canary-2 on stage-1 pass; Canary-2->Serving on commit; any canary stage -> Hold-Hard on R2, -> Hold-Soft on R1/R3/timeout; Soft exits on kappa_short expiry or emergency override; Hard exits on kappa_long expiry or m_clear consecutive clean instances.
- **Time model** (Sec 3): labels arrive after tau; label-dependent quantities (detector, accuracies, canary tallies) update only at the frontier i<=t-tau on release; live quantities (q_t, hold/canary clocks, routing) at t. The controller raises `LeakageError` for any label released before the frontier or never requested. Note: tau=0 means "visible at the next step" (prequential), i.e. effective delay >=1.
- **Gate 1**: pluggable detector (river ADWIN delta=0.002, or scripted); burn-in = guard gap g plus `detector_warmup` updates after each model birth, then re-baseline; onset t_hat_d = frontier - width + 1.
- **Gate 2**: l_t(W_train)>=theta_L (0.7), window anchored at t_hat_d, capped at W_train. Earliest time t* = t_hat_d + tau + ceil(theta_L W_train) - 1 (`earliest_retrain_time`; test checks the simulation hits it exactly and that one step earlier the gate fails). Feasibility W_train>=tau/(1-theta_L) and latency Eq. 5 `latency_estimate` (test: frozen example gives 6,390).
- **Gate 3**: A_pre(t_hat_d) - A_cur(t) >= theta_R (0.05); A_pre over W_ref ending t_hat_d - g.
- **Alert arm**: A1 (gate 1 pass, gate 2 fail), A2 (gates 1-2 pass, gate 3 fail), A3 (no flag, soft anomaly), alerts de-duplicated per (flag, type), A3 rate-limited by W_mon. Canary timeout = rollback plus alert.
- **Staged canary**: stage 1 routes fraction p1=0.2 by stratified interleaving (one slot per block, seeded phase per episode); only *served* predictions are ledgered, shadow predictions never; stage-1 clock counts *labelled routed* obs until W1=300; stage 2 full traffic until W2=600 with old model shadow-scored; commit iff z=(n01-n10)/sqrt(n01+n10) >= z_commit=1 else dead-band revert; old model retained for rollback; per-stage timeout.
- **Rollback causes** (Alg. 2): R1 margin screen A_new < A_old - delta (+ interim checkpoint), R2 sustained corruption flag (hard hold, no override), R3 worse than majority-class on the canary window; charge C_b once, discard M_new, restore M_old, reset detector. Emergency override from Hold-Soft: elapsed>=kappa_min, A_cur < A_ref - Delta_crit (2 theta_R), Gate 2 label fraction, q_t clean.
- **Corruption pre-filter q_t**: step-size check (mean abs successive difference of standardised features vs train-prefix baseline); quarantined instances are served and ledgered but not fed to the detector.
- **Objective** (Eq. 3): U = sum 1{yhat=y} - C_r N_r - C_a N_a - C_b N_b, C_r=rho, C_a=0.05 rho, C_b=0.2 rho. Each counter is incremented in exactly one function (`_act`) at the moment the action is performed (test: log events == counters == formula). U is affine in rho for cost-blind policies (`utility_at_rho`).
- **Six cost-blind policies + Cost-Aware Binary** (`MODES`): No-Response, Always-Retrain (every W_train, immediate deploy), Binary (ADWIN -> retrain on last W_train labelled, immediate), Alert-Only, Rollback-Only (Binary + canary + holds, no alerts), Full RAR; Cost-Aware Binary = Binary retrains only if max(0, A_pre - A_cur) * H_hat >= rho with H_hat = mean inter-detection interval so far floored at W_train (evaluated once per detector flag).
- **Swappable hooks** (`components.py`), no other code touched: (a) `LabelRequestPolicy.request(HookContext)` decides at serve time whether to request y_t (default `AllLabelsPolicy`, RAR's "labels eventually arrive"; the context exposes state, canary stage, routed flag, pending-label inventory but no unreleased label); an optional `c_query` extends U (default 0, not in RAR's U). (b) `GateRule.passes(HookContext)` for Gate 2 (`ThetaLGate`) and Gate 3 (`ThetaRGate`); context carries labelled-in-window count, A_pre, A_cur, rho, t_hat_d. Tested by swapping both.
- **Audit log**: every transition, action, flag, gate evaluation, commit/dead-band and hold exit is appended to `controller.log` (dict per event with t and state).

## Parameters not stated in the readable paper text (reconstruction choices, `config.py` marks each STATED/CHOICE)

delta=0.03 (ablation set {0.01,0.03,0.05}), kappa_short=1500, kappa_long=5000, kappa_min=500, W_mon=1000, W_cur=500, warm-up=1000 rows, detector_warmup=30, ADWIN delta=0.002, canary timeout = 2x nominal stage duration, interim checkpoint at 50% with margin 2 delta, A3 threshold 0.03, q_t window 30 / ratio 3.0 / R2 run 100, Hoeffding-tree settings = river defaults. R2 while *Serving* enters Hold-Hard (paper text read only specifies rollback from canary). **Not implemented:** the prediction-collapse monitor, per-feature freeze/variance/categorical checks, routing i.i.d. variant, detectors other than ADWIN. Gate 3 / emergency-override reference window definitions are my reading.

## Guarantees versus empirical claims

- **No statistical guarantee.** The paper offers no validity, false-retrain, or regret theorem. The canary margin screen is "an operational margin screen, not a significance test"; the commit rule is a one-sided z with alpha~0.16 on discordant pairs, evaluated once, with no sequential or adaptive-selection correction, and holds only heuristically under independence.
- **Deterministic design facts** (verified here by test): the earliest retrain time, the feasibility condition W_train>=tau/(1-theta_L), and the latency formula follow from the gate definitions given constant delay.
- **Empirical claims** (paper): RAR "does not dominate"; windows where RAR beats Binary/Always-Retrain/No-Response simultaneously (S-RB-Drift 41<rho<1013, Covertype 146-1706, S-Gradual 162-1984, S-Abrupt 237-961); H2 not supported; canary removal raises utility on 11/13 streams at rho=1.
- **Limitation relevant to this programme:** the gates are fixed thresholds (theta_L, theta_R, delta, z_commit); they do not optimise intervention costs. Only the Cost-Aware Binary baseline reads rho, and it has no canary/rollback/alert machinery. A cost-aware Gate-2/Gate-3 rule is therefore a legitimate target for the `GateRule` hook, and the proper comparators are Cost-Aware Binary *and* unmodified RAR.
- **Null class (for the programme registry):** none declared by the paper (no hypothesis test is run at the gates; the commit z-test is nominally a one-sided test on paired discordance, conditional-on-nothing). Do not score RAR on marginal- or conditional-null false promotions.

## Reproduction

See the section "RAR" in `docs/d2a_rar/BASELINE_REPRODUCTION.md` (kept in one place to avoid duplicated numbers).
