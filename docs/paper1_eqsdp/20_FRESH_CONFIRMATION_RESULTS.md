# 20 — Fresh chronological confirmation: results

Protocol: [19_FRESH_CONFIRMATION_PROTOCOL.md](19_FRESH_CONFIRMATION_PROTOCOL.md) (locked at `1c5f2fdd`, before any
data was fetched). Everything below was produced by the committed scripts; every number is copied from
`docs/paper1_eqsdp/fresh_results/` (the analysis outputs). This is the single confirmatory opening.

## 1. Provenance

| item | value |
|---|---|
| protocol commit | `1c5f2fdd` |
| build + registration + scripts commit (before any policy ran) | `e1948471` |
| run code SHA recorded in records | `e194847106041476a0bd646046dfd1dc6133704c` (rows carry `+dirty` where only the CLI of `fresh_confirm_run.py` had changed, see §6) |
| registration | `docs/paper1_eqsdp/fresh_registration.json` (seed base 2026111901, 10 policy seeds, contract B=200, c_q=.05, c_s=5, T=2000) |
| per-source builds | `docs/paper1_eqsdp/fresh_builds/<name>.json` |
| merged records | `outputs/paper1_eqsdp/fresh/records_all.jsonl` (164,100 rows = 547 episodes x 10 seeds x 30 policies; sha256 `32d1873e46f16778135383d210d91dce8260cc1a182d66dd0e137be36e6d7254`; not committed) |
| analysis | `python scripts/paper1_eqsdp/fresh_confirm_analyze.py --records outputs/paper1_eqsdp/fresh/records_all.jsonl --out outputs/paper1_eqsdp/fresh` |
| committed result tables | `docs/paper1_eqsdp/fresh_results/` |

Commands:

```
# build (per source; windows per doc 19 section 2)
python scripts/qsg_methods_search/c4_build.py build <name> --fetch --window 2025-07-01 2026-07-01 --tag fresh   # sf dallas kc austin cincinnati oakland
python scripts/qsg_methods_search/c4_build.py build <name> --fetch --window 2025-01-01 2026-01-01 --tag fresh   # dc sandiego
python scripts/paper1_eqsdp/fresh_register.py
# run (checksums verified against the registration before any policy runs)
python scripts/paper1_eqsdp/fresh_confirm_run.py --out DIR --workers N [--only DS] [--part core|panel]
```

Sealed arrays are `data/c4_sealed/<name>__fresh.npz` and raw downloads are in `data/raw/c4_fresh/<name>/`;
both are gitignored and were not committed. The builder never printed or recorded any test-window statistic;
no test arrays were inspected before the registration commit. The smoke test of the runner used the old
`sf_311` data and reproduced the stored search60 `P2_K2__E48_F60` records and all 25 comparators' stored
sota_nine records bit-exactly (net cost, 0 mismatches) before the fresh data was touched.

## 2. Eligibility (unchanged C4 gates)

| dataset | window | rows after filter (used) | validation disagreement | err inc / chal | base rate | episodes | eligible |
|---|---|---|---|---|---|---|---|
| sf_311 | 2025-07-01 to 2026-07-01 | 890,146 (400,000 systematic) | .175 | .256 / .207 | .715 | 100 | yes |
| dallas_311 | 2025-07-01 to 2026-07-01 | 435,164 (400,000 systematic) | .187 | .271 / .212 | .636 | 100 | yes |
| kc_311 | 2025-07-01 to 2026-07-01 | 161,000 | .167 | .294 / .221 | .656 | 40 | yes |
| austin_311 | 2025-07-01 to 2026-07-01 | 286,170 | .332 | .250 / .229 | .766 | 71 | yes |
| cincinnati_311 | 2025-07-01 to 2026-07-01 | 157,285 | .245 | .377 / .248 | .769 | 39 | yes |
| oakland_311 | 2025-07-01 to 2026-07-01 | 111,230 | .042 | .161 / .156 | .203 | 27 | **no** (27 < 35 episodes; other gates pass) |
| dc_311 | 2025-01-01 to 2026-01-01 | 440,600 (400,000 systematic) | .295 | .281 / .109 | .614 | 100 | yes |
| sandiego_311 | 2025-01-01 to 2026-01-01 | 389,970 | .139 | .191 / .135 | .737 | 97 | yes |
| montgomery_traffic | none (registered window already ends 2026-07-01) | | | | | | excluded in advance |

K = 7 eligible datasets, 547 episodes. Oakland is reported as ineligible and was not replaced or repaired.
Sealed-array hashes are in `fresh_registration.json`.

