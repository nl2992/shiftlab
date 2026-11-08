# C4 single opening: results

Registration: [c4_registration.json](c4_registration.json), committed at `013775db` before
opening. The user approved the opening on 2026-11-08. All 9 sealed files matched their registered
`array_content_sha256` (`outputs/qsg_methods_search/c4_confirm/checksums.json`). 759 episodes
× 10 policy seeds (seed base 2026111201), arms frozen since `10ba0237`. Raw records are gitignored
under `outputs/qsg_methods_search/c4_confirm/`; the locked analysis output is
`c4_confirm_analysis.txt`.

```bash
cd scripts/qsg_methods_search
OPENBLAS_NUM_THREADS=1 ../../.venv/Scripts/python.exe c4_confirm.py run --out ../../outputs/qsg_methods_search/c4_confirm --workers 16
../../.venv/Scripts/python.exe analyze_c4_confirm.py ../../outputs/qsg_methods_search/c4_confirm/records.jsonl
```

## Verdict under the registered rule: **C4 NOT PASS** (5 of 9 supporting; 8 required)

| dataset (city) | episodes | Δ J(B) − J(tuned Gong–Zhang-style) | one-sided 95% UB | supports | Δ vs Qiu-style | Δ vs never-switch |
|---|---|---|---|---|---|---|
| sf_311 (San Francisco) | 100 | −5.19 | −3.58 | **yes** | −8.56 | −382.7 |
| kc_311 (Kansas City) | 80 | −11.49 | −9.00 | **yes** | −1.18 | −19.1 |
| montgomery_traffic (Montgomery Co. MD) | 49 | −3.04 | −0.94 | **yes** | −10.94 | +10.9 |
| dallas_311 (Dallas) | 100 | −6.22 | −4.87 | **yes** | −3.41 | −77.2 |
| dc_311 (Washington DC) | 100 | −5.96 | −4.59 | **yes** | −10.26 | −425.9 |
| la_crime (Los Angeles) | 100 | −0.04 | +0.91 | no | −13.10 | +4.9 |
| nyc_collisions (New York City) | 88 | −0.17 | +0.84 | no | −14.18 | +4.4 |
| boston_311 (Boston) | 42 | −0.30 | +1.90 | no | −4.43 | −175.1 |
| philly_311 (Philadelphia) | 100 | −0.69 | +0.30 | no | −7.18 | −9.5 |

Registered secondary and summary statistics:

- Supporting: 5 of 9 distinct organisations. The one-per-city sensitivity count is also 5.
- Sign test: **9 of 9 negative**, one-sided p = 0.002.
- Pooled secondary vs the Qiu-style adapter: mean **−8.14**, one-sided p = 0.0003.

## Interpretation (fair grading, separate from the registered verdict)

- **Direction is uniform; size is small.** Arm B is cheaper than the tuned Gong–Zhang-style
  adapter on every dataset. The pooled mean is −3.68 per 2,000-event episode, which is **−0.77% of
  the comparator's cost** (graded *negligible to small* on total cost).
- **Where it supports, the mechanism is the expected one.** Arm B switches about half as often:
  - kc_311: 2.05 vs 4.18 switches;
  - dc_311: 1.14 vs 2.16;
  - sf_311: 1.38 vs 2.35.
- **Where it does not support, both policies rarely switch** (≈1 switch each), so there is
  nothing to win. On la_crime, nyc_collisions and montgomery_traffic **never-switching is best**:
  arm B costs +4 to +11 more than keeping the incumbent, because the challenger is not better.
  This is the documented null-churn limitation (no false-promotion guarantee).
- **Arm A (λ=.95) and Wald λ=.9 track arm B closely** (descriptive; not part of the claim). Arm A
  is lowest on 8 of 9 datasets, consistent with M5 (longer memory transfers better to real
  streams).
- The registered rule required per-dataset significance on ≥8 datasets. With effects of
  0.04–0.7 units on four datasets, that bar is not met. The pre-specified alternative
  summaries (sign test, pooled secondary) are significant.

## What may follow (registration §5)

Further datasets may only be added as a **new, separately reported batch** whose denominator
includes these 9. No dataset here is dropped or re-analysed.

---

# Batch 2 and cumulative result (Amendment A2)

Batch 2: 7 audited 311 datasets, registered at `0b034638` before opening, seed base 2026111301.
All sealed hashes verified. Analysis: `analyze_c4_batches.py` (locked per-dataset rule, same
bootstrap stream). Full output: [c4_cumulative_b2.txt](c4_cumulative_b2.txt).

| dataset (city) | episodes | Δ vs tuned Gong–Zhang-style | one-sided 95% UB | supports |
|---|---|---|---|---|
| sandiego_311 (San Diego) | 100 | −9.63 | −8.11 | **yes** |
| cincinnati_311 (Cincinnati) | 67 | −5.05 | −2.89 | **yes** |
| austin_311 (Austin) | 100 | −2.53 | −1.20 | **yes** |
| oakland_311 (Oakland) | 55 | −1.02 | −0.40 | **yes** |
| sacramento_311 (Sacramento) | 100 | −1.18 | +0.02 | no |
| baltimore_311 (Baltimore) | 83 | −0.78 | +0.40 | no |
| nola_311 (New Orleans) | 61 | −0.78 | +0.29 | no |

## Cumulative verdict: **TARGET REACHED. 9 of 16 opened datasets support the claim** (9 distinct organisations; also 9 under the one-per-city sensitivity count). Acquisition stops (A2 stopping rule).

| statistic (all 16 opened datasets) | value |
|---|---|
| batch 1 / batch 2 supporters | 5/9, 4/7 |
| binomial count bound P(X ≥ 9 \| N = 16, p = .05) | **1.6 × 10⁻⁸** |
| sign test (Δ < 0) | **16/16**, one-sided p = 1.5 × 10⁻⁵ |
| pooled secondary vs Qiu-style | −6.07, one-sided p = 2.2 × 10⁻⁵ |
| pooled Δ vs tuned Gong–Zhang-style | −3.38 per episode, **−0.75% of cost** (median −0.39%) |

## Honest reading

- **Real, small, consistent.** The direction is uniform across 16 sources, and the count test is
  overwhelming even under the outcome-dependent stopping rule. The size is negligible to small on
  total cost: below 1% on average, and up to −1.9% (Kansas City) where the comparator churns.
- **Mechanism.** Gains come from switching about half as often as the tuned point-estimate
  economic switcher.
- **Batch 2 was selected after batch 1.** Its pool favoured 311 streams (disclosed in A2). The
  application family the evidence supports is mostly municipal service-request closure streams,
  plus crime clearance, collision injury and traffic citations in batch 1.
- **Boundary.** On 3 datasets (la_crime, montgomery_traffic, nyc_collisions) never switching
  beats arm B: there is no false-promotion protection.
- **M5 again.** Arm A (λ=.95, descriptive) is the cheapest of arm A, arm B and Wald λ=.9 on
  **16/16** datasets. Longer memory transfers better to real streams. This is not part of the
  registered claim.
- **What is supported.** The claim is about the integration (confidence-bound payback ≡ Wald) vs
  a point-estimate adapter. It is not evidence for a new algorithmic primitive.
