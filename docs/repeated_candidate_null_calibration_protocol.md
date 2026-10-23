# Repeated-candidate nondegenerate null calibration protocol

**Protocol lock:** 2026-10-23, before the 2,000-stream evaluation run. This is a
calibration and power study of established monitors, not a method-selection or
novelty experiment. The existing exact-copy family and single-candidate null runs
are not the primary evidence for this protocol.

## Research question

How do familywise false-promotion rates and power change with candidate-family
size, label budget, and a conservative global support bound when all candidate
tests share the same randomly queried outcomes?

Primary safety estimand: familywise crossing probability in the nondegenerate
aggregate-zero scenario. Primary power estimand: familywise crossing probability in
the aggregate-positive scenario. The aggregate-negative scenario is a strict-null
control. Report exact pointwise Wilson intervals for each cell and paired-stream
differences against the fixed-mixture baseline. Do not select a monitor from these
evaluation results; no intervals are adjusted for the grid.

## Frozen design

- 2,000 independent streams, horizon 1,000 events, experiment seed `26102026`,
  alpha `0.05`.
- Candidate counts: 1, 5, and 13 distinct, frozen deterministic policies. Each
  flips the incumbent action on half the 32 balanced feature contexts. Across the
  flipped contexts, half have incumbent action 0 and half action 1.
- Query probabilities and hard caps: constant probabilities/rates 0.10, 0.20,
  and 0.40; stop before the next event once `floor(rate × horizon)` labels have
  been queried. Query randomization is independent of context and outcome.
- Support bounds: `M × κ/q`, where `M=5` is the maximum absolute paired cost
  contrast, `q` is the registered query probability, and `κ ∈ {1, 1.5, 2}`.
  Every registered bound is valid; no underbounded process is tested.
- Six monitors: fixed-stake mixture at candidate alpha, the mixture at candidate
  alpha/2, predictable plug-in Kelly, PM-EB, full-alpha one-sided positive
  betting, and the half-weighted hedged positive branch at candidate alpha/2.
- Equal Bonferroni allocation assigns candidate level `0.05/C`, fixed before the
  streams. All candidate tests share the same labels and differ only in the frozen
  policy action pattern. Common random numbers are used across candidate counts,
  query rates, bounds, and DGPs.
- Synthetic DGP outcome probabilities by incumbent action:
  - `aggregate_zero`: `P(Y=1|a_inc=1)=0.10`, `P(Y=1|a_inc=0)=0.10`.
  - `aggregate_positive`: `0.06` and `0.14`, respectively.
  - `aggregate_negative`: `0.14` and `0.06`, respectively.

With false-negative cost 5 and false-positive cost 1, each candidate's true mean
gain is `1.5 × (p0 − p1)`: exactly 0, +0.12, or −0.12 cost units per event. Under
the zero-mean DGP, eventwise candidate gains are nonzero on half the contexts and
have balanced conditional means +0.4 and −0.4 on those contexts. Thus the null has
nonzero paired-cost variance, unlike the exact-copy diagnostic. The gate uses a
global bound and constant query probability; it does not normalize by, or choose a
stake from, the current context. Its target is the history-conditional average
gain, not a pointwise conditional-on-context null.

## Statistical scope and validity conditions

Each fixed-stake process is a nonnegative supermartingale under its bounded
history-conditional mean null. A predictable stake in `[0,1]` preserves that
property for Kelly and one-sided positive betting. PM-EB uses the published
predictable empirical-Bernstein process. Candidate alpha levels sum to 0.05, so a
union bound controls familywise crossing for the frozen finite family. Inflating
the correct support bound preserves validity and tests its power cost.

This benchmark assumes independent contexts/outcomes over time, immediate labels,
fixed candidate policies, a query coin independent of the current context and
outcome, correct cost bounds, and no action-dependent outcome process. The
gate's betting stake and stopping logic use only its accumulated evidence and
query count; current context-specific evidence is intentionally excluded. The
Monte Carlo rates diagnose code and finite-sample behavior; they do not prove the
supermartingale guarantees.

## Reproduction

```powershell
uv run python scripts/calibrate_repeated_candidate_nulls.py `
  --streams 2000 --horizon 1000 --seed 26102026 --device cuda `
  --output outputs/repeated_candidate_null_calibration_2000
```

Use CUDA for generation and monitor-state updates. The manifest records the
resolved environment, protocol, artifacts, and SHA-256 hashes. A CPU smoke run is
for implementation checks only and is not part of the evaluation block.
