# 05 — Real data: the original nine-dataset C4 batch (retrospective)

**Status: retrospective comparison.** The nine datasets were opened once, for the registered arm B
vs tuned Gong–Zhang-style claim (`c4_results.md`). These new comparisons were not pre-registered on
them. Neither arm B's parameters nor any comparator's tuning used these nine streams (protocol 03 §4).
Batch 2 is not included.

## Inputs

- Protocol `03_EXPERIMENT_PROTOCOL.md` (locked at `67b57a79`; Challenger family added at
  `d0b86349` before the nine-dataset run).
- Policy list `nine_policies.txt`, committed at `bc7f01a9` before the run.
- The nine sealed files matched their registered hashes.
- 759 episodes × 10 policy seeds × 44 policies = 333,960 episode records (gitignored:
  `outputs/qsg_methods_search/sota_expansion/nine/`).
- Full analysis output: [nine_analysis.txt](nine_analysis.txt).

```bash
cd scripts/qsg_methods_search
OPENBLAS_NUM_THREADS=1 ../../.venv/Scripts/python.exe sota_nine.py nine --policies ../../docs/qsg_methods_search/sota_expansion/nine_policies.txt --out ../../outputs/qsg_methods_search/sota_expansion/nine --workers 20
PYTHONPATH=../failure_atlas_v2_flq PYTHONIOENCODING=utf-8 ../../.venv/Scripts/python.exe analyze_sota.py nine ../../outputs/qsg_methods_search/sota_expansion/nine/records.jsonl ../../outputs/qsg_methods_search/c4_confirm/records.jsonl
```

**Reproducibility: PASS.** Arm B, tuned GZ-style (w100 m10) and Qiu-style reproduce the C4 opening
exactly: 22,770 matched rows, max |ΔJ| = 0.0.

**Leakage: none found.**
- Labels reach policies only through the simulator's delayed release (`simulator.py:181-218`).
- The budget is enforced by the simulator and asserted in `run_metrics`.
- No comparator reads the evaluator-side gain (02 §5).
- The evaluator-side episode type is used only for the descriptive split below.

## Development selection (14 exposed real streams, never the nine)

Every tunable family selected a longer memory (λ = .97) or a larger window on real development
data than on synthetic data. On those development streams arm B (410.4) ranked behind
front-loaded economic (401.8), scaled margin λ.97 (403.2), Wald λ.97 (403.7), Challenger-style RD
(404.3) and Model Picker (404.3). Full ranking: [dev_selection.log](dev_selection.log). The
selection therefore already warned that real-data-tuned baselines would be hard to beat.

## Pooled results: Δ = J(arm B) − J(comparator), equal dataset weight, per 2,000-event episode

Columns:
- **Boot CI**: stratified episode bootstrap (registered primary).
- **neg**: datasets where the mean Δ < 0.
- **t-p**: one-sample t across the nine dataset means (between-dataset robustness).
- **t-Holm**: Holm-adjusted over the 43 contrasts.
- **Verdict**: registered cost verdict. The bootstrap p hits its floor (1/2000) for most contrasts,
  so Holm-adjusted p = 0.0215 for all WIN and LOSS rows.

