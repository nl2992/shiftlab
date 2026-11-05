# WP1 protocol: real-world validation of RMM on chronological incumbent-challenger competitions

> **Historical comparator note (2026-11-04):** this frozen protocol names `xu_acquisition_only`
> in its original “best certified” pool. That policy uses Xu's acquisition component together with
> ShiftLab's paired-loss certificate; it is not Xu et al.'s published risk-control certificate.
> The registered protocol below is preserved as historical record. Current comparator-class
> sensitivity is reported separately in [results_amended_no_xu.json](results_amended_no_xu.json),
> and the paper-to-code interpretation is in [SOTA_BENCHMARK_AUDIT.md](../SOTA_BENCHMARK_AUDIT.md).

Registered 2026-11-04 on branch `research/sprint2-a5b-d2-rmm`, **before** the new streams were built,
before any episode was classified, and before any policy was run on the new streams. Code:
[scripts/sota_sprint/late_real.py](../../../scripts/sota_sprint/late_real.py) (construction,
classifier, runner, analysis) and [scripts/sota_sprint/fam_e.py](../../../scripts/sota_sprint/fam_e.py)
(new policies). Everything below is fixed; deviations are recorded as dated amendments at the end.

## 1. Question

RMM's registered result (Amendment 5, HC PASS) is synthetic: on late-improvement regimes (challenger
worse first, better after a change at t = 600-1500) RMM on four certificate hosts beats Xu by 15-30
per 2000 events. Do real chronological streams contain genuine late improvement, and where they do,
does RMM keep its advantage over the best certified comparator?

## 2. Stream construction (new: `data/sprint_late_losses/`)

Raw data: the five UCI zips in `data/raw/sprint_fresh/` (metro, beijing_pm25, bike_hour, appliances,
household_power), loaded with the existing `fresh_real.LOADERS` (same feature/leakage handling). The
B3 raw data are not on this machine; nothing else raw is used.

* Binary label: `y = 1[yraw > median(yraw[:0.30 n])]` (fixed per dataset, rows before every
  evaluation window).
* Model class for both roles: `HistGradientBoostingClassifier(max_iter=100, max_depth=4,
  learning_rate=0.1, random_state=0)`. Same class for both roles, so a ranking difference comes from
  the training period only.
* Episode starts `e_j = e_min + 2000 j`, `e_min = max(0.30 n, 8000)`, `j = 0..K-1`,
  `K = floor((n - e_min) / 2000)`. If `K > 20`, the 20 starts with indices
  `round(linspace(0, K-1, 20))` are used (deterministic, chosen before any loss is seen). The
  episode is rows `[e_j, e_j + 2000)`, in time order; both models are refit for every episode.
* Two constructions (historical schedules), with `D = 4000` rows of deployment lag:
  * `win` (equal windows, different recency): incumbent fit on `[e-D-H, e-D)`, challenger on
    `[e-H, e)`, `H = 4000`.
  * `exp` (stale expanding vs short recent): incumbent fit on `[0, e-D)` (all history up to the lag),
    challenger on the recent window `[e-W, e)`, `W = 2000`.
* Preprocessing (`fresh_real.prep`: StandardScaler + OneHot) fit on the union of the two training
  ranges, i.e. rows `[start_inc, e)`, train-only.
* Loss `l = 1[pred != y]` (int8). Stream name `late_<dataset>_<construction>`, 10 streams.
* Native label delay = `fresh_real.DELAYS` (24 hourly, 144 for 10-minute data).

Exposure: the raw data were used for the sprint-1 fresh and twin streams (different model pairs), so
the new streams are new loss pairs on development-exposed raw data, not unseen data.

## 3. Existing fixed-pair streams scanned with the same rule

* 9 cached streams `data/atlas_v2_losses/*.npz` (all episodes) and 5 fresh streams
  `data/sprint_fresh_losses/*.npz` (all episodes). Both are development-exposed.
