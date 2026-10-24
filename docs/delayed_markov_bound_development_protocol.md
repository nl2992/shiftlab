# Delayed feedback under Markov volatility: development protocol

**Status:** frozen before this development run, 2026-10-24. This is a diagnostic screen, not null calibration or confirmatory evidence. Use new stream IDs beginning at seed root `28104027`; do not tune parameters after inspecting its results.

## Question and assumptions

Does the registered history-only query policy with the predictable PPI support bound retain useful behavior when the validated two-state Markov-volatility process is combined with delayed queried labels? Compare it with the same query policy and fixed support bound at delays 1 and 12. This is a comparison of complete monitor-query systems; the bound can alter later query probabilities and paths.

For each event `t`, the data-generating process has a latent regime state `S_t`. The frozen Markov construction has `E[Z_t | S_t]=0` in both states under each exact-zero null, and the state is part of the event-time past before the event's current context and outcome are drawn. Consequently it satisfies the stronger martingale null `E[Z_t | G_t]=0` for the full event-time history `G_t`, not merely an unconditional mean-zero assertion. The history-only propensity is selected from the resolved evidence prefix and reserved query budget before the current context and query coin are revealed. Conditional on `G_t`, the query coin is independent and `q_t` is predictable. Therefore the usual PPI conditional-mean and support argument applies eventwise under this registered DGP.

The learner commits evidence only through the largest contiguous resolved event-time prefix. An arrival-time alarm must therefore be a crossing of the event-time e-process. Delays are deterministic and outcome-independent in this screen; no delay or non-arrival information is used as evidence or to choose propensities. The result will not cover arbitrary dependence, arbitrary missingness, changing policies, or query rules using current context.

## Frozen screen

- Generate 60 stream replicates per scenario with CUDA when available; use CPU replay for the existing vectorized sequential monitor.
- Use 2,400 events, the 20% hard label-dollar cap (480 requested labels), onset at event 1,200, `q_min=0.05`, fixed action pair, independent source-trained proxy, and the existing five-stake fixed mixture.
- Scenarios: Markov exact-zero null, Markov strict-negative control, and Markov harmful effects `{0.04, 0.20, 0.40, 0.60}`.
- Compare delays `{1,12}` crossed with support bounds `B=M(2/q_min-1)` and `B_t=M(2/q_t-1)`. Within each scenario, all arms share generated states, contexts, outcome uniforms, query uniforms, and source training data.
- Validate the hard label cap, exact event order, eventwise support bound, complete flush, and no access to queried outcomes before arrival. Record event-time and wall-time detection delay, onset reach, labels, processed events, pre-onset alarms, and evaluator-only state-conditional expected harm exposure.
- Report per-cell false escalations as small-sample diagnostics only. Do not claim calibration from 60 streams. Any follow-up must use a fresh, independently frozen calibration block, followed by a disjoint alternative confirmation.

No figure is required for this screen. If a visual is later needed, use PaperBanana; when it is unavailable, document the limitation and publish the numeric table and Parquet metrics without substituting another generator.

## Reproduction

```powershell
uv run python scripts/validate_delayed_markov_predictable_bounds.py --streams 60 --seed 28104027 --device cuda --output outputs/delayed_markov_predictable_development_60
uv run pytest tests/test_delayed_markov_predictable_bounds.py tests/test_delayed_history_predictable_bounds.py tests/test_delayed_feedback.py -q
```
