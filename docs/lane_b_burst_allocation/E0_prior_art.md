# E0 prior-art audit: K candidates sharing one queried label

**Date:** 2026-10-29. **Gate:** Phase E, E0 (`LANE_CONTROL.md`). **Status:** literature and in-repo audit only. No code, no experiment, no novelty claim.

## 1. Verdict

**NARROW, LOW-CONFIDENCE PASS (about 25-30% chance E1 survives). The headline target is dead; one thin residual is left.**

- **Target retired.** Three of the five asked-for properties (a, b, e) are covered by published methods, and a fourth (d) is covered by composition (see section 3). The target "sample cost log K versus K" is not available against the right baseline. With one shared label stream, per-candidate Bonferroni or alpha-spending already costs only an additive log K inside the threshold, not a factor K in labels (section 4). Separately, full-information BAI and label-efficient experts already give log K.
- **Residual kept** (section 5):
  - **R1 (main):** a disagreement-metric covering number replaces log K in the false-promotion level.
  - **R2 (secondary):** pairwise-closure sampling under reversible re-baselining.
- **Kill test.** E1 must show R1 or R2 is not a corollary of chaining/union bounds plus standard convex allocation. If neither is, EXIT.
- **Prior from this lane's record.** Every earlier candidate died as a composition, so the default expectation is EXIT at E1.
- **No source forecloses everything.** I found no published rule that is simultaneously: shared-label, disagreement-gated, anytime-valid against an incumbent over K candidates, hard-budget, delayed, and reversible. That absence is not evidence the combination is non-trivial.

### Three closest sources

1. **Karimi et al., Model Picker (AISTATS 2021, arXiv 2010.09818).** Closest to (a) and (e).
   - K pre-trained models, a stream, and a randomized query probability from the "importance of the instance at hand".
   - If all models agree, the query probability is zero.
   - Regret O(sqrt(T log k)), matching full-information experts.
   - Expected queries O(sqrt(T log k) * |C| / gap).
   - Misidentification probability at most k * exp(-0.18 * ...).
   - Not anytime-valid against an incumbent, no hard budget, no delay, no switching cost.
2. **Dann, Ghavamzadeh, Marinov, multiple-policy HCPE (AISTATS 2023).** Closest to the overlap idea.
   - Sample complexity scales with an "expected disagreement" overlap among K policies instead of K.
   - Fixed-accuracy PAC, on-policy tabular MDP, no promotion, no anytime validity.
3. **Russo, Song, Pacchiano, Pure Exploration with Feedback Graphs (arXiv 2503.07824).** Closest to the structural frame.
   - Fixed-confidence best-action identification where a graph decides what is revealed.
   - Instance-dependent lower bound with graph quantities, the TaS-FG algorithm, and an allowance for unknown or stochastic graphs.
   - This is the template for "disagreement graph" characteristic times.

Runners-up: DISCERN (Balachandran, 2609.17560; single-candidate gating), and Lane A's online-FWER, sequential-MHT and Cheng / Ryabchenko audits.

### Composition baseline to beat (call it C-E)

1. **Per-candidate engine.** For each candidate k, a DISCERN-style disagreement-gated, Horvitz-Thompson-weighted betting e-process of paired excess cost against the current incumbent.
2. **Shared acquisition.** One label queried with predictable probability q_t(x) = max(pi_min, f(S_t(x))), where S_t(x) is the set of live candidates that disagree with the incumbent at x.
   - Variants f: Model Picker's maximum-hypothetical-variance rule, uniform on the union of disagreement sets, and a convex minimax-variance design (Neyman style) under the budget.
