# 16. Recovery factorial: freeze (selected on even episodes only)

Machine-readable freeze: `16_RECOVERY_FREEZE.json` (committed and pushed before any odd episode is run;
`stage5_odd.py` refuses otherwise). Protocol: doc 15 section 3. Contract: B=200, c_q=.05, c_s=5, T=2000,
10 policy seeds, nine development datasets, even episodes for selection, odd episodes once for checking.
No retuning after the odd results. No held-out (new chronological) data is built or opened.

## Fair references (best of their F0 grids on even episodes; grid median also reported)

| reference | policy | J (even) | grid best / median / worst | n |
|---|---|---|---|---|
| EQSDp arm R + cutoff | `s2armr_H1100` | 475.022 | 474.823 / 475.186 / 478.154 | 4 |
| Wald + cutoff | `s2wald_l0.98_g0.3_H1100` | 475.057 | 474.824 / 475.297 / 478.457 | 16 |

The references are chosen by the rule "lowest even-episode J among entries with dL/T <= +0.1 pp versus the
base policy `wald_l0.97_g0.2`". The grid minima (`s2armr_H1300`, dL/T +0.126 pp; `s2wald_l0.97_g0.3_H1300`,
+0.114 pp) fail the loss rule; both selected references have dL/T +0.078 pp. Full grids:
`outputs/paper1_eqsdp/stage5/selection_A.json`. Both selected references use cutoff H=1100.

## Chosen configurations (even episodes, best-of-grid; grid median in brackets)

| arm | configuration | grid n | J best | J median | control (matched) |
|---|---|---|---|---|---|
| R1 floor + cutoff | `s5r1_f0.1_G50_c1100` | 9 | 473.843 | 474.106 | calendar `s5cal_m50_c1100` (labels 41.9 vs 44.6) |
| R2 EVSI (Bayes mean rule) | `s5evsi_h0.0001_l0_cnone` | 12 | 473.986 | 474.559 | entropy `s5ent_h0.0001_cnone_th3` (32.5 vs 35.6); calendar `s5cal_m40_cnone` |
| R3 EVSI + tail | `s5tail_h0.0001_l0_cnone_t2` | 6 | 473.415 | 473.783 | no-tail = R2; tail-only `s5tail_only_h0.0001_l0_cnone_t2` (51.5 vs 52.3) |
| R2-roll (kmax 2) | `s5roll_h0.0001_l0_cnone_k2` | 2 | 473.634 | 473.642 | one-step R2 |

Best-of-grid optimism (best minus median) on even episodes: F0 EQSDp -0.36, F0 Wald -0.47, R2 -0.57,
R1 -0.26, R3 -0.37, R2-roll -0.01 J units. Odd-episode numbers will be reported against the median too.

## R2-roll decision

Built, because R2 and R3 both beat both references on even episodes with 95% CIs excluding 0
(R2 dJ -1.04 / -1.07; R3 dJ -1.61 / -1.64 versus EQSDp / Wald references). Implementation: query now iff
some bundle of k <= kmax labels (this one plus k-1 later labels released together) has
EVSI_k > k (c_q + lambda_t); grid kmax in {2, 3}; selected kmax = 2.

## Deviation (recorded)

R2 uses a Bayes posterior-mean preposterior rule (`rule="mean"`). The first-planned rule, arm R's
gamma-quantile payback rule inside the preposterior, starved: a single label cannot flip a quantile
decision, so it purchased about 2-2.5 labels per episode (pilot: `s5evsi_h0.0005_l0_c1100_quantile`
J 506.17, 2.00 labels; `..._cnone_quantile` J 500.74, 2.54 labels, versus 473-475 for the mean rule).
The quantile rule is reported as a negative result and is not carried forward.

Interpretation notes: criterion 3 (CVaR95 of excess cost) is implemented as CVaR95 of per-episode regret
against the hindsight best fixed model, arm over reference ratio <= 1.10; CVaR95 of the per-episode paired
dJ is reported alongside. The R3 tail threshold tau and the tail-only ablation are matched on label count
(nearest on even episodes).

## Advance criterion (verbatim from doc 15 section 3)

> **Advance criterion** (for any candidate, before held-out data are built):
> - lower paired mean J, with a 95% CI excluding 0, against **both** fair references;
> - ΔL/T ≤ +0.1 pp;
> - CVaR95 of the per-episode excess cost no worse than the reference by more than 10%;
> - no dataset with a paired mean worse than +1% of its J.
>
> Best-of-grid optimism is reported, and a candidate is chosen on even episodes and checked on odd episodes before any held-out data are built. A ≥ 2% gain is a goal, not a gate.
>
> **Stop rule:** if no arm meets the advance criterion, close this method search.

## Reproduce

```
PY=.venv/Scripts/python.exe   # OPENBLAS_NUM_THREADS=1 PYTHONIOENCODING=utf-8
python scripts/paper1_eqsdp/stage5_run.py A; python scripts/paper1_eqsdp/stage5_analysis.py A
python scripts/paper1_eqsdp/stage5_run.py B; python scripts/paper1_eqsdp/stage5_analysis.py B
python scripts/paper1_eqsdp/stage5_run.py C; python scripts/paper1_eqsdp/stage5_analysis.py C
python scripts/paper1_eqsdp/stage5_run.py D; python scripts/paper1_eqsdp/stage5_analysis.py D
python scripts/paper1_eqsdp/stage5_freeze.py
```
