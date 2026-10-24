# Minimum-propensity floor diagnostic

This same-seed comparison reuses the first 30 streams from the 60-seed `q_min=0.10` run and compares them with a `q_min=0.20` run under the same 20% dollar budget. It is descriptive, not an independent confirmation or a calibration study. The floor changes the e-process support bound and can change both propensities and the budget stopping horizon.

For uniform paths, the script verifies event-by-event equality of propensities, query indicators, observed labels, proxy predictions, PPI increments, and evaluator outcomes. The realized query floor is 0.20 in both runs. Thus the uniform crossing difference under the original common bounds isolates the support-bound setting: the `q_min=0.10` run used 96.9 despite uniform querying never falling below 0.20, while the second used 45.9. The CSV also reports fixed-mixture, predictable-variance, and plug-in empirical-Bernstein replays using each policy's registered support bound. For uniform, that policy-specific bound is 45.9 in both runs, so the correctly matched replay should be identical event by event.

|Scenario|Method|Streams|Common-bound detections q=.10 / .20|Policy-bound fixed-mixture detections q=.10 / .20|Policy-bound PVA detections q=.10 / .20|Policy-bound PM-EB detections q=.10 / .20|Reached harm q=.10 / .20|Mean events q=.10 / .20|Mean labels q=.10 / .20|Mean spend q=.10 / .20|PPI variance q=.10 / .20|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|evidence_curve_a0.05_p0.5|30|0/30 / 0/30|0/30 / 0/30|0/30 / 0/30|0/30 / 0/30|n/a|2319 / 1625|345.6 / 381.0|676.2 / 718.8|5.656 / 3.362|
|benign_nuisance|uniform_proxy|30|0/30 / 0/30|0/30 / 0/30|0/30 / 0/30|0/30 / 0/30|n/a|1834 / 1834|362.3 / 362.3|718.7 / 718.7|3.835 / 3.835|
|boundary_local_harm|evidence_curve_a0.05_p0.5|30|4/30 / 8/30|4/30 / 8/30|1/30 / 4/30|0/30 / 0/30|30/30|2376 / 1841|459.5 / 480.0|688.8 / 718.2|8.669 / 5.655|
|boundary_local_harm|uniform_proxy|30|2/30 / 24/30|24/30 / 24/30|20/30 / 20/30|1/30 / 1/30|30/30|2370 / 2370|468.9 / 468.9|703.4 / 703.4|7.500 / 7.500|
|stationary|evidence_curve_a0.05_p0.5|30|0/30 / 0/30|0/30 / 0/30|0/30 / 0/30|0/30 / 0/30|n/a|2400 / 2112|364.9 / 479.1|547.1 / 718.2|5.646 / 3.452|
|stationary|uniform_proxy|30|0/30 / 0/30|0/30 / 0/30|0/30 / 0/30|0/30 / 0/30|n/a|2370 / 2370|468.9 / 468.9|703.4 / 703.4|3.671 / 3.671|

Detection discordances are recorded in the CSV for paired inspection. Because seeds are reused from the development comparison, do not treat paired p-values or rates here as confirmatory and do not promote a floor setting from this diagnostic. Null false-escalation counts are similarly diagnostic only.

No figure was generated. PaperBanana remains the project preference for future research visuals.
