# 11 — Amendment: all real data, diverse sources, "≥ SOTA" as non-inferiority

Written 2026-11-08, after the batch-F 311 builds and **before any batch-F file is opened**.

**User direction (2026-11-08).** Use every real dataset, seen or not, and add diversity. The goal is
at least 8 datasets showing a result that is ≥ SOTA. Protocol 10 stays in force for the fresh
311 datasets. This amendment adds to it.

## 1. Evidence tiers (always reported separately, then pooled with tier labels)

| tier | datasets | status |
|---|---|---|
| **F** fresh | batch-F 311 (eligible: miamidade, minneapolis, louisville, chicago, denver, pittsburgh) + diverse sources in §2 | never opened before this run |
| **S** seen | C4 batch 1 (9) and batch 2 (7) | retrospective; outcome-informed selection disclosed in A2 |
| **D** development | the 14 C4-0 pilot streams (elec2, airlines, bank, spam, weather, criteo, …) | used to tune the RD configurations **and arm R**. Their results for arm R and the RD baselines are in-sample. |

Batch-F build outcomes:
- eligible: 6;
- ineligible by gate: cambridge (7 episodes), gainesville (1);
- not buildable: houston, seattle_csr, norfolk, somerville (no closure timestamp or no export),
  bloomington (too small), fortworth (no 311 export).

Build notes for the audit: louisville's page-size fetch fix (label and features unchanged);
validation base rates above 0.8 for minneapolis (.83), chicago (.80) and denver (.845); labels kept
as locked.

## 2. Diverse non-311 candidates (tier F; list fixed now, in this order)

Every buildable, eligible, audit-passing source is registered. Same brief, builder and gates.

| # | module | domain / publisher |
|---|---|---|
| 1 | bts_ontime | air travel; US DOT BTS On-Time Performance |
| 2 | chicago_food_inspections | food safety; Chicago Dept. of Public Health |
| 3 | sf_building_permits | permitting; SF Dept. of Building Inspection |
| 4 | seattle_building_permits | permitting; Seattle SDCI |
| 5 | cfpb_complaints | consumer finance; CFPB complaint database |
| 6 | sonoma_animal_shelter | animal shelter; Sonoma County |
| 7 | chicago_traffic_crashes | road safety; Chicago Police / CDOT |
| 8 | dallas_animal_shelter | animal shelter; Dallas Animal Services |

## 3. Arms and comparators

- Arms: **B** `EQSDp_l0.9_g0.2` (frozen) and **R** `EQSDp_l0.98_g0.3` (dev-selected, 10 §3).
- Comparators: the full nine-dataset panel (`nine_policies.txt`, 43 entries), run on every tier.
- "SOTA" means:
  - **published-method adapters**: Qiu-style; Gong–Zhang-style SD and RD; UPF-style SD and RD;
    Challenger-style nominal and RD; CAMS; Model Selector; Model Picker; online LLM picker;
    variance-min IPW; ARW;
  - **the strongest uncertified controls**: Wald, Hoeffding, scaled margin and dwell (SD and RD);
    econF; economic replacement.
- Certified methods stay **NOT COMPARABLE** (different guarantee), reported as cost Δ only.

## 4. "≥ SOTA" definition (fixed before opening)

For arm a, comparator c and dataset k, take the episode-level Δ = J(a) − J(c). Use a one-sided 95%
episode-bootstrap upper bound U_k, with 2,000 resamples and rng seed 0. The margin is
**m = 1% of c's mean J on k**, the "negligible" threshold of the fair-evaluation standard.

- **Superior** on k if U_k < 0.
- **Non-inferior (≥)** on k if U_k < m.
- **Dataset k supports "a ≥ SOTA"** if a is non-inferior to **every** uncertified comparator in §3
  on k (the hardest version: no adapter or control is meaningfully better on that dataset).
- **Headline count:** the number of tier-F datasets that support it, and separately tier F+S and
  F+S+D. The user's target is ≥ 8.
- **Pooled:** the equal-dataset mean Δ with a dataset-level t 95% CI per comparator and tier.
  Pooled non-inferiority holds if the upper CI limit is < 1% of the pooled comparator J.
- **Reported in full:** the per-comparator superiority counts; every dataset and every comparator,
  including those where an arm loses.

Protocol 10's primary (arm B vs Qiu-style, superiority on tier-F 311) is still evaluated and
reported as registered.

## 5. Seeds and runs

- Batch F (311 + diverse): seed base **2026111601**, 10 policy seeds, one opening after
  registration with hashes.
- Tier S: batch 1 has full-panel records from 05; arm R is added with the batch-1 seed base.
  Batch 2 gets the full panel plus arm R with its registered seed base 2026111301, so arm B and
  `gongT_w100_m10` must reproduce the C4 batch-2 records exactly.
- Tier D: the existing development records (`dev/`, `dev_eqsdp/`, `dev_chalgse/`; seed base
  2026111401, 5 seeds).
