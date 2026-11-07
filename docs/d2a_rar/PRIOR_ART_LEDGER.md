# Prior-Art Ledger (WP4) - Drift2Act / RAR programme

Date: 2026-11-07. Author: WP4 literature agent. Method: HKUSTDial `deep-research` (frozen RQs, adversarial
multi-perspective search, per-citation verification). Machine-readable twin: `registry/prior_art.yaml`.

**This is a spot-check-plus-reuse audit, not an exhaustive survey. A failed search is NOT proof of novelty.**
No candidate below is declared novel; PLAUSIBLY_DISTINCT means only "no direct hit found in the searched
sources; positioning and comparator obligations remain".

## Frozen research questions
- RQ1: For each candidate mechanism family, which published work already contains the mechanism?
- RQ2: What assumptions/guarantees differ, and which comparator is mandatory?
- RQ3: Which families retain room, and which must be dropped or repositioned as baselines/ablations?

## Verification levels
- **V** = page fetched this session (title, authors, year checked against the arXiv/PMLR page).
- **R** = verified through an earlier ShiftLab primary-source audit (full PDF read, SHA256 recorded there; not
  re-fetched here). Audits: `docs/switching_*_audit_v1.md` (main) and
  `origin/research/gave-r-2026-11-06:docs/gaver/40_PRIOR_ART_CHECK.md`, `docs/closest_prior_work.md`.
- **S** = bibliographic details from search-result metadata only; re-check before citing.
- **U** = UNVERIFIED (named from memory/secondary mention; not fetched).

Search coverage, honestly: WebSearch over arXiv/PMLR/proceedings/journal landing pages; WebFetch on ~40 abstract
pages. NOT done: OpenReview forum search, Econometrica/JASA/Biometrika full-text search, a real GitHub code search
(WebSearch returned no repository for Drift2Act or RAR), online-experiment ramp-up optimisation literature, full-text
reading of Drift2Act/RAR beyond the first ~100k characters of their HTML (Drift2Act App. D.7 and RAR Sec 8 unseen).

## Key verified facts about hosts/comparators (V)
- **Drift2Act** (arXiv 2603.08578; Lamaakal et al.; ICLR 2026 CAO workshop; no code link found). Audit labels drawn
  *uniformly at random* from the window (optionally within strata); sample size n_t set by a QueryPolicy that rises
  with drift evidence or a large radius relative to tau - R_hat; certificate recomputed *every step* with
  delta_t = 6 delta/(pi^2 t^2); labels available at i+d, certified window shifted back by d; no explicit pending queue
  described; rollback gated only by cooldown, not delay-aware. Theorem 1 is stated for the current window while the
  algorithm certifies the lagged window (App. D.7 not read) - an audit item, not a novelty claim.
- **RAR** (arXiv 2611.02251; Sadeghian et al.; submitted to DMKD). Its own *Cost-Aware Binary* baseline already gates
  ADWIN-flagged retrains on (Gate-3 degradation x mean inter-detection horizon) >= rho. Canary p1/W1/W2 are fixed
  (swept in ablation, not optimised); promotion = McNemar-type z on discordant pairs at end of stage 2. The paper
  reports RAR does not dominate; removing the canary raises utility on 11 of 13 streams. Harness said to be released;
  no URL found. Consequence: cost-aware Gate-3 is NOT new; Gate-2 and canary exposure are not cost-optimised there.
- **Sethi et al. ICML 2026** (PMLR 306:109294-109330; arXiv 2602.17587). Discrete-time finite-state ergodic chain
  observed at every integer step; composite null class P; plug-in KL statistic minimised over P, exponentiated into
  an e-process; alpha-correct; asymptotic optimality as alpha -> 0. NOT treated: continuous time, irregular/random
  sampling, missing or adaptively chosen observations (future work lists countable states / HMMs). The mandate's
  "continuous-time/irregularly-sampled chain tests" is therefore not in Sethi; no other such paper was found
  (absence of evidence only).
- **Fields-Javidi-Shekhar** (arXiv 2501.13187): one-sided SPRT-type Markov tests; every-step observation.

## Family-by-family ledger
Status: KNOWN / HIGH_OVERLAP / PLAUSIBLY_DISTINCT / UNVERIFIED.

