# Fair in-horizon F8 validation gate: frozen pilot protocol

**Status:** frozen before running outcome comparisons. This tests a conventional validation-selected
fixed challenger under a shared economic contract. It is not a novel-method proposal.

## Question

Does the previously favorable known fixed-challenger control retain practical advantage when the
candidate must use in-horizon labels to identify a challenger, and must pay the validation time,
incumbent loss, label cost, and switching cost?

## Frozen design

- Fresh paired synthetic streams: 50 seeds, base seed `2026110719`.
- Primary: `F8_rare_better`; adverse controls: `F0_null`, `F3_reversal_800`.
- Common `T=2000`, `B=200`, label price `0.05`, switch cost `5`, regime delay.
- Candidate baseline: query every model disagreement during events `[0,400)`, keep the incumbent
  deployed throughout validation, and make one decision at event `400 + delay`, after all validation
  labels have been released. Promote the pre-specified challenger only if (i) the one-sided 95%
  Clopper-Pearson lower bound for its correctness probability on queried disagreements exceeds
  `0.5`, and (ii) the projected remaining-horizon gain using the observed disagreement rate exceeds
  the switch cost. No labels are requested after the decision. The query costs, incumbent loss during
  validation, and switch cost are counted by the shared simulator.
- Comparators: `cams_adapter` (primary online selector from the prior registered F8 comparison),
  `SMCS+retain-incumbent`, `gated_deployment`, `CONTROL_never_switch`; `fixed_challenger` is retained
  only as an explicitly oracle-identity upper control, not an implementable comparator.
- Paired stream is identical across policies. Seeds are fresh relative to the prior 100-seed F8
  result. No outcomes are pooled across regimes.
- Primary endpoint: paired net-cost difference (candidate minus CAMS). Practical threshold is at
  least 5 cost units saved, with paired 95% bootstrap interval below zero. This is a bounded pilot,
  not independent confirmation or a method novelty test.
- Report net cost decomposition, labels, switches, promotion frequency/time, all adverse cells, and
  paired uncertainty. No real dataset or locked source is opened.

## Interpretation limits

The exact one-look binomial bound assumes iid queried disagreement signs, which is true by
construction only for the registered stationary F8 generator. The null and reversal cells are
adverse economic diagnostics; the bound is not claimed to protect under their nonstationarity or
after adaptive data collection. The synthetic task reveals both frozen model predictions, and the
challenger identity is pre-specified; it does not solve candidate search or model-training cost.

## Reproduction

```bash
uv run python scripts/failure_atlas_v2_flq/run_atlas_v2.py --kind synthetic --seeds 50 \
  --seed-base 2026110719 --regimes F8_rare_better,F0_null,F3_reversal_800 \
  --policies fair_validation_gate,cams_adapter,SMCS+retain-incumbent,gated_deployment,CONTROL_never_switch,fixed_challenger \
  --extra f8_fair_extra --workers 4 \
  --out research/scoped_method/pilots/f8_fair_gate_20261107/run
```
