# 07 — Failure mechanisms behind each meaningful difference

Evidence comes from:
- secondary metrics (05: switches, labels, first-deploy round, promotion rates);
- the Δ split by evaluator-side episode type (05);
- the synthetic regime table (04, `synth_analysis.txt`).

The evaluator-side gain is used only in this analysis, never by a policy.

## Wins

| comparator | failure mode | evidence (nine; synthetic) |
|---|---|---|
| Qiu-style Hedge | **Churn plus slow blocked movement.** Fixed-share Hedge on IW differences moves in blocks of max(d+1, T/20) and does not price switching. It pays on both episode types. | 2.41 vs 1.43 switches; Δ −8.5 (challenger better) and −8.6 (not better); synthetic: worst on reversal/late cells (C3) |
| Gong–Zhang-style (SD) | **Point-estimate payback churn.** A discounted IW point estimate plus a fixed margin crosses the hurdle on noise and switches back. Arm B's confidence-bound hurdle widens when evidence is thin. | 2.04 vs 1.43 switches (switch cost 10.2 vs 7.1); Δ −6.0 on not-better episodes; synthetic: 6.4 vs 3.3 switches on null |
| Gong–Zhang-style (RD w800 m20) | *No failure on real data.* A long window plus a larger margin removes the churn (1.09 switches), and it ties arm B. The SD win is a tuning-transfer effect. | Δ +0.9 n.s. |
| UPF-style T3 | **Slow, periodised adoption.** The quantile comparison runs per period of length m, after warm-up, on extrapolated cells. It adopts a better challenger late and sometimes never. | first deploy (gain > 0) 472 vs 282; promoted when better .84 vs .97; Δ −17.2 (better) vs +10.0 (not better) |
| Challenger-style (irreversible) | **No rollback, conservative.** It adopts later (359 vs 282) and cannot return after a reversal. It is better when the challenger is not better (+11.7). | synthetic: change cells 370–392 vs 346; guard cells 367 vs 374 |
| Model Picker / Selector / CAMS / LLM picker / variance-min | **Switching cost is not in the objective.** They track the currently best-estimated model, so they churn (2.5–3.4 switches). Model Picker partly offsets this with label efficiency (48 labels vs 153: about −5 label cost). These methods win on la_crime, montgomery and nyc, and lose on boston, dc and sf, where the challenger is better from the start and they adopt it as fast while spending fewer labels. | switch cost 12.6–17.1 vs 7.1; per-dataset Δ positive on boston/dc/sf (e.g. Model Picker +4.4/+8.4/+7.7) |
| ARW label clock | **Noise flipping.** With no margin, the adaptive window flips on single labels. | 14.8 switches |
| Posterior-median ablation | Same evidence, **no confidence bound**: churn. | 6.4 switches; Δ −24.9 (9/9); synthetic −50.8 |

**The common mechanism.** Arm B's gains come from a switching hurdle that scales with evidence
uncertainty (a confidence bound) and stays reversible. This avoids three distinct failures:
1. churn by cost-unaware or point-estimate rules: Qiu-style, GZ-style, the selection adapters,
   ARW, the median ablation;
2. slow adoption by periodised or certified rules: UPF-style, the certified class;
3. no rollback: the Challenger-style rule.

## Ties and losses

- **Wald LCB (any tuning) and arm A.** These are the same mechanism. A Beta posterior quantile and
  a Wald bound with the same discounting are interchangeable (synthetic Δ −0.3; real −0.2).
- **Real-tuned λ=.97 controls beat arm B by about 0.5%.**
  - Real streams have autocorrelated outcomes (lag-1 .3–.95, NEXT_METHOD ledger) and slow drift.
  - λ=.9 forgets evidence too fast there. Arm B switches more (1.43 vs 1.02) and promotes falsely
    more (.71 vs .54).
  - This is hyperparameter transfer (M5), not a hurdle defect. Arm A (λ=.95) closes most of the gap.
- **econF ties arm B on real data and is cheaper on 8/9 datasets.**
  - It front-loads labels and decides early with a point estimate. It switches rarely (0.85).
  - It loses badly only on kc_311, where only 26% of episodes have a better challenger and early
    commitment is wrong (−57.7).
  - On synthetic data it is −16: front-loading fails on late changes.
- **Certified methods.**
  - Arm B is cheaper where the challenger is better: they delay adoption (first deploy 560–1066)
    or never adopt (35–58% promoted when better).
  - Certified methods are cheaper where the challenger is not better (Δ +15 to +18 for arm B):
    arm B promotes falsely in 71% of those episodes.
  - This trade is the guarantee itself, not a defect of either side.
