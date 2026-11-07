# Baseline comparison across validity modes (development; nothing here is confirmation)
| mode | what it controls | winner (power, mean of 18 worlds, 5/10/20% labels) | status of the winner's guarantee |
|---|---|---|---|
| A / B: theory thresholds, finite-horizon valid | P_{H0}(τ ≤ T) ≤ α (T = 2000) | geometric-restart H2c .078 / .183 / .350, i.e. ≈ ordinary H2c .075 / .174 / .327 (the difference is within noise) and Brier-guided ONS with coarse8 at 20% labels (.344) | PROVED for fixed known delay |
| C: empirical thresholds on the G1 null | size ≈ α on that null only | **H2c with SR recursion .270 / .416 / .555** (existing SR .219 / .326 / .414) | NONE beyond the calibration null; transfer .03–.13, up to .30 under strong dependence |
| diagnostic: ARL threshold 1/α | E_{H0}[τ] ≥ 1/α | not comparable (null FA over 2000 steps = 1.000) | ARL only |
Not yet compared: a published cost-risk monitor (unavailable offline), Page–Hinkley/CUSUM on cost with matched calibration, restart-specific bets, R2/R5/R6.
