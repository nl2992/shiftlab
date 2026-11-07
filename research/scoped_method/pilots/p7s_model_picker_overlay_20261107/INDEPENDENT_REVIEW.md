# Independent artifact review

Read-only review of the frozen development pilot. The reviewer recomputed reported values from
`raw_episode_rows.jsonl` and streamed `raw_event_records.jsonl.gz`; it did not change implementation
or open real/locked data.

## Checks

- 1,400 episode rows, each key unique: four cells × 50 seeds × seven methods.
- 2,800,000 ordered event rows: 200 candidate streams × 2,000 events.
- Source, raw artifact, and result hashes agree with `MANIFEST.json`.
- Recomputed all means, paired t intervals, and frozen contrasts; all match `RESULTS.md` to rounding.
- Recomputed `net cost = predictive loss + label expenditure + switch expenditure` and component
  identities; no failures (maximum floating residual `2.84e-14`).
- All 400,000 candidate event propensities match the frozen union propensity with hard-budget
  depletion applied; 37,414 issued requests carry the logged combined propensity.
- Zero refused requests, no budget violations, monotone remaining budget, no requests without
  disagreement. Requested labels have issue time equal to the event and release time 100 events
  later when within horizon; otherwise release is outside the horizon.

An initial propensity check that omitted budget depletion flagged 2,311 events. Every one was an
expected zero-propensity event after the hard budget was exhausted; this was not an implementation
mismatch.

## Recomputed primary contrasts

- `F1_late_800`: candidate − Model Picker `−0.996 [−10.532, 8.540]`.
- `F1_late_800`: candidate − P7s `+0.728 [−2.780, 4.236]`.
- `F3_reversal_800`: candidate − never-switch `+56.432 [47.693, 65.171]`.
- `F0_null`: candidate − never-switch `+9.965 [9.895, 10.035]`.
- Null promotions: `1/50`; this passes the pilot's promotion-count screen only.

The frozen development gate therefore fails exactly as reported in `RESULTS.md`.

## Chronology limitation

The simulator supplies due feedback at the start of an event. The P7s adapter stages feedback,
then makes the event's query decision before incorporating evidence due at that same event;
the overlay applies its staged Model Picker update after the parent request. Thus the policy
filtration does not use same-event delivered feedback to choose that event's query probability.
This is consistent with the P7s adapter's issue-then-release update order and does not reveal
future labels, but is a conservative algorithmic timing convention rather than a claim that the
policy consumes every label already delivered at event start.