* Twin known-null streams `data/sprint_twin_losses/twin_*.npz`, splits 0 and 1 only (all their
  episodes). These are a **false-positive check of the classifier** (the two models are exchangeable,
  so classified changes there measure the rule's spurious-change rate) and the real Track-V check.

## 4. Episode classifier (evaluator side, outcome-blind)

Inputs: only the two models' realised losses in the episode, `d_t = l0_t - l1_t` (positive means the
challenger was right). No policy output is used, ever. Constants: `delta = 0.01` per event,
segment minimum `m = 200`, late threshold `t_late = 400`, block length 50, 999 block permutations
(generator `default_rng(20261104)`), significance `p <= 0.01`.

1. `S_k = sum_{t<k} (d_t - mean(d))` for `k in [m, T-m]`; `tau = argmax_k |S_k|`;
   `stat = max |S_k| / (sd(d) sqrt(T))` (no change if `sd(d) = 0`).
2. p-value: permute the 40 blocks of 50 events, recompute `stat`; `p = (1 + #{perm >= obs}) / 1000`.
   `change = p <= 0.01`.
3. `m1 = mean(d[:tau])`, `m2 = mean(d[tau:])`, `mbar = mean(d)`; `sgn(x) = +` if `x >= delta`, `-` if
   `x <= -delta`, else `0`.
4. Class (first match):
   * `late_improvement`: change, `sgn(m1) in {0,-}`, `sgn(m2) = +`, `m2 - m1 >= 2 delta`, `tau >= 400`.
   * `early_improvement`: as above with `tau < 400`.
   * `reversal`: change, `sgn(m1) = +`, `sgn(m2) in {0,-}`, `m1 - m2 >= 2 delta`.
   * `stationary_better`: otherwise, if `sgn(mbar) = +`.
   * `null`: everything else (sub-tag `worse` if `sgn(mbar) = -`; sub-tag `changed` if `change`).
5. Rule sensitivity (counts only, never used for the primary analysis): `delta in {0.005, 0.02}`.

Every episode of every stream in sections 2-3 is classified and every one is evaluated. No window is
dropped or chosen after seeing a policy result.

## 5. Policies (identical budget, delay, costs, seeds in each comparison)

RMM on its 4 certificate hosts: `rmm:gated_deployment+RMM`, `rmm:discern_style+RMM`,
`rmm:SMCS+retain-incumbent+RMM`, `rmm:gated_adaptive_range+RMM`; the hosts `gated_deployment`,
`discern_style`, `SMCS+retain-incumbent`, `gated_adaptive_range`; `xu_acquisition_only`;
`gated_adaptive_range+front`; `choe_ramdas_eb+front`; `A5b`; nonstationary baselines
`qiu_delayed_movement`, `rmm:LRMD`, and `E_swcert` (new sliding-window certificate, fam_e, because no
sliding-window or discounted certificate is registered); RMM with B2-style certified rollback on all
4 hosts, `E_rb:<host>` (fam_e, `fam_b.RecoveryMonitor(rollback=True)` with each host); control
`CONTROL_never_switch`. 20 policies.

Contract: T = 2000, B = 200, c_q = .05, c_s = 5, alpha = .05; real seed base 2026110803
(bench2.REAL_SEED_BASE), **5 seeds per real episode** (a real seed only re-randomises label/prediction
coding and the policies' query coins; the episode is the unit). Twin Track-V run: the RMM, E_rb,
E_swcert, Xu, A5b, control subset, 5 seeds.

## 6. Primary analysis

* Per-episode cost `J = mean over seeds of net` (net = loss + .05 labels + 5 switches).
* Per class, contrasts `Delta = J(candidate) - J(comparator)` for each RMM host vs (a) its host,
  (b) the **best certified** comparator: the policy among {xu_acquisition_only,
  SMCS+retain-incumbent, gated_adaptive_range+front, choe_ramdas_eb+front, gated_deployment,
  discern_style, gated_adaptive_range} with the lowest mean J over that class's episodes (chosen per
  class on the same episodes, conservative for RMM), (c) `CONTROL_never_switch`.
