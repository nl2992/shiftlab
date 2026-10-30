# Search preregistration — infrastructure checkpoint v1

## Resource envelope

The checked-in `configs/sota_search/resource_budget.json` sets a maximum of 1,500
attempts per batch, one hour wall time per batch, 60 seconds wall and CPU time per
worker, 2 GiB resident process-tree memory, and 512 MiB per output snapshot. The
supervisor samples every 50 ms and kills the worker tree on a breach. These are
sampled limits, not OS-enforced exact instantaneous ceilings. Worker logs count
toward storage. This checkpoint runs serially on CPU with OMP_NUM_THREADS=1.

This envelope is not permission to repeatedly launch one-hour batches. Cumulative
programme accounting must be implemented before the first 500–1,500-configuration
screen. Current authorization is a 12-run infrastructure smoke batch under this
envelope. No downloads, real datasets, or protected holdouts are used.

## Locked smoke manifest, before execution

- Workers: PPE and direct IPW bounded betting from existing repository modules.
- Worlds: IID Bernoulli losses, risk 0.2 (null) and 0.5 (alternative); horizon 512.
- Seeds: 271000, 271001, 271002, paired across methods.
- Nominal risk: 0.2. Alarm threshold: wealth 20 (alpha 0.05).
- Queries: independent Bernoulli(0.2), common random numbers across methods;
  this is an expected budget and is explicitly not a hard-budget comparison.
- Proxy: constant nominal-risk proxy. PPE stake 0.08. Direct IPW bound 5 and
  normalized stake 0.4, making the effective coefficient identical.
- Feedback: immediate, observed labels only; no current unqueried label passed
  to either monitor. No adaptation or intervention.
- Primary diagnostic: execution completes and matched methods agree on alarm
  outcome and time for every paired world. Secondary: captured label use and logs.
- No screening, selection, tuning, confidence intervals, or novelty inference
  from these six worlds. No survivors are chosen from this batch.

## Full search still required

The requested 500–1,500 valid configurations, S01–S12 families, G1–G4 generators,
successive-halving criteria, matched baseline tuning, Q1/Q2/Q3 primary metrics,
development/validation/confirmation seed separation, multiple-comparison handling,
and held-out generator-family pools must be frozen in a later protocol before
the substantive screen. This smoke protocol does not replace those requirements.
