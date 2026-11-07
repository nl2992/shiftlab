# Fresh real loss streams (SOTA sprint, final external validation)

Built by `uv run python scripts/sota_sprint/fresh_real.py` (sklearn 1.9.1, numpy 2.5.4,
pandas 3.0.6; repo HEAD at build time e664e52). Raw zips live under `data/raw/sprint_fresh/`
(gitignored). Protocol: `docs/sota_sprint/fresh_real_protocol.md`.

Each `<dataset>.npz` holds `l0`, `l1` (int8, shape `(K, 2000)`; incumbent and challenger 0-1
losses) and `starts` (int64, absolute row index of each episode in the chronologically sorted,
cleaned table). `stats.json` holds the full build record (descriptive only).

`npz_sha256` is the file hash. `np.savez` stamps zip entry times, so a rebuild changes it;
`array_content_sha256` = sha256(l0.tobytes() + l1.tobytes() + starts.tobytes()) is the
reproducible check.

| dataset | UCI id / source URL | raw zip sha256 | rows n | K | delay (events) |
|---|---|---|---|---|---|
| metro | 492, https://archive.ics.uci.edu/static/public/492/metro+interstate+traffic+volume.zip | b99aeabcbd6cc86f642da3a79d90883425798f58abd3b3302da2fa19dda73768 | 48204 | 16 | 24 |
| beijing_pm25 | 381, https://archive.ics.uci.edu/static/public/381/beijing+pm2+5+data.zip | 40cdd29c24918e855133dce280ff59779bb0b5852898e05bafcf422a4cc0a175 | 41757 | 14 | 24 |
| bike_hour | 275, https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip | b70182d0d0508e9abbb79306ce5c0cec34869000f8220175ac83d11dbe845401 | 17379 | 6 | 24 |
| appliances | 374, https://archive.ics.uci.edu/static/public/374/appliances+energy+prediction.zip | 2fccf354445d886e7917620b0195db1f3e3e34d5a067a93b844694a4c561255a | 19735 | 6 | 144 |
| household_power | 235, https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip | 9f84b46ade8a2d8e1286ec4b2b6c2987a45a755c59f263be3b3b3d10dfbda3ff | 204950 | 20 | 144 |

All five: license CC BY 4.0 (UCI Machine Learning Repository).

| npz | file sha256 | array_content_sha256 |
|---|---|---|
| metro.npz | d2e44130d052f1e73a38c6e2b8d731d1c9bef5b955b0447c14c1a5998788bdb1 | fcffeb091836f64753acd1d59f1cb7d3cb9d698c2b1671c8899e584138bafb7d |
| beijing_pm25.npz | b29ea4991e25abdd3160399e597d56ce08d786da7a6fd6a6439f4cdb5065a4aa | 5e162db728f5b3a87f98c8712bc2f188c39acb5c771a44d2b768cc8d33a6cdf0 |
| bike_hour.npz | 6572177367e66927859e6a64e189ae41402bdc262d96f480490977f87c73fb66 | 9e00cebfd33996f4ed6f0db719e28d7f7a20c234d7696329a38c464b530655db |
| appliances.npz | 03e7a8b93a55a4efe5a6cef5af25b16aa88f3b73c03bde6c2444037a543af734 | 4e86c780a1c16c3334517bee634e76aadd23bf2a4ce94213dbf1b5abbfdced51 |
| household_power.npz | e72049ab25102e9192b4c1ad43c73ee2fffb66e6dcba30da27a96eee72c6a582 | e658a1f8e3a8ff6dcb9edc8e9594ea77207bb9a58dd36e32f905a251f7433983 |

## Construction (identical for all datasets)

1. Load, clean, sort chronologically (stable sort); n = remaining rows.
2. Binary label y = 1[target > median(target over rows [0, 0.30n))].
3. Train-only `prep`: StandardScaler on numeric columns, OneHotEncoder(min_frequency=20,
   handle_unknown="ignore") on categorical columns, both fit on rows [0, 0.30n).
4. Incumbent: LogisticRegression(max_iter=300, C=1.0) fit on rows [0, 0.15n).
   Challenger: HistGradientBoostingClassifier(max_iter=100, max_depth=4, learning_rate=0.1,
   random_state=0) fit on rows [0, 0.30n).
5. Episodes: K = min(20, floor((n - n30)/2000)) consecutive non-overlapping 2000-row windows
   starting at n30 = int(0.30n). Losses l = 1[pred != y].

## Per-dataset cleaning and features

- **metro**: target `traffic_volume`; features holiday, weather_main, weather_description
  (categorical), temp, rain_1h, snow_1h, clouds_all, plus hour/weekday/month from `date_time`
  (then dropped). Note: 7629 rows share a timestamp with another row (one row per weather
  description per hour, same traffic_volume); kept, as specified, so 24 events is slightly less
  than one day on those hours.
- **beijing_pm25**: target `pm2.5`; 2067 rows with missing target dropped. Features DEWP, TEMP,
  PRES, Iws, Is, Ir, cbwd (categorical), hour/weekday/month. Dropped No, year, day.
- **bike_hour**: target `cnt`; dropped casual and registered (they sum to cnt), instant, dteday,
  yr (trend index); calendar re-derived. Features season, holiday, workingday, weathersit, temp,
  atemp, hum, windspeed, hour/weekday/month.
- **appliances**: target `Appliances` (Wh, 10-min); dropped date and rv1/rv2 (documented random
  variables). Features lights, T1-T9, RH_1-RH_9, T_out, Press_mm_hg, RH_out, Windspeed,
  Visibility, Tdewpoint, hour/weekday/month.
- **household_power**: 1-min data ("?" = missing) resampled to 10-minute means; bins with no
  complete reading dropped (n = 204950). Target `Global_active_power`. Dropped as leakage:
  Global_intensity (about P/V) and Sub_metering_1-3 (contemporaneous components of the target).
  Features Global_reactive_power, Voltage, hour/weekday/month.

## Descriptive statistics (evaluator-side, not tuning inputs)

Over all K episodes; advantage = mean(l0 - l1) per episode (positive: challenger better).

| dataset | K | incumbent err | challenger err | disagreement | challenger better | eval pos. rate |
|---|---|---|---|---|---|---|
| metro | 16 | 0.360 | 0.047 | 0.360 | 16/16 | 0.510 |
| beijing_pm25 | 14 | 0.332 | 0.260 | 0.207 | 13/14 | 0.497 |
| bike_hour | 6 | 0.276 | 0.115 | 0.258 | 6/6 | 0.649 |
| appliances | 6 | 0.411 | 0.259 | 0.432 | 6/6 | 0.464 |
| household_power | 20 | 0.316 | 0.250 | 0.246 | 15/20 | 0.420 |

Per-episode advantages are in `stats.json` (`mean_adv_per_episode`). The challenger is better
in 56 of 62 episodes, so these streams mostly test whether a policy promotes a better challenger
quickly and cheaply; only household_power (5/20) and beijing_pm25 (1/14) have harmful-switch
episodes.