### F1 Exact-gap Markov evidence P^{g_i} -> HIGH_OVERLAP
- Closest: Sethi (V), Fields (V); Krishnamurthy 2012, arXiv 1208.3291 (V; choice of sampling *intervals* for a noisy
  Markov chain with measurement cost, Bayesian quickest detection); Ren-Johansson-Shi, IEEE TAC 62(6) 2017 (S;
  observation scheduling); Lau-Tay arXiv 1912.11693 (V; sampling policy with switching cost, GLR-CUSUM).
- Overlap: the g-step kernel is Chapman-Kolmogorov; the likelihood of a fully observed chain at irregular times is a
  product of P^{g_i}(x,y) (textbook). Sequential-test shell with composite null/e-process is Sethi's.
- Remaining: a proved time-uniform null when gaps are random and the observation mechanism is informative (selection
  depends on past states); ergodicity/aperiodicity of P^g across the gap set; plug-in estimation under sparse gaps.
  No source found for these, which proves nothing.
- Differences: Sethi assumes every-step observation; a fixed-known-gap version is likely a corollary by conditioning
  on the gap sequence. Adaptive gaps matter only if gap choice depends on unobserved state.
- Mandatory comparators: Sethi plug-in test on thinned/fixed-gap chain; ShiftLab Markov-LR; fixed spacing; restart without gaps.
- Verdict: do not claim "gap-aware Markov likelihood". Residue = validity/power under informative selection.

### F2 Transition envelopes -> HIGH_OVERLAP (generic idea KNOWN)
- Closest: Fauss-Zoubir-Poor, Ann. Statist. 48(5) 2020, arXiv 1811.04286 (V; minimax-optimal Markov sequential tests
  with uncertainty sets); Sethi composite null class (V); Managoli-Prabhakaran arXiv 2605.12063 (R); repo audits
  `switching_markov_robust_sequential_testing_prior_audit_v1.md`, `switching_finite_memory_adversarial_testing_prior_audit_v1.md`.
- Remaining: only the coupling with delayed/pending queries or the economic objective (repo audits already reject
  generic coupling).
- Comparators: Sethi composite-null test; LFD robust tests; Markov-LR with plug-in/mixture parameter.
- Verdict: use as baseline/ablation arm, not a headline.

### F3 Onset / restart mixtures with gaps -> HIGH_OVERLAP
- Closest: Shin-Ramdas-Rinaldo e-detectors, arXiv 2203.03532 (V; SR and CUSUM-style detectors from e-processes started
  at consecutive times, with mixtures, non-iid); Lorden 1971 Ann. Math. Statist. 42(6):1897-1908 (S); Pollak 1985
  Ann. Statist. 13(1):206-227 (S); Gafni-Iyengar-Zeevi arXiv 2602.11406 (V; ICML 2026 restart-CUSUM with regret).
- Overlap: restart mixtures over start times are e-SR; any valid per-start e-process (incl. a Markov gap-LR) plugs in.
- Remaining: wall-clock start-time mixing weights depending on gap length; ARL calibration under sparse adaptively
  selected observations.
- Comparators: e-SR/e-CUSUM with Markov-LR base; Page-CUSUM; restart without gaps.
- Verdict: reposition as an e-detector instance; novelty only if gap-weighted mixing improves delay at equal ARL.

### F4 Decision-valued label requests, VOQ = E[J|wait] - E[J|query] - c_q -> HIGH_OVERLAP (generic VOI); narrow residue
- Closest: Horvitz et al. selective supervision IJCAI 2007 and UAI 2007 (S); ADOWIP arXiv 2606.25068 (V; delayed
  sealed pending queue, hard budget, decision-loss priority); Ferrari-Zhao-Scaglione arXiv 1705.05960 (V; finite-horizon
  utility sensing, time-varying thresholds); Naghshvar-Javidi arXiv 1203.4626 (V); Li et al. arXiv 1601.06447 (V);
  Xu-Karampatziakis-Mineiro arXiv 2406.10490 (V; NeurIPS 2024, optimal labeling probabilities maximising e-process
  log-growth under a label budget); Zrnic-Candes arXiv 2403.03208 (V); Cai-Kandasamy arXiv 2304.06808 (V);
  Setoudehtanzangi-McLachlan arXiv 2609.06873 (V); Ham et al. arXiv 2609.28859 (V; SCALE, cost-aware selective scoring
  with valid sequential test); Gong-Zhang (V). Repo audits (R): response_adaptive_switching, finite_horizon_sensing,
  usage_constrained, adowip.
- Overlap: wait-vs-query value, remaining-horizon pricing, decision-loss scoring, hard budgets, delayed labels.
  Generic posterior-aware VOI was already rejected by the repo's G1 audits.
