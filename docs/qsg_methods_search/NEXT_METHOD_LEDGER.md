# Next-method candidate ledger (authoritative)

Contract for every row: 14-regime family (10 change + 4 guard), T=2000, B=200, c_q=.05, c_s=5,
delay 100, paced disagreement-only acquisition unless stated. Development seeds: base
2026110901, 40 seeds (in-sample selection; the comparator is selected in-sample too). Metric:
family-mean net cost per episode (lower is better). Primary comparator: **best widened-grid
fixed-discount Wald-LCB on the same seeds = `wald_l0.85_g0.15`, 354.69** (change 346.82, guard
374.34). EQSDp-B on the same seeds: 355.06 (+0.38 [−0.21, +0.97]); so the historical tie
replicates. Code: `scripts/qsg_methods_search/next_method.py`; analysis
`analyze_nm.py`; raw records `outputs/qsg_methods_search/nm_dev*/` (gitignored).

| ID | Target failure | Design | Best config (in-sample) | Δ family vs tuned Wald (95% CI) | Δ change / Δ guard | Ablation / diagnosis | Novelty | Decision |
|---|---|---|---|---|---|---|---|---|
| A3 multi-timescale (`ms_`) | M2/M3 memory trade-off | fast/slow counts, use fast when an inconsistency test fires | `ms_f0.85_s0.95_z1.5_g0.3` 357.88 | **+3.20 [+2.18, +4.22]** | +5.22 / −1.86 | slow memory buys guard (−1.9) but the test fires late, losing 5 on change | known (multi-scale monitoring) | **STOP** |
| A1 two-state restart (`rs_`) | same | slow counts replaced by fast counts on inconsistency | `rs_f0.8_s0.95_z1.5_g0.3` 357.34 | **+2.66 [+1.61, +3.71]** | +4.35 / −1.59 | same mechanism as A3 | known (restart-on-detection) | **STOP** |
| A4 leader over discounts (`ld_`) | same | follow-the-leader over λ∈{.8,.9,.95,.98} by discounted predictive log-lik | `ld_e0.95_g0.15` 355.88 | +1.19 [+0.37, +2.01] | +1.40 / +0.68 | predictive score selects short memory most of the time | known (forgetting-factor selection) | **STOP** |
| B1 asymmetric hysteresis (`asym_`) | M2 rollback churn | separate Wald levels for promotion and rollback | `asym_l0.93_p0.2_r0.3` 355.97 | +1.29 [+0.55, +2.03] | +2.77 / −2.42 | asymmetry trades guard for change; no net gain at any of 18 configs | known (asymmetric thresholds) | **STOP** |
| A5 BOCPD mixture (`bocpd_`) | M3 adaptive memory | run-length posterior, moment-matched quantile | `bocpd_h0.02_g0.2` 354.81 | +0.12 [−0.81, +1.05] (tie) | +2.37 / −5.49 | wide mixture after a change delays switching; wins guard | known (Adams–MacKay) | **STOP** (tie) |
| A5b BOCPD MAP segment (`bmap_`) | same | Wald on MAP run-length segment | `bmap_h0.01_g0.15` 364.34 | +9.6 | +17.3 / −9.6 | MAP segment flips to short runs on noise; Wald overconfident at small n | known | **STOP** |
| A6 GLR change-point-cut window (`glr_`) | same | cut window at maximising GLR split, Wald on post-cut labels | `glr_c6.0_l0.97_g0.2` 357.99 | +3.30 | +7.43 / −7.01 | false cuts → windows of 3–10 labels → 7–11 switches/episode at c≤4 | closest prior GLR-klUCB (Besson et al. 2022), see NEXT_METHOD_NOVELTY_lit.md | **STOP** |
| D1 decision-ambiguity acquisition (`amb_`) | M1/M3 information timing | query every disagreement while the point estimate favours switching but the Wald bound does not pay back; otherwise pacer × ρ | `amb_l0.9_g0.15_m0.0_r1.0` 353.94 | −0.75 [−1.66, +0.17] (n.s.; best of 36) | +1.17 / −5.53 | bursts help nulls/late onsets, hurt recurrent/transient (budget borrowed from later) | prior: D2 decision-at-stake clause (−0.9 n.s.), GAVE-R | **STOP** (tie) |

