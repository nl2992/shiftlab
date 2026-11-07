# HG x H2c novelty and reducibility audit (Amendment A1.7, written before any stage-3/4 result)

Status: reducibility analysis and literature check. Nothing here is a result. No novelty claim is made. Companion to `THEORY_AUDIT.md`; the code references are to `src/shiftlab/hgxh2c/{engines,grammar,baselines}.py` as in the working tree on 2026-10-31.

## 1. Bottom line (before results)

1. The per-track factor is a Csillag-style prediction-powered e-value with a predictable stake. Nothing in the S, Q or R channels changes this form (Section 2).
2. H2c is discounted Kelly on cost with the moment ratio replaced by the Brier moment ratio (known result X1, max |dlogW| = 9e-16, `00_ANCHOR_SPEC.md` section 1.2). HG is the same construction in the other direction with a sign gate. In the grammar these are the single-operator candidates `(BC,S,ratio a=1 ref=0)` and `(CB,S,gate thr=0)`. They are the anchors, not discoveries.
3. S-channel operators `ratio` and `shift` lie (up to the discount of the guide track and the final clip) in the function class of the joint contextual ONS/Kelly control, whose stake is linear in both tracks' relative Kelly positions. Proposition A0 says that an information-matched gain over that control can only come from the optimisation procedure or a coarser information set, not from information. So an S-channel win over joint contextual ONS would be an optimisation or regularisation finding, with weak novelty.
4. Q-channel operators are Xu-style predictable IPW querying (active, anytime-valid) with the query driven by the other track's wealth or residual variance. R-channel operators are stake-estimator resets or discount switches, not wealth-level start-time mixtures, so they are NOT e-detector constructions. The cross-track trigger is the only new element in both.
5. The most plausible surviving candidate classes are Q and R channels with cross-track triggers, and the pre-registered combinations of them, evaluated against the strongest baseline. The decision table (PROTOCOL section 10) decides how much is claimable. Prior expectation: "useful combination, weak novelty", with a minority chance of a scoped result in the delayed, sparse-label regimes.

## 2. Reducibility by channel and family

Notation as in `THEORY_AUDIT.md`: x = h + (Q/q)(R - h) - theta, f = 1 + lam x.

### 2.1 (i) Prediction-powered e-values (Csillag et al.)

Csillag, Struchiner and Goedert (arXiv:2502.04294, accepted ICML 2025 per the arXiv page) state that every e-value procedure has a prediction-powered counterpart, e^PP = e(yhat) + (Q/q)(e(y) - e(yhat)). Take e(y) = 1 + lam (y - theta), affine in the loss with predictable lam. Then e^PP = 1 + lam [ (h - theta) + (Q/q)(R - h) ] = 1 + lam x exactly. Hence:

- Every candidate's per-track factor is a special case of a PP e-value with an affine base e-value and a predictable bet. Test E5 below checks this identity to 1e-12 on random draws, so no engine-side algebra drift remains.
- Predictable q_n (the Q channel) is within the class provided the propensity is known and positive; Csillag state the construction for known sampling probabilities. I read the abstract of 2502.04294; I did NOT read the body, so the exact statement on adaptively chosen q_n and the form of their Algorithm 1 are [UNVERIFIED] here. Stage 1 lists Csillag as "independent reproduction", not source-reproduced (`03_BASELINE_REGISTRY.md`).
- S and R channels only change lam. They cannot leave the class.

Verdict: the PP correction is not a contribution of any candidate. Only the choice of lam_n and q_n as functions of the other track can differ.

### 2.2 (ii) Joint contextual Kelly / ONS

`JointContextualONS` (`baselines.py`): stake_track = hi_track x clip(w_track . [1, u_B, u_C], 0, 1), u = relative Kelly position min(K, hi)/hi, w fitted by ONS, initial w = own-track indicator.

