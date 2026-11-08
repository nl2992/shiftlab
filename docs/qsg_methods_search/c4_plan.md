# C4 plan: real-data confirmation (draft for registration, 2026-11-07)

Inputs: [real_data_inventory.md](real_data_inventory.md) (exposure audit),
[comparator_panel_results.md](comparator_panel_results.md) (which claim survived),
`scripts/promising_directions/b3_real_data.py` (the existing chronological pair pipeline).

## 1. Frozen claim to transfer

Arm B (`EQSDp_l0.9_g0.2`, frozen since `10ba0237`; equivalent to Wald λ=.9 γ=.2) has lower net
cost per 2,000-event episode than **both** the tuned Gong–Zhang-style adapter
(`gongT_w100_m10`) and the Qiu-style adapter (`qiu_delayed_movement`).

- **Contract:** B=200, c_q=.05, c_s=5. The label delay is declared per dataset (section 3).
- **Why this claim:** it is the largest surviving edge (5–10 units synthetic). The ≈2-unit edge
  over simple hysteresis forms is too small to confirm per dataset at feasible sizes. It is
  reported descriptively only.
- **Secondary, descriptive only:** horizon-scaled margin, dwell, UPF-style, econ+front, never
  switch.

The claim is about net cost, so it needs no causal change labels. Nothing about when shifts
happen is inferred from alarms or outcomes.

## 2. Coherent target family

**Chronological production-style binary classification streams with a frozen older-vs-newer
model pair.** These are datasets where a deployed model trained on an older window could be
replaced by a challenger trained on a newer window, the labels arrive later, and labelling is
paid.

Each dataset must satisfy all of:

- a true event-time order, with timestamps from the source;
- at least 60k post-training events, i.e. ≥25 non-overlapping 2,000-event test episodes after a
  validation window;
- a public licence that permits research use; CRSP and similar licensed data are excluded;
- never used for any ShiftLab outcome, according to the inventory and a `git grep` over all refs
  at registration time.

## 3. Construction (one recipe for every dataset; no per-dataset tuning)

Reuse the B3 recipe:

- **Split each source chronologically into four windows:** train-old (20%), train-new (20%),
  validation (10%), test (50%). Any remainder before test is discarded.
- **Model pair, both frozen:**
  - incumbent: standardised logistic regression trained on train-old;
  - challenger: `HistGradientBoostingClassifier` (defaults) trained on train-new.
- **Preprocessing:** fitted on each model's own training window only.
- **Features:** only those available at event time, using the source's issue/publication time
  where the source provides one (cf. the Elexon lag fix on the codex branch).
- **Label delay:** declared from the domain, never tuned:
  - hourly series: 24 events;
  - transactional or record streams: 100 events (the Atlas default);
  - sources with a publication lag: that lag.
- **Episodes and seeds:** non-overlapping 2,000-event episodes over the test window. 10 policy
  seeds per episode (query randomness only).

## 4. Eligibility gates (validation window only; no policy outcome is computed before the lock)

A dataset enters the confirmation set only if, on the validation window:

- the incumbent and challenger disagree on ≥3% of events;
- both error rates are in (0.02, 0.5);
- the test window yields ≥25 episodes.

These gates use model predictions and losses on validation data only, never a policy's cost.
Datasets that fail are recorded with the reason.

## 5. Evidence criterion and multiplicity (to be locked before any test window is read)

**Per-dataset support.** Let Δ_e be the episode mean over policy seeds of
J(arm B) − J(comparator). The dataset **supports** the claim if, for both comparators, the
episode-level bootstrap one-sided 95% upper bound of mean Δ is below 0 (2,000 resamples over
episodes).

**Count rule.** Register a fixed list of K candidate datasets before any test window is opened.

- **C4 PASS** requires ≥8 supporting datasets among the K, counting distinct sources only.
- Report X / K together with a one-sided sign test across all K.
- If fewer than 8 support, a second batch may be registered only as a new, separately reported
  batch; the denominator is then all registered datasets.
- No dataset is dropped after its test window is read.

**Independence.** Each underlying source or publisher counts at most once. EIA balancing
authorities count as one source: one pre-named BA, chosen by data size before any look. OPSD
countries count as one source. Variants of one source (INSECTS-style splits) count once.

## 6. Candidate pool (K target = 12–14; fetch and verify before registration)

