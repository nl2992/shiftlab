# P2 known-null real streams: exchangeable-twin protocol

Registered 2026-11-03, before any twin stream was built or any policy was run on one. This file
answers the evidence gap that the ARIS result-to-claim review assigned to P2: real streams with known
null truth, so that real-data false-promotion validity can be measured, not only cost.

## Construction (`scripts/sota_sprint/twin_null.py`)
For each of the five fresh UCI datasets (metro, beijing_pm25, bike_hour, appliances, household_power),
the following is repeated for each split s = 0..19.

1. **Data preparation.**
   * Chronological rows, binary label and train-only preprocessing are exactly as in
     `fresh_real.py`.
   * The training window is rows [0, 0.30n).
2. **Twin models.**
   * Training rows are assigned to halves A or B by an iid fair coin seeded by (dataset, s).
   * Twin A and twin B are trained with the identical model and hyperparameters:
     HistGradientBoostingClassifier(max_iter=100, max_depth=4, learning_rate=0.1, random_state=0).
   * A second fair coin, seeded by (dataset, s), decides which twin is the incumbent.
3. **Episodes.** These are the same evaluation windows as the fresh streams: up to 20 consecutive
   2000-event windows from 0.30n. Losses are 1[pred != y].
4. **Why the null is known.**
   * The split and the role coin are exchangeable, so E[l0_t - l1_t] = 0 at every event t over the
     construction's randomisation. The data, labels and evaluation stream are held fixed.
   * The evaluation stream itself is untouched, so the disagreements keep their real serial
     dependence.
   * This is a known marginal null that needs no dependence model.
   * For any single split one twin may be slightly better. Every split's realised advantage is
     reported (expected to centre on 0). "Harmful promotion" is reported separately: a promotion in an
     episode whose realised challenger advantage is <= 0.
5. **Delays.** These are the registered fresh-data delays (24 or 144 events).

## Runs
* **Contract.** T=2000, B=200, c_q=.05, c_s=5, alpha=.05.
* **Policy seeds.** 3 per episode, base 2026110620.
* **Policies.**
  * Certified published ports: gated_deployment, gated_adaptive_range,
    gated_adaptive_range+front, discern_style, discern_design_floor, SMCS+retain-incumbent,
    xu_acquisition_only, choe_ramdas_eb, choe_ramdas_eb+front, gated_deployment+QCE,
    gated_deployment+QCE+front.
  * Sprint candidates: A5b, A1b, the four RMM certificate hosts (Amendment 5), D1, D2 and QSG.
  * Fast uncertified selectors: model_picker_adapter and cams_adapter.
  * CONTROL_never_switch.

## Pre-registered analyses
* **Unit.** The split. Promotion rates and costs are averaged over that split's episodes and seeds.
* **CIs.** 95% confidence intervals come from a cluster bootstrap over the 20 splits (2000 resamples).
  Pooled per-run Wilson intervals are also reported but are not used for decisions.
* **Persistence.** The gap-indexed persistence MLE rho-hat of every twin stream is reported, with the
  same method as `real_persistence.py`.

| id | hypothesis | decision rule |
|---|---|---|
| K0 | construction sanity | the per-dataset mean realised advantage over splits has a bootstrap CI containing 0 (descriptive) |
| K1 | real persistence breaks powered certified ports | at least 5 of the 9 powered certified ports have promotion > .0936 with bootstrap lower bound > .05 on at least one dataset whose median twin rho-hat >= .5. The powered ports are the 11 above minus gated_deployment and discern_style, which almost never promote. |
| K2 | A5b holds the bound on real persistent nulls | A5b's bootstrap upper bound is <= .0936 on every dataset |
| K3 | harm | mean J(policy) - J(never-switch), and the harmful-promotion rate, per dataset (descriptive) |

A K1 or K2 failure is reported as a failure, and the P2 claim is revised to match. Nothing is tuned on
these runs.
