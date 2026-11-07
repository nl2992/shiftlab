# Track B mechanism diagnosis: why do certified deployment methods miss late improvement? (protocol, locked before run)

**Locked:** 2026-11-07, before any run under the seed base below. **Evidence status:**
descriptive mechanism diagnosis on synthetic development regimes. It is not confirmatory, and it
nominates no new method. Its purpose (strategy brief, section 9) is to separate four candidate
causes of late-change failure before any combinatorial search: (M1) budget exhausted before the
change, (M2) stale evidence (accumulation diluted by pre-change data), (M3) delayed labels,
(M4) feedback stops after an initial verdict.

## Contract and seeds

`bench.CONTRACT` (T=2000, c_q=.05, c_s=5, alpha=.05), budget varied as below. Seed base
`2026120701`, 100 paired seeds per regime cell; this base appears nowhere else in the repository.

## Regime grid (pre-change p=0.4, i.e. the challenger is worse; then it improves)

- Change time × budget: `F1_late_400`, `F1_late_800`, `F1_late_1200`, `S_late_1500` (post p
  0.68 / 0.70 / 0.75 / 0.75 as registered) at B in {100, 200, 400} (the `@B` suffix). 12 cells.
- Delay: `F1_late_800` at B=200 with delay 10 and 400 (registered delay is 100). 2 cells, built
  with `dataclasses.replace`, named `F1_late_800_d10`, `F1_late_800_d400`.

## Policies (fixed)

- Published-certificate hosts (mandatory track-B baselines): `gated_deployment`,
  `gated_adaptive_range`, `gated_adaptive_range+front` (front-loaded querying), `discern_style`,
  `SMCS+retain-incumbent`.
- RMM ablations on the gated host: `rmm:gated_deployment+RMM`, `+RMM_noacq` (no post-verdict
  acquisition), `+RMM_single` (one start: stale evidence), `+RMM_norestart` (host not restarted).
- Detector-only RMM pacing: `rmm:LRMD_k1` (uniform), `rmm:LRMD` (k=2), `rmm:LRMD_k3`,
  `rmm:LRMD_single`.
- Fidelity comparators: `two_sided_esr_label_clock`, `esr_rmmbets_fullalpha`,
  `han_arw_label_clock`, `shekhar_ramdas_rcs_t3_anyexcl`.
- Control: `CONTROL_never_switch`.

## Metrics per episode

Net cost J; promoted before the change (an error, since the challenger is worse then); detection
delay = first round at or after the change with the challenger deployed, minus the change time
(censored at T, reported as missed); labels bought before / after the change; whether any label
is bought after the change.

## Diagnostic contrasts (paired over seeds, 95% t intervals; descriptive, unadjusted)

- **M4 post-verdict stopping:** share of host episodes with zero labels after the change;
  J(gated+RMM_noacq) − J(gated+RMM) by change time.
- **M2 stale evidence:** J(gated+RMM_single) − J(gated+RMM); J(LRMD_single) − J(LRMD); detection
  delay of the single-start vs mixture vs every-label e-SR, by change time.
- **M1 budget exhaustion:** labels remaining at the change vs detection delay, across change time
  × budget; J(LRMD_k3) − J(LRMD_k1) by change time (does horizon-weighted pacing help more for
  late changes?); `gated_adaptive_range+front` vs `gated_adaptive_range`.
- **M3 delay:** detection delay and J for each policy at delay 10 / 100 / 400.
- **Track-B competitor check:** J(rmm:gated+RMM) − J(two_sided_esr_label_clock) and
  J(rmm:LRMD) − J(two_sided_esr_label_clock) per cell.

## What counts as an identified mechanism (stated now)

A mechanism is "supported as a driver" when its ablation contrast has a 95% interval excluding
zero in the harmful direction in at least two change-time cells at B=200, and the direction is
consistent with detection-delay differences. Otherwise it is "not resolved". Any mechanism
supported here only nominates a candidate for the later search; it does not establish novelty.

## Reproduce

```bash
uv run --extra drift python scripts/sota_fidelity/late_change_diagnosis.py run --out outputs/sota_fidelity/late_change_diagnosis --workers 9
uv run python scripts/sota_fidelity/late_change_diagnosis.py analyze --out outputs/sota_fidelity/late_change_diagnosis
```
