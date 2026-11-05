# Family H diagnosis: why D5 (D2 + A1 evidence) lost power

Development diagnostics only (seed base 2026110701, 20 seeds per regime). Not validation.

## Reproduce
```
uv run python scripts/sota_sprint/screen.py --regimes F0_better,F9_bursty_better,F7_near_better,F1_late_800,F5_dep_better_r8,S_dep_better_r95,F0_null,F5_dep_null_r8 \
  --policies D2,D5,A5b --seeds 20 --seed-base 2026110701 --workers 2 --out outputs/sprint2/H/diag_base
uv run python scripts/sota_sprint/fam_h.py diagnose --regimes F0_better,F9_bursty_better,F7_near_better,F1_late_800,F5_dep_better_r8,S_dep_better_r95,F0_null,F5_dep_null_r8,F5_dep_null_r95 \
  --policies Hchk:D2,Hchk:D5,H1-twocycle,H1,H2,H2-iid_space --seeds 20 --out outputs/sprint2/H/diagnosis.json
```
`Hchk:D2` and `Hchk:D5` are `fam_h.HGate` re-implementations. They reproduce D2 and D5
episode for episode: net cost and deployment path are identical (unit test
`test_exact_reimplementation_of_d2_d5`). `diagnose` traces every request: host draw or gate draw,
whether the test is open, and the host's preference. It also traces every evidence update.

The offline evidence-efficiency check is a scratch script whose numbers are quoted below. It uses
synthetic Bernoulli/Markov sequences observed at a fixed event gap, 40 repetitions each. It asks:
how often does each evidence process reach e >= 40 (D2/D5 cycle-1 threshold) within 200 outcomes?

## Re-measured baseline (new seeds)
On base 2026110701 the D5 loss is smaller on iid alternatives than in sprint 1 (base 2026110501).
fam_a.py also changed after the sprint-1 D5 run.

| regime | D2 promote / net | D5 promote / net | A5b promote / net |
|---|---|---|---|
| F0_better | .90 / 356.0 | .85 / 366.6 | .85 / 366.6 |
| F9_bursty_better | .95 / 359.6 | .70 / 391.7 | .75 / 382.8 |
| F7_near_better | .50 / 383.5 | .30 / 391.5 | .30 / 393.1 |
| F1_late_800 | .55 / 384.0 | .55 / 383.0 | .10 / 398.9 |
| F5_dep_better_r8 | .95 / 349.3 | .20 / 417.1 | .30 / 417.0 |
| S_dep_better_r95 | .95 / 344.3 | .00 / 426.8 | .00 / 421.7 |
| F5_dep_null_r8 | .15 | .00 | .00 |
| F5_dep_null_r95 (diagnose run) | .70 | .00 | — |

## Measured causes

**C1. The price of the free-rho composite null (inference).**
- Offline, on iid outcomes with p=.65, SUI needs about 1.5x the outcomes of the iid mixture to
  reach e >= 40. Median outcomes to cross:
  - gap 5: iid 84, SUI default 136, SUI `_B` 128.
  - gap 20: 89, 140, 132.
- At p=.58 within 200 outcomes, P(cross) is .20-.23 for iid and .03-.12 for SUI.
- In episodes, D5 and H1-twocycle consume more evidence than D2 before deciding. Mean outcomes:
  - F0_better: 103 / 99 vs 82.
  - F9: 139 / 130 vs 75.
  - F7: 181 / 168 vs 154.
- Because evidence costs more, the same budget ends with fewer crossings.
- The A5b prior `_B` recovers only a little: on F9, promotion goes from .70 (D5) to .80
  (H1-twocycle).

**C2. Alpha left unspent on a second cycle that cannot occur (threshold).**
- D2 and D5 have no rollback, so promotion is absorbing and only cycle 1 ever runs. DeployGate
  still uses the cycle-1 threshold 2/alpha = 40. Ville gives P(ever cross 1/alpha) <= alpha, so
  1/alpha = 20 is valid when there is only one cycle.
- Offline on D2's own evidence streams, the share of episodes where SUI `_B` would cross is:
  - F0_better: .05 at 40 vs .35 at 20.
  - F7: .05 vs .40.
  - F9: .00 vs .20.
- In episodes, H1 (`_B` + 1/alpha) recovers relative to D5:
  - F9: .95 vs .70 promotion.
  - F7: .50 vs .30.
  - F1_late_800: .65 vs .55.
  - F0_better: .90 vs .85.
  - Every iid alternative reaches D2's promotion rate.
- H1 keeps D5's null behaviour: 0/20 on F0_null, F5 r8 and F5 r95.

