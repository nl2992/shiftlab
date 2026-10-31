# Research ledger (append-only)

Each entry: UTC date, author/role, what was done, evidence path, decision. Entries are never
edited after the fact; corrections are new entries.

## 2026-10-30 — orchestrator — environment and isolation
- Repo root `ICML/shift-research-starter`, branch `main` at `ce9d3ca`, clean. 18 worktrees
  listed. Failure Atlas (`scripts/run_failure_atlas_loop.py --workers 12`) and
  `scripts/promising_directions/a1c_alpha_mechanism.py` running at start; another 12-process
  pool was also live. Hardware: i7-13700HX, 24 logical CPUs, 15.7 GB RAM. Python 3.13.1, numpy
  2.4.2, scipy 1.17.1, pandas 3.0.1, scikit-learn 1.6.1.
- Created worktree `ICML/branch-research-monitoring-to-decision-value-2026-10-30` on new
  branch `research/monitoring-to-decision-value-2026-10-30` from `ce9d3ca`. Compute ceiling for
  this programme: 4 processes.
- Independence note: Agents A–H are same-model (Claude) subagents. Their reviews are
  **self-review**, not independent verification.

## 2026-10-30 — Agent B (prior art) — completed `02_PRIOR_ART_AND_NOVELTY.md`
- Closest threat: Regol et al., "When to retrain" (ICML 2025), which argues detection-triggered
  retraining over-triggers under retraining cost. Also Drift2Act (workshop), Cara (Mahadevan &
  Mathioudakis).
- Verdicts: H4 ESTABLISHED qualitatively; H6 established in spirit; H3 trivial corollary; H1/H2
  partially new (folklore; controlled fixed-controller protocol not found); H5 potentially new
  (shallow search). The slogan "better detection ≠ better decisions" is not claimable as novel.
- Limitations: classical QCD originals, Xu et al. theorems, HCPI not read in full; no external
  comparator code run → no VERIFIED_REPRODUCTION.
- Decision: the programme cannot claim the qualitative thesis. Any contribution must be
  quantitative/predictive (exact conversion accounting validated against simulation and real
  replay) or a sharp T3/T4-type characterisation, and must cite Regol et al. as the closest work.

## 2026-10-30 — Agent E (engine) — `src/shiftlab/decision_value/`, 30 tests pass
- Vectorised lockstep engine; truth only in `score`; label for event e first visible at
  decision e+d+1 (tested). CUSUM and Kelly detector cross-checked numerically against repo
  implementations (`monitoring.one_sided_cusum`, `dive.eprocess.MultiTimescaleStartedKellyEProcess`);
  PH, batch, SR betting are textbook reimplementations. Orchestrator re-ran tests: 30 passed.
- Smoke (S1, permanent controller, n=500): every monitor costs more than never-switch
  (+8 to +32, CIs exclude 0); CUSUM most powerful and most costly. Descriptive only — permanent
  switching into a challenger that is worse outside a transient window is expected to lose (P1).

## 2026-10-30 — Agent C (real data) — `03_REAL_DATA_AUDIT.md`, `manifests/datasets.json`
- Setting A eligible: OPSD DE load (reserved 2020-01-01..2020-09-30, 6,577 rows, outcomes not
  read), Monash electricity (reserved 2014), Binance ETH 1h (reserved 2026-01..09). Dev-only
  headroom: OPSD frozen-vs-sliding-refit H_T = 23.6 at c_s=5 vs shuffled-95% 4.7; OPSD
  frozen-vs-TSO forecast H_T well above noise at all costs; Monash noise-level for c_s ≥ 1
  ("do-nothing" control); Binance equals its shuffle reference (null control).
- No measured label-release times or application costs anywhere: delays and costs are imposed
  sensitivity parameters. Open Bandit is Setting B with no untouched window.
- Decision (G2): ≥2 eligible real Setting-A tasks exist (OPSD primary; Monash and Binance as
  negative controls with different characteristics). Reserved windows must stay closed until the
  real-data protocol is frozen.

## 2026-10-30 — Agent A (evidence audit) — `01_EVIDENCE_AUDIT.md`, `claim_registry.json` (21 claims)
- F1 VERIFIED by analysis recomputation (+0.0858 [0.0586,0.1133] @10%, +0.0938 [0.0634,0.1251]
  @20%); not a simulation rerun. "32 cells" is 14 harm cells from one generator; one benign cell
  has H2c false-alarm rate 0.307 hidden by pooling. Gas reversal PARTIALLY_VERIFIED; "reduces to
  discounted Kelly" DOC_ONLY.
- F2: HG vs local parent VERIFIED; HG vs PH not better (−0.066, −0.110, CIs include/touch 0).
  HG−PH switching net regret: +19.2 [6.2,32.2] persistent-beneficial, +26.5 [14.6,39.2] harmful
  delay-50; reversed in transient scenarios, **but there both are worse than never switching**,
  and PH was empirically calibrated while HG used 1/α → not size-matched. Doc's "20% vs 30%"
  switch rates contradicted by per-seed data (57% vs 68%; 47.5% vs 63%).
