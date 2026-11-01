# 15. Real-data admissibility audit for a certified model-switching policy

Date 2026-11-01. Status: development-window audit only. No method was run. No confirmatory claim.

## 0. Bottom line

- No local dataset shows convincing net switching headroom on its dev window once switch and query costs are charged.
- Two datasets show a real but small, time-structured paired advantage:
  - Elec2: structured but small headroom. It is exposed, and its file-order chronology is untrusted.
  - Criteo click: a large, persistent, non-switching challenger advantage. "Always challenger" is optimal there.
- Gas is exposed. NOAA (constructed precipitation label) shows noise-level headroom.
- Folktables, WILDS and the forecasting datasets are not event streams for this method.
- Recommendation: do not freeze a confirmatory real-data claim yet. If a real-data section is required, use the two "reference" streams in section 5 and label them exposed / descriptive. Their roles differ: Elec2 for switching mechanics, Criteo for promotion economics.

## 1. Locked evaluation window (hard rule) and how it was honoured

For every stream, events were ordered chronologically. The final 40% is locked: no label, loss or prediction from it was read, computed, summarised or plotted.

Enforced in code (`scripts/promising_directions/realdata_audit/run_audit.py`, `run_criteo.py`). The loader slices before parsing any outcome:

| Stream | How the locked tail was kept unread |
|---|---|
| Elec2 | Raw text lines sliced to the first 27,187 before CSV parsing. The tail was only counted. |
| Gas | Raw text lines sliced to the first 8,346 before parsing labels. |
| NOAA | Step 1 reads only `STATION` and `DATE` for every row (feature-free). It builds the event list, ranks it and fixes the cut hour. Step 2 reads measurement and precipitation columns only for rows with `DATE` earlier than the locked start. Events whose next-hour label hour reaches the locked start were purged (4 events). |
| Criteo | `nrows` = first 9,880,816 rows, then a 1-in-10 subsample. Events whose 1-day label would mature after the end of the early window were purged. |

The only things recorded about the tail are feature-free counts and times (in the table in section 3).

Caveat: the Elec2 and Gas locked windows were opened by earlier branches (section 2). The rule above binds this audit, not those prior analyses. Earlier exposure is a property of the data, not of this audit.

Pre-stated selection rule (written in the `run_audit.py` docstring before any number was computed):

- Early 60% → train = first 30% of all events, dev = next 30%.
- Five fixed pairs, with old = first half of train and new = second half of train:
  - A: LR_old vs LR_new
  - B: LR_old vs HGB_new
  - C: LR_all vs HGB_all
  - D: HGB_old vs HGB_new
  - E: LR_all vs HGB_new
