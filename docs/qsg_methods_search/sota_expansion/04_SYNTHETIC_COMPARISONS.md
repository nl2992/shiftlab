# 04 — Synthetic comparisons (exploratory, fresh seeds)

**Status: post-confirmation, exploratory.** The setup:
- Fresh seed base 2026111501 (never used before), 50 seeds;
- the 14 C3 regimes (10 change + 4 guard), equal regime weights;
- the C4 contract (B=200, c_q=.05, c_s=5).

The C3 and P1 seeds are spent, and this regime family was used to develop EQSDp, so these numbers
describe behaviour. They do not confirm anything independently. Arm B (`EQSDp_l0.9_g0.2`) is unchanged.

Raw records (gitignored): `outputs/qsg_methods_search/sota_expansion/synth/` (first pass) and
`synth2/` (the real-dev-selected configurations and the median ablation, same seeds). They are
merged in `synth_all/`. Arm B's 700 overlapping rows are identical across the passes
(max |Δnet| = 0.0). The arm B family mean (354.19) reproduces C3 (354.1) on new seeds.

```bash
cd scripts/qsg_methods_search && PYTHONPATH=../failure_atlas_v2_flq ../../.venv/Scripts/python.exe analyze_sota.py synth ../../outputs/qsg_methods_search/sota_expansion/synth_all/records.jsonl
```

## Contrasts: Δ = J(arm B) − J(comparator), family mean per 2,000-event episode

The test is a paired t over 50 seeds, Holm-adjusted over the 43 contrasts. "% regret" is Δ as a
share of the comparator's expected-oracle regret. SD = synthetic-dev-selected configuration;
RD = configuration selected on the 14 real development streams.

| comparator (fidelity class, 02) | Δ (95% CI) | % cost | % regret | Holm p |
|---|---|---|---|---|
| Wald LCB, SD λ.9 γ.2 (internal) | −0.31 [−0.75, +0.14] | −0.1 | −0.7 | 0.17 |
| scaled margin, SD (internal) | −2.40 [−3.00, −1.80] | −0.7 | −5.5 | <1e-3 |
| dwell, SD (internal) | −3.02 [−3.84, −2.19] | −0.8 | −6.8 | <1e-3 |
| Hoeffding LCB, SD (internal) | −3.34 [−4.28, −2.40] | −0.9 | −7.5 | <1e-3 |
| arm A λ.95 (descriptive) | −4.52 [−5.34, −3.69] | −1.3 | −9.8 | <1e-3 |
| dwell, RD λ.97 k3 | −7.58 [−8.38, −6.78] | −2.1 | −15.5 | <1e-3 |
| S2 Qiu-style (C) | −8.61 [−10.01, −7.22] | −2.4 | −17.2 | <1e-3 |
| S1 tuned GZ-style SD w100 m10 (C) | −8.74 [−10.23, −7.25] | −2.4 | −17.4 | <1e-3 |
| Wald LCB, RD λ.97 γ.2 | −9.50 [−10.67, −8.32] | −2.6 | −18.7 | <1e-3 |
| scaled margin, RD | −12.57 [−14.10, −11.05] | −3.4 | −23.3 | <1e-3 |
| S1 GZ-style untuned (C) | −14.90 [−16.38, −13.43] | −4.0 | −26.5 | <1e-3 |
| econF RD mo5 m0 (internal) | −14.99 [−16.75, −13.22] | −4.1 | −26.6 | <1e-3 |
| N1 Challenger-style GSE, RD λ.9 γ.3 (C) | −15.08 [−16.39, −13.77] | −4.1 | −26.7 | <1e-3 |
| econF SD mo5 m5 (internal) | −16.17 [−17.97, −14.37] | −4.4 | −28.1 | <1e-3 |
| Hoeffding LCB, RD | −16.58 [−18.00, −15.16] | −4.5 | −28.6 | <1e-3 |
| economic replacement (internal) | −17.71 [−19.57, −15.85] | −4.8 | −30.0 | <1e-3 |
| S5 Model Selector causal (C) | −21.61 [−23.32, −19.89] | −5.7 | −34.3 | <1e-3 |
| S1 tuned GZ-style RD w800 m20 (C) | −23.40 [−24.76, −22.03] | −6.2 | −36.1 | <1e-3 |
| never switch (control) | −24.46 [−25.74, −23.18] | −6.5 | −37.2 | <1e-3 |
| S4 Model Picker (B) | −25.13 [−27.60, −22.67] | −6.6 | −37.8 | <1e-3 |
| online LLM picker (B) | −27.83 [−30.30, −25.35] | −7.3 | −40.2 | <1e-3 |
| e-SR, RMM bets, full α (C; certified) | −28.74 [−30.51, −26.98] | −7.5 | −41.0 | <1e-3 |
| S3 UPF-style SD δ.95 m50 (B) | −30.06 [−31.72, −28.41] | −7.8 | −42.1 | <1e-3 |
| S3 UPF-style RD δ.8 m50 (B) | −30.43 [−32.07, −28.79] | −7.9 | −42.4 | <1e-3 |
| N1 Challenger-style GSE, nominal λ1 γ.2 (C) | −30.91 [−32.44, −29.38] | −8.0 | −42.8 | <1e-3 |
| S6 CAMS (B) | −32.21 [−34.47, −29.96] | −8.3 | −43.8 | <1e-3 |
| variance-min IPW (C) | −32.42 [−34.81, −30.04] | −8.4 | −44.0 | <1e-3 |
| QSG (internal; certified) | −33.25 [−35.06, −31.44] | −8.6 | −44.6 | <1e-3 |
| two-sided e-SR (B; certified) | −33.85 [−35.81, −31.90] | −8.7 | −45.0 | <1e-3 |
| S7 DISCERN-style (B; certified) | −34.44 [−35.72, −33.16] | −8.9 | −45.4 | <1e-3 |
| S10 gated certificate (B; certified) | −35.20 [−36.80, −33.61] | −9.0 | −46.0 | <1e-3 |
| S7 DISCERN +QCE+front (C; certified) | −36.31 [−38.24, −34.38] | −9.3 | −46.8 | <1e-3 |
| S9 Xu acquisition (C; certified) | −37.03 [−38.73, −35.33] | −9.5 | −47.2 | <1e-3 |
| S10 MOPE adaptive range +front (C; certified) | −37.46 [−39.29, −35.64] | −9.6 | −47.5 | <1e-3 |
| S8 SMCS +QCE+front (C; certified) | −37.68 [−39.41, −35.95] | −9.6 | −47.7 | <1e-3 |
| S10 MOPE adaptive range (B; certified) | −38.75 [−40.71, −36.80] | −9.9 | −48.4 | <1e-3 |
| S8 SMCS retain-incumbent (B; certified) | −38.83 [−40.60, −37.06] | −9.9 | −48.4 | <1e-3 |
| S7 DISCERN design floor (B; certified) | −39.01 [−40.91, −37.11] | −9.9 | −48.5 | <1e-3 |
| Shekhar–Ramdas RCS any-excl (B; certified) | −39.21 [−41.29, −37.14] | −10.0 | −48.7 | <1e-3 |
| S9 Xu +front (C; certified) | −39.49 [−41.15, −37.84] | −10.0 | −48.9 | <1e-3 |
| S7 DISCERN design floor +front (C; certified) | −43.58 [−45.84, −41.31] | −11.0 | −51.3 | <1e-3 |
| **ablation: arm B with posterior-median hurdle** | −50.79 [−52.93, −48.65] | −12.5 | −55.1 | <1e-3 |
| ARW label clock (B) | −101.97 [−104.56, −99.39] | −22.4 | −71.1 | <1e-3 |

