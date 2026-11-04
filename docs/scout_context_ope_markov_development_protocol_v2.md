# Source-matched OPE LIL comparator with validation DR prediction

**Frozen:** 2026-11-04 before execution. **Status:** exploratory development only. This protocol refines the constant-predictor comparator after its first disjoint screen reported zero OPE promotions; the first screen is retained as negative efficiency evidence and is not used for parameter tuning.

## Question and estimand

Does the contextual scout's fixed-after-scout mapping retain a utility advantage when certification uses the source-matched doubly robust OPE LIL confidence sequence with a predictable validation-trained outcome model? Each eligible certification event is a two-action contextual-bandit record: query/skip logging probabilities `h_t=(1-q_t,q_t)`, target `pi=(0,1)` always queries, and bounded query reward equals normalized per-event net decision gain including the amortized switching charge only where a candidate was selected. The target value above `1/2` is positive average conditional net value. Future utility remains an evaluator-known outcome, not the CS estimand.

## Frozen design

- 60 matched seed clusters `21,900,000–21,900,059`, disjoint from the prior development, calibration, confirmation, and first OPE comparator blocks.
- Full 108-cell Markov grid: prevalence `{0.10,0.50,0.90}` × persistence `{0,0.50,0.80}` × signal `{0,0.05,0.10}` × proxy error `{0,0.25}` × budget `{0.20,0.40}`.
- Use the exact-floor eventwise scout mapping, query uniforms, queried outcomes, and cap-limited prefix. Compare the OPE LIL gate with the fixed-mixture gate on the same stream.
- Query reward normalization scale is `max(FN,FP)+switching_cost/deployment_horizon`. The predictor for the query action is the selected candidate's mean net gain on the fully labeled validation slice within each context, normalized by this scale and clipped to `[0,1]`; incumbent fallback predicts `1/2`. Skip-action prediction is zero. All predictions and selected mappings are fixed before certification outcomes are observed.
- DR truncation `k=1`, alpha `0.05`, source Proposition 3 LIL boundary, promotion threshold `1/2`. No predictor or truncation tuning on this block.
- Report promotion rates, paired agreement, crossing time, final lower bound and interval width, labels, cap integrity, and evaluator-known expected/realized future net utility under each gate. Zero-signal rates are diagnostic only and do not calibrate null error.
- This is a development comparison only. Any further change requires another fresh block. A positive method claim requires independent null calibration, confirmation, transport justification, and aligned real/deployment validation.

## Reproduction

```powershell
uv run shiftlab-dive-scout-markov-development `
  --seeds 60 --seed-offset 21900000 --n 3200 --d 16 --device cpu --workers 6 `
  --exact-uniform-propensity-floor `
  --protocol docs/scout_context_ope_markov_development_protocol_v2.md `
  --output outputs/scout_context_ope_markov_development_v2
```
