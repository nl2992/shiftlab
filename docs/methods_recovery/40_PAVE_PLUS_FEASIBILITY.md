# PAVE+ feasibility (Track C): can a simple acquisition rule capture delay-gated PAVE's long-delay gain?

Date 2026-11-08, branch `research/methods-recovery-2026-11-07`. Development evidence only; no confirmation
seeds. Script: `scripts/methods_recovery/pave_plus_feasibility.py`. Outputs (gitignored):
`outputs/methods_recovery/pave_plus/{rows_tune,rows_eval}.jsonl, picks.json, tuning_table.json, analysis.json`.

## Question and stop rule (registered before running)

GAVE-R WP5 found delay-gated PAVE 4.4% cheaper (J/T) than DSS acquisition (= uniform there) in 9 gate-on cells
(d = 50, B/T .05-.1, gate `d >= 2T/(B+2)`), same DSS evidence. Does a SIMPLE rule capture that gain?
- STOP PAVE+ if the best simple rule is within 1% of PAVE (or better) pooled over gate-on cells.
- ADVANCE if PAVE beats the best simple rule by >= 2% (relative to uniform) with a CI excluding 0.
- Otherwise weak/inconclusive.

## Arms (evidence = frozen DSS shell evidence in every arm; only the request rule differs)

`uniform` (the DSS-shell variant `uniform`; identical to DSS acquisition in gate-on cells), `episode_front`
(existing Atlas baseline, own evidence), `pave` (`GaverMethod("dss","pave")`, delay-gated, reserve off,
kappa .1, q .03), and simple rules implemented as `SimpleAcq(GaverMethod)` overriding `_query` (the request at
t depends on t, config, own request count and pending count only; `can_query` keeps `used < B`, `t+d <= T`;
every run asserts `queries <= B`):
- S1 deadline cutoff: uniform pacing over `[1, T-d-m]`, no query afterwards; m in {0, 25, 50, 100}.
- S2 pending cap: uniform pacing over `[1, T-d]`, query only while pending < cap; cap in {1, 2, 3, 5, 8}.
- S3 front-loading: fraction f of B in the first half of `[1, T-d]`; f in {0.5, 0.6, 0.7, 0.8, 0.9}.
- S4 = S1 + S2 with the separately selected best m and best cap (not jointly tuned).
Sanity checks: S1 m=0 and S3 f=0.5 reproduce `uniform` exactly (identical costs).

## Cells and seeds

- Primary: the 9 WP5 gate-on cells (all d = 50): `on0.3_L1_strong_harmful`, `on0.6_L0.6_strong_harmful`,
  `on0.6_L1_medium_harmful`, `on0.6_L1_strong_harmful_s0.05`, `..._s0.1` (the regression cell), `..._s0.5`,
  `..._b0.1`, `on0.6_L1_strong_neutral`, `on0.8_L1_strong_harmful` (all `_d50_b0.05_s0.1` unless noted).
- Stress extension: same 9 cells with d = 100 (also gate-on).
- Control (gate off, report only): 6 cells with d = 10: {on0.6 L1 strong, on0.3 L0.6 strong, on0.6 L1 medium}
  harmful x B/T {.05, .1}, s .1. Simple rules are applied ungated here (with the d = 50 picks), versus `dss`.
- Seeds (registered in `configs/seed_registry.yaml` before running): `pave_plus_tuning` 101500000-101509999,
  `pave_plus_eval` 101600000-101609999; seed = start + 100 x cell_index + replicate. 20 tuning seeds and 60 eval
  seeds per cell; streams paired across arms. No re-tuning after eval.

## Tuning picks (20 seeds/cell, pooled mean J/T over the 9 cells of each delay)

| delay | S1 m | S2 cap | S3 f | S4 | uniform J/T | tuning J/T of the pick (S1 / S2 / S3) |
|---|---|---|---|---|---|---|
| 50 | 50 | 5 | 0.5 (= uniform) | m50, cap5 | .4218 | .4142 / .4214 / .4218 |
| 100 | 50 | 8 | 0.5 (= uniform) | m50, cap8 | .4278 | .4181 / .4327 / .4278 |

Front-loading never helped (every f > 0.5 was worse than uniform), so S3 degenerates to uniform. A tight cap
(1-3) is clearly harmful.

