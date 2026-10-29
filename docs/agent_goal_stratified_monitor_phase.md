# Agent goal: stratified decision-harm monitor phase (≈45–55 commits)

**Issued:** 2026-10-27. **Audience:** the coding/research agent working in this repository.
**Scope:** one bounded phase that ends at a reviewable **checkpoint**, not the full study. When
you reach the checkpoint (Section 8), stop and hand back. Do not start confirmatory runs.

## 1. Mission

Build and pre-screen one candidate Paper 1 algorithm, a **stratified prediction-powered
decision-harm monitor with per-stratum support bounds**, against the strongest matched baselines.
Do this honestly enough that the checkpoint gives a clean **GO / NO-GO for a confirmation study**.

Along the way:
- verify the disagreement-gating baseline every candidate must beat;
- pre-screen a second candidate, the data-efficient e-detector, so the next phase has a ranked
  fallback.

**Definition of done for this phase:** every work package has reached its own exit (pass or stop),
and the phase report in Section 8 exists. A NO-GO is a valid, successful outcome if it is
evidenced.

## 2. Read first (in this order)

1. `AGENTS.md` and `docs/research_charter.md`. These are binding. Keep the three estimands
   separate; don't fabricate; protocol before data; record negative results.
2. `docs/anchored_gated_harm_monitor_development_protocol.md` and
   `docs/adg_growth_prescreen_results.md`. The previous candidate stopped at G1. Its growth
   machinery (`src/shiftlab/dive/adg_growth_prescreen.py`) is reusable.
3. `docs/gated_vs_ungated_monitor_comparison_protocol.md`: drafted, not yet frozen.
4. `docs/marginal_null_predictable_bound_audit.md`, which explains why a bound chosen from the
   current covariate is invalid under the pooled null, and `docs/theory_targets.md` (items 1 and 5,
   and the open issue around line 47).
5. `src/shiftlab/dive/eprocess.py` (`BoundedMeanEProcess`, `PredictableBoundMeanEProcess`,
   `StartedMixtureEProcess`), `src/shiftlab/dive/hard_budget.py` (generator, cap logic,
   `_one_method`), and `src/shiftlab/dive/predictable_bound_replay.py` (`replay_mixture_log_e`).
6. `src/shiftlab/dive/budgeted_promotion.py`: `BOUND_MODES = ("global", "decision_local")` and the
   context-alpha guard. Also `scripts/calibrate_mixed_mean_null_local_bounds.py`, and
   `src/shiftlab/dive/contextual_weighted_alpha_grid.py` for the pilot weight contract, which is
   currently hard-wired to two contexts.
7. `papers/shiftguard_unified/novelty_audit.md` (Timans, DISCERN, Xu et al., PPE, MOPE, Wang,
   e-detectors).

## 3. Verified facts and corrections to the proposal you were given

**Verified in the repository (2026-10-27):**
- `budgeted_promotion.py` refuses non-global bounds for context alpha: "context alpha requires the
  common global support bound".
- The weight helper in `contextual_weighted_alpha_grid.py` requires exactly two contexts.
- `decision_harm_experiment.py` marks `stationary` and `benign_nuisance` as **population-average**
  nulls whose per-stream oracle averages can cross `epsilon`.
- The contextual-stratified intervention result of +30.53 utility exists in
  `docs/contextual_stratified_intervention_results.md`.

**Corrections you must carry into the design:**

1. **Per-context bounds are not entirely new here.** A `decision_local` bound mode already exists.
   The repository already ran `calibrate_mixed_mean_null_local_bounds.py` (strata at ±0.12, pooled
   mean zero) **as a null** for the pooled estimand, where local bounds are invalid. Your
   reinterpretation is correct: under the stratum-wise intersection null, that design is an
   **alternative**. Say explicitly that this changes the estimand, not that it repairs the old
   result.
2. **Unverified numbers.** The proposal's "measured ratio 4.3×" and "10× measured" are not in the
   repository docs. Either source each one to a specific artifact or drop it. Do not cite the "≈18"
   derived from them.
