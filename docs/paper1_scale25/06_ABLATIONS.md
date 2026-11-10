# 06 — Ablations, headroom and oracle bounds (Workstream B)

Development data only: the nine registered windows (751 episodes, both parities) and the 7 fresh 2025-26 windows (547 episodes; development-exposed after doc 20). No confirmation window exists and none was built. J = net cost / T x 100 (pp of T); seed-averaged per episode, equal-dataset means, paired stratified episode bootstrap (2000, rng seed 0), negative = better. Contract B=200, c_q=.05, c_s=5, delay 100, 10 policy seeds. No tail statistic is used as a criterion. Tables: `docs/paper1_scale25/algo/tables/`; code `scripts/paper1_scale25/algo/` (`ablation.py`, `headroom.py`, `oracle.py`, `calibrate.py`).

## 1. Provenance and reuse
- Reused unchanged (same seeds, windows, contract; bitwise-checked where a rerun overlapped): EQ+cut `s2armr_H1100`, `P1_E48_s0`, `P1_F60_s0`, `P2_K2__E48_F60`, `s2wald_l0.98_g0.3_H1100`, `P4W__P2_K2__E48_F60` on the nine windows (search60 `full/`); EQ+cut, EQ+pair, W+cut, W+pair, arm R and the 25 comparators on the fresh windows (`fresh/records_all.jsonl`); the 25 comparators on the nine (sota_expansion panel).
- Newly run here: W+cut+E48 and W+cut+F60 (both pools), EQ+cut+E48 and EQ+cut+F60 on the fresh windows, and the label-matched controls. An empty-module spec equals `s2armr_H1100` / `s2wald_*_H1100` bitwise. `scripts/paper1_scale25/algo/test_algo.py`: 69 tests pass (all-off identity, budget and cutoff, no future-label access by loss-suffix replacement).
- Label-matched controls sit on the same parent (same evidence, switching rule, cutoff H=1100) with the parent's acquisition replaced. **UNI** buys the first disagreement at or after each of N evenly spaced calendar slots. **UNC** buys a disagreement with probability min(1, c*H(mu)), H the binary entropy of the parent's posterior mean. N and c are calibrated per dataset so the mean label count equals that of the matched pair arm (EQ+pair for the EQ parent, W+pair for the Wald parent). Calibration uses label counts only, on a 1-in-5 episode, 2-seed subsample, and is verified on the full runs: pool means 53.5 (UNI) and 54.0 (UNC) against 53.5 for the pair on the nine; 55.1 and 56.0 against 55.0 on fresh.

## 2. Ablation table (all episodes)
Equal-dataset means. Components are pp of T and sum to regret over the best fixed model.

| pool | arm | J | labels | switches | late adopt. | false prom. | churn | label spend | residual |
|---|---|---|---|---|---|---|---|---|---|
| nine (9 win, 751 ep) | EQ+cut | 23.686 | 70.8 | 1.219 | .584 | .222 | .084 | .177 | .179 |
| | EQ+cut+E48 | 23.650 | 44.1 | 1.134 | .616 | .240 | .069 | .110 | .175 |
| | EQ+cut+F60 | 23.635 | 78.4 | 1.232 | .541 | .193 | .086 | .196 | .178 |
| | EQ+cut+E48+F60 | 23.583 | 53.5 | 1.159 | .565 | .196 | .073 | .134 | .175 |
| | W+cut | 23.689 | 70.8 | 1.226 | .586 | .222 | .085 | .177 | .179 |
| | W+cut+E48 | 23.652 | 44.1 | 1.139 | .615 | .243 | .069 | .110 | .175 |
| | W+cut+F60 | 23.638 | 78.4 | 1.239 | .542 | .194 | .088 | .196 | .178 |
| | W+cut+E48+F60 | 23.582 | 53.5 | 1.166 | .562 | .197 | .074 | .134 | .175 |
| | UNI (EQ) | 23.651 | 53.5 | 1.113 | .615 | .225 | .061 | .134 | .175 |
| | UNC (EQ) | 23.634 | 54.0 | 1.125 | .624 | .195 | .067 | .135 | .174 |
| fresh (7 win, 547 ep) | EQ+cut | 23.104 | 76.1 | 1.191 | .834 | .020 | .053 | .190 | .239 |
| | EQ+cut+E48 | 23.048 | 47.7 | 1.126 | .861 | .025 | .040 | .119 | .235 |
| | EQ+cut+F60 | 23.064 | 81.9 | 1.180 | .782 | .021 | .051 | .205 | .238 |
| | EQ+cut+E48+F60 | 23.013 | 55.0 | 1.117 | .811 | .024 | .039 | .138 | .235 |
| | W+cut | 23.103 | 76.1 | 1.194 | .833 | .020 | .054 | .190 | .239 |
| | W+cut+E48 | 23.049 | 47.7 | 1.130 | .862 | .025 | .041 | .119 | .235 |
| | W+cut+F60 | 23.064 | 81.9 | 1.181 | .781 | .021 | .051 | .205 | .238 |
| | W+cut+E48+F60 | 23.014 | 55.1 | 1.118 | .811 | .024 | .039 | .138 | .235 |
| | UNI (EQ) | 23.072 | 55.1 | 1.102 | .878 | .020 | .035 | .138 | .235 |
| | UNC (EQ) | 23.075 | 56.0 | 1.121 | .873 | .020 | .039 | .140 | .235 |

