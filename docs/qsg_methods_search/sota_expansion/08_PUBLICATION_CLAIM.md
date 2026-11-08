# 08 — Publication claim (scoped)

## Selected claim

> In budgeted, delayed-label model replacement, a reversible remaining-horizon payback rule with a
> confidence-bound switching hurdle (EQSDp; a Beta-quantile or, equivalently, a Wald-bound hurdle on
> discounted disagreement evidence) has lower cumulative net deployment cost than common-contract
> adaptations of published switching and active model-selection methods:
> - Qiu-style delayed movement;
> - Gong–Zhang-style paid-observation payback;
> - Regol-UPF-style switch timing;
> - a Challenger-style irreversible confidence-bound payback rule;
> - CAMS, Model Selector and Model Picker deployment adapters.
>
> The method gains by avoiding three failure modes of these adapters: switching churn, slow
> periodised adoption, and the absence of rollback. It provides no false-promotion guarantee.

## Main-paper results (strongest supported comparisons)

| comparison (adapter) | synthetic, fresh seeds | nine real datasets (retrospective) | mechanism |
|---|---|---|---|
| Qiu-style | −8.6 (−2.4% cost, −17% regret) | −8.1 (−1.8%), **9/9**, dataset-level Holm p = .024 | churn + blocked movement |
| Gong–Zhang-style, synthetic-tuned | −8.7 (−2.4%, −17%) | −3.7 (−0.8%), **9/9**, sign p = .004 | point-estimate churn (2.0 vs 1.4 switches) |
| UPF-style (Regol, T3) | −30.1 (−7.8%, −42%) | −14.0 (−3.1%), 6/9 | late periodised adoption |
| Challenger-style GSE | −15.1 to −30.9 (−4 to −8%) | −2.9 to −5.1 (−0.7 to −1.2%), 6/9 | no rollback, late adoption |
| CAMS / Model Selector / Model Picker | −32.2 / −21.6 / −25.1 (−6 to −8%) | −7.7 / −4.2 / −2.0 (−0.5 to −1.7%), 6/9 each | cost-unaware churn |
| ablation: posterior-median hurdle | −50.8 | −24.9, 9/9 | isolates the confidence bound |

**Environments where the gains are strongest.**
- Synthetic: reversal and late-change regimes (vs Qiu-style and UPF-style) and null churn (vs the
  Gong–Zhang-style and selection adapters).
- Real: municipal 311 closure streams where the challenger is usually better and adapters churn or
  adopt late (sf, dc, kc, dallas, boston).
- Gains are near zero or negative on la_crime, montgomery_traffic and nyc_collisions, where the
  challenger is often not better.

## Mandatory disclosures (must appear in the paper, not only in an appendix)

1. **Scale of the evaluation.** 18 external method families and 43 policy entries were evaluated,
   on 9 real datasets and 1 synthetic family. The full matrix (06) goes in the appendix. Batch 2
   (7 datasets) is reported separately, for the registered Gong–Zhang-style comparison only.
2. **Adapters, not native methods.** Every published-method comparator is a common-contract
   adaptation (class B) or a heuristic inspired by the source (class C). No native reproduction
   passed author-parity checks. Write "Qiu-style", "Gong–Zhang-style", "UPF-style" and so on, never
   the paper's name alone.
3. **Strongest baselines are tied or slightly better on real data.**
   - A Wald-LCB hurdle with matched tuning ties EQSDp everywhere.
   - Wald and scaled-margin hurdles tuned on real development streams (λ=.97) beat arm B by about
     0.5% on 8–9/9 datasets.
   - Front-loaded economic replacement ties arm B on real data.
   - The Gong–Zhang-style adapter tuned on real development data ties arm B.
   The contribution is the reversible confidence-bound payback integration (shared with the Wald
   variant), not a tuned arm B that beats every control.
4. **No guarantee.** Arm B promotes falsely in 71% of real episodes where the challenger is not
   better, and in 92% on synthetic null/worse streams. Certified methods are dearer but control this.
   Report cost Δ with the guarantee class. Never say arm B "dominates" or "outperforms" a certified
   method.
5. **Evidence status.**
   - The synthetic family was used for development.
   - The nine datasets were opened before these comparators were run, so all nine-dataset
     comparisons are retrospective.
   - Effects on real data are negligible to small (0.5–3% of cost). They are meaningful only against
     UPF-style.
6. **Prior art.**
   - The payback-with-confidence-bound form appears in the Challenger (arXiv 2512.18390, GSE,
     irreversible).
   - Quantile horizon-cost decisions appear in Regol et al. (ICML 2025).
   - Novelty is NOVEL-INTEGRATION: reversibility, discounting, and budgeted, delayed,
     disagreement-only evidence.

## Novelty assessment (section 10 of the brief)

| candidate novelty | supported? |
|---|---|
| New algorithmic primitive | **No.** A quantile/LCB payback hurdle is published (Challenger GSE; Regol UPF). |
| Novel, useful integration | **Yes, modestly.** A reversible payback rule with a confidence-bound hurdle on discounted, budgeted, delayed, disagreement-only labels. No source found combines these. The ablation shows the confidence bound matters (−25 real, −51 synthetic). |
| New restricted problem formulation | **Partly.** The budgeted delayed two-model replacement contract with explicit c_q and c_s is a clean formulation, and the benchmark harness is reusable. But Gong–Zhang (paid observations) and Challenger (switching economics) cover nearby formulations. |
| Empirical methods contribution | **Yes.** A matched-contract benchmark of 18 families with a fidelity classification. It shows that cost-unaware selection methods churn, certified methods pay 4–17% for their guarantee where challengers are usually better, and memory length dominates hurdle form on real data. |
| Analysis contribution | **Descriptive only.** It decomposes failures into three mechanisms (07). No theorem is claimed. |

## Framing recommendation

Frame the paper as **"Economic model replacement under label budgets and delay: a matched-contract
benchmark and a reversible confidence-bound payback rule"**. Put the benchmark finding and the
three-mechanism decomposition next to the method. Present EQSDp as the representative of the
reversible confidence-bound class (Beta ≡ Wald), not as a uniquely tuned winner. This frames the
real-data ties against tuned Wald and scaled-margin as consistent with the class claim, rather than
as defeats of the paper's method.
