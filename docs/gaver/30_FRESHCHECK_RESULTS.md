# GAVE-R WP3: FreshCheck screening results

Date 2026-11-06, branch `research/gave-r-2026-11-06`. Development/screening only: seeds
101120000-101159999 (WP3 block of `gaver_screening_development`), no confirmation seeds. Every
number below comes from `outputs/gaver/wp3/records.jsonl` (gitignored; regenerate with the commands
at the end). Code commit: `2a8b695b`; follow-up (E_rb, two-phase) commit `5521a269`.

## Verdict (screening)

**Fail on value, pass on null safety. Do not carry FreshCheck into WP5 as a value-adding component.**

- Against the existing rollback controllers FreshCheck gets *worse* post-reversal harm, not better:
  0.0527 /T vs 0.0094 (existing Page-CUSUM), 0.0260 (existing hysteresis), 0.0429 (cost-threshold rule).
  Against promotion-only harm falls by 79% (95% CI 71-88%), which is expected for any rollback.
- Persistent-case value lost vs promotion-only is 17.7% of J/T with the 20% reserve (substantial) and
  about 5% without the reserve (Table A: 0.418 vs 0.397). Most of the reserve's cost is slower promotion.
- Null safety passes: false promotion in 1000 boundary-null streams, pooled upper bound 0.017 (<= 0.1).
  False rollback at the keep-null boundary is 2/584 promoted streams (upper 0.012).
- What FreshCheck does uniquely deliver is a rollback that is level-controlled at the boundary
  keep-null while the heuristics are not (Table H). That is a safety property, not a cost gain: on
  equal-weight mean J/T over the three alternatives the ranking is cost-threshold 0.471, hysteresis
  0.472, reuse_noreserve 0.476, CUSUM 0.488, fresh_noreserve 0.489, fresh_reserve 0.496,
  promotion-only 0.530 (Table A).
- Continue/pivot/stop: **stop** FreshCheck-as-benefit; **keep** it only as an optional validity
  wrapper if a later claim needs a certified rollback. A cheaper next step would be a level-valid
  version of the cost-threshold rule, not more tuning of this one.

**Follow-up (E_rb and two-phase added): the verdict is unchanged.** E_rb behaves like FreshCheck
without the reserve (same J/T and harm to within noise); two-phase avoids reversal harm only by almost
never promoting and loses 17.8% on persistent value. See "Ported comparators".

## Build

`src/shiftlab/gaver/freshcheck.py` (subclass of `ComposedMethod`; no existing module edited).

- Promotion unchanged: started-mixture bounded-betting e-process on `-D - h`, episode j at level
  `alpha * 2^-(j+1)` (as in the repo; `alpha` itself when there is no rollback).
- At promotion that wealth is retired (the object is dropped in mode `fresh`; a test checks this).
- Fresh post-switch process: new started-mixture bounded-betting e-process, wealth 1, fed `D + h` from
  *released* labels whose *event round* is >= the promotion round. Null `H_keep`: challenger still better
  by the hurdle, `E[-D | F] >= h`. Alarm at level `alpha_rb * 2^-(k+1)` for the k-th promotion
  (`alpha_rb = 0.1`, so family-wise false rollback <= 0.1 across all episodes). Rollback = alarm AND
  economic gate `(T-t+1) * mean(last m post D) > s` (the gate can only reduce false rollbacks).
- Reserve: `R = round(0.2 B)` labels the pre-promotion phase cannot spend; the deployed phase spends all
  remaining budget. Acquisition is credit pacing of the spendable budget over the remaining rounds
  (hard cap `B`, `t + d <= T` as in the harness).