**C3. Bursty and front-loaded acquisition puts the evidence at the smallest gaps (acquisition).**
- With gate front-loading (q=1 on every disagreement while the host prefers the challenger), the
  median event gap between outcomes is about 4-5 on iid regimes and 1.0 on F9_bursty.
- At small gaps the null cells with large rho^g explain runs of hits at little cost. C1 is
  therefore largest on F9: D5 used 139 outcomes against D2's 75.
- On Markov alternatives the front-loaded gap makes the true lag correlation large:
  rho^gap = .41 on F5 r8 and .80 on S r95.
- Offline (Markov alternative, p=.65, rho=.8), P(SUI crosses within 200) depends on the gap:
  - gap 5: .07-.10.
  - gap 20: .60-.62.
- A5b spacing (H2) raises the median gap on F5 r8 from 4 to 11 and lowers rho^gap from .41 to .12.
  It also cuts labels from 190 to 156. It does **not** raise promotion within T=2000 (.20 vs .20):
  - At gap g*, the event horizon caps the number of outcomes.
  - Effective sample size is about T(1-rho)/(1+rho), roughly 222 events for rho=.8 and 51 for
    rho=.95.
  - Crossing at p=.65 needs about log(20)/KL(.65||.5), roughly 68 effective outcomes, before the
    composite price.

**C4. Evidence-information trade-off on the tested strongly persistent alternative.**
- On S_dep_better_r95, every SUI variant ends with log e_up max of about 0. Promotion is .00 for
  D5 and H1, and .05 for H2.
- D2's .95 promotion there comes from the same mechanism that gives it .70 promotion on
  F5_dep_null_r95 and .15 on F5_dep_null_r8. The iid mixture reads a long winning run as evidence.
- In this construction, a long winning run is compatible with high persistence under the free-rho
  null; the tested SUI variants therefore accumulate little evidence. The S r95 trajectory has
  about 20 effective sign changes in T=2000. This is a mechanism-level interpretation of the tested
  process and implementations, not a general characterization of every valid Markov e-process.
- The finite-horizon results show that the tested SUI variants did not recover D2's promotion rate
  on S_dep_better_r95. They do not prove that every method valid for the stationary-Markov null
  must have low power there.
- H2-iid_space (spacing with iid evidence) promotes .80 on F5 r8 and .75 on S r95. It also
  promotes .15 on the F5 r8 null and .50 on the r95 null, so spacing alone does not repair iid
  evidence.

**C5. The host spends the budget (acquisition, secondary).**
- 55-65% of open-test labels are CAMS's own draws. Examples: F0_better 58.5 of 99.6, and F0_null
  140.7 of 200.
- Between 14 (F0_better) and 111 (F1_late_800) labels are spent while CAMS prefers the incumbent.
  The gate adds nothing then, but the host keeps drawing.
- The budget is exhausted before T on the nulls: D2/D5 exhaust_t is about 1413 on F0_null and
  about 1200 for D5 on S r95.
- Under D2 the iid certificate crosses before this matters. Under SUI, which needs 1.3-1.8x more
  evidence, it binds on F7 and F1, where the budget runs out with the test still open.
- The C2 shadow price (H3) and the monitoring reserve (H6) target this.

**C6. When gate queries happen.**
- The gate front-loads only while CAMS ranks the challenger first. Crossing and promotion
  coincide on every traced episode, so host agreement is not binding.
- The gate's share of the labels is 41-50% on iid alternatives.
- On F1_late_800, D2 spends 28.9 labels after a discard verdict against D5's 10.8. These are
  wasted on host draws, because the host keeps querying after the gate stops.

## Consequences for the H configurations
- **H1** targets C1 + C2: `_B` evidence plus the single-cycle threshold 1/alpha.
- **H2** targets C3: spacing on host and gate draws. Ablations: H2-iid_space (acquisition only),
  H1 (inference only), H2-gateonly.
- **H3** targets C5 with the shadow price on open-test draws.
- **H4** targets delay: in-flight awareness, a release-time deadline, and event-order segments.
- **H5/H6** target reversals and monitoring.
- The reversal test needed a further change, found while unit-testing H5. fam_a's started-mixture
  weights 1/(m(m+1)) made late starts so expensive that H5 never rolled back on F3 in 6/6 test
  seeds. H5 therefore uses `UniformStartSUI`: at most ceil(B/10) starts with equal weight, which
  remains a valid mixture. `H5-decay` keeps the fam_a weights as an ablation.
- C4 is a tested evidence-information trade-off, not an impossibility result. The screened H
  candidates did not recover D2's persistent-alternative promotion rate while retaining their
  tested null behavior; no statement about all V2-valid methods is made.
