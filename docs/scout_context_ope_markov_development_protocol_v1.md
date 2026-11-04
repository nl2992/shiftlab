# Source-matched OPE LIL comparator on the exact-floor Markov scout

**Frozen:** 2026-11-04 before execution. **Status:** exploratory development; no confirmatory inference.

## Question and estimand

Does the contextual scout's fixed-after-scout mapping retain a utility advantage when its certification gate is replaced with a source-matched doubly robust OPE LIL confidence sequence? At each certification event, encode query/skip as a two-action logging policy with known uniform propensity `q=b`, target policy always query, and query reward equal to normalized selected-policy net gain including the amortized switching charge only in selected contexts. Reward lies in `[0,1]`; lower-CS crossing of `1/2` is positive average conditional net value. The estimand is average conditional certification-period value. Evaluator-known postpromotion utility is reported separately and is not covered by that CS absent a transport assumption.

## Frozen design

- 60 matched seed clusters: `21,800,000–21,800,059`; verified disjoint from development (`21,510,000–21,510,059`), null calibration (`21,600,000–21,600,999`), and confirmation (`21,700,000–21,700,599`).
- Full 108-cell Markov grid: prevalence `{0.10,0.50,0.90}` × persistence `{0,0.50,0.80}` × signal `{0,0.05,0.10}` × proxy error `{0,0.25}` × budget `{0.20,0.40}`.
- OPE comparator is evaluated on the exact-floor eventwise contextual scout, using exactly its scout-selected context mapping, certification queries, queried outcomes, and cap-limited prefix. Fixed-mixture output from that same row is the matched incumbent gate. Rank and nested-volume rows remain in the output as context for utility, not as additional OPE-selected policies.
- OPE construction: `pi=(0,1)` over skip/query; `h_t=(1-q_t,q_t)`; reward prediction `(0,0.5)`; DR truncation `k=1`; alpha `0.05`; Proposition 3 LIL CS; crossing threshold `0.5`. Promotion requires a nonempty selected mapping and a lower-CS crossing.
- Report gate promotion rates and paired agreement, crossing event and final CS width, label use and hard-cap integrity, plus expected and realized postpromotion net gain under each gate. Report null-cell rates as exploratory diagnostics only; this run does not calibrate OPE null error.
- No tuning or confirmation on these seeds. Any positive result must be followed by independent calibration for the exact OPE mapping and a fresh disjoint confirmation. No novelty/SOTA claim follows from this run.

## Reproduction

```powershell
uv run shiftlab-dive-scout-markov-development `
  --seeds 60 --seed-offset 21800000 --n 3200 --d 16 --device cpu --workers 6 `
  --exact-uniform-propensity-floor `
  --protocol docs/scout_context_ope_markov_development_protocol_v1.md `
  --output outputs/scout_context_ope_markov_development_v1
```