3. **The efficiency formula depends on the regime.** `(B_global/B_k)^2 / K` is the
   Hoeffding/range-limited scaling.
   - For the repository's fixed-stake betting mixtures, the time to detection is about
     `B·log(1/alpha)/(s·mu)` when the stake cap binds, which is linear in `B`.
   - When the cap does not bind, it is about `2V·log(1/alpha)/mu^2`, independent of `B`.
   - Stratum `k` sees a fraction `w_k` of the events, has stratum mean `mu_k`, and pays
     `log(K/alpha)` under Bonferroni.
   - Derive the optimal `K` (and the label allocation `q_k`) separately for each regime, and check
     it numerically with the exact-growth machinery before any simulation.
   - The gain needs `B_k < B_global` (stratum-specific propensity floors) and/or localised harm
     (`mu_k >> mu_bar`). Under uniform `q` with homogeneous harm, stratification only loses.
4. **Disagreement gating is the `K = 2` special case.** The agreement stratum has `Z ≡ 0` and needs
   no labels; the disagreement stratum receives the whole budget. That is DISCERN's idea. **The
   stratified monitor must be compared with, and beat, the gated baseline (G1/G3 of the
   gated-vs-ungated protocol), not only pooled ungated monitors.** On the hard-budget generator,
   disagreement is about 9% of events, so this baseline is strong.
5. **Exact intersection null for calibration.** Every stratum's conditional mean of `Z - epsilon`
   must be exactly at the boundary (= 0) or below it, to machine precision.
   - For binary paired costs the right per-stratum outcome probability depends on the action pair.
     For `Z ∈ {+5, -1}` and margin `epsilon`, it is `p = (1 + epsilon)/6`, not 0.5.
   - Derive it per stratum and assert it in tests.
   - Never calibrate the intersection null on `stationary` or `benign_nuisance`.
6. **Prior art to check before claiming anything (G0):**
   - Chugg, Cortes-Gomez, Ramdas et al., *Auditing Fairness by Betting* (NeurIPS 2023): group-wise
     sequential betting tests.
   - e-value multiple testing (Vovk & Wang, e-BH).
   - Timans et al. (UAI 2025).
   - DISCERN (arXiv 2609.17560), the gating special case.
   - Xu, Karampatziakis & Mineiro (NeurIPS 2024).
   - Any anytime-valid subgroup or local-risk monitoring.

   If "per-group betting with per-group bounds plus a weighted-Bonferroni or mixture combination"
   is already published for this estimand, the novelty claim narrows to the decision-harm estimand,
   the optimal-`K`/allocation result, and the matched evidence.

## 3A. State-of-the-art comparator panel (mandatory)

Every development grid, calibration, and real-data check in this phase benchmarks against the
established methods below, with **matched information**: the same events, query uniforms, label
cap, `alpha`, and false-alarm target. Label adaptations as adaptations. If a method is
structurally incompatible with a task, exclude it **with a written reason** in the protocol.
Silent omission is not allowed.

| Method | Status in the repository | Role |
|---|---|---|
| Timans et al. (UAI 2025), official `approx_grapa` / `grapa` | Replay-verified (`scripts/reproduce_timans_risk_monitor_paired_cost.py`, `verify_…`) | Primary Q1 comparator. Full-feedback upper reference, plus a selective-label version on HT increments (adaptation) |
| Prediction-Powered E-Values (Csillag, Struchiner & Goedert, ICML 2025) | Implemented (`dive/prediction_powered_evalues.py`) | Selective-label comparator |
| Active, anytime-valid RCPS (Xu, Karampatziakis & Mineiro, NeurIPS 2024): predictor-based betting with `q* ∝ sqrt(residual second moment)` and a `q_min`-dependent stake | **Not implemented** (analytic arm A4 only) | Active-labelling comparator. Implement faithfully to its Section 2.2 construction, transferred to paired cost |
| DISCERN-style disagreement gating (Balachandran 2026) | Being built in WP1 (HT plus fixed mixture, and an empirical-Bernstein variant) | Gating baseline. Adaptation (no official code) |
| E-detectors (Shin, Ramdas & Rinaldo 2023): SR and CUSUM, horizon-calibrated threshold `T/alpha` | **Not implemented** | Required for late onset (WP2 secondary, WP3 primary) |
| Group-wise betting audits (Chugg et al., *Auditing Fairness by Betting*, NeurIPS 2023) | **Not implemented** | Required for WP2: the closest per-group betting construction |
| Comparecast (Choe & Ramdas, JMLR 2023) | Implemented (`dive/comparecast_gamma_mixture.py`) | Weak running-average null. Report it as a different null, not a head-to-head on the eventwise null |
| PPRM (ICML 2026) | Implemented (`dive/pprm_risk_monitor.py`) | Predictive-risk estimand. Include as an estimand-mismatch comparator, or exclude with a reason |
| Charter baselines: direct paired-loss full feedback; conservative no-action; one generic feature-shift sentinel (existing MMD or ADWIN code) at a matched false-alarm budget | Implemented | Required by the charter. The sentinel shows shift alarms are not evidence of harm |

