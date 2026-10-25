# Eventwise-scout null calibration under persistent contexts

**Status:** frozen 2026-10-25 before execution. This calibration follows the exploratory
eventwise Markov development screen. It evaluates false promotion for the exact eventwise scout
under the registered Markov-context family; it does not establish power or positive utility.

## Null and scope

The learner-visible context follows a stationary two-state Markov chain with stationary prevalence
`p ∈ {0.10, 0.50, 0.90}` and persistence `rho ∈ {0, 0.50, 0.80}`. Independent proxy noise corrupts
the context feature at rate `e ∈ {0, 0.25}`. At every target event and in either latent context,
the Bernoulli outcome probability is exactly the FN/FP decision threshold `1/6`. Therefore every
fixed candidate has zero gross conditional expected decision gain event by event; the registered
switching cost is 0.05, so net expected gain is nonpositive. This conditional null remains true
despite serial dependence in the observable context process.

The tested procedure is the frozen eventwise-propensity-bound context scout, with the same fixed
split, candidate family, selection and certification stages, alpha 0.05, uniform randomized query
process, direct-IPW estimator, switching cost, and 20%/40% hard label caps as the Markov development
screen. No parameter is tuned on these calibration streams.

## Frozen design and gate

- 1,000 independent streams per cell, seed block 20300000–20300999. The block is disjoint from
  prior recorded experiment seeds and the Markov development block 20273000–20273059.
- 36 cells: three stationary context prevalences × three persistence values × two proxy-error
  rates × two label caps. Every seed is reused across cells for pairing; cellwise streams remain
  independent across seed IDs.
- Use simultaneous one-sided exact Clopper–Pearson upper limits with familywise alpha 0.05 and
  per-cell alpha `0.05/36`. A cell passes only with at least 1,000 streams, no cap violations, all
  evaluator-defined null flags true, positive query support, and an upper limit at most 0.05. The
  full calibration passes only if every cell passes.
- Save every stream-level eventwise result, cell counts and limits, evaluator-null and cap audit,
  source and artifact SHA-256 hashes, software/GPU environment, and the protocol hash. A smoke run
  with fewer than 1,000 seeds is explicitly `smoke_only_not_calibration`.

This gate supports only false-promotion control for the registered conditional-mean null, Markov
context family, uniform-query process, immediate feedback, split, and candidate policy. It does not
cover delayed/selective labels, outcome-dependent query selection, adaptive candidate families,
nonstationary prevalence, or real-world utility. If any cell fails, do not confirm the current
Markov positive-signal result; retain the failure and revise only in a new development cycle.
No figure is planned; use PaperBanana for any later visual.

## Reproduction

```powershell
uv run shiftlab-dive-scout-markov-eventwise-calibration `
  --seeds 1000 --seed-offset 20300000 --n 3200 --d 16 --device cuda --workers 6 `
  --protocol docs/scout_context_policy_eventwise_markov_null_protocol.md `
  --output outputs/scout_context_policy_eventwise_markov_eventwise_null_1000
```
