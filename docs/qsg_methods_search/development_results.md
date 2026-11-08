# QSG methods search: development results

All results here are **development** evidence on exposed synthetic regimes. None is confirmatory.

## D0: baseline panel (seed base 2026110701, 50 seeds, 13 regimes, 39 policies)

Reproduce:

```bash
OPENBLAS_NUM_THREADS=1 uv run python scripts/failure_atlas_v2_flq/run_atlas_v2.py --kind synthetic --seeds 50 --seed-base 2026110701 --regimes F0_better,V_better_a,V_better_b,V_better_c,V_bursty,V_dep_better_r5,F7_near_better,F0_null,V_null,V_worse,V_null_dep_r8,F1_late_800,F3_reversal_800 --extra v2_extra --workers 12 --out outputs/qsg_methods_search/panel0
```

(`OPENBLAS_NUM_THREADS=1` is required: at 20 workers the default OpenBLAS thread pools exhausted
memory and killed workers mid-run.)

Mean net cost (lower is better). The alt mean is over the 7 persistent-improvement regimes.

| policy | F0_better | V_better_a | V_better_c | F7_near | alt mean | F1_late_800 | F3_rev_800 | F0_null | V_null | V_worse | V_null_dep_r8 (promote rate) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hindsight oracle | 302.8 | 345.7 | 347.7 | 323.8 | | 296.8 | 290.8 | 342.0 | 378.0 | 320.6 | 345.3 |
| model_selector_causal | 327.8 | 374.5 | 386.1 | 357.1 | 345.7 | 370.3 | 387.0 | 394.8 | 435.4 | 346.5 | 437.3 (0.90) |
| economic_replacement | 331.5 | 372.2 | 391.3 | 350.1 | 346.2 | 350.7 | 411.4 | 374.7 | 412.3 | 351.2 | 413.3 (0.84) |
| qiu_delayed_movement | 331.2 | 377.6 | 393.5 | 357.0 | 349.3 | 342.7 | 352.1 | 390.8 | 432.4 | 348.4 | 434.1 (1.00) |
| QSG | 349.8 | 414.6 | 409.6 | 388.0 | 372.7 | 400.9 | 409.9 | 367.9 | 412.8 | 332.0 | 414.8 (0.26) |
| SMCS+QCE+front | 353.8 | 420.5 | 416.0 | 389.3 | 376.9 | 401.6 | 423.6 | 367.9 | 412.7 | 332.0 | 414.2 (0.22) |
| xu+front_only | 353.2 | 416.1 | 431.4 | 386.4 | 379.3 | 401.6 | 429.5 | 367.9 | 411.9 | 332.0 | 411.4 (0.08) |
| gated_adaptive_range+front | 358.9 | 435.2 | 423.5 | 393.4 | 384.6 | 400.9 | 421.7 | 367.9 | 411.8 | 331.1 | 411.0 (0.12) |
| QSG-env8 | 391.9 | 453.4 | 478.7 | 397.0 | 414.7 | 401.5 | 398.8 | 367.9 | 411.8 | 332.0 | 411.6 (0.00) |
| never switch | 418.2 | 460.8 | 535.1 | 393.2 | 434.6 | 391.6 | 348.2 | 357.9 | 401.8 | 322.0 | 401.6 (0.00) |

Findings:

1. **The M1/M2 frontier is reproduced.** On persistent improvements the fast uncertified methods
   are about 25-30 units cheaper than the best certified method (QSG), and 30-40 cheaper than the
   dependence-safe certified methods. On null and worse streams they cost 11-75 more than never
   switching, through 2-11 switches per episode.
2. **Certified methods pay about 10 units on every null stream** (all 200 labels at c_q=.05),
   because no certified host stops buying labels when the challenger cannot pay back.
3. **M4 is reproduced.** QSG promotes on 0.26 of V_null_dep_r8 streams (registered bound .094);
   among front-loaded certified hosts only Xu (0.08) stays under it. QSG-env8 is safe but gives up
   most of the speed (alt mean 414.7 vs 372.7).
4. **The strongest comparator on the stationary-persistent family is the plain economic payback
   control** (`economic_replacement`, a development-tuned point-estimate rule from the repo's
   controls). Family mean regret over the 11 D1 regimes: economic_replacement 33.5,
   model_selector 38.9, qiu 40.4, QSG 48.2. Its weak cells are V_worse (+29 over never switching),
   null churn, and reversal (no rollback: 411 vs 348 for never switching).
5. Late (F1_late_800) and reversal cells: every adaptive method except qiu/gong/econ loses to never
   switching on reversal; this matches `docs/sota_fidelity/econ_gate_bound_results.md` (other
   branch).

## D1: EQS on the stationary-persistent family (seed base 2026110711, 40 seeds) — STOP

Protocol: `development_protocol.md` §D1. Code: `scripts/qsg_methods_search/eqs.py`. Analysis:
`uv run python scripts/qsg_methods_search/analyze_d1.py outputs/qsg_methods_search/d1/records.jsonl`.
Parity check: `econ_mo15_m0` reproduces `economic_replacement` exactly on every row.

| policy | family mean net (11 regimes) | family regret (hindsight) | null promote | labels on null |
|---|---|---|---|---|
| econF_mo5_m5 (best tuned econ+front) | **357.56** | 29.8 | 0.75 | 200 |
| EQS_g0.1-no_rollback (best EQS) | 358.03 | 30.3 | 0.41 | 162 |
| EQS_g0.1_mf0.0_gr.02 | 358.12 | 30.3 | 0.38 | 132 |
| econ_mo5_m10 (best econ, paced) | 359.25 | 31.5 | 0.68 | 200 |
| economic_replacement (default) | ~361.6 | | | 200 |

The entire grid of about 70 econ, econ+front and EQS configurations spans 357.6–361.

**Advance rule not met**: EQS does not beat the straightforward econ+front composition.

Diagnosis (expected-oracle regret by regime):

1. **econ+front is already at the delay floor on persistent improvements.** Median first
   promotion is at event ~125, i.e. the 100-event label delay plus 5 labels. Its expected-oracle
   regret on F0_better / V_better_a / F7_near is 17.6 / 18.4 / 14.9, about delay × per-event gain.
   No rule can act before labels return.
2. **EQS's confidence bound and acquisition stop buy null safety at the cost of alternatives.**
   Expected-oracle regret on F0_null / V_null / V_worse falls from 19.6 / 19.6 / 28.5
   (econ+front) to 11.4 / 8.4 / 4.6. On F0_better it rises from 17.6 to 31.6, through false
   early discards. Under equal regime weights these offset. The trade is a prior over regimes,
   not an algorithmic gain.
3. **Benchmark finding (C1 material):** a 5-label point-estimate payback rule with front-loading
   (a trivial composition, uncertified) beats every published certified and uncertified adapter
   on this family (D0 best: economic_replacement 33.5 hindsight regret; QSG 48.2). Certification
   at alpha=.05 costs 20–100 units per episode here. The trivial rule promotes on 75% of null
   streams. Promoting under an exact null is cheap; the harm is concentrated in V_worse.
4. The change regimes hold the remaining headroom: expected-oracle regret 55–121 on F1_late_800 /
   F3_reversal_800 for every D1 policy. This motivates D2.
