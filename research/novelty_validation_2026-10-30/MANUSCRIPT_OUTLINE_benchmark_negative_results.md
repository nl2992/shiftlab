# Manuscript outline: benchmark / negative-results paper

**Working title.** *When a better betting engine is not a better monitor: estimand accounting, calibration limits and negative
results for limited-label monitoring of decision harm.*
**Status.** Outline only. Every claim is tagged with its evidence class (CONFIRMED / PROVED / DEVELOPMENT_ONLY / EXPLORATORY /
FALSIFIED / UNVERIFIED) and a source in this repository. Items marked **[TO DO]** need work before they may be written as results.
**Venue fit.** Benchmarks/negative results track (ICML/ICLR workshop or datasets-and-benchmarks style), not a main-track method paper
(see `12_FINAL_PUBLICATION_DECISION.md`).

## Thesis (one paragraph)
Under limited, delayed labels, apparent power gains for decision-cost monitors are easy to produce and hard to attribute. We show that
(i) several headline gains reflect an estimand/label mismatch or an unequal null rather than a better detector; (ii) a prominent
engine improvement (Brier-guided discounted-Kelly betting) is a composition of known techniques whose gain is conditional on guide
alignment and reverses on a real stream; (iii) estimated nominal risk, not the betting engine, dominates power at realistic calibration
sizes; and (iv) a joint label-acquisition-and-switching policy yields at most a small, DP-implied advantage on exact instances.
We release the registered protocols, counterexamples, and per-seed artefacts.

## 1. Introduction
- Problem: decide when a deployed model's *decision harm* warrants action with few, delayed labels; distinguish shift, predictive degradation, harm (AGENTS.md separation).
- Contributions (all negative/benchmark; no new-method claim):
  1. An estimand ledger separating three quantities and the null classes used by each monitor.
  2. A reduction audit showing the strongest repository candidate (H2c) is a composition (Gate A, `02`).
  3. Counterexamples: guide misalignment, estimand mismatch, covariate-dependent cap (HG), evaluator null-harm bug.
  4. A real-data replay where the synthetic ordering reverses (`07` §3), with a wealth-level mechanism.
  5. Exact-solver kill test for joint acquisition+switching (`07` §2).
- What we do **not** claim: superiority over any published method; novelty; real-data confirmation.

## 2. Setting and estimands
- Notation: `D(P_t,P_0)`, `R_t(f)−R_0(f)`, `R_t(π_t)−R_t(π_ref)`; decision loss FN 5 / FP 1; economic tolerance ε.
- Null classes: conditional per-step cost null vs stationary-average risk null vs Brier-risk null (`04`). Why a Brier alarm is not an economic error.
- Information structure: filtration, label-release clock, query propensity, hard budget; synthetic oracle truth is evaluator-only.
- Validity accounting: horizon-Ville vs ARL (e-detector SR alarms on 100 % of 2000-step null streams at threshold 1/α — repo, PROVED); α split `δ_S + α_T`.

## 3. Related work and reduction matrix
- Table from `02`: Podkopaev–Ramdas, PPRM, Betting on Predictions, active RCPS, CAMS, e-detectors, Challenger, Drift2Act, budgeted sensing/CPOMDP.
- Reading depth stated per row; UNRESOLVED rows kept UNRESOLVED. **[TO DO]** read Challenger, Drift2Act, CAMS full text; e-detectors body; appendices of Betting on Predictions.

## 4. Benchmark design
- Synthetic: G5 generator family (8 conditions × shifts), delay 5, 5/10/20 % labels, paired seeds; evaluator-side oracle truth never visible to monitors.
- Comparators with status labels (`03`): cost-only pooled/discounted Kelly, ONS, PR-style CS (SOURCE_INSPIRED), PPRM adapters, CUSUM/PH, SR e-detector; Brier-null methods reported on a separate axis.
- Metrics: null rejection, power, detection delay, cumulative pre-alarm harm, labels used, runtime.
- Real: UCI gas counterfactual replay (protocol `06`, committed before run). **[TO DO]** unexposed second domain (NYC TLC is the candidate; declare event vs publication time and the replay label).
- Protocol hygiene: frozen hypotheses, append-only ledger, withdrawn reports retained.

