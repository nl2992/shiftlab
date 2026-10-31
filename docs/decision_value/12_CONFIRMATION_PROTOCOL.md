# Frozen confirmation protocol (v1)

**Written:** 2026-10-31, before any confirmation seed (≥ 7,000,000) or reserved real window was
used. This file, the selected-config JSON and the scripts are committed and hashed before
execution; the confirmation script refuses to run if the hashes differ. Statistical design
reviewed by Agent F (development analysis, `06`) and Agent G (`07`) — same-model self-review, not
independent.

## Scope after development

Development established (`11`, section 8) that the value of tuned sequential monitoring over the best
tuned simple policy is **conditional**: zero where a static policy is near-optimal (symmetric
regimes, persistently better challenger), and about 1% of cost (6.5–9.4 units, MME 6.4–7.1) where
bad states are rare and persistent and label delay is short. Confirmation tests that conditional
pattern; it does not test an unconditional "monitors win" or "monitors lose" claim.

## Part S — synthetic (Setting C), asymmetric regimes

**Cells.** The 12 useful-fallback asymmetric S2 cells of `11` §8 (mean bad-run B ∈ {100, 400, 1000},
π_b ∈ {0.1, 0.25}, d ∈ {0, 50}; Δ=0.15, δ=0.05, c_s=2, q=0.2, T=3000) plus the useless-fallback
control (B=400, π_b=0.1, d=0).

**Step 0 (development, before freezing).** Development flagged that the simple family stopped at
its margin boundary (m=0.1). Re-tune the simple family only, on the same development tuning seeds
(base 300000, n=500), with calendar margins and static margins extended to
{0, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3}. The monitor selection from run
`type2_asym_20261031T021545Z` is kept. Per cell, write the selected monitor system and the selected
simple policy to `docs/decision_value/manifests/confirmation_selected_configs.json`, then commit.
No confirmation seed is touched in Step 0.

**Execution.** Confirmation seeds `7_000_000 + 10_000·cell_index`, n = 2000 per cell, evaluated
once for the frozen configs only. Thresholds are recalibrated with the calibration seeds already used
in development (5,000,000+), because calibration is part of the frozen procedure.

**Primary endpoints** (diff = cost(simple) − cost(monitor); positive favours the monitor):
- **CF-S1 (where monitoring should pay).** The mean diff over the 4 cells with d=0 and
  B ∈ {400, 1000}. Pass if the one-sided 95% paired-bootstrap lower bound is > 0 **and** the point
  estimate is ≥ the mean MME of those cells (MME = 1% of never-switch cost).
- **CF-S2 (delay erosion).** The mean over the 6 (B, π_b) pairs of [diff(d=0) − diff(d=50)]. Pass if
  the one-sided 95% lower bound is > 0.
- **CF-S3 (negative control).** In the useless-fallback cell, the monitor system's value vs
  never-switch is ≤ MME (two-sided 95% CI upper bound ≤ MME).

Family-wise: CF-S1 and CF-S2 are tested with Holm at α=0.05; CF-S3 is a validity check, and if it
fails Part S is reported as invalid. Secondary results (reported, not tested): the per-cell diffs
with Holm across 12 cells, headroom captured, N_s, and selected α.

**Bootstrap.** Over episodes, 10,000 resamples, paired by seed; cells are independent seed blocks.

## Part R — real data (Setting A), one shot

Adopted verbatim from `10_REAL_DATA_DEV_RESULTS.md` §6, items 1–10, including the primary
endpoint (OPSD TSO-vs-sliding, CUSUM + Hold(7), c_s=5, d=1, q=1, minus the better of never and
calendar28), MME, block bootstrap, controls (Monash 2014, Binance 2026-01..09) and the
pass/fail rule.

Disclosed risks:
- The primary monitor/controller was chosen because it produced the only positive dev cell
  (selection risk).
- The OPSD 2020 window contains the public spring-2020 demand disturbance.
- There is one series per pair.
- Delays and costs are imposed.

The reserved windows are opened once, in a single run.

## Interpretation rules (fixed now)

- If CF-S1 and CF-S2 both pass: "conditional value of monitoring" is confirmed in this synthetic
  family (Setting C only).
- If CF-S1 fails: the development wins are treated as not confirmed. They are not re-tested on new
  confirmation seeds.
- If Part R fails its pass rule, the result is reported as negative or uninformative real-data
  evidence. That does not contradict Part S, because the settings differ.
- No re-run, re-selection or endpoint change after execution. Failures are appended to the ledger.