| comparator | fid. | Δ | boot 95% CI | % | neg | t-p | t-Holm | verdict |
|---|---|---|---|---|---|---|---|---|
| **S2 Qiu-style** | C | **−8.14** | [−9.09, −7.20] | −1.8 | **9** | .0006 | **.024** | WIN (small) |
| **S1 tuned GZ-style, SD w100 m10** | C | **−3.68** | [−4.33, −2.99] | −0.8 | **9** | .022 | .64 | WIN (negligible) |
| S1 GZ-style untuned | C | −3.93 | [−4.73, −3.13] | −0.9 | 7 | .008 | .28 | WIN (negligible) |
| **S1 tuned GZ-style, RD w800 m20** | C | +0.88 | [−0.16, +1.90] | +0.2 | 3 | .20 | 1 | COMPETITIVE |
| **S3 UPF-style, SD δ.95 m50** | B | **−14.02** | [−16.34, −12.00] | −3.1 | 6 | .045 | 1 | WIN (meaningful) |
| S3 UPF-style, RD δ.8 m50 | B | −12.32 | [−14.98, −10.11] | −2.7 | 6 | .045 | 1 | WIN (small) |
| S4 Model Picker | B | −2.00 | [−3.10, −0.96] | −0.5 | 6 | .41 | 1 | WIN (negligible) |
| S5 Model Selector causal | C | −4.21 | [−5.79, −2.66] | −1.0 | 6 | .14 | 1 | WIN (negligible) |
| S6 CAMS | B | −7.65 | [−9.37, −6.04] | −1.7 | 6 | .033 | .85 | WIN (small) |
| online LLM picker | B | −3.74 | [−4.96, −2.59] | −0.8 | 6 | .24 | 1 | WIN (negligible) |
| variance-min IPW | C | −9.26 | [−10.69, −7.77] | −2.1 | 6 | .013 | .45 | WIN (small) |
| N1 Challenger-style GSE, nominal λ1 γ.2 | C | −5.12 | [−8.16, −2.82] | −1.2 | 6 | .060 | 1 | WIN (small) |
| N1 Challenger-style GSE, RD λ.9 γ.3 | C | −2.94 | [−5.65, −0.93] | −0.7 | 6 | .25 | 1 | WIN (negligible) |
| ARW label clock | B | −70.03 | [−72.11, −67.84] | −13.8 | 9 | <1e-4 | <1e-3 | WIN (substantial) |
| S11 Wald LCB, SD λ.9 γ.2 | int. | −0.19 | [−0.35, +0.01] | −0.04 | 7 | .27 | 1 | COMPETITIVE |
| **S11 Wald LCB, RD λ.97 γ.2** | int. | **+2.15** | [+1.41, +2.87] | +0.5 | **0** | .003 | .10 | **LOSS (negligible)** |
| Hoeffding LCB, SD λ.9 γ.45 | int. | +1.32 | [+0.81, +1.86] | +0.3 | 3 | .077 | 1 | LOSS (negligible) |
| Hoeffding LCB, RD λ.97 γ.3 | int. | −0.41 | [−1.49, +0.58] | −0.1 | 5 | .78 | 1 | COMPETITIVE |
| S12 scaled margin, SD | int. | −0.86 | [−1.21, −0.51] | −0.2 | 6 | .28 | 1 | WIN (negligible) |
| **S12 scaled margin, RD λ.97** | int. | **+2.21** | [+1.31, +3.08] | +0.5 | 1 | .018 | .57 | **LOSS (negligible)** |
| S12 dwell, SD | int. | −4.19 | [−4.65, −3.74] | −0.9 | 9 | .0003 | .012 | WIN (negligible) |
| S12 dwell, RD λ.97 k3 | int. | +0.01 | [−0.56, +0.62] | 0.0 | 4 | .97 | 1 | COMPETITIVE |
| **S12 econF, SD mo5 m5** | int. | −3.26 | [−7.65, +0.25] | −0.7 | **1** | .65 | 1 | COMPETITIVE |
| S12 econF, RD mo5 m0 | int. | −3.04 | [−7.44, +0.43] | −0.7 | 1 | .67 | 1 | COMPETITIVE |
| S12 economic replacement | int. | −9.05 | [−12.17, −6.60] | −2.0 | 6 | .067 | 1 | WIN (small) |
| arm A λ.95 (descriptive) | int. | +1.99 | [+1.44, +2.54] | +0.5 | 0 | .004 | .16 | LOSS (negligible) |
| ablation: posterior-median hurdle | int. | −24.92 | [−26.52, −23.30] | −5.4 | 9 | .0006 | .023 | WIN (meaningful) |
| never switch | ctrl | −118.80 | [−128.2, −110.1] | −21.4 | 6 | .073 | 1 | WIN (substantial) |
| *Certified class: cost Δ under a different guarantee (verdict NOT COMPARABLE, see 06)* | | | | | | | | |
| S7 DISCERN-style | B | −88.44 | [−92.98, −83.79] | −16.8 | 7 | .050 | 1 | (cost lower) |
| S7 DISCERN design floor | B | −31.61 | [−36.03, −28.10] | −6.7 | 7 | .025 | .69 | (cost lower) |
| S7 DISCERN design floor +front | C | −30.18 | [−35.03, −26.13] | −6.5 | 7 | .021 | .63 | (cost lower) |
| S7 DISCERN +QCE+front | C | −8.93 | [−13.31, −5.35] | −2.0 | 7 | .013 | .45 | (cost lower) |
| S8 SMCS retain-incumbent | B | −16.79 | [−21.18, −13.35] | −3.7 | 7 | .031 | .84 | (cost lower) |
| S8 SMCS +QCE+front | C | −8.68 | [−13.23, −5.12] | −1.9 | 7 | .012 | .45 | (cost lower) |
| S9 Xu acquisition | C | −24.35 | [−26.77, −22.12] | −5.3 | 7 | .054 | 1 | (cost lower) |
| S9 Xu +front | C | −17.41 | [−22.07, −13.63] | −3.8 | 7 | .017 | .54 | (cost lower) |
| S10 gated certificate | B | −78.93 | [−84.94, −73.10] | −15.3 | 7 | .091 | 1 | (cost lower) |
| S10 MOPE adaptive range | B | −34.70 | [−39.16, −31.09] | −7.4 | 7 | .058 | 1 | (cost lower) |
| S10 MOPE adaptive range +front | C | −10.21 | [−14.65, −6.61] | −2.3 | 7 | .013 | .45 | (cost lower) |
| e-SR two-sided | B | −31.70 | [−34.12, −29.41] | −6.8 | 6 | .062 | 1 | (cost lower) |
| e-SR RMM bets, full α | C | −24.90 | [−26.86, −22.95] | −5.4 | 6 | .069 | 1 | (cost lower) |
| Shekhar–Ramdas RCS any-excl | B | −19.31 | [−21.59, −17.18] | −4.2 | 6 | .057 | 1 | (cost lower) |
| QSG | int. | −4.39 | [−6.28, −2.74] | −1.0 | 6 | .056 | 1 | (cost lower) |

