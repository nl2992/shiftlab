# Dataset eligibility protocol (WS-A, Paper 1 scale-25)

Written 2026-11-09, before any new-source build and before any confirmation-window data was built or inspected.
It governs `DATASET_DISCOVERY_LEDGER.csv`, `DATASET_SOURCE_REGISTRY.json`, `02_DATASET_DISCOVERY.md` and `03_DATASET_ELIGIBILITY.md`.
Nothing here changes the cost contract (T=2000, B=200, c_q=.05, c_s=5, delay 100) or the C4 builder.

## 1. Stages and counters

| stage | meaning | evidence allowed |
|---|---|---|
| discovered | a candidate has a ledger row with public metadata | catalogue/API metadata, documentation |
| downloaded | raw data for the DEV window is on disk with a receipt (url, time, bytes, sha256) | fetch receipts |
| D0 eligible | passes every D0 criterion below, decided from metadata and documentation only | no label statistics |
| D1 dev-built | `c4_build` ran on the DEV window; validation-gate statistics exist | validation split only; test half sealed |
| D1 gate-pass | passes the four C4 gates on the DEV build | build record |
| dev-only | D0 metadata pass but no settled CONFIRM window of at least 150,000 rows; usable for development, not for the confirmatory cohort | counts |
| pending-review | counts pass but label/feature/timing design was not completed | metadata |
| confirmation window available | a settled CONFIRM window passes the metadata size rule (section 4) | row counts only |

Counters are reported separately and never merged. Windows used for D1 are development windows; they carry no confirmatory weight.

## 2. D0 criteria (all must hold; failing any gives `d0_status = ineligible` with the reason recorded)

1. **Access and licence.** Public download, no login, no payment, no terms that forbid research use. Licensed or login-gated data (CRSP, WRDS, Kaggle) is recorded in the ledger but is not D0 eligible for this public cohort.
2. **Genuine event timestamps.** A per-event timestamp (event creation or observation time) exists, so chronological order is real. Row order without calendar time (benchmark streams such as Elec2 or airlines) is recorded as `ordered-stream` and is not eligible for a confirmation window.
3. **Valid binary task with a natural delay.** The label is a recorded outcome of the event (resolution within a fixed horizon, severity class, outcome category) or a next-period observation. The outcome becomes known later than the event; the C4 delay is 100 events (24 for hourly series). The label rule is written down before any build and is not changed after seeing validation or test statistics. The expected base rate is in roughly [0.2, 0.8] from documentation, not from the data.
4. **Size.** At least 150,000 eligible events in the DEV window (the C4 gate needs 35 episodes of T=2000 in the 50% test half, so at least 140,000). Larger sources are systematically subsampled by the builder above 400,000.
5. **Features at event time.** Every feature is recorded at or before event creation, before the label is determined. Fields written at or after resolution (status, close/update dates, outcome-derived codes, fields re-assigned during handling) are excluded. A field whose timing the documentation does not state is excluded, unless it is a routing field the publisher documents as assigned by request type at intake (flagged "pass with caveat" as in `c4_build_audit.md`).
6. **Label maturity.** The DEV window ends at least 4 months before the fetch so open items have settled. The label threshold is fixed relative to event time.
7. **Leakage risks.** Duplicate/parent-child ticket propagation, identifiers that encode the outcome, near-deterministic features, and maturity trends are recorded in `leakage_risks`. A source with a feature that determines the label is ineligible.
8. **No reuse of the same data.** Overlapping windows, seeds, chunks and renamed tasks do not create new datasets (section 3).

## 3. Independence: `parent_source_id` and `domain_id`

- `parent_source_id` names the originating dataset (publisher plus dataset family). Two ledger rows with the same `parent_source_id` count once. Different windows, shards, label thresholds, carriers or stations of one dataset are not distinct datasets.
- A second task from the same publisher counts as distinct only when it is a different underlying dataset (different table, different event process: for example SF 311 and SF building permits) and the distinction is documented in `notes`. Sensitivity count: one dataset per publishing organisation (`org_id` = publisher).
- `domain_id` is the application family (municipal-311, public-safety, transport, energy, environment, health, finance-economics, text-nlp, permits-enforcement, benchmark-stream). The cohort report must show the per-domain split.

## 4. Window design (fixed here, before any build)

Every dataset has a DEVELOPMENT window and a later CONFIRMATION window from the same recipe (label, features, delay, gates).

- **Registered sources (27 sealed windows).** DEV = registered C4 window (already opened). CONFIRM = [DEV end, min(DEV end + DEV length, 2026-07-01)).
- **Fresh-opened sources (sf, dallas, kc, austin, cincinnati, dc, sandiego, oakland).** The 2025-26 fresh window is now also development. CONFIRM = [fresh end, min(fresh end + registered length, 2026-07-01)). If that interval is empty or fails the size rule, the source is marked `no confirmation window available`. No other period is substituted.
- **New sources.** DEV = [2023-07-01, 2025-07-01), or the last 12 months of it when the metadata count exceeds 400k rows per year (the builder subsamples to 400k anyway); the source is D0-ineligible on size if the DEV count is below 150k. CONFIRM = [2025-07-01, 2026-07-01). The cap 2026-07-01 guarantees at least 4 months of settlement before 2026-11-09. Sources that publish annual vintages or have another natural cadence (annual files, monthly archives) use the nearest whole-vintage rule stated in their ledger row, fixed in the registry before building.
- **Size rule for CONFIRM.** Available iff the metadata row count in the CONFIRM interval is at least 150,000 (about 37 episodes before any subsampling). Counts come from API count queries or documented file sizes. Rates extrapolated from the DEV build are labelled `estimated`, never `verified`.
- **No inspection.** Confirmation windows are not fetched, built or summarised in this workstream. Only row counts and date ranges are read. Confirmation builds happen after a confirmation protocol is registered with hashes.
- DEV windows of new sources are development data. The C4 builder still seals test-half losses and records only validation-split statistics; the D1 summary table uses only those records.

## 5. D1 criteria (on DEV windows only)

D1 is the C4 builder gate set: validation disagreement between the logistic-regression incumbent and the gradient-boosting challenger at least .03; both validation errors in (.02, .5); at least 35 episodes. A failed D1 gate is a recorded negative result and the source is not repaired (no relabelling, new features or window changes after a build). Allowed repairs are crash/parse bugs that do not change label or feature definitions, stated in the build record.

## 6. Recording rules

- Failed downloads are recorded as failures with the error, never replaced silently.
- Metadata in the ledger is copied from the publisher's API/documentation or measured by a count query. Unknown fields are left empty, not guessed.
- Hashes in the registry: raw receipt sha256 for downloaded files; sealed-array content sha256 (from `c4_build`) for built windows. For the 27 registered windows the hash is checked against the registration file; a mismatch is reported, not repaired.
- CRSP (local, licensed) is recorded for completeness only. Its market dates are not verified causal change labels or point-in-time publication timestamps (AGENTS.md), and it is not part of the public cohort.