## 3. Primary and secondary hypotheses (doc 19 section 3)

J = net cost per episode / T x 100 (pp of T). Delta = arm minus reference, equal-dataset mean of the
per-dataset mean paired episode difference; the CI is the stratified episode bootstrap (2000 resamples, rng
seed 0). Pass rules, scripted in `fresh_confirm_analyze.py`: H1 passes iff delta < 0, bootstrap 95% CI upper
bound < 0 and dL/T <= +0.1 pp. H2 and H3 pass iff delta < 0, Holm-adjusted (two tests) two-sided bootstrap
p < .05 and dL/T <= +0.1 pp. The bootstrap p is 0 in all three (no resample >= 0 of 2000, i.e. p < .0005, so the
Holm-adjusted p < .001).

| hypothesis | cand vs ref | delta J (pp) | % of ref J | 95% CI delta J | 95% CI % | dL/T (pp) | datasets neg | dataset t one-sided | size | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| **H1** (primary) | EQ+pair vs EQ+cut | -0.0903 | -0.391 | [-0.1300, -0.0491] | [-0.564, -0.213] | -0.019 | 7/7 | .0015 | small | **PASS** |
| H2 | W+pair vs W+cut | -0.0894 | -0.387 | [-0.1294, -0.0482] | [-0.560, -0.208] | -0.018 | 7/7 | .0019 | small | PASS |
| H3 | EQ+pair vs W+cut | -0.0899 | -0.389 | [-0.1298, -0.0489] | [-0.562, -0.212] | -0.018 | 7/7 | .0018 | small | PASS |

The 97.5% CIs (Holm first level) also exclude 0: H2 [-0.1349, -0.0442], H3 [-0.1348, -0.0448]. Size grade is
"small" (< 0.5% of reference J) for all three, as anticipated in doc 19 (development estimate -0.41%).

Labels and switches (equal-dataset means): EQ+pair 55.04 labels and 1.117 switches per episode; relative to
EQ+cut it uses 21.1 fewer labels (-21.10) and 0.075 fewer switches. For W+pair vs W+cut: -21.05 labels,
-0.076 switches. Tail (per-episode delta J, pp): CVaR95 = +0.972 (H1), +0.974 (H2), +0.970 (H3); worst episode
+3.83 in all three, i.e. some episodes are hurt by the add-on although the mean is lower.

Per-dataset delta J (pp), H1 / H2 / H3:

| dataset | H1 | H2 | H3 |
|---|---|---|---|
| austin_311 | -0.063 | -0.063 | -0.063 |
| cincinnati_311 | -0.065 | -0.063 | -0.065 |
| dallas_311 | -0.174 | -0.174 | -0.174 |
| dc_311 | -0.105 | -0.106 | -0.105 |
| kc_311 | -0.020 | -0.014 | -0.015 |
| sandiego_311 | -0.124 | -0.126 | -0.126 |
| sf_311 | -0.081 | -0.080 | -0.082 |

Equal-dataset mean J: EQ+pair 23.013, EQ+cut 23.104, W+pair 23.014, W+cut 23.103, arm R (no cutoff) 23.373.
On this data the EQSDp and Wald parents are practically identical once the cutoff is applied, so H1, H2 and H3
are close to one another and are not independent confirmations.

**Decision per doc 19:** H1 passes, so the add-on claim (cutoff H=1100 + E48 + F60 over the cutoff parent) is
confirmed on fresh data **at its graded size, small (-0.39% of J)**. It is not a large effect.

## 4. Panel comparison (descriptive; doc 18 claim on fresh data)

Pooled equal-dataset delta J against each of the 25 comparators plus arm R (`panel_pooled.csv`):

- EQ+pair is lower than every one of the 26 references: bootstrap 95% CI upper bound < 0 for 26/26 and the
  dataset-level t 95% CI upper bound < 0 for 26/26; at least 6 of 7 datasets negative for each reference.
  Smallest pooled gap: -0.238 pp (-1.02%) vs `econF_mo5_m0`; largest: -3.556 pp (-13.4%) vs `han_arw_label_clock`.
- EQ+cut (the doc 18 method) is also lower than all 26: bootstrap and t upper bounds < 0 for 26/26. Smallest
  pooled gap: -0.148 pp (-0.64%) vs `econF_mo5_m0`; at least 5 of 7 datasets negative for each reference.

Per-dataset >= SOTA (amendment 11, per-dataset 95% one-sided bootstrap upper bound < 1% of the comparator's
mean J, required against all 25 comparators):

