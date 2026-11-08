# A2_DRAFT: Stage-B amendment A2 (final screening round before the checkpoint decision)

Status: DRAFT ONLY. Nothing here is registered, implemented or run. No frozen file was edited. Worktree HEAD
`e3259829`; ledger read-only (149 records). All numbers below are read from `registry/EXPERIMENT_LEDGER.jsonl`
(`results.components_per_cell`, `power_delay_per_cell`, `baseline_relative`, `counterexamples`) and from
`src/shiftlab/autoresearch/stage_b.py`; none is a new measurement.

Context: 143 Stage-B experiments, 0 KEEP; Mandate Q2 stop rule reads NEGATIVE. Remaining registered budget 57. This
round is mechanism-driven: every candidate is tied to a diagnosed cause or a documented RAR failure.

## 0. Findings the coordinator must see before registering anything

**F-SEED (blocking).** The proposed sub-block `110060000 + cell_index*1000 + replicate` is NOT disjoint from v2.
v2 uses `110050000 + cell_index*1000 + replicate` for cell_index 0-14, i.e. 110050000-110064019 (ledger
`seed_group.sub_block = v2`, `seed_end = 110064019`). The proposal would reuse the seeds of v2 cells idx 10-14
(S3b, S3c, S4a, S4b, S4c) for A2 cell idx 0-4. Proposed replacement: **`110070000 + cell_index*1000 + replicate`**
(section 5). `configs/seed_registry.yaml` registers only the whole block `d2a_rar_dev` 110000000-110099999 and
confirmation 120000000-120099999; v1 occupies 110000000-110003019, v2 110050000-110064019. No integer seed
>= 110065000 appears in `results/`, `configs/` or `docs/` (a grep hit on `110073089` is a runtime float).

**F-CTRL (affects every Q1 shell record).** Of the 27 scope-iii records with a v2 result, **27/27** fail the
control-cell check on S2e, S2f (extra_spend) and S3c (extra_promotion), and 25/27 on S4c (worse_J). These checks do
not discriminate between candidates (section 1.2): they are protocol artifacts, so the registered A1 KEEP rule cannot
return KEEP for any shell candidate. Options for the coordinator: (a) register the A2 control reading in section 1.3;
(b) refuse it, in which case the Q1 arm is not run (saves 5 experiments) and the Q1 line is recorded closed under A1.

**F-CANARY.** The v1/v2 suites never exercised RAR's canary except on S2a (one cell). In every other cell the RAR
host issues zero retrains (N_r = 0; label cap 50-300 << T makes Gate 2 unreachable), so canary identities were
inert (`+2.50 [2.50, 2.50]` vs never_switch). On S2a with `deploy_on_complete=False` the host costs J=580.8 versus
529.0 with immediate deployment: **+51.8 (9.8%) canary overhead**, of which 10.0 is the contract's commit-switch
charge c_s that native RAR does not pay (adapters_rar.py deviation (ii)). See section 2.

**F-CAB.** The contract-scale Cost-Aware Binary comparator is degenerate on `intervention_dear`: H_hat is floored at
W_train = 100 and the gate is `drop * H_hat >= c_r (+ c_s) = 100-110`, which needs drop >= 1.0. Ledger: CAB host on S2a
has N_r = 0, J = 689.9 (labels only, worse than never_switch 640.0). A comparator that cannot fire is a strawman
(idea-evaluator F3). Section 2.4 adds a pre-registered strengthened variant.

## 1. Arm (a): Q1 repair

### 1.1 Near-KEEP records and diagnosed failure components

Near-KEEP records (valid under claimed null `cond`, effect label other than none on a target cell, DISCARD only via
control/regression checks). Candidates: CAND-0c6c168c019f555d `min_of_both_certificate` (substantial, Q1_2 vs
thinned_hedged_gate dJ -69.85 [-127.77, -11.60], FP 7/160, CP95 upper 0.081); CAND-554673b35895b8a4
`geometric_hazard_prior` (meaningful, Q1_2 -50.15 [-97.65, -2.75], FP 3/160); CAND-535bb9e297b2660b
`e_cusum_markov_base` (meaningful, Q1_2 -48.35 [-93.95, -1.74], FP 2/160). CAND-7862c5cf/0de97ac9/af5957d8/b8629b81/
0369028b are behavioural duplicates of the hazard record and are not re-run.

