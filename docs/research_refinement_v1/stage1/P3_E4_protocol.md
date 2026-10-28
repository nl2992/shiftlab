# P3: E4 protocol, eligibility freeze and development smoke

**Status.** 2026-10-28. Eligibility and split are done and recorded. The locked authorities have
**not** been opened. This file registers the E4 analysis before any locked value is read.
**It is a draft until the lead records the freeze hashes (Section 11).** No demand, forecast or
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

**R20 is defined here and evaluated later.** Counting procure events needs the frozen Ridge
forecast and `tau` (the 90th percentile of demand), so it cannot be computed from availability
alone. The runner applies it to each authority before any monitor result is computed. An authority
that fails R20 is excluded and **reported as a post-split exclusion**, with its count, in the final
table. R20 uses demand and forecasts but never `Z` or any monitor output. It is evaluated on the
development authorities in the smoke run, and on the locked authorities at the single locked run.

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

**Only two changes from WP4**, both in the wrapper `scripts/run_e4_heldout.py`
(SHA-256 `8ec99783a7b1b907acd21ae07b08d59696675af2b460c7106d1396a09a846e1b` at the time of
writing; re-record at freeze):
1. An equivalent series reader for any authority (the audit's reader is fixed to CISO and ERCO).
2. The coin functions of `eia_validity_analysis` are replaced at run time with the E4 seed layout
   (Section 8). The frozen file on disk is untouched, and its hash is unchanged.

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

- **Per path** (authority x {2025, 2026}) and **per cell** (the 17 arm/budget cells): 1,000
  replicates with random orientation signs, all arms and budgets sharing the coins; primary
  `epsilon = 0.1`; sensitivity at `epsilon = 0` is descriptive, with no pass rule.
- **Statistic.** Alarm before the reserve stop or the end of the path.
- **Exact bound with Bonferroni.** Let `m` be the number of primary cells actually evaluated
  (17 x the number of evaluated paths, at most 17 x 42 = 714 for 21 locked authorities; this
  counts every authority x window x arm x budget cell, so it is stricter than authorities x arms).
  A cell passes if the one-sided Clopper-Pearson upper bound at level `1 - 0.05/m` is **at most
  0.05**. The family-wise claim is that every cell passes. For m = 714 and 1,000 replicates a cell
  with no alarm has upper bound 0.0095, and the cell passes with up to 25 alarms; for m = 34 the
  numbers are 0.0065 and 30.
- **One registered fix, as WP4.** A failing primary cell is re-run once with 4,000 fresh
  replicates, judged by the same Bonferroni bound (up to 149 alarms at m = 714). Failing both is a
  validity failure for that arm.
- **Per-arm decision.**
  - **FAIL** if any cell of the arm fails after the re-run. The arm is withdrawn from every
    efficiency claim (proposal "Validity stop"), whatever the other arms do.
  - **SUPPORTED** if no cell fails **and** the arm has at least **6 informative paths from at least
    3 authorities**.
  - **INCONCLUSIVE** otherwise. A pass on uninformative paths is reported as vacuous and is never
    counted as support.
- **Minimum-disagreement requirement (VALIDITY_TABLE obligation 4).** A path is *informative for
  the null* if it has at least **30 disagreements** (`D_p >= 30`). Rationale, stated before the
  run: with every disagreement at its maximum value +5 the full-feedback mixture needs at least 8
  events to reach `1/alpha = 20` (computed from the frozen mixture, with `epsilon` = 0.1 or 0), so
  paths with fewer than 8 disagreements cannot alarm at all, and WP4's three paths with 1-7
  disagreements were exactly that. 30 is about four times that minimum, so that sign-randomised
  paths have room to cross the threshold by chance. WP4's single informative path had 150. The
  number 30 and the 6/3 path/authority counts are conservative engineering choices, not derived
  optima. `gated_ht_fixed` is additionally vacuous (propensity 1, no HT weighting) on any path
  where the rehearsal disagreement rate leaves it at 1; the runner reports the realised fixed
  propensity per authority, and the report states which authorities exercised HT weighting. The
  paced and ungated arms at low `r` can be low-information even on informative paths, and are
  reported with their labels per cell.

## 8. H-B4(b): injected harm (descriptive replication criterion)

- **Injection and onsets: exactly WP4.** Onsets at floor(f n) for f in {0.25, 0.50, 0.75}.
  After onset every deployed procure event whose frozen margin lies in `(0, m]` is switched to no
  reserve, with `m` the median positive margin among the deployed procure events in the
  authority's own 2024 rehearsal (set before looking at any registered path). 200 query
  replicates per path and onset; the full-feedback monitor is deterministic.
- **Detectable cell** (as WP4's 10 of 12): a path-onset cell in which the deterministic
  `full_feedback` monitor alarms **at or after onset** (`detection_rate = 1`). Cells with no flipped
  event, or where full feedback does not detect before the path ends, are excluded from the
  denominator and counted.
- **Matches** (primary, exactly as WP4 compared them): the `gated_ht_fixed` median delay **in
  events** equals the full-feedback median delay in events, in the same path-onset cell, at the
  same budget. Cells are (path, onset, `r in {0.05, 0.10, 0.20}`). Pre-onset alarms are never
  detections.
- **Criterion.** The primary match fraction over all detectable cells is **at least 0.80**. If it
  is not, the transfer statement is withdrawn (proposal H-B4). A fraction is reported, not a test.
  The denominator is cells, **not** independent deployments.
- **Secondary (descriptive, labelled as such).** Median delay in hours within `max(24 h, 10% of
  the full-feedback delay)`. It is reported next to the primary and cannot rescue it. This is
  added because exact equality is expected to hold only where the fixed propensity is 1 (WP4's
  result), and a primary that equals 1 for a trivial reason would say little.
- **Reported separately:** pre-onset alarm rate, detection rate, labels and dollars per cell;
  `gated_ht_fixed` at `r = 0.02` (where its reserve was too small in WP4) is reported, not counted.

## 9. Reporting, clusters and the seed layout

- **Per path and per authority first.** One row per authority x window, with `n`, disagreements,
  the fixed propensity, R20 count, the informative flag, and each arm's verdict. No pooled p-value
  or pooled "independent deployments" statement is made anywhere.
- **Regional clusters.** The 8 locked clusters are by EIA region, from
  `stage1/e4_region_map.json` (SHA-256
  `26909570316302bd4241e811b62300fd3cc993b3de41d3dd26de682f16423cdd`). **The map is
  provisional: it is not verified against an EIA list** (the archive has no region field), and
  five entries are marked uncertain. It affects reporting only. It must be verified and
  re-hashed before the locked run. Locked clusters: NW 6 (CHPD, GCPD, IPCO, PACW, PGE, TPWR), FLA 4
  (FPC, FPL, HST, SEC), CAR 3 (CPLE, CPLW, DUK), SW 3 (EPE, NEVP, TEPC), MIDW 2 (LGEE, MISO), CAL 1
  (LDWP), MIDA 1 (PJM), SE 1 (SOCO). Clusters of three or more are reported on their own, the rest
  are pooled as "other"; every authority row is always shown.
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
| Orientation null (1,000 replicates: signs, then uniforms) | `100400001 + k` | 100400001-100400110 |
| Unmodified streams (200 uniform replicates) | `100400111 + k` | 100400111-100400220 |
| Injected harm (200 replicates) | `100400221 + 3k + o` | 100400221-100400550 |
| Single re-run (4,000 replicates) | `100400551 + (17k + j) mod 449` | 100400551-100400999 |

`j` is the registered cell index (0-16). The re-run streams can collide across cells; this is
harmless for validity because each cell is judged on its own bound. The block is `reserved_unused`
in the registry; the registry file was **not** edited here. Seeds consumed so far by the
development smoke (AECI, rank 0): 100400001-100400002, 100400111-100400112, 100400221-100400226.

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

## 11. Locked set opened once (preconditions)

The locked run is authorised only after the lead:
1. verifies `region_map` against an EIA list and re-hashes it;
2. confirms this protocol (and, if changed, re-records the hashes above);
3. writes `stage1/P3_E4_freeze.json` containing UTC time and the SHA-256 of this protocol, the
   runner, `e4_eligibility.py`, `e4_eligibility.json`, `e4_region_map.json`, the 7 WP4 files, the 4
   extra dependencies and `streams.parquet`;
4. updates the seed registry (`used_by`);
5. implements the `locked` mode of the runner. **It is a refusing stub today.** It must check the
   freeze record, write `stage1/e4_locked_opened.json` before reading any locked series, and
   refuse a second run.

The locked run reads one archive pass for all 21 authorities, applies R20, runs analyses (a)-(c)
and the summaries above, and writes only to a new directory under `outputs/e4_heldout/`.
Estimated cost from the smoke (below): about 160 s of replay per authority, so roughly one hour
for 21 authorities on CPU, plus about 45 s to read the archive.

## 12. Implementation and smoke record

**Files (all new; nothing existing was edited):**

| File | SHA-256 |
|---|---|
| `scripts/e4_eligibility.py` | `2ae257140448373400e1e0cac63b3b158d9a7fb3ee1dcc8a91cf07e6654225cf` |
| `scripts/run_e4_heldout.py` | `8ec99783a7b1b907acd21ae07b08d59696675af2b460c7106d1396a09a846e1b` |
| `stage1/e4_eligibility_prerun.json` | `3ecfbf5eb41c4048573ea392a7ce29d29f77d5a4a6e2cd4f1b23760dcbe9e56d` |
| `stage1/e4_eligibility.json` | `bdd1eb38f119b7e620fe0c3bcbdcb0c4584bfa8a0af2cc8fe87d54ced755a324` |
| `stage1/e4_exposure_audit.json` | `5b90f0a9ed32c1d22ad317435c1d77f9ac82abb7f7334bd2d5b832d86c4540ab` |
| `stage1/e4_region_map.json` | `26909570316302bd4241e811b62300fd3cc993b3de41d3dd26de682f16423cdd` |

**Commands (Windows, Git Bash, from the repository root):**
```
uv run --no-sync python scripts/verify_wp4_freeze.py
uv run --no-sync python scripts/e4_eligibility.py
uv run --no-sync python scripts/run_e4_heldout.py exposure-audit
uv run --no-sync python scripts/run_e4_heldout.py smoke --authority AECI
```

**Eligibility run:** about 72 s wall-clock (one pass over the 4.4 GB `EBA.txt` member). Outputs:
31 eligible, 10 development, 21 locked (Sections 2-3).

**Smoke run (development authority AECI, rank 0, CPU, torch 2.9.1+cu130, CPU Ridge).** Registered
replicate counts (null 1,000; re-run 4,000; unmodified 200; injected 200). Code git HEAD
`ef60fc075fa3a595d0ea877ffa1322bfc5cd77b7` with the new files untracked. Output
`outputs/e4_heldout/smoke_AECI/` (ignored by Git).

| Stage | Seconds |
|---|---:|
| Read the four series (one archive pass) | 31.8 |
| Build rehearsal, 2025 and 2026 streams | 2.9 |
| (a) Orientation null, 2 paths x 17 cells x 2 epsilons | 112.6 |
| (b) Unmodified | 10.7 |
| (c) Injected harm | 32.8 |
| **Total** | **190.9** |

(A first identical run took 184 s; two earlier attempts failed with `MemoryError` because the machine
had about 1 GB free, and succeeded unchanged when memory was available. The reported run is the
second complete one and uses the final wrapper hash.)

Results on AECI, development only, descriptive:
- R20: 653 deployed procure events in the rehearsal, passes.
- Paths: 2025 with 8,736 events and 1 disagreement; 2026 with 6,989 events and 1 disagreement.
  Both are **uninformative** for the null (D < 30); the arm verdicts are all INCONCLUSIVE, which is
  the intended behaviour of the informativeness rule.
- Null at `m = 34`, level 0.99853: 34/34 cells pass, 0 informative cells, 0 failing. WP4-style
  decision (68-cell rule on the 4-path layout, here 2 paths): pass.
- H-B4(b) machinery: 9 detectable cells, 9 of 9 exact matches (and 9 of 9 within tolerance). With
  one disagreement per path this reflects a fixed propensity of 1, as in WP4, and is not evidence.
- The coin override was exercised (the seed layout is applied, not WP4's). The locked refusal was
  tested: `smoke --authority CHPD` exits with "LOCKED authority" before any series is read;
  `locked` exits without freeze.
- Existing WP4 tests pass (`tests/test_eia_real_data_validity.py`, `test_eia_paired_reserve.py`,
  `test_eia_injected_harm.py`: 36 passed). No new unit tests were added for the wrapper.

**Problems and open items:**
1. **R20 is evaluated after the split**, on values (the Ridge forecast and `tau`). Every R20 failure
   must be reported as a post-split exclusion.
2. **The coverage gate removed 22 authorities**, including large ones. Mostly `path_2026` below 95%.
   Whether this is a data artefact of the 2026 snapshot (recent revisions) was not examined and
   would need values or finer availability analysis. It is not a problem for validity, only for
   representativeness.
3. **Region map is unverified** (Section 9).
4. **Many locked paths will probably be uninformative**, as AECI is (1 disagreement). The rate of
   informative locked paths is unknown until the run. The 6-path, 3-authority rule makes
   INCONCLUSIVE a real possible outcome for H-B4(a) support. That is honest, not a defect.
5. **Wrapper `locked` mode is a stub**, and the registry is not updated (Section 11).
6. **Unfrozen dependencies of WP4** (Section 4) were hashed here, not in the WP4 freeze.
7. The runner patches module-level functions of a frozen module at run time. The file hash is
   unchanged and the patch is tiny, but it is a monkeypatch, and a reviewer should check that the
   replaced functions are exactly `orientation_coins`, `rerun_coins`, `unmodified_coins` and
   `injection_coins`.
8. Memory: the machine had about 1 GB free during the work; the full locked run reads one archive
   pass and holds 1,000 x n replicate arrays per path (about 150 MB), so it should be run when
   memory is free.

**Continue / pivot / stop.** Continue to the freeze (Section 11). E4 is cheap and well specified,
but its main risk is power: the validity null on real paths is informative only where disagreements
are plentiful, and the previous four paths had one such path.