The Wald-parent UNI/UNC rows are in `ablation_levels_*.csv`; they are within .002 of the EQ versions.

## 3. Contrasts (Delta J, pp; 95% CI)

| contrast | nine, all episodes | fresh |
|---|---|---|
| E48 - parent (EQ) | -0.036 [-.064,-.005] (-0.15%) | -0.056 [-.085,-.027] (-0.24%) |
| F60 - parent (EQ) | -0.051 [-.095,-.020] (-0.22%) | -0.040 [-.061,-.017] (-0.17%) |
| pair - parent (EQ) | -0.103 [-.152,-.064] (-0.44%) | -0.090 [-.130,-.049] (-0.39%) |
| **interaction** J(pair)-J(E48)-J(F60)+J(parent), EQ | -0.016 [-.045,+.007] | +0.005 [-.017,+.032] |
| interaction, Wald parent | -0.019 [-.048,+.005] | +0.004 [-.019,+.031] |
| pair - UNI (label-matched, EQ) | -0.068 [-.121,-.016] | -0.059 [-.116,+.001] |
| pair - UNC (label-matched, EQ) | -0.051 [-.080,-.022] | -0.062 [-.098,-.025] |
| UNI - parent | -0.035 [-.104,+.027] | -0.031 [-.087,+.027] |
| UNC - parent | -0.052 [-.095,-.017] | -0.029 [-.057,-.001] |
| W+cut - EQ+cut | +0.004 [.000,.008] | -0.000 [-.002,+.001] |
| EQ+pair - W+cut | -0.107 [-.156,-.067] | -0.090 [-.130,-.049] |

Parity split on the nine (EQ): pair - parent even -0.081, odd -0.125. Interaction even -0.008 and odd -0.025, both CIs include 0. Pair - UNI even -0.023 [-.104,+.049] (not distinguishable), odd -0.113 [-.200,-.035]. Pair - UNC even -0.031 [-.070,+.010], odd -0.071 [-.114,-.029]. Per-dataset values are in `ablation_contrasts_*.csv`.

Reading:
- **Interaction is not established.** The pair effect is roughly the sum of the two modules (sum of singles -0.087 on the nine, -0.096 on fresh). The interaction CI includes 0 in every pool, parity and parent. Do not claim synergy.
- **Mechanism by component** (change vs parent, pp). E48 mainly cuts label spend (-0.067 on the nine) and churn, and adds late adoption (+0.032) and false promotion (+0.019). F60 mainly cuts late adoption (-0.044) and false promotion (-0.028) and adds about 7.5 labels. The pair keeps most of the F60 timing gain (late adoption -0.019) and most of the E48 fee saving (label spend -0.043).
- **Label-matched controls explain a large part of the gain.** Uncertainty sampling with the same label count recovers -0.052 (nine) and -0.029 (fresh) against the parent, roughly half of the pair's effect on the nine and a third on fresh. What the E48+F60 acquisition adds beyond a label-matched control is -0.05 to -0.07 pp (about 0.2 to 0.3% of J). The CI excludes 0 for UNC in both pools and for UNI on the nine. For UNI on fresh it is borderline (upper bound +0.001). On the nine even episodes alone the pair-vs-matched contrasts include 0.
- EQ and Wald parents give the same results (W+cut equals EQ+cut to .004), consistent with doc 20.