Per-cell components (J; N_q label spend in labels; promotion rate; mean delay after onset), min_of_both vs
comparators, from `components_per_cell` and `power_delay_per_cell`:

| cell | cand | rmm_detector | thinned_gate | markov_lr | note |
|---|---|---|---|---|---|
| S2d (alt, cap 300) | 473.8; 300; 1.0; 240 | 362.9; 300; 1.0; 101 | 483.2; 240 | 457.8; 227 | dJ vs rmm +111.0 [89.1, 130.4] |
| S2e (null) | 374.55; 300 | 374.55; 300 | 374.55; 300 | 374.55; 300 | identical; host spends 250 |
| S3c ("control") | 386.5; 60; 1.0; 270 | 527.7; 446 | 450.4; 349 | 845.0; 797 (p=.5) | cand best of all |
| S4c ("control") | 459.7; prom .45; 504 | 440.3; .10; 296 | 447.0; .15; 498 | 449.5; 0 | dJ vs rmm +19.4 [-18.9, 62.7] |
| S3a (alt, reversal) | 670.0; .90 | 689.6; .65 | 564.0; .65 | 574.6; 0 | vs markov_lr +95.4 [63.9, 127.8] |
| Q1_3 (null) | FP 3/20 | 0/20 | 1/20 | 0/20 | |

### 1.2 Failure diagnosis (mechanism, with evidence from the ledger)

| id | check that failed | diagnosis | class | repairable by an evidence rule? |
|---|---|---|---|---|
| D1 | extra_spend on S2e, S2f (27/27 records) | `stage_b.py:520` compares candidate N_q to the unmodified **Drift2Act host** (250 labels). The promoter shell uses a calendar schedule that spends the whole cap (300) for every shell method; markov_lr, thinned and rmm all spend 300 (N_q cost 75.0 each). Spend is fixed by the schedule, not by the evidence. | protocol artifact | No |
| D2 | extra_promotion on S3c (27/27) | S3c = `reversal_persistent_1200`: p 0.25 -> 0.9 from onset, persistent; `null_truth_expected` cond/marg/abs = false. For a promoter it is a true alternative. The check compares to the host promotion rate (0, since the host retrains rather than promotes). Promoting here is power (cand J 386.5 vs 450.4 / 527.7 / 845.0). | role mis-labelled for promoters | No (and should not be) |
| D3 | worse_J on S4c (25/27) | Rule is a point-estimate rule (`dJ_mean > 0.01 * J_comp`, no CI). All four near-KEEPs have CIs containing 0 on S4c (e.g. +19.4 [-18.9, 62.7]). Underlying cause is real but structural: S4a/S4c/S3a are transient-regime cells; promotion-only shells have no exit after the advantage expires (late promotions: delay 504-535 vs rmm 296). S3a harm vs markov_lr is significant (+95.4 [63.9, 127.8]) but is the reversal problem of FL-025/FL-042/FL-043. | rule artifact + known-unsolved structural cost | No (FL-043 "BENCHMARK_OR_CASE_STUDY_ONLY") |
| D4 | worse on S2d vs rmm_detector (min_of_both only) | Delay 240 vs 101 (rmm); loss 396.8 vs 285.4. Full-sample evidence methods cluster at 227-240 (markov_lr, thinned, min_of_both); onset-mixing methods reach 87-101 (rmm 101, geometric_hazard_prior 87, e_cusum 88). Pre-onset negative drift of log e must be climbed out of; a restart/onset mixture discards it. The two near-KEEPs that have onset mixing already close the gap (S2d vs rmm -8.2 [-19.5, 4.8] and -7.4 [-18.9, 5.8]). | real, mechanism located | Yes: restart/onset mixing |
| D5 | extra_promotion on Q1_3 (min_of_both only, 3/20) | Binomial(20, 0.1): P(X>=3) = 0.32. Indistinguishable from alpha = 0.1; markov_lr is simply more conservative (0/20). | sampling noise | n/a (needs replicates, not a rule) |

Not diagnosed, stated explicitly: the ledger stores per-cell means and rates, not per-seed promotion times, so
"late promotion after regime exit" in D3 is inferred from delay means (504-535 vs regime mean duration 150), not
traced seed by seed.