- LR = median-impute, standardise, logistic regression. HGB = HistGradientBoosting, 100 iterations. Preprocessing is fit on each model's own training slice only.
- Eligible: dev disagreement ≥ 5%.
- Rank eligible pairs by H_net(s=5, q=0.05), keep the top 2.
- Headroom uses 0/1 loss with the incumbent as the start state:
  - H(s) = min(Σl0, s + Σl1) − DP_opt(s).
  - DP_opt(s) is the hindsight-optimal switching cost, charged s per switch.
  - H_net = H(5) − 0.05 × (#disagreement events). This is a pessimistic query burden: every disagreement is labelled.
- Also reported: a net figure with 25% of disagreements labelled, and a time-shuffled null (20 permutations of the paired losses; 5 for Criteo). The p95 of the shuffled headroom shows how much "headroom" is just noise-chasing.

Software: sklearn 1.6.1 is available, so no numpy fallback was used. Compute: CPU, under 2 minutes in total. Raw data was not copied into git.

## 2. Integrity (sha256) and exposure audit

### 2.1 Integrity

`scripts/promising_directions/realdata_audit/verify_sha.py` → `results/realdata_audit/sha_check.json`. Result: 171 of 171 checks OK, with no mismatches and no fetches.

- Manifest `raw_checksums`: noaa (5 manifests), criteo_attribution (2), gas_sensor (4), folktables (18), wilds (3).
- Every `.receipt.json` under noaa, criteo_attribution, gas_sensor and folktables.
- Elec2 has no manifest or receipt in `data/manifests`. Its sha256 is `2d86fbc7…ccf024d7f2`. This matches the value recomputed in `switching_c1_c2_exploratory_results_v1.md`. The `elec2_candidate_audit.md` quotes a 65-character string with one stray `e`, which is a typo in that audit. The MD5 `8ca97867d960ae029ae3a9ac2c923d34` matches the OpenML metadata quoted there.
- Elec2 provenance is therefore weaker than the manifest-backed datasets: the file is not in the canonical inventory.

### 2.2 Exposure (all 39 local and remote refs grepped; checked in detail on `research/monitoring-to-decision-value-2026-10-30`, `main`, and this branch)

| Dataset | Class | Evidence |
|---|---|---|
| Elec2 | **EXPOSED** (nearly the whole stream) | Used in `switching_c1_c2_exploratory_*` (C1/C2 replay on rows 22,656–25,655). In `decision_value/03_REAL_DATA_AUDIT.md` the fit window is rows 0–18,123 and the dev window is rows 25,656–36,249. That branch computed a frozen-vs-sliding error of 0.350 vs 0.258 and headroom there. It labels rows 36,250–45,311 "reserved, low trust". So **all of the first 60% (0–27,186) and rows 27,187–36,249 of the "locked" 40% have been examined**. Only rows 36,250–45,311 (9,062 rows) look unread in the repo. The benchmark itself is also a long-public one. |
| Gas | **EXPOSED** | Batches 6–10 used as the holdout. `exhaustive_evaluation` candidate selection, D2 event-level replay on `sweet-lovelace`, and recorded clairvoyant headroom 0.972%. |
| NOAA 2023 | **PARTIALLY EXPOSED** | The repo ran only temperature-regression diagnostics (`time_series_real_diagnostics`, `noaa_panel`) on the final event-time partition, plus a descriptive eligibility note. The decision_value audit tags the whole year "EXPOSED_DEVELOPMENT_ONLY". No switching, monitoring or promotion run was found, and the precipitation label was never constructed. For this task, the feature series and calendar have been seen descriptively; the label has not. |
| Criteo Attribution | **PARTIALLY EXPOSED** | The maturity audit scanned the whole sequence for aggregate label-maturity counts (3.31% of labels mature in-stream). `switching_real_data_eligibility_v1.md` ruled it "not suitable for within-stream switching". No model losses, switching or promotion run was found on any window. The exposure is aggregate label counts over the full file, including the tail. |
| Folktables | UNEXPOSED to switching | Only offline domain-shift diagnostics (`folktables_*`, `reproduce_robust_asi_acs`). |
| WILDS CivilComments | UNEXPOSED to switching | Only candidate-selection and PACE-gate studies (offline). |

## 3. Chronology and label semantics

| | Elec2 | NOAA ISD (3 stations, 2023) | Criteo Attribution | Gas | Folktables | WILDS |
|---|---|---|---|---|---|---|
| Event time | **Not trustworthy.** `date` is a normalised float, with 528 duplicated (date, period) groups, 5 date decreases and 943 period resets. Only file row order is used. | Real UTC report times, irregular (METAR/SYNOP mix). | Publisher-relative seconds (0 – 30.9 days), sorted. Not calendar time. | None within batch. Row order inside the 10 ordered batches. | Year only (2017/2018/2019). | None. |
| Label | UP/DOWN vs a 24 h moving average, so it is known when the price is realised (zero physical delay). | **Constructed:** any precipitation in the next hourly bin (AA1 1-h depth > 0, or MW1/AW1 present-weather codes ≥ 50/40). This is my coding and a forking path. | click (immediate); conversion-within-W-days (real delay). | 6-class gas identity. | ACS income; no stream. | toxicity; no stream. |
| Label availability | Imposed delay needed. | About 1 h physically (next bin). But ISD files are final-QC archives (S3 object modified 2026), not point-in-time releases. | Positive conversions have **real** delays (below). Click has none (imposed). Negatives mature only at ts+W (imposed rule). | Imposed. | n/a | n/a |
| Is a real delay available? | No. Impose. | No. Impose, 1 h or more. | **Yes for conversions only.** Impression→conversion delay on 48,586 positives in the early 1-in-10 subsample: median 88.6 h, p25 1.5 h, p75 288 h, p95 601 h. | No. | No. | No. |
| Leakage risks | Features are min-max normalised with **global** statistics (includes future rows). Mitigation: the normalisation is a per-column affine map. With train-only `StandardScaler`, logistic regression is exactly invariant. HGB is invariant to monotone maps. Neither model sees the leak. The label is a function of past 24 h prices only. | Next-hour label uses obs from the next bin. Handled by purging boundary events. Station dummies are included, with no day-of-year feature. | Target-free frequency encoding is fit on train only. Per-impression `conversion` is defined by future conversions, so the label is available at conversion time or ts+W, not at the impression. Purged accordingly. 700 campaigns and heavy user repetition mean events are not independent. | Batch drift is a mix of sensor drift, not a clock. | n/a | n/a |

Feature-free split facts:

| Stream | N total | Early 60% | Locked | Train | Dev |
|---|---|---|---|---|---|
| Elec2 | 45,312 | 27,187 | rows 27,187–45,311 (18,125) | rows 0–13,592 | rows 13,593–27,186 (13,594) |
| NOAA | 26,277 station-hour events | 15,766, 15,762 after the 4-event purge | from 2023-08-07 23:00 (10,511 events) | 7,881; 2023-01-01 00:00 → 04-20 10:00 | 7,881; 2023-04-20 11:00 → 08-07 21:00 |
| Criteo | 16,468,027 | rows 0–9,880,815; t ≤ 1,595,031 s (18.46 d) | rows 9,880,816–16,468,026 (6,587,211) | 470,578 (1-in-10, label-purged); t 0–8.478 d | 470,579 (1-in-10); t 8.478–17.461 d (the purge removes the last day for the 1-day conversion label) |
| Gas | 13,910 | 8,346 | rows 8,346–13,909 (5,564) | rows 0–4,172 (batches 1–5 and part of 6) | rows 4,173–8,345 (batch 6 partly, batch 7 partly) |

## 4. Dev-window results (first 60% only)

Notation:
- e0 / e1: incumbent / challenger error rate on dev.
- dis: disagreement rate.
- adv: mean of l0−l1; positive means the challenger is better.
- chunks: adv per 10% of dev.
- H5 / H20: clairvoyant headroom at switch cost 5 / 20 (cost units = 0/1 errors).
- p95: the shuffled-null 95th percentile of the same quantity.
- Hn: H5 − 0.05 × #disagreements. Hn25: the same with 25% of disagreements labelled.
- Static cost is about 3,800–4,000 errors for Elec2 (T = 13,594).
- A figure is "real" only if H exceeds p95.

### 4.1 Elec2 (file order; T = 13,594)

| Pair | e0 | e1 | dis | adv | H5 (p95) | Hn / Hn25 | H20 (p95) |
|---|---|---|---|---|---|---|---|
| A LR_old/LR_new | .311 | .291 | 3.4% | +.020 | 30 (1) | +7 / +24 | 21 (1) |
| **B LR_old/HGB_new** | .311 | .281 | **5.2%** | +.029 | 26 (2) | **−9** / +17 | 15 (2) |
| C LR_all/HGB_all | .299 | .292 | 3.7% | +.006 | **54 (9)** | +29 / +48 | 18 (6) |
| D HGB_old/HGB_new | .292 | .281 | 4.4% | +.011 | 23 (2) | −7 / +16 | 0 (3) |
| E LR_all/HGB_new | .299 | .281 | 4.3% | +.017 | 31 (2) | +2 / +24 | 13 (4) |

- By the pre-stated rule, only B is eligible (dis ≥ 5%).
- B's adv per 10% chunk: .059 .040 .005 .026 .043 .010 .026 .007 .039 .038. The advantage is positive in every chunk with moderate variation, so a persistent challenger gain dominates. The switching structure is weak.
- H5 = 26 is real (above p95 = 2) but small: 0.7% of the best static cost, or 1.9 per 1,000 events. It is negative net of labelling every disagreement (−9), and only +17 if labelling is capped at 25% of disagreements.
- At s = 20, only 15 remains. Pair C has the largest headroom (54, 1.4%) but is ineligible at 3.7% disagreement.
- Dev gain of the challenger over the incumbent is 3 points for B, i.e. a promotion-only story.

### 4.2 NOAA, precipitation in the next hour (T = 7,881)

Base rate 16.6% in train, 9.3% in dev: a real seasonal shift.

| Pair | e0 | e1 | dis | adv | H5 (p95) | Hn | H20 (p95) |
|---|---|---|---|---|---|---|---|
| A LR_old/LR_new | .057 | .061 | 1.4% | −.003 | 0 (0) | −6 | 0 |
| B LR_old/HGB_new | .057 | .061 | 3.4% | −.004 | 5 (9) | −8 | 0 |
| C LR_all/HGB_all | .057 | .058 | 2.0% | −.001 | 10 (6) | +2 | 0 |
| D HGB_old/HGB_new | .065 | .061 | 4.2% | +.004 | 15 (14) | −2 | 13 (7) |
| E LR_all/HGB_new | .057 | .061 | 3.2% | −.004 | 4 (5) | −9 | 0 |

- No pair reaches 5% disagreement, so none is eligible. Headroom is at or below the shuffled null in all five pairs (D has H5 = 15 vs null p95 14).
- The 0/1 loss is dominated by predicting "no rain" (about 94% accuracy); there is nothing to switch.
- Admissibility: the constructed label is admissible as a development label only. The release latency is not point-in-time, the coding of precipitation is a forking path, and station-hours with a missing next-hour report are dropped (an unmodelled selection). No headroom regardless.

### 4.3 Criteo Attribution (1-in-10 subsample; T = 470,579; dev t = 8.48–17.46 d)

Click label (immediate; the delay must be imposed). Click rate: 34.8% in train, 36.3% in dev.

| Pair | e0 | e1 | dis | adv | H5 (p95) | Hn | H20 |
|---|---|---|---|---|---|---|---|
| A LR_old/LR_new | .3416 | .3416 | 0.3% | 0 | 50 (67) | −8 | 20 |
| **B LR_old/HGB_new** | .3416 | .3287 | **6.6%** | +.0130 | 124 (75) | −1,426 | 0 |
| C LR_all/HGB_all | .3415 | .3290 | 6.7% | +.0125 | 89 (105) | −1,483 | 1 |
| D HGB_old/HGB_new | .3300 | .3287 | 3.1% | +.0013 | 436 (435) | −283 | 8 |
| **E LR_all/HGB_new** | .3415 | .3287 | **6.6%** | +.0129 | 128 (93) | −1,421 | 0 |

- The rule selects E and B, but both are essentially the same comparison (an HGB challenger vs a logistic incumbent).
- adv per chunk for B is .011–.016, uniformly positive. The challenger is better in every tenth of dev.
- H5 = 124 on a static cost of 154,677 is 0.08%. H20 = 0. Headroom is at the noise level.
- The right action throughout is "promote at once and never switch back". Net of labelling all 6.6% of events as disagreements (31k labels at 0.05), switching is negative.
- This stream tests promotion latency and query-cost economy, not switching.
- At a 25% label budget, Hn25 is still −263.

Conversion within 1 day (real positive delays; negatives mature at ts+1 d): rate 1.7%. Disagreement ≤ 0.15% for all pairs, so no eligible pair; all H5 are within noise (≤ 33, versus shuffled p95 up to 26). A 0/1 loss on a rare outcome gives near-identical classifiers. The real delay is therefore unusable under a 0/1 disagreement-triggered query design.

### 4.4 Gas (EXPOSED; reference only; T = 4,173)

| Pair | e0 | e1 | dis | adv | H5 (p95) | Hn / Hn25 | H20 |
|---|---|---|---|---|---|---|---|
| A LR_old/LR_new | .353 | .427 | 49% | −.073 | 167 (4) | 64 / 141 | 107 |
| C LR_all/HGB_all | .395 | .514 | 25% | −.119 | 53 (0) | 0 / 40 | 0 |
| B, D, E | | | 38–61% | −.14 to −.23 | ≤ 32 | < 0 | ≤ 2 |

- The challenger is worse in every pair here, because the "newer" and HGB models were fit on pre-drift batches and drift is severe.
- Pair A has structured headroom (167 vs p95 4, 11% of static) whose advantage sign flips across chunks (−.26 → +.14 → −.05).
- This differs from the documented +12.3% challenger gain, because that used regularisation-swept candidates trained on batches 1–5. The two are different pair definitions, so this audit makes no statement about the documented gain.
- 49% disagreement means the label budget is not scarce. It is a mechanics test bed, not a "labels only on disagreement" test.

### 4.5 Brief: clearly unsuitable

- **Folktables (2017–2019, 5 states, ACSIncome).** Year-level chronology only: no within-year order and no release clock. A year-granular "stream" would have 2–3 blocks and could not host a sequential test, rollback or per-event labelling. Its year boundaries (33/33/33) do not match the 60/40 split. Not run.
- **WILDS CivilComments.** Domains, not time. Not a stream.
- **OPSD, EIA, Monash, Binance, CRSP.** Regression or return losses, not 0/1, or too short (Binance local extent is 743 hourly bars). Previous branches froze reserved windows for several. Not part of this 0/1 design.
- **Open Bandit, CriteoPrivateAds.** Logged-bandit (Setting B), with simulated delays or unknown release. Not run.

## 5. Recommendation

1. **Do not claim a real-data confirmation.** No admissible dataset has both (a) an unexposed locked window and (b) net dev headroom after switch and query costs.
2. **If one real-data section is needed, lock two structurally different reference streams, labelled exposed/descriptive:**

| | Stream 1: Elec2 pair B (LR_old → HGB_new) | Stream 2: Criteo Attribution click, pair B (LR_old → HGB_new) |
|---|---|---|
| Role | Small structured switching headroom, high temporal dependence; checks the validity and cost accounting of the e-process, not the benefit. | Large persistent challenger gain, no switching headroom; checks promotion latency, label-budget economy and the no-false-rollback property against "always challenger". |
| Exposure | EXPOSED. The first 60% and rows 27,187–36,249 were seen by earlier branches. Only rows 36,250–45,311 are repo-unread, and the benchmark is public. | PARTIALLY EXPOSED (aggregate label counts only). |
| Splits (0-based) | Train rows 0–13,592; dev 13,593–27,186; **locked 27,187–45,311** (file order, untrusted clock). | Train t < 8.478 d; dev 8.478–18.46 d (the click label needs no purge, so dev can extend); **locked rows 9,880,816–16,468,026 (t > 1,595,031 s, about 18.46–30.9 d)**; 1-in-10 subsample or full. |
| Delay to impose | 48 events (1 day of half-hours); sensitivity at 0 and 336 events. | 1 hour (about 22k impressions at full scale, about 2.2k on the 1-in-10 subsample); sensitivity at 24 h. The real conversion delays (median 88.6 h) apply only to a conversion label, which is too rare for 0/1 disagreement. |
| Label budget | Disagreement events only (about 5% of events); cap at 25% of disagreements, with 100% as sensitivity. | Disagreement events only (about 6.6% of events); cap at 25% of disagreements, with 100% as sensitivity. |
| Costs | Switch 5 and 20; query 0.05, as specified. | Same. Rescale to dataset units: at T = 470k a 0.05 query is tiny against a static cost of about 155k, but labelling every disagreement is about 31k queries (1,550 units). |

3. **Blockers**
   - **Elec2:**
     - Untrusted chronology.
     - The locked window was partly examined by the repo's earlier switching work.
     - No manifest or receipt.
     - It was previously classed "exclude from final online confirmation".
     - Net-of-query headroom is negative under the pessimistic query rule (−9) and only +17 under a 25% budget.
   - **Criteo:**
     - Timestamps are publisher-relative.
     - Click has no real delay; the real-delay label (conversion) fails the 5% disagreement rule.
     - The challenger gain is persistent, so the comparators "always challenger" and the proposed method coincide after the first promotion.
     - Impressions are not independent: users and campaigns repeat. The CC BY-NC-SA licence restricts non-research use.
   - **NOAA:** no headroom, and the constructed label is not point-in-time.
   - **Gas:** exposed, no clock, and 49% disagreement.
   - **Cross-cutting:** the paired-loss design uses only the disagreement events, so any dataset needs the 0/1 task with at least 5% disagreement. Both recommended streams have that, only barely for Elec2 (5.2%).
4. **Better route.** The missing ingredient is an unexposed period with an auditable release contract. The monitoring branch's own conclusion (`09_FINAL_RESEARCH_DECISION.md`) already points the same way. Candidates remain a prospective vintage (new EIA or Binance months) or a regression-loss version of the method. Neither was audited here.

## 6. Reproduction

```
python scripts/promising_directions/realdata_audit/verify_sha.py docs/promising_directions/results/realdata_audit/sha_check.json
python scripts/promising_directions/realdata_audit/run_audit.py {elec2,gas,noaa}   # seconds
python scripts/promising_directions/realdata_audit/run_criteo.py                   # about 2 minutes
```

Outputs are in `docs/promising_directions/results/realdata_audit/{elec2,gas,noaa,criteo}_dev.json` and `sha_check.json`. They hold only aggregates computed on the first 60% of each stream.

Code state: the worktree has no committed changes from this audit. Nothing was committed.

Limitations:
- Single seed for the shuffled null (20 permutations; 5 for Criteo).
- HGB hyper-parameters were not tuned.
- The five pairs are fixed and not exhaustive. A different, staler incumbent would give a larger Elec2 gap (the monitoring branch saw 0.350 vs 0.258 with a much older incumbent). That would be a different pair and was not selected, to keep the rule pre-stated.
