# WP4 minimum: EIA real-data validity and injected-harm results

**Validity: PASS.** Every one of the 68 registered primary cells passed the per-path
random-orientation null. No cell needed the registered re-run. The protocol is
[`eia_real_data_validity_protocol.md`](eia_real_data_validity_protocol.md), frozen by hash in
[`eia_real_data_validity_freeze.json`](eia_real_data_validity_freeze.json) at
2026-10-27T20:58:55Z, before the first registered run. Analyses (b) and (c) are descriptive.

All four paths are previously examined development windows. Nothing here is prospective or
confirmatory, and nothing here is evidence about real operational harm. Costs are imposed.

## (a) Random-orientation null (registered pass/fail)

| Quantity | `epsilon = 0.1` (primary) | `epsilon = 0` (descriptive, null boundary) |
|---|---:|---:|
| Cells | 68 | 68 |
| Largest alarm rate | 0 / 1,000 | 28 / 1,000 |
| Largest exact one-sided 95% upper bound | 0.0030 | 0.0382 |

- At the registered tolerance no arm alarmed on any path.
- The informative path is CISO-2026, which has 150 disagreements. There, the sharper `epsilon = 0`
  check gave 2.7% for full feedback and every `gated_ht_fixed` cell, 1.6–2.8% for `gated_ht_paced`,
  0.3–0.8% for `gated_eb_paced`, and 0–0.7% for `ungated_ht`. All are below 5%, with upper bounds
  at most 3.8%.
- As stated before the run, the other three paths have 1–7 disagreements. A pass there carries
  little information.

## (b) Unmodified streams (descriptive)

- The deterministic full-feedback monitor did not alarm on any of the four paths.
- No selective-label arm alarmed, except `ungated_ht` at `r = 0.20` on CISO-2026: 2 of 200
  replicates, so 99% agreement with the full-feedback verdict.
- At `epsilon = 0.1`, the monitors therefore found no evidence that the frozen policy's
  imposed-cost excess over weekly refitting exceeded the tolerance on these windows. This is
  consistent with the very low disagreement rates. It is not a statement about real harm.

## (c) Injected under-procurement with known onset (descriptive positive control)

- **The band** is `(0, m]`, where `m` is the median positive frozen margin in the 2024 rehearsal:
  3,875 MW for CISO and 6,424 MW for ERCO.
- **Injected harm is seasonal.** It only bites when forecast demand is near `tau`, which happens
  mostly in summer peaks. So delays from onset run to thousands of hours.
  - CISO-2025 at the 75% onset has **no** flipped events. That cell has no injected harm, and no arm
    detects there.
  - ERCO-2025 at the 75% onset has 122 flips with a post-onset mean excess of 0.22. Even full
    feedback does not detect it within the window.
- **No arm alarmed before onset in any replicate.**

Detection by the end of the path (200 query replicates; full feedback is deterministic). The two
cells without detectable injected harm are excluded from the row counts.

| Arm | `r = 0.02` | `r = 0.05` | `r = 0.10` | `r = 0.20` |
|---|---|---|---|---|
| `full_feedback` (unmatched) | 10/10 cells at 1.00 | — | — | — |
| `gated_ht_fixed` | 2/10 cells detect | 10/10 at 1.00 | 10/10 at 1.00 | 10/10 at 1.00 |
| `gated_ht_paced` | ≤ 0.33 everywhere | 0.00–1.00 (mixed) | 9/10 at 1.00 | 10/10 at 1.00 |
| `gated_eb_paced` | 0 everywhere | ≤ 0.44 | 0–1.00 (mixed) | 6/10 at 1.00 |
| `ungated_ht` | 0.00–0.48 | 0.00–1.00 | 0.02–1.00 | 0.06–1.00 |

Delay and labels:

- **`gated_ht_fixed`, `r ≥ 0.05`: median delay identical to full feedback in all 10 cells.**
  Example: CISO-2026 at 50% onset, 1,232 h for both. It used 338–701 labels per path.