- F3 VERIFIED (10.20/9.65/7.88/7.67%; fresh seeds 10.02/9.59/7.60/7.54%; batch test
  8.99/8.51/7.68/7.21%). Average driven by W1; P3b worse than best simple comparator by 14%/10%
  in W3/W4 at B400_cs20.
- F4 VERIFIED (exact rerun; fresh seeds 587.9/291.4/208.6). F5 PARTIALLY_VERIFIED: stored
  artifact recomputes exactly, but a rerun here gives 3416 vs 2974 errors and 1.08% headroom
  (library-version sensitivity); exposed data. F6 bound VERIFIED (exact enumeration); oracle
  table DOC_ONLY.
- Process note: the agent reports its audit outputs under `outputs/decision_value/development/audit/`
  were deleted mid-run (cause unknown, possibly another agent) and regenerated.
- Decision (G1): F2's reversal is not a matched comparison and occurs where acting is wrong;
  it is not used as a headline example of H1. F3 supports H6 (batch test captures most of P3b).
  F4 supports H2 (fallback quality) as a stylized lead.

## 2026-10-30 — Agent C phase 2 (real-data dev replay) — `10_REAL_DATA_DEV_RESULTS.md`
- Run `outputs/decision_value/real_data/dev/replay_20261030T231500Z/`; reserved windows not read.
  Thresholds from a stationary block-bootstrap null on validation data (not the conditional null).
- Realised-loss P1/P4 identity holds to ≤1.4e-12 in every checked cell (accounting verified on
  real data).
- OPSD frozen-vs-sliding and frozen-vs-TSO: the challenger is persistently better; always-challenger
  beats every monitor (by ~28 and ~290 units). Monitoring adds nothing over the best static policy.
- OPSD TSO-vs-sliding (only genuinely dynamic pair): best cell CUSUM+Hold7 V=+44/+24/0 at
  c_s=0/5/20 (~5% of headroom); not robust to bootstrap or d=7; Permanent negative everywhere.
  Detection-vs-cost ranking inverted on this pair (Spearman −0.75) but flips to +0.65 under rolling
  origins → unstable, descriptive only.
- Controls behave: Monash no positive cell for c_s>0; Binance max +2.0.
- κ̂ (validation-only recipe) does not predict realised capture (frozen/TSO highest κ̂, ~3% capture).
  Negative result for the deployable diagnostic as specified.
- Decision (G9 dev): real-data dynamic headroom exists in hindsight but online monitors convert
  ~0–5% of it under imposed delays/costs; the simplest static policy dominates where the challenger
  is persistently better. Real-data confirmation is reduced to a small sanity check.

## 2026-10-30 — Agents E/F (development mechanisms) — `06_STATISTICAL_ANALYSIS.md`
- Runs `outputs/decision_value/development/mech_th{1..4}_20261030T23*`, n=1000/cell, 10 monitors
  (5 defaults + 5 variants declared before cost results), matched null alarm rate 2.8–5.2%.
- TH-1 (P2) CONFIRMED: identity exact (1.7e-13); predicted switching-cost crossing c_s* from one
  seed set's alarm CDFs agrees with the empirical crossing on an independent seed set in 39/39
  pairs (e.g. PH vs batch20: 84.5 [77.2,91.6] predicted, 78.1 [70.2,85.6] empirical).
- TH-2 (P3) CONFIRMED: incumbent-monitor alarm times bitwise identical across fallback types;
  Kendall τ(power, value) +0.24 strong, −0.78 none, −0.29 common-shock, −0.38 reversing;
  ≥MME reversals in common-shock and reversing (21/90 ordered pairs each).
- TH-3 (P5) CONFIRMED: predicted vs simulated value r=0.9999, slope 1.011, MAE 0.095 over 360
  tests; 0/360 exceed the delay–persistence ceiling.
- TH-4 (P6) INCONCLUSIVE: κ (Spearman 0.47) no better than power_opp (0.53) at predicting value;
  16/1620 ordered-pair reversals by power_T, concentrated at L=400, q=0.5.
- H6: a monitor beat the best simple reference by ≥MME in 1/66 cells — **with untuned
  controllers**. "Always" beats monitors by 17–148 in TH-1 and useful-fallback TH-3 cells.
- Note: the identities (P1/P2/P4) are exact by construction; their numerical confirmation verifies
  the implementation, not a scientific claim. The non-trivial evidence is the out-of-sample
  crossing prediction (TH-1) and the P5 predictive formula/ceiling (TH-3).
- Decision: before any H6 claim, run Experiment Type II (equal-budget tuning of controller and
  threshold per monitor and for simple references, evaluated on fresh dev seeds).

## 2026-10-31 — Type II (tuned controllers) — `11_TYPE2_TUNED_CONTROLLERS.md`, run `type2_20261031T020507Z`
- Design section of doc 11 was committed in `ac8b844` before results were written (provenance).
- 11 cells, 160 monitor configs vs 32 simple configs per cell; tune n=500 (seeds 100000+),
  evaluate n=2000 fresh (200000+), Holm over cells. Best monitor system won 0/10 non-control
  cells; best simple won 3 (−13.7, −18.2, −12.8, all beyond MME); 7 ties within MME. Negative
  control passed. Selection optimism small (−1 to +2.4).
