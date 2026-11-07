# RPOQ S6: CRSP label-allocation headroom replay, protocol (pre-registered)

**Branch:** `research/rpoq-s1-fatal-flaw-audit`. **Date:** 2026-10-29.

| Label | Value |
|---|---|
| Work type | Real-data replay (CRSP CIZ panel, `crsp_ciz_next_day` v`5211412140dcb86f08f9`), exploratory external-sequence evaluation |
| Data authorisation | The user confirmed the WRDS licence covers this use and instructed use of the data. Panel obtained from the repo's `data-2026-10-22` release; kept outside Git |
| Claim level | None for validity or deployment. Clocks, costs and the null are imposed assumptions |
| Candidate under test | **None.** The adaptive-policy branch (S3, S3b) produced no compact policy class, so this replay measures *benchmark landscape and headroom*, not a new method |

## Question

On real security-day paired decision costs, how much can *any* label-allocation rule add over uniform querying at a matched hard budget? An oracle-allocation upper bound answers this. If the headroom is small, no allocation algorithm can matter on this data.

## Stream (frozen)

- Panel test split (2020–2025). Cohorts: 10 disjoint random cohorts of 300 PERMNOs, drawn without replacement from the **train-split universe** (seed 20261029). Cohort choice does not use test presence. Events are ordered by date, then PERMNO.
- Candidate action: long if a Ridge (alpha 1; train-split rows of the cohort only; median-impute and standardise on train) predicts a positive next return. Reference action: long if same-date `vwretd > 0`. This is the repo's existing action pair.
- Paired cost `Z` = candidate cost − reference cost, with next returns clipped to ±10% and 5 bps per unit of position turnover (entry, change, exit), as in `scripts/evaluate_crsp_monitor_comparison.py`.
- Two directions are reported separately: **benefit** (`Y = −Z`, null `E[Y|G] ≤ 0`, certify that the candidate is better) and **harm** (`Y = Z`, null `E[Y|G] ≤ 0`).
- Label for a date becomes available at the next trading date (the panel's `label_available_time`). Evidence is updated through the resolved prefix only; the bet for date `d` uses statistics from increments resolved before `d`.
- Hard budget `B` = 5% or 20% of the cohort's events, counted at issue. When exhausted, no further queries and the wealth is frozen.

## Monitor (frozen)

Prediction-powered increment `X = H + Q (Y − H)/q`, with `H` a train-only Ridge prediction of `Y` clipped to the bound `M = 0.20 + 4·0.0005`. Predictable bound `B_t = M(2/q_t − 1)`. Bet: plug-in Kelly `λ_i = min(μ̂₊/m̂₂, 0.5/B_i)` per event, where `B_i` is that event's own predictable bound and `μ̂, m̂₂` come from increments resolved before its date (prior shrinkage: one pseudo-observation of zero). Threshold `1/α`, `α = 0.05`.

## Allocation rules

1. **Uniform:** `q = B/N`.
2. **Neyman / ASI shape:** `q(x) ∝ sqrt(r̂(x))`, `r̂` a train-only Ridge fit of `(Y − H)²`, floored at 10% of its mean, scaled to expected spend `B` using the validation split's features, capped at 1. This is the allocation form of Active Statistical Inference, as an adaptation and not a reproduction of its estimator.
3. **Evaluator-only oracle:** `q ∝ |Y − H|` (reads the outcome; **not implementable**), scaled to the same expected spend. It is an upper reference on allocation headroom.
4. **Full feedback:** every label queried (ceiling for evidence).

The repo's evidence-directed rule, Robust ASI, PPRM and Podkopaev–Ramdas baselines are **not** run in this replay. The comparison is therefore not a comparison with the full set of published benchmarks.

## Outcomes and decision

- Primary: mean final log-wealth per rule over (cohort × 20 query seeds), with paired differences against uniform and a cohort-cluster bootstrap 95% interval (2,000 resamples).
- Also: crossing frequency at `1/α`, first-crossing date, spend.
- Headroom = (oracle − uniform). If the headroom interval includes 0 or is below 0.05 log-units at both budgets, conclude that allocation cannot matter on this stream and stop.
- Any rule that beats uniform here is a descriptive finding, not a method claim.

## Validity limits

CRSP returns are cross-sectionally and serially dependent, the close-date ordering is not a verified release clock, and the conditional-mean null is not verified. Crossings are descriptive, not error-controlled.

## Reproduction

`uv run python -m shiftlab.dive.rpoq_crsp_replay --panel <path to observations.parquet>` writes `outputs/rpoq_s6_crsp_headroom_v1/`.

## Amendment before the registered run (2026-10-29)

A one-cohort, two-seed smoke run (not a result; discarded) showed that a single date-wide bet cap based on the date's largest bound throttled all non-uniform rules and put the oracle below uniform. The cap was changed to the per-event form now written in the Monitor section, which applies identically to every rule. No other parameter changed and no registered output existed.
