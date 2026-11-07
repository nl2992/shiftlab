# P5: multi-model (K = 3–4) extension of the deploy gate

**Mechanism extended: D2.** D2 is the two-model mechanism with the strongest real-data record from
sprint 1. The K-model version is `fam_p.KGate`, which keeps D2's architecture:

* **Host.** A CAMS host (`CAMSDeploymentAdapter(n_models=K)` over K constant policies) ranks the
  models and queries with its own randomness.
* **Gate.** The gate front-loads queries on (incumbent, host-preferred) disagreements while that
  challenger is uncertified.
* **Certificate.** Each challenger j gets its own pairwise started mixture against the current
  incumbent, built on z = 1[j right] over their disagreements. Its threshold is
  (K-1)·2^cycle/alpha, a Bonferroni split over the K-1 challengers.
* **Promotion rule.** A challenger is promoted only if it is certified AND the host ranks it first.
* **Labels.** One label reveals all K losses. Each pairwise certificate advances on queried events
  where that model pair disagrees; it skips events where the incumbent and challenger losses match.

**Validity scope (V1, conditional).** The threshold and per-cycle Bonferroni allocation in the code
support the advertised bound only if, for every incumbent–challenger pair tested, the pairwise sign
null holds conditional on the full pre-label query-selection information. A label may be requested
because the host prefers a *different* challenger; when that shared label arrives, `KGate.observe`
updates every incumbent–challenger pair whose losses disagree. Thus it is insufficient to assume the
null only conditional on querying that pair's own disagreement. The required null must remain true
under the cross-pair selection induced by the host ranking and the full prediction vector. The code
does not record a separate propensity for each pair. The class docstring's Bonferroni argument
assumes these stronger conditional nulls; it is not a universal marginal or arbitrary-selection
guarantee. The tested K3/K4 simulator rates are empirical diagnostics, not proof of this condition.

**Simulator support.** `run_episode` handles (T, n_models) without changes.
`stream_from_losses` also handles K columns, through labels XOR losses.

## Streams

**Synthetic.** The K-model regimes are `fam_p.K_REGIMES`.

* The incumbent errs w.p. .3.
* Challenger j disagrees at rate .2 and is right on a disagreement w.p. p_j(t).
* Regimes: K3_best1, K4_mixed, K3_near, K4_late (challenger 3 goes from .40 to .72 at t = 800),
  K3_null and K4_null.

**Real K = 4.** The real streams (`fam_p.kbuild`, built into `outputs/sprint2/P/kstreams/`) use the
fresh UCI raw data, the fresh_real loaders, the same episode windows and train-only preprocessing.

* m0 = LR on [0, .15n)
* m1 = HGB on [0, .30n)
* m2 = LR on [0, .30n)
* m3 = shallow HGB on [.15n, .30n)

Columns 0 and 1 reproduce the committed 2-model cache exactly on all 5 datasets (`matches_2model_cache`).

**Runner.** `fam_p.py kscreen` uses 20 seeds per synthetic regime (seed base 2026110701) and one
replay per real episode (62 episodes). Results are in `outputs/sprint2/P/kscreen/kscreen.json`.

## Results (development)

Paired ΔJ of K_D2 against each comparator, mean ± 95% half-width:

