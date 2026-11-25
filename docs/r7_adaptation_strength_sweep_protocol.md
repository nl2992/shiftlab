# R7 adaptation-strength sweep: protocol and pre-run predictions

Written 2026-11-23 before any sweep stream was generated. Extends the
[gated-versus-ungated comparison](gated_monitor_comparison_results.md), whose R7 finding (fixed gating
equal or better than past-paced gating under harmful adaptation) was measured at one intervention
strength. Gating is DISCERN's mechanism; this sweep characterises how the monitors behave as the
intervention strengthens.

## Design

- Scenario `harmful_adaptation`, n = 3200, intervention at event 1600, monitor from event 800.
- New knob `adaptation_strength` s in {0.10, 0.25, 0.50, 0.75, 1.00}: each post-intervention event
  is forced to the positive action with probability s (coins from `seed + 31337`). s = 1.00 is the
  registered scenario and replicates the earlier cell on fresh seeds.
- Budgets r in {0.02, 0.05, 0.10, 0.20}. Seeds 61000000-61000099 (100 per cell, unused elsewhere in
  the repository). 2,000 tasks. All arms and engines of the registered comparison are recorded
  unchanged. Added per gated arm: `labels_pre_onset`, `q_mean_post_onset`; `processed` is the event at
  which the label reserve stops the monitor.
- Primary comparison: `gated_ht_fixed` vs `gated_ht_paced` under the same engines, detection and
  censored delay by (s, r); secondary: reserve-exhaustion horizon (`processed`), ungated `uniform_ppi`
  and full feedback as references.

## Predictions

1. **P1 (R7 extends).** At every s where the path has material harm, `gated_ht_fixed` loses no more
   than 3 detection points to `gated_ht_paced` at any budget, and is ahead at s = 1.00 (r = 0.10).
2. **P2 (reserve).** Fixed gating's processed horizon shrinks monotonically in s (disagreement
   rises, q stays at its validation value); paced gating's horizon shrinks more slowly because q falls.
3. **P3 (failure boundary).** At r <= 0.05 every selective arm's detection falls with s and is at or
   below 0.35 at s = 1.00; `uniform_ppi` stays near 0 throughout.
4. **P4 (validity).** Pre-onset alarm rate of every arm is at most 5% in every cell (simultaneous
   exact upper bound across cells for each arm).

Cells where the realised path has no material harm are reported as null cells (false-alarm rate
only). No tuning follows the results; the sweep is a characterisation.