* Inference: cluster bootstrap over **source datasets** (14 clusters: 9 cached + 5 UCI; the fresh,
  `win` and `exp` streams of one UCI dataset share a cluster), 2000 resamples, 95% percentile CI, plus
  the number of episodes and clusters. Classes with < 3 clusters get descriptive numbers only.
* **Registered hypothesis H_late.** Real data supports the synthetic late-improvement mechanism iff
  the real `late_improvement` class has >= 10 episodes from >= 3 clusters AND for >= 3 of the 4 hosts
  RMM's mean Delta vs best certified is < 0 with cluster-bootstrap CI upper bound < 0. If the class
  is too small, the verdict is `INSUFFICIENT_REAL_LATE_EPISODES`, reported as a limitation.
* Secondary: reversal class, RMM vs host and `E_rb` vs RMM (does certified rollback reduce reversal
  cost?); post-switch monitoring diagnostics (rollbacks, false rollbacks against the episode's
  realised segment means).

## 7. Sensitivity (key comparison only)

One factor at a time around the contract, on all real episodes, 3 seeds, policies: RMM gated, RMM
gar, RMM SMCS, `E_rb:gated_deployment`, Xu, gar+front, SMCS, choe+front, control.
Label delay {native x 0.5, native x 2}; budget {100, 400}; switch cost {2, 10} (the runner in
late_real.py takes these overrides; screen.py cannot for real streams). Synthetic budget sensitivity
uses the `@B` suffix: V_late_600, W_late_1000, F1_late_800, F1_late_1200, F3_reversal_800,
W_reversal_700 at B in {100, 200, 400}, 20 seeds at 2026110701.

## 8. New candidates (sprint-2 rules)

`E_rb:*` and `E_swcert` get unit tests, a 20-seed development screen at 2026110701 (targeted:
F3_reversal_800, W_reversal_700, S_reversal_400, V_late_600; null/adverse: F0_null, F5_dep_null_r8;
outside: F0_better, F4_recurrent), mechanism ablations (`E_rb` without horizon gate, at alpha_rb = .05;
`E_swcert` with W in {25, 100, cumulative}), Track R at bench2.ALPHA_GRID on RISK_NULLS + RISK_ALTS
(dev 2026110701, eval 2026110711), and Track V. Development evidence is not validation.

## Amendments

**A1 (2026-11-04, before any build finished, classification or policy run; lead's novelty audit,
docs/sprint2/novelty/NOVELTY.md section 1).** Added to the section-5 policy set and to the primary
and twin runs:
* `E_srr:<host>` for all 4 hosts: the host + an off-the-shelf Shin-Ramdas-Rinaldo e-CUSUM betting
  detector (start at every label, unit mass per start, same bets, same alpha split, same continued
  acquisition, same restart). `E_srrSR:gated_deployment` (e-SR variant).
  `E_srr_noacq:{gated_deployment, gated_adaptive_range}` (no continued acquisition).
  `E_glr:{gated_deployment, gated_adaptive_range}` (uncertified Bernoulli GLR restart, GLR-klUCB style).
  SRR detectors control the average run length only; Track V = none.
* RMM attribution ablations already registered: `rmm:gated_deployment+RMM_single`,
  `rmm:gated_deployment+RMM_noacq`, `rmm:discern_style+RMM_single`, `rmm:discern_style+RMM_noacq`,
  `rmm:SMCS+retain-incumbent+RMM_single`.
* Added secondary contrast (per class, cluster bootstrap): each RMM host vs `E_srr:<same host>`. If
  RMM is within noise of `E_srr` the write-up must attribute the gain to "detector + continued
  acquisition", not to RMM's mixture.
* The Giacomini-Rossi one-time-reversal diagnostic was later run post hoc; see A5.
* A6 (2026-11-04, post hoc): replayed five timestamp-retaining fresh UCI streams with RMM start
  positions laid out over elapsed timestamps, keeping the host event-clock based. Three paired
  seeds per episode, seed base 2026110803; 62 episodes, 372 policy rows. The known episode endpoint
  is used to allocate the timestamp grid. This does not reconstruct timestamps for nine cached
  loss-only streams or represent label publication-time delays. See
  `clock_ablation_posthoc3.md/json`; treat as exploratory, not registered evidence.

