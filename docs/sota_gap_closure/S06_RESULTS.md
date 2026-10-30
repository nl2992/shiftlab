# S06 budget-paced delayed query allocation: results
Hard pathwise budget B = frac*T charged at issue; exhausted paths become inactive. Rules: `bernoulli` (expected budget, no cap), `hard_bern` (Bernoulli q = frac with a hard cap), `const` (q = B/T), `remaining` (q = remaining budget / remaining steps), `info_value` (remaining-budget rate x estimated variance score), `reserve` (high rate on above-average score events, low rate otherwise), `two_stage` (30% of the budget in the first quarter), `growth_pace` (growth score + pacing). Grid actually run: T=2000 with onset {.2,.5,.8} x regime {abrupt, gradual, transient, recurrent} x delay {0,1,5,20} x fraction {.01,.05,.10,.20} (v1) and delay {0,5,20} x fraction {.05,.10,.20} (v2); T in {100, 500} at onset .5 (abrupt, transient). 100 seeds per cell. The short-horizon dynamic program and the RPOQ exact solver are used only on the toy instance (`S11_ORACLE_GAP_RESULTS.md`): a DP at scale was NOT implemented.

**Defect disclosure.** v1 used a propensity floor of frac/4 for every pacing rule, **including `const`, which is exactly `hard_bern`**; the predictable cap was therefore 4x tighter than necessary and v1 numbers confound pacing with the cap floor. v2 sets the exact floor for `const` and frac/2 for the others. v1 is kept as the record of that error.

## v1 (floor frac/4, confounded)
Mean power over onset x regime x delay (T=2000, 100 seeds per cell):

| frac_cfg | bernoulli | const | growth_pace | hard_bern | info_value | remaining | reserve | two_stage |
|---|---|---|---|---|---|---|---|---|
| 0.010 | 0.002 | 0.000 | 0.000 | 0.002 | 0.000 | 0.000 | 0.000 | 0.000 |
| 0.050 | 0.172 | 0.023 | 0.024 | 0.155 | 0.033 | 0.029 | 0.022 | 0.029 |
| 0.100 | 0.409 | 0.224 | 0.247 | 0.394 | 0.250 | 0.232 | 0.155 | 0.224 |
| 0.200 | 0.697 | 0.558 | 0.602 | 0.682 | 0.606 | 0.577 | 0.445 | 0.572 |

By onset (fraction .10, delay 5):

| onset | bernoulli | const | growth_pace | hard_bern | info_value | remaining | reserve | two_stage |
|---|---|---|---|---|---|---|---|---|
| 0.2 | 0.655 | 0.460 | 0.507 | 0.647 | 0.500 | 0.460 | 0.345 | 0.458 |
| 0.5 | 0.463 | 0.205 | 0.240 | 0.450 | 0.242 | 0.217 | 0.125 | 0.198 |
| 0.8 | 0.125 | 0.010 | 0.022 | 0.110 | 0.015 | 0.018 | 0.003 | 0.015 |

By regime (fraction .10, delay 5):

| regime | bernoulli | const | growth_pace | hard_bern | info_value | remaining | reserve | two_stage |
|---|---|---|---|---|---|---|---|---|
| abrupt | 0.583 | 0.400 | 0.420 | 0.563 | 0.457 | 0.417 | 0.290 | 0.393 |
| gradual | 0.537 | 0.373 | 0.407 | 0.520 | 0.403 | 0.393 | 0.250 | 0.370 |
| recurrent | 0.300 | 0.107 | 0.163 | 0.297 | 0.130 | 0.103 | 0.057 | 0.110 |
| transient | 0.237 | 0.020 | 0.037 | 0.230 | 0.020 | 0.013 | 0.033 | 0.020 |

Pathwise compliance: max over all paths of (labels - B) per hard-budget arm: `{'const': 0.0, 'growth_pace': 0.0, 'hard_bern': 0.0, 'info_value': 0.0, 'remaining': 0.0, 'reserve': 0.0, 'two_stage': 0.0}`. Spending / pending-queue statistics (fraction .10, all delays):

| config | mean_pending | max_pending_delay20 | frac_paths_exhausted | labels | harm_before_alarm | mean_exhaust_t |
|---|---|---|---|---|---|---|
| bernoulli | 0.716 | 10.000 | 0.000 | 198.130 | 129.252 |  |
| const | 0.701 | 10.000 | 0.430 | 193.670 | 151.926 | 1888.209 |
| growth_pace | 0.722 | 21.000 | 0.944 | 199.939 | 149.970 | 1985.479 |
| hard_bern | 0.701 | 10.000 | 0.430 | 193.670 | 129.454 | 1888.209 |
| info_value | 0.722 | 15.000 | 0.976 | 199.976 | 148.606 | 1988.367 |
| remaining | 0.722 | 10.000 | 1.000 | 200.000 | 151.451 | 1990.590 |
| reserve | 0.724 | 14.000 | 0.986 | 199.981 | 156.213 | 1939.909 |
| two_stage | 0.722 | 10.000 | 1.000 | 200.000 | 152.756 | 1989.940 |

Null-world false alarm (all arms):

| frac_cfg | bernoulli | const | growth_pace | hard_bern | info_value | remaining | reserve | two_stage |
|---|---|---|---|---|---|---|---|---|
| 0.010 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 0.050 | 0.020 | 0.000 | 0.000 | 0.020 | 0.000 | 0.000 | 0.000 | 0.000 |
| 0.100 | 0.020 | 0.000 | 0.000 | 0.020 | 0.000 | 0.000 | 0.003 | 0.000 |
| 0.200 | 0.015 | 0.000 | 0.000 | 0.015 | 0.000 | 0.000 | 0.010 | 0.000 |