## Secondary metrics (pooled means; evaluator-side split descriptive)

| policy | J | loss | labels | switches | switch cost | false promo | first-deploy round (gain>0) | promoted when gain>0 |
|---|---|---|---|---|---|---|---|---|
| scaled margin RD | 434.9 | 421.6 | 152.8 | 1.12 | 5.6 | .64 | 196 | .93 |
| Wald RD | 434.9 | 422.2 | 152.8 | 1.02 | 5.1 | .54 | 264 | .93 |
| arm A | 435.1 | 422.0 | 152.8 | 1.09 | 5.4 | .60 | 282 | .94 |
| tuned GZ-style RD | 436.2 | 423.1 | 152.9 | 1.09 | 5.5 | .62 | 193 | .84 |
| **arm B** | **437.1** | 422.3 | 152.8 | 1.43 | 7.1 | .71 | 282 | .97 |
| Model Picker | 439.1 | 422.7 | **48.4** | 2.80 | 14.0 | .84 | 247 | .98 |
| econF SD | 440.3 | 428.4 | 154.2 | 0.85 | 4.3 | .66 | 200 | .91 |
| tuned GZ-style SD | 440.8 | 422.9 | 152.9 | 2.04 | 10.2 | .80 | 226 | .95 |
| Model Selector | 441.3 | 421.0 | 153.5 | 2.52 | 12.6 | .83 | 192 | 1.00 |
| Challenger-style nominal | 442.2 | 431.6 | 152.8 | 0.59 | 3.0 | .11 | 359 | .68 |
| CAMS | 444.7 | 421.6 | 120.3 | 3.41 | 17.1 | .86 | 199 | .99 |
| Qiu-style | 445.2 | 425.5 | 152.9 | 2.41 | 12.0 | .91 | 269 | 1.00 |
| UPF-style SD | 451.1 | 438.4 | 152.9 | 1.02 | 5.1 | .28 | 472 | .84 |
| e-SR two-sided | 468.8 | 458.7 | 152.9 | 0.48 | 2.4 | .02 | 1066 | .55 |
| gated certificate | 516.0 | 508.2 | 123.3 | 0.32 | 1.6 | .00 | 981 | .35 |
| never switch | 555.9 | 555.9 | 0 | 0 | 0 | 0 | — | 0 |

