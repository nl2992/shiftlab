## Summary (factual, descriptive; read with the tables below)

All statements are pooled over the nine datasets (equal weight), with stratified episode-bootstrap
95% intervals; the tables give the numbers. "Strongest comparators" are the five uncertified
comparators with lowest pooled mean cost (wald_l0.97_g0.2, smarg_l0.97_k0.2, hoef_l0.9_g0.45,
gongT_w800_m20, dwell_l0.97_s3). Nothing was tuned or rerun. These are retrospective descriptive
scores, not confirmatory evidence.

- **Decision harm vs the frozen incumbent.** Both arms beat never-switch on pooled cost (arm B
  harm_all -114.4, arm R -117.5; negative is better), driven mainly by sf_311 and dc_311. They
  capture 0.613 (B) and 0.661 (R) of the hindsight best-fixed-model improvement on challenger-better
  episodes. Arm R is indistinguishable from wald_l0.97_g0.2 and smarg_l0.97_k0.2 on harm_all and capture
  (intervals include 0), lower-cost than hoef_l0.9_g0.45, gongT_w800_m20 and dwell_l0.97_s3, and
  better than 23 of 25 uncertified comparators with none significantly better. Arm B is significantly worse than wald_l0.97_g0.2,
  smarg_l0.97_k0.2 and hoef_l0.9_g0.45 on harm_all (+3.05, +2.99, +2.05) and better than 19 of 25.
  On the episodes where the challenger is not better, both arms pay a real cost for adapting
  (harm_N: B +28.5, R +22.7); the strongest controls pay less (wald_l0.97_g0.2 +20.3). On
  montgomery_traffic both arms are worse than never-switch (harm_all +10.9 B, +7.5 R) and arm B's
  capture is negative (-0.534).
- **Wrong-model exposure and timing.** Arm R spends 0.152 of rounds on the worse model versus 0.182
  for B; R is lower than all strongest comparators (CI excludes 0 vs each of the five), B is higher
  than wald_l0.97_g0.2, smarg_l0.97_k0.2 and dwell_l0.97_s3 and equal to the others. Time to first
  correct deployment (censored at 2000): B 237, R 209 rounds. B is faster than wald_l0.97_g0.2,
  hoef_l0.9_g0.45 and gongT_w800_m20, level with smarg_l0.97_k0.2, slower than dwell_l0.97_s3 and
  gong_zhang_paid_obs (187). R is faster than the five strongest comparators except dwell_l0.97_s3
  (level) and slower than gong_zhang_paid_obs (+21.5, CI excludes 0). B promotes
  the challenger in 99.9% of challenger-better episodes, R in 98.7% (R promotes less often than
  qiu_delayed_movement and gong_zhang_paid_obs, 100%).
- **False promotion (EQSDp looks worse).** Both arms deploy the challenger in a large share of
  episodes where it is not better: B 0.763, R 0.676 (pooled over the 8 datasets that have such
  episodes). The strongest controls are lower (wald_l0.97_g0.2 0.521, hoef_l0.9_g0.45 0.570,
  smarg_l0.97_k0.2 0.630). Arm B is significantly higher than the five strongest uncertified
  comparators except dwell_l0.97_s3, with which it is level; R is higher than all strongest
  comparators except dwell_l0.97_s3 (lower), qiu and gong_zhang (lower, i.e. better). Over all 25
  uncertified comparators, B has a lower false-promotion rate than 9, a higher one than 12; R lower than 13, higher than 10.
- **Terminal correctness.** B 0.903, R 0.942 of non-tied episodes end on the truly better model;
  R is higher than wald_l0.97_g0.2 (0.931, +0.011), smarg_l0.97_k0.2 and hoef_l0.9_g0.45, and level
  with dwell_l0.97_s3; B is lower than wald_l0.97_g0.2 (-0.028).
- **Churn and labels.** Switches per episode: B 1.67, R 1.34, versus 1.10 for wald_l0.97_g0.2 and
  1.20 for smarg_l0.97_k0.2; B switches more than wald, smarg, hoef and gongT, and is level with dwell_l0.97_s3; R switches
  more than the first four (gongT by 0.05) and less than dwell_l0.97_s3; both switch less than
  qiu (2.10) and gong_zhang (2.66). Switch cost is 1.4-1.8% of net cost
  and label cost 1.9% for every policy that uses the budget, so neither separates policies in
  magnitude. Net cost averted per paid label is 0.586 (B) and 0.603 (R), level with the strongest
  controls for R (wald_l0.97_g0.2 0.604) and 0.017 lower for B.
- **Limits.** dc_311 has no challenger-not-better episode and sf_311 has one, so false-promotion
  and harm_N rest on the other datasets and are noisy per dataset. The measures use the
  episode-level realised loss difference as truth; they do not show that any alarm or promotion
  is statistically valid, and EQSDp makes no false-promotion guarantee.