Prior-ledger constraints that bind this arm: FL-001/FL-005 (late/transient advantage is mostly the cost of a valid
gate; restart is the known start-multiplicity trade-off), FL-025/FL-043 (post-switch evidence reset and
promote-then-rollback are blocked without a new hypothesis). Variants that revisit those are excluded (section 1.5).

### 1.3 Proposed A2 Q1 control reading (to be registered BEFORE any A2 record; applies to all Q1 shell records)

The change is motivated by the component table above (shell comparators spend identically; S3c is an alternative
for promoters; S4c is read on a point estimate), not by any candidate outcome, and it is applied to the whole Q1 line.
Risk acknowledged: it is made after seeing which checks killed the near-KEEPs. Safeguards: fresh seeds; the strict A1
reading is computed and reported beside it; A2 target cells stay the A1 target cells (Q1_2, S1a, S2d, S3a, S4a);
S3c is descriptive only and is never a target; a KEEP only promotes to Stage C.

- C1 spend: extra_spend iff candidate N_q > 1.10 x (strongest eligible **shell** comparator N_q) + 0.5 on that cell.
- C2 promotion: extra_promotion is scored only on cells where the claimed null holds in evaluator truth (Q1_0, Q1_3,
  S1b, S1c, S2e, S2f, S3b, S4b = the validity cells already listed in each ledger record). On other control cells
  promotion is judged through J (C3).
- C3 J regression: a control or regression cell fails iff the paired 95% CI of dJ vs the per-cell strongest
  comparator lies entirely above 0 AND the mean exceeds 1% of J_comp.
- C4 validity unchanged: pooled false promotion over the 8 null cells, report Clopper-Pearson upper bound, "screen-level".
- C5 fresh-seed rule: the effect on the A1 best cell (Q1_2) must replicate (paired CI upper < 0 vs thinned gate).
- Both readings (A1-strict, A2) are written into every record; A1 decisions are never re-labelled.

### 1.4 Q1 experiments

Panel: the 16 scope-iii cells (v1 Q1 row + 12 v2 cells), same definitions, **fresh seeds** (section 5), 20
replicates, shell = `adapters_evidence.promoter_adapter`, calendar schedule, alpha 0.1. Comparators: valid Markov-LR
(`markov_lr_gate`), gap-10 thinned gate (`thinned_hedged_gate`), `rmm_detector` (restart mixture without gaps), and
the unmodified host; Gap-Mix `exact0.8_s4` is excluded for a `cond` claim (declared `marg`), and because it needs up
to ~11 CPU-min per seed on cap=T cells it is run only as a reported reference on Q1_2, S1a, S2d, S3a, S3c, S4a
(deviation, needs coordinator approval).

**A2-Q1-REP1/2/3: replications under A2 reading** (3 experiments): CAND-0c6c168c019f555d, CAND-554673b35895b8a4,
CAND-535bb9e297b2660b, unchanged code. Hypothesis: the A1 near-KEEP effect on Q1_2 is real, not selection noise.
Falsification: record DISCARD with NEGATIVE note if the Q1_2 CI vs thinned gate contains 0 on fresh seeds, or any of
C1-C4 fails. If 0/3 replicate, close the Q1 shell line and report that the A1 near-KEEPs were winner's-curse
selections. Needs a ledger key that distinguishes A1 from A2 records (`suite` or `amendment` field) so Stage A does not
mark them DUPLICATE.

**A2-Q1-R1: `restart_min_certificate`** (1 experiment) and **A2-Q1-R1V** (validity audit, 1 experiment).
- Hypothesis: min_of_both's single significant loss (S2d vs rmm, +111) is pre-onset dilution (D4). Putting a restart/
  onset mixture inside each of the two components, with ONE shared summable start-time prior, removes the dilution
  while keeping validity under either null.