3. **Multiplicity.** Choose among:
   - alpha/(K) Bonferroni;
   - online alpha-spending alpha/[i(i+1)] (this repo's rank allocation) or Tian-Ramdas online fallback for a growing stream;
   - e-BH or online e-BH, only if the target is FDR rather than any-false-promotion.
4. **Switching.** Promote to the first or best certified candidate. Demote on a symmetric e-process. Use a lazy/dwell switching rule (Cheng-style, or the dynamic-indicator regret construction) for the cost term.
5. **Delay.** Event-prefix bookkeeping from `docs/delayed_event_prefix_validity.md`, and fixed-delay batching as in Ryabchenko et al.

Alternatives C-E must also beat: successive elimination or label-efficient Hedge on shared labels, plus a final alpha-spent gate.

## 2. In-repo state (reused, not redone)

- `src/shiftlab/dive/promotion_grid.py` `_candidate_alpha_allocations`: finite grid of validation-ranked candidates, alpha_i = alpha/[i(i+1)], equal, or validation-power softmax. Frozen before shadow monitoring, union bound valid conditional on validation.
- `budgeted_promotion.py` and `nested_candidate_context_alpha.py`: repeated-candidate promotion under a shared hard label budget, nested candidate x context alpha.
  - These are sequential-candidate or per-candidate monitors.
  - A grep of `budgeted_promotion.py` finds only a shared *query randomness* flag; I did not trace whether one label is reused across candidates.
  - No code exploits overlap of disagreement sets across K simultaneous candidates.
  - Disagreement appears only in the single-candidate gated monitor, `adg_growth_prescreen.py`.
- Matrix (`PRIOR_ART_AND_NOVELTY_MATRIX.md`, B1 Q2 table, reused with its recorded verification levels):
  - OCS/MOPE: single candidate, IID.
  - HCPI: sample split plus a safety test per iteration.
  - OPI (Molitor): log|Pi| scaling with alpha/(2m), stationary.
  - AnyRank: graphical FWER over pairwise tests, adaptive trial allocation to hard-to-separate pairs, IID, evaluator runs a policy on a fresh task.
  - Digalakis et al.: one challenger, one irreversible switch, finite-epoch Hoeffding plus union over epochs.
  - Zhang-Wu-Qian (2609.13714): finite library with Bonferroni or a fixed order, fixed n.
  - DISCERN: disagreement-only labels, anytime CS, chains of promotions.
- Lane A audits (read as headers only for the two multiplicity files):
  - `switching_sequential_multiple_testing_prior_audit_v1.md` (Malek et al., AISTATS 2017: adaptive allocation across tests plus a monotone procedure inherits FWER).
  - `switching_online_fwer_comparator_audit_v1.md` (Tian-Ramdas: alpha spending, online fallback, ADDIS).
  - `switching_cheng_audit_v1.md` (hard observation budget plus switching: minimax Theta(T sqrt(K/B)); batched full-information O(T sqrt(K log K / B))).
  - `switching_delay_capacity_audit_v1.md` (Ryabchenko et al.).
  - `switching_dynamic_indicator_regret_audit_v1.md` (2609.30556).
  - `switching_active_sequential_two_sample_audit_v1.md` (Li et al.: finite label cap plus active selection plus anytime Type-I).

## 3. Property-by-property coverage

| Property | Covered by | Status |
|---|---|---|
| (a) Acquisition that uses the structure of disagreement sets | Model Picker (zero query probability when models agree; variance of hypothetical losses as informativeness). CODA (ICCV 2025, disagreement-driven pool-based). Query-by-committee and disagreement-based active learning. Dann et al. (overlap measure). DISCERN (gating for one candidate). Multi-candidate allocation of a shared budget is a convex minimax-variance design (Neyman, optimal design). | **Covered as a heuristic and as standard design.** No known finite-sample anytime-valid *certification* analysis of it. |
| (b) Multiplicity-controlled anytime-valid promotion over K or a stream | Online alpha spending and fallback (Tian-Ramdas), e-BH (Wang-Ramdas), online e-BH and e-LOND (Xu-Ramdas, Fischer et al.), Malek et al., OPI, AnyRank, Zhang-Wu-Qian. | **Covered.** |
| (c) Delay plus hard budget | Lane A: Cheng (budget), Ryabchenko (fixed delay, full information), delayed event-prefix validity (repo). Grover et al. (BAI with delayed feedback; bandit, abstract only). | **Covered by composition** (Lane A's open G1 is the joint safe-frontier, not this). |
| (d) Reversible switching among candidates | Dynamic-indicator regret (2609.30556), Cheng, switching-costed experts. No false-promotion constraint in these. | **Covered for regret**; the false-promotion-constrained version is Lane A's open G1, shared by every Lane B candidate. |
| (e) Scaling better than per-candidate testing | Full-information BAI and experts give log K (see section 4). Model Picker matches sqrt(T log k) with fewer labels. | **Covered**, and the stated comparison class is wrong (section 4). |

## 4. Why "log K versus K" is the wrong target

1. **Shared labels already remove the factor K.** The baseline C-E shares each label across all K e-processes. Its cost over a single candidate is only that every threshold goes from 1/alpha to K/alpha (Bonferroni), under arbitrary dependence and with no new assumption.
2. **That is the full multiplicity price, and it is small.** A betting e-process crosses its threshold after roughly ln(threshold) / (growth rate) events. The wait therefore inflates by ln(K/alpha)/ln(1/alpha):

   | K | wait inflation, alpha = 0.05 |
   |---|---|
   | 2 | about 1.23x |
   | 8 | about 1.70x |
   | 32 | about 2.16x |
   | 1024 | about 3.3x |

   (My arithmetic. It assumes growth rate is the only driver and the same candidate wins.) Even a perfect multiplicity-free method can gain at most this factor, which is logarithmic in K.
3. **Disagreement structure can produce the K factor, but only on the cost side.** If the disagreement sets are disjoint, each label informs one candidate, and the label need adds up across candidates (K-linear). This is information-theoretic and applies to every method. If the sets coincide, one label informs everyone and you recover log K. So the interesting quantity is a covering or fractional-packing value of the overlap structure. That is exactly what Dann et al. (overlap) and Russo et al. (graph-dependent characteristic time) already formalise in other settings. A convex allocation that attains it is standard design.
4. **Full-information BAI.** With all K means revealed per sample, the sample complexity is governed by the single gap and log K. This is textbook (successive elimination, Hedge/experts). I did not fetch Kaufmann et al., Jamieson's lil'UCB, or Jourdan et al. (anytime); see section 6. Those results are bandit-feedback and use all-arms sampling only where noted. A feedback-graph version exists (Russo et al.).
5. **Label-efficient prediction (Cesa-Bianchi, Lugosi, Stoltz, COLT 2004 / IEEE TIT 2005).** Experts with a label query probability epsilon. Regret bound of order sqrt(T log K / epsilon) (this form is quoted secondhand from Model Picker's discussion; I did not read the original). One label reveals all experts' losses. It is blind to disagreement. Model Picker is its direct improvement, which adapts epsilon to disagreement and achieves sqrt(T log k) regret with a sublinear number of expected queries. So (e) in the regret sense is already covered. The cost-of-labels trade-off (queries ~ sqrt(T log k) at no extra regret) is already published.

## 5. The residual

Fix the contract of `switching_problem_v1.md` (shared common label, loss determined by prediction, i.e. DISCERN Assumption 1, so agreements are free and uninformative; delay d; pathwise query cap B; causal null E[Z_k | H_t] <= 0). The question is whether either of the following is a theorem that is not a corollary of existing machinery.

### R1: multiplicity by covering number in the disagreement pseudometric

- **Setup.** Define rho(c, c') = P_x(c(x) != c'(x)).
- **Claim to test.** The e-processes for two close candidates are nearly identical sequences of HT increments (they differ only on a rho-small set). The any-false-promotion level should then pay ln N(eps; rho) (a covering number) plus a small residual term, in place of ln K or ln(1/alpha_i).
- **Why it is not trivial.** Bonferroni (alpha/K) and e-BH under arbitrary dependence ignore correlation. Union over an eps-net plus a discretisation term is the textbook chaining move, but a *time-uniform*, betting-based version, with HT weights depending on a *data-dependent q_t*, is not something I found.
- **Gain is capped.** At most a log K factor per section 4. It is useful only when K is large (hundreds of correlated candidates, such as lookback grids or ridge penalty grids).
- **Prior status.** Chaining and uniform bounds over policy classes (VC-type) appear in HCPI-style and OPE-class work. I did not search for time-uniform chaining. **Unsearched; must be searched before E1 (for example, "time-uniform chaining confidence sequence", "sequential uniform convergence e-process class").**

### R2: pairwise-closure sampling under reversible switching

- **Setup.** Disagreement is defined relative to the current incumbent. A promotion changes the reference, so labels gated on old-incumbent disagreement can miss events informative for the new pairs (j, k).
- **Why it can matter.** An event with c_j(x) != c_k(x) is a disagreement for at least one of them against the old incumbent h, but may have been under-sampled when only a dead or low-priority candidate disagreed. Reversible switching therefore needs a sampling floor on the *union of pairwise* disagreement, which is a cost not paid by a single-switch method.
- **Prior status.** Related to AnyRank's graphical pairwise allocation (PARTIAL) and to the DISCERN promotion chain; neither combines this with delay plus a hard cap. A plausible E1 object is a trade-off between the floor pi_min and the budget. It risks being a design heuristic with no separation. Compare against a uniform floor on the union of pairwise disagreements.

### Candidate E1 theorem shapes (any one suffices)

- An *upper bound with matching lower bound* on the labels needed for any-false-promotion-controlled promotion, expressed through a fractional cover of the disagreement hypergraph, such that no K-independent bound exists for the C-E acquisition rules (a separation against the Model Picker / uniform-on-union rules).
- A time-uniform false-promotion level scaling with ln N(eps; rho) (R1) together with a counterexample showing alpha/K spends strictly more at matched safety.
- A counterexample showing that pairwise-closure sampling is necessary for reversibility (R2) and that C-E lacks it.

### Exit triggers for E1

- The covering-number level is dominated by a union over an eps-net plus a standard discretisation argument, giving no gain beyond a constant on realistic K (<= 32 in E2).
- The optimal acquisition is the convex minimax-variance design, with the same guarantee as C-E.
- The whole advantage disappears when C-E uses a pi_min floor on the union of pairwise disagreements.

## 6. Sources and verification level

Levels: **FULL** (theorem statements read in primary text), **PARTIAL** (abstract plus setting or selected theorems), **ABSTRACT** (abstract or listing only), **SNIPPET** (search-result summary only), **REPO** (taken from a repo audit and not re-read), **UNVERIFIED** (named from memory or by search without fetching).

| Source | Used for | Level |
|---|---|---|
| Karimi et al., Model Picker, arXiv 2010.09818 (AISTATS 2021) | Disagreement-gated queries, sqrt(T log k) regret, query and identification bounds (Theorems 1, 2, 4, 5, 6 statements) | PARTIAL: I extracted the PDF text and read the statements, discussion and related-work text. I did not read the proofs, so the exact constants and the stochastic-stream assumptions (e.g. unique best model, gap) should be checked. |
| Russo, Song, Pacchiano, arXiv 2503.07824 | Feedback-graph pure exploration; instance-dependent lower bound; TaS-FG | ABSTRACT (summary of the arXiv listing). I did not read the theorems or confirm the full-information case. |
| Dann, Ghavamzadeh, Marinov (AISTATS 2023) | Overlap (expected disagreement) in K-policy evaluation | REPO (matrix: PARTIAL) |
| Cesa-Bianchi, Lugosi, Stoltz, label-efficient prediction (COLT 2004; IEEE TIT 2005) | Label-efficient experts | SNIPPET (bibliographic and abstract-level) plus Model Picker's description of the bound. Not read. |
| Grover et al., BAI with delayed feedback, arXiv 1803.10937 (AISTATS 2018) | Delayed pure exploration | ABSTRACT. Bandit feedback; no formal bound seen. |
| Jourdan, Reda et al., anytime good-arm identification (APGAI), arXiv 2310.10359 | Anytime fixed-confidence threshold identification | SNIPPET. Note this is good-arm identification, not BAI. Closest to "certify against a threshold" but bandit-feedback. |
| Kaufmann et al. (2016 BAI), Jamieson et al. (lil'UCB, 2014) | Fixed-confidence and anytime BAI | UNVERIFIED (not fetched) |
| Kocak and Garivier (spectral/feedback-graph BAI); Chen et al. 2021 | Graph-side-information BAI | UNVERIFIED. A search returned Thaker et al. (GRUB, arXiv 2108.01152; abstract-level, homophily-based) and no Chen or Kocak paper. Do not cite them as found. |
| Wang and Ramdas, FDR control with e-values, arXiv 2009.02824 | e-BH: FDR control under arbitrary dependence | ABSTRACT (guarantee statement confirmed on the listing) |
| Xu and Ramdas, online multiple testing with e-values (AISTATS 2024); Fischer, Xu, Ramdas, online e-BH (arXiv 2407.20683) | e-LOND and online e-BH | SNIPPET |
| Tian and Ramdas (online FWER, SMMR 2021); Malek et al. (AISTATS 2017) | FWER spending and adaptive allocation | REPO (Lane A audits) |
| Jin and Candes, conformal selection (JMLR 2023) | Unit-level FDR via conformal p-values | ABSTRACT. Not a promotion rule; unit-level selection, fixed sample, exchangeable. Not relevant to this residual. |
| Kay et al., CODA (ICCV 2025) | Disagreement-driven pool-based active model selection | SNIPPET |
| Balachandran, DISCERN (2609.17560); Karampatziakis et al. (OCS); Thomas et al. (HCPI); Molitor (OPI); Badithela et al. (AnyRank); Zhang-Wu-Qian (2609.13714); Digalakis et al. (2512.18390) | Gating, certificates, finite candidate banks, switching cost | REPO (matrix and `challenger_switching_fidelity_audit.md`, as recorded there) |
| Cheng, Zhou, Ji (ICML 2023); Ryabchenko et al. (2503.19856); 2609.30556; Li et al. (TMLR 2024) | Hard budget, fixed delay, dynamic indicator regret, active sequential testing | REPO (Lane A audits) |

### Searches not done (carry into E1 if the lane continues)

- Time-uniform chaining or uniform-over-class betting confidence sequences (for R1).
- Seldonian and multi-candidate HCPI variants beyond a single split (Thomas et al. 2019; unverified in the repo).
- Thompson-based or combinatorial promotion with a safety constraint.
- Off-policy selection with shared logged outcomes.
- Full reads of Russo et al. (is the complete-graph case a corollary?) and of Model Picker's proofs.
- The "Pure exploration with feedback graphs" statement for a *context-dependent* graph is unchecked. My claim that it covers the disagreement structure rests on the abstract (graphs may be unknown and stochastic).

## 7. Assessment (continue / pivot / stop)

- **Continue to E1, narrowly,** with a single-tick budget on R1 and R2 and with the target statement rewritten as "false-promotion level and label need governed by overlap structure, not by K".
- **Do not** claim a K-versus-log-K separation, a new acquisition heuristic (Model Picker, CODA and convex design cover it), or novelty from "multiplicity-controlled switching" (Lane A's baselines cover it).
- **E1 must open with the baseline C-E and a written reduction attempt** that tries to derive the proposed rule from C-E. Failure to find such a reduction is the entry condition for E2, not a result.
- **If E1 does not produce a lower bound or a matched upper bound that C-E provably cannot attain within 2 ticks, EXIT** and record Phase E as closed on the same grounds as C and D (decomposes into design, union/chaining and switching pieces).
