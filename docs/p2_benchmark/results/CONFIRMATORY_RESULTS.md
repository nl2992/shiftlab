# P2 confirmatory results: H1–H7 (W4, 2026-11-07)

**Verdict.** All five directional tests (H1, H2, H4, H5, H6b) pass their registered Bonferroni 99%
rules, and the H3 equivalence rule passes. Among the descriptive results, H1b rises with horizon.
In H7 the leading policy changes between gates. However, the "two-tier" gate as Amendment 1
implemented it is Tier A alone, and it admitted every certified policy. H7 therefore does not show
that the two-tier rule discriminates.

Registration: [CONFIRMATORY_HYPOTHESES.md](../CONFIRMATORY_HYPOTHESES.md), commit `d89643b9`
(rules) plus Amendment 1 (`1564c122`, cohorts, H7 gates and the analysis script). The raw output is
in [confirmatory.json](confirmatory.json) and [confirmatory.md](confirmatory.md).

## Evidence class

These results are confirmatory **for the registered cohorts**: twin v3 splits 40–159 (new model
fits, never run before) and new synthetic seeds. The underlying five UCI-derived sources were
already used in development, and so were the synthetic regime parameters. This does not replace
the untouched-source confirmation (W5/W6). Empirical rates are not guarantees.

## Results against the registered rules

| ID | Rule | Result | Pass |
|---|---|---|---|
| H1 | Strict-pool pooled first-promotion rate on twin v3: 99% LB > .05 | **.098** [.091, .106] | Yes |
| H1b | Descriptive: rate at T = 1000/2000/4000 | **.073 → .098 → .104** | (rises) |
| H2 | Mean `adv_rest` at first promotion, strict pool: 99% LB > 0 | **.0152** [.0114, .0198], 3,644 promotions | Yes |
| H3 | 95% CI of π_EI(mean-reverting nulls) − π_EI(twin v3) inside ±.15, both in [.3, .7] | .530 vs .444; difference CI **[+.032, +.141]** | Yes |
| H4 | CAMS and Model Picker: per-dataset 99% LB on promotion > .5 | LBs: CAMS .755–.919, Model Picker .660–.894 | Yes |
| H5 | Pooled synthetic J(A5b) − J(QSG) over six dependent alternatives: 99% LB > 0 | **+50.3** [+47.0, +53.5] | Yes |
| H6 | A5b per dataset: 95% UB vs .0936 (report) | metro .007, beijing .028, appliances .071, household .031 meet it; **bike_hour .105 does not** | (report) |
| H6b | A5b on bike_hour: 99% LB > .05 | estimate .089, **LB .067** | Yes |
| H7 | Descriptive: certified leaderboard on fresh real data under two gates | Single gate admits **only `discern_style`** (J = 602.8, the highest of all 16). Tier A admits all 16; top is D2 (407.1), then QSG (410.0) | Top changes |

Intervals are stratified cluster-bootstrap percentiles (4,000 draws, seed 20261107). Clusters are
(dataset, split) for twins and seed for synthetic data. H1–H5 and H6b use 99% intervals; H3 uses
a 95% interval.

## How to read each result

- **H1/F1.** On real twins with an exact marginal null, the six published-certificate ports promote
  about twice the nominal α. The confirmatory rate (.098) is below the development figure
  (.141). That figure used the wider V1-certified pool on v2 splits, so the two are not like for
  like.
- **H2/F2.** Those promotions are conditionally informed: at the moment of promotion, the challenger
  is on average ahead over the remaining events. The rate is therefore not noise-chasing, but it
  breaks the marginal null as stated.
- **H3/F3.** The registered equivalence passes, but the interval excludes zero. Mean-reverting
  synthetic nulls yield about 9 points more EI-appropriate promotions than real twins. Read it as
  "within ±.15, near one half under both", not "identical".
- **H4/F4.** Uncertified selectors promote on most real-null episodes on every dataset.
- **H5/F5.** On synthetic dependent alternatives, robustness to dependence (A5b) costs about 50 units
  of J per episode compared with QSG. That is ten switch costs. The development figure (+118.5)
  came from a different cohort, real realised-better episodes, and is not comparable.
- **H6/F7.** With 120 splits, A5b's bike_hour excess over α is a real failure (LB .067 > .05), not
  design noise. Its point estimate (.089) is still below .0936. The failure is a moderate excess
  over the nominal level on one dataset, not a collapse. The other four datasets meet the bound.
- **H7/F8.** The single all-null gate is so strict that it admits only the most conservative and most
  expensive certificate. **Caveat:** the Amendment 1 "two-tier" gate checks Tier A only, on the
  claimed nulls. Every certified policy passes Tier A on the iid null (F0_null rates .000–.030),
  so that gate admits all 16. The finding supported here is "the all-null gate is
  degenerate". The claim "the two-tier rule picks the right subset" is not supported. Tier B
  (dependent-null economics) must be part of the gate before the reordering can be claimed.