The Q2 certification methods (MOPE, OPI/Molitor, Wang 2026) are out of scope for this monitoring
phase. Record that scope decision in each protocol.

A candidate counts as winning only if it beats the **strongest applicable panel member** in its
registered cell, not merely the repository's own baselines.

**How to benchmark and what counts as a win:** follow
[`agent_goal_sota_benchmark_supplement.md`](agent_goal_sota_benchmark_supplement.md). It holds the
agent prompt, the incumbent leaderboard by regime, the mechanisms M1–M7, the forbidden
shortcuts, and the win definition.

## 4. Work packages and commit budget

Commit in small vertical slices, with tests passing at every commit. Target 45–55 commits in
total, including about 4–5 for the missing comparator implementations (Section 3A). The rough
split is below. Every protocol is frozen (committed, hash in header) **before**
its first seed is run.

### WP0: housekeeping (2–3 commits)
- [ ] Commit the uncommitted ADG/G1 work: protocol, G1 module, script, tests, results, research-log
      entries, novelty-audit and PPE-audit edits. Outputs stay wherever `.gitignore` puts them.
- [ ] Before freezing `docs/gated_vs_ungated_monitor_comparison_protocol.md`, add these panel
      arms (Section 3A) to its arm table, at matched labels: Timans GRAPA (full-feedback reference
      plus the HT adaptation), PPE, and the Xu et al. active arm. Then freeze it (commit; add the
      hash and date to its header in a follow-up commit).
- [ ] Record a UTC timestamp for when the current EIA snapshot was last on disk. Anything pulled
      later is a candidate prospective window.

**Exit:** the working tree is clean apart from WP1 work.

### WP1: gated-vs-ungated verification, Stages S0–S3 of the frozen protocol (10–12 commits)
- [ ] S0: `src/shiftlab/dive/gated_monitor_comparison.py`, reusing the hard-budget generator. Write
      the tests listed in protocol Section 6.
- [ ] S1: the fidelity replay must reproduce 6/60 (common bound 96.9) and 47/60 (policy-specific
      45.9) on seeds `20373024–20373083`. **If it does not reproduce exactly, stop WP1 and
      reconcile.**
- [ ] Smoke run on 5 seeds (`58600000–04`); record runtime.
- [ ] S2: null calibration (GPU).
- [ ] S3: fresh comparison (GPU).
- [ ] Results document and research-log entry.

**Exit:** the protocol's Section 5 decision rule is applied and recorded.

### WP2: stratified monitor (≈18–20 commits)
1. **G0 prior work (2 commits).** Full reads from Section 3 item 6, recorded in `novelty_audit.md`.
   **Stop WP2 if the exact construction and estimand are published.**
2. **Theory note (3 commits)**, in `papers/paper1_decision_drift/theory_notes.md`:
   - **(a) Validity.** Optional skipping on the predictable stratum subsequence. The stratum is
     known before the outcome; propensity and anchor are fixed before the coin. Per-stratum
     constant bounds. Weighted Bonferroni (FWER for "no stratum harmed") and the fixed convex
     mixture (tests the intersection null). State the estimand difference from the pooled null
     explicitly.
   - **(b) Regime-correct detection-time approximations** and the optimal `K` and allocation `q_k`
     under a label-dollar budget (Section 3 item 3).
   - **(c) The gating special case.**

   Have a cheaper subagent check the algebra independently (Section 5).
3. **Protocol (1 commit):** `docs/stratified_harm_monitor_development_protocol.md`, using the same
   structure as the ADG protocol. It must register:
   - the estimand;
   - the arms, at least: the full Section 3A panel (including Chugg-style group-wise betting and
     e-detectors), pooled ungated (correct bound), gated HT/PPI (best from WP1, or G1f if
     WP1 is unfinished), stratified with `K ∈ {2, 4, 8}`, and an oracle-strata reference;
   - stratum construction: fixed in advance, or from an outcome-free disjoint pilot;
   - the label allocation;
   - the seed blocks (Section 7);
   - the gates and stop rules (below).