- Remaining: VOQ priced against a promotion/rollback certificate state with P(advantage survives to release) in
  E[J|wait]; validity when propensities are decision-dependent for a paired policy-cost null (Xu et al. cover risk
  control, not paired promotion).
- Comparators: uniform; front-loaded; Drift2Act active audit; ASI/Xu propensities; Gong-Zhang adapted; pending cap;
  fixed schedule; deadline heuristic; ADOWIP priority.
- Verdict: test only as a label-request replacement; if it does not beat pending cap/fixed schedule, stop (Mandate Q2).

### F5 Pending-aware / deadline-aware querying -> PLAUSIBLY_DISTINCT (weak-to-moderate)
- Closest: Pham-Kottke-Krempl-Sick, Machine Learning 2022 (S; verification-latency active learning, utility estimated at
  label arrival); survey arXiv 2106.09170 (S); ADOWIP (V; pending queue but acts on arrivals, not on requests);
  Drift2Act (V; no explicit pending queue); Prudent-Banker arXiv 2605.23351 (V; safe delayed bandits, delay-calibrated
  restart threshold); para-active learning arXiv 1310.8243 (S).
- Overlap: delay-aware label utility (Pham) and budgets counting pending requests. Nothing found tying request value
  to a certificate deadline / promotion horizon and P(label arrives before the window closes).
- Remaining: pathwise budget accounting of in-flight requests; release-time- and deadline-aware value.
- Differences: Pham targets classifier-training utility, no anytime-valid guarantee.
- Comparators: pending cap, fixed schedule, Pham FS, ADOWIP, Drift2Act as-is.
- Caveat: may be absorbed as an engineering heuristic; internal Lane A shows small headroom.

### F6 Cost-aware RAR Gate-2/3 -> PLAUSIBLY_DISTINCT for Gate-2 only; Gate-3 pricing is KNOWN
- Closest: RAR Cost-Aware Binary (V; degradation x horizon vs rho); CARA, Mahadevan-Mathioudakis arXiv 2310.04216 (V);
  Zliobaite-Budka-Stahl, Neurocomputing 150:240-249 (2015) (S); The Challenger arXiv 2512.18390 (V; v2 July 2026).
- Overlap: cost-aware retrain gating by expected gain x horizon is published (RAR, CARA, Zliobaite).
- Remaining: cost/value-of-waiting gating of the label-fraction threshold theta_L (Gate-2); a recovery-gain estimate
  rather than incumbent degradation (RAR notes Gate-3 measures loss, not recovery).
- Comparators: RAR unmodified; RAR Cost-Aware Binary (mandatory); CARA; Zliobaite ROI rule; Challenger OSE/GSE/LSE.
- Caveat: host-internal and incremental; acceptable under the acceptance bar only if it beats Cost-Aware Binary.

### F7 Canary exposure optimisation (p1, W1, W2) -> PLAUSIBLY_DISTINCT (search coverage thin)
- Closest: RAR (V; fixed exposure); Lindon-Sanden-Shirikian KDD 2022, arXiv 2205.14762 (V; sequential canary tests);
  CMAS arXiv 2610.31436 (V; promotion gate + canary + rollback, empirical not valid bounds); Feng et al. UAI 2022,
  PMLR 180 (V; alpha-recycling for repeated updates); Karampatziakis et al. ICML 2021 (V; gated deployment);
  Conformal Policy Control arXiv 2603.02196 (V; ICML 2026; reference policy regulates a new policy).
- Overlap: sequential canary testing and risk-calibrated exposure exist; no source found that optimises canary
  exposure/duration against an economic ledger with delayed labels.
- Not searched: ramp-up optimisation in experimentation-platform / safe-rollout bandit literature -> may become HIGH_OVERLAP.
- Comparators: RAR fixed canary; RAR no-canary (its own ablation beats canary on 11/13 streams); Lindon sequential
  canary; CPC-style regulated exposure.

### F8 Drift2Act certificate scheduling -> HIGH_OVERLAP
- Closest: Xu et al. 2406.10490 (V); ASI (V); PPRM arXiv 2602.02229 (V; ICML 2026 per repo docs, PMLR page not
  re-fetched); Kilian et al. arXiv 2505.18000 (V; anytime-valid PPI); Csillag et al. arXiv 2502.04294 (V; ICML 2025);
  Podkopaev-Ramdas arXiv 2110.06177 (V; ICLR 2022, delayed batches); WATCH arXiv 2505.04608 (V; ICML 2025).