- Mechanism: `log e = min( log sum_s w_s E_cond^(s), log sum_s w_s E_marg^(s) )`, w_s = 1/(j(j+1)) on a geometric
  grid of label-index starts (s = 1, 2, 4, ...), sum w <= 1. Min is taken OUTSIDE the mixtures (more powerful than
  min inside). Validity argument (not a proof, to be unit-tested): each mixture is a nonnegative supermartingale under
  its own null when its per-start processes are, and the min is dominated by each, so it inherits H0cond OR H0marg
  validity exactly as MinCore does; summable weights are what make the time-uniform bound hold (an unweighted
  Shiryaev-Roberts e-detector only gives an ARL bound). A2 test asserts sum w <= 1 and fails the identity as INVALID
  otherwise.
- Closest prior art: Shin-Ramdas-Rinaldo e-detectors (`shin2023_edetectors`, V), Sethi 2026 (V), Gafni et al. 2026 (V).
  Status HIGH_OVERLAP (family F3). Not claimed novel; positioned as a combination with an either-null intersection.
- Target null: `cond` (also valid under `marg` within the declared class; scored on `cond` validity cells only).
- Assumptions: seam gives in-order identified outcomes only (out-of-order dropped and counted); calendar schedule is
  F-predictable; weights fixed before the run.
- Predicted win region: dependent-chain alternatives with sparse gap labels (Q1_2) and persistent shifts (S2d, S1a);
  expected S2d dJ vs rmm within about +-3% J of the e_cusum record. Predicted failure region: S3a/S4a/S4c (no exit
  after advantage expires), FL-043.
- Complexity: 2 (about 50 LOC, one new Core class; compute bounded by the geometric grid; the 4 restart identities
  that crashed at 300 CPU-s used dense windows).
- Falsification: DISCARD with NEGATIVE note if (i) S2d dJ vs rmm_detector CI lower bound > 0 (still worse),
  or (ii) it is not better than REP3 (`e_cusum_markov_base`) on any target cell with CI excluding 0 (the min adds
  nothing), or (iii) the ablation "restart removed" (= REP1) does not reproduce the S2d gap, or (iv) pooled FP on the
  8 null cells exceeds 0.10 or CP95 upper exceeds 0.15. R1V: 100 replicates on Q1_0, Q1_3, S3b, S4b (seed idx 21-24,
  replicate 0-99): FP must be <= 0.10 with CP95 upper <= 0.15 on the pooled 400 paths.

### 1.5 Considered and excluded (so nothing is re-proposed silently)

- Reversal-aware veto or post-promotion rollback in the shell (D3): blocked by FL-025, FL-043 (needs the exact
  low-alpha E-SR vs E_rb protocol; E_rb already exists). Not a Q1 repair.
- Futility stop on queries (would cut the 75-unit null-cell label spend): an acquisition rule, i.e. Q2 territory,
  and Mandate Q2 is NEGATIVE.
- Reorder buffer for out-of-order labels: per-seed drop counts are not in the ledger; cannot be diagnosed from it.
- Alpha tightening (0.05): hyperparameter sprawl; D5 is noise, not mechanism.

## 2. Arm (b): RAR canary-exposure

### 2.1 Why the old canary records are uninformative, and what the family must do

Ledger (CAND-aad82c8e, CAND-cb208e8b, CAND-27378bf0, S2a-S4c): RAR calibrated_v1 retrains only on S2a. Elsewhere
N_r = 0, N_b = 0 and J equals never_switch + alert cost. The new family must make Gate 2 reachable (label cap = T, all
labels requested, delay tau) and must contain a case where retraining is harmful, otherwise a canary has nothing to
catch. Facts about the contract that constrain the design (BENCHMARK_CONTRACT 4a/4b, `simulator.py`):
retrained loss rate `q(e) = q_best + (q_poor - q_best)(1 - min(1, e/e_sat))` (StreamSpec fields `retrain_rate`,
`retrain_poor_rate`, `retrain_sat_fraction`), candidate model loss = 1 - incumbent loss; `route(target, p)` is free and
cancelled by any model change; in `shadow` mode a queried round reveals RETRAINED losses on rounds >= retrain_ready_t
for free; retrospective queries need `ClockSpec.max_lookback > 0`. No simulator code change is needed: the family is
YAML only.

### 2.2 New frozen stream family `rar_persistent` (alternative / correct null / neighbouring control + 2)