4. **Implementation (5–6 commits).**
   - `StratifiedEProcess`: per-stratum bounded-mean mixtures with constant `B_k` and fixed
     Bonferroni or mixture weights.
   - A generalised `K`-context pilot weight contract.
   - The **exact `K`-vector intersection-null DGP** and a mixed-sign alternative DGP.
   - Tests: the per-stratum mean equals the boundary to `1e-12`; strata are predictable; oracle
     perturbation does not change learner outputs; `|increment| <= B_k`; Bonferroni and mixture
     wealth identities; `K = 1` reduces to the pooled process; the gated special case matches the
     WP1 gated HT arm on a fixed seed.
   - Do not weaken the guard in `budgeted_promotion.py`. Build the new path alongside it.
   - Panel implementations not yet in the repository (Xu et al. active betting, SR/CUSUM
     e-detectors, Chugg group-wise audit) each get a paper-to-code audit note and formula-level
     tests before use, following the existing PPE and PPRM audits. Budget: about 4–5 commits.
5. **G1-style analytic pre-screen (2–3 commits).** Reuse `adg_growth_prescreen.py`. Compute exact
   expected growth on learner-side slices only, for the stratified arm against the gated and
   pooled arms, at budgets `{0.02, 0.05, 0.10, 0.20}` and `K ∈ {2, 4, 8}`. Register the criterion
   **before running**. Suggested: predicted growth of the best `K` ≥ 1.5 × the gated baseline in
   the localised-harm alternative at some registered budget, **and** no worse than 0.8 × gated in
   the homogeneous-harm alternative.
6. **Development grid (2–3 commits, GPU).** 60 seeds per cell. Primary: detection by horizon in
   the mixed-sign alternative (pooled mean zero) and in a localised-harm alternative. Secondary:
   homogeneous harm, delay, labels. Run only if the pre-screen passes.
7. **Intersection-null calibration (2 commits, GPU).** 2,000 streams per cell on the exact
   `K`-vector null. Pass if the simultaneous exact one-sided 95% upper bound is ≤ 5%. Run only if
   the development grid passes.

**WP2 stop rules:**
- prior art found (item 1);
- pre-screen fails (item 5);
- the development grid shows no gain over the gated baseline (stratified best-`K` minus gated
  < +10 percentage points of detection in the localised alternative, or > 3 points worse in
  homogeneous harm);
- calibration fails twice.

At any stop, write the results document and move to WP3.

### WP3: data-efficient e-detector pre-screen only (5–6 commits)
- [ ] G0: full reads of Banerjee & Veeravalli (arXiv 1105.1361, 1211.3729), Hou, Bidkhori &
      Banerjee (2412.20207), Lubenia & Banerjee (2509.14186), Shin, Ramdas & Rinaldo (2203.03532),
      and Saha & Ramdas (2607.28322), plus one targeted search for "e-detector" combined with
      sampling or observation control.
- [ ] A short theory note:
  - Skipped events contribute factor 1. DE-CuSum's drift-during-skip trick is **not**
    e-valid; design a predictable skip/intensity rule instead.
  - Show the horizon-calibrated SR bound `P(false alarm by T) <= T/c` survives skipping.
- [ ] Analytic or small-simulation pre-screen protocol, then a run on CPU or GPU. Compare detection
      at 75% onset at matched labels against the uniform/paced gated e-detector.
      **Stop if < +10 percentage points or < 1.5× delay reduction.**

**Exit:** a ranked recommendation for the next phase.

### WP4: live and real-data verification (6–9 commits; required at minimum level)

Read Section 4A first. Minimum level, which is required for checkpoint A:
- [ ] Inventory the live sources (Section 4A table) and confirm receipts and hashes.
- [ ] Build the EIA paired reserve-decision stream adapter from the verified 2026-10-20 snapshot
      (ADG protocol, Section 5.2 R1). The threshold, costs, and policies are fixed from 2019–2024
      data only.
- [ ] Build the random-orientation null wrapper and the label-subsampling replay.
- [ ] Run a per-path null check: 1,000 coin replicates per path for the pooled, gated, and (if
      alive) stratified arms, on the CISO and ERCO development windows. Pass if every per-path
      exact one-sided 95% upper bound is ≤ 5%.
- [ ] Inject harm with a known onset on the development windows. This is descriptive: detection,
      delay, and labels against the full-feedback verdict.
- [ ] **Start the prospective clock** (Section 4A rule 2) as soon as each arm's code is frozen.

