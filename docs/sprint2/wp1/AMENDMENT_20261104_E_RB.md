# WP1 post-development E_rb reversal follow-up (2026-11-04)

This amendment is registered before the run. It is a post-development sensitivity: the existing
reversal results and candidate-selection history are known, so it is not an untouched confirmatory
test and cannot establish a prospective general guarantee.

## Frozen run

- Regimes: `F3_reversal_800`, `W_reversal_700`, `S_reversal_400` (two previously registered
  reversal specifications plus the WP1 reversal regime).
- Paired candidates: `E_rb:gated_deployment`, `E_rb:discern_style`,
  `E_rb:SMCS+retain-incumbent`, `E_rb:gated_adaptive_range`; matched RMM policies with the same
  four host names; `CONTROL_never_switch` for context.
- 100 seeds per regime, seed base `2026110811`, alpha .05, 4 workers. This seed base is reserved
  for this run and is separate from the development and registered WP1 seed bases.
- Unit of pairing: regime x seed; all policies replay the same generated stream with private policy
  randomness.
- Primary estimand: for each seed, average over the three regimes and four matched hosts of
  `J(E_rb:<host>) - J(rmm:<host>+RMM)`, where `J=net` from the runner. Summarize the 100 seed-level
  values with their mean and a two-sided 95% t interval. A result is directionally supportive only
  if mean < 0 and the interval upper bound < 0.
- Secondary/exploratory: the 12 host-by-regime paired contrasts and rollback/promotion counts;
  report unadjusted intervals and label them exploratory.
- No exclusions or stopping based on interim results. Preserve the runner manifest and raw records.

Reproduction command:

```sh
uv run python scripts/sota_sprint/screen.py --regimes F3_reversal_800,W_reversal_700,S_reversal_400 --policies E_rb:gated_deployment,E_rb:discern_style,E_rb:SMCS+retain-incumbent,E_rb:gated_adaptive_range,rmm:gated_deployment+RMM,rmm:discern_style+RMM,rmm:SMCS+retain-incumbent+RMM,rmm:gated_adaptive_range+RMM,CONTROL_never_switch --seeds 100 --seed-base 2026110811 --workers 4 --alpha 0.05 --out outputs/sprint2/round5/wp1_erb_reversal_postdev100
```
