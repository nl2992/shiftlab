# Timans et al. unknown-shift risk monitor: matched paired-cost comparison

**Status:** frozen before execution, 2026-10-26. This is a source-pinned development comparison of a directly task-compatible Q1 monitor. It is not an independent final real-data confirmation or a novelty claim.

## Research question

On the registered ShiftLab synthetic paired-cost streams, how does the default predictable `approx_grapa` betting rule from Timans, Verma, Nalisnick, and Naesseth compare with ShiftLab's fixed-stake mixture when both test the same eventwise conditional-mean harm null, receive the same outcomes, and use the same alarm threshold?

This comparison directly addresses whether ShiftLab's existing Q1 monitor provides a detection advantage over an established risk-violation monitor on a compatible score. Both methods test the same null after rescaling the paired excess cost to a bounded loss in `[0,1]`; their betting-rate strategies differ.

## Source and exact adaptation

- Primary paper: [On Continuous Monitoring of Risk Violations under Unknown Shift](https://proceedings.mlr.press/v286/timans25a.html), UAI 2025, PMLR 286, 4204–4226.
- Official code: [alextimans/risk-monitor](https://github.com/alextimans/risk-monitor).
- Source commit recorded before execution: `4bf66a37dc2a3d7959bb9dcb325b61e8bb3c28e5`.
- The repository is AGPL-3.0. This study independently implements the published scalar betting formulas in ShiftLab and does not copy or vendor the upstream source. The exact source files used for formula verification are hash-recorded in the manifest.
- Primary comparator: `EProcessTracker` with the official default `approx_grapa` rule (`c=0.5`) and burn-in of 100 observations. A second, prespecified paper-code option uses the exact grid-search `grapa` rule with grid `{0.1, 0.2, ..., 1.9}`. These are two betting-rate strategies under the same published bounded-risk test, not separate estimands.
- ShiftLab comparator: `BoundedMeanEProcess` with its frozen five-stake equal mixture `(0.05, 0.1, 0.2, 0.4, 0.8)`.

## Estimand and validity contract

For each stream, let `d_t` be the deployed policy's realized cost minus the declared reference policy's realized cost, and let `m=0.10` be the registered tolerated excess cost. ShiftLab monitors `x_t=d_t-m` with support `[-b,b]`, where `b=max(fn_cost, fp_cost)+m` is known before outcomes. For the paper's `[0,1]` risk score use

`z_t = (x_t + b) / (2b)` and `epsilon = 1/2`.

Then `E[z_t | F_{t-1}] <= epsilon` is exactly `E[d_t-m | F_{t-1}] <= 0`. Every monitor sees the same `z_t`, bound, one fixed deployed/reference policy pair, and full immediate feedback. Evaluator-only expected costs and true change parameters are used only to label scenarios and calculate onset; they are not monitor inputs.

The experiment uses one prespecified policy score per stream, so it does not invoke the paper's separate multiple-threshold family. The paper's bound is time-uniform under its conditional risk null, predictable bets, bounded `[0,1]` scores, and observed labels. The study does not claim validity when outcomes are delayed, selectively missing, or used to choose the policy adaptively after monitoring begins.

## Frozen design

- Synthetic generator and feature dimension: existing `decision_harm_experiment` / `risk_proxy_monitor_grid`, `n=2,400`, `d=16`.
- Monitor starts at event 800; 1,600 monitor events are processed in every stream.
- Null controls: `stationary` and `benign_nuisance`, 1,000 fresh seed IDs per scenario.
- Alternatives: `boundary_local_harm`, `residual_variance`, `recurring_regimes`, and `harmful_adaptation`, 300 fresh seed IDs per scenario.
- Seed block: `1,500,000,000` onward, with disjoint contiguous blocks assigned to null and alternative cells. The runner must audit manifests for overlap before generation.
- Generator device: CUDA when available; the current NVIDIA RTX 4060 is the selected execution device. Scalar monitor updates use CPU float64 for deterministic formula calculations.
- Significance level: `alpha=0.05`; crossing occurs at `E_t >= 1/alpha`.
- No method parameters are tuned on these streams. The `approx_grapa` burn-in and betting formula and `grapa` grid come from the pinned official code; the fixed-mixture configuration comes from the existing ShiftLab implementation.

## Outcomes and stopping rule

Report all cells separately. Primary measurements are false escalations in both null controls; post-onset detection rate and delay in each alternative; pre-onset crossings; maximum log e-value; and paired per-seed detection differences. Also record actual monitor events and bounds. Use one-sided exact binomial upper bounds for the six method-by-null cells with Bonferroni familywise 95% coverage. For the 12 method-pair-by-alternative comparisons, report paired detection differences with percentile seed-bootstrap 95% intervals (10,000 resamples, fixed RNG seed `20261026`) and two-sided exact McNemar p-values adjusted by Holm. Alternative marginal intervals are descriptive and familywise-adjusted across all method-by-alternative cells. No composite cross-method score or arbitrary weighted winner is allowed.

Stop if source hashes/commit mismatch, the stream score leaves `[0,1]`, any event is skipped, a method uses current/future outcomes to choose its bet, or the max label/resource contract differs. No additional tuning or extended runs are allowed under this protocol.

## Validation requirements

1. Unit tests verify the score transformation, bet predictability, factor nonnegativity, boundary behavior, and alpha-crossing rule.
2. A deterministic short-stream check compares both independently implemented bet schedules and wealth paths with the official code at the pinned commit, to floating-point tolerance.
3. An independent verifier checks seed/scenario completeness, row counts, per-stream event counts, null confidence bounds, output hashes, protocol hash, and source hashes.
4. The run is descriptive component benchmarking on controlled synthetic data only. It does not establish a real-data advantage or support a new-method claim.
