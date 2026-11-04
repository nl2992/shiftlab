# SOTA sprint: fresh real-data external validation protocol

Registered 2026-11-03 by the benchmarking/data agent. The datasets, pair specification, episode
plan, label delays and analysis below were fixed **before any ShiftLab policy, candidate, or the
screen runner touched these data**. Only the frozen incumbent/challenger models were fit (to
produce the loss streams). The descriptive statistics in
`data/sprint_fresh_losses/README.md` are evaluator-side and must not be used to tune, select or
re-specify any policy, contract parameter or analysis choice.

None of the five datasets has been used in ShiftLab before (previously used: airlines, bank,
criteo, elec2, rialto, spam, NOAA weather, openml_ldpa, uci_occupancy). No substitutions were
needed: all five suggested downloads succeeded (total about 35 MB).

## Datasets

All from the UCI Machine Learning Repository, license CC BY 4.0. Raw zips are kept under
`data/raw/sprint_fresh/uci_<id>/raw.zip` (gitignored).

| dataset | UCI id | URL | raw zip sha256 | span | rows n |
|---|---|---|---|---|---|
| metro | 492 | https://archive.ics.uci.edu/static/public/492/metro+interstate+traffic+volume.zip | b99aeabcbd6cc86f642da3a79d90883425798f58abd3b3302da2fa19dda73768 | 2012-10 to 2018-09, hourly | 48204 |
| beijing_pm25 | 381 | https://archive.ics.uci.edu/static/public/381/beijing+pm2+5+data.zip | 40cdd29c24918e855133dce280ff59779bb0b5852898e05bafcf422a4cc0a175 | 2010-01 to 2014-12, hourly | 41757 |
| bike_hour | 275 | https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip | b70182d0d0508e9abbb79306ce5c0cec34869000f8220175ac83d11dbe845401 | 2011-01 to 2012-12, hourly | 17379 |
| appliances | 374 | https://archive.ics.uci.edu/static/public/374/appliances+energy+prediction.zip | 2fccf354445d886e7917620b0195db1f3e3e34d5a067a93b844694a4c561255a | 2016-01 to 2016-05, 10-min | 19735 |
| household_power | 235 | https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip | 9f84b46ade8a2d8e1286ec4b2b6c2987a45a755c59f263be3b3b3d10dfbda3ff | 2006-12 to 2010-11, 10-min means | 204950 |

Derived loss caches (`data/sprint_fresh_losses/<dataset>.npz`, arrays `l0`, `l1` int8 (K, 2000),
`starts`):

| npz | file sha256 | array_content_sha256 |
|---|---|---|
| metro.npz | d2e44130d052f1e73a38c6e2b8d731d1c9bef5b955b0447c14c1a5998788bdb1 | fcffeb091836f64753acd1d59f1cb7d3cb9d698c2b1671c8899e584138bafb7d |
| beijing_pm25.npz | b29ea4991e25abdd3160399e597d56ce08d786da7a6fd6a6439f4cdb5065a4aa | 5e162db728f5b3a87f98c8712bc2f188c39acb5c771a44d2b768cc8d33a6cdf0 |
| bike_hour.npz | 6572177367e66927859e6a64e189ae41402bdc262d96f480490977f87c73fb66 | 9e00cebfd33996f4ed6f0db719e28d7f7a20c234d7696329a38c464b530655db |
| appliances.npz | 03e7a8b93a55a4efe5a6cef5af25b16aa88f3b73c03bde6c2444037a543af734 | 4e86c780a1c16c3334517bee634e76aadd23bf2a4ce94213dbf1b5abbfdced51 |
| household_power.npz | e72049ab25102e9192b4c1ad43c73ee2fffb66e6dcba30da27a96eee72c6a582 | e658a1f8e3a8ff6dcb9edc8e9594ea77207bb9a58dd36e32f905a251f7433983 |

The file hash changes on rebuild because `np.savez` stamps zip entry times; verify rebuilds with
`array_content_sha256` = sha256(l0.tobytes() + l1.tobytes() + starts.tobytes()).

## Pair specification

Mirrors `scripts/promising_directions/b3_real_data.py::build_fetched`; code in
`scripts/sota_sprint/fresh_real.py` (sklearn 1.9.1, numpy 2.5.4, pandas 3.0.6).

* Rows sorted chronologically; n rows after cleaning; n15 = int(0.15n), n30 = int(0.30n).
* Label y = 1[target > median of target on rows [0, n30)].
* Train-only preprocessing on rows [0, n30): StandardScaler (numeric) and
  OneHotEncoder(min_frequency=20, handle_unknown="ignore") (categorical).
* Incumbent pi_0: LogisticRegression(max_iter=300, C=1.0) on rows [0, n15).
* Challenger pi_1: HistGradientBoostingClassifier(max_iter=100, max_depth=4, learning_rate=0.1,
  random_state=0) on rows [0, n30).
* Losses l_k = 1[pi_k(x) != y]. Both are observed for every row once the label arrives, so the
  paired loss difference is identifiable without an off-policy design.
* Per-dataset target, leakage drops and features are listed in `data/sprint_fresh_losses/README.md`.
  Leakage drops: bike casual/registered; household Global_intensity and Sub_metering_1-3.
  Timestamps are dropped after deriving hour, weekday and month.

## Episode plan

K = min(20, floor((n - n30)/2000)) consecutive non-overlapping windows of T = 2000 rows starting
at n30. `starts` in each npz gives absolute row indices.

| dataset | n30 | K | last row used |
|---|---|---|---|
| metro | 14461 | 16 | 46461 |
| beijing_pm25 | 12527 | 14 | 40527 |
| bike_hour | 5213 | 6 | 17213 |
| appliances | 5920 | 6 | 17920 |
| household_power | 61485 | 20 | 101485 |

Total 62 episodes. The household_power windows after row 101485 are not used.

## Label delays (registered, in events; `DELAYS` in fresh_real.py)

One day of natural time: metro 24, beijing_pm25 24, bike_hour 24, appliances 144,
household_power 144. Metro has 7629 rows that share an hour with another row (one row per weather
description), so 24 events is somewhat less than 24 hours there. Delays are fixed and in event
order; no missing or out-of-order labels are simulated.

## Analysis the lead will run

* Contract: T = 2000, B = 200, c_q = .05, c_s = 5, label delay as registered above.
* Policy seeds: 20 per episode at seed base 2026110604. Policy randomness is averaged within an
  episode; the episode is the unit of inference.
* Primary statistic per dataset and contrast: episode-level paired Delta J = J(candidate) -
  J(comparator), mean over episodes with a 95% t-interval (df = K - 1). Also pooled over all 62
  episodes, and reported per dataset.
* Because episodes within a dataset are consecutive windows of one series, they are dependent and
  the t-intervals are optimistic. Report, in addition: the fraction of episodes with Delta J < 0,
  and a per-dataset two-sided exact sign test on episode Delta J (ties dropped).
* Report promotion time and false promotions (switching on episodes where the challenger's
  episode mean loss is not lower) as descriptive outcomes. Note that 56 of 62 episodes favour the
  challenger, so these streams are mainly a test of cost of promoting a better challenger; harmful
  switches are only possible on 6 episodes (5 household_power, 1 beijing_pm25).
* Market or calendar dates are not causal change labels; no change times are inferred.

## Status

Smoke-level build only. No policy has been run on these streams as of registration.
