# P3: E4 protocol, eligibility freeze and development smoke

**Status.** 2026-10-28. Eligibility and split are done and recorded. The locked authorities have
**not** been opened. This file registers the E4 analysis before any locked value is read.
**It is a draft until the lead writes the freeze record (Section 11); revised 2026-10-28 after
the Codex review (`CODEX_PROTOCOL_REVIEW_1.md`, P3/E4).** No demand, forecast or
generation value appears in this file or in any file listed here.

Charter links: `FINAL_RESEARCH_PROPOSAL.md` Section 5 (E4) and H-B4; `REFINEMENT_ROUND_2.md`
Addendum 2; `IMPLEMENTATION_READINESS_GATE.md` row P3; `stage0/VALIDITY_TABLE.md` rows 18-19 and
obligations 3-4.

## 1. What E4 can and cannot show

- **Can show:** whether the WP4 monitors keep the per-path false-alarm bound under random
  orientation on real paths of authorities never examined for this task, and whether the
  fixed-gating injected-harm finding replicates there.
- **Cannot show:** that the frozen policy is harmful or harmless on any authority; application
  utility (costs are imposed); real-time availability; prospective performance. The calendar period
  overlaps the examined CISO and ERCO windows, and authorities share weather, calendar and market
  shocks. Paths are **correlated, not independent deployments**. The result is task-untouched
  retrospective evidence.
- **The null that is actually tested.** Random orientation certifies the monitor code on real
  covariates and dependence. It does **not** test `E[Z_t - eps | F_{t-1}] <= 0` against the real
  moving weekly-refit reference (VALIDITY_TABLE obligation 3). Any pass is a statement about the
  code, not about the real policy pair.

## 2. Eligibility algorithm (frozen and hashed before the first read)

Code: `scripts/e4_eligibility.py`. Input: `data/raw/eia/EBA.zip` (SHA-256
`3a6143c4bd853c3d6a9d9d3bb3ca7f1603a641835e9c7a050e5c8a927101936f`, verified against the receipt at
run time). The reader replaces every observed number by a presence flag before storing it, so only
availability is used. The audit's own row builder (`_eligible_rows`, `SPLITS`, `TYPES`) is imported
unchanged from `scripts/audit_eia_2026_holdout_readiness.py`.

| Step | Rule |
|---|---|
| Universe | Every `EBA.<BA>-ALL.D.H` series: **70** |
| E-agg | Exclude the 14 aggregates: CAL, CAR, CENT, FLA, MIDA, MIDW, NE, NW, NY, SE, SW, TEN, TEX, US48 |
| E-exp | Exclude previously used or exposed: CISO, ERCO, NYIS |
| E-ser | Require all of `EBA.<BA>-ALL.{D,DF,NG,TI}.H` and no duplicate hour |
| E-cov | An event is an hour with D, DF, NG, TI present and the next-hour D observed. Require coverage (complete events / hours) of **at least 0.95 in each of four windows** |
| R20 | Require at least 20 deployed-policy procure events in the 2024 rehearsal. **Deferred**, see below |

Coverage windows (event time, inclusive, UTC): `fit_2019_2023` 2019-01-01T00 to 2023-12-31T23;
`rehearsal_2024` 2024-01-01T00 to 2024-12-30T23; `path_2025` 2025-01-01T00 to 2025-12-30T23;
`path_2026` 2026-01-01T00 to 2026-10-19T17. They follow the WP4 builder and the audit splits (the
audit drops 2024-12-31 and 2025-12-31, inherited). This gate is stricter than Addendum 2's
"95% in 2019-2024 and in the evaluation window" because each registered window must pass.

**R20 is an explicit deterministic amendment, applied after the split.** Counting procure events
needs the frozen Ridge forecast and `tau` (the 90th percentile of demand), so it cannot be computed
from availability alone, and it does **not** satisfy the original promise that eligibility is fixed
before any value is touched. It is frozen here as follows.
- It is applied by the runner to each authority in the list order, before any monitor result.
- An authority with fewer than 20 deployed-policy procure events in its 2024 rehearsal is
  **excluded and retained in the report** with its count and the reason `R20`.