- Validity argument (what is claimed): given a predictable query rule, released-label filtration,
  and the conditional null, `1 + lambda (D+h)/(1+h)` is a nonnegative supermartingale factor for
  `|D+h| <= 1+h`, so the mixture is an e-process and Ville gives the level. The promotion and rollback
  alphas are separate budgets for separate nulls; nothing is reused across the two. **Not claimed:** any
  guarantee under serially dependent D (the harness map's discrepancy 2 applies unchanged), nor that the
  econ-gated decision is optimal. The simulations here are iid within regime, so they test the level
  under the null the argument covers, not robustness.

## Design

- Streams (`Wp3Cell`, T=1000, B=100, s=0.1, c=0.01, h=0.1, alpha=0.1, d in {1, 10}): 3-state path,
  P(Y=1) = 0.5 neutral, 0.9 challenger better (D = -0.8), 0.1 harmful (D = +0.8). Onset 0.2T (early) or
  0.5T (late) with +-0.05T jitter. **persistent**: better from onset to end. **reversal**: better for 0.25T,
  then harmful. **transient**: better for 0.1T, then neutral. 12 cells x 60 paired seeds. These are my own
  generators (the repository's rollback scripts are exact-game LP certificates, not stream generators).
- Null/safety studies, 500 streams per cell: boundary null (P(Y=1)=0.55, `E[-D] = h`, d in {1,10});
  persistent early/late x d (false rollback); **keep-null**: better window 0.25T then benefit exactly `h`
  (P=0.55), d in {1,10}.
- Comparators: `existing_promo_only`, `existing_cusum` (repo default spec: uniform calendar, Page-CUSUM
  kappa=2, per-episode alpha spending; this stands in for the non-existent `E_rb`), `existing_hysteresis`
  (repo `hysteresis`, k=2), and, on the same pacing as FreshCheck, `paced_promo_only`, `paced_cusum`,
  `paced_cost_threshold` (roll back when remaining horizon x recent mean loss exceeds `s`).
  The follow-up (section "Ported comparators" below) adds `erb`, `erb_a05` (E_rb from
  `origin/codex/sprint2-leaderboards@297a706e`) and `two_phase` (`persistence_promotion.py`). My first
  search missed them because they are not in the rollback/reversal scripts.
- Ablations: `reuse_*` keeps feeding the promotion process with post-switch labels and rolls back when
  its wealth falls below 1 (a heuristic, not a level-alpha test); `*_noreserve` vs `*_reserve`;
  `cusum_reserve` isolates the reserve from the evidence; `fresh_reserve_a20` is a sensitivity run
  (`alpha_rb = 0.2`).
- Metrics are evaluator-side: J/T = loss + c N_q + s N_s over T; components; post-reversal harm =
  sum of realised D over deployed rounds from window end until the first rollback, divided by T;
  rollback delay (rounds, censored at T); false promotion = any promotion while `E[-D] <= h`; false
  rollback = any rollback while `E[-D] >= h`.
- Statistics: paired percentile bootstrap (2000 resamples over seeds, pooled over the four cells of a
  kind), Clopper-Pearson two-sided 95% intervals. Gain = mean(comparator - first-named); relative =
  gain / comparator mean. Grades: substantial >= 10% with CI excluding 0, meaningful 3-10%
  CI excluding 0, small 1-3%, negligible < 1%.

## Results

All numbers are generated by `scripts/gaver/run_freshcheck_analyze.py` (`outputs/gaver/wp3/tables.md`,
`contrasts.csv` per cell and per kind, `rates.csv`).

### Table A. Mean J/T by kind (pooled onset x d: 4 cells x 60 seeds)

| method | persistent | reversal | transient |
|---|---|---|---|
| existing_promo_only | 0.397 | 0.651 | 0.541 |
| existing_cusum | 0.507 | 0.417 | 0.541 |
| existing_hysteresis | 0.436 | 0.439 | 0.541 |
| paced_promo_only | 0.397 | 0.656 | 0.542 |
| paced_cusum | 0.511 | 0.420 | 0.541 |
| cusum_reserve | 0.561 | 0.432 | 0.541 |
| paced_cost_threshold | 0.418 | 0.453 | 0.541 |
| fresh_reserve | 0.467 | 0.480 | 0.541 |
| fresh_noreserve | 0.418 | 0.508 | 0.542 |
| reuse_reserve | 0.467 | 0.455 | 0.541 |
| reuse_noreserve | 0.418 | 0.467 | 0.542 |
| fresh_reserve_a20 | 0.467 | 0.475 | 0.541 |

Transient cells are uninformative (all methods within 0.1%; the better window is too short to
promote reliably, so little is at stake).

### Table B (excerpt). Reversal components, mean per stream

Components for all kinds are in `tables.md`. Switch cost (<= 0.0002/T) and query cost (~0.001/T) are
negligible; the differences are loss. Persistent loss: promo-only 0.396, CUSUM 0.506, fresh_reserve
0.466. In the persistent cells FreshCheck made 0.98 switches per stream (no rollbacks); CUSUM 1.90.

| method | loss/T | switches | queries | post-reversal harm/T | rollback delay | still deployed at window end |
|---|---|---|---|---|---|---|
| existing_promo_only | 0.650 | 0.81 | 100 | 0.2542 | 318 (censored 80%) | 0.80 |
| existing_cusum | 0.416 | 1.43 | 100 | 0.0094 | 11.8 | 0.61 |
| existing_hysteresis | 0.438 | 1.27 | 100 | 0.0260 | 32.6 | 0.60 |
| paced_cusum | 0.419 | 1.37 | 100 | 0.0101 | 12.7 | 0.62 |
| cusum_reserve | 0.431 | 0.96 | 80 | 0.0054 | 6.9 | 0.42 |
| paced_cost_threshold | 0.452 | 1.37 | 100 | 0.0429 | 53.8 | 0.66 |
| fresh_reserve | 0.480 | 0.96 | 80.8 | 0.0527 | 66.2 | 0.46 |
| fresh_noreserve | 0.507 | 1.32 | 100 | 0.0970 | 121.6 | 0.66 |
| reuse_reserve | 0.455 | 0.96 | 80.1 | 0.0289 | 36.7 | 0.46 |
| reuse_noreserve | 0.466 | 1.37 | 100 | 0.0572 | 71.3 | 0.66 |

### Table C1/C2. Reversal: FreshCheck (`fresh_reserve`) vs comparators

| comparator | J/T gain [95% CI] | relative | grade | post-reversal harm gain | relative | grade |
|---|---|---|---|---|---|---|
| existing_promo_only | 0.1710 [0.1520, 0.1905] | +26.3% | substantial better | 0.2015 [0.1796, 0.2244] | +79.3% | substantial better |
| existing_cusum | -0.0636 [-0.0707, -0.0569] | -15.3% | substantial worse | -0.0433 [-0.0512, -0.0360] | -463% | substantial worse |
| existing_hysteresis | -0.0411 [-0.0474, -0.0349] | -9.4% | meaningful worse | -0.0267 [-0.0351, -0.0184] | -103% | substantial worse |
| paced_cusum | -0.0606 [-0.0678, -0.0538] | -14.4% | substantial worse | -0.0426 [-0.0504, -0.0354] | -423% | substantial worse |
| paced_cost_threshold | -0.0270 [-0.0340, -0.0202] | -6.0% | meaningful worse | -0.0098 [-0.0185, -0.0017] | -23% | substantial worse |

Harm relative percentages are large because the comparators' harm is near zero; read the absolute
gain. Per-cell: FreshCheck is worse than existing CUSUM in all four reversal cells (J/T gains
-0.054 to -0.070, CIs exclude 0; Table D in `tables.md`).

### Table C3. Persistent: value lost / gained (`fresh_reserve`; gain < 0 means value lost)

| comparator | J/T gain [95% CI] | relative | grade |
|---|---|---|---|
| existing_promo_only | -0.0702 [-0.0821, -0.0582] | -17.7% | substantial worse |
| existing_cusum | +0.0394 [0.0238, 0.0549] | +7.8% | meaningful better |
| existing_hysteresis | -0.0315 [-0.0440, -0.0190] | -7.2% | meaningful worse |
| paced_cusum | +0.0433 [0.0274, 0.0596] | +8.5% | meaningful better |
| paced_cost_threshold | -0.0496 [-0.0612, -0.0384] | -11.9% | substantial worse |

Early-onset persistent cells carry the CUSUM advantage (+0.058 and +0.078, substantial); late-onset
persistent cells are unresolved (CI spans 0). The advantage over CUSUM is mostly CUSUM's own false rollbacks
(Table F), not a FreshCheck gain over promotion-only.

### Table E. False promotion, boundary null (500 per d; Clopper-Pearson upper)

| method | d=1 | d=10 | pooled 1000 |
|---|---|---|---|
| existing_promo_only | 14/500 (0.047) | 6/500 (0.026) | 0.020 (0.031) |
| existing_cusum | 6/500 (0.026) | 0/500 (0.007) | 0.006 (0.013) |
| existing_hysteresis | 3/500 (0.017) | 0/500 (0.007) | 0.003 (0.009) |
| paced_promo_only | 11/500 (0.039) | 10/500 (0.036) | 0.021 (0.032) |
| paced_cusum, paced_cost_threshold, fresh_noreserve, reuse_noreserve | 5/500 (0.023) | 5/500 (0.023) | 0.010 (0.018) |
| fresh_reserve, cusum_reserve, reuse_reserve, fresh_reserve_a20 | 7/500 (0.029) | 2/500 (0.014) | 0.009 (0.017) |

All upper bounds are well under 0.1. These are the same promotion gate in every method, so differences
among them are pacing and alpha spending, not the rollback rule.

### Table F. False rollback in persistent streams (500 per cell, 2000 pooled)

Pooled rate (upper): existing_cusum 0.535 (0.558), paced_cusum 0.520, cusum_reserve 0.585, existing_hysteresis
0.033 (0.042), paced_cost_threshold 0.002 (0.004), fresh_* and reuse_* 0.000 (0.002). The existing
Page-CUSUM rolls back a challenger that is truly better by 0.8 in 43-73% of streams, which also explains
its persistent-case loss; this reflects its parameters (kappa=2, `ref` derived from the promotion window),
which I did not tune.

### Table H. Keep-null (benefit exactly h after an early better window; promoted streams, d pooled)

| method | promoted | rollback statistic fired | realised rollback |
|---|---|---|---|
| existing_cusum | 773 | 0/773 | 772/773 (0.999) |
| existing_hysteresis | 722 | n/a | 713/722 (0.988) |
| paced_cusum | 775 | 775/775 | 775/775 |
| paced_cost_threshold | 775 | n/a | 706/775 (0.911) |
| fresh_reserve | 584 | 2/584 (0.003; upper 0.012) | 2/584 (upper 0.012) |
| fresh_noreserve | 775 | 2/775 (0.003; upper 0.009) | 2/775 |
| reuse_reserve | 584 | 381/584 (0.652) | 364/584 (0.623) |
| reuse_noreserve | 775 | 388/775 (0.501) | 365/775 (0.471) |
| fresh_reserve_a20 | 584 | 8/584 (0.014; upper 0.027) | 8/584 |

(The `existing_cusum` statistic column is 0 because that repo object does not expose the flag; the
realised column is the measurement.) At a boundary where staying is still right by the hurdle, the
heuristics roll back almost every time; the fresh e-process stays at about 0.3%, well under the
allocated 0.05 for the first episode (the mixture and the boundary are conservative). The `reuse`
ablation, which has no level argument, rolls back in 47-62% of promoted keep-null streams. This is the
one place where the fresh-versus-reuse distinction pays: reuse is faster (below) but invalid.

### Table G. Ablations (pooled)

| contrast | reversal J/T gain (rel) | reversal harm gain | persistent J/T gain (rel) |
|---|---|---|---|
| reuse vs fresh, reserve | +0.0250 [0.0212, 0.0288] (+5.2%, meaningful) | +0.0238 (+45%, substantial) | 0.0000 (identical; no rollback occurs) |
| reuse vs fresh, no reserve | +0.0413 [0.0366, 0.0460] (+8.1%, meaningful) | +0.0397 (+41%, substantial) | 0.0000 |
| no reserve vs reserve (fresh) | -0.0281 [-0.0373, -0.0190] (-5.8%, worse) | -0.0443 (-84%, worse) | +0.0497 [0.0384, 0.0614] (+10.6%, substantial better) |
| reserve vs none (CUSUM) | -0.0123 [-0.0168, -0.0081] (-2.9%, small worse) | +0.0046 (+46%) | -0.0505 [-0.0698, -0.0309] (-9.9%, meaningful worse) |

Reading: (i) *Fresh vs reuse*: reusing wealth reverses faster (5-8% J/T on reversal) but fails the
keep-null level check (above), so the speed gain is the price of an invalid test; the fresh process pays
roughly 30-50 extra rounds of rollback delay (66 vs 37 with reserve, 122 vs 71 without) for validity. (ii) *Reserve vs none*: the reserve speeds
rollback after a reversal (harm -84% relative) but delays promotion by thinning the pre-promotion labels
(persistent J/T +10.6% worse with it); net on the equal-weight mean it is a loss (0.496 vs 0.489 for
fresh). For CUSUM the reserve is a net loss too.

## Ported comparators (follow-up)

Code: `src/shiftlab/gaver/erb_port.py` (docstring cites sources and every adaptation), run with
`--methods erb,erb_a05,two_phase --tag ext` on the same cells and the same WP3 seeds (including keep-null),
rows in `outputs/gaver/wp3/records_ext.jsonl`. Because the file merges with `records.jsonl`, the tables
in `tables.md` now include them.

Adaptation choices (details in the module docstring): E_rb keeps the source's detector (restart-mixture SR
e-detector, gap 10, bets .15/.3/.5, `alpha_rb` 0.10 or 0.05 for `erb_a05`, grid over the budget left at
promotion, halving shares for re-promotion, horizon veto) but takes x = D, uses this harness's promotion
gate and credit pacing (no reserve), and has no hurdle in its null (`E[D] <= 0`) and no economic gate; with
`g_ref = h` the horizon veto is 1 round and effectively inactive at s = 0.1. Two-phase: the source's
fixed discovery/persistence windows become adaptive (phase 2 starts at the phase-1 alarm round, fresh
e-process, each phase at the full promotion level), promotion-only, no rollback.

| method | J/T persistent | J/T reversal | J/T transient | equal-weight mean | reversal harm/T | rollback delay | switches (reversal) |
|---|---|---|---|---|---|---|---|
| erb | 0.418 | 0.508 | 0.542 | 0.489 | 0.0965 | 120.8 | 1.34 |
| erb_a05 | 0.418 | 0.520 | 0.542 | 0.493 | 0.1083 | 135.8 | 1.30 |
| two_phase | 0.569 | 0.445 | 0.541 | 0.518 | 0.0027 | 3.4 | 0.01 |
| fresh_reserve (reference) | 0.467 | 0.480 | 0.541 | 0.496 | 0.0527 | 66.2 | 0.96 |
| fresh_noreserve (reference) | 0.418 | 0.508 | 0.542 | 0.489 | 0.0970 | 121.6 | 1.32 |
| existing_cusum (reference) | 0.507 | 0.417 | 0.541 | 0.488 | 0.0094 | 11.8 | 1.43 |

FreshCheck (`fresh_reserve`) vs the ported comparators (gain = comparator - FreshCheck, J/T, pooled):

| comparator | reversal J/T gain [95% CI] | grade | reversal harm gain | persistent J/T gain [95% CI] | grade |
|---|---|---|---|---|---|
| erb | +0.0272 [0.0183, 0.0362] (+5.4%) | meaningful better | +0.0438 (+45%) substantial better | -0.0497 [-0.0614, -0.0384] (-11.9%) | substantial worse |
| erb_a05 | +0.0392 [0.0294, 0.0490] (+7.5%) | meaningful better | +0.0555 (+51%) substantial better | -0.0497 (-11.9%) | substantial worse |
| two_phase | -0.0353 [-0.0428, -0.0273] (-7.9%) | meaningful worse | -0.0500 (harm 0.0027) substantial worse | +0.1014 [0.0886, 0.1142] (+17.8%) | substantial better |

Safety: false promotion in boundary-null streams is 10/1000 for `erb`/`erb_a05` (upper 0.018) and 0/1000
for `two_phase` (upper 0.004). Persistent false rollback is 0/2000 for all three. Keep-null rollback among
promoted streams: `erb` 1/775 (upper 0.007); `two_phase` promoted only 58/775 streams, 0 rollbacks (no
rollback exists).

Reading.
- **E_rb vs FreshCheck:** the fresh e-process (without reserve) and E_rb are indistinguishable in the
  means (reversal J/T 0.508 vs 0.508, harm 0.0970 vs 0.0965, delay 122 vs 121 rounds; persistent
  identical). E_rb is not the stronger incumbent that would have changed the picture: it is as slow as the
  fresh process and far slower than the heuristic CUSUM (harm 0.0965 vs 0.0094). It also controls
  false rollback at the keep-null boundary (1/775), so FreshCheck's "level-valid" property is not unique to it;
  FreshCheck's distinct features are the explicit hurdle in the null and the reserve (which buys the 45%
  harm reduction at an 11.9% persistent cost).