## 4. Headroom by dataset
Definitions (evaluator-side, hindsight, label-free). J_fix = min(L0, L1), the trace_run convention with no switch fee. J_orc1 = best single switch time, paying c_s, starting on model 0. J_orc3 = at most 3 switches. Strongest reference = per dataset the lowest all-episode J among references with full-episode coverage (descriptive, optimistic for the reference). `gap` = (J_arm - J_orc1)/J_arm. `label-paid gap` also subtracts the arm's own label spend, i.e. a hypothetical policy with hindsight timing that still buys the arm's labels. Timing regret = late adoption + false promotion + churn. All are % of the arm's J.

| pool | dataset | strongest ref | J_ref | gap to J_orc1 | label-paid gap | timing regret | late adoption |
|---|---|---|---|---|---|---|---|
| nine | austin | EQ+cut | 33.77 | 2.39 | 1.94 | 1.62 | 0.81 |
| nine | cincinnati | W+cut | 24.13 | 4.71 | 3.93 | 3.49 | 2.19 |
| nine | dallas | EQ+cut | 24.11 | 4.94 | 4.15 | 3.30 | 2.46 |
| nine | dc | W+cut | 19.27 | 8.93 | 7.85 | 7.64 | 7.54 |
| nine | kc | hoef .9/.45 | 29.82 | 5.83 | n/a | n/a | n/a |
| nine | montgomery | hoef .97/.3 | 18.38 | 4.43 | n/a | n/a | n/a |
| nine | oakland | W+cut | 22.51 | 2.07 | 1.56 | 1.36 | 1.03 |
| nine | sandiego | EQ+cut | 18.90 | 5.48 | 4.43 | 3.89 | 1.71 |
| nine | sf | W+cut | 22.03 | 7.55 | 6.62 | 6.37 | 6.22 |
| fresh | austin | model_picker | 21.79 | 8.35 | 7.85 | 7.72 | 7.49 |
| fresh | cincinnati | EQ+cut | 35.28 | 2.45 | 1.98 | 1.43 | 0.86 |
| fresh | dallas | EQ+cut | 21.59 | 4.70 | 3.85 | 3.45 | 3.25 |
| fresh | dc | online_llm_picker | 18.85 | 9.57 | 8.08 | 7.83 | 7.01 |
| fresh | kc | econF_mo5_m5 | 26.98 | 4.02 | 2.17 | 1.76 | 1.76 |
| fresh | sandiego | EQ+cut | 17.39 | 4.84 | 3.69 | 3.52 | 3.28 |
| fresh | sf | EQ+cut | 19.75 | 3.74 | 2.90 | 2.45 | 1.88 |

Panel comparators carry no decomposition columns (n/a); their gap to J_orc1 is exact. The EQ+pair rows are in `headroom_by_dataset.csv`. Equal-dataset means for EQ+pair: label-paid gap 4.2% (nine) and 4.4% (fresh); late adoption 2.6% and 3.8% of J; false promotion 0.8% and 0.1%; churn about 0.3%; label spend about 0.6%; residual about 1%.

**Does the best-fixed reference understate headroom? Mostly no.** J_orc1 - J_fix is within -0.2% to +1.3% of J on all datasets except nine kc (-1.06%); a positive value is just the unavoidable 0.25 pp adoption fee. The three-switch oracle gains over J_fix are 3.3% on nine kc, 0.6 to 1.1% on cincinnati, dallas, montgomery and sandiego (nine), and none or negative elsewhere. Only nine kc has material mid-episode regime-change headroom.

**Which datasets can possibly support a >=2.5-3.5% reduction?** Treat the label-paid oracle gap against the strongest reference as an absolute ceiling; it presumes hindsight timing and is not achievable.
- At or above 3.5%: nine dc (7.9), sf (6.6), kc (about 5.8 on the label-free gap), sandiego (4.4), dallas (4.2), cincinnati (3.9); fresh austin (7.9), dc (8.1), dallas (3.9), sandiego (3.7).
- Between 2.5% and 3.5%: fresh sf (2.9).
- Below 2.5%: nine austin (1.9) and oakland (1.6); fresh cincinnati (2.0) and kc (2.2).
- Only nine dc and sf and fresh austin and dc, where late adoption is 6 to 8% of J, have a timing-regret ceiling comfortably above 3.5%. Elsewhere timing regret is under 4% of J, so a 2.5-3.5% reduction would need almost all of it removed. The realised v1 recovery is about 0.1 pp of about 23 pp (0.4% of J), 5 to 10% of this ceiling.