- **No replacement, no re-splitting, no changed threshold**, and the split lists above stay as
  recorded. The Bonferroni family (Section 7) is computed from the authorities that remain.
- R20 uses demand and forecasts but never `Z` or any monitor output. If every locked authority
  fails R20 the result is empty and is reported as such (tested).
- It is evaluated on the development authorities in the smoke run, and on the locked authorities at
  the single locked run.

**Freeze order, as executed.** `scripts/e4_eligibility.py` SHA-256 =
`2ae257140448373400e1e0cac63b3b158d9a7fb3ee1dcc8a91cf07e6654225cf`, recorded in
`stage1/e4_eligibility_prerun.json` at **2026-10-28T18:34:33+00:00**. The script then ran at
2026-10-28T18:34:35Z (it refuses to run unless its hash equals the recorded one) and wrote
`stage1/e4_eligibility.json`, which repeats both hashes. Nothing from `EBA.zip` was read for E4
before that.

### Result

| Stage | Authorities |
|---|---:|
| Demand series | 70 |
| Excluded: aggregates | 14 |
| Excluded: previously used or exposed | 3 |
| Excluded: coverage below 0.95 (no authority failed on missing series or duplicate hours) | 22 |
| **Eligible** | **31** |

Eligible: AECI, AVA, BPAT, CHPD, CPLE, CPLW, DOPD, DUK, EPE, FMPP, FPC, FPL, GCPD, HST, IPCO, ISNE,
LDWP, LGEE, MISO, NEVP, PACE, PACW, PGE, PJM, PNM, SCL, SEC, SOCO, TAL, TEPC, TPWR.

Coverage exclusions (window that fails; the full log with per-window counts is in
`e4_eligibility.json`):

| Fails `path_2026` only | AZPS, BANC, PSCO, SCEG, SWPP, TEC, TIDC, TVA, WACM, WALC, WAUW |
|---|---|
| Fails `fit_2019_2023` only | GVL, JEA, PSEI |
| Fails `path_2025` only | NWMT |
| Fails `path_2025` and `path_2026` | IID, SC |
| Fails `fit_2019_2023` and `path_2026` | SRP |
| Fails `rehearsal_2024`, `path_2025`, `path_2026` | SPA |
| Fails all four windows | AEC, BHBA, NSB |

Consequence to state plainly: several large authorities (TVA, SWPP, PSCO) are excluded because their
2026 window is under 95% complete. The gate is on availability only and was fixed before any look.
It narrows the population; it does not tilt it by outcome.

## 3. Development/locked split (seed fixed in the registry)

- Seed **100400000** (first id of `e4_split_and_orientation`, `configs/seed_registry.yaml`).
- Method: ids sorted ascending; `numpy.random.default_rng(100400000).permutation(31)`; the first
  `round(31/3) = 10` of the permutation are development, the remaining 21 are locked. numpy 2.5.4.
  Re-running `split_authorities` on the recorded eligible list reproduces the lists exactly (checked).
- **Development (10):** AECI, AVA, BPAT, DOPD, FMPP, ISNE, PACE, PNM, SCL, TAL.
- **Locked (21):** CHPD, CPLE, CPLW, DUK, EPE, FPC, FPL, GCPD, HST, IPCO, LDWP, LGEE, MISO, NEVP,
  PACW, PGE, PJM, SEC, SOCO, TEPC, TPWR.
- Development authorities are used only for implementation checks and smoke runs. The locked set is
  opened **once**, after the freeze in Section 11.

## 4. The task: the frozen WP4 task, unchanged

Reused without any edit: `src/shiftlab/dive/{reserve_costs,eia_paired_reserve,eia_injected_harm,
eia_validity_analysis,orientation_replay}.py`. The WP4 record is
`docs/eia_real_data_validity_freeze.json` (protocol SHA-256 `c40620ba...5ea`, streams SHA-256
`bcb3bcbe...e`, freeze 2026-10-27T20:58:55Z). Verified on 2026-10-28 with
`uv run --no-sync python scripts/verify_wp4_freeze.py`: **7/7 listed files match** (raw variant).