Should level, if budget remains:
- [ ] A second live source (Binance hourly klines or NOAA ISD hourly) with its own decision-task
      contract.
- [ ] One prospective pull at the checkpoint: EIA hours published after the freeze timestamp. This
      is a **prospective smoke check**: report the per-path null and the injected-harm results
      only, and call it confirmatory nowhere.

## 4A. Live data: how to use it for verification

The repository holds data from publishers that keep releasing new observations. Data published
**after** a code or protocol freeze is untouched by construction. That is the strongest external
check available here, and it doesn't depend on whether the old splits were exposed.

| Source | Local state (verified 2026-10-27) | Adapter | Refresh route | Decision task (all costs imposed and labelled as such) |
|---|---|---|---|---|
| **EIA EBA hourly** (CISO, ERCO; also others) | `data/raw/eia/EBA.zip`, retrieved 2026-10-20, data through 2026-10-19, SHA-256 in `data/reports/eia_2026_holdout_readiness.json` | `src/shiftlab/data/real/eia.py` (API needs `EIA_API_KEY`) | Per-series API pull (small) or one bulk snapshot (about 700 MB: **ask the user first**) | Reserve procurement if forecast demand > `tau`. Frozen Ridge versus weekly refit, and versus EIA day-ahead `DF` |
| **Binance spot klines** | `data/raw/binance/` (BTCUSDT 2023-01, ETHUSDT-1h 2025-01), with receipts | `src/shiftlab/data/real/adapters.py` (data.binance.vision) | Public monthly or daily archives; no key | Long/flat on the next hour. Frozen model versus a simple momentum or reference rule; assume our actions don't move the price |
| **NOAA ISD hourly** | `data/raw/noaa/` (2023 stations), with receipts | `src/shiftlab/data/real/noaa.py` | Public; append newer station-years | Threshold alert (for example frost or heat) from a frozen forecaster versus climatology |
| Other live pulls | Check `data/raw/**/*.receipt.json` and ask the user whether any live pulls exist outside this checkout | — | — | Add only with a written task contract |

**Rules:**
1. **Full-information pairing only.** Use sources where one realised outcome scores both fixed
   policies, so the action doesn't change the outcome; state this as an assumption. We impose label
   scarcity ourselves with known query probabilities, so propensities are exact.
2. **Prospective clock.** For each arm, record a UTC freeze timestamp in the protocol, together
   with the code hash, model weights, threshold, costs, and strata definition. Only observations
   whose **pull time** is after that timestamp count as prospective. Data already on disk, and
   anything published before the freeze, is development data. EIA revises data and publication
   times are unknown, so the claim is "prospective in pull order", not "real-time".
3. **Never overwrite snapshots.** Every refresh writes a new receipt-backed snapshot (source URL,
   retrieval time, bytes, SHA-256). Manifests reference the exact snapshot. Keep raw data out of
   Git.
4. **What live data can verify:**
   - **validity:** the random-orientation null gives `P(alarm | path) ≤ alpha` exactly on every
     real path (ADG protocol Section 3.6);
   - **label efficiency:** subsampling replay against the deterministic full-feedback verdict;
   - **detection and delay:** injected harm with known onsets as a positive control;
   - **for the stratified arm:** strata from outcome-free features fixed before the freeze (for
     example demand regime or hour-of-day blocks for EIA, or volatility regime for Binance).
5. **What live data cannot verify:** ground-truth harm on unmodified streams (report it
   descriptively against the full-feedback verdict only); application utility (costs are
   imposed); and real-time availability.
6. **Budget and permissions.** Small API or archive pulls are fine. Ask the user before any bulk
   download or anything needing a key you don't have. Respect each source's terms; CRSP and Criteo
   rules stay unchanged.

## 5. Subagent policy: spin off cheaper subagents when it saves cost

**Delegate to a cheaper or smaller model, with a written, scoped brief:**
- primary-source literature reads and structured summaries (G0 items), quoting equations and
  assumptions;
- code location and grep sweeps;
- boilerplate tests from an explicit spec;
- independent algebra checks of a written derivation;
- artifact and hash verification;
- babysitting long GPU runs: launch in the background, report on exit, never poll in a tight loop.

**Keep with the main agent:**
- the estimand and the null;
- protocol text, thresholds, and seed blocks;
- the validity argument;
- the final interpretation and any GO/NO-GO;
- any edit to a frozen protocol (only as a dated, visible amendment);
- any change to existing validated modules.

