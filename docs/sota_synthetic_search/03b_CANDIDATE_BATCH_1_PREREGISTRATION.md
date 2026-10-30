# Candidate batch 1: preregistration (frozen before running)

Same development pool, seeds, calibration and screening metric as `03_*`. Baselines in this batch are the **tight-capped** prediction-powered detectors, because the initial `pprm`/`pp_cost` implementation used a symmetric worst-case bet cap that a unit test shows is far looser than the true one-sided minimum of the increment. The loose versions stay in the registry as the historical implementation and must not be presented as strong baselines.

## X1 — tight one-sided bet cap (extra candidate generated from experimental results)
1. **Parent:** `pprm` (PPRM-inspired, Brier risk) and `pp_cost` (decision-cost). Two parents.
2. **Modification:** cap the Kelly bet by `0.5 / |X_min|`, with the exact predictable minimum of the increment `X_min = −(R̂(1/q − 1) + r₀ + tol)`, instead of `0.5 / (M(2/q − 1) + M)`.
3. **Targeted mechanism:** bet throttling from a loose range bound (evidence growth is proportional to the bet size).
4. **Predicted direction:** higher power and lower delay at the same label rate; null false-alarm unchanged or lower because the validity argument (`1 + λX ≥ 1/2`) is unchanged.
5. **Matched baseline:** the loose version of each parent at identical settings.
6. **Primary metric:** detection probability on harm worlds at null false alarm ≤ 0.05.
7. **Cost:** none (one array).
8. **Should fail if:** the loose cap was not binding (Kelly bets already below the cap), or tight caps inflate false alarm under null.
9. **Falsification experiment:** compare tight vs loose across the 108 shared configurations; the claim fails if the median paired difference in power on harm worlds is below +0.05.

## S01 — decision-harm-aware PPRM
`pp_cost_tight` against `pprm_tight`. Hypothesis: the decision-cost version alarms less on benign shifts (notably `prior`, where predictive loss rises while decision cost falls) and more on subgroup or concept shifts with asymmetric costs. **Fails if** its power on harm worlds is lower or its benign false alarm is no lower than `pprm_tight`.

## S02 — multi-start (Shiryaev–Roberts) form of the tight e-process
`sr_cost_tight` and `sr_brier_tight` (empirically calibrated threshold) against `pprm_tight`, `pp_cost_tight` and the strongest classical detectors. Hypothesis: the multi-start statistic recovers the delay lost to pre-change accumulation. **Fails if** it does not beat the corresponding single-start e-process on delay at matched null false alarm, or if it loses to Page–Hinkley/CUSUM on harm-before-alarm. Note: its threshold is empirical, so it carries no anytime-validity claim.

## Configurations
`{pprm, pp_cost, pprm_tight, pp_cost_tight, sr_cost_tight, sr_brier_tight} × frac {0.05, 0.10, 0.20} × delay {0, 5, 20} × tol {0, 0.05}` = 108 configurations × 16 development worlds, 200 seeds, registry batch `q1_candidates`.

## Decision rules
X1 supported if its falsification test passes and the null false alarm of the tight versions is ≤ 0.07. S01 and S02 supported only if their stated hypotheses hold in the batch summary. Supported ≠ confirmed: nothing is claimed until the held-out pool is run with frozen settings.