| Frozen file | SHA-256 |
|---|---|
| `src/shiftlab/dive/reserve_costs.py` | `1b7e61e519c32c341b5617de56ef4e849b853b78d5b738c827a870fd5df56a3b` |
| `src/shiftlab/dive/eia_paired_reserve.py` | `cc9b9becd1daef48debbcc9a0a3b9073b90a1aa663a2b9fc7e39af6675150478` |
| `src/shiftlab/dive/orientation_replay.py` | `285bf1ba6bdb3f8e47a56a41e45b597aaba8284b1a88a087aa289deb350ca43b` |
| `src/shiftlab/dive/eia_injected_harm.py` | `c18e18ac022f8372a1e5a3148f30e71b80bee3f37fb622492106e814efba9a91` |
| `src/shiftlab/dive/eia_validity_analysis.py` | `cad4539fa1479b46...edc35` (full value in the WP4 record) |
| `scripts/run_eia_real_data_validity.py` | `616442ac81c376fe...828e` |
| `docs/eia_real_data_validity_protocol.md` | `c40620ba990c02ab...5ea` |

**Task, as WP4:** the event is an hour with D, DF, NG, TI present and an observed next-hour D;
features are those four values; `tau` = 90th percentile of next-hour D over 2019-01-01 to
2024-12-30; procure if the forecast exceeds `tau`; costs 5 (shortfall) and 1 (idle); deployed =
Ridge frozen on 2019-2024; reference = weekly-refit Ridge, 24 h label delay; 2024 rehearsal fits
2019-2023. Paths per authority: `2025` and `2026`. `epsilon = 0.1`, `alpha = 0.05`, stake mixture
(0.05, 0.1, 0.2, 0.4, 0.8).

**Dependencies that are *not* in the WP4 freeze record.** The WP4 task also depends on files the
WP4 freeze does not hash. They are recorded here (and must be in the Section 11 record):

| File | SHA-256 |
|---|---|
| `scripts/audit_eia_2026_holdout_readiness.py` | `bb5456aa261b0fd7fe3770cb728346eb3244a77c51f87fbc7e527bd3a07aa84f` |
| `scripts/evaluate_eia_retraining_frontier.py` | `b01b6aeadb2595d69bc7bf081e18a2e70c8660bebc46c51934b648a478ddcbd7` |
| `src/shiftlab/dive/gated_monitor_comparison.py` | `c4e0281f4f10f1444a43801c52ffb3441ba35224a84d64428e9091d41e823f82` |
| `src/shiftlab/dive/eprocess.py` | `a9355d3883118ed32039feafe0db0b01fd8824dfbaed2e3d70e6710964565d41` |

