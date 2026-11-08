# Baseline fidelity audit: SOTA comparator panel (2026-11-08)

Scope: every entry in `scripts/qsg_methods_search/sota_extra.py` `FIXED` (sota_extra.py:73-99) and every tunable family in `FAMILIES`
(sota_extra.py:101-111: gongT, upf, wald, hoef, smarg, dwell, econF, and a `chalgse` family added during this audit). Prior material:
`origin/claude/shiftlab-methods-strategy-dba13e:docs/sota_fidelity/{LEDGER,REPORT}.md` and `impl/*.md`, `docs/qsg_methods_search/novelty_audit.md`
(section 2 note A), `sota_comparator_matrix.md`, `sota_expansion/01_PRIOR_ART_AUDIT.md`. No papers were fetched in this pass; paper-side claims are
taken from repo docstrings, the ledger and the prior-art audit, and are marked as such. No code was edited.

Fidelity classes. A = source-faithful (decision rule and constants as printed, or parity-checked against author code). B = common-contract
adaptation (the source's core rule is kept, but acquisition, feedback model, deployment or stopping semantics are replaced). C = heuristic inspired by prior
work (the decision rule is not the source's, or is a ShiftLab repair attached to a host). D = non-comparable. Guarantee class: "certified" means the
code is built to bound false promotion at alpha under a stated null; "uncertified" means no such claim. Neither implies a published theorem covers the
adapter. **No entry in this panel is class A**: author-parity tests that would justify A are skipped because `vendor_sota/` is empty (see 6).

Naming rule from the ledger and novelty audit: result tables must say "<method>-style adapter (T3)", never the paper's bare name.

## 1. Information discipline: verification from code

(a) **Labels reach policies only through released feedback.** `run_episode` (simulator.py:127-240) passes a policy an `Event` containing only
`model_predictions` and `context` (simulator.py:36-45, 170-176). The label array is read at simulator.py:191 (loss) and when a request is granted,
where it is packed into a `ReleasedFeedback` stored in `pending[t+delay]` (simulator.py:197-218). The only channel to the policy is
`policy.observe(due)` at simulator.py:181-183, called at the start of event `t` for requests whose `release_time == t`. `delay < 1` is rejected
(simulator.py:151). A runtime probe in this audit wrapped `observe` for 33 registered policies and found no feedback with `t_released - t_requested != delay`
or `event_id >= t_released` (0 violations; see 1(e)). Existing test: `tests/promising_directions/test_sota_simulator.py::test_label_arrives_only_after_the_declared_delay`,
`::test_policy_never_receives_unrequested_labels`.

(b) **Hard budget is enforced by the simulator.** `granted = bool(req.requested) and remaining > 0` (simulator.py:197); a refused request increments
`refused_requests` (simulator.py:198-199) and no label is released. `run_metrics` additionally asserts `res.requested_labels <= budget`
(suite.py:108-109). That assertion is a consistency check on the simulator, not independent enforcement. Test: `test_hard_budget_is_enforced_pathwise`.

(c) **Costs are counted by the simulator, not by the policy.** `net = total_loss + label_price * n_requested + switch_cost * n_switches`
(simulator.py:235); a switch is `deployed != prev` computed by the simulator from the policy's returned index (simulator.py:186-190). Policies may read
their own `cs` and `cq` as contract parameters (build_suite passes `T, B, cs, cq, alpha, delay`, suite.py:56) but cannot alter the charge. Note
`cq` is ignored by every policy below except as listed (price never enters a decision; e.g. upf docstring "Label price is ignored").

(d) **No policy uses the evaluator-side `gain`, `oracle_cost`, `exp_path` or `losses`.** `run_metrics` takes `gain` only for post-hoc diagnostics
(`better`, `worse`, `on_wrong`, `excess_vs_expected_G`; suite.py:115-128) and never passes it to the policy; `sota_nine._job` computes `gain` from the
realised mean and likewise passes it only to `run_metrics` (sota_nine.py:42-70). I grepped every registered comparator file
(`promising_directions/sota/competitors/*.py`, `failure_atlas_v2_flq/{r6_policies,strong_hosts,qce,qsg}.py`, `qsg_methods_search/{hurdles,eqs,eqs_d,d3_extra,p1_extra,upf_style_switch_timing}.py`)
for `gain|oracle|labels|losses|hidden`. Hits are docstring uses of "gain" meaning the challenger's expected advantage, plus the following **oracle-taking
classes that are not registered anywhere** (verified by grep over `scripts/`): `ORACLE_retrospective_best` (controls.py:283-291, reads full labels),
`ModelPickerNative` (model_picker.py:99-128, takes `oracle`), `ModelSelectorNative.run` and `run_block_pool_experiment`
(model_selector.py:149-197, 428-500, take `oracle`/`labels`), `CAMSNative`. The registered adapters (`ModelPickerDeploymentAdapter` model_picker.py:152,
`ModelSelectorCausalAdapter` model_selector.py:292, `CAMSDeploymentAdapter` cams.py:381) take no label array. Feedback `model_losses` (the 0/1 loss of every
frozen model on the queried event) is released data, so the paired loss is identifiable from one bought label (simulator.py:210).

(e) **Dynamic probe (smoke, not evidence).** One synthetic episode (T=2000, B=200, delay=100, cs=5, cq=0.05, 25% disagreement, challenger right 50% until
t=600 then 80%) through `build_suite(..., extra=EXTRA)` and `run_episode`: for all 25 FIXED entries, the frozen `EQSDp_l0.9_g0.2`, and the 8 synthetic-selected
family members (33 policies, one seed): labels requested <= 200 for all, `refused_requests == 0` for all, `check_budget_feasible` and `check_no_future_access`
(simulator.py:241-262) return no problems, and the wrapped-`observe` probe saw no early delivery. Largest label use 200; smallest among queried policies 79
(online_llm_picker) and 89 (model_picker_adapter). Script: `$TEMP/sm/smoke.py` (scratchpad, not committed). One seed on one stream; it checks the plumbing only.

**Residual information-discipline notes (not leaks):**
1. The task `delay` is passed to every comparator as a public contract parameter (suite.py:56, factory signature). It is used by `gong_zhang_paid_obs`/`gongT`
   (r6_policies.py:67-92: discount `gamma = 1 - 1/max(delay+1, T/5)` and normaliser `last = t - delay`), `qiu_delayed_movement` (block length `L = max(delay+1, T/20)`,
   r6_policies.py:94-117), `upf_*` (period completeness, upf_style_switch_timing.py header "Period completeness uses the task delay"; ledger records it as acceptable) and
   `xu_*` (`delay=` argument). The frozen EQSDp does not use `delay`. This is a mild asymmetry in favour of those comparators, in the open.
2. Event `horizon` and `T` are public contract parameters and enter every payback rule (`T - t`), including the frozen method.
3. `run_metrics` does not export `refused_requests`, so a policy that asks after exhaustion is invisible in `records.jsonl` (suite.py:118-129; sota_nine rows lack it).
   The simulator drops such requests safely, but any policy whose internal counters assume a granted label would be mis-modelled silently. Probe in 1(e) shows 0 refusals on this one stream.
4. `variance_min_ipw` is built with `class_prior=[.5,.5]` (suite.py:79). The streams have balanced random labels (suite.py:96-100), so this matches by construction, not by peeking; with two classes the score is the disagreement indicator regardless (variance_min.py docstring).

**Verdict: no leak and no budget breach found.** No policy can see an unreleased label; no policy exceeded the budget in the probe, and the simulator makes a breach impossible by construction.

## 2. Per-comparator audit

Common defaults unless stated: all "paced" comparators share `PacedDisagreementAcquisition(T, B, p_min=0.05, prior_rate=0.25, prior_w=20)`
(controls.py:28-50): query only on disagreements, propensity `clip(remaining / (rate_hat (T-t)), p_min, 1)`, 0 on agreement or exhausted budget. Evidence
is the paired outcome on queried disagreements, `model_losses[0]` vs `[1]` from released feedback.

### S1 Gong and Zhang, paid observations: `gong_zhang_paid_obs`, family `gongT`
1. Source: Gong and Zhang, "The Cost of Information: Phase Transitions in Contextual Bandits with Paid Observations", ICML 2026 (PMLR v306). Code:
   `r6_policies.py:67` `GongZhangPaidObsPolicy`; `d3_extra.py:10` `GongTuned` (window and margin).
2. Rule as implemented: `s_hat = sum_i (-x_i/q_i) gamma^(t-e_i)` over released events, `gain_left = (T-t) s_hat / den`; switch 0->1 if `gain_left > cs`, back if
   `-gain_left > cs` (r6_policies.py:75-92). Source (per prior-art audit, abstract-only): regret with a free-observation budget phase transition and a meta-controller;
   **it defines no payback or switching rule**. Class C: the rule is a repo invention (discounted IW point-estimate payback), named after the paper.
3. Changed/added: disagreement-gated paced querying; IW by frozen issue propensity; symmetric switch-back with no hysteresis; `gongT` adds
   `gamma = 1 - 1/W` and an additive margin `m` on `cs` (d3_extra.py:10-22).
4. Tuning: default untuned. Family grid W in {100,200,400,800} x m in {0,5,10,20} = 16 configs (d3_extra.py:35-38). Synthetic-dev selection `gongT_w100_m10`
   (D3, in-sample on the D3 seeds; `development_results.md` D3). Real-dev winner `gongT_w800_m20` (406.13, section 2b).
5. Information: released feedback only (observe at r6_policies.py:74-77); budget via shared acquisition + simulator; costs by simulator; no `gain`/`oracle`. Uses `delay` (note 1 in section 1).
6. Tests: `tests/test_atlas_r6_baselines.py` (5 tests); `tests/promising_directions/test_sota_controls.py` for the acquisition.
7. Class **C**, **uncertified** (r6_policies docstring: "the source guarantees do not transfer"; novelty_audit note A).

### S2 Qiu et al., delayed movement: `qiu_delayed_movement`
1. Source: Qiu, Jacobsen, Esposito, Zhang, "Parameter-free Dynamic Regret: Time-varying Movement Costs, Delayed Feedback, and Memory", arXiv 2602.06902 (ICML 2026).
   Code: `r6_policies.py:94` `QiuDelayedMovementPolicy`.
2. Rule: blocks of `L = max(delay+1, ceil(T/20))`; per block `z <- clip(z - eta*buf, -30, 30)`, fixed-share mix with `share = min(.5, k_sw/n_blocks)`,
   deploy `1[p > 1/2]` with `eta = 3 sqrt(k_sw/n_blocks)/L` (r6_policies.py:96-117). Source: comparator-adaptive, parameter-free OCO dynamic regret over a continuous action set,
   with delay treated as movement cost. The adapter is a fixed-share Hedge with hand-set constants: **not parameter-free and not the paper's algorithm**.
3. Changed/added: discrete two-model Hedge; IW differences; blocks; constants set in code; no switching-cost awareness (`cs` not used).
4. Tuning: none (defaults). Not a tunable family. Real-dev: included in the dev run as a fixed entry.
5. Information: as S1 (`observe` r6_policies.py:106-109); uses `delay` for `L`.
6. Tests: as S1.
7. Class **C**, **uncertified**.

### S3 Regol et al., UPF ("When to retrain"): family `upf` (`upf_d{.5,.8,.95}_m{50,100,200}`)
1. Source: Regol, Schwinn, Sprague, Coates, Markovich, ICML 2025 (PMLR v267; arXiv 2505.14903). Code: `upf_style_switch_timing.py:136` `UPFStyleSwitchTimingT3`
   via `p1_extra._upf` (p1_extra.py:13-16, 30-33). The T2 native port is `src/shiftlab/dive/upf_retraining.py` and is not what runs here.
2. Rule: periods of `m` rounds; IPW (Horvitz-Thompson) period cells on disagreement rounds; ElasticNetCV on `[arm, period, z_shift]` fitted on matured cells; Beta
   forecast (Eq. 51-52 with the T2 port's clipping); reversible backward recursion (Eq. 17-20), switch iff the strict `delta`-quantile of switch-cost-to-go is below keep (Eq. 16)
   (docstring steps 1-5). The Eq. 16-20 decision structure is retained; the forecaster, cells and reversibility are not the paper's.
3. Changed/added (docstring "Every deviation"): free period length `m`; reversible switching of two frozen models; IPW cells without the offline w=7 table;
   regressor weaker than native (arm and time only, models frozen); sigma includes an added HT variance (conservative double counting); decisions only at period
   boundaries; `T` must be a multiple of `m` (raises otherwise, upf_style_switch_timing.py:153-155; all 2000-length real streams satisfy it); label price ignored;
   warm-up `min_periods=3`, first possible switch near round 400 at delay 100; once the budget is gone, disagreement cells have zero propensity and the forecaster stops learning.
4. Tuning: grid delta in {.5,.8,.95} x m in {50,100,200} = 9 configs (p1_extra.py:30-33). Synthetic-dev selection `upf_d0.95_m50` (P1 stage 1, in-sample on D3 seeds,
   `comparator_panel_results.md`). Real-dev winner in section 2b.
5. Information: released feedback only; shared pacer; uses `delay` for period completeness; label-free z-shift (disagreement rate) since contexts are None.
6. Tests: `tests/qsg_methods_search/test_upf_style_switch_timing.py` (11 tests: 11 pass in the targeted run of this audit; the two torch cross-checks documented in the ledger were not separately observed here).
7. Class **B**: the Eq. 16-20 delta-quantile recursion is the paper's, but the forecaster and state space are substantially weaker. It is the closest thing in the panel to a rule-faithful
   adaptation of a non-certified method. **Uncertified** (no type-I control; nested quantiles not coherent, ledger/spec sec. 3). Smoke: `upf_d0.95_m50` ran in 10 s on one episode (slowest policy).

### S4 Model Picker: `model_picker_adapter`
1. Source: Karimi et al., "Online Active Model Selection for Pre-trained Classifiers", AISTATS 2021 (arXiv 2010.09818). Code: `model_picker.py:152` `ModelPickerDeploymentAdapter`;
   native `ModelPickerNative` (model_picker.py:~99) is not registered.
2. Rule: eta_t = eta_0/sqrt(t), exp-weights posterior over models, query iff Bernoulli(u_t) on disagreement with importance weight 1/u_t, posterior from IW loss; deploy
   **argmax posterior** (incumbent on ties) instead of sampling (adapter docstring, model_picker.py:155-160). The query/update arithmetic is ported from author code lines (module docstring).
3. Changed/added: argmax deployment (the paper samples `m*`, which would pay a switch nearly every round); delayed labels via `observe`; frozen issue-time weight; hard cap by the simulator
   (the author code never stops querying); ties never switch.
4. Tuning: none (`tuning_par=1.0`). Fixed entry.
5. Information: `observe` only; budget `remaining_budget <= 0` guard (model_picker.py:193); smoke: 89 labels used of 200.
6. Tests: `test_sota_model_picker.py` (13); author-parity test skips (model_picker.py needs `vendor_sota/model_picker`, test line 147).
7. Class **B** (query and posterior rules from author code, deployment replaced; T1 claim unverified because parity skipped). **Uncertified.** Degenerates to disagreement-gated sampling with two models.

### S5 Model Selector: `model_selector_causal`
1. Source: Okanovic et al., "All models are wrong, some are useful: model selection with limited labels", AISTATS 2025 (arXiv 2410.13609). Code: `model_selector.py:292` `ModelSelectorCausalAdapter`.
2. Rule: record gate over eligible disagreements in the last `window=50` arrivals (request the current event iff its expected posterior entropy is no worse than all other
   eligible ones), pacing `ceil(B (t+1)/T)`, deploy highest labelled-set accuracy (incumbent on ties). The class docstring says "NOT the published algorithm": Algorithm 1 argmins entropy over an unlabelled
   pool and labels the winner, which the simulator cannot express (no `target_event_id`).
3. Changed/added: pool replaced by a sliding record gate; pace cap; tie rule; `probability` reported as 1 (no IW). Ledger fix: record gate compares with 1e-12 tolerance.
4. Tuning: none (default `epsilon`, `window=50`). Fixed entry.
5. Information: pending labels leave the eligible set at issue and change the posterior only when released (docstring); no label array. Smoke: 199 labels.
6. Tests: `test_sota_model_selector.py` (22; 8 skipped per ledger because `vendor_sota/` is absent).
7. Class **C**: with two models and two classes it reduces to paced disagreement sampling plus majority-accuracy deployment (ledger); the pool algorithm is not exercised. **Uncertified.**

### S6 CAMS: `cams_adapter`
1. Source: Liu et al., "Online Contextual Active Model Selection" (CAMS), NeurIPS 2024 (arXiv 2207.06030). Code: `cams.py:381` `CAMSDeploymentAdapter` over `_CAMSCore`.
2. Rule: CAMS exp-weights and entropy-based query probability with the advice matrix `E` frozen at issue; deploy `argmax w_t` (the paper recommends argmax; the author code samples) (cams.py:382-396).
3. Changed/added: delayed labels; hard cap guard (cams.py:`request_labels` returns no draw at 0); `advice_fn=stack_advice(2, [])` supplies **constant policies only** (suite.py:76-78) because streams have no contexts, so
   the contextual machinery that defines CAMS is unused. Known paper-vs-code gaps: eta = sqrt(P/t) in code vs sqrt(ln m/t) in paper; u_t = 0 without floor when entropy is 0 (ledger).
4. Tuning: none. Fixed entry.
5. Information: released feedback only; smoke: 200 labels, 7 switches.
6. Tests: `test_sota_cams.py` (10; author-parity at line 269 skips: `vendor_sota` absent).
7. Class **B**, closer to **C** because the context-free configuration removes what CAMS is for. **Uncertified.**

### S7 DISCERN: `discern_style`, `discern_style+QCE+front`, `discern_design_floor`, `discern_design_floor+front`
1. Source: Balachandran, "Pay Only for Disagreement: Certified No-Regression Verdicts for Model Updates", arXiv 2609.17560 (no venue). No author code obtained.
   Code: `certificate_stops.py:474` `DiscernStyleStop`; `qce.py:116` `DiscernQCE`; `strong_hosts.py:53` `DiscernDesignFloor`.
2. Rule: HT increment `Z = (L/q) A d`, mapped to [0,1] with `c = 1/p_min`; predictable-plug-in empirical-Bernstein CS (WSR 2024 Thm 2); stop at `Safe(eps)` (promote) or `Regression` (keep), `eps = 0`.
   Printed-source departures: `v_i` carries the factor 4 per the cited theorem, whereas DISCERN's Appendix A prints it without; `lambda_max = 1/2` and the plug-ins are not printed by DISCERN.
   Learned judge routing is not used; Tier 0 is off by default; deployment semantics are ours.
3. Variants: `design_floor` sets `p_min = 0.25` (c = 4); `+front` queries every disagreement while undecided; `QCE` replaces the HT stream with unweighted queried-disagreement outcomes in request order
   (qce.py docstring; an internal repair, pointwise conditional null, range 1 instead of `1/p_min`).
4. Tuning: none; alpha = 0.05 fixed by the guarantee. Fixed entries.
5. Information: released feedback only; CS processes increments in event order and blocks on the earliest unresolved one (predictability under delay); smoke: `discern_style` 200 labels, 0 switches (it did not certify on this episode).
6. Tests: `test_sota_certificate_stops.py` (18), `tests/test_atlas_v2_qce.py` (6).
7. `discern_style`, `discern_design_floor`: **B** (Tier 1 CS printed construction, acquisition and deployment ours). `discern_style+QCE+front`, `discern_design_floor+front`: **C** (ShiftLab repair attached to a host; evidence and acquisition changed).
   **Certified** at alpha under the stated predictable-propensity null for the plain hosts (construction-level argument, delay handled by blocking; not a DISCERN theorem under delay). QCE+front variants: certified under the pointwise conditional null stated in qce.py, which is stronger than the event-average null.

### S8 SMCS: `SMCS+retain-incumbent`, `SMCS+QCE+front`
1. Source: Arnold, Gavrilopoulos, Schulz, Ziegel, "Sequential Model Confidence Sets" (arXiv 2404.18678). Code: `smcs.py:267` `SMCSDeploymentPolicy` over ported `SMCSInference` (smcs.py:131); `qce.py:141` `SMCSQCE`.
2. Rule: pairwise conditional-null e-process `prod(1 + lambda_ij (L_i - L_j))`, arithmetic-mean e-value over rivals, closure-principle adjustment, set intersection (excluded models never return). Deployment: retain the incumbent until it leaves the set (**ours**; SMCS is an inference object, not a switching policy).
3. Changed/added: selective-feedback construction `c_s = 1/q_s, lambda_s = 1/(2 c_s)` (ours, smcs.py docstring, "development argument, not a published guarantee"); paced acquisition; QCE variant swaps in aGRAPA-clipped bets on the unweighted stream.
4. Tuning: none; alpha = 0.05. Fixed entries.
5. Information: released feedback only. Estimand caveat: cumulative superiority, not current-regime (smcs.py docstring "THE caveat"). Smoke: 1 switch.
6. Tests: `test_sota_smcs.py` (15); numerical parity with the R code requires Rscript and `vendor_sota/smcs` (skipif at test line 139).
7. `SMCS+retain-incumbent`: **B** (evidence core ported from author R code, T1 unverified because parity skipped; selective-feedback and deployment ours). `SMCS+QCE+front`: **C**. **Certified** (pairwise nulls; development argument only for sampled/delayed feedback).

### S9 Xu et al.: `xu_acquisition_only`, `xu+front_only`
1. Source: Xu, Karampatziakis, Mineiro, "Active, anytime-valid risk controlling prediction sets", NeurIPS 2024 (arXiv 2406.10490). Code: `xu_acquisition.py:223` `XuAcquisitionPolicy`.
2. Rule: only the **acquisition score** `Q = clip(sqrt(var)/exp(norm_const), q_min, 1)` is taken (Player.py:177 per docstring), run inside ShiftLab's own single-null paired e-process (`b1.bet_from_stats`), margin 0, rollback by the
   sign-flipped process. No risk-controlling prediction set, beta grid or theorem is inherited. With two models and 0/1 loss the predictor-free score is constant, so the rule reduces to disagreement-gated uniform sampling at `budget/horizon`
   (docstring: their "oblivious" arm). The acquisition-derivation is "reconstructed, NOT checked against the paper text".
3. Changed/added: hard cap replaces their expected-proportion constraint; evidence side is ours; `+front_only` queries every disagreement while undecided.
4. Tuning: none; alpha = 0.05. Fixed entries.
5. Information: released feedback; labels bought before a switch are discarded (`live = s >= seg`); cap-suppression counters in the policy. Smoke: `xu_acquisition_only` 185 labels, `xu+front_only` 200.
6. Tests: `test_sota_xu_acquisition.py` (16), `test_sota_b3_plus_adapter.py` (8).
7. Class **C** (a component of a different method in ShiftLab's certificate). **Certified** only in the sense of the repo's own B3+ argument, not Xu et al.'s.

### S10 MOPE / gated deployment: `gated_deployment`, `gated_adaptive_range`, `gated_adaptive_range+front`
1. Source: Karampatziakis, Mineiro, Ramdas, "Off-policy Confidence Sequences" (ICML 2021, arXiv 2102.09540), Section 5.3 gated deployment. Code: `certificate_stops.py:549` `GatedDeploymentStop`;
   `strong_hosts.py:25` `GatedAdaptiveRange`. Author repo pinned at `a4b8584`, parity unchecked (comparator matrix).
2. Rule: MOPE Algorithm 2 hedged betting over the main-text bet set `C`, CS for `G = E[d]` via `w = L/q` on disagreements and `w = 1` on agreements, `r = (d+1)/2`; deploy when the lower CS exceeds 0, discard when the upper falls below 0. The mapping
   onto the paired difference is **not the paper's K^gd process** (certificate_stops.py docstring); appendices C-E not ported. `adaptive_range` evaluates `C` at `wmax_t = 1/q_t` (predictable) instead of the declared `1/p_min`.
3. Changed/added: ADAPTER for delay (block on earliest unresolved increment); CS frozen once budget is exhausted (no later zeros recorded); stopping and deployment pure functions of the verdict (no `cs`).
4. Tuning: none; alpha = 0.05; `p_min = 0.05`. Fixed entries.
5. Information: released feedback; smoke: 0 and 1 switches, 199/190/200 labels.
6. Tests: `test_sota_certificate_stops.py` (18), `test_atlas_v2_qce.py`.
7. `gated_deployment`, `gated_adaptive_range`: **B**. `gated_adaptive_range+front`: **C** (front-loading is a ShiftLab acquisition repair). **Certified** under the predictable-propensity null (construction-level; no published guarantee under delay or a hard cap).

### S11 Wald / Hoeffding LCB hurdles (internal control): families `wald`, `hoef`
Internal. Textbook origin: lower confidence bound on the advantage (Wald normal bound; Hoeffding bound `sqrt(log(1/gamma)/(2n))`). Code: `hurdles.py:25` `WaldLCB`, `:33` `HoeffdingLCB`, registered at sota_extra.py:38-44 with
`lam = 0.97` extending p1 grids at lam {.9,.95} (p1_extra.py:22-28). Same evidence (discounted counts), pacing (`stake=False`) and remaining-horizon payback as EQSDp; only the hurdle changes. Grids: wald lam {.9,.95,.97} x gamma {.05,.1,.2,.3} = 12; hoef lam x gamma {.1,.2,.3,.45} = 12.
Synthetic-dev selection: `wald_l0.9_g0.2`, `hoef_l0.9_g0.45` (P1, in-sample on D3 seeds). Real-dev winner in section 2b. **Uncertified** (no false-promotion claim). Tests: indirect only (`test_sota_controls.py` for the pacer); no dedicated hurdle test found.
Note: EQSDp arm B ties the Wald LCB on synthetic confirmation (`comparator_panel_results.md`: -0.05 [-0.28, +0.19]); this internal control is therefore a matched, not a weaker, comparator.

### S12 Horizon-pays family (internal controls): `economic_replacement`, family `econF`, `smarg`, `dwell`
Internal. Textbook origin: horizon-pays (Wan et al. KDD 2023; Chick, Forster, Pertile JRSS-B 2017). Code: `controls.py:186` `EconomicReplacement` (point estimate `delta = (2 phat - 1) r`, switch iff `delta (T-t) > cs + margin` after `min_obs`, one-way, no rollback);
`eqs.py:143` `EconFront` (adds q = 1 while undecided; eqs.py:143-154); `hurdles.py:41` `ScaledMargin` (`(adv - kappa) r (T-t) > cs`), `:52` `Dwell` (k-streak).
Grids: econF min_obs {5,10,15,25,40} x margin {0,5,10,20} = 20 (eqs.py:167-171); smarg lam x kappa {.05,.1,.2,.3} = 12; dwell lam x k {3,5,10,20} = 12. Synthetic-dev selection: `econF_mo5_m5` (D1), `smarg_l0.9_k0.2`, `dwell_l0.9_s5` (P1).
`economic_replacement` runs at its registered default (min_obs 15, margin 0). Note the D1 finding that the best econF is within about 0.5 of the best EQS variant (`development_results.md` D1: 357.56 vs 358.03).
Information: released feedback only (controls.py:225-237); budget via shared acquisition. **Uncertified.** Tests: `test_sota_controls.py` (15). Smoke: econ 200 labels, 1 switch.

### N1 Challenger-style payback with a Hoeffding bound: family `chalgse` (added to the registry during this audit)
Source: Digalakis Jr, Perignon, Saurin, Sentenac, "The Challenger: When Do New Data Sources Justify Switching Machine Learning Models?", arXiv 2512.18390. Code: `hurdles.py:71` `ChallengerGSE(HoeffdingLCB)` (switch once when the Hoeffding lower bound times `r (T-t)` exceeds `cs`; never switch back), registered at sota_extra.py:64-67.
Grid lam {1.0,.97,.9} x gamma {.1,.2,.3,.45} = 12; nominal default `chalgse_l1.0_g0.2`. The source has no label budget, delay or disagreement-only labels, and the paper's GSE/OSE are optimal-stopping procedures over growing data; the adapter is an irreversible Hoeffding-lower-bound payback on EQSDp's evidence clock with EQSDp's pacing. Class **C**, not B: the stopping/payback inequality is the paper's idea, but the evidence, acquisition and feedback model are ShiftLab's and I have not checked the adapter against the paper's algorithm (not read in this pass). **Uncertified.** Real-dev winner `chalgse_l0.9_g0.3` (404.28; section 2b); the nominal default is `chalgse_l1.0_g0.2`. Tests: none dedicated.

### e-SR: `two_sided_esr_label_clock`, `esr_rmmbets_fullalpha`
1. Source: Shin, Ramdas, Rinaldo, "E-detectors" (NEJSDS 2024; arXiv 2203.03532v4). Code: `shin_esr.py:344` `TwoSidedESRDeploymentAdapter`; ported byte-identical from the methods-strategy branch. T2 core (`algorithm3_grid`,
   `BoundedMeanEDetector`) reproduces the paper's NBA alarm (game 378); the R code was not executed.
2. Rule: per delivered label `z = loss(deployed) - loss(other)`, increment `1 + lambda z`; shiritaev-Roberts recursion `S_n = L_n (S_{n-1} + pi_n)`; mixture over an Algorithm 3 lambda grid; alarm at `>= 1/alpha_side`; two one-sided detectors alternate (promote
   against the incumbent, rollback against the deployed model); restart after any switch and drop labels requested at or before the switch. Calibration `rmm_matched`: start weights `1/B` over the first `B` labels (Remark 2.7, derived in the check file, not printed).
3. Changed/added: label clock (delivery order); start at every label; disagreement-conditional mean (no IPW); `delta_min = 0.05` design constant; shared pacer. `esr_rmmbets_fullalpha` additionally replaces the Algorithm 3 grid with RMM's fixed lambdas {.15,.3,.5} and gives each side the full alpha (`side_alpha_fraction=1.0`), so it is a matched control for the repo's RMM, not Shin's algorithm.
4. Tuning: none; alpha = 0.05. Fixed entries.
5. Information: released feedback only; in-flight labels dropped at a switch still consume budget (docstring). Smoke: both 200 labels, 1 switch.
6. Tests: `tests/sota_fidelity/test_shin_esr.py` (20).
7. `two_sided_esr_label_clock`: **B** (T2 core faithful, T3 deployment layer ours). `esr_rmmbets_fullalpha`: **C**. **Certified** per phase under `rmm_matched` (null: conditional mean <= m in the delivery filtration after the last restart); levels add across promote/rollback cycles, no joint guarantee; Markov persistence not covered.

### RCS: `shekhar_ramdas_rcs_t3_anyexcl`
1. Source: Shekhar and Ramdas, "Reducing sequential change detection to sequential estimation", ICML 2024 (arXiv 2309.09111). Code: `shekhar_ramdas.py:384` `ShekharRamdasDeploymentAdapter`, `stop_rule="any_excludes"` (registered at sota_extra.py:`_shekhar`).
2. Rule: repeated Hoeffding CSs (Definition 2.1; main-text schedule `lam_i = min(1, sqrt(8 log(2/alpha)/(i log(i+1))))`), CS started at `n` at level `1 - 6 alpha/(pi^2 n^2)` (Remark 2.5). Promote when any single CS is disjoint from `Theta0 = [1/2, 1]` (ShiftLab's `any_excludes`); the paper's joint-emptiness rule
   (`shekhar_ramdas_rcs_t3`) false-alarmed on 100% of constructed drifting-within-null streams (ledger finding 2), which is why the registry uses the variant. After promotion, a fresh partitioned RCS for rollback; `rearm=False`.
3. Changed/added: label clock; disagreement-conditional mean (no IPW); stopping rule differs from Definition 2.1; level spending; no cost awareness. The author code departs from the printed CS and was not ported.
4. Tuning: none; alpha = 0.05. Fixed entry.
5. Information: released feedback; pacer uses predictions and past query counts only. Smoke: 199 labels, 1 switch.
6. Tests: `tests/sota_fidelity/test_shekhar_ramdas.py` (17).
7. Class **B** (the stopping rule is a declared deviation, at best B). **Certified** by a union bound over Remark 2.5 levels under the composite conditional-mean null; independence of signs and constant delay assumed; not claimed under Markov persistence.

### ARW: `han_arw_label_clock`
1. Source: Han, Huang, Wang, "Model Assessment and Selection under Temporal Distribution Shift", ICML 2024 (arXiv 2402.08672v2 / PMLR 235). Code: `han_arw.py:263` `HanARWDeploymentAdapter` (re-implemented from printed equations; the author repo has no licence).
2. Rule: window argmin `k_hat = argmin phi_hat + psi_hat` (Goldenshluger-Lepski bias proxy plus variance proxy), pairwise comparison of mean paired loss in that window (Algorithm 2, tie rule `<= 0` -> incumbent), deploy candidate iff the windowed gap exceeds `margin = 0`. Constants `theory`: `M = b - a`, `delta' = delta/(3t)`.
3. Changed/added: one "period" per delivered label (`B_j = 1`); windows count labels in delivery order, not calendar time; shared pacer; no IPW; margin exposed (paper has none). The paper's guarantee is an oracle inequality for estimating `mu_t` at one fixed `t` under i.i.d., unselected, undelayed feedback.
4. Tuning: none (`theory`, margin 0). A margin-tuned variant would count as an equally-tuned baseline only if tuned on development seeds (ledger). Fixed entry.
5. Information: released feedback only. Smoke: 200 labels, 13 switches (flips on noise at margin 0, as the ledger records).
6. Tests: `tests/sota_fidelity/test_han_arw.py` (15).
7. Class **B** (T2 core faithful, T3 deployment mapping ours). **Uncertified** ("NO FALSE-PROMOTION GUARANTEE").

### Online LLM picker: `online_llm_picker`
1. Source: Turrin, Okanovic, Hoefler, Gurel, arXiv 2610.01592. Code: `online_llm_picker.py:69` `OnlineLLMPicker` from the paper's full text; no author code located.
2. Rule: `q_t = max{max_k Var_k * Hbar(p_t), eta_t}` (0 if all variances are 0), IW loss at the issue-time `q_t`, posterior `p ∝ exp(-eta_t Lhat)`, deploy argmax posterior (incumbent on near-ties).
3. Changed/added: exact-agreement loss for binary classification (the paper uses similarity losses and 130+ models); hard cap guard (`enforce_cap=True`, online_llm_picker.py:140); `eps = 1e-8` in `eta_t` is **ours** (not recoverable from the text) and controls early budget burn.
   Degeneracy: with 2 models the score carries no instance information (docstring).
4. Tuning: none. Fixed entry.
5. Information: released feedback; smoke: 79 labels, 3 switches.
6. Tests: `test_sota_online_llm_picker.py` (13).
7. Class **B** (formulas quoted from the paper; specialised loss, `eps` and cap ours). **Uncertified.**

### Variance-minimising IPW: `variance_min_ipw`
1. Source: Hara et al., "Active model selection: a variance minimization approach", ACML 2024 / Machine Learning 2024. Code: `variance_min.py:299` `VarianceMinStreamingIPW`.
2. Rule: query score `1[disagree] + eps` (the paper's Equation 8 form from author code, `eps = 1e-2`), running-mean normaliser over arrived events, rate `B/T`, deploy argmin of the **Horvitz-Thompson** loss estimate; the published estimator is LURE. The class docstring: "NOT the published method ... Report it under this name only."
3. Changed/added: streaming normaliser; HT replaces LURE; no switching-cost awareness; `class_prior = [.5, .5]`.
4. Tuning: none. Fixed entry.
5. Information: released feedback (propensities frozen at issue; `observe` raises on non-positive propensity); hard cap guard at variance_min.py:`request_labels`. Smoke: 192 labels, 13 switches.
6. Tests: `test_sota_variance_min.py` (13); its 4 author-parity tests skip at test line 120 because the author code needs numba (not vendor-related per the skip message).
7. Class **C** (score and sampler ported, estimator replaced; degenerates to disagreement sampling with two classes). **Uncertified.**

### QSG (internal, ours): `QSG`
Internal method from Failure Atlas v2, not a prior-art comparator. Code: `qsg.py:72` `QSG`. Rule: query-conditional started-mixture e-process over the grid p' in {.55,...,.95} on queried disagreement outcomes (`w_j = 1/(j(j+1))`), promotion cycles at `alpha/2^j`, rollback test at `alpha_r = 0.05`, front-loaded then paced acquisition (qsg.py:1-40 docstring).
Parameters set a priori, no tuning. **Certified** under H+ (`p_t <= 1/2` for every t) by the Ville argument in the docstring. Empirical caveat from the comparator matrix: QSG's false-promotion rate was 0.26 at rho = 0.8 (Markov persistence), i.e. the certificate does not survive dependence. Tests: `tests/test_atlas_v2_qce.py` (6). Smoke: 200 labels, 1 switch.

### Frozen method and control (for reference)
`EQSDp_l0.9_g0.2` is `EQSD(stake=False, lam=0.9, gamma=0.2)` (eqs_d.py:37; d3_extra.py:41): discounted Beta(k+1, n-k+1) quantile payback, paced acquisition, symmetric switching. **Uncertified**; no false-promotion claim. `CONTROL_never_switch` is `FixedModel(0)` (controls.py:251): zero queries, zero switches; trivially no false promotion.

## 2b. Real-dev selected configurations (from `dev_selection.log`)

`sota_nine.py dev` on the 14 exposed pilot streams. RD = real-dev winner (lowest mean net), SD = pre-existing synthetic-dev winner scored on the same real-dev streams. Arm B (frozen) real-dev score 410.43.

| family | RD winner (net) | SD winner (net) | next two RD |
|---|---|---|---|
| gongT | `gongT_w800_m20` (406.13) | `gongT_w100_m10` (416.17) | w800_m10 406.21; w800_m5 406.58 |
| upf | `upf_d0.8_m50` (423.86) | `upf_d0.95_m50` (427.97) | d0.5_m50 425.47; d0.95_m50 427.97 |
| wald | `wald_l0.97_g0.2` (403.66) | `wald_l0.9_g0.2` (410.57) | l0.97_g0.3 404.30; l0.95_g0.2 405.28 |
| hoef | `hoef_l0.97_g0.3` (405.48) | `hoef_l0.9_g0.45` (408.65) | l0.97_g0.45 405.70; l0.95_g0.45 406.30 |
| smarg | `smarg_l0.97_k0.2` (403.19) | `smarg_l0.9_k0.2` (410.37) | l0.97_k0.1 403.96; l0.95_k0.2 404.22 |
| dwell | `dwell_l0.97_s3` (407.61) | `dwell_l0.9_s5` (415.51) | l0.97_s5 408.18; l0.95_s3 410.13 |
| econF | `econF_mo5_m0` (401.75) | `econF_mo5_m5` (401.97) | mo5_m10 402.17 |
| chalgse | `chalgse_l0.9_g0.3` (404.28) | `chalgse_l1.0_g0.2` (408.03) | l0.97_g0.3 404.79; l1.0_g0.3 405.42 |

Every family's real-dev winner beats its synthetic-dev winner on the same real streams (by 0.2 to 10 net units), and winners favour longer memory (lambda 0.97) in the hurdle families. Several real-dev winners sit at the grid edge (gongT W=800, m=20; lambda 0.97), so the grids may be truncated. Fixed entries seen in the dev ranking: `model_picker_adapter` 404.30, `online_llm_picker` 404.99, `cams_adapter` 405.32, `QSG` 407.29 (full ranking in the log). The frozen arm B (410.43) is beaten on the dev streams by several tuned comparators (econF, smarg, wald), which is development evidence only; the confirmatory comparison is the registered nine-dataset run. Dev selection is in-sample on streams that are exposed pilot data, not a test.

## 3. Tests run

Command: `OPENBLAS_NUM_THREADS=1 .venv/Scripts/python.exe -m pytest tests/sota_fidelity tests/promising_directions -q -x -p no:cacheprovider -rs`.
Result of this audit (the single combined command did not finish inside 9 minutes while the machine was loaded by the dev run, so `tests/promising_directions` was run file by file, 170 s timeout each, in parallel, afterwards):
- `tests/sota_fidelity`: 62 passed, 1 skipped (as stated in the brief; not re-run separately here).
- `tests/promising_directions`, 21 of 23 files completed with **0 failures**: passed / skipped per file: a1_exact_separation 3/0, a1c_alpha_mechanism 2/0, a1d_mixture_comparator 3/0, a3_calendar_certificates 7/0, b1_certified_switching 9/0, b3_plus_experiments 6/0, b3_plus_policy 18/0, b3_real_data 7/0, research_loop 7/0, sota_b3_plus_adapter 11/0, sota_cams 10/6, sota_certificate_stops 30/0, sota_controls 17/0, sota_economic_stop 9/0, sota_model_picker 12/3, sota_model_selector 21/8, sota_online_llm_picker 13/0, sota_simulator 10/0, sota_smcs 17/4, sota_variance_min 12/4, sota_xu_acquisition 23/1. Subtotal 247 passed, 26 skipped.
- **Not completed (timeout at 170 s, no failure observed):** `test_b3_plus_screening.py` and `test_sota_sawade.py` (the latter is not a registered comparator in this panel). Their results are unknown, not passing.
- Companion tests (below): 58 passed.
Per-file counts in the section 2 test lines that quote the number of `def test_` functions are the static counts and differ from these parametrised run counts; the run counts here are authoritative.

Additional run (companion tests): `tests/qsg_methods_search tests/failure_atlas_v2 tests/test_atlas_v2_qce.py tests/test_atlas_r6_baselines.py`: **58 passed**, 0 skipped (118 s on a machine busy with the dev run).

Author-parity tests that need `vendor_sota/` are skipped or never exercised because the directory is empty/absent (the ledger's open action 1): `test_sota_cams.py:269` (`skipif`, `CAMS_identity.py`), `test_sota_model_picker.py:147`,
`test_sota_model_selector.py:403/431/445`, `test_sota_variance_min.py:120` (skip reason is numba, not the vendor directory), `test_sota_xu_acquisition.py:233` (author clone not present), and `test_sota_smcs.py:139` (also requires Rscript). Consequently the "T1 native, pending parity" status of CAMS, Model Selector, Model Picker, SMCS and variance-min is unverified, and no class A can be assigned.
The new ports have no author-parity test at all: Shin, Shekhar-Ramdas and Han are T2 audited mathematical ports (no T1 claim possible).

## 4. Summary table

Tuning column: "none" = registered default; "grid n, synth X" = grid size and the pre-existing synthetic-dev winner; real-dev winners are from `dev_selection.log` (section 2b). Leakage column: result of code inspection (section 1) plus the one-seed probe (1(e)); "clean" = no label, gain, oracle or budget issue found; "clean + delay" = also reads the public task `delay`.

| ID | Implementation | Fidelity | Guarantee | Tuning | Leakage check | Tests |
|---|---|---|---|---|---|---|
| S1 | `gong_zhang_paid_obs`; family `gongT_w*_m*` | C | uncertified | grid 16, synth `gongT_w100_m10`, real-dev `gongT_w800_m20` | clean + delay | test_atlas_r6_baselines (5) |
| S2 | `qiu_delayed_movement` | C | uncertified | none | clean + delay | test_atlas_r6_baselines |
| S3 | family `upf_d*_m*` (`UPFStyleSwitchTimingT3`) | B | uncertified | grid 9, synth `upf_d0.95_m50`, real-dev `upf_d0.8_m50` | clean + delay | test_upf_style_switch_timing (11) |
| S4 | `model_picker_adapter` | B | uncertified | none | clean | test_sota_model_picker (13; parity skip) |
| S5 | `model_selector_causal` | C | uncertified | none | clean | test_sota_model_selector (22; 8 skip) |
| S6 | `cams_adapter` | B (near C) | uncertified | none | clean | test_sota_cams (10; parity skip) |
| S7 | `discern_style`, `discern_design_floor` | B | certified (construction-level) | none, alpha .05 | clean | test_sota_certificate_stops (18) |
| S7 | `discern_style+QCE+front`, `discern_design_floor+front` | C | certified (pointwise null) | none | clean | test_atlas_v2_qce (6) |
| S8 | `SMCS+retain-incumbent` | B | certified (dev. argument) | none | clean | test_sota_smcs (15; R parity skip) |
| S8 | `SMCS+QCE+front` | C | certified (pointwise null) | none | clean | test_atlas_v2_qce |
| S9 | `xu_acquisition_only`, `xu+front_only` | C | certified (repo B3+ argument only) | none | clean + delay | test_sota_xu_acquisition (16) |
| S10 | `gated_deployment`, `gated_adaptive_range` | B | certified (construction-level) | none | clean | test_sota_certificate_stops |
| S10 | `gated_adaptive_range+front` | C | certified | none | clean | test_atlas_v2_qce |
| S11 | families `wald_l*`, `hoef_l*` (internal) | internal | uncertified | grid 12 each; synth `wald_l0.9_g0.2`, `hoef_l0.9_g0.45`; real-dev `wald_l0.97_g0.2`, `hoef_l0.97_g0.3` | clean | none dedicated |
| S12 | `economic_replacement`; families `econF_*`, `smarg_l*`, `dwell_l*` (internal) | internal | uncertified | econF grid 20 (synth `econF_mo5_m5`, real-dev `econF_mo5_m0`); smarg, dwell 12 each (real-dev `smarg_l0.97_k0.2`, `dwell_l0.97_s3`) | clean | test_sota_controls (15) |
| N1 | family `chalgse_l*_g*` | C | uncertified | grid 12, synth default `chalgse_l1.0_g0.2`, real-dev `chalgse_l0.9_g0.3` | clean | none dedicated |
| e-SR | `two_sided_esr_label_clock` | B | certified per phase | none | clean | test_shin_esr (20) |
| e-SR | `esr_rmmbets_fullalpha` | C | certified per phase | none | clean | test_shin_esr |
| RCS | `shekhar_ramdas_rcs_t3_anyexcl` | B | certified (union bound) | none | clean | test_shekhar_ramdas (17) |
| ARW | `han_arw_label_clock` | B | uncertified | none | clean | test_han_arw (15) |
| LLM | `online_llm_picker` | B | uncertified | none | clean | test_sota_online_llm_picker (13) |
| VMin | `variance_min_ipw` | C | uncertified | none | clean | test_sota_variance_min (13; parity skip) |
| QSG | `QSG` (internal) | internal | certified under H+, empirically violated at rho = .8 | a priori, none | clean | test_atlas_v2_qce |
| ref | `EQSDp_l0.9_g0.2`; `CONTROL_never_switch` | internal; control | uncertified; trivial | n/a | clean | n/a |

Class counts over the 20 external-method rows of the table (one per row; A/B/C of the worst member where a row mixes): A 0; B 10 (S3, S4, S6, S7 plain, S8 plain, S10 plain, e-SR plain, RCS, ARW, LLM); C 10 (S1, S2, S5, S7+front/QCE, S8+QCE, S9, S10+front, e-SR rmmbets, VMin, N1); D 0. Internal controls (S11, S12, QSG, EQSDp, never-switch) are not classed. Report the per-member class in any table, not the parent's.

## 5. Known defects or caveats

1. **No class A anywhere.** Parity tests are inert without `vendor_sota/`; restoring pinned clones needs the user's go-ahead (ledger open action 1).
2. **Names overstate fidelity.** `gong_zhang_paid_obs`, `gongT_*`, `qiu_delayed_movement` carry the paper's name but implement invented rules (class C). Tables must say "Gong-Zhang-style" and "Qiu-style" (novelty_audit note A, still not applied to the registry names).
3. **Public `delay` is an input to S1, S2, S3 and S9** but not to the frozen method. Minor asymmetry; report it.
4. **Context-free CAMS and degenerate selectors.** `cams_adapter` uses constant advice only; `model_picker_adapter`, `online_llm_picker`, `variance_min_ipw`, `xu_*`, `model_selector_causal` all collapse to disagreement-gated sampling with two models, so they test the deployment rule, not the sampling idea.
5. **Budget accounting is invisible in outputs.** `run_metrics` drops `refused_requests` (suite.py:118-129); add it before the confirmatory run so any cap-binding behaviour is auditable. The cap itself cannot be exceeded.
6. **`T % m == 0` is required by the UPF adapter** (raises otherwise); all nine registered datasets have T = 2000, so safe for m in {50,100,200}, but a new stream of other length would crash the family.
7. **`chalgse` family** was added to `sota_extra.py` after this audit began; no test file covers `ChallengerGSE`.
8. **Synthetic-dev winners are in-sample** on the D3 seeds (`comparator_panel_results.md`), so the tuned families have a mild selection advantage on synthetic data and none yet on real data until the real-dev winners are used (they are in section 2b).
9. **Certified does not mean valid here.** Every certified entry's guarantee is a construction-level argument for a predictable-propensity or conditional-mean null; none is a published theorem under delay plus a hard cap plus the persistent (Markov) regimes. QSG's observed 0.26 false promotion at rho = .8 shows the null assumption can fail; guarantee claims should be reported with cost, not instead of it.
10. **Composite-null warning for RCS.** The paper's joint-emptiness rule false-alarms on drifting-within-null streams; only the `any_excludes` variant is registered (deliberately), which is a different stopping rule from the paper.
11. **Smoke results above are one seed on one stream** and say nothing about comparative performance.
