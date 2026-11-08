# Gap-Mix+ C3 development results

Prereg: `00_PREREG_GAPMIX_PLUS.md` (commit 1fc3a300). Frozen config: `configs/methods_recovery/gapmix_plus_frozen.json` sha256 `1010a0f9a3079b7a17b6fc10bfc1e104c4413d37da3bccb7e04ec59875980fe4`.
Eval seeds `gapmix_plus_eval` (101400000-101429999). Alt/neighbour cells: 112 cells (target 48), seeds per cell 60-60. Null: 18 cells, streams per cell 500-500.
Development evidence only. Effects are relative reductions of mean J/T (equal-weight over cells; paired bootstrap 95% CI over seeds within cell, 4000 resamples).

## 4. Validity: null grid (rho in {0,.5,.8} x B/T in {.05,.1,.25} x d in {1,10}), Clopper-Pearson 95% upper bound

| arm | worst UCB | at cell | pooled FP rate | valid (<= 0.1) |
|---|---|---|---|---|
| Arm1 Markov-LR/DSS-acq | 0.018 | dep_rho0.5_bt0.25_d10 | 0.0026 | yes |
| Arm2 Gap-Mix/DSS-acq | 0.048 | dep_rho0.8_bt0.25_d10 | 0.0084 | yes |
| Arm3 Gap-Mix/PAVE | 0.039 | dep_rho0.8_bt0.1_d1 | 0.0090 | yes |
| Arm4 Gap-Mix+ | 0.048 | dep_rho0.8_bt0.25_d10 | 0.0137 | yes |
| Arm5 Gap-Mix/fixed pacing | 0.055 | dep_rho0.8_bt0.25_d10 | 0.0148 | yes |
| Arm4a (evidence frozen) | 0.060 | dep_rho0.8_bt0.1_d10 | 0.0163 | yes |
| QSG-envelope evidence | 0.024 | dep_rho0.8_bt0.05_d10 | 0.0041 | yes |
| gap-10 thinning | 0.083 | dep_rho0.8_bt0.1_d1 | 0.0262 | yes |
| episode_front | 0.552 | dep_rho0.8_bt0.25_d10 | 0.0866 | NO |
| uniform | 0.423 | dep_rho0.8_bt0.25_d10 | 0.0540 | NO |

## Comparator per cell family (strongest valid arm among Arms 1,2,3,5 + extras, lowest mean J on eval seeds)

| family (B/T, d) | comparator | its mean J/T | Arm 4 mean J/T |
|---|---|---|---|
| b0.05_d1 | Arm3 Gap-Mix/PAVE | 0.4543 | 0.4641 |
| b0.05_d10 | Arm3 Gap-Mix/PAVE | 0.4446 | 0.4621 |
| b0.1_d1 | gap-10 thinning | 0.3997 | 0.4241 |
| b0.1_d10 | gap-10 thinning | 0.4109 | 0.4279 |
| b0.25_d1 | Arm5 Gap-Mix/fixed pacing | 0.4143 | 0.4129 |
| b0.25_d10 | gap-10 thinning | 0.4240 | 0.4579 |

## 5. C3 criteria

| contrast (candidate minus reference, J/T) | diff [95% CI] | rel. gain [95% CI] |
|---|---|---|
| C1: Arm 4 vs strongest valid comparator, pooled target | +0.0169 [+0.0139, +0.0197] | -3.97% [-4.66, -3.27] |
| C2: Arm 4 vs Arm 4a, pooled target | -0.0053 [-0.0074, -0.0033] | 1.19% [0.74, 1.66] |
| C3a: Arm 4 vs Arm 2 | -0.0075 [-0.0099, -0.0049] | 1.66% [1.09, 2.20] |
| C3b: Arm 4 vs Arm 5 | -0.0035 [-0.0056, -0.0014] | 0.79% [0.31, 1.27] |
| C3c: Arm 4 vs Arm 3, pooled target | -0.0078 [-0.0104, -0.0051] | 1.73% [1.13, 2.30] |
| C3d: Arm 4 vs Arm 3, gate-on subset (8 cells) | -0.0030 [-0.0093, +0.0028] | 0.65% [-0.61, 2.01] |
| C5: Arm 4 vs strongest valid comparator, neighbour `rho0` (24 cells) | +0.0253 [+0.0211, +0.0294] | -5.98% [-7.00, -4.97] |
| C5: Arm 4 vs strongest valid comparator, neighbour `d50` (24 cells) | +0.0129 [+0.0098, +0.0159] | -2.86% [-3.55, -2.18] |
| C5: Arm 4 vs strongest valid comparator, neighbour `b0.5` (16 cells) | +0.0463 [+0.0411, +0.0514] | -11.31% [-12.68, -9.96] |

| # | criterion | value | pass |
|---|---|---|---|
| 1 | effect >= 3%, CI excludes 0 | -3.97% [-4.66, -3.27] | False |
| 2 | attribution: Arm 4 < Arm 4a, CI excludes 0 | diff -0.0053 [-0.0074, -0.0033] | True |
| 3 | beats Arm 2, Arm 5, Arm 3 (pooled and gate-on) | A2 -0.0049.. / A5 -0.0014.. / A3 -0.0051.. (CI upper bounds) | False |
| 4 | null UCB <= 0.1 for Arms 2-5, 4a | worst 0.060 | True |
| 5 | neighbours: loss upper bound within 3% | rho0: worst-case loss 7.00%; d50: worst-case loss 3.55%; b0.5: worst-case loss 12.68% | False |

## Verdict: **FAIL (criteria failed: 1, 3)**