- **Two-phase vs FreshCheck and CUSUM:** it wins the reversal cells (J/T 0.445, harm 0.0027) only because
  the second e-process rarely completes before the reversal (0.01 switches per stream), and it pays 17.8% in
  persistent value versus FreshCheck (0.569 vs 0.467; 43% above promotion-only). Against CUSUM it is worse
  on persistent (+0.062) and slightly worse on reversal (0.445 vs 0.417). Its equal-weight mean (0.518) is
  the worst of the rollback-capable comparators.
- The adaptive phase boundary is my adaptation of an offline fixed-window design; a fixed-window
  version with an optimised split could behave differently.

## Limitations and caveats

- One synthetic family: iid Bernoulli within regime, a single effect size (D = +-0.8), one budget
  (B=0.1T), s=0.1, two delays. No dependence, no weak effects. The conclusion that the heuristics roll
  back at the boundary is partly a statement about these generators; the existing CUSUM `ref` is tied to
  the promotion window and is not tuned for this setting, so its poor persistent-case performance is not
  necessarily its best case.
- FreshCheck's slowness is partly mixture dilution (32 starts x 5 stakes) at level 0.05; I did not
  tune stakes, mixture, or `alpha_rb` (one sensitivity run at 0.2 changed little: harm 0.0472 vs 0.0527).
