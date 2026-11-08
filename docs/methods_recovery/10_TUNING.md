# Gap-Mix+ tuning (tuning seeds only)

Seeds: gapmix_plus_tuning 101300000-101309999; 48 target-family cells x 8 seeds (seed = 101300000 + 100*cell_index + k).
Metric: equal-weight mean over cells of mean J/T (lower is better). No eval seed has been run.

Design note (recorded for honesty): the Arm 4 grid was shifted once, before the real tuning run, after an
8-cell x 1-seed smoke on tuning seeds showed the best configs at the old grid edge (kappa=2, phi=1.5):
old grid kappa{0.5,1,2} x phi{0.75,1,1.5} x omega{0,.5,1}; used grid kappa{1,2,4} x phi{1,1.5,2.5} x omega{0,.5,1}.
Both grids have 27 configs (<= 30).

Reference on tuning seeds: Gap-Mix with existing acquisition (Arm 2) mean J/T = 0.4419.

## Arm 4 (Gap-Mix+, 3 parameters, 27 configs)

| config (kappa_phi_omega) | mean J/T |
|---|---|
| k4_p1_w0 **(chosen)** | 0.4386 |
| k4_p2.5_w0.5 | 0.4402 |
| k4_p1_w1 | 0.4404 |
| k4_p1_w0.5 | 0.4408 |
| k2_p1.5_w0 | 0.4418 |
| k4_p1.5_w0 | 0.4425 |
| k4_p1.5_w1 | 0.4429 |
| k2_p1_w1 | 0.4431 |
| k4_p1.5_w0.5 | 0.4432 |
| k2_p1.5_w0.5 | 0.4434 |
| k4_p2.5_w1 | 0.4436 |
| k2_p1.5_w1 | 0.4459 |
| k2_p1_w0.5 | 0.4465 |
| k2_p2.5_w1 | 0.4466 |
| k4_p2.5_w0 | 0.4468 |
| k2_p1_w0 | 0.4473 |
| k2_p2.5_w0 | 0.4489 |
| k2_p2.5_w0.5 | 0.4526 |
| k1_p1.5_w0 | 0.4604 |
| k1_p1_w0 | 0.4605 |
| k1_p1.5_w1 | 0.4608 |
| k1_p2.5_w0 | 0.4613 |
| k1_p1.5_w0.5 | 0.4623 |
| k1_p2.5_w1 | 0.4652 |
| k1_p2.5_w0.5 | 0.4653 |
| k1_p1_w1 | 0.4666 |
| k1_p1_w0.5 | 0.4668 |

## Arm 5 (fixed pacing, 32 configs per family, >= Arm 4's 27)

Pooled over all families (information only):

| config | mean J/T |
|---|---|
| f1 | 0.4434 |
| f0.9 | 0.4444 |
| f0.7 | 0.4499 |
| f1.2 | 0.4534 |
| f0.8 | 0.4542 |
| f1.5 | 0.4572 |
| G15 | 0.4589 |
| G10 | 0.4615 |
| G8 | 0.4639 |
| G12 | 0.4661 |

Chosen per (B/T, d) family:

| family | chosen | best J/T | 2nd best |
|---|---|---|---|
| b0.05_d1 | f0.9 | 0.4528 | f0.7 (0.4531) |
| b0.05_d10 | G20 | 0.4698 | f1 (0.4698) |
| b0.1_d1 | G10 | 0.4352 | f1 (0.4352) |
| b0.1_d10 | G10 | 0.4221 | f1 (0.4221) |
| b0.25_d1 | G4 | 0.4101 | f0.9 (0.4101) |
| b0.25_d10 | G6 | 0.4626 | f1.5 (0.4626) |

## Frozen config

`configs/methods_recovery/gapmix_plus_frozen.json`, sha256 `1010a0f9a3079b7a17b6fc10bfc1e104c4413d37da3bccb7e04ec59875980fe4`.

```json
{
  "arm4": "k4_p1_w0",
  "arm5": {
    "b0.05_d1": "f0.9",
    "b0.05_d10": "G20",
    "b0.1_d1": "G10",
    "b0.1_d10": "G10",
    "b0.25_d1": "G4",
    "b0.25_d10": "G6"
  },
  "note": "chosen on tuning seeds 101300000-101309999 only; Arm 4 global (equal-weight cell mean J/T); Arm 5 per (B/T,d) family"
}
```

Arm 4 chosen: `k4_p1_w0` (kappa, phi, omega) = k4_p1_w0. Ablation 4a and the Markov-LR hybrid use the same parameters.

Limitation recorded before eval: the chosen Arm 4 kappa = 4 is at the upper edge of the tuned grid (and phi = 1 at the lower edge), so a larger kappa
might do slightly better; the grid was not extended again (30-configuration cap, and no further tuning after this freeze). Arm 4's tuning-seed gain over Arm 2
is small (0.4386 vs 0.4419). Arm 5 was chosen per (B/T, d) family from 32 configs, Arm 4 globally from 27 configs.
