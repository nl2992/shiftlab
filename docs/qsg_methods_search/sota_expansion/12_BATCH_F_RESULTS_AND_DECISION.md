# 12 — Batch F (fresh data) results, all-tier "≥ SOTA" counts, and decision

Written 2026-11-08, after the single registered opening of batch F.

## Provenance

- **Runs:** `sota_nine.py --reg docs/qsg_methods_search/c4_registration_batchF.json`, seed base 2026111601, 10 seeds, 45 policies, 8,010 jobs, no errors. Batch 2 was rerun with seed base 2026111301 (5,660 jobs, no errors).
- **Checksums:** all 10 sealed files matched their registered hashes before running (`outputs/.../batchF/checksums.json`).
- **Reproducibility:** for arm B and `gongT_w100_m10`, the batch-2 rerun is identical to the C4 batch-2 records (`c4_confirm_b2`) on all 5,660 rows each, with maximum |diff| 0.0.
- **Analysis:** `analyze_all.py` produced `outputs/qsg_methods_search/sota_expansion/all_tier_analysis.txt` (UTF-16; a UTF-8 copy is `all_tier_analysis_utf8.txt`) and `all_tier_per_dataset.csv`. The protocol-10 tests were computed from that CSV (equal dataset weight, t-test on dataset means, Holm over the 4 secondaries).
- **Code:** branch `research/qsg-methods-search-2026-11-07`, at 00d00084 plus this doc.

## 1. Protocol 10, as registered (fresh 311 cities, K = 6)

| arm | contrast | mean Δ | % | p | Holm p | negative | verdict |
|---|---|---|---|---|---|---|---|
| **B (primary)** | vs Qiu-style | −3.10 | −1.13 | .079 | — | 5/6 | **NOT CONFIRMED** |
| B | vs CAMS | −6.35 | −1.94 | .033 | .130 | 6/6 | not confirmed |
| B | vs GZ-SD | −4.62 | −0.83 | .227 | .682 | 5/6 | not confirmed |
| B | vs UPF-SD | +3.00 | +1.02 | .250 | .682 | 3/6 | not confirmed |
| B | vs Challenger | +2.50 | +0.78 | .286 | .682 | 3/6 | not confirmed |
| R (descriptive) | vs Qiu-style | −6.40 | −1.88 | .005 | — | 6/6 | would be confirmed |
| R | vs CAMS | −9.65 | −2.69 | .016 | .063 | 6/6 | not confirmed |
| R | vs GZ-SD | −7.91 | −1.58 | .145 | .435 | 6/6 | not confirmed |
| R | vs Challenger / UPF-SD | −0.79 / −0.30 | ≈0 | .77 / .92 | 1.0 | 3/6 | tie |

**The registered primary failed.** Under protocol 10 §7, the arm-B method-superiority claim is dropped. Arm R passing the same test is a secondary or descriptive result, not a substitute for the primary.

## 2. Amendment 11: "≥ SOTA" counts

A dataset supports the claim if the arm is non-inferior, at a 1% margin, to every one of the 25 uncertified comparators.

| tiers | arm B | arm R |
|---|---|---|
| F (fresh, 10) | 2/10 | **4/10** |
| F + S (26) | 6/26 | **15/26** |
| F + S + D (40) | 8/40 | **18/40** |

Arm R supporting datasets:
- F: bts_ontime, chicago_traffic_crashes, dallas_animal_shelter, louisville_311;
- S1: dallas, kc, la_crime, nyc_collisions, philly, sf;
- S2: austin, cincinnati, oakland, sacramento, sandiego;
- D (in-sample for arm R): airlines, criteo, weather.

The user's target of 8 datasets is met on F + S (15) and on F + S + D (18). It is **not** met on fresh data alone (4).

Arm R failures on tier F:
- chicago_311: GZ-RD, UPF ×2, Challenger ×2, Hoeffding λ.97, econF ×2, economic replacement;
- denver_311: econF ×2, economic replacement;
- miamidade_311: UPF ×2, Challenger λ1.0, Hoeffding λ.97;
- minneapolis_311: GZ-RD, UPF ×2, Challenger λ1.0, Wald λ.97, Hoeffding ×2, scaled margin λ.97;
- pittsburgh_311: econF ×2, economic replacement;
- sf_building_permits: econF ×2.

## 3. Pooled across real datasets (arm R, F + S, K = 26; dataset-level t 95% CI)

- **Non-inferior to all 25 comparators.**
- **Superior (CI < 0) to 19/25:**
  - every one of the 14 published-method adapters: Qiu −2.0%, GZ paid-obs −1.4%, GZ-SD −1.3%, GZ-RD −0.2%, UPF ×2 −1.8/−2.1%, Challenger ×2 −0.9/−1.1%, CAMS −2.2%, Model Selector −1.4%, Model Picker −1.2%, online LLM picker −1.8%, variance-min IPW −2.8%, ARW −15.4%;
  - plus Wald λ.9, scaled margin λ.9, dwell ×2 and economic replacement.
- **Ties (CI includes 0) with 6 controls:** Wald λ.97 (+0.10%), scaled margin λ.97 (+0.07%), Hoeffding ×2, econF ×2.

On fresh data alone (F, K = 10), arm R is non-inferior to 22/25 pooled. The exceptions, whose wide CIs exceed the margin rather than showing a loss, are UPF ×2 and Hoeffding λ.97. Its mean is slightly worse than Wald λ.97 (+0.37%), scaled margin λ.97 (+0.20%), Hoeffding λ.9 (+0.12%) and GZ-RD (+0.12%), all within the 1% margin.

Arm B on F + S trails the λ.97 controls, as in 05. Arm R, which uses λ.98, closes that gap.

## 4. Caveats

- Arm R was chosen on the dev tier. The real-data preference for λ ≈ .97 was seen on tier S before that choice (05 / M5), so tier-S evidence for arm R is retrospective. Tier F is the only fresh evidence, and arm R was fixed before it was opened.
- Every comparator is a class B/C adapter. No author code has been run (09 §4 item open).
- Effects are 1–3% of total cost. There is no false-promotion guarantee.
- The tier-F 311 base rates are high for minneapolis, chicago and denver (validation .80–.85; flagged in the batch-F audit).

## 5. Continue / pivot / stop

**PIVOT the claim; CONTINUE the paper.**
- Drop as registered: "frozen arm B beats Qiu-style on fresh data". It was not confirmed.
- Supportable claim: the confidence-bound payback class, at the dev-selected λ.98 (arm R), has lower cost than all 14 published-method adapters pooled over 26 real datasets, and is ≥ every uncertified comparator on 15 of 26 datasets (18 of 40 including dev). On fresh data it is confirmed vs Qiu-style (6/6, p .005) but supports the full ≥ SOTA bar on only 4/10 datasets.
- Stop trigger: not reached.
- Next steps that would most strengthen the paper:
  - author-code parity for Qiu or Gong–Zhang;
  - `paper-claim-audit` on this doc and 08;
  - figures (blocked: PaperBanana not installed).
