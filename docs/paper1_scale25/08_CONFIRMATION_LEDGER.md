# 08 — Confirmation-attempt ledger

Machine-readable ledger: [`confirmation_attempts.csv`](confirmation_attempts.csv). Code:
`scripts/paper1_scale25/stats/ledger.py`. Statistical method and power: [09](09_STATISTICAL_CERTIFICATION.md).
Template for registrations: [07](07_CONFIRMATION_PROTOCOL.md) (DRAFT).

## 1. Rules

1. **Index at registration.** Before any confirmation window is opened, `register_attempt` appends a `register`
   row. It takes the next chronological index `i = (largest index so far) + 1` and fixes `alpha_i = .05 / (i (i+1))`.
   The index does not depend on any confirmation outcome.
2. **Every opened attempt counts**, whether or not it succeeds. A registered attempt that is never opened still
   consumes its index (nothing is renumbered).
3. **Opening** is `open_attempt`, which computes the primary lower bound at the registered `alpha_i` and appends one
   `open` row (`opened = 1`, `r_hat_pct`, `L_pct`). An index can be opened once. A `(dataset_id, protocol_id)` pair
   can be registered once.
4. **Append-only.** Rows are never edited or deleted. Each row stores `prev_hash` and `row_hash` (sha256 over the
   row fields and the previous hash), so `validate()` detects edits and deletions of interior rows, a reused
   index, a wrong `alpha_i`, an open without a registration, an open before its registration time, or a double
   open. Deleting the *last* row(s) is not detectable by the chain alone; Git history of this file is the external
   anchor, so commit the ledger at every registration and at every opening.
5. **Cohort certificate** (`certify_cohort`) refuses to certify if `validate()` reports any problem. Legacy rows
   (below) reserve indices but never enter a cohort.
6. **Counts are reported separately and never merged:** registered, legacy-reserved, opened, positive (`r_hat > 0`),
   supported (`L > 0`), selected (cohort size). The all-opened mean reduction and its simultaneous lower bound are
   reported next to the selected-cohort figure.

Columns: `attempt_index, event (register|open), opened, utc, dataset_id, parent_source_id, protocol_id, contrast,
alpha_i, n_episodes, block_len, r_hat_pct, L_pct, legacy, note, prev_hash, row_hash`.
`parent_source_id` identifies the data source family (e.g. a city's 311 system), so different windows of one source
are not counted as distinct datasets in a cohort (`distinct="parent"`, the default).

## 2. The Nov-9 doc 19/20 confirmation occupies indices 1..7

The fresh chronological confirmation of 2026-11-09 (protocol [doc 19](../paper1_eqsdp/19_FRESH_CONFIRMATION_PROTOCOL.md),
locked at `1c5f2fdd`; results [doc 20](../paper1_eqsdp/20_FRESH_CONFIRMATION_RESULTS.md), builds and registration at
`e1948471`) was registered under a different protocol and had no attempt ledger. The question is whether it
consumes attempt indices in the new ledger.

**Decision (conservative): yes.** The seven eligible datasets are entered as legacy attempts 1..7 in the order of the
doc 20 eligibility table (sf, dallas, kc, austin, cincinnati, dc, sandiego), with `legacy = 1`.

Reasons and consequences:
- They were opened, and under a strict "every opened attempt counts" reading they spend part of the global error
  budget of .05. Ignoring them would make the new family appear to have a larger budget than the combined record.
- The cost is that the first new attempt is index 8 (`alpha_8 = 6.9e-4`) instead of 1 (`alpha_1 = .025`). For
  a cohort of 25 at indices 8..32 instead of 1..25, the needed common point reduction rises from about 4.4% to 4.7%
  (09, section 5).
- Oakland (ineligible by the unchanged C4 episode-count gate, `27 < 35`) and Montgomery (excluded in advance) were
  never evaluated by any policy, so they are *not* opened attempts and do not occupy indices.
- Legacy rows have no registered estimator. Their `r_hat_pct` and `L_pct` were computed afterwards, by the primary
  estimator at `alpha_i`, for the doc 19 H1 contrast (EQ+pair vs EQ+cut), purely for information. The `note` column
  says so. The H2/H3 hypotheses used the same datasets and are nested comparisons, not separate attempts.
- Legacy rows never enter a cohort: those windows are development-exposed, and the reference was the parent method,
  not the strongest reference.
- The opening time in the legacy `open` rows is the earliest possible time (the commit `e1948471` registering the
  sealed builds). The exact run time was not logged.
- If a later protocol shows the legacy confirmation should not consume budget, the correct fix is a *new* ledger
  revision with the justification recorded; the existing rows are not edited.

## 3. Operations

```
python scripts/paper1_scale25/stats/init_ledger.py --records <records_all.jsonl> --ledger docs/paper1_scale25/confirmation_attempts.csv   # one-time; refuses if the file exists
python - <<'PY'
import sys; sys.path.insert(0, "scripts/paper1_scale25/stats"); import ledger as lg
lg.register_attempt("docs/paper1_scale25/confirmation_attempts.csv", dataset_id, parent_source_id, protocol_id, contrast)   # BEFORE opening; commit
lg.open_attempt("docs/paper1_scale25/confirmation_attempts.csv", index, a, b)                                         # a, b: seed-averaged episode series
print(lg.certify_cohort("docs/paper1_scale25/confirmation_attempts.csv"))
PY
```

Concurrent writers are serialised by a lock file next to the ledger.
