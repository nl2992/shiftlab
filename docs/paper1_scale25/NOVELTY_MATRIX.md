# Novelty matrix (Workstream E2)

Rows are the closest works found in `PRIOR_ART_AUDIT.md`; columns are the eight features of the Paper 1 contract. Cell code: **●** feature is part of the work's model; **◐** partial, implicit or only in the code/experiments; **○** absent; **?** not established from what I read. The level in the last column is the verification level of the row (TEXT = read the paper's text; PAGE = abstract page; LISTING = search record only; INHERITED = earlier repo audit). A row labelled LISTING or PAGE can only support what its abstract says, so its "○" means "not in the abstract", not "absent from the paper".

Columns: **PL** paid labels (a label costs something to obtain) · **DL** delay / pending observations · **HB** hard label budget · **RV** reversible deployment (can switch back) · **SC** switching cost · **CH** change hazard (an explicit non-stationarity model, not only adversarial streams) · **FH** finite horizon (payback over remaining time) · **RS** empirical evaluation on real data streams or event logs.

| work | PL | DL | HB | RV | SC | CH | FH | RS | level |
|---|---|---|---|---|---|---|---|---|---|
| Karimi et al. 2021, Model Picker | ◐ | ○ | ○ | ● | ○ | ○ | ◐ | ◐ | TEXT |
| Liu et al., CAMS | ◐ | ○ | ● | ● | ○ | ○ | ◐ | ● | TEXT |
| Okanovic et al., Model Selector | ◐ | ○ | ● | ○ | ○ | ○ | ○ | ● | PAGE |
| Turrin et al., Online LLM Picker | ◐ | ? | ◐ | ● | ○ | ○ | ◐ | ● | PAGE |
| Hara et al. 2024, variance minimisation | ◐ | ○ | ◐ | ○ | ○ | ○ | ○ | ● | LISTING |
| Madani, Lizotte, Greiner 2004 | ● | ○ | ● | ○ | ○ | ○ | ○ | ? | LISTING |
| Cesa-Bianchi, Lugosi, Stoltz 2005, label-efficient prediction | ◐ | ○ | ● | ● | ○ | ○ | ● | ○ | LISTING |
| Castellani, Schmitt, Hammer 2022, PRopagate | ● | ● | ● | ○ | ○ | ◐ | ○ | ● | PAGE |
| Chick, Forster, Pertile 2017 | ● | ● | ◐ | ○ | ◐ | ○ | ● | ◐ | TEXT |
| Digalakis et al., The Challenger | ● | ○ | ○ | ○ | ● | ○ | ● | ◐ | PAGE + INHERITED |
| Regol et al. 2025, When to retrain | ○ | ○ | ○ | ○ | ● | ◐ | ● | ● | PAGE |
| Mahadevan and Mathioudakis, cost-aware retraining | ○ | ? | ○ | ○ | ● | ? | ◐ | ? | LISTING |
| Wan et al. 2023, A/B early stopping | ◐ | ? | ○ | ○ | ◐ | ○ | ● | ● | PAGE |
| Frazier, Powell, Dayanik 2008, knowledge gradient | ● | ○ | ● | n/a | ○ | ○ | ● | ○ | LISTING |
| Ryzhov, Powell, Frazier 2012, online KG | ◐ | ○ | ○ | n/a | ○ | ○ | ● | ? | LISTING |
| Desautels, Krause, Burdick 2014, GP-BUCB | ○ | ● | ○ | n/a | ○ | ○ | ◐ | ● | LISTING |
| Joulani, György, Szepesvári 2013 | ○ | ● | ○ | ● | ○ | ○ | ● | ○ | LISTING |
| Altschuler and Talwar 2021 | ○ | ○ | ○ | ● | ● | ○ | ● | ○ | LISTING |
| Gong and Zhang 2026 | ● | ○ | ◐ | ● | ◐ | ○ | ● | ◐ | TEXT (structure) |
| Qiu et al. 2026 | ○ | ● | ○ | ● | ● | ○ | ● | ○ | PAGE |
| Adams and MacKay 2007, BOCPD | ○ | ○ | ○ | ○ | ○ | ● | ○ | ● | LISTING |
| Geng, Bayraktar, Lai 2014 (change detection with limited sampling) | ◐ | ○ | ● | ○ | ○ | ● | ○ | ○ | INHERITED (B0) |
| DISCERN, Balachandran 2026 | ● | ? | ○ | ◐ | ○ | ◐ | ○ | ? | INHERITED |
| **This programme: EQSDp + cutoff + E48 + F60 (v1)** | ● | ● | ● | ● | ● | ◐ | ● | ● | repo |

Notes on cells that could be disputed:
- *CAMS HB ●*: Figure 1 buys a label only while C_t <= b. *Model Picker HB ○*: the paper has no cap; the authors' code only stops recording queries.
- *Karimi/CAMS RV ●*: every round the learner may use any expert, at no cost; the matrix asks whether a deployed model can be replaced and restored, which is true, but with no switching cost (SC ○), so the interaction RV x SC is absent.
- *Chick et al. HB ◐*: a maximum sample size T_max, not a hard budget in the sense of a cap that competes with other uses. *SC ◐*: a one-time adoption cost I, not a repeated reversible switch.
- *Castellani CH ◐*: concept drift is handled by detection and budget redistribution, not by a hazard model inside a decision rule.
- *This programme CH ◐*: E48/F60 use a constant per-event hazard inside a heuristic; the evidence model is discounted counts, not a change-point filter, and no guarantee follows.
- *Regol CH ◐*: it forecasts performance trends rather than modelling change times.

## Reading

1. **No other row has more than four ● cells (this programme has seven plus one partial).** The closest, Chick-Forster-Pertile 2017, has paid sampling, delay with a pipeline, a finite horizon and a (one-time) switching cost, with a maximum sample size; it lacks reversibility, a hazard and a streaming evaluation. The Challenger has the payback structure and switching cost but no delay, budget, reversibility or disagreement evidence. Castellani et al. have paid, delayed, budgeted labels under drift but no deployment decision.
2. The empty region of the matrix is the **conjunction** DL x HB x RV x SC x FH with paid labels. That conjunction is the only candidate for novelty; each single column has a precedent.
3. What the matrix does **not** show: that nothing exists. Rows with LISTING are limited to their abstract, and the search covered about 25 queries (PRIOR_ART_AUDIT.md section 9). Restless-bandit/Whittle treatments of switching with observations and real-options learning were not searched.
4. The matrix says nothing about performance. Empirical standing against the panel is in docs 18 and 20 and in the scale-25 results.