**Rules:**
- A subagent's output is a report, not proof. Verify its claims, diffs, and numbers before
  committing.
- Never let a subagent pick thresholds after seeing outcomes, or run on confirmation or calibration
  seed blocks without an explicit instruction.
- Two subagents must never write the same files.

## 6. Compute and GPU policy

- **Environment:** always use the pinned environment (`uv run --no-sync …`). Do not bypass it
  (no system or conda Python), because manifests record the environment.
- **Where to run:** unit tests, analytic pre-screens, and replays run on CPU. Stream generation for
  smoke, development, calibration, and comparison runs uses **CUDA on the RTX 4060**
  (`device="cuda"`, falling back to CPU only if unavailable, and recording which was used).
- **Parallelism:** use process workers where the existing runners support them.
- **Order:** smoke run (5 seeds) first, with recorded runtime. Then project the full-run time
  before launching it.
- **Long runs:** run anything over about 2 minutes in the background. Keep the full test suite run
  (about 11 minutes) for after code changes and before each results commit.
- **Recording:** every run writes a manifest with config, Git HEAD, dirty paths, source and output
  SHA-256, device, hardware, and runtime.
- **Disk:** check free space before large runs. Keep large artifacts and raw data out of Git, as
  `.gitignore` requires.

## 7. Seed-block registry for this phase

These blocks were checked as unused in `docs/`, `papers/`, `scripts/`, `src/`, and `configs/` on
2026-10-27. Re-check before freezing.

| Use | Block |
|---|---|
| WP1 fidelity (historic) | `20373024–20373083` |
| WP1 comparison / null / smoke | `58400000–58400099` / `58500000–58501999` / `58600000–58600004` |
| WP2 pre-screen (learner slices) | `58700000–58700019` |
| WP2 development | `58800000–58800059` |
| WP2 intersection-null calibration | `58900000–58901999` per cell |
| WP3 pre-screen | `59000000–59000019` |
| Reserved for a future WP2 confirmation (do **not** use this phase) | `59100000–59100999` |

## 8. Exit criteria: the checkpoint

Stop the phase and hand back as soon as **one** of these holds.

**A. Success checkpoint (GO for a confirmation design).** All of:
- WP1 is complete and its decision rule applied;
- WP2 passed G0, the pre-screen, the development grid **against the gated baseline**, and
  intersection-null calibration;
- the theory note's validity argument has been independently checked;
- WP3 has a recorded pre-screen outcome;
- WP4 minimum level is done, and the real-data per-path random-orientation null passed for every arm
  still alive.

Deliverable: `docs/phase_report_stratified_monitor.md` containing:
- each gate's result, with links to artifacts;
- the measured gain over the gated baseline **and over the strongest applicable panel member**
  (Section 3A), with uncertainty, plus the list of excluded comparators and the reasons;
- the live-data status: the freeze timestamps; how many prospective events have accumulated per
  source; the null and injected-harm results; and the date by which a confirmatory prospective
  window will have enough events;
- the proposed confirmation protocol outline, using the reserved block;
- the remaining risks, including prior art;
- a continue/pivot/stop assessment.

**B. Evidenced NO-GO checkpoint.** WP2 hit a stop rule, and WP1 and WP3 reached their exits. Same
report, recording why the stratified monitor stopped, which candidate (if any) ranks next, and
what the benchmark manuscript should absorb (for example the gating result and the estimand
distinction).

**C. Hard stop: hand back immediately with a short report.**
- A validity failure (null calibration or a random-orientation null fails twice after one
  registered fix).
- The S1 fidelity replay cannot be reconciled.
- Prior art fully covers both WP2 and WP3.
- More than 60 commits without reaching A or B.
- A prospective-clock violation: any post-freeze live data used for development or tuning.
- Any need to change an estimand, threshold, or seed block after outcomes are visible.
- Any action outside this repository or any licensed-data rule conflict (CRSP, Criteo).

## 9. Reporting discipline

- Every gate gets its own `*_results.md`, including failures, plus a research-log entry with
  commands, code and data hashes, limits, and a continue/pivot/stop assessment.
- Keep descriptive diagnostics, development screens, and confirmatory evidence clearly separate.
- No figures unless they are made with PaperBanana from validated outputs and checked against the
  source values; if PaperBanana is unavailable, say so.
- Do not call any result "novel", "superior", or "valid" beyond what its registered gate
  establishes.
