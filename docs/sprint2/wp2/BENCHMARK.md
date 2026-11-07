# WP2 benchmark: certifying model deployment under temporal dependence

This is a reproducible benchmark for label-budgeted, actively-queried, anytime deployment decisions
between an incumbent model and a challenger. It scores each method against the null it claims to
control and measures its promotions' predictive and economic outcomes. Application-level
decision harm is not identified by these records because no causal application utility is available.

* **Framing.** The conditional/unconditional distinction is Giacomini & White (Econometrica 2006),
  following Diebold & Mariano (1995) and West (1996). Henzi & Ziegel (2022) and Choe & Ramdas (2024)
  give anytime-valid conditional tests.
* **Benchmark features.** This implementation evaluates three elements in a shared setting: a hard label budget with
  predictable, actively chosen queries and delayed labels; exact known marginal nulls on real
  persistent streams (exchangeable twins); and all-in excess economic-cost accounting. This is a
  description of the benchmark contract, not a claim that these ingredients are individually novel;
  prior-art scope remains subject to review (see `../SOTA_BENCHMARK_AUDIT.md`).
* **Lower bounds.** None is claimed. Testing a marginal mean over unrestricted dependent classes is
  an instance of known non-existence results (Bahadur & Savage 1956; Ryabko; Sethi et al.,
  arXiv:2602.17587).

## Contract

* T = 2000 events per episode. The variants use T in {1000, 4000}.
* Hard label budget B = 200, label price c_q = .05 and switch cost c_s = 5.
* Each policy states its nominal alpha (default .05).
* The simulator is `scripts/promising_directions/sota/simulator.py`. Propensities are frozen at
  issue, and labels arrive after the delay.
* The objective is J = loss + c_q·labels + c_s·switches.

## Error and harm definitions

Write d_t = l0_t - l1_t (incumbent loss minus challenger loss) and tau for the first promotion.

| symbol | definition | what it scores |
|---|---|---|
| **V1 error** (conditional) | promote, and the realised next-H mean advantage mean(d_t, t in [tau, tau+H)) <= 0, for H = 100 or 500 | Promoting when the near-future conditional advantage was not positive. This is a realised-loss estimate of a violation of E[d_t given F_{t-1}] <= 0. It is an estimate, not the true conditional mean. |
| **V2 error** (marginal) | promote on a stream whose marginal advantage is 0 by construction (twin nulls, `*_null`, `*_twin`) | Violation of the marginal (stationary or exchangeable) null |
| **Registered V3 proxy** (historically labelled V3 error) | first promotion, and EI, where EI is sum_{t >= tau} d_t - c_s <= 0 | Hold-to-end challenger benefit fails to cover the switch cost. This narrow proxy excludes label spend and ignores later rollback; it is not the full economic non-improvement objective. |
| path harmful | any promotion, and DB <= 0, where DB = sum l0 - realised loss - c_s·switches | Whole realized prediction-loss/switch path, including rollbacks; excludes label cost |
| **prediction-loss delta** | prediction loss(policy) - loss(CONTROL_never_switch) | Action-level predictive loss difference; it is not causal application utility. |
| **all-in excess economic cost** | J(policy) - J(CONTROL_never_switch) = prediction-loss delta + label expenditure + switching expenditure | Includes monitoring and realized deployment costs. Its positive rate is retrospective, not a prospective per-promotion test or expected-value estimate. See [`REALIZED_HARM.md`](REALIZED_HARM.md). The raw `harm` field is a legacy name for this quantity. |
| pi_EI | sum EI / sum promotions | Share of promotions that are economically inappropriate |

* Each method is labelled with the null it claims (`bench2.NULL_TESTED`; `DM_HAC_monitor` = V2,
  asymptotic).
* A V1 rate is never compared with a V2 rate as if the two tested the same hypothesis. The
  three-null matrix reports all three errors side by side for every method on every null stream.

## Datasets

| set | construction | files |
|---|---|---|
| Registered twins | `twin_null.py`, splits 0..19 (sprint 1) | `data/sprint_twin_losses/twin_<ds>.npz` (content hashes in `stats.json`, reproduced 5/5 by `wp2_twins.py reproduce`) |
| **v2 twins** | the same construction on new splits 20..39 | `data/sprint_twin_losses_v2/twin2_<ds>.npz`, `stats.json` |
| v2 twin variants | T = 1000 / 4000 re-windowings within split | `data/sprint_twin_losses_v2/twin2_<ds>_T{1000,4000}.npz`, `variants.json` |
| Fresh real (alternatives) | LR incumbent and HGB challenger (`fresh_real.py`) | `data/sprint_fresh_losses/<ds>.npz` |
| Synthetic dependence | `fam_f.py` (WP2_*), plus F0, F5, S_dep and O_null regimes | generated from seeds |