- Tuning collapses toward simple policies: 8/10 cells select Permanent/Reverse at α=0.5, the
  grid boundary (near-immediate one-way switching).
- H1 under tuning: 0 protocol reversals in every cell. **Gate G6: the 16/1620 untuned reversals
  in TH-4 are controller-confounded; H1 is not promoted.**
- Orchestrator critique (not yet tested): all S2 cells use a symmetric chain (π_b = 0.5), where
  "always fallback" is near-optimal whenever the fallback is useful. This favours static policies.
  The regime where monitoring should matter — rare, persistent bad states (as in F4) — has not been
  tested. α grid boundary also unexplored. Decision: run asymmetric-regime Type II before any H6
  claim.

## 2026-10-31 — Agent G (adversarial self-review, same model) — `07_ADVERSARIAL_REVIEW.md`
- Classifications: P1/P4 SUPPORTED_BUT_ESTABLISHED; TH-1 crossing SUPPORTED_ONLY_IN_NARROW_SETTING
  (near-tautological: controllers are c_s-blind); P3/TH-2 SUPPORTED_BUT_ESTABLISHED; P5/TH-3
  SUPPORTED_ONLY_IN_NARROW_SETTING (r=0.9999 uses evaluator θ — an identity check, not a deployable
  prediction); C2 SUPPORTED_ONLY_IN_NARROW_SETTING; C3 INCONCLUSIVE.
- Executed falsifications (`outputs/decision_value/development/redteam/`):
  (a) random-τ: CDF-only crossing prediction inside CI in 3/10 pairs (vs 10/10 fixed τ), ~1.5–2×
  too low → TH-1 claim restricted to environments where Δ path is independent of alarms.
  (b) undelayed proxy breaks the P5 ceiling (label-only θ_max=0.197, gain −4.0; proxy θ 0.88–0.997,
  V +25..+28) → P5 scope is label-only, fixed-Hold, Markov.
  (c) Beta losses + outliers + drift: monitor +4.5 [4.0,5.1] in a ramp cell (< MME 8.4) → C2's
  "0 wins" is a tie pattern, not dominance.
  (d) "Simple" calendar/static policies are fixed-sample monitors with effective α 0.5–1 → C2 is
  about controller form/threshold, not monitoring vs no monitoring.
  (e) boundary-null false-alarm rates at interior-calibrated thresholds: CUSUM 0.389, SR 0.340,
  Kelly 0.224, batch 0.217, PH 0.037 → "matched α" is point-null only.
- Recommended decision: D. Orchestrator accepts objections 1–5 as valid; C2 is re-scoped to
  "cost-aware, high-α fixed-sample rules match tuned sequential monitors", and the theory is framed
  as accounting, not as novel theorems.

## 2026-10-31 — Type II asymmetric follow-up — `11` §8, runs `type2_asym_20261031T021545Z`, `type2_orig_ext_20261031T022617Z`
- S2 gained optional rho_g/rho_b (defaults unchanged; old-cell data SHA-256 identical; 31 tests pass).
- Rare, persistent bad states (fresh seeds 300000+/400000+): tuned monitor beat best tuned simple
  policy by ≥MME in 6/12 useful cells, 0 simple wins (diffs 6.5–9.4 vs MME 6.4–7.1); wins at d=0
  and/or B≥400; ties at d=50; B=100, π_b=0.1 neither system captures headroom. Control passed.
- Extended α grid on original cells: monitor diff improved in 8/11 cells (th2 strong −12.8 → +0.3);
  now 1 monitor win, 1 simple win, 8 ties.
- **H6 as an unconditional statement is CONTRADICTED** in development; it holds only where static
  policies are near-optimal. Simple family hit its own margin boundary → Step 0 of the confirmation
  protocol re-tunes it before freezing.
- Decision: freeze `12_CONFIRMATION_PROTOCOL.md` (conditional-value hypotheses CF-S1..S3 + Part R
  one-shot OPSD/Monash/Binance).

## 2026-10-31 - Confirmation executed - 13_CONFIRMATION_RESULTS.md, pre-execution commit ca84d30
- Part S (confirmation seeds 7,000,000+, n = 2000): CF-S1 FAILED (6.58 vs mean MME 6.79; one-sided LB 6.07 > 0),
  CF-S2 passed (1.87, LB 1.35), CF-S3 passed (-0.05 [-0.07, -0.03] vs MME 6.44). Development wins not confirmed.
- Part R (OPSD 2020, Monash 2014, Binance 2026-01..09): primary pair had no alarm at all (E = 0.0 vs MME 7.3);
  controls V <= MME; pass rule FAILED (negative or uninformative real-data evidence).
- Decision: no re-run, no re-selection; the claim that monitors beat tuned simple policies is dropped; any
  effect is at most about 1% of cost, conditional on d = 0 and rare persistent bad states.