| Operator | In the joint class? | Remark |
|---|---|---|
| S `ratio` (a, ref=0) | Yes, lam = hi[(1-a) u_tgt + a u_src] up to the guide discount (0.995/0.99 vs base) and clipping | w = (0, 1-a, a). Differs only by the guide's gamma and the clip. a=1 is H2c |
| S `ratio` (a, ref=1) | Yes (own Kelly only) | collapses to discounted Kelly on cost (known X1) |
| S `shift` | Yes, w = (0, 1, a) before the clip | |
| S `gate` | No (indicator) | HG is gate with thr=0. Not linear in u, but a thresholded function of the source's mean |
| S `temper` | No (min with a function of source log-wealth) | |
| Q channel | Outside (joint ONS does not move q) | |
| R channel | Outside (joint ONS has no reset) | |

Consequences. (a) A fixed-parameter `ratio`/`shift` candidate is a point in a class that the control searches over online; any advantage over the control is the control's learning cost (burn-in, ONS regret), which is an optimisation fact. (b) `gate` and `temper` are not in the class, so they are the S-channel candidates that could differ in kind, but they are single threshold rules with an obvious linear-class approximation.

### 2.3 (iii) Multivariate gambling (Ryu and Wornell)

Ryu and Wornell, "Gambling-Based Confidence Sequences for Bounded Random Vectors", ICML 2024 (arXiv:2402.03683, PMLR 235:42856-42869). The relevant device is a vector bet with factor 1 + lam . x and a mixture over bets. In this repo `VectorMixMonitor` (J only) is a formula-level port of the mixture portfolio, not a reproduction (the ONS-adaptive variant is omitted).

- A cross-stake candidate keeps two separate wealth processes and combines them with bonf or mix. A vector bettor keeps one wealth with a joint bet. For the J null (both one-sided nulls) the vector factor 1 + lam_B x_B + lam_C x_C with lam >= 0 is valid under dependence, and it is exactly the fix P-2 for the invalid product combiner (`THEORY_AUDIT.md` 4.3). Any J-track gain of a `prod` candidate over bonf/mix must be compared with this baseline, and the product itself cannot be reported as a valid method.
- Per-track B or C claims (track-level alarms) are outside the scope of a vector bettor, but the vector factor can be used with one lam set to 0 and then reduces to a per-track bet.

### 2.4 (iv) Timans GRAPA

Timans, Verma, Nalisnick and Naesseth, "On Continuous Monitoring of Risk Violations under Unknown Shift" (arXiv:2506.16416, UAI 2025, PMLR 286:4204-4226). Not an ICML paper; earlier task text called it GRAPA/ICML, which I could not confirm: my search snippets for that page do not mention the name GRAPA. The repo's reproduction (`02_NATIVE_REPRODUCTION.md`) runs authors' `approx_grapa` and `grid grapa` scripts, so the grapa bases (`BASES`) are base engines that the hooks sit on top of. GRAPA originates in Waudby-Smith and Ramdas (JRSSB 2024, arXiv:2010.09686, as cited in `references/closest_competitors.md`; [UNVERIFIED] by me in this session). Verdict: a base engine, not a channel. The question for stage 4 is whether a transfer operator improves on `grapa` base alone, not whether GRAPA is new.

### 2.5 (v) Xu active querying

Xu, Karampatziakis and Mineiro, "Active, anytime-valid risk controlling prediction sets" (arXiv:2406.10490, NeurIPS 2024): predictable labelling probability, inverse-propensity correction, betting e-process, anytime-valid. `grammar` Q operators:

| Operator | Relation |
|---|---|
| `ipw` | `xu_query(src)` applied with the SOURCE track's released residual variance, tempered by exponent e. With src = tgt it is the Xu variance policy. The only new element is using the other channel's residual variance |
| `boost`, `straddle` | Predictable query inflation as a function of the other track's log-wealth: an active-querying schedule. Heuristic, not variance-optimal |
| `pace` | Budget pacing (remaining budget per remaining step vs design rate) times a wealth factor. Standard budget control, wealth coupling is the new piece |

