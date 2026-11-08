# 10 — Fresh-data confirmation protocol (batch F)

Written 2026-11-08 and committed **before any candidate source below is fetched or built**.
This turns the 09 design into a locked protocol. The registration file
(`c4_registration_batchF.json`, with sealed hashes) is committed later, still before opening.

## 1. Claim under test

The SOTA-expansion claim (08), restricted to the contrasts with a realistic chance on fresh data:
arm B `EQSDp_l0.9_g0.2` (frozen since `10ba0237`) has lower net deployment cost J than
common-contract adapters of published switching/selection methods.

## 2. Data: candidate pool, fixed now, in this order

The candidates are public city 311 service-request streams from cities **not** used in batch 1,
batch 2, or the 14 development streams. Every candidate that can be built is built. Every
candidate that is eligible under the builder gates and passes the coordinator audit is
registered. No candidate is dropped for any other reason.

| # | module | publisher (expected portal) |
|---|---|---|
| 1 | houston_311 | City of Houston |
| 2 | louisville_311 | Louisville Metro |
| 3 | cambridge_311 | City of Cambridge MA |
| 4 | chicago_311 | City of Chicago |
| 5 | seattle_csr | City of Seattle (Customer Service Requests) |
| 6 | denver_311 | City and County of Denver |
| 7 | gainesville_311 | City of Gainesville FL |
| 8 | norfolk_311 | City of Norfolk VA |
| 9 | somerville_311 | City of Somerville MA |
| 10 | pittsburgh_311 | City of Pittsburgh (WPRDC) |
| 11 | miamidade_311 | Miami-Dade County |
| 12 | minneapolis_311 | City of Minneapolis |
| 13 | bloomington_311 | City of Bloomington IN |
| 14 | fortworth_311 | City of Fort Worth |

- A candidate with no official public machine-readable 311 export (login-gated, removed, or
  without a creation and closure timestamp) is recorded as **not buildable**. It is not replaced.
- Buffalo and Detroit (batch 2, ineligible by gate) are not rebuilt.
- **Selection disclosure.** This pool favours 311 closure streams, and was chosen after batch 1
  and batch 2 results were known. That is the same outcome-informed selection already disclosed
  in Amendment A2, and it is reported as such.
- The rules in `c4_source_brief.md` apply unchanged: label, features and window are fixed in the
  module before the first build; test windows are never inspected; features must be known at
  intake. The builder (`c4_build.py`) and its gates (≥ 35 episodes, ≥ 3% disagreement) are
  unchanged.

## 3. Arms

- **Arm B** (primary): `EQSDp_l0.9_g0.2`, unchanged.
- **Arm R** (secondary, class claim): the EQSDp configuration with the lowest equal-stream-weight
  mean J on the 14 development streams (seed base 2026111401, 5 seeds). The grid is the existing
  `d3_extra` grid, λ ∈ {.9, .95, .98} × γ ∈ {.1, .2, .3, .5}. It is selected before opening and
  written into the registration.

## 4. Contrasts and power

Power was computed from the between-dataset spread of the nine dataset means (05):

| contrast (arm B vs) | nine mean Δ | sd of dataset means | power at K = 10, two-sided α .05 |
|---|---|---|---|
| Qiu-style `qiu_delayed_movement` | −8.1 | 4.5 | 1.00 |
| GZ-style SD `gongT_w100_m10` | −3.7 | 3.9 | .76 |
| CAMS `cams_adapter` | −7.7 | 8.9 | .68 |
| UPF-style SD `upf_d0.95_m50` | −14.0 | 17.8 | .60 |
| Challenger-style `chalgse_l1.0_g0.2` | −5.1 | 7.0 | .54 |
| GZ-style RD `gongT_w800_m20` | +0.9 | 1.9 | (tie expected) |

These powers are optimistic, because the nine means are retrospective point estimates. So:

- **Primary (confirmatory, one test):** arm B vs Qiu-style.
- **Secondary (Holm over 4):** arm B vs GZ-style SD, CAMS, UPF-style SD and Challenger-style.
  These are underpowered at K ≈ 10 and are reported as estimates with intervals. A non-significant
  result is not called a failure of the method.
- **Descriptive:** arm B vs GZ-style RD, real-tuned Wald λ.97, scaled margin λ.97 and econF (ties
  or small losses expected, as in 05). Arm R vs every comparator above.
- Certified comparators are not run in batch F.

## 5. Test

Per dataset k, the episode-level Δ_e = (seed-mean J of arm B) − (seed-mean J of comparator). Each
dataset contributes its mean Δ_k, with equal weight.

A contrast is **CONFIRMED** if all three hold:
1. a two-sided one-sample t-test on the K dataset means gives p < .05 (Holm-adjusted for
   secondaries);
2. the mean is < 0;
3. a strict majority of the K dataset means are < 0.

It is **REVERSED** if 1 holds with mean > 0 and a strict majority > 0. Otherwise it is
**NOT CONFIRMED**. The stratified episode bootstrap (05 method) is reported alongside. The size
grade follows 03 §6.

**Minimum K.** If fewer than 6 datasets are eligible, batch F is not opened. Instead it is
reported as "insufficient fresh data", and the decision falls back to 09's narrowed claim.

## 6. Run

- Contract: B = 200, c_q = .05, c_s = 5, T = 2000, 10 policy seeds per episode.
- Seed base **2026111601** (unused).
- Opened once, with the `sota_nine.py` runner pointed at the batch-F registration. Every policy
  from §4, plus `CONTROL_never_switch`, is run in one pass.
- Before opening, check that each sealed file matches its registered hash.

## 7. Decision rule (from 09)

- **Primary CONFIRMED:** keep the method claim in the narrowed 08 form, and add the batch-F
  numbers as the confirmatory evidence.
- **Primary NOT CONFIRMED or REVERSED:** drop the method-superiority claim. Publish the benchmark
  and the three-mechanism analysis (07) alone.
- Whatever happens, every number from every batch is reported.
