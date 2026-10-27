# WP1 S3: numerical-tolerance amendment (no change to estimand, arms, thresholds, or seeds)

**Recorded 2026-10-27, before any S3 outcome was available.** This applies to the
[frozen WP1 protocol](gated_vs_ungated_monitor_comparison_protocol.md).

## What happened

Two S3 launches on the registered block `58400000–58400099` stopped without writing any outputs:
- the GPT agent's launch at 2026-10-27T20:12:11Z, kept as
  `outputs/gated_monitor_compare_aborted_20261027T201211Z/launch.json`;
- the relaunch at 20:47Z, which ran about 30 minutes and raised `ValueError: observed value is
  outside the declared bounded range` from `PredictableBoundMeanEProcess.update`, called by
  `replay_gated` on the PPI arm.

The runner holds every row in memory until it finishes, so neither attempt wrote a stream or
analysis row. No S3 outcome was seen. The traceback names a code path, not a seed or a value.

## Cause (derived from code, not from S3 data)

`gated_ppi_paced` uses a proxy clipped at `5 + epsilon = 5.1`, with anchor `h = proxy + epsilon`
and support bound `B = (5 + epsilon)(2/q − 1)`.

When the proxy saturates at +5.1 and a queried disagreement has `Z = −5`:
- the increment `h − epsilon + (Z − h)/q` has magnitude `10.2/q − 5.1`;
- this equals `B` **exactly**;
- in floating point it exceeds `B` by up to about 1.4e-14 for about 22% of `q` values (checked on
  200,000 draws of `q ∈ [0.1, 1]`), and the strict `abs(value) > bound` check raises.

Saturation happens when the proxy learns large positive harm, which occurs in the harmful
scenarios S3 adds. The S2 null scenarios did not trigger it.

## Amendment

In `replay_gated`, an increment that exceeds its bound by at most `1e-9 × bound` is set to exactly
`±bound`. Anything larger still raises. Mathematically the increment lies on its bound, its
factors `1 − lambda` stay nonnegative, and every downstream consumer now sees `|v| = B` exactly.

Regression test: `test_ppi_anchor_at_clip_snaps_rounding_to_exact_bound` in
`tests/test_gated_monitor_comparison.py`. It fails on the frozen code and passes with the
amendment. All 52 tests in that file pass.

## Effect on completed stages

- **None on recorded results.** The snap acts only when the old code would have raised.
- S1 (fidelity, a historic replay) and S2 (null calibration, which finished without error) would
  reproduce exactly.
- The estimand, arms, engines, bounds, thresholds, endpoints and seed block are unchanged.

## Provenance

The S3 relaunch records the amended source in its `launch.json` source hashes and dirty-path list.
The protocol text is unchanged, so the runner's freeze check (protocol identical to HEAD) still
applies. The amendment needs a commit before the S3 results are reported as part of the phase.
