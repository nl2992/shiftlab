# PAVE matched-acquisition comparison (Track C)

Date 2026-11-08, branch `research/methods-recovery-2026-11-07`. Development evidence only. Script
`scripts/methods_recovery/pave_matched.py`; outputs (gitignored) `outputs/methods_recovery/pave_matched/`.

## Question

Doc 40 compared PAVE (DSS-shell evidence) with `episode_front` (own evidence) and found a tie, which is not a
matched comparison. Here every arm uses the SAME frozen DSS-shell evidence and decision rule; only the request
rule differs. Does PAVE's value-of-label acquisition beat the best matched simple schedule (including the
`episode_front` schedule) in long-delay cells, and which PAVE term carries the gain?

## ef_sched: exact port of episode_front's acquisition

`episode_front` is `EpisodeComposition("front")` (`src/shiftlab/dive/switching_explore.py`). `"front"` names its
ALPHA SPENDING (all alpha on episode 0, `_alpha_j`), not its schedule. Its request rule is
`decide(...) -> (act, t in self.cal)` with `self.cal = uniform_calendar(T, B, d)`: up to B rounds
`ceil(j (T-d)/B)`, j = 1..B, fixed before the run, data-independent, parameter-free. So `ef_sched` =
`t in uniform_calendar(T, B, d)` (plus the shell's `used < B`, `t + d <= T` guard) inside the DSS shell; there is
nothing to tune and no dependence on evidence state, so no mapping beyond that is needed. The DSS-shell
`uniform` variant uses the same calendar (`t in self.cal`), so `ef_sched` should equal the shell's `uniform` (and
gate-on DSS acquisition); the smoke run confirms identical cost, label count and pending inventory. Consequence:
**PAVE - ef_sched is PAVE - uniform acquisition**, and the whole difference between native `episode_front` and
`ef_sched` is evidence/decision machinery (episode_front's own bounded-mean e-process + economic check), not
acquisition.

## Arms

All DSS-shell evidence unless noted. `ef_sched`; `pave` (`GaverMethod("dss","pave")`, delay-gated, reserve off,
kappa .1, q .03, no tuning); `pave_nopend` (`PaveParams.pending=False`); `pave_nopendinfo`; `pave_nodeadline`
(`deadline=False`); simple rules from doc 40 (`SimpleAcq`): S1 deadline cutoff (m in {0,25,50,100,200}), S2
pending cap (cap in {1,2,3,5,8}, needed only for S4), S3 front-loading (f in {.5,...,.9}), S4 = S1 + S2 at the
separately selected m and cap; native `episode_front` (own evidence, descriptive reference).

PAVE pending/deadline terms (`src/shiftlab/gaver/pave.py`): `pending` is ONE switch that does two things: (a) in
the rollout, pending labels enter the posterior sample size `n_pend` and the last-update time `e_last`; (b) the
request capacity is `ceil(d B_rem / H_rem)` instead of the fixed DSS `pending_cap`. `deadline` is a separate
switch (rollout uses post-arrival horizon `R = T - a + 1` and arrival offset `d`, vs `R = T - t + 1`). Since
`pending=False` also reverts the capacity to the DSS fixed cap (2), it is a confounded ablation, so a finer
`pave_nopendinfo` hides pending labels from the rollout only (adaptive capacity kept). Smoke at d=200: PAVE spends
all 50 labels, `pave_nopend` only 8, `pave_nopendinfo` 50.

## Cells and seeds

27 long-delay cells = the 9 GAVE-R gate-on specs at d in {50, 100, 200} (`on0.3_L1_strong_harmful`,
`on0.6_L0.6_strong_harmful`, `on0.6_L1_medium_harmful`, `on0.6_L1_strong_harmful_s{0.05,0.1,0.5}`, `..._b0.1`,
`on0.6_L1_strong_neutral`, `on0.8_L1_strong_harmful`; `b0.05/s0.1` unless noted), T=1000, B in {50,100}.
Gate `d >= 2T/(B+2)` (threshold 38.5 at B=50, 19.6 at B=100): `gate_check.json` and every eval row assert it; all 27
satisfy it. 6 d=10 control cells (gate off, report only): {on0.6 L1 strong, on0.3 L0.6 strong, on0.6 L1 medium}
harmful x B/T {.05,.1}.
Seeds (registered in `configs/seed_registry.yaml` before any run): `pave_c_tuning` 101700000-101709999,
`pave_c_eval` 101800000-101809999; seed = start + 100 x cell_index + replicate; 20 tuning, 60 eval seeds per cell.
Tuning per delay on the pooled mean J/T over that delay's 9 cells; no re-tuning after eval.

## Registered decision rule (written before any tuning or eval run)

Primary estimand: pooled J/T over the 27 long-delay cells, equal cell weights, paired bootstrap (4000 resamples
over seeds within cells), differences as % of `ef_sched` (= uniform) pooled J/T. "Best matched simple rule" =
argmin over {S1, S3, ef_sched, S4} of pooled TUNING-seed J/T, selected separately per delay (so the 27-cell
contrast uses each delay's selected rule).
- ADVANCE PAVE as the Track-C candidate iff: PAVE beats the best matched rule by >= 2% of uniform with 95% CI
  excluding 0 AND PAVE - ef_sched has CI excluding 0 (PAVE cheaper) AND the pending ablation PAVE - pave_nopend
  has CI excluding 0 (PAVE cheaper).
- STOP iff the best matched simple rule is within 1% of PAVE (PAVE advantage < 1%) or better.
- Otherwise WEAK.
Qualifier (also registered): if the pending ablation passes only for `pave_nopend` but not `pave_nopendinfo`, the
contribution is attributed to the adaptive pending capacity (a cap rule), not to the value-of-label rollout, and
is reported as such. `pave_nodeadline`, `pave_nopendinfo`, per-delay contrasts and `episode_front` native are
descriptive. Control cells and the native comparison are descriptive.

## Tuning picks (20 seeds/cell, pooled over each delay's 9 cells; tuning J/T)

| delay | S1 m | S2 cap | S3 f | S4 | ef_sched | S1 / S3 / S4 | best matched (tuning) |
|---|---|---|---|---|---|---|---|
| 50 | 100 | 8 | .5 (= ef_sched) | m100, cap8 | .4190 | .4098 / .4190 / .4098 | S1 |
| 100 | 25 | 8 | .5 | m25, cap8 | .4301 | .4250 / .4301 / .4297 | S1 |
| 200 | 100 | 8 | .5 | m100, cap8 | .4430 | .4418 / .4430 / .4570 | S1 |

Front-loading again never helped (S3 = ef_sched). At d=50 the cap never binds, so S4 = S1. The selected rule is S1
in every delay, so the 27-cell "best matched" arm is S1 with per-delay m.

## Evaluation (60 fresh seeds x 27 cells; J/T = (loss + c N_q + s N_s)/T)

Pooled J/T with equal cell weights; q = mean labels used, arr = mean rounds between label arrival and T,
pend = mean pending inventory.

| arm | d50 | d100 | d200 | all 27 | q (all) | arr | pend |
|---|---|---|---|---|---|---|---|
| ef_sched (= uniform acquisition) | .4181 | .4269 | .4399 | .4283 | 55.6 | 433 | 6.43 |
| episode_front (native, own evidence) | .4048 | .4166 | .4354 | .4189 | 55.6 | 433 | 6.43 |
| **PAVE** | .4016 | .4171 | .4374 | .4187 | 50.6 | 380 | 5.82 |
| PAVE no-pending (flag) | .4459 | .4585 | .4585 | .4543 | 21.3 | 499 | 1.75 |
| PAVE no-pending-info (rollout only) | .4290 | .4359 | .4453 | .4367 | 55.5 | 490 | 6.42 |
| PAVE no-deadline | .4606 | .4584 | .4585 | .4592 | 11.6 | 429 | 0.99 |
| S1 (tuned, = best matched) | .4173 | .4264 | .4409 | .4282 | 55.6 | 471 | 6.43 |
| S2 (cap 8) | .4181 | .4316 | .4539 | .4345 | 46.7 | 447 | 4.76 |
| S3 (f = .5) | .4181 | .4269 | .4399 | .4283 | 55.6 | 433 | 6.43 |
| S4 | .4173 | .4316 | .4545 | .4345 | 46.4 | 474 | 4.70 |

Paired bootstrap 95% CI (4000 resamples over seeds within cells), difference in J/T as % of ef_sched's pooled J/T
(negative = first arm cheaper):

| contrast | d50 | d100 | d200 | all 27 |
|---|---|---|---|---|
| **PAVE - best matched (S1)** | -3.76 [-5.08, -2.44] | -2.18 [-3.15, -1.20] | -0.81 [-1.52, -0.12] | **-2.22 [-2.81, -1.67]** |
| **PAVE - ef_sched** | -3.96 [-5.25, -2.70] | -2.29 [-3.29, -1.31] | -0.56 [-1.20, +0.05] | **-2.24 [-2.84, -1.67]** |
| **PAVE - pave_nopend (flag)** | -10.59 [-11.70, -9.48] | -9.71 [-10.50, -8.91] | -4.80 [-5.26, -4.34] | **-8.32 [-8.82, -7.84]** |
| PAVE - pave_nopendinfo (rollout only) | -6.55 [-7.74, -5.31] | -4.41 [-5.49, -3.35] | -1.78 [-2.42, -1.16] | -4.21 [-4.79, -3.63] |
| PAVE - pave_nodeadline | -14.12 [-15.10, -13.15] | -9.69 [-10.48, -8.89] | -4.80 [-5.25, -4.33] | -9.46 [-9.91, -9.02] |
| PAVE - episode_front native (descriptive) | -0.78 [-2.15, +0.55] | +0.11 [-0.90, +1.14] | +0.45 [-0.19, +1.09] | -0.06 [-0.68, +0.54] |
| best matched - ef_sched | -0.20 [-1.50, +1.09] | -0.11 [-1.02, +0.79] | +0.24 [-0.40, +0.90] | -0.02 [-0.57, +0.55] |
| ef_sched - episode_front native | +3.18 [+2.71, +3.63] | +2.41 [+2.12, +2.72] | +1.02 [+0.86, +1.20] | +2.18 [+1.99, +2.38] |
| PAVE - S4 (all 27) | | | | -3.68 [-4.25, -3.12] |

Per-cell: PAVE is cheaper than the best matched rule in 20 of 27 cells (7/9, 6/9, 7/9 at d = 50/100/200). Its
gain is concentrated in the strong-harm B/T .05 cells (d50: -9 to -13% of uniform; d100: about -7%; d200: -2 to
-3%). It loses in the `on0.3_L1` cell at every delay (+5.3, +1.2, +3.5%) and clearly in the `b0.1` (B=100) cell
(+15.6, +11.1, +1.7%), where the budget is large and a deadline cutoff is the better rule.

Gate: all 27 long-delay cells satisfy `d >= 2T/(B+2)` (threshold 38.5 for B=50, 19.6 for B=100;
`gate_check.json`; every eval row has the gate on). No cell failed.

Control (d=10, gate off, 6 cells, report only; pooled J/T): dss .4094, ef_sched .4181, episode_front .3997,
S1(m100, d50 pick, ungated) .4139. Versus dss: ef_sched +2.13% [+0.30, +4.01], S1 +1.10% [-0.91, +3.19],
episode_front -2.38% [-4.15, -0.61]. PAVE equals dss by construction here (gate off) and was not run.

## Verdict (registered rule): ADVANCE (qualified)

Pooled 27 cells: PAVE beats the tuning-selected best matched simple rule by 2.22% of uniform, CI [1.67, 2.81]
(threshold 2%, CI excludes 0); beats ef_sched by 2.24% [1.67, 2.84]; the pending ablation (flag) is -8.32%
[-8.82, -7.84] and the rollout-only pending ablation is -4.21% [-4.79, -3.63]. All three registered conditions
hold. Attribution: the pending contribution is not just the adaptive capacity cap. With the adaptive capacity kept
and all labels still bought (55.5 vs 50.6), hiding pending labels from the value rollout costs 4.2%, and
dropping the deadline term costs 9.5%. Both ablations are large partly because they change what PAVE does at long
delay: `pave_nopend` and `pave_nodeadline` collapse to 21 and 12 labels, i.e. they under-spend. The numbers are
upper bounds on each term's marginal value, not clean unit effects.

Readings that limit the claim (why "qualified"):
1. The margin is thin and shrinks with delay: 3.76% at d=50, 2.18% at d=100, 0.81% at d=200 (CI [-1.52, -0.12];
   PAVE - ef_sched at d=200 is -0.56 [-1.20, +0.05], not significant). Only d50/d100 exceed 2% individually; the
   pooled 2.22% is carried by them.
2. Native `episode_front` is tied with PAVE (-0.06% [-0.68, +0.54]). Its schedule equals ef_sched; what differs
   is its evidence/decision machinery, which is 2.18% [1.99, 2.38] cheaper than the DSS-shell evidence on the
   identical calendar. So PAVE's acquisition gain on DSS evidence is about the size of swapping in
   episode_front's evidence. Whether PAVE's gain survives on episode_front's evidence (the stronger engine) is
   untested and is the decisive next test: if it vanishes there, PAVE only compensates for a weaker shell.
3. Cell concentration and a loss region (large budget B/T=.1; onset .3), as in doc 40.
4. Simple schedules (S1, S3) are indistinguishable from uniform pooled (S1 -0.02% [-0.57, +0.55]); pending caps
   (S2, S4) hurt at d=200 (+3.2%, +3.3% of uniform), consistent with doc 40.

Grade: small-to-moderate effect (2.2% of J/T), CI well away from 0, 20/27 cell wins; meets the registered bar.
Continue PAVE as the Track-C candidate, first step PAVE on `episode_front`'s evidence, then a locked-parameter
confirmatory seed block.

## Deviations and caveats

- Rule applied exactly to the 27-cell pool. `ef_sched` has no parameters and is the same schedule as the DSS-shell
  `uniform` variant, so "PAVE - ef_sched" is the same contrast as "PAVE - uniform acquisition" (reported as
  registered; it is not independent evidence from the best-matched contrast when S1 ~ uniform).
- Extra arms beyond the spec: `pave_nopendinfo` (the single `pending` flag also changes the capacity rule) and
  `pave_nodeadline` (separate flag). The registered pending criterion used the flag version `pave_nopend`; the
  rollout-only version passes too.
- S1's grid was extended to m in {0,25,50,100,200} (doc 40 stopped at 100) because d=200 widens the useful
  cutoff. Best matched is selected per delay on tuning seeds (ties: ef_sched, S1, S3, S4; none occurred).
- Simple rules in the control cells run ungated with the d=50 pick (harm check only). T = 1000, fixed delays,
  family-1 streams; on0.8 cells at d=200 are nearly uninformative (labels for post-onset events arrive late).
- Seeds allocated manually (1017xxxxx-1018xxxxx unused in configs on all local refs); development evidence, not
  confirmatory.

## Commands

```
export OPENBLAS_NUM_THREADS=1
PY=C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/.venv/Scripts/python.exe
$PY scripts/methods_recovery/pave_matched.py gate
$PY scripts/methods_recovery/pave_matched.py tune --workers 6     # ~1.5 min
$PY scripts/methods_recovery/pave_matched.py eval --workers 6     # ~15 min
$PY scripts/methods_recovery/pave_matched.py analyse
```
