# Measures: field semantics and definitions

Paths are relative to the main checkout `shift-research-starter` (read only). Line numbers refer
to commit 1bb6d055.

## 1. What each record field means

One record = one (stream, episode `ep`, policy `seed`, `policy`) run of `run_episode`
(`scripts/qsg_methods_search/sota_nine.py:_job`, lines 31-92). The episode is a stream of T=2000
events with two models: model 0 = incumbent, model 1 = challenger. Losses are 0/1 and come from the
sealed arrays `l0`, `l1` (`sota_nine.py:42`). Predictions and labels are synthesised so that the
prediction loss reproduces the stored loss exactly (`scripts/failure_atlas_v2_flq/suite.py:96-100`,
`stream_from_losses`).

| field | meaning | code |
|---|---|---|
| `stream`, `ep` | dataset and episode index | sota_nine.py:66-67 |
| `seed` | policy seed (10 per episode); the stream is fixed, only policy randomness changes | sota_nine.py:59 |
| `delay` | feedback delay in events (dataset constant); a label requested at t is released at t+delay | scripts/promising_directions/sota/simulator.py (`release_time = t + delay`) |
| `loss` | total 0/1 prediction loss of the **deployed** model over the T events (a count, not a mean) | simulator.py:192-193 |
| `labels` | number of paid labels, `<= B = 200` | simulator.py `n_requested`; suite.py:108 assert |
| `switches` | number of changes of the deployed model index, counting switches back and forth, starting from model 0 | simulator.py:191 |
| `net` | `loss + c_q * labels + c_s * switches` with c_q=.05, c_s=5; the episode total cost J | simulator.py:235; checked exactly in `data.check_invariants` (max abs error 0.0 over all 337,950 rows) |
| `first_deploy` | first event index t at which the challenger (model 1) is deployed, **-1 if never**; 0-based, so event t is already scored with model 1 | suite.py:114 |
| `ever_promote` | `1[first_deploy >= 0]` (checked) | suite.py:121 |
| `final` | model index deployed at the last event (0 incumbent, 1 challenger) | suite.py:122 |
| `mean_gain` | evaluator-side episode constant `mean_t(l0_t - l1_t)`: **positive = the challenger (model 1) has lower realised loss, i.e. is truly better; negative = the incumbent is better**; units: loss per event; `mean_gain * T` is the integer loss difference `L0 - L1` (checked) | sota_nine.py:43, 85 |
| `frac_on_wrong` | fraction of the T events on which the deployed model is the **episode-level worse model**: `1[dep=1 & gain<0] + 1[dep=0 & gain>0]`, averaged over events. It is 0 when `gain == 0` (no worse model), not undefined | suite.py:115-117, 123 |

Oracle status: `mean_gain`, `first_deploy`, `final`, `frac_on_wrong` are computed by the evaluator
from hidden full-episode losses and labels; policies never see them (`run_episode` docstring:
labels are "evaluator-only"). All measures below are evaluator-side scores.

Consequences, each checked in `data.check_invariants`:

- `CONTROL_never_switch` (= `FixedModel(0)`, `scripts/promising_directions/sota/competitors/controls.py:251`)
  has `labels = 0`, `switches = 0`, `net = loss = L0` for every seed, so `J_never(ep) = L0(ep)` is
  seed independent. It is the **frozen incumbent reference pi_ref**.
- `L1 = L0 - T * mean_gain`, hence the cost of the best fixed model in hindsight (no labels, no
  switches) is `J_hind = J_never - T * max(gain, 0) = min(L0, L1)`.
- The episode-level `gain` is one sign per episode. "Challenger truly better" refers to the whole
  episode's realised loss, not to local regimes inside it. Within-episode regime changes are not in
  the records, so a time-varying hindsight switching oracle is **not derivable**; the hindsight
  reference is the best *fixed* model only. A policy that switches profitably inside an episode can
  exceed 100% capture.

Episode classes (evaluator-side): **C** = `gain > 0` (challenger better), **S** = `gain < 0`
(challenger strictly worse), **N** = `gain <= 0` (challenger not better = S plus ties; ties are
about 1% of episodes). Class counts per dataset are tabulated in `03_MEASURE_RESULTS.md`; dc_311
has no N or S episode.

## 2. Aggregation