### Post-hoc (not registered): why the single gate rejects 15 of 16

Highest promotion rate on any synthetic null and on any twin v3 dataset:

| Policy | Claims | F0_null | Max synthetic null | Max twin |
|---|---|---:|---:|---:|
| discern_style | V1 | .000 | .005 | .004 |
| gated_deployment | V1 | .000 | .050 | .161 (appliances) |
| discern_design_floor | V1 | .005 | .180 | .136 (appliances) |
| gated_adaptive_range | V1 | .000 | .140 | .210 (appliances) |
| SMCS+retain-incumbent | V1 | .025 | .390 | .321 (appliances) |
| A5b | V2 | .020 | .420 (WP2_hs_null) | .089 (bike_hour) |
| D2 | V1 | .030 | .585 | .439 (appliances) |
| QSG | V1 | .020 | .710 | .531 (appliances) |

The remaining eight rows (front-loaded, QCE, Choe–Ramdas, Xu, RMM variants) fall between
.265 and .670 on their worst null. Appliances is the hardest real twin for every V1 method. Even A5b,
the V2 method, fails the single gate, on bike_hour and on the semi-Markov `WP2_hs_null`, which lies
outside its claimed class.

## Deviations and checks

1. **Code version.** All five run directories record git `35bab34b`. The registered analysis and
   runner are at `1564c122`; `35bab34b` changes only `docs/p2_benchmark/COMPARATOR_FIDELITY.md`
   (verified with `git diff --stat`). This is not a code change.
2. **Manifest field `unknown_policies`.** It lists panel names resolved outside the runner's
   extras table. All 25 policies are present with equal counts in every run (checked).
3. **Analysis code unchanged.** It was run exactly as committed (SHA-256 `e018af00…`), with the
   default `N_BOOT=4000` and `--expect-splits 120`.
4. The post-hoc table above was computed after the registered analysis and is labelled as such.

## Provenance

| Run | Records | SHA-256 of `records.jsonl` |
|---|---:|---|
| twin (panel P, 7,440 episodes) | 186,000 | `d717821a753cdaf5c4367738b2780b8f74436b5a404bdcfe21424d039ea792f7` |
| twin_T1000 (strict + control) | 104,160 | `185abb12381d2b667907b3abc3d1e230b5be5433abe7239c5a756f79d192d47e` |
| twin_T4000 (strict + control) | 26,040 | `37b84fb8cd302df420fe4dcd192fb09ba27d6df30c16d3b4bcd8d374febc0a62` |
| synth (14 regimes × 200 seeds) | 70,000 | `a029671a59460c004e9f26299c89b8be616fcf37952d9a30af2d5e7450614b4a` |
| fresh (5 sources, 3 seeds) | 4,650 | `4d9853f230ba296f7870316c95b380f38b8cb99d2b1e49a7002315d183eecb1f` |

Twin v3 array content hashes and stream statistics are in [twin_v3_stats.json](twin_v3_stats.json).
The v2 rebuild matched its recorded hashes before v3 was built. The UCI archives match the SHA-256
values in `data/sprint_fresh_losses/stats.json`. Environment: Python 3.12 venv, numpy 2.5.4,
pandas 3.0.6. Runs are under `outputs/p2_benchmark/confirmatory/` (not in Git).

Reproduce the analysis:

```bash
D=outputs/p2_benchmark/confirmatory
PYTHONPATH=scripts/promising_directions/sota .venv/bin/python scripts/p2_benchmark/analyze_confirmatory.py \
  --twin $D/twin --twin-t1000 $D/twin_T1000 --twin-t4000 $D/twin_T4000 --synth $D/synth --fresh $D/fresh \
  --out docs/p2_benchmark/results/confirmatory
```

## Assessment

- **Continue:** F1, F2, F4, F5 and F7 are now confirmatory on twin v3, and F3 passes its
  equivalence rule. These five findings can carry the benchmark's evaluation section. The next
  risk is generality, which requires untouched sources (W5/W6).
- **Pivot (F8):** restate it as "the single all-null gate is degenerate: it admits only the most
  expensive certificate". Before claiming that the two-tier rule is better, register a gate that
  includes Tier B economics, and test it on a fresh cohort.
- **Limitations:** five exposed UCI-derived sources. Imposed label delays. EI is a hold-to-end proxy
  that excludes label cost. Gated-deployment ports are conservative relative to native MOPE
  ([COMPARATOR_FIDELITY.md](../COMPARATOR_FIDELITY.md)). The Choe–Ramdas stand-in is more aggressive
  than the authors' e-process.