## Interaction I = (J_00 - J_11) - [(J_00 - J_10) + (J_00 - J_01)]
J_00 Markov-LR/existing acquisition, J_10 Gap-Mix/existing, J_01 Markov-LR/Gap-Mix+ governor (E_t from its own e-process, uniform alternative weights), J_11 Gap-Mix/Gap-Mix+. Positive = synergy.

Pooled target: I = +0.0102 [+0.0071, +0.0130]

## Arm 4 vs every other arm (pooled target)

| reference | ref mean J/T | diff [CI] | rel. gain [CI] |
|---|---|---|---|
| Arm1 Markov-LR/DSS-acq | 0.5109 | -0.0694 [-0.0722, -0.0668] | 13.59% [13.08, 14.12] |
| Arm2 Gap-Mix/DSS-acq | 0.4490 | -0.0075 [-0.0100, -0.0050] | 1.66% [1.11, 2.22] |
| Arm3 Gap-Mix/PAVE | 0.4493 | -0.0078 [-0.0103, -0.0051] | 1.73% [1.15, 2.30] |
| Arm5 Gap-Mix/fixed pacing | 0.4450 | -0.0035 [-0.0056, -0.0014] | 0.79% [0.31, 1.26] |
| Arm4a (evidence frozen) | 0.4468 | -0.0053 [-0.0074, -0.0032] | 1.19% [0.72, 1.65] |
| Markov-LR+Gap-Mix+ governor | 0.5137 | -0.0721 [-0.0748, -0.0694] | 14.05% [13.54, 14.56] |
| QSG-envelope evidence | 0.4879 | -0.0463 [-0.0489, -0.0438] | 9.50% [9.00, 10.00] |
| gap-10 thinning | 0.4303 | +0.0112 [+0.0083, +0.0142] | -2.61% [-3.31, -1.92] |
| episode_front | 0.4026 | +0.0389 [+0.0357, +0.0419] | -9.66% [-10.45, -8.84] |
| uniform | 0.4419 | -0.0004 [-0.0028, +0.0020] | 0.09% [-0.46, 0.64] |

## Per-cell table (mean over seeds): J/T; detection rate; delay (rounds, detected only); queries; false-promotion rate