File `configs/d2a_rar/stream_families_v3.yaml` (coordinator-owned, new, sha256 recorded in A2). All cells:
`dependence: iid`, `T: 1500`, `label_cap = T = 1500`, cost vector `intervention_dear`, `retrain_duration 20`,
`ClockSpec(deploy_on_complete=False, max_lookback=10, w_train=100)`, `obs_mode shadow`, 20 replicates.
Label-frontier semantics come from the contract release clock (labels visible at t + tau, none earlier; policy
requests every round while budget remains = RAR's "labels eventually arrive"), so RAR's earliest retrain time
`t_d + tau + ceil(theta_L W_train) - 1` applies.

| cell | role | stream | retrain model | purpose |
|---|---|---|---|---|
| S5a | alternative | onset 0.25, persistent; p 0.25 -> 0.50; delay fixed 10 | best 0.25, poor 0.60, sat 0.7 | drift where retraining pays (gain 0.25/round); candidate model 1 is NOT better (0.50 = 0.50), so a free switch cannot substitute |
| S5b | correct null | no drift, p 0.25; delay 10 | as S5a | retrain has zero benefit; gates/canary must not spend |
| S5c | neighbouring control | onset 0.25, persistent; p 0.25 -> 0.33; delay 10 | best 0.45, poor 0.70 | drift where retraining is HARMFUL (retrained 0.45-0.70 vs incumbent 0.33); the canary's job; drop 0.08 is below Delta_crit = 2 theta_R = 0.10 |
| S5d | alternative (label-frontier stress) | as S5a with fixed delay 40 | as S5a | canary duration tau + W1/p1 and gate latency scale with tau |
| S5e | adverse stress, descriptive | p 0.25 -> 0.50 persistent; delay 10 | best 0.60, poor 0.80 | big visible drop but retraining does not help: the failure probe for skip-the-canary rules |

All constants are proposals. Obligation G0 (no candidate may run before it passes; one host-only calibration pass
allowed, recorded, as for host_audit v2): with the reference methods only, RAR calibrated_v1 must retrain and enter
Canary-1 in >= 80% of seeds on S5a/S5d/S5c and in <= 10% on S5b; S5c must show a rollback or abort rate >= 50% for RAR
and a J penalty for NoCanary vs RAR; otherwise the family is declared not RAR-exercising and the whole arm is
UNVERIFIED (no candidate records). The functional form of q(e) is an assumption (contract 4a), so the continuation
experiments in section 4 include a (q_poor, e_sat) sensitivity.

### 2.3 Comparators and controls

RAR `calibrated_v1` (canary clocks); **NoCanary** (mandatory: RAR with the canary stage disabled, immediate
deployment, gates/holds/alerts intact; RAR's own ablation raised utility on 11/13 streams); Rollback-Only (RAR with
pass-through Gate 2/3 and alerts disallowed, canary on); Binary; Cost-Aware Binary as defined by the paper (reported;
expected degenerate, F-CAB) and **CAB-horizon** (H_hat = T - t, pre-registered strengthened variant labelled
PAPER_RECONSTRUCTION_VARIANT so candidates are not credited for beating a comparator that cannot fire); the A1 v2
comparator set: never_switch, uniform_query, fixed_schedule, pending_cap, episode_front, Gap-Mix `exact0.8_s4`
(reported only; invalid for a `cond` claim), gap-10 thinned gate. Strongest comparator = lowest mean J per cell among
comparators; since the RAR candidates claim no statistical null (`none`/economic), all comparators are eligible.
Reference runs (9-11 methods x 5 cells x 20 seeds) are computed once and cached and do NOT count as experiments
(same accounting as A1, where cached references are not records); G0 outcome is written to a status note.

### 2.4 Candidates (at most 3) and the controls they must beat

KEEP-A2 for a canary candidate (no validity claim; economic): J beats BOTH RAR calibrated_v1 AND NoCanary on at
least one of S5a/S5c/S5d with paired CI excluding 0 (graded effect), is not significantly worse (C3 rule) than either
on S5b, S5c, and the exposure/overhead secondary metrics (peak exposed traffic share, rollback latency, canary
overhead = J - J_NoCanary) are reported. Equalling NoCanary is a restatement of RAR's ablation, not a win.
Structural handicap to disclose: every canary-capable policy pays c_s = 10 for the commit switch (deviation (ii)),
NoCanary does not; records report J and J minus that charge (descriptive).

**A2-RAR-K1 `fast_verification_full_traffic`** (config only).
- Hypothesis: in J-units (no risk term), at a fixed number W1 of routed labelled observations the harm of a bad
  retrain is W1 x h independent of p1, while latency is tau + W1/p1; so p1 < 1 only buys delay.
- Mechanism: p1 = 1.0, W1 = 20, W2 = 40 (other constants as calibrated_v1).
- Prior art: RAR (fixed p1=0.2, `rar2026`, V); Lindon et al. sequential canary (V). Status PLAUSIBLY_DISTINCT in the
  registry (F7) but I assess it as KNOWN-BY-DERIVATION: it is a reading of RAR's own ablation, not a method.
  Role `baseline_or_ablation_only`; no novelty claim.
- Target null: economic/none. Assumptions: J has no exposure-risk term; shadow labels on non-routed rounds NOT used
  as canary evidence (fidelity guard, tested).
- Predicted win: S5a, S5d (about 80 rounds x ~0.25 foregone gain, ~20 J, i.e. 3-5%). Predicted failure: the
  secondary exposure metric (1.0 vs 0.2 peak traffic share); S5e is neutral. Complexity 1.
- Falsification: no J gain vs calibrated_v1 on S5a/S5d with CI excluding 0, or significantly worse on S5c.

**A2-RAR-K2 `critical_degradation_skip_stage1`** (skip-canary-when-expected-value-negative).
- Hypothesis: when the incumbent's observed degradation already exceeds RAR's own critical threshold, waiting
  tau + W1/p1 rounds in Canary-1 costs more than the harm it can avert; stage 1 should be skipped and verification
  kept as full-traffic probation with rollback.
- Mechanism: at retrain-ready, if `A_pre - A_cur >= Delta_crit = 2 theta_R` (RAR's existing emergency-override
  constant, no new tuning) then `switch(RETRAINED)` and run stage 2 (W2, paired z, rollback on failure); otherwise
  run the normal Canary-1. Decision uses only released labels.
- Closest prior art: RAR emergency override from Hold-Soft (V); CMAS conservative promotion gate (V); Karampatziakis
  gated deployment (V); cost-aware retrain gating (`cara2023`, `zliobaite2015`). Status PLAUSIBLY_DISTINCT, search
  thin (ramp-up literature unsearched; may become HIGH_OVERLAP).
- Target null: economic/none. Assumptions: degradation magnitude predicts retrain benefit (false on S5e by design).
- Predicted win: S5a, S5d (saves stage-1 latency; ~3-5% over calibrated_v1) while S5c keeps the full canary (drop
  0.08 < 0.10) and matches calibrated_v1. Predicted failure: S5e (skips the canary on a retrain that does not help;
  pays c_b = 25 plus ~40 rounds of full exposure, +20-40 J vs calibrated_v1).
- Complexity 2 (about 40 LOC subclass override of `_retraining`).
- Falsification: loses to NoCanary on S5a/S5d (the skip is then not distinguishable from RAR's ablation), or S5c
  significantly worse than calibrated_v1 (the threshold leaks into the harmful regime), or no gain on any cell.

**A2-RAR-K3 `ambiguity_extended_verification`** (adaptive W2).
- Hypothesis: a fixed W2 is too long when stage 1 is decisive and too short when it is ambiguous.
- Mechanism: after Canary-1 passes, W2 = W2/2 if `|a_new - a_old| >= 3 delta`, W2 = 2 W2 if `|a_new - a_old| < delta`,
  else W2 (three pre-registered levels; no tuning).
- Prior art: Lindon-Sanden-Shirikian sequential canary tests (V) and any sequential testing stopping rule. Status
  HIGH_OVERLAP in substance (registry marks `sequential_canary_stop` as not a config field); included only as the
  "known mechanism" arm; drop it first if budget is cut.
- Target null: economic/none. Predicted win: S5c (earlier rollback when ambiguous-bad) a few percent; elsewhere
  <1% ("none"). Complexity 2. Falsification: no effect label other than "none" on any cell.

**A2-RAR-L `routed_only_stage_labels`** (ablation, 1 experiment; uses retrospective queries).
- During Canary-1, request labels with `query(round=t-1)` only for rounds that `served_hist` shows were routed
  (`max_lookback >= 1`), applied to calibrated_v1. Bound on benefit: (1 - p1) x 110 rounds x c_q 0.05 ~ 4.4 J per
  canary (<1% of J), so the prediction is "none"; the experiment exists to show retrospective-query support works in
  the family and to bound the claim, and a test must show that setting `max_lookback = 10` leaves every host result
  bit-identical when no retrospective query is issued.

## 3. Per-candidate registry fields and idea-evaluator fatal-flaws verdicts

Common fields (all candidates): host = RAR/`rar.config` or `d2a.evidence_log_lik` via the evidence promoter shell
(Q1); fidelity tier PAPER_RECONSTRUCTION (no author code for Drift2Act or RAR); required baselines as sections 1.4
and 2.3; ledger key `suite = a2`. New identities (R1, K1-K3, L) must be appended by the coordinator through
`build_candidate_registry.py` (batch_002, never silent edits) so Stage A does not return INVALID/not-reproducible.
Retrieval was not repeated in this draft; prior-art statuses are those of `PRIOR_ART_LEDGER.md` (verified-level V
unless noted), so the novelty judgements below are "no directly overlapping work retrieved under those keywords", not
proof of novelty.

| candidate | status (prior art) | fatal flaws found (max 2) | verdict |
|---|---|---|---|
| REP1 min_of_both | HIGH_OVERLAP (Sethi, e-detectors); trivial combination | F1 MAJOR (min of two valid e-processes is textbook); data: significant loss on S2d vs rmm (+111) | Accept with Revisions as a replication only; no novelty claim |
| REP2 geometric_hazard_prior | HIGH_OVERLAP (F3; FL-005) | F1 MAJOR. Data caution: onset prior is matched by the simple control rmm on S2d (-8.2 [-19.5, 4.8]); if Q1_2 vs rmm also contains 0 on fresh seeds this is a **data-refuted core mechanism = CRITICAL -> Reject and Pivot** (clause pre-registered) | Conditional: Accept with Revisions pending fresh-seed Q1_2 vs rmm |
| REP3 e_cusum_markov_base | HIGH_OVERLAP (e-detectors with Markov base) | same as REP2 | same |
| R1 restart_min | HIGH_OVERLAP (F3) | F1 MAJOR (combination of two known components); F3 MAJOR (rmm_detector is the real baseline and already roughly ties on S2d). No CRITICAL flaw; failure region (reversal) stated | Accept with Revisions, screening only |
| K1 p1=1 | KNOWN-by-derivation | F9/F1: a reading of RAR's ablation; gains are an artifact of J having no exposure term | Reject as a method; keep as ablation control |
| K2 critical skip | PLAUSIBLY_DISTINCT, thin search | F6 MAJOR: claim rests on a synthetic family whose harmful-retrain cell is designer-chosen (q(e) is an assumption); F5-style risk none | Accept with Revisions, screening only |
| K3 adaptive W2 | HIGH_OVERLAP (Lindon) | F1 MAJOR; missing baseline (Lindon sequential canary not implemented => `missing_baselines`, record would be UNVERIFIED per section 2 of the program) | Reject and Pivot unless the Lindon comparator is added; first to drop |
| L routed-only labels | n/a (ablation) | no novelty claimed | n/a |

Cross-cutting fatal flaws of the round (idea-evaluator audit of the plan, not of a single candidate):
1. **Post-hoc control rules (section 1.3).** Selection-bias risk; mitigated by fresh seeds, strict-A1 co-reporting
   and S3c kept descriptive. If the coordinator does not accept it, drop the Q1 arm.
2. **Designer-chosen RAR family.** Every RAR effect depends on the retrain-quality model and on constants chosen by
   me; mitigated by G0, the sensitivity continuation, and by labelling results developmental. A win here is a
   statement about this family, not about production drift (F6).
3. **Seed collision** in the proposed 110060000 sub-block (section 0); fixed by 110070000.

## 4. Experiment count (budget: at most 57; this draft plans 9, hard maximum 15)

| id | experiment | count |
|---|---|---|
| A2-Q1-REP1, REP2, REP3 | replications on fresh seeds, A2 reading | 3 |
| A2-Q1-R1 | restart_min on the 16-cell Q1 panel | 1 |
| A2-Q1-R1V | R1 null-cell validity audit, 4 cells x 100 replicates | 1 |
| A2-RAR-K1, K2, K3 | canary candidates on the 5-cell family | 3 |
| A2-RAR-L | routed-only labels ablation | 1 |
| **definite total** | | **9** |
| continuation, conditional on non-DISCARD only | per surviving K: `balanced` cost-vector re-run (<= 3) and (q_poor, e_sat) sensitivity re-run (<= 3) | <= 6 |
| **hard maximum** | | **15** |

Reference runs do not count: Q1-panel comparators on fresh seeds (4 comparators x 16 cells x 20 seeds, plus the
Gap-Mix reference on 6 cells) and the `rar_persistent` references (about 10 methods x 5 cells x 20 seeds), as in A1
(cached, shared, no ledger record per reference). The G0 qualification is a gating status note, not a ledger
experiment; if the coordinator prefers conservative accounting, count it as 1 (still <= 16 of 57). At least 41 of
the 57 remain unspent by design: the next decision belongs to the checkpoint review, not to more screening.

## 5. Seeds (check against `configs/seed_registry.yaml`)

Rule: `seed = 110070000 + cell_index*1000 + replicate`, replicate 0-19 (0-99 for R1V). Cell index space (A2 only,
independent of v1/v2 indices): Q1 panel 0-15 (110070000-110085019), `rar_persistent` S5a-S5e 16-20
(110086000-110090019), R1V audit cells 21-24 (110091000-110094099). Maximum 110094099.

Checks: (1) v1 = 110000000-110003019 and v2 = 110050000-110064019 per ledger `seed_group`; A2 minimum 110070000 >
110064019 so disjoint, with a 5,980-seed gap. (2) All of A2 lies inside the registered `d2a_rar_dev` block
110000000-110099999 (status development), outside smoke 110900000-110900999 and confirmation 120000000-120099999.
(3) The proposed 110060000 base fails check (1) (collides with v2 idx 10-14). (4) The coordinator should add a
sub-block note to `configs/seed_registry.yaml` in the style of lane_b D2 ("seed id = start + cell_index*1000 +
replicate"); registry text is a frozen file and was not edited. (5) Within A2, Q1 and RAR panels do not share seeds,
and every method inside a cell uses identical seeds (paired).

## 6. Code needed (small)

1. `src/shiftlab/bench/contract/evidence_q1_a2.py` (new): `RestartMinCore` (shared geometric start grid, summable
   weights, min outside) + factory registration; leaves `evidence_q1.py` untouched.
2. `src/shiftlab/bench/contract/canary_a2.py` (new): `RARCanaryA2Policy(RARPolicy)` with modes
   `nocanary | p1 | skip_critical | adaptive_w2 | routed_labels`, `rollback_only()` factory (pass-through Gate 2/3,
   alerts disallowed), `CABHorizon`.
3. `src/shiftlab/autoresearch/stage_b_a2.py` (new): runner derived from `stage_b_q1.py` / `stage_b_v2.py` with the
   A2 seed rule, the section 1.3 control reading, the `rar_persistent` panel, `suite = a2` ledger keys.
4. `tests/d2a_rar/test_a2.py` (new): seed disjointness vs v1/v2; sum of start weights <= 1; veto/min-only
   subset property for FP; routed-only evidence guard (no non-routed RETRAINED loss used before commit); G0 canary
   entry rates; `max_lookback = 10` bit-identical host; A1 golden results unchanged.
5. Coordinator-owned, not method-agent code: `configs/d2a_rar/stream_families_v3.yaml`, `registry/DEV_SUITE_A2.json`
   (builder in `host_audit.py` style), A2 text appended to `AUTORESEARCH_PROGRAM.md` section 3a, seed registry note,
   batch_002 identities.

## 7. Registration checklist for the coordinator (before the first A2 record)

Freeze: A2 text (sections 1.3, 2.4 KEEP rule), family YAML and its sha256, DEV_SUITE_A2.json sha256, seed rule,
comparator lists, G0 thresholds, the preregistered_predictions block of every identity (win/failure region, effect
category, strongest comparator), and the REP2/REP3 refutation clause. After the first A2 record nothing above changes
without an A3 and a fresh sub-block.