- The `paced` comparators differ from the repo's uniform calendar in how the budget is spread; the
  existing-controller rows use the unmodified repo code and uniform calendar.
- Row provenance: the alt/null500/persist500 studies were produced by the first launch; the keep-null
  study was added afterward together with the `stat_trigger` flag and a boundary-inclusive `false_rb`
  tolerance (`mean <= -h + 1e-9`). These only add fields or boundary cases; they do not change the
  earlier rows (no stream in those studies sits on the boundary). The pre-keep-null persistent false-rollback
  counts above are unaffected.
- The "false rollback" in Table F/H is relative to the hurdle-based null; economically, rolling back
  at benefit exactly 0.1 loses 0.1 per round, so treating those rollbacks as false is also the
  economic reading.
- Transient cells are not informative at this window length.

## Commands

```bash
cd C:/Users/nigel/OneDrive/桌面/ICML/shiftlab-gave-r-2026-11-06
export PYTHONPATH="$PWD/src" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONIOENCODING=utf-8
PY=C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/.venv/Scripts/python.exe
$PY -m pytest tests/test_gaver_freshcheck.py -q                       # 11 passed
$PY -m ruff check src/shiftlab/gaver/freshcheck.py scripts/gaver/run_freshcheck_*.py tests/test_gaver_freshcheck.py
$PY scripts/gaver/run_freshcheck_main.py --smoke --workers 12          # smoke, outputs/gaver/wp3/smoke
$PY scripts/gaver/run_freshcheck_main.py --workers 10                  # full, resumable, ~11 + ~4 min
$PY scripts/gaver/run_freshcheck_main.py --workers 12 --methods erb,erb_a05,two_phase --tag ext   # follow-up, ~8 min
$PY scripts/gaver/run_freshcheck_analyze.py                            # tables.md, *.csv
```

The full run was launched detached with PowerShell `Start-Process` (two launches: the second added the
keep-null study and resumed). Seed blocks: alt 101120000 + 100 x cell (60 each), boundary null
101130000/101131000, persistent 101140000 + 1000 x cell, keep-null 101150000/101151000, all inside
101120000-101159999. Stream seed shared by all methods per (cell, replicate). Environment: repo `.venv`
Python, numpy/scipy as installed; commit `2a8b695b` (code), results doc committed afterward.