- **`ungated_ht` at the same budget:**
  - at `r = 0.05`, slower: 1,884 h versus 1,232 h in the same cell, with detection 0.00–1.00
    (0.52–1.00 outside ERCO-2026 at 75% onset);
  - at `r = 0.10` and `0.20`, it detects in most cells but needs 669–1,717 labels;
  - at `r = 0.20` on ERCO-2026 at 75% onset it detects only 6%, while every gated HT arm detects
    100%.
- **Paced gating is slower than fixed gating on these paths.** After onset, injected disagreements
  rise from about 0.1% to about 6–15% of events. The past-only 200-event pacer then cuts `q`
  toward its 0.10 floor, and the bound `5/q + epsilon` grows with it. Under bursty harm, the pacer
  spends labels unevenly and pays a larger bound. The empirical-Bernstein engine is slowest of
  all.
- **Why `gated_ht_fixed` works so well here.** Its fixed propensity is 1, because the rehearsal
  disagreement rate is so low, so it labels every disagreement until the reserve stop. At
  `r = 0.02` the reserve (about 140–170 labels) runs out before the summer harm, which explains its
  low detection there.

## Interpretation (descriptive)

On real EIA covariates, outcomes and dependence:
- every WP1 gated and ungated arm kept per-path false alarms well below `alpha`;
- under injected harm, fixed disagreement gating matched the full-feedback detection time from a
  5% budget upward, with a few hundred labels.

This is a real-data replication of the gating mechanism WP1 tests on synthetic paths. **Gating is
DISCERN's contribution, not ours.**

The pacing result is new and practically relevant. A past-only disagreement pacer seeded from a
quiet pre-window degrades when harm creates a burst of disagreements. Any confirmatory design
should register a pacing floor and window with that in mind.

None of this supports a method claim.

## Limits

- All four windows were examined in earlier forecasting replays.
- The injected band was chosen from 2024 data, but the harm mechanism (under-procurement near
  `tau`) is imposed.
- The real policy pair rarely disagrees, so the unmodified-stream analysis has almost no power.
- Label delay is taken as 0 for the monitors. A delay `d` shifts every HT alarm by `d` hours.
- The gated PPI arm, the Timans, PPE and Xu adaptations, and the stratified arm were not run (see
  protocol Section 3).

## Prospective clock

Started at **2026-10-27T20:58:55Z** for the arms and policy construction hashed in the freeze
record. No post-freeze EIA data has been pulled. The earliest useful prospective smoke check is
after about six weeks (about 1,000 hours per respondent; around 2026-12-08). It needs the user's
go-ahead for an API key or a fresh bulk snapshot (about 700 MB).

## Reproduction and integrity

```powershell
uv run --no-sync python scripts/build_eia_paired_reserve.py      # 84.8 s, CUDA Ridge fits
uv run --no-sync python scripts/run_eia_real_data_validity.py   # 287 s, CPU, vectorised
uv run --no-sync pytest tests/test_eia_paired_reserve.py tests/test_orientation_replay.py tests/test_eia_injected_harm.py tests/test_eia_real_data_validity.py -q
```

- **Artifacts.** `outputs/eia_paired_reserve/` holds the streams and their manifest.
  `outputs/eia_real_data_validity/` holds `null_cells.csv`, `unmodified.csv`, `injected.csv`,
  `decision.json`, and `manifest.json`.
- **Vectorised replay equivalence.** The vectorised replay equals the scalar WP1 `replay_gated` per
  replicate: identical alarms, queries and dollars, and log-e differences of at most 4.4e-16. This
  was checked by tests and by an independent 3,000-event spot check.
- **Formatting change after the stream build.** `reserve_costs.py` was reformatted by `ruff format`
  after the stream build and before the freeze. The change is layout only. The freeze record hashes
  the reformatted file, so the stream manifest's earlier hash of that file differs.
- **Implementation split.** Implementation was delegated: Sonnet wrote the stream builder, the
  replay engine and the runner, and Haiku wrote the injection. The protocol, the design, the review,
  the equivalence check, the freeze, and this interpretation are the lead's.

## Continue / pivot / stop

**Continue.** The WP4 validity minimum is met for every arm still alive, so it is recorded. Feed the
real-data validity table and the pacing caveat into the benchmark manuscript. The prospective smoke
check waits on data access.