**The effective program is a new E4 composition, not the WP4 program.** The unchanged WP4 file
hashes do not freeze what actually runs. The freeze record (Section 11) therefore lists the runner
`scripts/run_e4_heldout.py`, which contains every replacement, and every module it imports. The
composition differs from WP4 as follows.
1. An equivalent series reader for any authority (the audit's reader is fixed to CISO and ERCO).
2. Three coin functions of `eia_validity_analysis` (`orientation_coins`, `unmodified_coins`,
   `injection_coins`) are replaced at run time by the E4 seed layout (Section 9). The file on disk is
   untouched. A test asserts that exactly these three names change, and that the seeds equal the
   registered formulas and stay inside the block.
3. **No re-run.** The WP4 null loop re-runs a failing cell with 4,000 replicates when the cell's
   *unadjusted* 95% bound exceeds 0.05. That trigger does not match the Bonferroni decision (30 alarms
   in 1,000 passes the trigger and fails the 714-cell criterion, so the re-run would be skipped),
   and choosing between two looks needs its own correction. E4 therefore uses its own null loop
   (`e4_null_analysis`): a fixed replication count per cell, one look, no re-run. The re-run coin
   function is not used and a test fails if it is called.
4. E4 summaries (Sections 7-9), which only read the analysis tables.

## 5. Four-clock contract (VALIDITY_TABLE obligation 3)

Four clocks are fixed separately. Hours are event-time hours in UTC.

| Clock | Definition in E4 | Where it is fixed |
|---|---|---|
| **1. Event time** `t_i` | The hour whose features `X_i` are observed. The outcome `Y_i` is next-hour demand, which exists at `t_i + 1 h`. Events are processed in strictly increasing `t_i`. | `eia_paired_reserve._complete_arrays` |
| **2. Reference-training availability** | The weekly-refit reference at event `i` may train on outcome `j` only if `t_j + 1 h + 24 h <= t_i`, so its refit data end at `t_i - 25 h`. Refits happen at most weekly. The deployed policy is **frozen** on data through 2024-12-30. The reference consumes **all** matured outcomes of the monitored stream, not only the monitor's queried ones. | `evaluate_eia_retraining_frontier._simulate_policy`, `delay_hours = 24` |
| **3. Monitor feedback** | **0 h (idealised) in the primary analysis.** A queried `Z_i` is used by the monitor at event `i`, although `Y_i` exists only at `t_i + 1 h`. This is the WP4 convention and is kept so that E4 is the frozen task. Zero-cost-on-agreement makes unqueried agreements free. It is a stated idealisation, not a real-time claim. | `orientation_replay.replay_batch` |
| **4. Alarm reporting** | An alarm is the first event index `i` with `log E_i >= log(1/alpha)` before the reserve stop. Its reported time is `t_i` (clock 3 = 0 h). Delay is `t_i - t_onset` in hours, right-censored at the last event. A delayed-feedback variant of `d` hours shifts HT-type alarm times by `d` and nothing else, because queries and pacing use decision-time information only; it is reported as `d = 0` plus the stated shift, and is descriptive. | `eia_validity_analysis.classify_alarms` |

What follows from the clocks. The monitor is faster than real life by the feedback gap (clock 3
versus clock 1's `+1 h`), and the reference is slower by 24 h. Neither affects the orientation
null's mechanics, which condition on the realised path. Both limit the interpretation of any
injected-harm delay as a real detection time. Publication timing of EIA data is unknown and the
data are revised; no real-time claim is made.

## 6. Arms

| Arm | Construction | Labels |
|---|---|---|
| `full_feedback` | Mixture on `Z - eps`, bound `5 + eps` | Every event (unmatched upper reference) |
| `ungated_ht` | Uniform HT, `q = r`, bound `5/q + eps` | Any event |
| `gated_ht_fixed` | Gated HT, fixed propensity from the rehearsal disagreement rate | Disagreements only |
| `gated_ht_paced` | Gated HT, 200-event past-only pacer | Disagreements only |
| `gated_eb_paced` | Paced gating with the plug-in empirical-Bernstein engine | Disagreements only |

Budgets `r in {0.02, 0.05, 0.10, 0.20}`, hard reserve stop, as WP4: 17 cells per path.

**`gated_ppi_paced` and the uniform-PPI arm are excluded.** Their proxy needs a delayed-feedback
refit on real streams, and no validated delayed proxy implementation exists (WP4 Section 3). Per
the E4 charter the PPI arm joins only after such an implementation is validated. Timans, PPE and Xu
adaptations are not run (WP1 S3 only); the stratified arm is not alive.

## 7. H-B4(a): per-path orientation nulls (validity criterion)

- **Per path** (authority x {2025, 2026}) and **per cell** (the 17 arm/budget cells): **1,000**
  replicates (fixed), random orientation signs, all arms and budgets sharing the coins; primary
  `epsilon = 0.1`; sensitivity at `epsilon = 0` is descriptive, with no pass rule. **One look, no
  re-run.**
- **Statistic.** Alarm before the reserve stop or the end of the path.
- **Family and exact bound.** Let `m` be the number of primary cells evaluated:
  `m = 17 x (evaluated paths)`, at most `17 x 2 x 21 = 714`. The family counts every authority x
  window x arm x budget cell, so it is stricter than authorities x arms. A cell is **validated** if
  its one-sided Clopper-Pearson upper bound at level `1 - 0.05/m` is at most 0.05; otherwise the cell
  is **insufficiently validated**.
- **The replication count is chosen so that validation is possible.** With `R` replicates and no
  alarm, the bound is `1 - (0.05/m)^(1/R)`, which is at most 0.05 when
  `R >= ln(20 m)/(-ln 0.95)`: **187 at m = 714** (128 at the m = 34 of the smoke). The runner raises
  if `R` is below that. The registered `R = 1000` gives a zero-alarm bound of 0.0095 at m = 714 and
  validates a cell with up to **25 alarms** (30 at m = 34). It costs about one hour (Section 11).
- **What a failure means.** An upper bound above 0.05 means **insufficient validation**, not a
  demonstrated invalidity. The stronger statement "the observed alarm rate itself exceeds 0.05" is
  flagged separately (`point_exceeds_alpha`) and is the only case read as evidence of an invalid
  monitor. If sample size is the problem, a larger fresh-seed count is a **new registered run**, not
  a re-run of this one.
- **Per-arm decision.**
  - **NOT_VALIDATED** if any cell of the arm is insufficiently validated. This is a validity stop:
    the arm is withdrawn from efficiency claims (proposal "Validity stop"), with the wording above.
  - **SUPPORTED** if no cell is insufficient **and** the arm has at least **6 arm-informative paths
    from at least 3 authorities**.
  - **INCONCLUSIVE** otherwise. A pass on uninformative cells is vacuous and never counts as
    support. INCONCLUSIVE is an expected, legitimate outcome.
- **Information, per path, arm and budget (VALIDITY_TABLE obligation 4).**
  - A path is screened by `D_p >= 30` disagreements. 30 is about four times the 8 events that are
    needed for any alarm even when every disagreement has the maximum value +5 (computed from the
    frozen mixture); it is a screen, not a proof of adequacy.
  - For each cell the runner also reports the **expected queried disagreements**
    `sum_t D_t q_t` (before the reserve stop; `r D_p` for ungated; `D_p` for full feedback) and the
    mean labels. A cell is **informative** if `D_p >= 30` and the expected queried disagreements
    are at least **8**. An **arm-informative path** is a path whose cell at the arm's largest budget
    (`r = 0.20`; full feedback has one cell) is informative.
  - The numbers 30, 8, 6 and 3 are conservative engineering choices, not derived optima.
- **Limit that stays.** Random orientation validates the monitor mechanics conditional on the
  realised path. It does not test the real moving-reference null (obligation 3). A SUPPORTED
  verdict is about the code under that construction.

## 8. H-B4(b): injected harm (descriptive replication criterion)

- **Injection and onsets: exactly WP4.** Onsets at floor(f n) for f in {0.25, 0.50, 0.75}.
  After onset every deployed procure event whose frozen margin lies in `(0, m]` is switched to no
  reserve, with `m` the median positive margin among the deployed procure events in the
  authority's own 2024 rehearsal. 200 query replicates per path and onset; full feedback is
  deterministic.
- **Detectable cell**: a (path, onset) cell in which `full_feedback` alarms at or after onset
  (`detection_rate = 1`). Cells with no effective injection, or where full feedback does not
  detect, are excluded from the denominator and counted.
- **Matches** (primary, as WP4): the `gated_ht_fixed` median delay in events equals the
  full-feedback median delay in events in the same (path, onset), at the same `r`. Cells are
  (path, onset, `r in {0.05, 0.10, 0.20}`). Pre-onset alarms are never detections.
- **Stratification by the fixed propensity.** For each cell the runner computes the fixed
  propensity `q_fixed = min(1, r / rehearsal disagreement rate)` (the arm's own value).
  - **`q = 1` cells are structural.** Fixed gating then labels every disagreement, so matching the
    full-feedback delay follows from the construction (as in WP4's 10 of 10). They are reported in
    their own stratum and **never count toward support**.
  - **The criterion is evaluated on the `q < 1` stratum only.**
- **Rule.** Let `N` be the number of detectable `q < 1` cells and `A` their number of authorities.
  - `N >= 10` and `A >= 3` and primary match fraction `>= 0.80`: **SUPPORTED**.
  - `N >= 10` and `A >= 3` and fraction `< 0.80`: **WITHDRAWN** (the transfer statement is withdrawn).
  - Otherwise: **INCONCLUSIVE**. The fraction is reported, not tested; cells are not independent
    deployments.
- **Secondary (descriptive, labelled as such):** median delay in hours within `max(24 h, 10% of the
  full-feedback delay)`, in each stratum. It cannot rescue the primary.
- **Also reported:** pre-onset alarm rate, detection rate, labels and dollars per cell;
  `gated_ht_fixed` at `r = 0.02` is reported, not counted.

## 9. Reporting, clusters and the seed layout

- **Per path and per authority first.** One row per authority x window, with `n`, disagreements,
  the fixed propensity, R20 count, the informative flag, and each arm's verdict. No pooled p-value
  or pooled "independent deployments" statement is made anywhere.
- **Regional clusters.** The 8 locked clusters are by EIA region, from
  `stage1/e4_region_map.json`. **The map is provisional and unverified.** The repository was
  searched (docs, papers, src, scripts, configs, reports, and the EIA bulk manifest) for any
  authority-to-region assignment: none exists and the EBA archive has no region field, so **no entry
  could be verified without a download**. Entries come from recollection. Uncertain: AECI, DOPD,
  FMPP, HST, LGEE, PACE (locked: HST, LGEE). The map affects reporting only. Locked clusters:
  NW 6 (CHPD, GCPD, IPCO, PACW, PGE, TPWR), FLA 4 (FPC, FPL, HST, SEC), CAR 3 (CPLE, CPLW, DUK), SW 3
  (EPE, NEVP, TEPC), MIDW 2 (LGEE, MISO), CAL 1 (LDWP), MIDA 1 (PJM), SE 1 (SOCO). Regions with fewer
  than 3 evaluated authorities are pooled as "other"; every authority row is always shown. Per
  cluster: insufficiently validated cells and the `q < 1` H-B4(b) matches.
- **Dependence.** H-B4(b) is also reported as the fraction within each cluster, and as the
  fraction of authorities whose own detectable cells all match. Standard errors are not computed
  across authorities as if independent.

**Seed layout (block 100400001-100400999; 100400000 is the split seed).** Path index
`k = 2 * rank + w`, rank = position of the authority in the sorted eligible list (0-30), `w = 0`
for 2025 and 1 for 2026, so `k < 62 <= 110`. Each stream is one `numpy.random.default_rng(seed)`
that yields all replicates of the path (WP4 used one seed per path for 1,000 replicates, and this
follows it).

| Use | Seed | Range |
|---|---|---|
| Orientation null (1,000 replicates: signs, then uniforms; fixed, no re-run) | `100400001 + k` | 100400001-100400110 |
| Unmodified streams (200 uniform replicates) | `100400111 + k` | 100400111-100400220 |
| Injected harm (200 replicates) | `100400221 + 3k + o` | 100400221-100400550 |
| Reserved, unused (the re-run is dropped) | | 100400551-100400999 |

The block is `reserved_unused` in the registry; the registry file was **not** edited here. Seeds
consumed so far by the development smoke (AECI, rank 0): 100400001-100400002, 100400111-100400112,
100400221-100400226.

## 10. Exposure audit

Command: `uv run --no-sync python scripts/run_e4_heldout.py exposure-audit`; output
`stage1/e4_exposure_audit.json` (SHA-256
`5b90f0a9ed32c1d22ad317435c1d77f9ac82abb7f7334bd2d5b832d86c4540ab`).

Scope: all text-like files and string columns of parquet files under `outputs/` (including
`outputs/**/manifest.json`), `configs/`, `docs/`, `papers/`, `scripts/`, `src/` and `tests/`
(3,356 text files and 669 parquet files; this registration directory is excluded). Skipped: 2
parquet files over 300 MB (both under `outputs/shiftguard_unified/integrated_confirmation/
efficacy_100_v1/`, an integrated synthetic study, not EIA), and binary files (`.npz` 78, `.png`
326, `.pdf` 14, `.pyc` 570, others). Two patterns: a bounded token and the series style `EBA.<ID>-`.

Findings:
- **Series-style hits: none** for any of the 31 eligible authorities. `EBA.` appears in `outputs/`
  and `configs/` only in manifests and inventories for the CISO and ERCO paired stream and the
  readiness and source records.
- **No locked authority** appears as a token anywhere in `outputs/` or `configs/`. Five locked ids
  (DUK, FPL, MISO, PJM, SOCO) appear once each in `REFINEMENT_ROUND_2.md`, where they are the list of
  authorities with "zero references" in earlier work. This is the proposal itself, not an analysis.
- Development ids: BPAT and ISNE appear only in that same sentence. **PACE** has 21 token files; they
  are the WILDS "PACE" gate, an unrelated abbreviation (the matched path is
  `.../wilds_pace_gate_v1/`). The AECI hits are this smoke run's own outputs.
- Processed EIA datasets (`data/processed/eia/*`, outside the requested scope but checked because
  they are the other place an authority could enter): the entity ids are only NYIS, CISO and ERCO;
  none of the 31 eligible ids occurs.
- Conclusion: no recorded prior ShiftLab use of any eligible authority. This is the same limit as
  the earlier audit: it cannot rule out unrecorded human inspection, and it does not cover the time
  before the repository. The 2026 EBA source dates were inspected for coverage only.

## 11. Locked set opened once: implemented guard and freeze list

**Locked mode is implemented and tested** (`run_e4_heldout.py locked`, synthetic tests only). Order of
operations:
1. `shiftlab.freeze.require_freeze(docs/research_refinement_v1/stage1/P3_E4_freeze.json)` must pass
   (every listed file unchanged and committed). The record must list at least the protocol, the
   runner, the eligibility script and JSON, the region map and the two analysis modules, or the run
   refuses. A failed check creates nothing.
2. An exclusive marker `outputs/e4_heldout/locked/opened.json` is created with `O_CREAT|O_EXCL`
   (atomic; eight racing threads give exactly one winner in the test). It records UTC time, git HEAD,
   the freeze-record SHA-256 and the number of locked authorities. **It is created before any locked
   value is read** (a test asserts the marker exists when the first read happens).
3. If the marker exists the run refuses and reads nothing. If a run crashes after step 2 the marker
   stays: a re-run needs an explicit, recorded decision by the lead, never silent deletion.
4. Then, and only then, one archive pass reads all locked authorities, R20 is applied (Section 2),
   and analyses (a)-(c) and the summaries run. Output: `outputs/e4_heldout/locked/results/`.

**Freeze file list (what `uv run --no-sync python scripts/run_e4_heldout.py freeze-list` prints).**
It is computed from the modules the runner actually loads, so it follows the code. At the time of
writing it is 55 files (38 under `src/shiftlab/`), listed below. Each is hashed over LF-normalised bytes by `write_freeze`.

- Protocol: `docs/research_refinement_v1/stage1/P3_E4_protocol.md` (passed as `protocol`).
- Runner and tests: `scripts/run_e4_heldout.py`, `tests/test_e4_heldout.py`.
- Eligibility: `scripts/e4_eligibility.py`, `docs/research_refinement_v1/stage1/e4_eligibility.json`,
  `e4_eligibility_prerun.json`, `e4_region_map.json`, `e4_exposure_audit.json`.
- Reused scripts: `scripts/audit_eia_2026_holdout_readiness.py`,
  `scripts/evaluate_eia_retraining_frontier.py`, `scripts/verify_wp4_freeze.py`,
  `scripts/run_eia_real_data_validity.py`.
- WP4 record and protocol: `docs/eia_real_data_validity_freeze.json`,
  `docs/eia_real_data_validity_protocol.md`.
- Every loaded `src/shiftlab/**` module (the package `__init__` pulls in `shiftlab.data`,
  `shiftlab.dive` and `shiftlab.monitoring`), including `src/shiftlab/freeze.py`,
  `eia_validity_analysis.py`, `orientation_replay.py`, `eia_paired_reserve.py`,
  `eia_injected_harm.py`, `reserve_costs.py`, `gated_monitor_comparison.py`, `eprocess.py`.
- Configuration and environment: `configs/seed_registry.yaml` (after the `used_by` update),
  `pyproject.toml`, `uv.lock`.
- Not listed, by design: the data archive (pinned by SHA-256 inside the runner and eligibility
  record), `outputs/eia_paired_reserve/streams.parquet` (pinned by the WP4 freeze record, which
  this record includes; it is ignored by Git and so cannot be committed).

Other preconditions: the lead verifies the region map and re-hashes it; the seed registry is updated;
the freeze record is written **after** the last edit and all listed files are committed.

**Cost.** About 168 s per authority (Section 12), so **about one hour for 21 authorities** plus one
archive pass (about 45 s). That is inside the 2 h limit, so the family is not reduced. If a locked
authority has far more disagreements the paced arms loop in Python and may take longer; the budget
stays 2 h.

## 12. Implementation and smoke record

**Files (new; nothing existing was edited).** Current hashes are in the freeze record, not typed here,
so they cannot go stale. Immutable records: `e4_eligibility_prerun.json` SHA-256
`3ecfbf5eb41c4048573ea392a7ce29d29f77d5a4a6e2cd4f1b23760dcbe9e56d` and `scripts/e4_eligibility.py`
SHA-256 `2ae257140448373400e1e0cac63b3b158d9a7fb3ee1dcc8a91cf07e6654225cf` (unchanged since the
recorded pre-run time).

**Commands (Windows, Git Bash, repository root):**
```
uv run --no-sync python scripts/verify_wp4_freeze.py
uv run --no-sync python scripts/e4_eligibility.py            # done: 2026-10-28T18:34:35Z
uv run --no-sync python scripts/run_e4_heldout.py exposure-audit
uv run --no-sync python scripts/run_e4_heldout.py smoke --authority AECI
uv run --no-sync python scripts/run_e4_heldout.py freeze-list
uv run --no-sync pytest -q tests/test_e4_heldout.py
```

**Tests (`tests/test_e4_heldout.py`, 15 tests, synthetic data only, temp directories):** coin
replacement changes exactly three names and uses the registered seeds; seed ranges are disjoint and
inside the block; the null loop never calls the re-run coins; replication count certifies zero alarms
at m = 714 (187 does, 186 does not); Bonferroni family size is enforced and the 30/1,000 example is
insufficient with no re-run; arm support verdicts; H-B4(b) stratification (q = 1 cannot support);
empty paths; a full synthetic run that keeps an R20 failure; atomic opening; refusal without a valid
or complete freeze record; marker before any read and a refused second opening; smoke refuses a
locked authority before any read; the freeze list covers the imported modules.

**Smoke run (development authority AECI, rank 0, CPU, torch 2.9.1+cu130), final code.** Registered
counts (null 1,000, unmodified 200, injected 200), no re-run. Code git HEAD at the time:
`01a5232` plus the uncommitted edits to the runner.

| Stage | Seconds |
|---|---:|
| Read the four series (one archive pass) | 44.8 |
| Build rehearsal, 2025, 2026 streams | 4.2 |
| (a) Orientation null, 2 paths x 17 cells x 2 epsilons | 113.6 |
| (b) Unmodified | 12.6 |
| (c) Injected harm | 38.2 |
| **Total** | **213.5** |

Analysis without reading and building: about 164 s per authority. Results, development only:
R20 passes (653 procure events); 2 paths with 1 disagreement each, so every arm is INCONCLUSIVE; at
m = 34 no cell is insufficiently validated (the minimum zero-alarm count is 128 replicates);
H-B4(b): all 9 detectable cells are in the `q = 1` structural stratum, so the state is INCONCLUSIVE.

**Open items.**
1. R20 remains a post-split amendment (Section 2).
2. The coverage gate removed 22 authorities, mostly on the 2026 window (Section 2).
3. The region map is unverified and affects reporting only (Section 9).
4. Many locked paths will probably be uninformative; INCONCLUSIVE is a likely outcome for H-B4(a)
   support and for H-B4(b), since a `q < 1` stratum needs at least 10 detectable cells.
5. The seed registry still shows the block as `reserved_unused`.
6. The runner patches three module-level functions of a frozen module at run time. The freeze list
   now includes the runner and every loaded module, and tests pin the patched names.
7. The previous AECI smoke output (older code, with the WP4-style re-run logic) was deleted and
   re-generated from the final code; it was development output only.

**Continue / pivot / stop.** Continue to the freeze. The risk is power: the real-data validity check
is informative only where disagreements are plentiful, and the support rules are meant to let
INCONCLUSIVE stand.
