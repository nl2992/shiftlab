# QSG methods search: development protocol (registered 2026-11-07, before any candidate run)

Branch `research/qsg-methods-search-2026-11-07`, from `main@9f62583a`. Contract unchanged from
Failure Atlas v2: T=2000, B=200, c_q=0.05, c_s=5, alpha=0.05, shared simulator, paired streams.

## D0: baseline panel (descriptive, done before this file was written)

Seed base 2026110701, 50 seeds, 13 regimes, all `v2_extra` policies (39). Output
`outputs/qsg_methods_search/panel0/` (gitignored). Summary in `development_results.md`. These
seeds are now exposed and are used only for development.

## D1: first candidate screen (EQS, Track B / M2 with an M1 component)

**Target failure.** Fast uncertified selectors and the economic payback control churn or promote
on null/worse streams. Certified methods (alpha=.05) are 20-40 cost units slower on persistent
improvements. Neither is good on a mixed portfolio of persistent stationary regimes.

**Target family (stationary-persistent economic replacement), 11 regimes:** F0_better,
V_better_a, V_better_b, V_better_c, V_bursty, V_dep_better_r5, F7_near_better, F0_null, V_null,
V_worse, V_null_dep_r8. Late/reversal regimes (F1_late_800, F3_reversal_800) are reported as
guard cells only: they are not in the primary metric.

**Primary metric.** The family mean of per-regime mean net cost (equal regime weights), in cost
units per 2,000-event episode. Paired per-seed difference vs comparator; 95% t-interval over seeds
of the per-seed family-mean difference.

**Secondary.** Worst-regime mean regret vs hindsight oracle (within family); null/worse
promotion rate and switches; labels spent; the guard-cell costs.

**Strongest comparator (pre-declared).** `economic_replacement` (best family mean in D0), plus
a straightforward-composition control `econ+front` (the same point-estimate payback rule with
front-loaded acquisition) and a tuned version of each (`min_obs`, `margin` grid on the same dev
seeds as ours). Also reported: `model_selector_causal`, `qiu_delayed_movement`, QSG.

**No guarantee claimed.** EQS is an economic rule. It does not claim false-promotion control at
alpha; null promotion rates are reported, not certified.

**Tuning grids (fixed before D1).** econ and econ+front: min_obs {5,10,15,25,40} x margin
{0,5,10,20}. EQS: gamma {.05,.1,.2,.3} x monitor_frac {0,.25} x gamma_r {=gamma, .02}; ablations
no_front / no_stop / no_rollback per gamma, and EQS_point (gamma=.5). The best configuration of
each family is chosen by the primary metric on the D1 seeds; that selection is in-sample, so
D1 is development only and the frozen winner goes to fresh seeds.

**Screening seeds.** Seed base 2026110711, 40 seeds. Tuning of every tunable (ours and the
econ controls) uses only these seeds. Fresh confirmation seeds are not touched in D1.

**Advance rule (development).** EQS advances to frozen synthetic confirmation if its family-mean
cost is lower than the best tuned econ control with a 95% CI excluding 0, AND an ablation shows
that at least one EQS mechanism beyond front-loading contributes (CI excluding 0), AND neither
guard cell is worse than the econ control by more than 10 units. Effect grading follows the fair
standard: >=10% substantial, 3-10% meaningful, 1-3% small (relative to the comparator's family
mean regret, reported alongside the relative-to-cost figure).

## D1 outcome (recorded after the run; see development_results.md)

Advance rule **not met**: best EQS family mean 358.03 vs best tuned econ+front 357.56. EQS stops
on the stationary-persistent family.

## D2: change-aware economic switching (registered 2026-11-07, after D1, before any D2 run)

**Target failure.** M3 (late improvement, reversal, recurrence) for economic switchers. econ+front
has no rollback; Gong-Zhang (discounted economic switching) and Qiu (delayed-movement Hedge)
recover but churn on nulls; certified methods miss late changes (other-branch diagnosis).
Front-loading through the delay window also buys labels that a 5-label economic decision does not
need, starving post-decision monitoring.