**A2 (2026-11-04, after the classification and before any policy run on real streams; compute).**
The shared machine is saturated (load ~17 on 10 CPUs, 2 workers per agent). Real seeds only
re-randomise query coins and label coding (the episode is the unit), so: primary real run 3 seeds per
episode (was 5); real sensitivity 1 seed per episode (was 3); twin Track-V run 3 seeds; Track R on
`E_rb:gated_deployment`, `E_srr:gated_deployment`, `rmm:gated_deployment+RMM`, `xu_acquisition_only`
only. Classification output at this point (frozen, outputs/sprint2/WP1/classes.json): real non-twin
late_improvement 10 episodes / 5 clusters, reversal 16, early_improvement 0.

**A3 (2026-11-04, after the primary run started and before any of its results were read; compute,
machine load > 40).** Real sensitivity runs only on the episodes the frozen classifier labels
`late_improvement` or `reversal` (26 non-twin episodes; selection by the outcome-blind classifier,
not by any policy result), 3 seeds, with a native-setting reference run on the same episodes and
seeds (`sens_delay1`); `E_srr:gated_deployment` added to the sensitivity policy set. Synthetic budget
sensitivity on V_late_600, W_late_1000, F3_reversal_800, W_reversal_700 at B in {100, 200, 400}.

**A4 (2026-11-04, post hoc scope completion; after the original Track-R outputs were available).**
The A2 resource amendment omitted E_swcert from the original section-8 Track-R list. Run E_swcert
alone on the same RISK_NULLS + RISK_ALTS, alpha grid, 20-seed development/evaluation bases
2026110701/2026110711, and T/B/cost contract. This fills the registered-policy coverage gap, but
because the add-on follows inspection of existing results, treat it as post hoc descriptive evidence.
Report it as a one-policy curve; its Pareto flag is not a comparison against other methods.

**A5 (2026-11-04, post hoc secondary diagnostic).** Implement the Giacomini–Rossi (2010) One-time
Reversal statistic (Proposition 3) on all cached, fresh, and constructed-late non-twin WP1 loss
episodes. Use `d_t=l0_t-l1_t`, a Bartlett/Newey–West long-run variance estimator with lag
`floor(4*(n/100)^(2/9))`, 15–85% trimming, and the paper's tabulated asymptotic critical values.
This is an exploratory retrospective diagnostic, not confirmatory inference: it reuses outcomes that
defined the WP1 classes, does not adjust across episodes/source clusters, and does not establish the
paper's FCLT/HAC assumptions on these streams.

**A7 (2026-11-04, post hoc comparator-class audit):** the frozen seven-policy “best certified”
pool contains the Xu acquisition + ShiftLab-certificate composite and the Choe–Ramdas port, and it
omits `discern_design_floor`. It is a tested certificate-adapter panel, not a complete published
certificate pool. A strict shared-pool sensitivity uses only the five available members of
`bench.CERTIFIED_PUBLISHED`; the sixth, `discern_design_floor`, was not run in this WP1 primary
panel. A strict shared-pool sensitivity uses the six members of `bench.CERTIFIED_PUBLISHED`; the
sixth, `discern_design_floor`, was replayed on the same streams and seed contract. At the default
setting, the selected late-class comparator remains `gated_adaptive_range+front`; the registered
verdict remains NOT_SUPPORTED. See `strict_published_subset_20261104.json` and the SOTA audit.

**A8 (2026-11-05, post hoc strict-pool sensitivity completion):** replayed the strict published
ports missing from the earlier reduced-panel sensitivity at B={100,400}, delay multipliers={0.5,2},
and c_s={2,10}; runs use the same 26 frozen late/reversal episodes, three seeds, and original seed
base. The six-port panel is assembled with matching earlier sensitivity records and supplemental
records. These remain selected-subset descriptive analyses; no independent confirmation is implied.