The share of episodes where the challenger is better in hindsight differs widely by dataset:
- 1.00: boston, dc;
- .99: sf;
- .91: philly;
- .80: dallas, nyc;
- .76: montgomery;
- .73: la;
- .26: kc.

## Δ by episode type (gain > 0 = challenger better in hindsight; equal dataset weight)

| comparator | Δ, challenger better | Δ, challenger not better |
|---|---|---|
| Qiu-style | −8.5 | −8.6 |
| tuned GZ-style SD | −2.7 | −6.0 |
| tuned GZ-style RD | +0.2 | +5.2 |
| UPF-style SD | −17.2 | +10.0 |
| Model Picker | −2.6 | −7.5 |
| Challenger-style nominal | −7.3 | +11.7 |
| Wald RD | +1.3 | +7.8 |
| econF SD | −0.5 | −3.7 |
| certified (e.g. e-SR two-sided) | −38.6 | +17.0 |

## Reading

1. **Against published-method adapters at their pre-specified (synthetic-dev) settings, arm B is
   cheaper on the nine datasets.**
   - Qiu-style: 9/9 datasets, −1.8%. This is the only adapter win that survives the dataset-level
     Holm test.
   - Tuned GZ-style: 9/9, −0.8%.
   - UPF-style: 6/9, −3.1%.
   - Selection adapters (CAMS, Model Selector, Model Picker, LLM picker, variance-min): 6/9 each,
     negligible to small, and only the CAMS and variance-min wins reach unadjusted dataset-level
     significance (t-p .033 and .013; none survive Holm).
2. **The edge over GZ-style depends on how GZ-style is tuned.**
   - Synthetic-tuned GZ-style: arm B wins 9/9.
   - Tuned on real development streams (w800 m20): GZ-style ties arm B (+0.9, n.s.).
   - Arm B was not given real-dev tuning (frozen). The descriptive arm A (λ=.95), which is still
     EQSDp, is −1.1 vs real-tuned GZ-style (7/9 negative). It is not part of any claim.
3. **The strongest internal controls beat or match arm B on real data.**
   - Real-tuned Wald (λ=.97) and real-tuned scaled margin are cheaper on 9/9 and 8/9 datasets
     (+2.2 each, about 0.5%).
   - Real-tuned Hoeffding and dwell tie.
   - econF is cheaper than arm B on 8 of 9 datasets. Its pooled advantage for arm B comes from one
     dataset (kc_311, −57.7).
   - These are the most relevant baselines, and arm B does not beat them on real data.
4. **The hurdle family is the same mechanism.** Arm A ≈ Wald λ.97 (+0.16) ≈ scaled margin λ.97
   (+0.22). Memory length, not the Beta form, decides the real-data ranking.
5. **The confidence-bound component matters on real data too.** The posterior-median ablation
   costs +24.9 (9/9; 6.4 switches vs 1.4).
6. **Certified methods are dearer where the challenger is uniformly better, and cheaper where it
   is not.**
   - Dearer on the 311 streams: boston, dc, sf, dallas, philly.
   - Cheaper on la_crime, montgomery_traffic and nyc_collisions, by about 1–4.
   - This is the expected cost of false-promotion control. Their false-promotion rate is ≤ 3%;
     arm B's is 71%.
