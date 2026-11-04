# Version-indexed gate: null implementation check

**Status:** development calibration diagnostic, not confirmatory evidence or proof of validity.
Locked before this run.

## Question

Does the version-indexed implementation show a null promotion frequency grossly inconsistent with
its nominal alpha allocation in the exact synthetic conditional null used by the version-update
screen?

## Protocol

* Run `scripts/sota_sprint/versioned_screen.py --scenarios null --seeds 1000` with seed base
  `2026110907`.
* T=2000, B=200, c_q=.05, c_s=5, delay=24; versions activate at 0 and 800.
* The incumbent and both versions have independent Bernoulli error probability .40 at every
  scored event; future version 2 predictions are copied from the incumbent until activation.
* Run the same version-indexed gate, RMM, front-loaded gated and Choe-Ramdas gates, A5b, and
  version-reset Model Picker as in the existing runner.
* Record candidate promotion count and Wilson 95% interval, label use, maximum budget use and mean
  cost. Baseline promotion rates are diagnostics only.

## Interpretation rule

For 1000 seeds, a candidate point rate above .06 or a Wilson 95% upper bound above .07 triggers an
implementation and derivation audit before any alternative screen proceeds. Passing this screen
would show only that one synthetic null run is not grossly inconsistent with alpha=.05; it cannot
prove anytime validity, cover other conditional nulls, or justify a SOTA claim. The theorem remains
the primary validity evidence.

## Result

Completed 2026-11-04 with seed base `2026110907`; output is in the ignored development artifact `outputs/sota_sprint/versioned_null_1000/records.jsonl` (7 policies × 1000 seeds). The version-indexed gate promoted 26/1000 times (2.6%; Wilson 95% CI [1.78%, 3.78%]), below both locked thresholds (.06 point rate and .07 upper bound). Mean query use was 199.22/200, maximum 200, and mean net cost was 810.22.

Decision: pass this implementation diagnostic and proceed to the separate chronological real-data development stream. This does not validate the theorem; the iid simulation also does not instantiate the required per-query conditional null with adaptive model fitting. Keep the candidate exploratory and retain the real-stream and proof audits as gating requirements.

For reference, RMM promoted 11/1000 (1.1%, Wilson [0.62%, 1.96%]); the front-loaded gate 2/1000 (0.2%, [0.05%, 0.73%]); Choe-Ramdas EB 4/1000 (0.4%, [0.16%, 1.02%]); A5b 5/1000 (0.5%, [0.21%, 1.17%]); never-switch 0/1000 ([0%, 0.38%]). These are descriptive simulation comparisons under the same generator, not calibrated guarantees for those methods.
