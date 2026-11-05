# WP1 results: real-world validation of RMM late improvement (development evidence)

Protocol: [protocol.md](protocol.md), registered before any build, classification or real policy
run, with amendments A1 (e-detector competitor, lead's novelty audit), A2 (seeds, compute) and A3
(sensitivity restricted to classified late/reversal episodes). The protocol records the amendments
as preceding review of their relevant results; this chronology is not independently verifiable from
the saved result artifacts. Machine-readable outputs are
[results.json](results.json) (all contrasts, diagnostics, twin rates and sensitivity),
[trackR.md](trackR.md) and [screen_dev.md](screen_dev.md). Raw records are in `outputs/sprint2/WP1/`
(gitignored). The code is uncommitted on top of 1e46378 (`git` reports `+dirty`).

**Bottom line.**
* **Strict comparator-class analysis (post hoc):** the strict-pool analysis covers all 6 of 6
  registered published ports. `discern_design_floor` was replayed on the same 348 episodes and
  three-seed contract in a supplemental run, then joined to the frozen primary records. On the
  late-improvement class, `gated_adaptive_range+front` remains the lowest-cost port; the host-support
  count remains 0/4 and the verdict is **NOT_SUPPORTED**. See
  [strict_published_subset_20261104.json](strict_published_subset_20261104.json) and
  [COMPARATOR_CLASS_AUDIT.md](COMPARATOR_CLASS_AUDIT.md). This is a same-episode selected-subset
  sensitivity, not independent confirmation. See
  [COMPARATOR_CLASS_AUDIT.md](COMPARATOR_CLASS_AUDIT.md) for the pool definition and reproduction.
* **Comparator amendment:** the historical protocol and tables below include `xu_acquisition_only`,
  which uses Xu's acquisition component with ShiftLab's certificate; it is not Xu et al.'s published
  certificate. See [results_amended_no_xu.json](results_amended_no_xu.json) for the separately written
  analysis excluding Xu from certificate-comparator selection. It leaves the late-class best
  comparator as `gated_adaptive_range+front` and the registered verdict **NOT_SUPPORTED**. That
  amendment is same-sample/descriptive, not selection-adjusted confirmation. All comparator names
  below refer to common-contract methods/ports, not author-native deployments.
* The retrospective classifier labels 10 of 348 non-twin episodes as `late_improvement`, from 5 of
  14 dataset clusters, 4 of them from openml_ldpa. These labels are not verified causal shift times.
* On those 10 episodes RMM's point estimate is 32-39 per 2000 events below the selected certificate-policy comparator
  on all 4 hosts. No CI excludes 0, so **H_late is NOT_SUPPORTED** under the registered rule.
* RMM is significantly better than its own host and than Xu on late improvement, but not
  significantly better than the off-the-shelf SRR e-detector competitor.
* RMM loses to cheap certified methods on the large stationary-better class.
* B2-style rollback (`E_rb`) lowers reversal cost on every host. It costs a little on late and
  stationary episodes.
* **Post hoc CAMS-MAX baseline:** on the same 348 episodes, three seeds and native-delay contract,
  CAMS-MAX's mean J is 3.73 [1.30, 5.60] above CAMS (source-cluster bootstrap interval). On late
  improvements the difference is +5.29 [−2.33, +17.00], and on reversals −6.49 [−27.26, +17.67].
  See [cams_max_comparison.json](cams_max_comparison.json) and the comparator-fidelity discussion in
  [SOTA_BENCHMARK_AUDIT.md](../SOTA_BENCHMARK_AUDIT.md). This is a post hoc common-contract adapter
  comparison, not the paper's contextual benchmark reproduction.

## 1. Streams and classification (outcome-blind; `outputs/sprint2/WP1/classes.json`)

New chronological competitions are in `data/sprint_late_losses/` (stats.json holds hashes). They come
from 5 UCI datasets with HGB in both roles, refit for every episode, at a 4000-row deployment lag:
* `win`: incumbent window `[e-8000, e-4000)`, challenger `[e-4000, e)`;
* `exp`: incumbent on all data before `e-4000`, challenger `[e-2000, e)`.

Episode-level class counts:

| family | episodes | late_improvement | early_improvement | reversal | stationary_better | null |
|---|---|---|---|---|---|---|
| cached (9 streams) | 168 | 5 | 0 | 2 | 100 | 61 |
| fresh fixed pairs (5) | 62 | 2 | 0 | 3 | 52 | 5 |
| new `win` (5) | 59 | 2 | 0 | 6 | 27 | 24 |
| new `exp` (5) | 59 | 1 | 0 | 5 | 7 | 46 |
| **real total** | **348** | **10 (5 clusters)** | **0** | **16 (7 clusters)** | **186** | **136** |
| twin known-null (splits 0-1) | 124 | 1 | 0 | 2 | 25 | 96 |

* Late episodes by dataset: openml_ldpa 4, beijing_pm25 2, bike_hour 2, household_power 1, uci_occupancy 1.
* Reversal episodes by dataset: household_power 6, beijing_pm25 5, and one each from airlines, uci_occupancy,
  metro, bike_hour and appliances.
* Classifier false-positive check: 3 of 124 twin episodes (2.4%) were classified as a change. On real
  episodes the rate was 62/348 (18%) significant changes, but only 26 of them met the
  effect-size/sign rule.
* Rule sensitivity: delta = .005 gives late 8, reversal 16; delta = .02 gives late 12, reversal 15.
* The new constructions add little late improvement (3 episodes). They mostly produce reversals:
  recency-trained challengers start better and then decay.

## 2. Primary: per-class paired contrasts

Units are episodes, each the mean of 3 seeds. The contract is T=2000, B=200, c_s=5, native delays.
Intervals are 95% cluster-bootstrap CIs over source datasets. Delta J < 0 means the first policy is
better.

| class (episodes / clusters) | best certified | RMM gated | RMM discern | RMM SMCS | RMM gar |
|---|---|---|---|---|---|
| late_improvement (10/5): vs best certified | gar+front | −37.9 [−68.0, +11.4] | −38.8 [−69.1, +2.8] | −34.7 [−68.2, +17.7] | −32.0 [−59.3, +8.1] |
| late: vs own host | | −93.1 [−143, −22.5] | −118.7 [−174, −21.0] | −55.1 [−75.2, −19.9] | −64.4 [−90.9, −16.7] |
| late: vs E_srr (same host) | | +6.3 [−4.5, +13.1] | +4.4 [−20.4, +23.3] | +7.1 [−0.1, +11.2] | +9.3 [−11.9, +23.7] |
| reversal (16/7): vs best certified | discern_style | +30.3 [−60.3, +56.9] | +37.2 [−61.8, +69.8] | +35.7 [−60.5, +72.1] | +29.3 [−77.1, +59.6] |
| reversal: vs E_srr | | +26.5 [+0.7, +34.9] | +31.5 [+3.3, +46.3] | +36.8 [+18.8, +50.0] | +33.2 [−2.7, +46.4] |
| stationary_better (186/13): vs best certified | choe_ramdas_eb+front | +12.5 [+4.8, +22.8] | +11.2 [+4.2, +20.1] | +6.4 [+0.3, +13.8] | +12.1 [+5.1, +20.8] |
| null (136/10): vs best certified | gated_deployment | +4.9 [+1.5, +9.6] | +5.0 [+1.6, +10.3] | +6.0 [+1.7, +12.1] | +4.6 [+1.6, +9.3] |
| all real (348/14): vs best certified | gar+front | −1.2 [−16.8, +10.4] | −1.6 [−17.1, +9.3] | −3.7 [−17.4, +6.1] | −1.4 [−16.6, +9.3] |

* **Mean J on late_improvement:**
  * RMM gated 417.5, E_srr gated 411.1, rmm:LRMD 420.5, qiu_delayed_movement 428.5, E_swcert 439.2;
  * gar+front 455.4, choe+front 456.2, Xu 462.3, A5b 500.4, control 525.3.
  * RMM gated vs Xu: −44.9 [−56.6, −19.4]. The gain over Xu is significant; the gain over the best
    certified method is not.
* **Heterogeneity in the late class** (RMM gated − gar+front, per episode):
  * −279, −110 and −89 on openml_ldpa ep3, openml_ldpa ep8 and beijing_win ep4;
  * +67 and +34 on openml_ldpa ep2 and bike_exp ep0;
  * the other five are between −24 and +16.
  * The mean rests on three episodes.
* **Registered H_late:** the class has enough episodes (10 from 5 clusters), but 0 of 4 hosts have a
  CI upper bound below 0. Verdict: **NOT_SUPPORTED** (direction consistent, underpowered).
* **Attribution ablations** (late class; RMM − ablation):
  * RMM vs `_single` (no restart mixture): −45.5, −40.8, −48.1 (gated, discern, SMCS), all CIs < 0.
  * RMM vs `_noacq` (no continued acquisition): −34.5 [−62.0, +1.2] gated and −5.8 [−12.8, +1.2]
    discern.
  * So, unlike sprint-1 synthetic attribution, the restart mixture matters on these 10 real late
    episodes.
  * On all 348 real episodes: `_single` gives about 0, and `_noacq` gives −4.5 (gated) and −4.0
    (discern), both CIs < 0.
* **SRR e-detector competitor** (`E_srr`: host + SRR e-CUSUM + the same alpha split, continued
  acquisition and restart):
  * RMM is never significantly better than E_srr on late episodes (+4 to +9).
  * E_srr is significantly better on reversals (RMM − E_srr = +26 to +37, 3 of 4 CIs > 0).
  * RMM is better on null episodes (−4.5 to −5.9).
  * E_srr buys this by not controlling false promotion (sections 4-5).
  * E_srr's own continued acquisition is worth −40.5 [−69.4, −6.3] on late episodes.
  * Per the A1 rule: on real late episodes RMM's gain cannot be attributed to its specific mixture
    over a generic e-detector. On iid synthetic nulls RMM's mixture does buy validity.
* **GLR restart** (`E_glr:gated`, uncertified): worse than RMM on all real episodes (−44.2 for RMM),
  because it rarely promotes on stationary-better episodes.

## 3. Reversal, post-switch monitoring and certified rollback

On reversal episodes (16), means per episode-seed:

| policy | promote | rollbacks | switches | J |
|---|---|---|---|---|
| RMM gated | .83 | .48 | 1.31 | 594.3 |
| E_rb gated | .83 | .56 | 1.42 | 581.2 |
| E_srr gated | 1.00 | 1.15 | 2.48 | 567.8 |
| Xu | .46 | .17 | .63 | 583.5 |
| control | 0 | 0 | 0 | 621.6 |

* **E_rb vs RMM, reversal class:**
  * −13.0 [−18.1, +2.7] gated, −12.4 [−24.0, −2.1] discern, −19.6 [−31.0, −0.7] SMCS,
    −17.1 [−23.9, +1.8] gar.
  * Synthetic F3/W_reversal: −3.5 to −13.2, most CIs < 0.
* **The price of E_rb:**
  * late class +2.5 to +10.4 (CIs touch 0);
  * stationary_better +1.2 to +1.5 (CIs ≥ 0);
  * all real episodes, net −0.1 to +0.3 (n.s.).
* **E_rb ablations** (synthetic): the horizon gate never bound (identical to `-nogate`). Using alpha_rb
  = .05 instead of .10 lost 4-6 on reversals. So the gain comes from the higher rollback level and the
  start grid on the remaining budget.
* RMM still does not beat the best certified method on reversals (+29 to +37, wide CIs). The reversal
  cost is reduced, not removed.

**False-rollback trace diagnostic.** The follow-up replayed all 348 primary real episodes, 3 seeds,
and the 4 E_rb hosts (1,044 episode-seed jobs; 4,176 policy rows), preserving event times for each
rollback. A rollback is classified as false when the frozen outcome-blind episode classifier's
realised segment-mean gain at the rollback event is >= 0. These are evaluator-side retrospective
labels, not outcomes available to the policy. In the late-improvement class all observed rollbacks
were in the positive-mean segment: gated 7/7, DISCERN 5/5, SMCS 8/8, GAR 5/5. In the reversal class,
false rollback rates were 4/27, 4/27, 4/26 and 2/26, respectively. In stationary-better episodes
they were 35/45, 27/35, 26/38 and 31/42; in null episodes 5/25, 6/27, 4/31 and 3/23. The
source-cluster bootstrap intervals and full event list are in
[`false_rollback_audit.json`](false_rollback_audit.json). The late-class counts are small and the
classifier is retrospective, so this is mechanism diagnosis rather than a real-world false-alarm
rate or validity result.

## 4. Track V: twin known-null promotion

Twin streams, splits 0-1, 124 episodes x 3 seeds; nominal .05. The null tested by RMM and E_rb is V1
(iid conditional).

| policy | promotion rate |
|---|---|
| RMM gated / discern / SMCS / gar | .220 / .218 / .272 / .223 |
| E_rb gated / discern / SMCS / gar | identical to their RMM hosts (rollback cannot change the first promotion) |
| E_srr gated / gar | .409 / .406 (ARL-only, Track V: none) |
| E_swcert | .228 |
| Xu | .134 |
| A5b (V2) | .032 |
| control | 0 |

On iid synthetic nulls (dev screen, 20 seeds):
* F0_null: RMM, E_rb and E_swcert all promote 0; E_srr .05-.20; E_srrSR 1.00.
* F5_dep_null_r8 (persistent; V1 not claimed): RMM and E_rb .15-.25; E_srr .55-.85; E_swcert .05.

## 5. Track R (dev 2026110701 / eval 2026110711, 20 seeds, RISK_NULLS + RISK_ALTS)

| policy | R5 / R10 operating point | R15 / R20 |
|---|---|---|
| xu_acquisition_only | R5: none; R10: alpha .5, risk .013, cost 387.0 | same R10 point |
| rmm:gated_deployment+RMM | none | alpha .01 / .02: risk .10, cost 390.8 / 386.3 (Pareto at R20) |
| E_rb:gated_deployment | none | alpha .01 / .02: risk .10, cost 392.2 / 388.1 |
| E_srr:gated_deployment | none | none |

* E_srr reaches an operating point only at R30: risk .31, cost 371.9.
* The risk is driven by the rho = .95 persistent null.
* E_srr's synthetic cost advantage is bought with risk.

## 6. Sensitivity (A3: the 26 late + reversal episodes, 3 seeds; one factor at a time)

| setting | late: RMM gated − best certified | late: RMM gar − best certified | reversal: E_rb − RMM (gated) |
|---|---|---|---|
| native (reference) | −37.9 [−68.0, +11.4] | −32.0 [−59.3, +8.1] | −13.0 [−18.1, +2.7] |
| delay x0.5 | −41.6 [−53.8, −26.9] | −38.9 [−50.8, −25.0] | −15.2 [−27.5, −2.2] |
| delay x2 | −28.2 [−59.5, +25.8] | −16.5 [−43.4, +31.1] | −11.3 [−22.9, +2.6] |
| B = 100 | −11.6 [−62.7, +75.6] | −7.1 [−62.9, +89.2] | −1.4 [−1.8, −0.4] |
| B = 400 | −33.4 [−52.1, −8.4] | −32.4 [−52.0, −7.1] | −2.8 [−6.2, −0.1] |
| c_s = 2 | −40.2 [−71.2, +9.9] | −34.3 [−62.5, +7.7] | −13.3 [−18.5, +2.5] |
| c_s = 10 | −34.1 [−63.4, +13.7] | −28.1 [−53.9, +10.4] | −12.5 [−17.5, +3.2] |

* The best certified comparator is re-selected in each setting from the reduced panel (Xu, gar+front,
  SMCS, choe+front).
* The late advantage becomes significant with shorter delays or a larger budget, and vanishes at
  B = 100.
* Synthetic `@B` (20 seeds), e.g. V_late_600 at B = 100 / 200 / 400:
  * RMM gated 397.8 / 370.9 / 363.5;
  * Xu 401.2 / 399.4 / 380.7;
  * gar+front 408.8 / 413.0 / 416.7.
* Synthetic conclusion: RMM's late gain needs B ≥ 200.

## 7. Assessment

* **Does real data support the synthetic late-improvement mechanism?**
  * Partly, and only descriptively. Genuine late improvements exist but are rare: 2.9% of real
    episodes, with 4 of the 10 from one cached stream.
  * There, RMM's direction matches the synthetic claim, and it beats its host and Xu significantly.
  * The registered test against the best certified method fails (CIs cross 0). It would need roughly
    3x more late episodes from more clusters.
  * The new historical schedules mainly generate reversals, not late improvements.
* **RMM's specific mixture vs a generic e-detector:** on real late episodes RMM is within noise of
  host + SRR e-CUSUM + continued acquisition. RMM's distinguishing value is false-promotion control:
  * iid null 0 vs .05-.20;
  * Track R points at R15/R20 vs none.
  * On twin nulls it still promotes .22-.27, so that value does not survive real persistence.
* **Rollback:** E_rb is the one mechanism here with a consistent, if modest, improvement: reversal −12
  to −20 across 4 hosts on real data, and −4 to −13 synthetic, with no change to first-promotion
  validity.
* **Continue / pivot / stop:**
  * Continue E_rb as an RMM extension.
  * Pivot the RMM real-data claim to "beats its host and Xu; not shown to beat the best certified
    method; no evidence it beats a generic e-detector on real late episodes".
  * Stop claiming RMM-specific novelty on real late improvement.
* **Limitations:**
  * Development-exposed raw data.
  * 3 seeds per real episode (A2), and sensitivity only on classified episodes (A3).
  * A post hoc label-clock vs elapsed-timestamp start-grid replay covers five fresh UCI streams (62 episodes, 3 seeds; `clock_ablation_posthoc3.md/json`). Equal-dataset mean ΔJ was −0.61, with a five-dataset cluster-bootstrap 95% CI [−5.85, +2.41]. This is exploratory; it does not cover nine cached loss-only streams or publication-time delays. The Giacomini-Rossi diagnostic below is also post hoc and full-sample.
  * False-rollback traces are now available; they use the evaluator's segment-mean classification and
    do not establish the policy's conditional expected gain at each rollback.
  * The classifier's delta and block length are conventions.
  * The cluster bootstrap with 5-7 clusters is coarse.
  * `E_srr` is a Python re-implementation; `edetect` is R-only.

## Reproduce

    uv run python scripts/sota_sprint/late_real.py build
    uv run python scripts/sota_sprint/late_real.py classify --streams all,twin --out outputs/sprint2/WP1/classes.json
    bash outputs/sprint2/WP1/run_all.sh   # primary line only (it was stopped after primary; see A3)
    bash outputs/sprint2/WP1/run_rest.sh  # twin, sensitivity, synthetic budget, Track R
    uv run python scripts/sota_sprint/screen.py --regimes F3_reversal_800,W_reversal_700,S_reversal_400,V_late_600,W_late_1000,F0_null,F5_dep_null_r8,F0_better,F4_recurrent --policies $(cat outputs/sprint2/WP1/screen_policies.txt) --seeds 20 --seed-base 2026110701 --workers 2 --out outputs/sprint2/WP1/screen_dev
    uv run python scripts/sota_sprint/late_real.py report --primary outputs/sprint2/WP1/primary --twin outputs/sprint2/WP1/twin --sens outputs/sprint2/WP1/sens_* --classes outputs/sprint2/WP1/classes.json --out docs/sprint2/wp1/results.json
    uv run python scripts/sota_sprint/wp1_false_rollback.py --workers 4
    (cd scripts/sota_sprint && uv run python risk_curves.py --dev ../../outputs/sprint2/WP1/trackR_2026110701_a* --eval ../../outputs/sprint2/WP1/trackR_2026110711_a* --out ../../docs/sprint2/wp1/trackR.json)
    uv run pytest -q tests/sprint2/test_late_real.py   # 60 passed

## Round-5 status audit (2026-11-04)

The ledger's `E_rb` next action says “Round-5 fresh-seed reversal,” but the registered WP1 protocol
does not define that follow-up. The general sprint specification supplies the Round-5 seed base
(`2026110801`) and minimum size (100 seeds), but it does not specify which reversal regimes to use,
which E_rb host(s) and comparator policies to include, or the primary statistic/decision rule for
this check. WP1 section 8 defines a 20-seed **development** screen and the existing primary real
reversal analysis; neither is a registered Round-5 evaluation. No WP1 output manifest uses the
Round-5 seed base. At the time of this original status audit the fresh-seed reversal check was not
run. A later dated post-development sensitivity is now recorded below; it used a separately
registered seed base and must not be described as untouched Round-5 validation.

To make a future run interpretable, a dated prospective amendment must specify the regimes, exact
policy names/hosts and paired contrast, seed count and seed base, primary metric and interval or
decision rule, and output path before the new results are inspected. Because the development results
are already known, that run must be labelled a post-development follow-up rather than an untouched
confirmatory evaluation.

## Post-development reversal sensitivity (2026-11-04)

A preregistered 100-seed follow-up is recorded in `AMENDMENT_20261104_E_RB.md` and raw records at
`outputs/sprint2/round5/wp1_erb_reversal_postdev100/`. Across three synthetic reversals and four
matched hosts, `E_rb` minus matched RMM mean net cost was **-6.65** (95% t interval **[-7.31,
-6.00]**, 100 seed blocks). All 12 exploratory host-by-regime mean contrasts were negative with
uncorrected intervals below zero. This supports the rollback extension in these simulator reversal
settings. It is post-development, uses simulated regimes, and does not validate real-world reversal
benefit, overall null validity, or an anytime guarantee. Analysis: `erb_reversal_postdev100.json`;
reproduce with `scripts/sota_sprint/analyze_wp1_erb_postdev.py`.

## E_swcert Track R (post hoc completion of the A2 omission)

The A2 compute amendment omitted E_swcert from the original section-8 Track-R list. The policy was
run separately on the same frozen ten-regime mix, eight-alpha grid, 20 development seeds (base
2026110701), and 20 evaluation seeds (base 2026110711). This completes the missing operating-curve
screen, but it is explicitly a post hoc scope completion and not a confirmatory test.

Development selected no alpha for R5, .005 for R10, .1 for R15, .2 for R20, and .3 for R25/R30.
Evaluation risks were .0625 (95% Wilson [.0270,.1381]) at R10, .1875 ([.1171,.2866]) at R15,
.2000 ([.1270,.3005]) at R20, and .2375 ([.1576,.3414]) at R25/R30. The R10 operating point
had point risk below the .10 target, but its 95% Wilson interval upper bound (.1381) crossed the
target. These empirical rates are descriptive, not guarantees. Alternative
costs were 402.8, 371.7, 368.8, and 363.3 respectively; since this is a one-policy curve, its Pareto
flags do not compare E_swcert against other methods. Raw records are in
`outputs/sprint2/WP1/trackR_E_swcert_{dev,eval}_a*`; the summary is `trackR_E_swcert.json`.

## Giacomini–Rossi one-time-reversal diagnostic (post hoc)

I implemented Giacomini and Rossi's (2010) Proposition 3 statistic for each of the 348 registered
non-twin WP1 loss episodes (cached, fresh and constructed-late streams; 14 source clusters), using
`d_t = l0_t-l1_t`, a Bartlett/Newey–West long-run variance estimate, the paper's 15–85% trim, and
the tabulated 5% critical values. The omnibus Q statistic rejected in 10/10 late-improvement, 16/16
reversal, 79/135 null, and 157/186 stationary-better valid episodes; one zero-variance episode was
undefined and excluded. The LM2 break component rejected in 10/10, 16/16, 35/135 and 63/186,
respectively. These raw episode-level frequencies are not multiplicity-adjusted or cluster-inferential.

The late/reversal results are circular with respect to the registered WP1 class: that classifier also
uses these same complete loss sequences to find and label a break. The diagnostic is retrospective;
its asymptotic assumptions (including a functional CLT and consistent positive long-run variance)
are not established for these binary, dependent streams. It neither verifies causal change times nor
supports an online or anytime-valid claim. The test is Giacomini & Rossi, “Forecast comparisons in
unstable environments,” *Journal of Applied Econometrics* 25(4), 595–620 (2010),
[doi:10.1002/jae.1177](https://doi.org/10.1002/jae.1177). Full per-episode values and limitations are
in `gr_one_time_reversal.json`; reproduce with `uv run python scripts/sota_sprint/wp1_giacomini_rossi.py`.
