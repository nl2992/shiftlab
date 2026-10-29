# G1 analytic growth pre-screen: results

**Gate G1: FAIL.** Stop rule **S2** fires for the registered anchored, gated monitor (ADG)
design. This is a learner-side analytic calculation: no monitor was run, and no query, outcome, or
monitor-window event was drawn. It is a design-stage result, not a detection, calibration, or
validity result. See [the protocol](anchored_gated_harm_monitor_development_protocol.md),
Section 6.1. That section was written before any pre-screen output existed, together with the
pre-run prediction that the primary cell would tie.

## Primary result

The primary cell is `boundary_local_harm`, label-dollar budget `r = 0.20`, working alternative
`mu = 0.277`. Eighteen of 20 seeds are feasible; seeds 58000002 and 58000004 need `eta > 1` and are
excluded, as registered.

| Arm | Mean `G*` (per event) | Bound | Expected spend / target |
|---|---:|---:|---:|
| A1 `ppi_symmetric` (`q = 0.20`) | 0.003673 | 45.9 | 1.00 |
| A1 at the diagnostic bound | 0.0020 | 96.9 | 1.00 |
| A2 `ppe_fixed_stake` | 0.0040 | 45.9 | 1.00 |
| A4 `xu_active` | 0.0020 | 96.9 | 1.00 |
| A10 `ungated_gamma0` | 0.0049 | 5.1 | 1.00 |
| A3 `discern_gated` | **0.027630** | 5.1 | 0.45 |
| A8 `adg_gamma_mix` | **0.027630** | 5.1 | 0.45 |

The criterion `G*(A8) >= 1.5 × max(G*(A1), G*(A3))` gives a ratio of **1.000**.

The cause is the one predicted before the run. The two policies disagree on only 8.9% of validation
events (range 6.5–11.5% across seeds), and always with deployed 0 / reference 1. So at a 20% budget
every gated arm labels every disagreement (`q_D = 1`) while spending 45% of the budget. With
`q_D = 1`, the anchor has no effect: A3, A7, every A8 component, and the gated symmetric arm
produce identical increments. **The entire predicted gain over the repository's ungated monitors
(7.5×, median over seeds) comes from disagreement gating, which is DISCERN's contribution.**

## Secondary budget cells (descriptive, declared before the run)

| Budget `r` | `q_D` | A8 / A3 (ratio of means, `mu = 0.277`) | A3 / A1 (median) | Best `gamma` component (seeds) |
|---:|---:|---:|---:|---|
| 0.02 | 0.23 | 1.23 | 17.9 | 0.5 (17), 0.25 (1) |
| 0.04 | 0.45 | 1.17 | 17.8 | 0.25 (14), 0.5 (4) |
| 0.06 | 0.68 | 1.10 | 17.6 | 0.25 (10), 0 (7), 0.5 (1) |
| 0.10 | 0.99 | 1.00 | 15.7 | 0 (17), 0.25 (1) |
| 0.20 | 1.00 | 1.00 | 7.5 | ties (all equal) |

Across all budgets and all three alternatives (`mu ∈ {0.10, 0.178, 0.277}`), the anchor's gain over
DISCERN-style gating never exceeds **1.23×** as a ratio of seed means. The largest single-seed
ratio is 1.28×; no seed reaches 1.5×. The anchor helps only
when labels are scarce enough that `q_D < 1`.

At low budgets the pure boundary anchor (`gamma = 0`) is worse than intermediate anchors. Under the
working alternative, the unfavourable-outcome probability on disagreements rises from 0.35 (mean
natural value) to about 0.88. That raises the `gamma = 0` acquisition-variance penalty `1/(1-p)`
(Section 3.3 of the protocol), and the mixture's best component moves to `gamma ∈ {0.25, 0.5}`.
This is consistent with the derivation, but the trade-off is too small on this generator to support
a separate method.

## Integrity checks and corrections

- **Spend.** Every ungated arm matched the target expected label-dollar spend exactly. Gated arms
  spent at or below target.
