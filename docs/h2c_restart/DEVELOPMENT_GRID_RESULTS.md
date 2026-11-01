# Development results (restart mixtures; fresh seeds 100000+; 18 harm worlds + null; 400 seeds; `outputs/h2c_restart/dev_search.csv`)
Harm worlds: concept shift δ ∈ {1.5, 2} × onset {300, 1000, 1500} × {abrupt, transient (200 steps), recurrent (period 400)}; power = alarm at or after the first harmful step; null FA = alarm rate on the null world over T = 2000 (theory-threshold rows).

## Mode B: finite-horizon-valid comparison (threshold 1/α on the restart mixture; SR-1 at T/α)
Mean power over the 18 worlds at 5% / 10% / 20% labels, and null FA:
| factor source | start weights | power | null FA |
|---|---|---|---|
| H2c | single (ordinary) | .075 / .174 / .327 | .003 / .010 / .022 |
| H2c | uniform (= SR at T/α) | .056 / .157 / .327 | 0 / .003 / .010 |
| H2c | front | .066 / .167 / .333 | 0 / .007 / .007 |
| H2c | geometric (0.995^t) | **.078 / .183 / .350** | 0 / .005 / .013 |
| H2c | coarse8 | .060 / .163 / .334 | 0 / .005 / .010 |
| cost-only ONS | single / geometric | .092 / .150 / .225 → .100 / .171 / .272 | ≤ .028 |
| Brier-guided ONS | single / coarse8 | .110 / .174 / .260 → .104 / .196 / .344 | ≤ .020 |
| SR-1 on H2c factors, ARL threshold 1/α | – | 0 (every path alarms before the harm) | **1.000** |
| SR-1 on H2c factors, finite-horizon T/α | – | .056 / .157 / .326 | 0 / .003 / .010 |
On late, transient and recurrent cells only (15 worlds): H2c single .044 / .116 / .258; geometric .045 / .122 / .279; uniform .031 / .102 / .256.
**Findings.** (1) **ARL ≠ finite-horizon error, confirmed:** the SR recursion at the ARL threshold 1/α alarms on 100% of null streams within 2000 steps; the same recursion at T/α has the finite-horizon guarantee and matches the uniform restart mixture exactly, as the theory predicts. (2) **No valid restart schedule materially beats the ordinary single-start H2c.** The best (geometric) gains +.003 / +.009 / +.023, mostly within noise (an SE of roughly .01–.02 on a mean over 18 worlds), and the uniform/coarse schedules are slightly worse because they pay capital for restarts that discounted Kelly bets already provide. (3) Within restart schedules, Brier guidance keeps its advantage over cost-only betting (H2c vs cost-only ONS: +.02 to +.10 across schedules). (4) The valid null FA (≤ .022) is far below α = .05: the Ville/capital-split bounds are conservative for these bets.

## Mode C: empirical (null-calibrated) thresholds (`mode_c.csv`; threshold = 95th percentile of the horizon-max over 1000 G1 null streams, per label rate)
Mean power (5% / 10% / 20% labels):
| method | power |
|---|---|
| H2c, single start | .180 / .314 / .453 |
| H2c, geometric restart mixture | .212 / .358 / .504 |
| **H2c, SR recursion** | **.270 / .416 / .555** |
| cost-only ONS, SR recursion | .193 / .309 / .408 |
| Brier-guided ONS, SR recursion | .260 / .384 / .519 |
| existing cost SR (`sr_cost_tight`) | .219 / .326 / .414 |
**Finding.** At matched empirical size on the calibration null, **SR restart with H2c bets beats the existing cost SR by +.05 / +.09 / +.14 and the ordinary H2c by +.09 / +.10 / +.10**, and Brier guidance is worth +.08 to +.15 inside SR (H2c-SR vs cost-ONS-SR). So the SR's extra power over H2c is a real restart effect, but it is only obtainable with a threshold (≈ 5,600–7,300) far below the finite-horizon-valid T/α = 40,000.

## Does the empirical calibration transfer? (`calibration_transfer.csv`; thresholds from the G1 null, evaluated on other nulls; 400 seeds each, SE ≈ .011–.018)
Null FA at the G1-calibrated threshold (target .05), 10% / 20% labels: H2c-SR .028–.092 / .040–.108 on G1-other-seed, G2, six G5 conditions; existing SR0 .040–.118 / .035–.080; **AR(1) ρ = .98: H2c-SR .188 / .302, SR0 .162 / .188**. H2c-SR therefore transfers about as well (and as badly) as the existing SR: the guarantee is only the calibration null's size, and a mild shift of the null moves the rate between roughly 0.03 and 0.13.