**Candidate EQS-D.** Discounted QCE counts (factor lambda); symmetric economic switching with Beta
quantile hysteresis gamma (switch to the other model when the gamma-conservative payback over the
remaining horizon exceeds c_s); **decision-at-stake acquisition**: q=1 on disagreements only while
the optimistic payback of switching away from the deployed model exceeds c_s and fewer than
P_cap labels are pending; otherwise the paced rate x mf. Grid: lambda {.95,.98}, gamma {.2,.35},
P_cap {10, inf}, mf {.5,1}. Ablations: lambda=1; always-paced acquisition.

**Comparators.** gong_zhang_paid_obs (the closest prior construction), qiu_delayed_movement,
model_selector_causal, econF_mo5_m5 (D1 winner), QSG, never switch.

**Family (14 regimes, equal weight).** Change: F1_late_400, F1_late_800, F1_late_1200,
F2_transient, F3_reversal_800, F3_reversal_1200, F4_recurrent, V_late_600, V_reversal_1000,
V_recurrent. Stationary guards: F0_better, F0_null, V_worse, V_null.

**Primary metric.** Family mean net cost, paired per-seed difference vs the best comparator, 95% t
interval. Secondary: change-only and guard-only means; null promotion; switches.

**Seeds.** Base 2026110721, 40 seeds (development; in-sample config selection).

**Advance rule.** Best EQS-D config beats the best comparator on the primary metric with CI
excluding 0, AND the decision-at-stake acquisition ablation (always-paced) is worse with CI
excluding 0, AND guard-only mean is not worse than econF_mo5_m5 by more than 5 units.

## D2 outcome (recorded after the run)

Advance rule **not met** on its acquisition clause. Best config `EQSD_l0.95_g0.2_pcinf_mf1.0`:
family −6.08 [−7.26, −4.89] vs qiu (best comparator), −11.79 vs gong_zhang; guard not worse than
econF. Decision-at-stake acquisition vs always-paced ablation: −0.87 [−2.18, +0.45] (CI includes
0). The registered mechanism is not supported. The gain over gong_zhang survives without it
(paced variant −10.93 [−12.41, −9.45]).

## D3: decomposition against a tuned closest construction (registered before running)

**Question.** Is EQS-D's gain over Gong–Zhang explained by tuning? If not, which component
carries it: disagreement-conditional label-clock evidence (QCE counts with per-label discount
lambda) or Beta-quantile hysteresis (gamma)?

**Policies.**
- Gong–Zhang tuned: event-clock discount window W in {100, 200, 400, 800}, margin m in
  {0, 5, 10, 20} (switch when gain_left > cs + m; symmetric).
- EQS-D paced (no acquisition coupling): lambda in {.9, .95, .98} x gamma in {.1, .2, .3, .5};
  gamma=.5 is the no-hysteresis point-estimate ablation.
- D2 winner frozen as-is; qiu; econF_mo5_m5; never switch.

**Seeds.** Fresh development base 2026110731, 40 seeds (not the D2 seeds). Same 14-regime family
and primary metric as D2.

**Reading rule.** (i) Hysteresis matters if the best gamma<.5 beats gamma=.5 at the same lambda
with CI excluding 0. (ii) The candidate survives tuning if the best EQS-D-paced beats the best
tuned Gong–Zhang with CI excluding 0. Both selections are in-sample on these seeds; a survivor
goes to frozen confirmation on new seeds.

## D3 outcome (recorded after the run)

RNG parity of the tuned Gong–Zhang wrapper with the original adapter: exact after a seed-name fix
(first run differed only in query randomness and was discarded). (i) Hysteresis matters:
EQSDp λ=.95 γ=.2 − γ=.5 = −18.80 [−21.10, −16.50]. (ii) Survives tuning: best EQSDp (λ=.9,
γ=.2) − best tuned Gong (W=100, m=10) = −9.09 [−10.91, −7.27]; the **frozen D2 winner**
replicates on these fresh seeds: −6.29 [−7.97, −4.62] vs tuned Gong, −6.98 [−8.11, −5.85] vs qiu.

## D4: quantile hysteresis vs additive margin (registered before running)

Same 14-regime family and metric. Seeds: D3 seeds (2026110731), so this is an in-sample
mechanism ablation, not confirmation. Policies: EQSDp γ=.5 (point estimate) + additive margin
m in {5,10,20,40} at λ in {.9,.95}, against EQSDp γ=.2 at the same λ. Reading: the quantile is
the mechanism if, at each λ, γ=.2 beats the best margin with CI excluding 0.