## Evaluation (60 fresh seeds per cell; J/T = (loss + c N_q + s N_s)/T)

Pooled with equal cell weights. "arr" = mean rounds between label arrival and T (larger = labels arrive earlier);
"pend" = mean pending-label inventory per round; "q" = mean labels used.

| arm | d50 J/T | q | arr | pend | d100 J/T | q | arr | pend |
|---|---|---|---|---|---|---|---|---|
| uniform | .4198 | 55.6 | 466.0 | 2.72 | .4276 | 55.6 | 441.5 | 5.50 |
| episode_front | .4053 | 55.6 | 466.0 | 2.72 | .4175 | 55.6 | 441.5 | 5.50 |
| PAVE (gated) | .4054 | 51.2 | 406.2 | 2.51 | .4200 | 51.0 | 393.8 | 5.05 |
| S1 (m=50) | .4138 | 55.6 | 491.5 | 2.72 | .4270 | 55.6 | 466.9 | 5.50 |
| S2 (cap 5 / 8) | .4189 | 55.0 | 466.1 | 2.69 | .4318 | 52.4 | 443.1 | 5.19 |
| S3 (f = .5 = uniform) | .4198 | 55.6 | 466.0 | 2.72 | .4276 | 55.6 | 441.5 | 5.50 |
| S4 | .4164 | 54.4 | 491.8 | 2.67 | .4326 | 52.1 | 468.0 | 5.16 |

(`episode_front` shares uniform's calendar, so its label statistics equal uniform's; its evidence engine
differs.) The best simple rule by pooled eval J/T is S1 (m = 50) in every pool; it was also the tuning-seed
winner, so the choice is not eval-contingent.

Paired bootstrap 95% CI (4000 resamples over seeds within cells), differences as % of uniform's pooled J/T
(negative = first arm cheaper):

| contrast | 9 cells d=50 (primary) | 9 cells d=100 | all 18 gate-on |
|---|---|---|---|
| PAVE - best simple (S1) | **-2.02 [-3.24, -0.78]** | -1.65 [-2.70, -0.60] | -1.83 [-2.67, -1.02] |
| best simple (S1) - uniform | -1.43 [-2.60, -0.21] | -0.14 [-1.09, +0.80] | -0.78 [-1.57, -0.01] |
| PAVE - uniform | -3.45 [-4.61, -2.21] | -1.79 [-2.74, -0.85] | -2.61 [-3.39, -1.84] |
| PAVE - S2 | -3.23 [-4.37, -2.03] | -2.76 [-3.73, -1.84] | -2.99 [-3.76, -2.23] |
| PAVE - S4 | -2.63 [-3.85, -1.40] | -2.97 [-3.97, -1.94] | -2.80 [-3.62, -2.02] |
| PAVE - episode_front | +0.01 [-1.24, +1.30] | +0.57 [-0.45, +1.57] | +0.29 [-0.52, +1.10] |

Per-cell shape (J/T, d = 50): PAVE beats uniform by 8-10% in the four B/T .05, onset .6 strong cells (.3583 vs
.4060, .3754 vs .4019, .3653 vs .3972, .3663 vs .4043), ties in three cells, and is worse in two: `on0.3_L1`
(.4880 vs .4740; S1 .4559) and `b0.1` (.3670 vs .3418; S1 .3237). S1 beats PAVE in those two cells and in the
d = 100 `b0.1` cell. The PAVE gain is concentrated in a few cells; S1 is the more uniformly safe rule.

Control (d = 10, gate off, 6 cells, pooled J/T): dss .4086, uniform .4143, episode_front .3944, S1(m50) .4057,
S2(cap5) = S3 = uniform .4143, S4 = S1. Versus dss: S1 -0.71% [-2.46, +1.10], S2/S3/uniform +1.37%
[-0.61, +3.35]. The simple rules (ungated) do not systematically harm gate-off cells, but cell-level spread is
large (S1 is +17.7% in `on0.6_L1_strong_b0.05`, -14.0% in `on0.3_L0.6_strong_b0.1`). PAVE equals DSS there by
construction.

## Verdict (registered rules)