Fields are first averaged over the 10 policy seeds per episode (numerators and denominators
separately); every measure is then a **ratio of sums over episodes**, `sum_e num_e / sum_e den_e`
(plain means have den = 1 on the relevant class). Dataset values are bootstrapped by resampling
episodes (2,000 resamples; one shared resample per dataset so arm-minus-comparator differences
are paired). POOLED = equal-weight mean of dataset values; its CI is the percentile interval of the
equal-weight mean of per-dataset bootstrap values (episodes resampled within dataset, independent
across datasets). Differences also carry a dataset-level t 95% interval and the count of datasets
with negative difference (`measure_diffs_*.csv`). The bootstrap resamples episodes, not time
points; episodes within a dataset are treated as exchangeable (serial dependence between adjacent
episodes is not modelled) and seeds are averaged, not resampled. Pooling skips datasets where a
measure is undefined (dc_311 for N/S measures; datasets where a policy never promotes in a C
episode for `ttc_given_promoted`).

## 3. Measures (J = net: loss + label cost + switch cost)

Notation: `J_pi`, `J_never`, `J_hind` as above. Lower is better unless stated.

(a) **Decision harm vs the frozen incumbent** (charter: R_t(pi_t) - R_t(pi_ref), with pi_ref = never
switch; label and switch costs are charged to pi, which is the operational cost of adapting):

- `harm_all = mean_e (J_pi - J_never)`; negative = pi beats the incumbent. `harm_C`, `harm_N` the
  same restricted to C and N episodes (`harm_N > 0` is the realised cost of adapting when the
  incumbent was already at least as good).
- `capture = sum_{e in C} (J_never - J_pi) / sum_{e in C} (J_never - J_hind)`: share of the
  hindsight-attainable improvement (best fixed model) that pi captured; higher is better; it can
  exceed 1 or be negative.
- `regret_hind = mean_e (J_pi - J_hind)`: cost above the best fixed model.

(b) **Wrong-model exposure**: `wrong_exposure = mean_{e: gain != 0} frac_on_wrong`; `_C` (time on
the incumbent when the challenger is better) and `_S` (time on the challenger when it is worse).

(c) **Time to correct action** on C episodes: `ttc = first_deploy` if >= 0, else **T = 2000
(right-censored)**. `ttc_rmst = mean_{e in C} ttc` (restricted mean, censored at T);
`promoted_C` = share of C episodes where the challenger is ever deployed (higher better);
`ttc_given_promoted` = mean `first_deploy` over promoted C episodes (conditional, not
censoring-adjusted: favours methods that rarely promote). "Correct action" is the first deployment
of the truly better model; staying there is measured by (g).

(d) **False-promotion rate**: `false_promo_N = mean_{e in N} ever_promote` (primary; challenger not
better); `false_promo_S` on strictly-worse episodes. It is the rate of ever deploying the
challenger when it is not better, not a calibrated type-I error: no EQSDp arm claims a
false-promotion guarantee (eqs_d.py docstring: "No false-promotion guarantee is claimed").

(e) **Churn and switch-cost share**: `switches = mean_e switches`;
`switch_cost_share = sum c_s*switches / sum J_pi`; `label_cost_share = sum c_q*labels / sum J_pi`.

(f) **Label efficiency** (higher better): `label_eff_gross = sum_e (J_never - loss_pi) / sum_e labels_pi`
(prediction loss averted per paid label) and `label_eff_net = sum_e (J_never - J_pi) / sum_e labels_pi`
(net cost averted per paid label, after label and switch costs). Undefined for never-switch
(0 labels). Totals run over all episodes, including N episodes where the numerator is typically
negative.

(g) **Terminal correctness** (higher better): `terminal_correct = mean_{e: gain != 0} 1[final is the
better model]`; `_C`: `final == 1` on C; `_S`: `final == 0` on S.

Not defined, omitted: a within-episode hindsight switching oracle and time to correct action after
a regime change (change times are not in the records); a false-alarm rate against a nominal alpha
(these policies have none); per-time harm curves (only episode totals and three timing fields are
recorded).

## 4. Interpretation boundary

These are post-hoc, descriptive, evaluator-side scores of already-run policies on retrospective
open-data streams; "challenger better" is the episode's realised mean loss difference, not a
verified causal shift label. They measure decision harm against a frozen reference under the paid
label budget; they do not establish a monitoring guarantee. The conditional excess-cost null of
Paper 1 (filtration, feedback regime, predictable policy selection) is not tested here.
