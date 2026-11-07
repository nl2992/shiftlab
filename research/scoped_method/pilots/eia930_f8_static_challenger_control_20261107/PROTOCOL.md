# EIA-930 F8 fixed-challenger control

**Status:** diagnostic baseline audit. The outcome-blind full panel omitted the direct
`always-deploy challenger` control. This addendum evaluates that simple fixed policy on the same
development model streams and episodes. It is not a new-method experiment and will not be presented
as prospective confirmation.

## Frozen control definition

Use the exact 11 BAs, 2021-trained predictions, 2022–2023 episodes, and 81 contiguous 2,000-hour
blocks in the completed F8 replay. Reconstruct the model pair and require exact match to the
committed profile artifact. For each episode compare:

1. `fixed_incumbent`: always use prediction column 0; zero labels, zero switches.
2. `fixed_challenger`: always use prediction column 1; zero labels; charge exactly one switch cost
   of 5 at episode start to represent precommitting to the challenger.
3. `CAMS`: use the episode-level mean over the five matched policy seeds in the completed replay.

Use the same error+label+switch cost decomposition; fixed controls have no label cost. Compare
fixed challenger minus CAMS by BA with paired episode bootstrap intervals and an equal-BA
hierarchical interval. Report all BAs, no post-hoc subset. The direct challenger is a feasible
fixed policy on these data because it uses only its current prediction; the choice of model 1 is a
fixed policy assumption, not a label-informed online decision. It is not a fair substitute for a
prospective validation-based selector and does not constitute a novel algorithm.

## Interpretation boundary

If the direct control beats CAMS on this development period, that diagnoses that the online
selection layer did not pay for itself on these already-selected F8-like BAs. It does not show that
the choice of challenger can be made prospectively, and it does not establish transfer. Any claim
that model 1 can be selected before deployment requires a separate chronological train/validation
selection rule, identical training-time information for comparators, and untouched 2024+ outcomes.
No 2024+ data are opened here. EIA values remain revised, feedback is simulated, and one provider
supplies all BAs.

## Reproduction

```bash
uv run python scripts/sota_sprint/eia930/evaluate_static_f8_controls.py
uv run python research/scoped_method/pilots/eia930_f8_static_challenger_control_20261107/analyze.py
```