All remain within Xu's class (predictable q, IPW). A common query reveals both B and C: that sharing is a property of the contract (one tape, one U), not a mechanism.

### 2.6 (vi) Restarts, start-time mixtures, e-detectors

Shin, Ramdas and Rinaldo, "E-detectors: a nonparametric framework for sequential change detection" (arXiv:2203.03532; New England Journal of Statistics in Data Science). Their detectors bet from every start time and sum (SR) or max (CUSUM) the resulting e-processes, giving ARL bounds. Dandapanthula and Ramdas (arXiv:2501.04130) combine e-detectors with e-BH / e-Bonferroni across streams, valid under general dependence across streams.

Implemented R operators do not do this. `restart` and `soft` reset the target's stake-estimation state (moments, ONS state) and leave the wealth as one product; `gamma` switches the discount. They are adaptive forgetting for the stake estimator, closely related to windowed/discounted Kelly and to the tracker window W in Timans. They do not give a start-time mixture, a change-point detection delay guarantee or ARL semantics. Verdict: `restart`, `soft`, `gamma` are not e-detectors, and they should not be described that way. The `soft` operator is the stake-state analogue of a wealth-level soft restart that would be INVALID without a capital ledger (`THEORY_AUDIT.md` 3.3). A real start-time mixture candidate would be a new operator and would have to be compared with e-detector SR on the same streams.

Cross-track trigger. Using the other track's log-wealth crossing to reset a stake estimator is a combination of known parts. The question is empirical: does it beat a source-independent restart schedule (periodic, or discount)? Test E6.

### 2.7 (vii) Proposition A0 consequences

From `docs/promising_directions/03_FORMAL_PROBLEM_AND_INFORMATION_CONTRACT.md` (worktree `shiftlab-promising-directions-2026-10-30`): if the query rule is allowed to use every released label, free observation and past query, then the "label-history-adaptive acquisition plus optimal action" class equals the joint class; an information-matched gap between jointly and separately designed procedures can arise only from (ii) the optimisation procedure (coordinate-wise vs team optimum), (iii) a strictly coarser information set, or (iv) a surrogate objective. Applied here:

