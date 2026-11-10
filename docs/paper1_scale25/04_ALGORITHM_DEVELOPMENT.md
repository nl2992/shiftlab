# 04 — Algorithm development: v2 search against late adoption (Workstream B)

v1 (EQ+cut+E48+F60, `P2_K2__E48_F60`) is untouched. All v2 work is on development data only: the nine registered windows and the 7 fresh windows (development-exposed). No confirmation window was built or opened. Code: `scripts/paper1_scale25/algo/` (`s25_v2.py`, `s25_modules.py`, `v2_specs.py`, `v2_analysis.py`, `lsw_train.py`). Ledger: `docs/paper1_scale25/algo/V2_CANDIDATES.csv` (definitions) and `V2_LEDGER.csv` / `tables/v2_tune_even.csv` (every candidate's even-episode result) and `tables/v2_check_odd.csv` (odd check). Context numbers are in `06_ABLATIONS.md`.

## 1. Motivation from the headroom analysis
The oracle bounds (06 section 4) say the best-fixed-model reference is nearly the right yardstick: a hindsight single switch beats it materially only on nine kc. Late adoption is large (6 to 8% of J) only on dc and sf (nine) and austin and dc (fresh), and 1 to 3% elsewhere. v1's gain over its parent is about 0.4% of J. Budget is not binding (about 55 of 200 labels), so budget shadow prices and "more labels" have little to act on; doc 11 puts the value of doubling free labels at 0.23 to 0.32%.

## 2. Protocol
- Tune stage: even episodes of both pools (nine 375 ep, fresh 273 ep, 16 dataset-windows), policy seeds 0-2. Select by pooled equal-window mean J.
- Reference R*: the lowest pooled even-episode J among the reference set (25 panel comparators, 12 Wald lambda x gamma + cutoff 1100 configurations, EQ cutoff 900/1100/1300, EQ+cut, W+cut, EQ+pair, W+pair, arm R). **R* is EQ+pair itself (v1)**, J=23.4327. Candidates are therefore compared with v1, and by transitivity with every control. Unequipped arm R is not used as the yardstick.
- Selection: the best 5 by even dJ plus the best of each family (9 candidates in total) go to the odd check. Odd stage: odd episodes, seeds 0-9, same R*, paired stratified episode bootstrap. A per-window best reference chosen on even episodes (R*_w) is also reported; it is subject to winner's-curse selection noise, which is why even v1 shows -0.039 against it on odd episodes.
- Functional tests (`test_algo.py`, 69 pass): all-off identity (bitwise), budget <= 200 and no purchase after the cutoff for every module, and no future-label access (replacing the loss stream from t0 = 600 leaves deployments and requests before t0 unchanged) for UNI, UNC, retunes, hazard-adaptive, EAP, DPW, INS, LSW and F59.
- Training for learned components used even episodes only: LSW (ridge, 12 even episodes per dataset, 2 seeds, 20,015 release samples; in-sample MSE 0.0102 vs 0.0140 for the parent's posterior mean as predictor; the weight is mostly on the undiscounted label mean, `lsw_params.json`); F59 is the existing search60 module, trained on even episodes of the nine.

## 3. Candidates (35 run, all recorded)
A. Retunes of E48/F60 parameters (10): arrival discount .75/1.0, lookahead 25/100, hazard .001/.004 for E48; bundle 3, horizon 150, hazard .001/.004 for F60. Not a new mechanism; they calibrate how much the v1 settings leave on the table.
B. Hazard-adaptive modules (6): E48A, F60A and both, with the change hazard multiplied by exp(kappa z), z the recent-8 vs overall disagreement of released labels, kappa 1 or 2 (dynamic lookahead and bundle value).
C. Early adoption under the change-hazard posterior (EAP, 5): adopt the other model when the gamma2-quantile (.4/.5) payback over the hazard-discounted horizon exceeds mult x c_s (1.0/1.5), on the pair, and alone on EQ+cut.
D. One-step DP (DPW, 2): adopt iff posterior-mean payback net of c_s is positive and at least the value of waiting for the labels in flight.
E. Evidence-insurance floor (INS, 3): buy a disagreement if no label has been requested for 80/150/250 events (pacing guard and cutoff respected).
F. Learned switching (LSW, 7): ridge-predicted future challenger-correct rate, adopt when (advantage - 2 z sigma) x rate x horizon > mult x c_s; z in {0,.5,1}, mult in {1,1.5}; and alone on EQ+cut.
G. Learned acquisition controller F59 (tree, logistic) on the pair (2).
Not run: a budget shadow price candidate, because the budget is slack (about 55 of 200 labels, and the existing pacing multiplier is inactive in the typical episode); recorded as an untested, low-prior idea. A short-horizon rollout beyond the one-step DP (D) was not built. The tier-D synthetic/real dev streams were not used here.

## 4. Results
Even episodes (tuning), dJ vs R* = v1, pp of T (negative better), 16 windows, 95% CI:

| rank | candidate | family | dJ vs v1 | CI | windows improved | labels | switches |
|---|---|---|---|---|---|---|---|
| 1 | V2A_E48 hazard .001 | retune | -0.031 (-0.13%) | [-.061, +.003] | 11/16 | 46.6 | 1.131 |
| 2 | V2G_F59tree | learned acq. | -0.027 (-0.11%) | [-.053, -.001] | 11/16 | 48.8 | 1.163 |
| 3 | V2G_F59logit | learned acq. | -0.018 | [-.060, +.024] | 12/16 | 49.5 | 1.150 |
| 4 | V2A_F60 horizon 150 | retune | -0.014 | [-.063, +.024] | 8/16 | 64.0 | 1.184 |
| 5 | V2E_INS age 250 | insurance | -0.009 | [-.026, +.008] | 8/16 | 55.1 | 1.151 |
| ... | hazard-adaptive (6) | B | -0.001 to +0.027 | all include 0 | | | |
| | V2D_DPW (2) | D | +0.023, +0.054 | m1.0 excludes 0 (worse) | | | |
| | V2F_LSW (7) | F | +0.017 to +0.135 | most exclude 0 (worse) | | | 1.3 to 1.7 |
| | V2C_EAP (5) | C | +0.082 to +0.211 | all exclude 0 (worse) | | | 1.4 to 1.9 |

Early adoption and learned switching (C, D, F) raise switches from 1.15 to 1.4 to 1.9 per episode and are worse than v1 and, on the nine, than the parent: the extra false promotion and churn exceed the saved late adoption. This repeats the doc 15/17 pattern: changing the switching rule trades late adoption for false promotion at about the same rate as the tuned gamma already does. EAP alone and LSW alone (no E48/F60) are +0.18 and +0.14 against v1.

Odd episodes (select check), seeds 0-9, R* = v1 (J = 23.2327), dJ vs v1:

| candidate | dJ | 95% CI | % of J | nine | fresh | windows improved |
|---|---|---|---|---|---|---|
| V2G_F59logit | -0.0175 | [-.0415, +.0075] | -0.075% | -0.010 | -0.028 | 13/16 |
| V2G_F59tree | -0.0164 | [-.0352, +.0035] | -0.071% | -0.012 | -0.023 | 12/16 |
| V2A_E48 hazard .001 | -0.0128 | [-.0344, +.0093] | -0.055% | +0.000 | -0.030 | 11/16 |
| V2E_INS age 250 | -0.0027 | [-.0083, +.0017] | -0.011% | -0.003 | -0.002 | 6/16 |
| V2A_F60 horizon 150 | -0.0023 | [-.0207, +.0148] | -0.010% | -0.009 | +0.006 | 8/16 |
| V2B_E48A kappa 2 | +0.0045 | [-.0164, +.0265] | +0.020% | | | |
| V2D_DPW m1.5 | +0.0198 | [+.0048, +.0367] | +0.085% (worse) | | | |
| V2C_EAP g.4 m1.5 | +0.0602 | [+.0377, +.0831] | +0.26% (worse) | | | |
| V2F_LSW z1 m1.5 | +0.0676 | [+.0121, +.1508] | +0.29% (worse) | | | |
| EQ+cut (parent) | +0.1034 | [+.0589, +.1595] | +0.445% | | | |

## 5. Assessment
- **No v2 candidate beats the strongest development-selected reference (v1) on the odd check.** The best three are -0.07% to -0.08% of J with CIs that include 0, i.e. no better than noise at this size, and they are at most small refinements of the same two modules (F59 scaling of F60-type acquisition; a lower E48 hazard). Their even-episode gains (-0.11% to -0.13%) shrank by about 40 to 55% on the odd episodes, the usual selection shrinkage. F59 was trained on even episodes of the nine, so its nine-window odd result is the only clean out-of-sample reading and is -0.010 (not significant).
- **Mechanism contribution.** Candidates in C, D and F fail through false promotion and churn. Hazard-adaptation of E48/F60 (B) changes nothing detectable. Evidence insurance (E) changes labels but not cost. The identifiable mechanism contributions remain those of 06: E48 saves label fee (-0.067 pp), F60 reduces late adoption (-0.044 pp), and the two are additive.
- **Matched-baseline comparison.** Against label-matched uniform and uncertainty acquisition, v1 retains -0.05 to -0.07 pp (06). Nothing in v2 changes that figure.
- **Implication for the 2.5% target.** The largest v2 improvement over v1 that survives the odd check is below 0.1% of J. With the headroom ceilings in 06 (late adoption is the only large component, and only on dc, sf, austin) a 2.5% reduction against the strongest reference is not reachable by any mechanism examined here. Continue/pivot/stop assessment for this workstream: stop searching for further timing refinements of the existing acquisition/switching rule on these data; a materially different information source would be needed (for example a prediction-side early-warning signal usable before labels arrive), which is outside the label-only design and was not tested.

Limitations: seeds 0-2 for tuning, selection among 35 candidates on even episodes, and the odd episodes are now selection-exposed as well as development data. The reference set on the nine windows includes the 25 panel comparators as run by `sota_expansion`; none is source-faithful (see the baseline fidelity audit). Per-window references R*_w are optimistic for the references.