## v2 (corrected floors)
Mean power over onset x regime x delay (T=2000, 100 seeds per cell):

| frac_cfg | bernoulli | const | growth_pace | hard_bern | info_value | remaining | reserve | two_stage |
|---|---|---|---|---|---|---|---|---|
| 0.050 | 0.172 | 0.155 | 0.120 | 0.155 | 0.141 | 0.133 | 0.114 | 0.126 |
| 0.100 | 0.407 | 0.392 | 0.403 | 0.392 | 0.416 | 0.386 | 0.372 | 0.363 |
| 0.200 | 0.693 | 0.679 | 0.732 | 0.679 | 0.747 | 0.698 | 0.677 | 0.681 |

By onset (fraction .10, delay 5):

| onset | bernoulli | const | growth_pace | hard_bern | info_value | remaining | reserve | two_stage |
|---|---|---|---|---|---|---|---|---|
| 0.2 | 0.655 | 0.647 | 0.698 | 0.647 | 0.680 | 0.630 | 0.632 | 0.613 |
| 0.5 | 0.463 | 0.450 | 0.455 | 0.450 | 0.500 | 0.432 | 0.432 | 0.422 |
| 0.8 | 0.125 | 0.110 | 0.085 | 0.110 | 0.110 | 0.105 | 0.062 | 0.080 |

By regime (fraction .10, delay 5):

| regime | bernoulli | const | growth_pace | hard_bern | info_value | remaining | reserve | two_stage |
|---|---|---|---|---|---|---|---|---|
| abrupt | 0.583 | 0.563 | 0.600 | 0.563 | 0.623 | 0.560 | 0.573 | 0.540 |
| gradual | 0.537 | 0.520 | 0.520 | 0.520 | 0.540 | 0.547 | 0.513 | 0.517 |
| recurrent | 0.300 | 0.297 | 0.327 | 0.297 | 0.323 | 0.277 | 0.273 | 0.260 |
| transient | 0.237 | 0.230 | 0.203 | 0.230 | 0.233 | 0.173 | 0.143 | 0.170 |

Pathwise compliance: max over all paths of (labels - B) per hard-budget arm: `{'const': 0.0, 'growth_pace': 0.0, 'hard_bern': 0.0, 'info_value': 0.0, 'remaining': 0.0, 'reserve': 0.0, 'two_stage': 0.0}`. Spending / pending-queue statistics (fraction .10, all delays):

| config | mean_pending | max_pending_delay20 | frac_paths_exhausted | labels | harm_before_alarm | mean_exhaust_t |
|---|---|---|---|---|---|---|
| bernoulli | 0.888 | 10.000 | 0.000 | 198.130 | 129.252 |  |
| const | 0.870 | 10.000 | 0.430 | 193.670 | 129.454 | 1888.209 |
| growth_pace | 0.898 | 21.000 | 0.982 | 199.982 | 124.213 | 1967.826 |
| hard_bern | 0.870 | 10.000 | 0.430 | 193.670 | 129.454 | 1888.209 |
| info_value | 0.897 | 11.000 | 0.976 | 199.976 | 124.588 | 1984.107 |
| remaining | 0.896 | 10.000 | 1.000 | 200.000 | 130.738 | 1990.050 |
| reserve | 0.898 | 12.000 | 0.987 | 199.987 | 129.085 | 1967.739 |
| two_stage | 0.896 | 10.000 | 1.000 | 200.000 | 132.859 | 1987.870 |

Null-world false alarm (all arms):

| frac_cfg | bernoulli | const | growth_pace | hard_bern | info_value | remaining | reserve | two_stage |
|---|---|---|---|---|---|---|---|---|
| 0.050 | 0.020 | 0.020 | 0.000 | 0.020 | 0.003 | 0.003 | 0.010 | 0.000 |
| 0.100 | 0.020 | 0.020 | 0.010 | 0.020 | 0.000 | 0.000 | 0.010 | 0.003 |
| 0.200 | 0.017 | 0.017 | 0.027 | 0.017 | 0.003 | 0.017 | 0.007 | 0.007 |

## Reading
* Hard-budget compliance holds on every path for every rule (tests + max(labels - B) = 0 in both runs).
* **v1 (confounded) vs v2 (corrected floors).** v1 suggested that every pacing rule loses ~0.15 power to hard-capped Bernoulli; that was the cap-floor confound (`const` is *identical* to `hard_bern` yet lost 0.17). In v2 `const` equals `hard_bern` and the paced rules are close to it.
* v2 gains over the hard-capped uniform arm (mean over onset x regime x delay): info_value at 20% labels +0.068; growth_pace at 20% labels +0.053; info_value at 10% labels +0.023; remaining at 20% labels +0.020
* Late onset (0.8) remains nearly undetectable for every arm; rules that spend the whole budget early (`remaining`, `two_stage`) exhaust on ~100% of paths and gain nothing from it; pending-feedback queues stay short (mean pending ~0.2 / 0.6 / 2.1 at delay 1 / 5 / 20), so pacing around pending labels is not the bottleneck.
**Acceptance (pacing improves on tuned uniform by >= +0.03 at some budget with 100% compliance): MET at the 20% budget by growth_pace, info_value (and not at 5%, where every paced rule is below `hard_bern`).** A dynamic-programming pacing rule at scale was not implemented; exact small-horizon references are in `S11_ORACLE_GAP_RESULTS.md`.
