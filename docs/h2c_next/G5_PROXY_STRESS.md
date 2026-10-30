# G5: corrected proxy-defect benchmark (checkpoint B; development seeds 80000+, 400 seeds per cell; `outputs/h2c_next/g5_dev.csv`)

**Repair of the invalid doc 07 design.** True boundary = G1 linear logit; the deployed model p = sigmoid(a·x·w + b + c·1{x₂>1}) has one of six defects (accurate; biased b=+0.8; overconfident a=2; underconfident a=0.5; subgroup failure c=−3; anti-informative a=−0.3). **Every condition's nominal cost and Brier risk come from that condition's own pre-shift source stream** (`detectors.source_moments("G5:<cond>")`), so a defective model starts at its own nominal and a no-shift stream is a true null. Shifts at t0=700: none; `prior1` (prior shift δ=1); `concept2` (concept shift δ=2). Ground-truth decision harm is computed per condition by population simulation; a world is `harm` if it is ≥ 0.10 (the same shift is harmful under one proxy and benign under another):
| condition | prior1 harm | concept2 harm |
|---|---|---|
| accurate | −.035 | **+.233** |
| biased | −.121 | **+.110** |
| overconfident | **+.153** | **+.369** |
| underconfident | −.150 | +.038 (benign) |
| subgroup failure | +.082 (benign) | **+.242** |
| anti-informative | −.158 | −.003 (benign) |
Seven harm cells, seven benign cells, six null cells. Not included from the brief: time-varying proxy bias, proxy deterioration with recovery, delayed recognition of proxy failure.

**Aggregate (7 harm / 7 benign / 6 null cells; threshold 1/α; C7a empirical, calibrated on each condition's null):**
| labels | method | harm power | benign FA | null FA |
|---|---|---|---|---|
| 10% | C0 cost parent | .180 | .013 | .011 |
| 10% | C1 cost disc. | .278 | .022 | .019 |
| 10% | C2 cost ONS | .323 | .029 | .024 |
| 10% | C3 guided ONS | .363 | .028 | .020 |
| 10% | **C4 H2c** | **.399** | .028 | .010 |
| 10% | C7a cost SR | .581 | .061 | .043 |
| 10% | HG (Brier) | .566 | **.119** | .007 |
| 10% | ONS (Brier) | .656 | **.188** | .025 |
| 20% | C0 / C1 / C2 / C3 | .405 / .530 / .503 / .510 | .020 / .028 / .039 / .033 | ≤ .028 |
| 20% | **C4 H2c** | **.644** | .037 | .012 |
| 20% | C7a cost SR | .779 | .104 | .065 |
| 20% | HG (Brier) | .781 | **.174** | .018 |
| 20% | ONS (Brier) | .774 | **.215** | .032 |

**Per-condition harm power at 20% labels (cost parent / cost-only discounted / H2c / HG-Brier):** accurate concept2 .618 / .798 / .905 / .985; biased concept2 .220 / .340 / .575 / .948; overconfident concept2 .795 / .895 / .955 / .978; overconfident prior1 .108 / .158 / .198 / .082; subgroup-failure concept2 .285 / .462 / .585 / .910.

**Findings (development evidence, not confirmation).**
1. **RQ2 (does Brier guidance survive a defective predictive model?):** yes in this benchmark. H2c beats the cost-only discounted Kelly in every one of the 5 harm cells at 20% labels (+.05 to +.24) and in all 5 at 10% labels, including the biased and subgroup-failure models. Power falls with a biased model (.905 → .575), so the advantage in absolute terms shrinks.
2. **The cost-null methods keep false alarms low under every defect:** null FA ≤ .028 for C0–C4 in all six conditions, benign FA ≤ .039. This is the empirical counterpart of the cost-null guarantee, which does not depend on the proxy being accurate.
3. **Brier-null methods pay for benign-for-decision shifts:** HG and Brier ONS alarm on 12–22% of benign cells (a Brier increase without decision harm), 3–6× the cost-null rate. They have higher harm power because they test a different, easier-to-violate null. When "alarm" must mean decision harm, they are the wrong tool; when predictive degradation is itself the concern, they are the right one.
4. The empirical-threshold cost SR (C7a) again has more power than H2c (.58 / .78) with 2–3× the benign and null FA (null FA .065 at 20% labels, close to the .07 limit) and no guarantee.
5. In one cell (overconfident, prior1, harm +.153) HG's power (.082 at 20%) is below H2c's (.198): a Brier-based test can miss decision harm that raises the cost but not the Brier loss enough.
Limits: static defects only, one shift magnitude per kind, 400 seeds per cell, fixed delay 5, development seeds (confirmation on fresh seeds still to run).