| cell | class | J Arm1 | J Arm2 | J Arm3 | J Arm4 | J Arm5 | J Arm4arozen | best comparator | Arm4 det | Arm2 det | Arm4 delay | Arm2 delay | Arm4 q | Arm2 q |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| f3_rho0.5_on0.3_L1_medium_harmful_d10_b0.05_s0.1 | target | 0.5775 | 0.5728 | 0.5728 | 0.5690 | 0.5668 | 0.5671 | Arm5 Gap-Mix/fixed pacing | 0.17 | 0.07 | 510 | 472 | 49.8 | 46.3 |
| f3_rho0.5_on0.3_L1_medium_harmful_d10_b0.1_s0.1 | target | 0.5700 | 0.5562 | 0.5562 | 0.5738 | 0.5700 | 0.5699 | Arm3 Gap-Mix/PAVE | 0.18 | 0.37 | 540 | 445 | 99.8 | 82.6 |
| f3_rho0.5_on0.3_L1_medium_harmful_d10_b0.25_s0.1 | target | 0.5741 | 0.5722 | 0.5727 | 0.5738 | 0.5739 | 0.5762 | gap-10 thinning | 0.32 | 0.35 | 462 | 521 | 250.0 | 250.0 |
| f3_rho0.5_on0.3_L1_medium_harmful_d10_b0.5_s0.1 | b0.5 | 0.5783 | 0.5779 | 0.5755 | 0.5784 | 0.5774 | 0.5788 | gap-10 thinning | 0.60 | 0.55 | 471 | 483 | 500.0 | 500.0 |
| f3_rho0.5_on0.3_L1_medium_harmful_d1_b0.05_s0.1 | target | 0.5801 | 0.5801 | 0.5801 | 0.5663 | 0.5599 | 0.5711 | Arm5 Gap-Mix/fixed pacing | 0.20 | 0.02 | 452 | 441 | 49.6 | 46.3 |
| f3_rho0.5_on0.3_L1_medium_harmful_d1_b0.1_s0.1 | target | 0.5676 | 0.5683 | 0.5683 | 0.5749 | 0.5735 | 0.5641 | gap-10 thinning | 0.17 | 0.25 | 530 | 473 | 99.7 | 89.8 |
| f3_rho0.5_on0.3_L1_medium_harmful_d1_b0.25_s0.1 | target | 0.5788 | 0.5661 | 0.5661 | 0.5643 | 0.5683 | 0.5737 | Arm3 Gap-Mix/PAVE | 0.53 | 0.42 | 529 | 489 | 245.8 | 144.8 |
| f3_rho0.5_on0.3_L1_medium_harmful_d1_b0.5_s0.1 | b0.5 | 0.5771 | 0.5663 | 0.5663 | 0.5695 | 0.5767 | 0.5689 | gap-10 thinning | 0.47 | 0.52 | 496 | 449 | 494.6 | 185.4 |
| f3_rho0.5_on0.3_L1_medium_harmful_d50_b0.05_s0.1 | d50 | 0.5821 | 0.5758 | 0.5655 | 0.5785 | 0.5749 | 0.5770 | Arm3 Gap-Mix/PAVE | 0.07 | 0.20 | 570 | 559 | 50.0 | 50.0 |
| f3_rho0.5_on0.3_L1_medium_harmful_d50_b0.1_s0.1 | d50 | 0.5866 | 0.5781 | 0.5815 | 0.5779 | 0.5752 | 0.5778 | Arm5 Gap-Mix/fixed pacing | 0.25 | 0.23 | 459 | 523 | 100.0 | 100.0 |
| f3_rho0.5_on0.3_L1_medium_harmful_d50_b0.25_s0.1 | d50 | 0.5717 | 0.5716 | 0.5753 | 0.5743 | 0.5686 | 0.5743 | Arm5 Gap-Mix/fixed pacing | 0.35 | 0.32 | 560 | 534 | 250.0 | 250.0 |
| f3_rho0.5_on0.3_L1_strong_harmful_d10_b0.05_s0.1 | target | 0.6378 | 0.3989 | 0.3989 | 0.4361 | 0.4382 | 0.4409 | Arm3 Gap-Mix/PAVE | 0.97 | 0.95 | 375 | 348 | 47.0 | 40.6 |
| f3_rho0.5_on0.3_L1_strong_harmful_d10_b0.1_s0.1 | target | 0.5065 | 0.4058 | 0.4058 | 0.3473 | 0.3694 | 0.3482 | gap-10 thinning | 1.00 | 1.00 | 277 | 342 | 87.7 | 55.3 |
| f3_rho0.5_on0.3_L1_strong_harmful_d10_b0.25_s0.1 | target | 0.5250 | 0.4766 | 0.4527 | 0.4598 | 0.4532 | 0.4637 | gap-10 thinning | 1.00 | 1.00 | 279 | 278 | 250.0 | 250.0 |
| f3_rho0.5_on0.3_L1_strong_harmful_d10_b0.5_s0.1 | b0.5 | 0.5482 | 0.5431 | 0.4723 | 0.5403 | 0.5584 | 0.5517 | gap-10 thinning | 1.00 | 1.00 | 291 | 289 | 500.0 | 500.0 |
| f3_rho0.5_on0.3_L1_strong_harmful_d1_b0.05_s0.1 | target | 0.6215 | 0.4058 | 0.4058 | 0.4399 | 0.4277 | 0.4524 | Arm3 Gap-Mix/PAVE | 0.95 | 0.88 | 396 | 311 | 46.9 | 40.9 |
| f3_rho0.5_on0.3_L1_strong_harmful_d1_b0.1_s0.1 | target | 0.5022 | 0.3798 | 0.3798 | 0.3557 | 0.3494 | 0.3582 | gap-10 thinning | 1.00 | 1.00 | 282 | 330 | 87.9 | 55.1 |
| f3_rho0.5_on0.3_L1_strong_harmful_d1_b0.25_s0.1 | target | 0.5311 | 0.4036 | 0.4036 | 0.3560 | 0.3421 | 0.3752 | gap-10 thinning | 1.00 | 1.00 | 267 | 315 | 215.4 | 92.8 |
| f3_rho0.5_on0.3_L1_strong_harmful_d1_b0.5_s0.1 | b0.5 | 0.5270 | 0.3823 | 0.3823 | 0.4213 | 0.3808 | 0.4035 | gap-10 thinning | 1.00 | 1.00 | 280 | 240 | 437.0 | 144.5 |
| f3_rho0.5_on0.3_L1_strong_harmful_d50_b0.05_s0.1 | d50 | 0.6634 | 0.4460 | 0.4589 | 0.4317 | 0.4559 | 0.4524 | gap-10 thinning | 0.88 | 0.87 | 379 | 381 | 50.0 | 50.0 |
| f3_rho0.5_on0.3_L1_strong_harmful_d50_b0.1_s0.1 | d50 | 0.5799 | 0.4382 | 0.4586 | 0.4462 | 0.4202 | 0.4430 | Arm5 Gap-Mix/fixed pacing | 1.00 | 1.00 | 327 | 326 | 100.0 | 100.0 |
| f3_rho0.5_on0.3_L1_strong_harmful_d50_b0.25_s0.1 | d50 | 0.5177 | 0.4693 | 0.4979 | 0.4799 | 0.4828 | 0.4830 | gap-10 thinning | 1.00 | 1.00 | 285 | 295 | 250.0 | 250.0 |
| f3_rho0.5_on0.6_L1_medium_harmful_d10_b0.05_s0.1 | target | 0.4556 | 0.4535 | 0.4535 | 0.4569 | 0.4558 | 0.4569 | Arm3 Gap-Mix/PAVE | 0.02 | 0.05 | 379 | 191 | 50.0 | 39.7 |
| f3_rho0.5_on0.6_L1_medium_harmful_d10_b0.1_s0.1 | target | 0.4614 | 0.4601 | 0.4601 | 0.4610 | 0.4604 | 0.4599 | gap-10 thinning | 0.05 | 0.12 | 393 | 351 | 100.0 | 58.9 |
| f3_rho0.5_on0.6_L1_medium_harmful_d10_b0.25_s0.1 | target | 0.4547 | 0.4559 | 0.4553 | 0.4562 | 0.4557 | 0.4566 | gap-10 thinning | 0.03 | 0.03 | 318 | 299 | 250.0 | 250.0 |
| f3_rho0.5_on0.6_L1_medium_harmful_d10_b0.5_s0.1 | b0.5 | 0.4695 | 0.4696 | 0.4661 | 0.4695 | 0.4670 | 0.4691 | gap-10 thinning | 0.17 | 0.20 | 334 | 338 | 500.0 | 500.0 |
| f3_rho0.5_on0.6_L1_medium_harmful_d1_b0.05_s0.1 | target | 0.4620 | 0.4603 | 0.4603 | 0.4607 | 0.4622 | 0.4608 | Arm3 Gap-Mix/PAVE | 0.07 | 0.02 | 342 | 183 | 50.0 | 32.5 |
| f3_rho0.5_on0.6_L1_medium_harmful_d1_b0.1_s0.1 | target | 0.4610 | 0.4611 | 0.4611 | 0.4611 | 0.4607 | 0.4621 | gap-10 thinning | 0.03 | 0.03 | 271 | 312 | 100.0 | 60.3 |
| f3_rho0.5_on0.6_L1_medium_harmful_d1_b0.25_s0.1 | target | 0.4629 | 0.4603 | 0.4603 | 0.4628 | 0.4620 | 0.4618 | Arm3 Gap-Mix/PAVE | 0.12 | 0.10 | 338 | 336 | 249.9 | 101.1 |
| f3_rho0.5_on0.6_L1_medium_harmful_d1_b0.5_s0.1 | b0.5 | 0.4577 | 0.4571 | 0.4571 | 0.4596 | 0.4555 | 0.4586 | Arm5 Gap-Mix/fixed pacing | 0.08 | 0.08 | 318 | 322 | 499.4 | 149.3 |
| f3_rho0.5_on0.6_L1_medium_harmful_d50_b0.05_s0.1 | d50 | 0.4602 | 0.4601 | 0.4602 | 0.4602 | 0.4594 | 0.4602 | gap-10 thinning | 0.00 | 0.03 | nan | 424 | 50.0 | 50.0 |
| f3_rho0.5_on0.6_L1_medium_harmful_d50_b0.1_s0.1 | d50 | 0.4609 | 0.4587 | 0.4604 | 0.4595 | 0.4607 | 0.4594 | Arm2 Gap-Mix/DSS-acq | 0.07 | 0.07 | 370 | 342 | 100.0 | 100.0 |
| f3_rho0.5_on0.6_L1_medium_harmful_d50_b0.25_s0.1 | d50 | 0.4580 | 0.4589 | 0.4577 | 0.4594 | 0.4584 | 0.4596 | gap-10 thinning | 0.03 | 0.03 | 355 | 370 | 250.0 | 250.0 |
| f3_rho0.5_on0.6_L1_strong_harmful_d10_b0.05_s0.1 | target | 0.4184 | 0.3538 | 0.3538 | 0.3961 | 0.3988 | 0.3951 | Arm3 Gap-Mix/PAVE | 0.37 | 0.77 | 332 | 290 | 49.8 | 34.9 |
| f3_rho0.5_on0.6_L1_strong_harmful_d10_b0.1_s0.1 | target | 0.4226 | 0.3704 | 0.3704 | 0.3460 | 0.3414 | 0.3533 | gap-10 thinning | 0.87 | 0.77 | 286 | 316 | 97.0 | 46.8 |
| f3_rho0.5_on0.6_L1_strong_harmful_d10_b0.25_s0.1 | target | 0.3650 | 0.3414 | 0.3607 | 0.3397 | 0.3462 | 0.3469 | gap-10 thinning | 0.95 | 0.98 | 256 | 262 | 250.0 | 250.0 |
| f3_rho0.5_on0.6_L1_strong_harmful_d10_b0.5_s0.1 | b0.5 | 0.3659 | 0.3694 | 0.3780 | 0.3759 | 0.3635 | 0.3741 | gap-10 thinning | 0.98 | 0.98 | 276 | 271 | 500.0 | 500.0 |
| f3_rho0.5_on0.6_L1_strong_harmful_d1_b0.05_s0.1 | target | 0.4169 | 0.3489 | 0.3489 | 0.4080 | 0.4193 | 0.4088 | Arm3 Gap-Mix/PAVE | 0.42 | 0.78 | 356 | 288 | 49.9 | 36.2 |
| f3_rho0.5_on0.6_L1_strong_harmful_d1_b0.1_s0.1 | target | 0.4159 | 0.3561 | 0.3561 | 0.3423 | 0.3414 | 0.3496 | gap-10 thinning | 0.87 | 0.87 | 280 | 306 | 95.5 | 51.7 |
| f3_rho0.5_on0.6_L1_strong_harmful_d1_b0.25_s0.1 | target | 0.4236 | 0.3583 | 0.3583 | 0.3180 | 0.3172 | 0.3181 | Arm5 Gap-Mix/fixed pacing | 0.97 | 0.88 | 256 | 300 | 234.3 | 81.5 |
| f3_rho0.5_on0.6_L1_strong_harmful_d1_b0.5_s0.1 | b0.5 | 0.4195 | 0.3401 | 0.3401 | 0.3514 | 0.3223 | 0.3221 | gap-10 thinning | 0.93 | 0.87 | 285 | 258 | 477.2 | 135.1 |
| f3_rho0.5_on0.6_L1_strong_harmful_d50_b0.05_s0.1 | d50 | 0.4225 | 0.4102 | 0.3836 | 0.4064 | 0.4163 | 0.4064 | Arm3 Gap-Mix/PAVE | 0.25 | 0.52 | 344 | 379 | 50.0 | 50.0 |
| f3_rho0.5_on0.6_L1_strong_harmful_d50_b0.1_s0.1 | d50 | 0.4225 | 0.3646 | 0.3672 | 0.3591 | 0.3646 | 0.3591 | Arm2 Gap-Mix/DSS-acq | 0.75 | 0.80 | 294 | 303 | 100.0 | 100.0 |
| f3_rho0.5_on0.6_L1_strong_harmful_d50_b0.25_s0.1 | d50 | 0.3792 | 0.3619 | 0.3531 | 0.3570 | 0.3499 | 0.3528 | gap-10 thinning | 0.92 | 0.92 | 296 | 299 | 250.0 | 250.0 |
| f3_rho0.8_on0.3_L1_medium_harmful_d10_b0.05_s0.1 | target | 0.5750 | 0.5731 | 0.5731 | 0.5676 | 0.5628 | 0.5630 | Arm5 Gap-Mix/fixed pacing | 0.13 | 0.03 | 439 | 352 | 49.9 | 42.9 |
| f3_rho0.8_on0.3_L1_medium_harmful_d10_b0.1_s0.1 | target | 0.5715 | 0.5645 | 0.5645 | 0.5645 | 0.5645 | 0.5683 | gap-10 thinning | 0.35 | 0.33 | 442 | 440 | 99.3 | 79.6 |
| f3_rho0.8_on0.3_L1_medium_harmful_d10_b0.25_s0.1 | target | 0.5858 | 0.5811 | 0.5780 | 0.5814 | 0.5842 | 0.5837 | gap-10 thinning | 0.27 | 0.32 | 510 | 506 | 250.0 | 250.0 |
| f3_rho0.8_on0.3_L1_medium_harmful_d10_b0.5_s0.1 | b0.5 | 0.5843 | 0.5834 | 0.5765 | 0.5837 | 0.5794 | 0.5831 | gap-10 thinning | 0.17 | 0.18 | 492 | 479 | 500.0 | 500.0 |
| f3_rho0.8_on0.3_L1_medium_harmful_d1_b0.05_s0.1 | target | 0.5829 | 0.5671 | 0.5671 | 0.5545 | 0.5674 | 0.5603 | Arm3 Gap-Mix/PAVE | 0.32 | 0.17 | 379 | 440 | 49.3 | 41.0 |
| f3_rho0.8_on0.3_L1_medium_harmful_d1_b0.1_s0.1 | target | 0.5821 | 0.5638 | 0.5638 | 0.5595 | 0.5640 | 0.5666 | gap-10 thinning | 0.35 | 0.27 | 423 | 418 | 98.8 | 80.2 |
| f3_rho0.8_on0.3_L1_medium_harmful_d1_b0.25_s0.1 | target | 0.5745 | 0.5658 | 0.5658 | 0.5684 | 0.5715 | 0.5676 | gap-10 thinning | 0.22 | 0.32 | 442 | 459 | 249.2 | 143.7 |
| f3_rho0.8_on0.3_L1_medium_harmful_d1_b0.5_s0.1 | b0.5 | 0.5738 | 0.5659 | 0.5659 | 0.5671 | 0.5683 | 0.5643 | gap-10 thinning | 0.33 | 0.30 | 362 | 432 | 498.6 | 186.3 |
| f3_rho0.8_on0.3_L1_medium_harmful_d50_b0.05_s0.1 | d50 | 0.5706 | 0.5600 | 0.5639 | 0.5586 | 0.5608 | 0.5581 | gap-10 thinning | 0.17 | 0.17 | 464 | 422 | 50.0 | 50.0 |
| f3_rho0.8_on0.3_L1_medium_harmful_d50_b0.1_s0.1 | d50 | 0.5801 | 0.5715 | 0.5699 | 0.5706 | 0.5701 | 0.5725 | Arm3 Gap-Mix/PAVE | 0.17 | 0.22 | 450 | 562 | 100.0 | 100.0 |
| f3_rho0.8_on0.3_L1_medium_harmful_d50_b0.25_s0.1 | d50 | 0.5965 | 0.5893 | 0.5805 | 0.5908 | 0.5883 | 0.5897 | gap-10 thinning | 0.30 | 0.32 | 438 | 445 | 250.0 | 250.0 |
| f3_rho0.8_on0.3_L1_strong_harmful_d10_b0.05_s0.1 | target | 0.6671 | 0.3996 | 0.3996 | 0.4080 | 0.4398 | 0.4410 | Arm3 Gap-Mix/PAVE | 0.97 | 0.93 | 343 | 322 | 45.9 | 38.1 |
| f3_rho0.8_on0.3_L1_strong_harmful_d10_b0.1_s0.1 | target | 0.6117 | 0.3905 | 0.3905 | 0.3495 | 0.3548 | 0.3801 | gap-10 thinning | 1.00 | 1.00 | 261 | 341 | 87.0 | 52.0 |
| f3_rho0.8_on0.3_L1_strong_harmful_d10_b0.25_s0.1 | target | 0.6060 | 0.4559 | 0.4428 | 0.4638 | 0.4635 | 0.4709 | gap-10 thinning | 1.00 | 1.00 | 174 | 163 | 250.0 | 250.0 |
| f3_rho0.8_on0.3_L1_strong_harmful_d10_b0.5_s0.1 | b0.5 | 0.6207 | 0.5013 | 0.4241 | 0.4999 | 0.5070 | 0.4969 | gap-10 thinning | 1.00 | 1.00 | 161 | 160 | 500.0 | 500.0 |
| f3_rho0.8_on0.3_L1_strong_harmful_d1_b0.05_s0.1 | target | 0.6499 | 0.4550 | 0.4550 | 0.4239 | 0.4567 | 0.4517 | gap-10 thinning | 0.97 | 0.73 | 380 | 329 | 46.3 | 41.7 |
| f3_rho0.8_on0.3_L1_strong_harmful_d1_b0.1_s0.1 | target | 0.6141 | 0.3924 | 0.3924 | 0.3186 | 0.3452 | 0.3370 | gap-10 thinning | 1.00 | 0.98 | 251 | 341 | 82.8 | 53.8 |
| f3_rho0.8_on0.3_L1_strong_harmful_d1_b0.25_s0.1 | target | 0.6161 | 0.3955 | 0.3955 | 0.3021 | 0.3269 | 0.3313 | Arm5 Gap-Mix/fixed pacing | 1.00 | 1.00 | 188 | 317 | 202.5 | 91.0 |
| f3_rho0.8_on0.3_L1_strong_harmful_d1_b0.5_s0.1 | b0.5 | 0.6337 | 0.4019 | 0.4019 | 0.3469 | 0.3686 | 0.3436 | gap-10 thinning | 1.00 | 1.00 | 170 | 232 | 425.3 | 148.5 |
| f3_rho0.8_on0.3_L1_strong_harmful_d50_b0.05_s0.1 | d50 | 0.6626 | 0.4549 | 0.4591 | 0.4334 | 0.4790 | 0.4586 | gap-10 thinning | 0.95 | 0.98 | 385 | 396 | 50.0 | 50.0 |
| f3_rho0.8_on0.3_L1_strong_harmful_d50_b0.1_s0.1 | d50 | 0.6193 | 0.4227 | 0.4805 | 0.4258 | 0.4237 | 0.4236 | Arm2 Gap-Mix/DSS-acq | 1.00 | 1.00 | 333 | 315 | 100.0 | 100.0 |
| f3_rho0.8_on0.3_L1_strong_harmful_d50_b0.25_s0.1 | d50 | 0.6084 | 0.4804 | 0.4927 | 0.4657 | 0.4699 | 0.4751 | gap-10 thinning | 1.00 | 1.00 | 222 | 226 | 250.0 | 250.0 |
| f3_rho0.8_on0.6_L1_medium_harmful_d10_b0.05_s0.1 | target | 0.4726 | 0.4699 | 0.4699 | 0.4711 | 0.4712 | 0.4711 | Arm3 Gap-Mix/PAVE | 0.07 | 0.08 | 361 | 310 | 50.0 | 36.0 |
| f3_rho0.8_on0.6_L1_medium_harmful_d10_b0.1_s0.1 | target | 0.4519 | 0.4504 | 0.4504 | 0.4493 | 0.4498 | 0.4495 | gap-10 thinning | 0.10 | 0.10 | 317 | 270 | 99.9 | 50.1 |
| f3_rho0.8_on0.6_L1_medium_harmful_d10_b0.25_s0.1 | target | 0.4635 | 0.4609 | 0.4551 | 0.4597 | 0.4574 | 0.4595 | gap-10 thinning | 0.22 | 0.18 | 294 | 265 | 250.0 | 250.0 |
| f3_rho0.8_on0.6_L1_medium_harmful_d10_b0.5_s0.1 | b0.5 | 0.4574 | 0.4560 | 0.4531 | 0.4565 | 0.4545 | 0.4571 | Arm3 Gap-Mix/PAVE | 0.05 | 0.08 | 216 | 212 | 500.0 | 500.0 |
| f3_rho0.8_on0.6_L1_medium_harmful_d1_b0.05_s0.1 | target | 0.4610 | 0.4592 | 0.4592 | 0.4603 | 0.4596 | 0.4609 | Arm3 Gap-Mix/PAVE | 0.05 | 0.05 | 327 | 292 | 50.0 | 35.8 |
| f3_rho0.8_on0.6_L1_medium_harmful_d1_b0.1_s0.1 | target | 0.4611 | 0.4591 | 0.4591 | 0.4558 | 0.4587 | 0.4577 | gap-10 thinning | 0.08 | 0.07 | 288 | 350 | 99.7 | 56.2 |
| f3_rho0.8_on0.6_L1_medium_harmful_d1_b0.25_s0.1 | target | 0.4682 | 0.4657 | 0.4657 | 0.4674 | 0.4677 | 0.4651 | Arm3 Gap-Mix/PAVE | 0.10 | 0.08 | 290 | 253 | 249.5 | 100.2 |
| f3_rho0.8_on0.6_L1_medium_harmful_d1_b0.5_s0.1 | b0.5 | 0.4585 | 0.4522 | 0.4522 | 0.4566 | 0.4517 | 0.4546 | Arm5 Gap-Mix/fixed pacing | 0.22 | 0.17 | 247 | 282 | 499.4 | 148.1 |
| f3_rho0.8_on0.6_L1_medium_harmful_d50_b0.05_s0.1 | d50 | 0.4567 | 0.4537 | 0.4523 | 0.4553 | 0.4567 | 0.4553 | gap-10 thinning | 0.03 | 0.05 | 340 | 302 | 50.0 | 50.0 |
| f3_rho0.8_on0.6_L1_medium_harmful_d50_b0.1_s0.1 | d50 | 0.4613 | 0.4589 | 0.4578 | 0.4598 | 0.4575 | 0.4592 | Arm5 Gap-Mix/fixed pacing | 0.12 | 0.07 | 344 | 339 | 100.0 | 100.0 |
| f3_rho0.8_on0.6_L1_medium_harmful_d50_b0.25_s0.1 | d50 | 0.4656 | 0.4644 | 0.4616 | 0.4608 | 0.4632 | 0.4625 | gap-10 thinning | 0.10 | 0.12 | 336 | 295 | 250.0 | 250.0 |
| f3_rho0.8_on0.6_L1_strong_harmful_d10_b0.05_s0.1 | target | 0.4162 | 0.3357 | 0.3357 | 0.3923 | 0.4033 | 0.3946 | Arm3 Gap-Mix/PAVE | 0.50 | 0.78 | 348 | 266 | 50.0 | 33.4 |
| f3_rho0.8_on0.6_L1_strong_harmful_d10_b0.1_s0.1 | target | 0.4256 | 0.3701 | 0.3701 | 0.3314 | 0.3337 | 0.3318 | gap-10 thinning | 0.90 | 0.80 | 274 | 312 | 96.3 | 47.0 |
| f3_rho0.8_on0.6_L1_strong_harmful_d10_b0.25_s0.1 | target | 0.4201 | 0.3290 | 0.3701 | 0.3290 | 0.3467 | 0.3380 | gap-10 thinning | 0.98 | 0.97 | 193 | 182 | 250.0 | 250.0 |
| f3_rho0.8_on0.6_L1_strong_harmful_d10_b0.5_s0.1 | b0.5 | 0.4122 | 0.3312 | 0.3531 | 0.3340 | 0.3359 | 0.3310 | gap-10 thinning | 0.98 | 0.98 | 167 | 166 | 500.0 | 500.0 |
| f3_rho0.8_on0.6_L1_strong_harmful_d1_b0.05_s0.1 | target | 0.4112 | 0.3580 | 0.3580 | 0.3992 | 0.4071 | 0.3966 | Arm3 Gap-Mix/PAVE | 0.33 | 0.67 | 358 | 277 | 49.9 | 38.0 |
| f3_rho0.8_on0.6_L1_strong_harmful_d1_b0.1_s0.1 | target | 0.4184 | 0.3673 | 0.3673 | 0.3250 | 0.3322 | 0.3341 | gap-10 thinning | 0.82 | 0.75 | 257 | 309 | 94.8 | 51.5 |
| f3_rho0.8_on0.6_L1_strong_harmful_d1_b0.25_s0.1 | target | 0.4263 | 0.3552 | 0.3552 | 0.2646 | 0.2589 | 0.2774 | Arm5 Gap-Mix/fixed pacing | 0.98 | 0.87 | 170 | 292 | 224.7 | 81.6 |
| f3_rho0.8_on0.6_L1_strong_harmful_d1_b0.5_s0.1 | b0.5 | 0.4187 | 0.3214 | 0.3214 | 0.2813 | 0.3033 | 0.2906 | gap-10 thinning | 0.98 | 0.97 | 165 | 234 | 456.4 | 134.3 |
| f3_rho0.8_on0.6_L1_strong_harmful_d50_b0.05_s0.1 | d50 | 0.4197 | 0.4104 | 0.3896 | 0.4104 | 0.4148 | 0.4104 | gap-10 thinning | 0.15 | 0.52 | 351 | 381 | 50.0 | 50.0 |
| f3_rho0.8_on0.6_L1_strong_harmful_d50_b0.1_s0.1 | d50 | 0.4209 | 0.3535 | 0.3843 | 0.3524 | 0.3515 | 0.3558 | Arm5 Gap-Mix/fixed pacing | 0.82 | 0.82 | 302 | 307 | 100.0 | 100.0 |
| f3_rho0.8_on0.6_L1_strong_harmful_d50_b0.25_s0.1 | d50 | 0.4253 | 0.3201 | 0.3536 | 0.3230 | 0.3322 | 0.3301 | Arm2 Gap-Mix/DSS-acq | 0.98 | 1.00 | 230 | 223 | 250.0 | 250.0 |
| f3_rho0_on0.3_L1_medium_harmful_d10_b0.05_s0.1 | rho0 | 0.5842 | 0.5842 | 0.5842 | 0.5712 | 0.5749 | 0.5746 | Arm5 Gap-Mix/fixed pacing | 0.17 | 0.00 | 420 | nan | 49.8 | 47.9 |
| f3_rho0_on0.3_L1_medium_harmful_d10_b0.1_s0.1 | rho0 | 0.5748 | 0.5728 | 0.5728 | 0.5577 | 0.5695 | 0.5661 | gap-10 thinning | 0.32 | 0.27 | 481 | 520 | 98.7 | 88.9 |
| f3_rho0_on0.3_L1_medium_harmful_d10_b0.25_s0.1 | rho0 | 0.5715 | 0.5731 | 0.5736 | 0.5726 | 0.5765 | 0.5762 | gap-10 thinning | 0.53 | 0.63 | 486 | 473 | 250.0 | 250.0 |
| f3_rho0_on0.3_L1_medium_harmful_d1_b0.05_s0.1 | rho0 | 0.5736 | 0.5749 | 0.5749 | 0.5712 | 0.5645 | 0.5699 | Arm5 Gap-Mix/fixed pacing | 0.12 | 0.03 | 499 | 342 | 49.8 | 44.2 |
| f3_rho0_on0.3_L1_medium_harmful_d1_b0.1_s0.1 | rho0 | 0.5677 | 0.5579 | 0.5579 | 0.5768 | 0.5662 | 0.5678 | Arm3 Gap-Mix/PAVE | 0.08 | 0.35 | 433 | 447 | 99.8 | 87.9 |
| f3_rho0_on0.3_L1_medium_harmful_d1_b0.25_s0.1 | rho0 | 0.5709 | 0.5616 | 0.5616 | 0.5608 | 0.5610 | 0.5691 | gap-10 thinning | 0.53 | 0.47 | 474 | 458 | 247.9 | 145.4 |
| f3_rho0_on0.3_L1_strong_harmful_d10_b0.05_s0.1 | rho0 | 0.6170 | 0.3793 | 0.3793 | 0.4343 | 0.4036 | 0.4027 | Arm3 Gap-Mix/PAVE | 0.93 | 0.98 | 353 | 328 | 46.7 | 39.6 |
| f3_rho0_on0.3_L1_strong_harmful_d10_b0.1_s0.1 | rho0 | 0.5118 | 0.3860 | 0.3860 | 0.3556 | 0.3473 | 0.3617 | gap-10 thinning | 1.00 | 1.00 | 291 | 345 | 87.3 | 52.1 |
| f3_rho0_on0.3_L1_strong_harmful_d10_b0.25_s0.1 | rho0 | 0.4801 | 0.4543 | 0.4573 | 0.4448 | 0.4590 | 0.4672 | gap-10 thinning | 1.00 | 1.00 | 262 | 282 | 250.0 | 250.0 |
| f3_rho0_on0.3_L1_strong_harmful_d1_b0.05_s0.1 | rho0 | 0.5901 | 0.4031 | 0.4031 | 0.4491 | 0.4395 | 0.4253 | Arm3 Gap-Mix/PAVE | 0.90 | 0.90 | 393 | 327 | 47.0 | 41.8 |
| f3_rho0_on0.3_L1_strong_harmful_d1_b0.1_s0.1 | rho0 | 0.4766 | 0.3726 | 0.3726 | 0.3791 | 0.3412 | 0.3446 | gap-10 thinning | 0.98 | 1.00 | 308 | 324 | 91.8 | 52.4 |
| f3_rho0_on0.3_L1_strong_harmful_d1_b0.25_s0.1 | rho0 | 0.4954 | 0.3794 | 0.3794 | 0.3734 | 0.3443 | 0.3753 | gap-10 thinning | 1.00 | 1.00 | 279 | 284 | 212.3 | 87.9 |
| f3_rho0_on0.6_L1_medium_harmful_d10_b0.05_s0.1 | rho0 | 0.4641 | 0.4636 | 0.4636 | 0.4636 | 0.4642 | 0.4636 | gap-10 thinning | 0.05 | 0.03 | 401 | 329 | 50.0 | 37.7 |
| f3_rho0_on0.6_L1_medium_harmful_d10_b0.1_s0.1 | rho0 | 0.4567 | 0.4565 | 0.4565 | 0.4562 | 0.4557 | 0.4558 | gap-10 thinning | 0.03 | 0.05 | 360 | 380 | 99.9 | 57.8 |
| f3_rho0_on0.6_L1_medium_harmful_d10_b0.25_s0.1 | rho0 | 0.4581 | 0.4596 | 0.4583 | 0.4605 | 0.4591 | 0.4601 | gap-10 thinning | 0.03 | 0.10 | 377 | 350 | 250.0 | 250.0 |
| f3_rho0_on0.6_L1_medium_harmful_d1_b0.05_s0.1 | rho0 | 0.4583 | 0.4558 | 0.4558 | 0.4562 | 0.4584 | 0.4563 | Arm3 Gap-Mix/PAVE | 0.08 | 0.03 | 349 | 212 | 50.0 | 40.2 |
| f3_rho0_on0.6_L1_medium_harmful_d1_b0.1_s0.1 | rho0 | 0.4563 | 0.4535 | 0.4535 | 0.4582 | 0.4592 | 0.4563 | gap-10 thinning | 0.05 | 0.22 | 309 | 320 | 99.9 | 64.6 |
| f3_rho0_on0.6_L1_medium_harmful_d1_b0.25_s0.1 | rho0 | 0.4654 | 0.4647 | 0.4647 | 0.4664 | 0.4661 | 0.4664 | Arm3 Gap-Mix/PAVE | 0.12 | 0.10 | 368 | 356 | 249.8 | 105.2 |
| f3_rho0_on0.6_L1_strong_harmful_d10_b0.05_s0.1 | rho0 | 0.4239 | 0.3511 | 0.3511 | 0.4011 | 0.4063 | 0.4005 | Arm3 Gap-Mix/PAVE | 0.45 | 0.72 | 346 | 282 | 49.9 | 36.7 |
| f3_rho0_on0.6_L1_strong_harmful_d10_b0.1_s0.1 | rho0 | 0.4168 | 0.3651 | 0.3651 | 0.3407 | 0.3355 | 0.3415 | gap-10 thinning | 0.82 | 0.72 | 278 | 309 | 97.2 | 45.9 |
| f3_rho0_on0.6_L1_strong_harmful_d10_b0.25_s0.1 | rho0 | 0.3435 | 0.3552 | 0.3478 | 0.3441 | 0.3388 | 0.3372 | gap-10 thinning | 1.00 | 1.00 | 268 | 275 | 250.0 | 250.0 |
| f3_rho0_on0.6_L1_strong_harmful_d1_b0.05_s0.1 | rho0 | 0.4158 | 0.3465 | 0.3465 | 0.3991 | 0.4101 | 0.3965 | Arm3 Gap-Mix/PAVE | 0.38 | 0.77 | 334 | 281 | 49.7 | 37.5 |
| f3_rho0_on0.6_L1_strong_harmful_d1_b0.1_s0.1 | rho0 | 0.4058 | 0.3570 | 0.3570 | 0.3392 | 0.3414 | 0.3460 | gap-10 thinning | 0.78 | 0.85 | 271 | 309 | 96.1 | 51.4 |
| f3_rho0_on0.6_L1_strong_harmful_d1_b0.25_s0.1 | rho0 | 0.4173 | 0.3511 | 0.3511 | 0.3236 | 0.3137 | 0.3083 | gap-10 thinning | 0.93 | 0.87 | 266 | 302 | 236.8 | 79.0 |

Pending-label inventory is not recorded in the rows (only queries and costs); not reported.