| # | Candidate source | Task | Size | Status per inventory | Feasibility notes |
|---|---|---|---|---|---|
| 1 | EIA-930, one untouched BA (e.g. PJM or MISO, chosen by size) | sign of day-ahead forecast error (over vs under) | ~70k hours | untouched BA; source family partly exposed (CISO, ERCO) | local `data/raw/eia/EBA.zip`; contestable independence. Report it, but consider it last for the count. |
| 2 | Elexon GB demand / system data | over/under-forecast sign | ~90k half-hours | untouched (metadata audit only) | needs fetch; publication-time features exist |
| 3 | NYC TLC yellow taxi (monthly parquet) | tip > 0 (card payments) | millions | not in inventory | public; subsample to a fixed daily rate |
| 4 | Chicago crimes (data portal) | arrest made | ~8M | not in inventory | public; event timestamps |
| 5 | BTS on-time performance, 2023–2025 | arrival delay > 15 min | millions | `airlines` (OpenML, 2008) is exposed: same publisher | **independence risk**: exclude or count only if airlines is excluded |
| 6 | Citi Bike trip data | member vs casual | millions | not in inventory | public |
| 7 | NYC 311 service requests | closed within 7 days | millions | not in inventory | public |
| 8 | NYPD motor vehicle collisions | any injury | ~2M | not in inventory | public |
| 9 | Wild-Time arXiv | category (binarised) | ~2M | LOCKED protocol, data not local | text features; heavier pipeline |
| 10 | Amazon Reviews 2023 (one category) | rating ≥ 4 from text | large | not in inventory | text; licence check |
| 11 | OPSD (one country) | load forecast-error sign | ~50k hours | LOCKED holdout 2020-01..09 exists | use only data after the locked window, or treat it as exposed |
| 12 | Binance ETH klines | next-interval direction | very large | LOCKED holdout | near-random labels; likely fails the disagreement/error gates |
| 13 | San Francisco 311 or fire incidents | priority / closure | ~1M+ | not in inventory | public |
| 14 | US Accidents or similar | severity ≥ 3 | ~7M | not in inventory | licence check (Kaggle terms) |

Excluded:

- Covertype (spatial) and Poker (not temporal): `15b_FETCHED_DATA_ADMISSIBILITY.md`.
- INSECTS, KDD-http, keystroke, creditcard, usenet: B3+ screening.
- The 9 Atlas and 5 Sprint streams, CRSP, HuffPost: exposed.
- Folktables: cross-sectional.

## 7. Steps

1. **C4-0 transfer pilot (development; exposed data only).** Run arm B and the comparators on
   the 9 Atlas and 5 Sprint cached streams. This sizes the real effect and its per-episode SD
   for the power calculation, and it is an early warning if the edge does not transfer. It
   counts for nothing.
   - If arm B does not beat both comparators on the pooled exposed streams, stop and
     reconsider the claim before spending fresh data.
2. **Power check:** from the C4-0 SD, compute the episodes needed for an 80% chance of per-dataset
   support at the pilot effect size. Raise the 60k-event floor if needed.
3. **Acquire and build:** fetch the candidates into fresh `data/raw/<source>/` directories,
   recording checksums and receipts. Build pairs with the frozen recipe. Run the
   validation-window gates. Keep test windows unread: the builder writes test losses to a
   sealed `.npz` with a SHA256 recorded and does not compute policy costs.
4. **Register and lock:** commit the K-dataset list, gate outcomes, sealed-file hashes, the
   criterion (section 5) and the analysis script.
5. **Single opening:** run all K once, then analyse with the locked script. Record every dataset,
   whether it supports or not.
6. **Report:** a per-dataset table (Δ vs each comparator with CIs, episodes, delay), X/K, the
   sign test, and the descriptive secondaries.

## 8. Risks

- **Transfer risk.** Real streams with a frozen pair are mostly stationary. Arm B's edge over
  Gong–Zhang-style is null-churn reduction, which should transfer. Its edge over Qiu-style is
  partly change response, which may not. C4-0 tests this cheaply.
- **Pool risk.** About 10 clean new sources may yield fewer than 8 supporters even if the claim
  is true. Plan for K≈14 and accept that C4 may end as "X of K".
- **Imposed delays.** No source has an authentic label-release clock, so the delay is a declared
  contract parameter, stated as a limitation.
- **Effort.** Builders for about 10 new sources take roughly 1–2 days of agent time. Fetch sizes
  are large (TLC, crimes); subsample by a fixed, predeclared rule.
