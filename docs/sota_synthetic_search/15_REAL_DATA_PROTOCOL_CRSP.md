# 15. CRSP real-data replay protocol (written and committed BEFORE running)

**Authorization.** The user lifted the synthetic-only restriction on 2026-10-30 ("Lift the synthetic data restriction") and had earlier stated the CRSP data is licensed. This stage is **separate from, and after,** the synthetic programme; synthetic verdicts (docs 11, 13) are not altered. Only `observations.parquet` from the existing pull is used; no WRDS/Binance access.

**Status of any result: exploratory.** Imposed daily clock, imposed cost and fee, no verified label-availability times, test period 2020–2025 already exposed in earlier RPOQ work (docs/rpoq_next). No claim of validity, causal shift, profit or deployment.

**Stream.** Same cohorts, features and candidate/reference construction as `dive/rpoq_next/crsp_b1.py` (`build_cohort_b`, eval split `test`): per event, `z` = candidate-minus-reference decision cost, `h` = ridge proxy trained on the train split. Harm direction: the candidate is worse than the reference (mean z > 0). Benefit direction (mean z < 0) is run as a sanity direction and is not a false-alarm count.

**Arms (frozen from the synthetic phase, nothing re-tuned):**
- `parent`: tight-capped PP e-process, pooled plug-in Kelly bet (the `pp_cost_tight` form), uniform q = frac.
- `DK`: same, with exponentially discounted Kelly moments, γ = 0.995 per **date** (frozen `DK_cost`).
- HG is **not run**: it gates on a Brier-vs-cost pair of losses, and this stream has only one loss. BD is not run (unconfirmed on G2). No Page–Hinkley/CUSUM arm: their thresholds need a null stream the real data does not provide.
Label fractions 0.05 and 0.20, α = 0.05, date-batched bets (all events of a date share the bet, labels resolve at end of date), 20 query seeds, cohort-level bootstrap.

**One-sided cap.** Increment X = h + (Q/q)(z − h); with z ≥ −BOUND, X ≥ −max(BOUND, (BOUND + h)/q − h). Cap λ ≤ 0.5 / that bound, same argument as docs 12.

**Metrics.** Mean final log-wealth and crossing probability (log-wealth ≥ log(1/α)) per direction; per-cohort DK − parent difference with 95% cohort bootstrap interval.

**Decision rule (set now).** DK is reported as "improved on real replay" only if the harm-direction log-wealth difference has a 95% interval excluding 0 at **both** label fractions. Otherwise reported as not supported. Single run, no re-tuning, no re-run after seeing results.