- **Unbiasedness.** The expected increment equalled the working-law mean excess
  (maximum absolute difference `1.7e-16` across all feasible alternative rows).
- **No invalid factors.** Every arm's bound covered its reachable lower tail; the function raises
  otherwise.
- **Correction to the protocol's sanity check.** Section 6.1 said the `eta = 0` growth "must be
  nonpositive for every arm". That statement was wrong. `eta = 0` is the learner's natural
  pre-onset working law, not a null. Its mean excess across seeds was 0.0002 (SD 0.026, range
  −0.037 to 0.047), so it is positive in some streams. The correct check, by Jensen, is that growth
  is nonpositive wherever the mean excess is nonpositive. It held: 0 of 2,240 natural rows violate
  it. The label `null` was renamed `natural` before the final run, which is deterministic. No
  result changed.
- **Scenario sensitivity carries no information.** `stationary` and `boundary_local_harm` share
  identical pre-monitor slices for the same seed, so their rows are identical.
- **Stake cap.** The registered stake grid tops out at 0.8. Most capped arms chose that maximum
  (`share_stake_at_cap = 1`), so larger valid stakes could raise every capped arm's growth. That
  would favour the ungated and DISCERN-style arms as much as ADG. It does not affect the tie at
  `q_D = 1`.
- **Before the gate run,** one seed (seed 0, primary cell) was run as a code smoke test. It showed
  the predicted tie. The criterion and cells were already registered.

## Limits

- The working alternative is a proportional tilt of the learner's own classifier probabilities on
  disagreement events. It is not the generator's boundary-harm mechanism. Growth ignores proxy
  updating, delays, and budget exhaustion.
- The real-data pre-window part of G1 (EIA, Gas Sensor) was **not run**: no real-data adapters
  exist yet. Real policies may disagree more often. Even so, the synthetic secondary cells show at
  most a 1.23× anchor gain when `q_D < 1`.
- A9 (horizon-calibrated Shiryaev–Roberts e-detector for late onset) concerns onset handling, not
  per-event growth. G1 does not test it.

## Continue / pivot / stop

- **Stop:** the ADG algorithm branch, under S2. The anchor ingredient fails the registered 1.5×
  criterion at the primary cell and in every secondary cell. Do not tune the threshold, stakes, or
  alternative after seeing these numbers.
- **Carry forward to the benchmark/failure-analysis manuscript:**
  1. The repository's sparse-label monitors (A1 and its relatives) spend about 91% of their labels
     on events whose paired cost is known to be zero. A DISCERN-style gated comparator is predicted
     to give 5–18× higher log-growth at matched spend. Prior selective-label comparisons in this
     repository did not include that comparator, so their "sparse labels lose power" conclusion is
     partly an artefact of label waste. This should be verified empirically before it is written up.
  2. The late-onset e-detector is still a missing required baseline.
- **Follow-up drafted:** [gated versus ungated verification protocol](gated_vs_ungated_monitor_comparison_protocol.md)
  (not frozen, not run).
- **Pivot options (each needs a new, separately approved protocol):**
  - an empirical gated-versus-ungated monitor comparison on the existing development design;
  - a standalone Shiryaev–Roberts e-detector baseline study.

## Reproduction

The gate run used Git HEAD `42709d70840e2e72ac8abea27bac9eb4108ef797`, with the new source files
uncommitted. The manifest records the source and output SHA-256 values and the runtime (8.9 seconds
on CPU).

```powershell
uv run --no-sync python scripts/run_adg_growth_prescreen.py
uv run --no-sync pytest tests/test_adg_growth_prescreen.py -q
```

The manifest's protocol hash is for the protocol text as it stood at run time. After the run, a
status header and the sanity-check correction note were added to the protocol; nothing in
Section 6.1's registered criterion, cells, or arms changed.

Artifacts: [`outputs/adg_growth_prescreen_20/`](../outputs/adg_growth_prescreen_20/) (`stream_rows.csv`,
`summary.csv`, `ratios.csv`, `criterion.json`, `manifest.json`). When reading `stream_rows.csv`
with pandas, use `keep_default_na=False, na_values=[""]`.