| arm | datasets >= SOTA | comparator-dataset pairs strictly superior (U < 0) |
|---|---|---|
| EQ+cut | **7/7** | 163/175 |
| EQ+pair | **7/7** | 168/175 |

The seven pairs where EQ+pair is non-inferior but not strictly superior: austin vs `model_picker_adapter`; dc vs
`model_picker_adapter`, `online_llm_picker`, `econF_mo5_m5`, `econF_mo5_m0`; kc vs `econF_mo5_m5`, `econF_mo5_m0`
(see `panel_per_dataset.csv`). The best mean-J policy per dataset is EQ+pair on 5/7, W+pair on dc, and `econF_mo5_m0`
on kc.

## 5. Interpretation

- Fresh evidence supports both Paper 1 statements: (i) doc 18, the cutoff method (EQ+cut) is at least as good as
  all 25 uncertified comparators on every fresh dataset and lower than all of them when pooled, and (ii) the
  E48+F60 add-on gives a consistent, small, additional cost reduction (7/7 datasets, all three hypotheses).
- These are cost-decision results for the stated contract (B=200, c_q=.05, c_s=5, delay 100), not harm-detection
  or certification results, and they say nothing about validity of the e-process null.

## 6. Caveats and deviations

1. **Run in stages.** The first launch (16 workers, all 30 policies) completed sf, dallas and kc (2,400 jobs) and
   then the multiprocessing pool stalled on austin with idle workers. It was killed, and its austin partial rows
   were discarded; the three completed datasets' rows (72,000) were kept. austin, cincinnati, dc and sandiego were
   rerun per dataset, first the five core policies (`--part core`) and then the 25 comparators (`--part panel`),
   with a stall watchdog (`driver_py.txt`, 8 to 10 workers). Policy outputs are independent of job grouping (same
   rng derivation per policy, bit-exact reproduction in the smoke test), so the merged table equals a single
   run. The final merged table has exactly 10 seeds, 30 policies and no duplicates per episode. The `+dirty` rows
   come from the working tree having an uncommitted CLI change (`--only`/`--part`) in `fresh_confirm_run.py`;
   policy code was unchanged.
2. **Builder change.** `c4_build.py` gained `--window/--tag` (default behaviour unchanged). For `dc_311`, the DCGIS
   publisher splits by calendar year, so the fresh build uses the same service's layer 18 (All Service
   Requests, 2025) instead of layer 16 (2024); schema and recipe are otherwise identical. `sandiego_311`
   already fetches closure-year files (closed_2024/2025/2026 and open), so only the window changed. Other sources
   query their APIs by date. Receipts are next to the raw downloads (not committed).
3. **Systematic subsample.** The builder subsamples to 400,000 rows where the window has more (sf, dallas, dc),
   as in C4.
4. **Dependence.** The bootstrap resamples episodes as independent within a dataset; episodes within a dataset are
   consecutive windows of one stream with the same fitted pair, so the bootstrap CIs are likely too narrow.
   The dataset-level one-sided t-test (K = 7, p = .0015 to .0019) and the 7/7 sign count are the more
   conservative readings, and they agree. With K = 7 and seven similar 311 closure-time tasks from US cities, the
   result is not evidence of generality outside this domain.
5. **Holm.** The Holm-adjustment for H2/H3 is applied to bootstrap p-values (both < 1/2000), so it is not
   binding here. The ">= 1% non-inferiority" margin is the amendment 11 rule, not a pre-registered effect size
   for this study.
6. **Fresh is chronological, not independent.** Each fresh window starts where the registered C4 window ended,
   from the same publishers; models were retrained on the new window by the unchanged builder. Market-style
   causal change labels are not claimed.
7. **Downside tail.** The add-on is not uniformly better per episode: CVaR95 of per-episode delta J is about
   +0.97 pp and the worst episode +3.83 pp, so the claim is about the mean cost.

## 7. Assessment

**Continue.** H1 (primary), H2 and H3 all pass at the "small" graded size, 7/7 datasets agree, and the doc 18
cutoff method reproduces its panel result on fresh data (>= SOTA on 7/7 datasets). Keep EQ+cut as the Paper 1
method result and report E48+F60 as a confirmed small incremental add-on. No further tuning, no extra arms
(any new variant is exploratory). The next reasonable step is a second fresh period or additional (non-311)
publishers only if a larger-effect claim is wanted, because the confirmed effect is below 0.5% of J.