**Primary 9 gate-on cells (d = 50): the ADVANCE criterion is met, only just.** The best simple rule (S1,
deadline cutoff, m = 50) is not within 1% of PAVE; PAVE beats it by 2.02% of uniform with CI [0.78, 3.24]
excluding 0, against a threshold of 2%. The point estimate sits on the threshold and the CI lower bound is far
below it, so this is a borderline pass. The d = 100 stress extension (1.65% [0.60, 2.70]) and the pooled 18 cells
(1.83% [1.02, 2.67]) are below the 2% bar; by the same rule they read "weak/inconclusive" (not STOP: the gap is
above 1% and the CIs exclude 0).

Established: (i) simple rules capture only part of PAVE's gain: S1 takes 1.43 of PAVE's 3.45 points at d = 50
(about 41%) and almost nothing at d = 100; S2, S3, S4 are at most 0.8 points and often worse than uniform;
(ii) PAVE beats every simple rule with a CI excluding 0 in all three pools.
Not established: (a) PAVE is statistically indistinguishable from `episode_front` (+0.01 [-1.24, +1.30] at
d = 50), an existing in-repo comparator, so the headroom attributable to a value-of-label mechanism specifically
is limited; a PAVE+ claim must beat `episode_front`, not uniform; (b) PAVE's gain is carried by four to five
cells and it loses to S1 in two d = 50 cells; (c) PAVE uses fewer labels (51.2 vs 55.6) and buys them later
(arrival 406 vs 466 rounds before T), whereas S1 buys earlier, so the two are mechanistically different.

Recommendation: weak ADVANCE at most. The gain over the best simple rule is real but small (about 2% of J/T),
cell-concentrated, and not distinguishable from an existing baseline. If PAVE+ continues, the next test is
PAVE+ versus `episode_front`, and a rule combining S1's deadline cutoff with PAVE's fewer, later spending;
a confirmatory run needs its own pre-registered seeds.

## Deviations and caveats

- The registered verdict is read on the 9 primary d = 50 cells (the WP5 gate-on family); the d = 100 and
  pooled-18 readings are reported alongside because they change the grade.
- S4 uses the separately tuned best m and best cap, not a joint grid ("only if cheap").
- Control cells run the simple rules ungated (they replace DSS acquisition there) with d = 50 picks; this is a
  harm check, not a tuned comparison.
- `uniform` is the DSS-shell `uniform` variant; in gate-on cells it equals DSS acquisition by construction (not
  re-asserted run by run). `episode_front` uses the Atlas evidence, not DSS evidence.
- "Best simple rule" for the contrast is the arm with the lowest pooled eval J/T (S1 in all pools), which
  coincides with the tuning-seed choice; selection among four arms slightly favours the simple side.
- One T = 1000, fixed delays, family-1 streams only; the d = 50 cells are a regression cell and its neighbours,
  as in WP5.
- Seeds were allocated manually in the registry (the 1015xxxxx-1016xxxxx range had no prior use in the repo).

## Commands

```
export OPENBLAS_NUM_THREADS=1
PY=C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/.venv/Scripts/python.exe
$PY scripts/methods_recovery/pave_plus_feasibility.py tune --workers 6     # ~1 min
$PY scripts/methods_recovery/pave_plus_feasibility.py eval --workers 6     # ~7 min
$PY scripts/methods_recovery/pave_plus_feasibility.py analyse
```

## Coordinator verdict (2026-11-08): **STOP PAVE+**

The registered rule reads ADVANCE-borderline: PAVE beats the best simple rule (S1 deadline cutoff,
m=50) by 2.02% [−3.24, −0.78] on the 9 primary d=50 cells. A PAVE+ contribution must also beat the
strongest existing acquisition baseline, though, and **delay-gated PAVE is tied with `episode_front`**:
- d=50: +0.01% [−1.24, +1.30];
- d=100: +0.57%;
- pooled over 18 cells: +0.29% [−0.52, +1.10].

The gain is concentrated in 4–5 cells, and PAVE loses to uniform in others. That meets directive
§6.7 ("simple front-loading matches the new policy"): no headroom survives for a delay-aware
acquisition method on this harness. A pending-label cap (S2) adds nothing, and the deadline cutoff
(S1) captures about 41% of PAVE's d=50 gain.

Kept findings:
- delay-gated PAVE ≈ `episode_front` in long-delay cells;
- deadline cutoff is a cheap partial substitute;
- pending caps are useless here.