## Behaviour (family means)

| policy | J | change | guard | exp.-oracle regret | null/worse promote | switches on null |
|---|---|---|---|---|---|---|
| arm B | **354.2** | 346.1 | 374.3 | 41.4 | 0.92 | 3.3 |
| Wald SD | 354.5 | 346.1 | 375.5 | 41.7 | 0.93 | 3.6 |
| Hoeffding SD | 357.5 | 353.1 | 368.6 | 44.7 | 0.76 | 1.5 |
| tuned GZ-style SD | 362.9 | 353.1 | 387.6 | 50.1 | 0.98 | 6.4 |
| Challenger-style RD | 369.3 | 370.0 | 367.5 | 56.4 | 0.41 | 0.5 |
| never switch | 378.7 | 379.8 | 375.8 | 65.8 | 0 | 0 |
| UPF-style SD | 384.3 | 391.2 | 367.0 | 71.4 | 0.39 | 0.7 |
| best certified (e-SR RMM bets) | 382.9 | 386.7 | 373.7 | 70.1 | 0.01 | 0.02 |
| arm B, median hurdle | 405.0 | 384.2 | 457.0 | 92.1 | 1.00 | 23.8 |

## Reading

1. **Arm B is the lowest-cost policy on this family.** It is significantly cheaper than every
   comparator except the matched Wald LCB at λ=.9, where Δ = −0.3 is not significant. This replicates
   the P1 panel (Wald tie; Hoeffding, scaled margin and dwell about −2 to −3) on fresh seeds.
2. **Against the published-method adapters, the advantage is meaningful.** It is 2–10% of cost and
   17–49% of expected-oracle regret:
   - tuned GZ-style −8.7; Qiu-style −8.6;
   - Model Selector −21.6; Model Picker −25.1; UPF-style −30;
   - Challenger-style −15 to −31; CAMS −32.
   Every one of these adapters is class B or C. None is a native reproduction.
3. **The certified methods are 33–44 units dearer, but they hold false-promotion control.** Their
   null/worse promotion is 0–1%; arm B's is 92%. This is a different guarantee class, so cost is not
   dominance (see 06 and 08).
4. **The confidence-bound hurdle is the mechanism.**
   - Replacing it with the posterior median makes arm B churn (23.8 switches on null) and costs
     +50.8.
   - The Challenger-style rule uses the same payback with a Hoeffding bound. Being irreversible, it
     loses on reversal/change regimes (change 370 vs 346) and wins on guard regimes (367 vs 374).
5. **Real-dev-selected baselines transfer badly to synthetic.** Every λ=.97 configuration is worse
   here than its λ=.9 synthetic-dev twin, for example Wald 363.7 vs 354.5. On the 14 real development
   streams the ordering reverses: every family selected λ=.97 (`dev_selection.log`). So the best memory length is environment-dependent (M5). Arm B's λ=.9 is a
   synthetic-family choice.
