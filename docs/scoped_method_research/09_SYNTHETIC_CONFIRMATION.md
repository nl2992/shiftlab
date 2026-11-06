# Synthetic evaluation and confirmation status

## Existing evidence

The corrected 100-seed × 21-regime replay is recorded in
[`CORRECTED_REPLAY_AUDIT.md`](../scoped_method_research_2026-11-06/CORRECTED_REPLAY_AUDIT.md),
with source summaries in `corrected_synthetic_replay.json` and `.md` in that directory. It is a
correction replay on previously used regimes, not an independent confirmation. In late cells
`V_late_600` and `W_late_1000`, C2/C6 lowered mean cost relative to Gated+front by approximately
7.4–7.8, but promotion remained at 0–1%; this is mostly reduced label spending and not successful
late recovery. They also lose in other improving, dependent and reversal cells.

The corrected iid null suite has 1,000 seeds and 0/1000, 1/1000, 1/1000 promotions for Gated,
Gated+front, pace-tuned respectively. Dependent-null and out-of-class results are explicitly
separated in the audit; they do not establish validity beyond the specified null class.

## New bounded pilot

The joint rollback/acquisition pilot is separately specified in
[`06_DEVELOPMENT_PROTOCOL.md`](06_DEVELOPMENT_PROTOCOL.md). Its records and results are
development-only, with reused synthetic regime families. They cannot satisfy confirmation even if
the result is favorable. It found E_rb/B2 identical across all paired episodes and E_rb more costly
than never-switch in each of three regimes. Alpha .05, SR/CUSUM and fixed reserve results were mixed
or confounded. The pilot did not include the direct front-loaded-plus-E_rb combination and did not
match all detector error guarantees; the critical review limits interpretation accordingly. Exact
results are in [`07_DEVELOPMENT_RESULTS.md`](07_DEVELOPMENT_RESULTS.md).

## Confirmation conclusion

No fresh-seed, untouched synthetic confirmation was run for a frozen new method because no distinct
candidate passed the development and novelty gates. Therefore the synthetic contribution is
**PARTIAL** for reproducible diagnosis, **FAIL** for confirmatory repair evidence. A favorable
retrospective cell must not be re-labelled as confirmation.