- Joint contextual ONS and every candidate use the same released information (both tracks' released histories, free proxies, spending). So "joint beats separable" cannot be claimed as an information result. A candidate that beats joint ONS wins by optimisation (learning rate, burn-in, clip structure, fixed vs fitted weights) or by a tied information restriction that we should state.
- Independent HG + H2c are "separable" because each stake is allowed only the guide moment of the other track, not the other track's wealth or arbitrary functions of its history. Any gap between a candidate and independent HG+H2c is a gap from richer information, which is real; the gap to joint contextual ONS is not.
- Fixed mixtures (control 3) and the per-track pair share the same information and differ in the combiner.
- Caveat in A0 itself: it was proved for the repository's decision game with public randomness; its use here is an analogy for the information structure of the monitoring contract, with U_n public. The analogy requires that no candidate uses private randomness, which the tape contract guarantees.

## 3. Candidate classes that could still be genuinely novel

Ranking by what is not already a special case of Sections 2.1-2.6:

1. Cross-track Q-channel schedules (`boost`, `straddle`, `pace`, `ipw` with the source's variance) in delayed, sparse-label regimes. A single query yields both B and C, so the allocation problem is genuinely two-track. Reducible to Xu with a different objective; novelty would come from a valid allocation that improves delay at matched labels. Strong baseline: Xu variance policy on the target alone.
2. Cross-track R-channel triggers (restart on the source's crossing, gamma switch), if they beat a source-independent forgetting schedule at matched parameters. Reducible to a discounted Kelly with schedule; the contribution would be an empirical finding about cross-risk timing in `lagged` and `intermittent` families.
3. S-channel `gate` and `temper` as nonlinear transfer rules. HG is a gate; novelty is limited to new variants.
4. Compositions (depth 2 per slot and several slots on). The search space is large and each element is a known part; a finalist is credible only if the mechanism ablations (remove a channel) and the controls below attribute the gain.
5. A deployable selector over candidates by design-time observables. A selection rule is not a new monitor; it needs its own validity argument (`THEORY_AUDIT.md` item 9) and the evaluation protocol of PROTOCOL section 7.

Not novel by construction: any `prod`-combiner result (invalid), PP correction, Kelly/ONS/GRAPA bases, H2c, HG, `ratio`/`shift` against joint contextual ONS.

## 4. Numerical equivalence tests required in stage 4

Run on audit seeds (`PARTITIONS["audit"]`) before confirmation, thresholds as stated. All use the existing `audit_equivalence` machinery where possible.

| ID | Test | Pass criterion for "equivalent" (candidate is reduced to the baseline) |
|---|---|---|
| E1 | `(BC,S,ratio a=1 ref=0)` vs discounted Kelly on cost with Brier moment ratio (X1); `(CB,S,gate thr=0)` vs HG | max abs dlogW < 1e-9 over B and C paths |
| E2 | Candidate vs `JointContextualONS().monitor()` and vs the same candidate with all slots empty | max abs dlogW < 1e-9 (already in `audit_equivalence`) |
| E3 | Function-class test: refit the joint class with the candidate's S operator frozen (fit w by least squares of the candidate's stake on [1, u_B, u_C]); report R^2 and the maximum stake residual | R^2 > 0.99 and J gap to the refit < 1 se means "in class"; otherwise report as outside the linear class |
| E4 | Query-only candidates vs `xu(target)` with matched budget; `ipw` e=1 with src=tgt vs Xu | identical alarms on at least 99% of seeds and mean |dlogW| < 1e-6 |
| E5 | PP identity: engine factor vs `1 + lam*(e_PP - 1)` computed from the Csillag formula with e(y) = 1 + lam (y - theta); plus exact enumeration of E[f] over (Q, R) for random finite supports | max abs diff < 1e-12; E[f] <= 1 for every enumerated null distribution |
| E6 | R controls: periodic predetermined restart at matched rate; discounted Kelly with gamma schedule; no restart | Delta_J to the best control must be significant for the candidate to count; otherwise label "no cross-track benefit" |
| E7 | J candidates vs `VectorMixMonitor`, fixed mixtures w in {.25,.5,.75}, Bonferroni of independent HG and H2c | paired Delta_J as in PROTOCOL section 9 |
| E8 | Cyclic time-shift of the source track (negative control, PROTOCOL section 9) | candidate gain must disappear (Delta_J vs its own no-transfer base within noise); if gain persists, it is not cross-risk transfer |
| E9 | Channel ablations (`Candidate.without(i)`) and `compile_batch(..., ctx_replace=True)` mechanism control | report which channel carries the gain |
| E10 | `prod` combiner candidates | excluded from finalists; if reported, labelled INVALID_COMBINER (THEORY_AUDIT F1) |
| E11 | Size audit on null_stationary / null_boundary with the finalists, 20,000 streams per family | Clopper-Pearson upper bound <= alpha for bonf/mix candidates; null_ar reported as stress only |

## 5. Literature check (novelty-check skill, run 2026-10-31)

The skill's cross-model reviewer step (Codex MCP, `gpt-6-astra`) is not available in this session (no `mcp__codex__*` tools are registered). It is recorded as REVIEW_UNAVAILABLE; the verdict below is the executor's own, based on web search plus fetches of arXiv records. The `verify_papers.py` helper was not available; citations below were checked against the search result or the arXiv page fetched in this session, and anything taken only from repo files is tagged [UNVERIFIED].

Core claims searched: (1) cross-risk transfer between two sequential betting monitors through stake; (2) through query probability; (3) through restart/forgetting; (4) multi-stream or multivariate betting; (5) prediction-powered e-values with adaptive querying. Years 2024-2026.

Queries (WebSearch, standard unless noted) and findings:

1. "multi-stream sequential testing by betting e-process information transfer between streams stake e-values 2025". Found PEAK, "Peeking with PEAK: Sequential, Nonparametric Composite Hypothesis Tests for Means of Multiple Data Streams" (arXiv:2402.06122; authors not checked); a Waudby-Smith and Sandoval 2025 paper on universal log-optimality (identifier and attribution from a search snippet only, [UNVERIFIED], not read). No cross-stream stake transfer found.
2. "anytime-valid monitoring ... cost-sensitive e-process auxiliary risk guided betting stake prediction-powered sequential". Found Xu et al. (2406.10490), a horizon-aware betting preprint (March 2026; identifier not verified, not cited), stochastic-dominance betting (arXiv:2604.21851, title only). No cost/predictive cross-track stake.
3. "Ryu Wornell multivariate gambling ... Csillag prediction-powered e-values". Verified Ryu and Wornell (arXiv:2402.03683; PMLR 235) and Csillag et al. (arXiv:2502.04294).
4. "Timans risk monitor GRAPA ...". Verified Timans et al. (arXiv:2506.16416; UAI 2025; the earlier ICML attribution is wrong). No GRAPA mention found in the snippets.
5. "Shin Ramdas Rinaldo E-detectors". Verified (arXiv:2203.03532). A 2026 Ramdas paper on e-detector universality surfaced (arXiv:2608.12660, snippet only, not examined).
6. "Xu Active RCPS ...". Verified (arXiv:2406.10490; NeurIPS 2024; authors Ziyu Xu, Nikos Karampatziakis, Paul Mineiro).
7. "sequential change detection e-process multiple correlated streams side information transfer betting 2025 ...". Found Dandapanthula and Ramdas (arXiv:2501.04130): multi-stream change detection with e-BH/e-Bonferroni; no cross-stream stake or side-information transfer.
8. (extended) "e-process betting two correlated risks cross stake guided by auxiliary loss ... 2026". Nothing matching. Related: monitoring risks by betting (Timans), e-backtesting with predictable bets (arXiv:2610.17681, title only).

Finding: I found no paper that proposes bidirectional cross-risk transfer (predictive-loss track guiding a decision-cost track and the reverse) through stake, query probability and restart in sequential e-value testing. This is a negative search result from eight queries through a general-purpose search engine; it does not prove absence. Not covered: Semantic Scholar/OpenAlex API searches, citation-graph forward search from Csillag/Xu/Timans/Ryu-Wornell, and the repo's own earlier negative prior-art check for H2c/HG (`docs/h2c_next`, `hg_validation`), which I did not re-read.

Verdict under the skill's limits: PROCEED WITH CAUTION as a methodological direction, because known parts compose and the nearest special-case results are named: Csillag (PP e-value form), Xu (predictable IPW querying), joint contextual Kelly/ONS (stake function class), Timans/Waudby-Smith and Ramdas (base engines), e-detectors (real restart semantics, not implemented here). The thin delta is: a cross-track trigger of query probability and of stake-estimator reset, tested against matched-information controls. What would make it carry: a finalist that beats joint contextual ONS and the Xu/forgetting controls on paired Delta_J with the cyclic-shift control removing its gain. If the best result is only versus independent HG+H2c, it is "useful combination, weak novelty".

## 6. What to say in any paper (guardrails)

- Call the R channel "stake-estimator restart / adaptive forgetting", not "e-detector" or "start-time mixture".
- Call the factor "prediction-powered e-value with predictable bet" and cite Csillag; call H2c "discounted Kelly with Brier moment ratio" (X1).
- Do not call `prod` a valid combiner; if reported, label it INVALID_COMBINER.
- State the joint-filtration null and the information-matched caveat from Proposition A0 next to any comparison with joint contextual ONS.
- Timans appeared at UAI 2025; Csillag at ICML 2025 (arXiv record).
- Post-results addendum (next attended session): update Sections 3-5 with the stage-3 E1-E11 outcomes, rerun the cross-model reviewer if available, and run `result-to-claim` and `experiment-audit`.
