# Contextual scout: empirical-Bernstein OPE gate

**Frozen:** 2026-11-04 before the EB development run. **Status:** exploratory development only. This is a source-matched alternative to the already implemented DR-LIL comparator, not a new method claim.

## Research basis

Waudby-Smith et al., [*Anytime-valid off-policy inference for contextual bandits*](https://arxiv.org/abs/2210.10768), Theorem 2 gives an empirical-Bernstein confidence sequence (EB-CS) as well as the LIL-CS. The paper states that the EB boundary is often tighter empirically, while the LIL boundary has a stronger asymptotic LIL rate. Both address predictable logging, bounded rewards, time-varying conditional policy values, and arbitrary stopping. Section 3.1 also gives a direct policy-value-difference construction that can avoid a union-bound penalty.

The current scout audit already implements the paper's DR-LIL mapping but found no crossings in 6,480 Markov streams, including positive-signal cases. This does not establish that the EB-CS will be useful; it identifies a concrete, source-backed next comparator before leaving this research direction.

## Frozen comparison requirements

- Use 60 matched seeds `21,900,120–21,900,179`, fresh relative to both prior OPE blocks (`21,900,000–21,900,059` and `21,900,060–21,900,119`). Use the registered 108-cell Markov design, exact-uniform propensity floor, same scout-selected mapping, same certification query stream and hard-cap prefix.
- Reuse the bounded two-action DR encoding and validation-trained predictor from OPE protocol v2. Freeze truncation `k=1`, alpha `0.05`, query/skip logger, and net-gain threshold `1/2`.
- Implement the source EB mixture boundary directly on the DR pseudo-outcomes, retaining the paper's predictable lagged-mean variance process. Set `rho=0.17817019505784423` from the source tuning expression at `alpha=.05` and a design intrinsic-time target `V*=250`; this value is data-independent and frozen before this block. Use 48 vectorized bisection steps on `[0,1]` (root bracket width at most `2^-48`) and the regularized incomplete-gamma identity for positive arguments, with the source confluent hypergeometric expression for nonpositive arguments.
- Compare the EB-CS, existing DR-LIL-CS, and fixed-mixture monitor on every paired stream. Record false promotions in the registered zero-signal cells as diagnostics, positive-signal promotion rate, event of first crossing, final lower bound and interval width, label count, hard-cap integrity, and evaluator-known future net utility.
- Report certification-period value inference separately from future deployment utility. Any interpretation of the latter requires an explicit stability/transport assumption.

This remains exploratory. A favorable development result requires a separately frozen null calibration and an independent confirmation block. If EB closes the gap, close the scout algorithmic lead; if it does not, this does not establish SOTA. Neither result alone supports a novelty claim.

## Reproduction

```powershell
uv run shiftlab-dive-scout-markov-development `
  --seeds 60 --seed-offset 21900120 --n 3200 --d 16 --device cpu --workers 6 `
  --exact-uniform-propensity-floor `
  --protocol docs/scout_context_ope_empirical_bernstein_gate_2026-11-04.md `
  --output outputs/scout_context_ope_eb_markov_development_v1
```