## 5. Results
### 5.1 What survives (synthetic, within class)
- Frozen G5: H2c − better cost-only comparator = +0.086 [.059,.113] / +0.094 [.063,.125]; 13/14 and 14/14 cells — **CONFIRMED, narrow**. Tolerance-aligned ε = 0.10: power .136 / .256, size ≤ .006 — DEVELOPMENT_ONLY.
### 5.2 What does not (estimand and null accounting)
- "Benign false alarm ≈ .067" was an artefact of labelling harm < 0.10 as benign under a zero-tolerance null: true-null alarm ≈ .01 — FALSIFIED reading (`icml_sprint/02`).
- Brier-null methods alarm ≈ 1 % where cost does not rise; they are more powerful at small real cost rises — different null, not worse decisions.
- HG covariate-dependent cap invalidates the marginal null; uniform cap repair — FALSIFIED then repaired.
### 5.3 Calibration dominates power
- Estimated nominal risk removes useful power below ~5,000 calibration events (repo, DEVELOPMENT_ONLY); in our gas replay the Hoeffding margin (0.30) is ≈ 27× mean cost, so the real-data null check was uninformative (`07` §3). **[TO DO]** pre-registered comparison of Hoeffding vs empirical-Bernstein bounds on an unexposed stream.
### 5.4 Mechanism of Brier guidance (C1)
- Exact reduction to discounted Kelly; validity independent of guide (PROVED, `08` S1).
- Stylised sweep: gain +.03–.14 only at 10–20 % labels with co-shifting guide, same at ρ = 0, loss up to −.59 when flat/opposed (DEVELOPMENT_ONLY).
- No growth-rate theorem (UNPROVED); Kelly restatement is insufficient.
### 5.5 Real-data reversal
- Gas replay: H2c later than cost-only Kelly/ONS by 242–824 events (CIs exclude 0), 2–4× pre-alarm excess cost; wealth deficit −7…−30 nats at batch-6 onset from betting without a margin (EXPLORATORY; exposed dataset; one fixed stream).
### 5.6 Joint acquisition and switching
- 192 exact instances: joint beats best separate in 27 (max 1.1 % of net cost), needs B ≥ 2, never loses — a benchmark illustration of standard belief-MDP value of information. Repository kills: deadline-aligned acquisition, RLS, split-clock, futility, belief compression, restarts.
- Real-data switching tasks (Bike, Beijing, gas): alarm-triggered controllers add cost or find little headroom (repo, DEVELOPMENT_ONLY).

## 6. Negative-result catalogue (table)
Columns: candidate · registered test · outcome · reduction/known source. Rows: stratified evidence (M1–M3), data-efficient e-detector (M4), PPI anchors (M7), restarts, dependence-aware monitoring (NO_GO), HG, H2c, Q2/Q3 controllers, 1,836-tuple combination screen (best 4.07 % cost reduction, below its 10 % gate).

## 7. Discussion
- Lessons: report separate validity and downstream-economic comparisons; fix the null before the detector; budget calibration explicitly; distinguish engine improvements from monitoring algorithms.
- Limitations: single-lineage authorship of most artefacts; one real domain; synthetic world families; no faithful PPRM/PR CM-EB reproduction; exposed real streams.
- Open question that would change the verdict: a separation theorem for auxiliary-statistic bet sizing plus a fresh two-domain confirmation.

## 8. Reproducibility appendix
Environment (`uv sync --all-extras`, Python 3.13, numpy 2.5.4), seeds and commit hashes (`LEDGER.md`), checksums (UCI zip `91e8f466…1fe4`), test counts (1475 + 899 passed baseline; 4 programme tests), scripts and outputs under `research/novelty_validation_2026-10-30/`.

## Figures and tables (all derived from validated outputs; **PaperBanana required per AGENTS.md — not yet available/run here [TO DO]**)
- F1 estimand/null-class diagram (method diagram).
- F2 power vs label rate by comparator, G5 frozen cells.
- F3 guidance-alignment heatmap (X1 sweep, `outputs/x1_guidance_mechanism_q*.json`).
- F4 gas stream: per-batch cost and log-wealth trajectories (H2c vs C1/C2).
- F5 joint-vs-separate gap by B and delay (`outputs/x2_joint_vs_separate_dp.json`).
- T1 reduction matrix; T2 baseline fidelity labels; T3 negative-result catalogue.

## Pre-submission checklist
- [ ] Read remaining primary sources; update `02`.
- [ ] Unexposed second real domain, protocol frozen first.
- [ ] Faithful PR/PPRM CM-EB implementations or explicit exclusion.
- [ ] Independent re-run of G5 by someone other than the original author agent.
- [ ] Figures via PaperBanana from validated outputs; inspect against source values.
- [ ] Remove or label every DEVELOPMENT_ONLY/EXPLORATORY number in the abstract.
