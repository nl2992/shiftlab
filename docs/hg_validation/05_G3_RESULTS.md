# 05. G3 confirmation results (single run of the frozen protocol; `outputs/hg_validation/05_G3_RESULTS.csv`)

960 of 1000 seeds reach the harmful regime. Power is over those seeds; false alarm over all seeds; null control = 400 seeds that never leave the source regime.

| labels | arm | power | false alarm | null FA | harm before alarm |
|---|---|---|---|---|---|
| 10% | parent | .227 | .006 | .005 | 96.6 |
| 10% | **HG_unifcap** | .277 | .001 | .010 | 95.0 |
| 10% | ONS | **.375** | .011 | .022 | 84.2 |
| 10% | mixture8 | .342 | .012 | .020 | 85.0 |
| 10% | disc_only | .334 | .005 | .005 | 89.8 |
| 20% | parent | .396 | .008 | .010 | 79.4 |
| 20% | **HG_unifcap** | .527 | .003 | .005 | 71.2 |
| 20% | ONS | .539 | .012 | .022 | 64.9 |
| 20% | mixture8 | .470 | .011 | .025 | 69.4 |
| 20% | disc_only | **.561** | .007 | .012 | 67.1 |

HG_unifcap minus parent: **+0.050 [0.028, 0.073]** at 10%, **+0.131 [0.106, 0.158]** at 20% (seed bootstrap; seeds here are independent regime paths).

**Frozen hypotheses**
- **H-G3-1** (gain ≥ +0.05 at both rates, CI lower bound > 0): **PASS**, with the 10% gain sitting exactly on the threshold (48/960).
- **H-G3-2** (power within 0.03 of ONS and false alarm ≥ 0.02 lower): **FAIL**. At 10% labels HG trails ONS by 0.098 in power; at 20% it is within 0.012 but the false-alarm gap is only 0.009 (all arms have false alarms ≤ .012 here, so the 0.02 gap was unreachable). The "lower false alarms than ONS at similar power" niche is **not confirmed on G3**.
- **H-G3-3** (null FA ≤ 0.07): **PASS** (.010 / .005).

**Reading.** HG's improvement over its own parent replicates on a structurally different generator, with a CI that excludes zero at both rates and a large effect at 20% labels. But on G3 plain discounting or ONS match or beat HG's power, and the gate's benign-false-alarm advantage is invisible because every arm's false alarms are tiny. So the supported claim is "HG improves its parent"; the claim that it improves on the established adaptive-betting alternatives is not supported. Limits: single generator family with one transition matrix, regime visits to the benign state are the only source of benign exposure, noise/loss-scale shifts not simulated, delay fixed at 5. No hyperparameters were changed after seeing the results.
