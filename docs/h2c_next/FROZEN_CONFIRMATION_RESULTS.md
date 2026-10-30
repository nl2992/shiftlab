# Frozen G5 confirmation results (single run of the protocol; `outputs/h2c_next/g5_confirmation_cells.csv`, `g5_confirmation_per_seed.parquet`)

**Execution note.** The runner simulated and saved all per-seed results, then crashed in the analysis block on a name clash (`DataFrame.shift`). The experiment was **not re-run**: the analysis was repeated from the saved per-seed file with the clash fixed (`scripts/sota_search/g5_confirmation_analysis.py`; identical formulas). 8 conditions × 4 shifts = 32 cells (14 harm, 10 benign, 8 null), 600 seeds per cell. The 6 development conditions are re-used with fresh seeds (90000+); `biased_neg`, `over_subgroup` and the `concept1.5` shift were never run before.

**Mean over cells (harm: power; benign/null: false-alarm rate):**
| labels | method | harm power (14 cells) | benign FA (10) | null FA (8) |
|---|---|---|---|---|
| 10% | C0 cost parent | .156 | .023 | .011 |
| 10% | C1 cost discounted | .265 | .030 | .010 |
| 10% | C2 cost ONS | .296 | .041 | .027 |
| 10% | **F1 H2c** | **.382** | .036 | .012 |
| 10% | F2 guided ONS | .326 | .042 | .021 |
| 10% | F3 multi-horizon guided | .344 | .030 | .014 |
| 10% | C7a cost SR (empirical) | .572 | .081 | .052 |
| 10% | HG (Brier) | .483 | **.159** | .009 |
| 10% | Brier ONS | .578 | **.257** | .025 |
| 20% | C0 / C1 / C2 | .402 / .545 / .491 | .032 / .048 / .057 | ≤ .037 |
| 20% | **F1 H2c** | **.640** | .067 | .018 |
| 20% | F2 / F3 | .492 / .608 | .066 / .062 | .033 / .019 |
| 20% | C7a cost SR | .773 | .112 | .057 |
| 20% | HG (Brier) | .774 | **.274** | .017 |
| 20% | Brier ONS | .769 | **.329** | .031 |

**Frozen hypotheses**
| hypothesis | 10% labels | 20% labels | verdict |
|---|---|---|---|
| D1: F1 − (per-cell better of C1, C2) ≥ +0.05, CI lower > 0 | +.086 [.059, .113] | +.094 [.063, .125] | **PASS** |
| D2: F1 ≥ F2 − .02 and ≥ F3 − .02 | +.056 / +.038 | +.148 / +.033 | **PASS** |
| D3: null FA ≤ .07 in every null cell; pooled benign FA ≤ .07 (F1, F2, F3) | max null .023–.042; benign .030–.042 | max null .027–.038; benign **.067**, .066, .062 | **PASS** (20% benign for F1 and F2 is within .004 of the limit) |
| D4 (descriptive): F1 − C7a | −.19 | −.13 | C7a more powerful, with 2–3× the false alarms and no guarantee |

**Reading.** On unseen G5 cells (including two defect conditions never run before), H2c improves on the stronger of the cost-only discounted and ONS comparators by +0.09 power at both label rates, and is the best of the three frozen finalists, while keeping the cost-null false-alarm profile (benign ≤ .067, null ≤ .027). This is the first frozen win of the candidate over a comparator set that includes the strongest cost-null alternatives I could implement. It is **not** a win over every method: the empirically-thresholded cost SR e-detector is more powerful (−.19 / −.13), and the Brier-null methods are more powerful but alarm on 16–33% of cells where there is no decision harm. Caveats: (i) the D1 comparator is the per-cell better of C1/C2 chosen from the realised means, which can only make the test harder for H2c; (ii) 20%-label benign false alarm sits near the .07 limit and the pooled benign cells are 10; (iii) the conditions are synthetic variations of one underlying linear-boundary generator; (iv) fixed delay 5, static proxy defects; (v) no comparator is a verified reproduction; (vi) real data is untested (`BLOCKED_EXTERNAL_ACCESS`).