- Overlap: replacing uniform audit sampling with model-guided propensities and a valid IPW/PPI certificate is
  published for risk control; summable per-step delta_t is a generic allocation.
- Remaining: decision-triggered alpha spending under serial dependence and delay.
- Comparators: Drift2Act as-is; Xu propensity policy; PPRM; Podkopaev CS.
- Verdict: reposition as an ablation/upgrade of the host.

### F9 Reversal-aware rollback -> PLAUSIBLY_DISTINCT, with internal negative evidence
- Closest: RAR (V; rollback causes, soft/hard holds, label-frontier vs live-edge clocks); Drift2Act (V; cooldown-only);
  Prudent-Banker (V); CMAS (V); Gafni et al. (V; contamination after change).
- Overlap: rollback triggers, holds, cooldowns are in RAR/Drift2Act; baseline-safe delayed learning exists for bandits.
- Remaining: using the reversal and delay to decide rollback. GAVE-R FreshCheck did not beat strong rollback
  comparators, so a new mechanistic hypothesis is required before re-testing (Mandate Phase 0).
- Comparators: RAR rollback rules; Drift2Act gate; Page-CUSUM post-switch; Prudent-Banker fallback.

### F10 Coupled information/intervention budgets -> HIGH_OVERLAP
- Closest: Gong-Zhang ICML 2026 (V; paid observations, free-budget phase transition, budget-adaptive meta-controller);
  Cheng-Zhou-Ji ICML 2023, PMLR 202 (V); RCCDA arXiv 2505.24149 (V; NeurIPS 2025); Drift2Act (V; label budget + lambda*c +
  cooldowns); ADOWIP (V); repo audits (R) `switching_recent_paid_delay_movement_prior_audit_v1.md`, `switching_cheng_audit_v1.md`.
- Overlap: joint spending of label and action budgets in one utility is the Drift2Act design; budget-regime
  meta-controllers are Gong-Zhang.
- Remaining: shadow-price coupling with a validity guarantee; Lane A found calendar-optimal at tight risk, small
  proven gaps elsewhere.
- Comparators: Drift2Act; Gong-Zhang adapted; RCCDA; Cheng batched observation.
- Verdict: reposition as the Q3 factorial test, not a mechanism claim.

## Coverage of the 10 mandate topics
1. Decision-aware active labeling: ADOWIP, Horvitz (S), Xu, ASI, Cai-Kandasamy, Setoudehtanzangi-McLachlan, Ham SCALE.
2. VOI under delayed feedback: Pham (S), ADOWIP, survey 2106.09170 (S), label-delay continual learning NeurIPS 2024 (S).
3. Controlled sensing / costly sequential testing: Chernoff 1959 (U), Naghshvar-Javidi (V), Li (V), Ferrari (V), Ren (S), Lau-Tay (V), Krishnamurthy (V).
4. Markov tests, irregular/adaptive observations: Sethi (V), Fields (V), Fauss (V); irregular-sampling sequential Markov e-test: none found.
5. Restart mixtures: e-detectors (V), Lorden (S), Pollak (S), Gafni (V).
6. Prediction-powered monitoring: PPRM (V), WATCH (V), Podkopaev-Ramdas (V), Kilian (V), Csillag (V), ASI (V), Xu (V).
7. Cost-sensitive replacement: Challenger (V), CARA (V), Zliobaite (S), RAR baseline (V).
8. Staged deployment / canary: RAR, Lindon, CMAS, Karampatziakis, Feng, CPC (all V).
9. Rollback with delayed outcomes: RAR, Drift2Act, Prudent-Banker (V); Joulani-type delayed bandits (U).
10. Meta-controllers: Gong-Zhang, Drift2Act, RCCDA, Cheng (V).

## Implications for WP5 candidate grammar
- Emit F1/F2/F3 only as baselines/ablation arms, not novelty-bearing candidates.
- Prioritise F5, F6-Gate-2, F7, each against the named mandatory comparator.
- `closest_prior_art` fields cite IDs from `registry/prior_art.yaml`.
- Open verification debts: Drift2Act App. D.7 and Sec 4; RAR Sec 8 and harness URL; Sethi App. G.4 baselines; Pham MLJ
  2022; Horvitz 2007; Chernoff 1959; Joulani delayed bandits; GitHub code search; OpenReview.
