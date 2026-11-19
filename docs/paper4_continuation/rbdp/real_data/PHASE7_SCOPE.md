# Phase 7 scope: model-promotion streams, standard benchmarks, baseline panel (draft, 2026-11-17)

Goal from the user: real model-promotion streams; more variety from the standard datasets used in streaming and drift
studies; up to 35 supporting datasets in total (25 now); and a comparison against baselines on each one.

## A. Model-promotion streams (the paper's own setting)

**Mapping onto the game.** For each dataset there are cached paired 0/1 loss vectors (`l0` incumbent, `l1` challenger, 2,000
rounds per episode) produced by earlier ShiftLab chronological train/score runs. Only disagreement rounds carry
information (on agreement both losses are equal). Stream: x_t = 1 when the challenger wins a disagreement round (l0 = 1, l1 = 0).
Under "no gain" the challenger wins half the disagreements, which is exactly the game's null at 1/2. The two hidden states are
regimes where the challenger is better (e1 > 1/2) or worse (e0 < 1/2). This is the cleanest real instance of the paper's problem.

**Inventory (copied 2026-11-17 into Paper 4's git-ignored `data/raw/real_chains/promotion/`, checksums in `MANIFEST.sha256`; Phase 7 reads only this copy).**
- `atlas_v2_losses`: airlines, bank, criteo, elec2, openml_ldpa, rialto, spam, uci_occupancy, weather (9, the standard
  drift benchmarks).
- `sprint_fresh_losses`: appliances, beijing_pm25, bike_hour, household_power, metro (5).
- `screen100_losses`: 100 more (36 FOREX pairs, 12 Beijing air stations, electricity meters, fraud, conversion, and others).

**Pre-screen (lead, today, descriptive only).** Lag-1 correlation of the challenger-wins stream, median over episodes: 2 of 114
datasets below −0.05, 1 below −0.15 (FOREX eur/rub, about 21 disagreements per episode); median of medians +0.30. So these
streams are mostly persistent: the challenger's advantage comes in runs. The synthetic theory gives no premium for persistent
chains, and the baselines tie there (E4). One real persistent stream, Spidroin-2 (r1 +0.53, noisy emissions), did show a
premium at T32 B4, so persistent streams with noisy emissions are evaluated, not skipped. Expected yield of this family is
uncertain; it is run first because it is the paper's own setting.

**Fit.** Per dataset: fit the two-state model on the concatenated disagreement stream of the first episodes up to 3,000 rounds
(episode boundaries cut the chain; the remaining episodes are a held-out check of the fit). Same evaluator, both orientations,
shuffle control as Phases 4b–6. The r1 screen is dropped for this family (persistent chains are kept).

## B. More variety: standard streaming benchmarks not yet in the cache

Fetched fresh, each turned into a model-promotion stream by the same chronological pipeline (incumbent trained on an early
window, challenger retrained on a recent window, both scored on the following rounds), then section A's mapping:
1. INSECTS (Souza et al. 2020): the abrupt, gradual, incremental and reoccurring variants, balanced and imbalanced (up to 10).
2. Forest Covertype, Poker-hand, KDD Cup 99 (10%), NOAA weather (if not the cached `weather`), Sensor (Intel Berkeley lab),
   Ozone (UCI).
3. Text streams already used in the study's languages family stop here; no new language families.

Sources are public (UCI, OpenML, the INSECTS repository). Pipeline code would reuse `failure_atlas_v2` scoring if it can be
imported unchanged; otherwise a small logistic-regression / tree pipeline fixed before any fit.

## C. Baseline panel on every supporting dataset

For each positive dataset (the existing 25 and every new one), run the `iid_failure` panel on its fitted chain
(`run_study.py --real-only --extra-chains`): P1 fixed-sample test, P2 count SPRT, P3 HMM-filter threshold, P4 myopic VOI, P5
IID-optimal, P6 e-process gate, P7 RB-DP. Report per dataset:
- causal risk / α for each policy (unsafe baselines that break the budget);
- cost of RB-DP against the safe baselines (P1, P2, P6), as the share of RB-DP's value of information each one captures (E4's
  metric).
"Supports us over baselines" = RB-DP is causal-safe, at least one IID-calibrated policy breaks α, and RB-DP's cost is below
every safe baseline's.

## Order and stopping

A (all 114, ordered: the 14 standard drift streams first, then screen100 in file order), then B, until 35 total positives; C runs on all positives at the end. Protocol text goes in as Addendum G before any fit.

## Cost

Each dataset takes 5–15 minutes (evaluator plus shuffles). A: 114 datasets, about 10–25 hours on this Mac if all are evaluated
(stopping at 35 cuts this only if positives come early); B: about 2–4 hours including fetching and training; C: about 1–2 hours.
A Sonnet subagent builds and runs it; the lead verifies counts from raw files.
