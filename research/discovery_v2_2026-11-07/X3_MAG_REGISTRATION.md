# X3 registration — margin-aligned guidance (MAG) for Brier-guided cost betting

Registered 2026-11-07, **before any MAG result was computed**. Evidence class of everything this produces: **EXPLORATORY**
(development seeds; gas is the dataset that motivated the hypothesis, so gas results are in-sample and cannot support the claim).

## Failure being addressed (observed, `research/novelty_validation_2026-10-30/07` §3)
With an estimated nominal risk, the cost statistic is tested against `U0_cost = r̂0 + margin`, but H2c's Brier guide is centred at the
point estimate `r̂0_brier`. Before any harm the guide is positive while cost increments are negative, so H2c bets and loses
7–30 nats before onset (gas stream B).

## Modification (decided before running)
**MAG:** centre the guide at its own Hoeffding upper bound at the same `δ_S`: `U0_brier = r̂0_brier + 1·sqrt(ln(1/δ_S)/(2 n_cal))`
(Brier range [0,1]). Nothing else changes: same cost increment, cost UCB, caps, discounting γ = 0.995, delay 5, cap 0.5. The guide still
takes no economic tolerance (repo bug history). Validity is unaffected (any predictable bet; doc 08 S1).

## Hypotheses and metrics (frozen)
* H-MAG-1 (primary, synthetic): with estimated nominal risk, MAG's power ≥ H2c's power in every harmful world and ≥ cost-only discounted Kelly (C1)
  in the "aligned" worlds; metric = alarm probability in the post-onset window, paired by seed.
* H-MAG-2 (synthetic): MAG's loss to C1 in "masked/opposed" worlds is no larger than H2c's.
* H-MAG-3 (safety): pre-onset alarm rate ≤ α_T for all arms in all worlds.
* Gas (in-sample, descriptive only): MAG alarm index vs H2c and C1/C2 on stream B.

## Design
Stylised worlds of `research/novelty_validation_2026-10-30/scripts/x1_guidance_mechanism.py` (same increments and caps), plus a null
calibration sample of `n_cal ∈ {500, 2000, 10000}` events drawn from the pre-onset law, label rate q ∈ {0.1, 0.2}, α_T = 0.04,
δ_S = 0.01, threshold ln 25, onset 500 of T = 1500, S = 2000 paths per cell. Fresh seeds 700000+ (never used before). Arms: C1 (cost
UCB), H2c (guide at point estimate), MAG (guide at Brier UCB). Worlds: aligned ρ .8, aligned ρ 0, masked, opposed, misleading null, null.

Follow-up rule: if MAG passes H-MAG-1/3 in development, a **fresh, frozen** confirmation on unexposed data (NYC TLC candidate) is
required before any superiority wording; gas cannot serve.