| regime | vs native CAMS(K) | vs Model Picker(K) | vs never switch | vs host_only ablation |
|---|---|---|---|---|
| K3_best1 | +10.2 ± 15.6 | +18.7 ± 20.6 | -51.3 ± 18.6 | -33.5 ± 18.3 |
| K4_mixed | +9.6 ± 21.2 | -1.5 ± 20.3 | -54.7 ± 18.7 | -25.7 ± 18.6 |
| K3_near | -21.8 ± 16.5 | -9.1 ± 18.0 | +8.0 ± 3.7 | -0.8 |
| K4_late | -21.4 ± 19.2 | -2.5 ± 26.2 | +6.5 ± 5.5 | -1.1 |
| K3_null | -48.0 ± 18.8 | -44.3 ± 17.2 | +10.0 | 0 |
| K4_null | -67.8 ± 19.6 | -63.9 ± 14.1 | +10.4 | +0.5 |
| real appliances (6 episodes) | -25.8 ± 55.1 | +2.2 ± 32.0 | -181.8 ± 115.7 | +6.2 ± 36.6 |
| real beijing_pm25 (14) | -29.6 ± 38.4 | +2.5 ± 44.8 | -79.5 ± 78.0 | -4.6 ± 16.2 |
| real bike_hour (6) | -15.5 ± 16.5 | -4.3 ± 25.9 | -323.3 ± 97.4 | -25.3 ± 15.7 |
| real household_power (20) | -23.1 ± 16.9 | -6.4 ± 19.9 | -93.1 ± 64.8 | -5.0 ± 9.7 |
| real metro (16) | -18.9 ± 14.1 | +22.7 ± 10.2 | -578.0 ± 40.9 | -6.0 ± 5.7 |

**Switching to a model that is not better** (ever-nonbetter rate):

| regime | K_D2 | native CAMS(K) | Model Picker(K) |
|---|---|---|---|
| K3_null | .05 | 1.00 | .95 |
| K4_null | .05 | 1.00 | 1.00 |
| real beijing_pm25 | .21 | .50 | .50 |
| real household_power | .10 | .30 | .35 |

* **Real-data gate.** On real data the "not better" label uses the evaluator proxy, the episode's
  realised mean advantage, which is not causal truth.
* **Mechanism ablation.** K_D2-host_only removes the gate's front-loading. It loses 26–34 on the
  synthetic alternatives that have a winner.

**Verdict: SCREENED_PROMISING (development).**

* In this development screen, the gate was evaluated with K = 3–4.
* It cuts null switching from 95–100% to 5%.
* It is cheaper than native CAMS(K) on 4/6 synthetic and 5/5 real datasets. Among the real streams,
  only household_power and metro have paired-cost CIs that exclude 0.
* It is within noise of Model Picker(K) except metro, where it is +22.7, worse.
* Like D2, it misses late improvement (K4_late is +6.5 vs never switch).
* Its V1 guarantee does not cover persistence (see P4).
* No certified published K-model port exists in the harness, so there is no certified comparator.
  That is a limitation of this comparison.
* These results show operation in the tested K = 3–4 settings; they do not establish general transfer.

## Separate K-model Track R follow-up

Because the shared Track-R null mix is two-model, P5 received a separate, estimand-matched K-model
grid rather than being left unmeasured. `scripts/sota_sprint/p5_trackr.py` evaluates K_D2 at all
eight registered alpha values on K3_null/K4_null and K3_best1/K4_mixed/K3_near/K4_late. There are
20 development and 20 separate evaluation seeds per regime/alpha; each alpha/regime batch is saved
as a checkpoint. Risk is the episode-level event of ever deploying a nonbetter challenger, pooled
equally over the two null regimes. Cost is net J pooled over four alternative regimes. Each reported
confidence interval uses 20 seed blocks, averaging the two null regimes for risk or four alternative
regimes for cost. Development null risk must be at or below the target; among eligible alpha values,
development alternative cost selects the operating point.

| Target | alpha | evaluation risk (95% CI) | alternative net J (95% CI) |
|---|---:|---:|---:|
| R5 | 0.2 | .025 [.000,.074] | 565.2 [560.4,570.0] |
| R10 | 0.3 | .050 [.000,.117] | 563.5 [556.2,570.8] |
| R15 | 0.5 | .150 [.047,.253] | 556.5 [550.2,562.7] |
| R20 | 0.5 | .150 [.047,.253] | 556.5 [550.2,562.7] |
| R25 | 0.5 | .150 [.047,.253] | 556.5 [550.2,562.7] |
| R30 | 0.5 | .150 [.047,.253] | 556.5 [550.2,562.7] |

These are small, empirical estimates; the intervals are broad and cross several targets. They do
not verify the selection-conditional theorem assumptions above. Raw records and calibration outputs
are in `outputs/sprint2/P/trackR_K/`.
