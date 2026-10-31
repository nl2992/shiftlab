# Monitoring-to-decision value: master protocol

**Branch:** `research/monitoring-to-decision-value-2026-10-30` (worktree
`ICML/branch-research-monitoring-to-decision-value-2026-10-30`), base commit
`ce9d3ca5381e4fcda658ebd7717fc4b223d295f1` (main, 2026-10-30).
**Status:** development protocol v1, written before any experiment in this programme was run.
Confirmation seeds, thresholds and comparison sets are frozen separately in
`05_EXPERIMENTAL_CONTRACT.md` before any confirmation run.

## Research question

When does an improvement in a statistical monitor (higher power, lower delay, fewer labels at a
matched false-alarm constraint) translate into lower net deployment cost, when is it irrelevant,
and when does it make deployment worse? Primary outcome: **net deployment cost**. Detection
metrics are explanatory secondary outcomes.

## Isolation and resource rules

- Failure Atlas (`scripts/run_failure_atlas_loop.py`, `outputs/failure_atlas_v1*` in the main
  checkout) is running with 12 workers at the time of writing. This programme does not read its
  reserved data, touch its outputs, or change its code. Our compute ceiling is **4 worker
  processes** and **30 CPU-minutes per experiment** unless this file is amended.
- Other worktrees are read-only sources. Reused code is copied or imported with branch, commit SHA
  and file path recorded.
- Outputs go to `outputs/decision_value/` (gitignored). Only small summaries/manifests are
  committed.

## Formal setting (summary; full statement in `04_THEORY.md`)

Time `t = 1..T`. Actions `a ∈ {0 (incumbent), 1 (challenger/fallback)}`; per-step losses
`ℓ_t(a)`. Deployed action `a_t` is `F_{t-1}`-measurable. Paired advantage
`Δ_t = E[ℓ_t(0) − ℓ_t(1)]` (evaluator-only in synthetic settings).

Net cost `C_T(P) = Σ_t ℓ_t(a_t) + c_q N_q + c_s N_s`. In synthetic settings the primary cost uses
the Rao–Blackwellised form `Σ_t μ_t(a_t)` (unbiased because `a_t` is predictable and `ℓ_t` is
conditionally independent of the past given the evaluator state); realised cost is also reported.

Clocks recorded per event: event time, action time, query time, label-release time
(`= query time + d` with declared delay `d`), monitor-update time, alarm time, switch time.
A monitor at time `t` sees only labels with release time `≤ t-1` (strictly before the action
decision at `t`). Labels released simultaneously are processed in event-time order.

Observability settings, always labelled separately:
- **A** fully observed prediction replay (a label reveals both models' losses);
- **B** logged-bandit (only the chosen action's outcome; requires OPE with checked overlap);
- **C** synthetic with evaluator-only potential outcomes.

## Operating policy decomposition

`P = (acquisition q, monitor m, controller π)`. Experiment types:
- **I fixed controller:** monitors swapped under an identical controller and identical acquisition
  (common random numbers, identical queried events).
- **II tuned controller:** each monitor gets a controller tuned on an equal development budget.
- **III simple references:** never switch, always challenger, fixed-calendar batch selection,
  fixed-sample batch test, static economic threshold.
- **IV factorial ablation:** one component exchanged at a time.

Oracles (labelled as such, never deployable): best static hindsight, best dynamic hindsight (DP
over realised or expected losses with switching cost), and a regime-aware clairvoyant (S2).

## Matched monitoring comparison

"Monitor A is better than B" is only claimed for a declared metric at a matched constraint:
thresholds are calibrated on a declared null generator (separate calibration seeds) to equal
probability of any alarm over the horizon, `α = 0.05`. Nominal (anytime-valid) versions of
e-process monitors are reported separately and never compared as if they tested the same null.

Monitor targets are kept distinct:
- **incumbent-risk** target: `E[ℓ_t(0)] > r_0` (needs a reference risk `r_0`, estimated on a
  calibration window — never the evaluator's true value);
- **paired-advantage** target: `E[ℓ_t(0) − ℓ_t(1)] > 0` (decision-relevant for switching).

## Registered hypotheses (development order)

H1 ranking reversal, H2 actionability determines conversion, H3 small headroom ⇒ negligible
monitoring value; then H4 alarm validity ≠ economic usefulness, H5 resource efficiency, H6 simple
methods competitive. Each experiment names one mechanism.

## Registered mechanisms for H1 (to test, not assumed)

1. **Metric mismatch:** power-by-horizon vs. delay relative to a transient opportunity.
2. **Target mismatch:** incumbent-risk alarms when the fallback degrades too (common shock).
3. **Controller interaction:** hold length vs. regime persistence.
4. **False-alarm asymmetry:** matched nominal level but different realised false-switch costs
   under dependence.

## Synthetic families (development seeds 0..9999; confirmation seeds ≥ 7,000,000, untouched)

- **S1 transient advantage:** incumbent degrades by `Δ` on `[τ, τ+L)`; challenger worse than
  incumbent by `δ` outside the window. Factors `L, Δ, d, c_s, q`.
- **S2 persistent dependent regimes:** two-state Markov chain with stay-probability `ρ`; fallback
  useful / useless / harmful in the bad state.
- **S3 action-set heterogeneity:** strong, weak, reversing, none, and common-shock alternatives.

These are new generators for a different endpoint (decision value), not Failure Atlas cells.

## Statistical plan (development)

Paired bootstrap over independent episodes (10,000 resamples), 95% percentile intervals. A
reversal requires: detection-metric advantage ≥ 0.05 (power) or ≥ 10% (delay) with CI excluding
zero **and** a cost disadvantage ≥ the minimum meaningful effect (MME, default 1% of never-switch
cost per cell, declared per task) with CI excluding zero. Correlated grid cells are not counted as
independent replications; inversion frequencies are reported per family. Holm correction across
the frozen confirmatory comparison set.

## Gates

G1–G9 follow the programme brief; decisions and their evidence are appended to
`RESEARCH_LEDGER.md`.