## Diagnostic: how much could adaptive memory gain? (evaluator-side, not a method)

`OracleRestart` resets the Wald counts at the first released label past each *true* change time
(it reads evaluator-side regime truth; it is a ceiling, never a candidate). On the 10 change
regimes, best oracle (λ=1, γ=.3) 335.14 vs tuned Wald 346.82: **11.7 units**. On the guard
regimes the oracle degenerates to long memory (λ≥.97: guard 362–364 vs 374). So the
adaptive-memory ceiling is ≈11 units/episode (≈26% of tuned Wald's expected-oracle regret of 42).

**Finding.** None of six online adaptive-memory designs gets any of that ceiling. Each one that
helps guard loses at least as much on change. Change of size |Δp|≈.3–.4 needs ≈10–12
disagreement labels to detect (Bernoulli KL≈.25/label), i.e. ≈100–120 events at the paced rate,
plus the 100-event label delay. The tuned λ=.85 memory (n_eff≈6.7) already reacts on that
timescale. The bottleneck is information arrival, not memory form. This motivates Candidate D
(when to buy labels) rather than further memory designs.

## Regime-weight-free check: the fixed-discount Wald Pareto frontier

The equal 10-change/4-guard weighting is arbitrary, so every candidate config was compared with
the lower envelope of the 27 fixed-discount Wald configs in the (change cost, guard cost)
plane, for every weight w∈[0,1] on change. The largest gain over the envelope by **any** of
≈150 candidate configs at its most favourable weight is **1.05 units**
(`amb_l0.9_g0.15_m0.0_r1.0`, w=.65), then 0.99 (`bocpd_h0.01_g0.1`, w=.25). Both are the best
of many configs on in-sample seeds, so they are within selection noise. **Conclusion: on this
contract, fixed-discount Wald-LCB payback switching is (to within ≈1 unit) Pareto-efficient
against adaptive memory, change-point windows, asymmetric hurdles and evidence-triggered
acquisition.** That is itself a C1/C2 finding: label-only evidence processing is saturated, so
gains must come from information the label stream does not carry.

## Next candidate: label-free sentinels (Candidate S, `sgr_`)

The oracle ceiling shows change *timing* is worth ≈11.7 units. The only cost-free source of
timing information in this contract is prediction-only: the disagreement indicator on every
event. Candidate S uses a label-free disagreement-rate sentinel to (i) reset the evidence
memory and (ii) burst label acquisition; the switch itself remains a label-evidence Wald
payback decision (an alarm alone never switches; cf. charter: shift alarms do not establish
harm). Evaluated on a new S-family (registered in `next_method.py` before any S run): 5
coupled regimes (performance change coincides with a disagreement-rate change), 3 false-alarm
regimes (rate change, no performance change), 2 silent regimes (performance change, no rate
change), plus the original 14 regimes to measure harm when the sentinel is uninformative.

## Stage 5–7 results (development seeds 2026110901, 40 seeds)

| ID | Target failure | Design | Family / comparator | Best config (in-sample) | Δ (95% CI) | Diagnosis | Decision |
|---|---|---|---|---|---|---|---|
| S sentinel-gated reset (`sgr_`) | M3 detection latency | label-free disagreement-rate sentinel resets evidence and bursts labels; switch stays label-based | S-family (10 regimes) vs Wald re-tuned on S (`wald_l0.9_g0.2`) | `sgr_l0.9_g0.15_W150_z2.5_L20` | −1.18 [−2.99, +0.63]; vs old-14-tuned Wald −1.92 [−3.76, −0.08]; on the original 14 regimes +1.20 [+0.36, +2.05] | a .2→.3 rate shift needs ≈100–150 events to detect, no faster than the labels; false alarms cost on S6–S8 | **STOP** (weak, harms uninformative family) |
| E dependence-adjusted Wald (`dep_`) | **M4** serial dependence | Wald s.e. × sqrt((1+r)/(1−r)), r = discounted lag-1 autocorrelation of released outcomes; r≡0 is plain Wald | 20 regimes (14 + 6 dependence) | `dep_l0.9_g0.15_lr0.99_rp5.0` | vs best Wald on the mixed 20: −0.81 [−1.62, +0.01]; vs old-tuned Wald on dependence regimes −12.2 [−14.9, −9.5]; vs dependence-tuned Wald (λ=.97) +3.3 on dependence, −8.9 on independent | sits ≈1.6 units inside the Wald frontier at best; minimax class regret 5.7 vs 7.25 for best fixed Wald | **REVISE → feeds G** (small but real; strongest real-data relevance, see below) |
| F Bayes-filter payback (`bpay_`) | rule headroom (Bayes-myopic benchmark) | BOCPD posterior with hazard-aware payback horizon H_eff=(1−(1−h)^(T−t))/h | original 14 | `bpay_h0.002_g0.2` 355.03 | +0.35 [−0.68, +1.38] | risk-neutral Bayes (γ=.5) is far worse (372–381): the confidence bound substitutes for the value of waiting and of avoiding switch-back | **STOP** (tie); benchmark says the rule has little headroom |

## Real-stream development (14 EXPOSED streams; counts for nothing)

`nm_real_dev.py` (C4-0 driver, checksums verified), seed base 2026110961, 5 policy seeds per
episode, 230 episodes. Analysis `analyze_nm_real.py`; output `outputs/qsg_methods_search/nm_real_dev_analysis.txt`.

- **Memory transfer failure.** Best fixed Wald on real streams is long memory, `wald_l0.97_g0.2`
  (stream-equal pooled 403.56). The synthetic-tuned short-memory configs are 6–9 units worse:
  `wald_l0.85_g0.15` +9.11 [+3.58, +17.12], frozen C4 arm `EQSDp_l0.9_g0.2` +6.03
  [+2.27, +10.55] (0 of 10 streams with ≥5 episodes better). Conversely `wald_l0.97_g0.2` is
  +8.8 on the synthetic family. No fixed (λ, γ) is good in both domains.
- **Real outcomes are serially dependent.** Lag-1 autocorrelation of disagreement outcomes is
  .3–.95 on 9 of 14 streams (uci_occupancy .95, appliances .70, household_power .62, beijing_pm25
  .61, openml_ldpa .45); the synthetic ρ=.8 family gives ≈.1 at label spacing.
- DepWald at λ=.9 halves the short-memory deficit (+4.49 → +2.32; ablation r≡0), but stays
  behind long-memory Wald.
- Change-adaptive memories are worst on real streams (BOCPD +8.7 to +10.4, sentinel +9.7 to +13.4):
  serial dependence looks like change to them.
- The existing C4 claim (arm B vs tuned Gong–Zhang-style) still holds descriptively on these
  exposed streams: B 409.6 vs gongT 415.3.

**New Atlas mechanism (M5, hyperparameter-transfer failure).** The evidence memory that is
optimal on change-heavy streams is badly wrong on dependent, mostly stationary streams, and vice
versa. This is not fixable by a better change detector (dependence fools detectors), and it is
what Candidate G targets: select among shadow switchers by their **IPW-estimated realised
economic cost**, which is exactly measurable online because acquisition is decision-independent.

## SAES pivot (2026-11-08)

| ID | Target failure | Design | Evidence | Decision |
|---|---|---|---|---|
| SAES-proxy | information limit (M1/M3) | unlabeled confidence-gap proxy as extra evidence on every disagreement (prediction-powered style) | cross-fitted ρ² .00–.11 on 11 dev streams → ≤1.13× labels; +100% labels worth 5.3 units → bound ≤0.7 | **STOP** (Phase 1) |
| SAES-staleness | information limit, M5 | drift / disagreement-rate / score-gap triggered acquisition or reset | pooled \|r\| ≤ .08 with the future advantage change; inconsistent signs | **STOP** (Phase 1) |

Details: [SAES_PHASE1.md](SAES_PHASE1.md).