* The five datasets are metro, beijing_pm25, bike_hour, appliances and household_power. Each has a
  registered delay (24 or 144 events), and the variants multiply it by {.5, 1, 2}.
* **Synthetic classes.**
  * Mean-reverting persistent nulls: F5_dep_null_r8, F5_dep_null_r95, O_null_semimarkov,
    O_null_order2, WP2_o2_null, WP2_sm_null and WP2_hs_null.
  * Fixed-effect (twin-analogue) nulls: WP2_{iid,m8,o2,sm,hs}_twin, which use an episode role coin
    with p_e = .5 ± .05.
  * Alternatives: F0_better, F5_dep_better_r8, S_dep_better_r95 and WP2_{o2,sm,hs}_better.

## Methods

* **Six registered published-certificate ports (strict pool).**
  * gated_deployment, gated_adaptive_range(+front);
  * discern_style, discern_design_floor;
  * SMCS+retain-incumbent;
* **Additional V1-capable common-contract ports/adapters** (not counted in the strict published pool):
  * `choe_ramdas_eb` and `choe_ramdas_eb+front` are local Choe–Ramdas ports, not author-native code;
  * `gated_deployment+QCE` and `gated_deployment+QCE+front` are ShiftLab QCE variants.
* **Acquisition adapter with ShiftLab V1 certificate:** `xu_acquisition_only`. Its empirical V1
  property is supplied by ShiftLab's paired-loss certificate. Xu et al.'s published guarantee is
  for risk-controlling prediction sets, so this policy is not counted as a published certificate
  comparator. It remains in the operational and economic baseline panel.
* The historical 11-port pooled analysis is preserved. A post-run sensitivity using only the six
  shared published-pool ports is reported in [`COMPARATOR_CLASS_AUDIT.md`](COMPARATOR_CLASS_AUDIT.md).
* A historical cached-real H5 extension covers nine previously exposed Atlas v2 sources; its
  retrospective positive-advantage selection and source-clustered contrasts are reported in
  [`CACHED_REAL_H5_SENSITIVITY.md`](CACHED_REAL_H5_SENSITIVITY.md). It does not count as fresh
  validation.
* **Internal.**
  * V1: QSG, D2 and the RMM hosts (rmm:gated_deployment+RMM, rmm:discern_style+RMM,
    rmm:SMCS+retain-incumbent+RMM, rmm:gated_adaptive_range+RMM).
  * V2: A5b and D5.
* **Marginal baseline (adaptation).**
  * `DM_HAC_monitor` is fam_f.DMHACMonitor: a Newey-West-studentised CUSUM on paced disagreement
    queries, with a linear Brownian boundary. Its size is asymptotic only.
  * `DM_HAC_monitor-iid` is the same monitor with lag 0.
* **Uncertified references:** cams_adapter and model_picker_adapter.
* **Controls:** CONTROL_never_switch and economic_replacement (V3 reference).

## Seeds and commands

The development seed base is 2026110701 for every WP2 run. For Round-5 use, rerun with
`bench2.EVAL_SEED_BASE` / `NULL_SEED_BASE`.

```
uv run python scripts/sota_sprint/wp2_twins.py reproduce      # H0 hash check -> docs/sprint2/wp2/reproduction.json
uv run python scripts/sota_sprint/wp2_twins.py v2             # build v2 splits 20..39
uv run python scripts/sota_sprint/wp2_twins.py variants       # T=1000/4000 re-windowings
uv run python scripts/sota_sprint/audit_wp2_run2.py --out docs/sprint2/wp2/run2_decision_flag_audit.json  # verify Run-2 stored flags/costs
bash outputs/sprint2/WP2/run_all.sh                            # runs 1-4 (exact commands inside; ~2 h at 2x2 workers)
uv run python scripts/sota_sprint/wp2_score.py --runs <run dir>[,<run dir>] --out scores.csv   # scoring
uv run python scripts/sota_sprint/wp2_analyze.py              # registered hypotheses -> results.json, tables.md
uv run pytest -q tests/sprint2/test_wp2.py
```

* `wp2_run.py` reproduces screen.py's pairing exactly, so a regime name and seed base give the same
  `net` as screen.py (this is unit-tested). It also records the deployment-path economics.
* To score a new method, register it in a family module's `EXTRA`, run `wp2_run.py` on the sources
  above, and run `wp2_score.py`.

## Uncertainty

* The units are:
  * real twins: the (dataset, split) cluster;
  * fresh real: the (dataset, episode) cluster;
  * synthetic: the seed.
* CIs are 95% percentile bootstrap intervals over clusters (2000 resamples), stratified by regime
  when pooled.
* Rates are means of cluster means. pi_EI and adv_rest are ratio estimators.
