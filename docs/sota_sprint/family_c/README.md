# Family C: label acquisition and economics (SOTA sprint, Agent C)

Date: 2026-11-03. Code: `scripts/sota_sprint/fam_c.py` (sha256 prefix `c598771b471989b0`; behaviour
identical to the screened version, later edits added the `report` CLI and fixed import order).
Tests: `uv run pytest -q tests/sota_sprint/test_fam_c.py` (34 passed). Branch
`research/sota-sprint-24`, uncommitted. Contract: T=2000, B=200, c_q=.05, c_s=5, alpha=.05.

**Evidence class.** All numbers below are development screening diagnostics (20 seeds, default
dev seed base 2026110501, the same seeds used for tuning, so tuned rows are in-sample), plus a
20-seed descriptive check and a 300-seed null check at seed base 2026110513. None of this is
confirmatory evidence.

## What was built

Every candidate changes only acquisition; the host CS, stopping rule and deployment rule are
untouched. A single `Controller` produces `(pi, q)` per event: the event is recorded in the host CS
with predictable probability `pi`, and if it is a recorded disagreement its label is requested with
propensity `q`, which is frozen at issue. The host's importance weight is `1/q` from
`ReleasedFeedback.query_probability`. On gated, `wmax_t = max(1/q, 2)` is also fixed at issue.
Re-implementations of the host pacers (`Cchk:*`) reproduce `gated_adaptive_range`,
`gated_adaptive_range+front` and `discern_design_floor` exactly (unit test).

| id | implementation | mechanism |
|---|---|---|
| C1 | `GatedC` + `Controller(base="front", credit=True)` | skip (unrecorded) when released + pending labels reach `kappa * n_needed`, extrapolated from the current CS half-width and the point estimate |
| C2 | `GatedC` + `Controller(base="front", shadow=True)` | query iff value per label `max(0, G_eff (T-t) - c_s) / n_remaining` >= shadow price `c_q * max(1, spend_rate (T-t)/remaining)^gamma`; `G_eff = (1-zeta) max(G_hat,0) + zeta g_hi` |
| C3 | `QSGTwoStage` | QSG with concentrated phase (q=1 while undecided, at most `f B` labels and only before `tau T`), then uniform protected monitoring |
| C4 | `DiscernC` + `Controller(base="verdict")` | corrected DISCERN (design floor .25): pace the remaining budget to the projected verdict time rather than T |
| C5 | C1 + C2 | pending labels are credited in C2's `n_remaining` and in the C1 skip |
| C6 | `GatedC`/`DiscernC` + `Controller(shadow, deadline, two_stage)` | C2 price, C3-style two-stage split (`f2 B`, then uniform thinning), deadline-aware value: label worth 0 if `(T - t - delay - collection time) G_eff <= c_s` |
| tuned pacing | `gated_adaptive_range+pace_tuned`, `discern_design_floor+pace_tuned` | k-pacer `q = k rem/(rate (T-t))` or front-fraction grid incl. host (uniform) and `+front` |

Skip action, declared per host: on gated (adaptive range) a skipped event is *unrecorded*, because
a recorded low-q event sets `wmax = 1/q`. On DISCERN (fixed range `c = 1/pi_min`) a skipped event is
recorded with `q = pi_min`. The ablations show the opposite choice is worse on both hosts:
C2-floorskip is +5.8 vs C2, and C6@discern-unrecorded is ±0.3 vs C6@discern.

## Validity, per candidate

* **C1, C2, C5, C6 (gated MOPE host).** `q` is predictable: it uses released labels, the pending
  count, budget, t and the predictions of event t, never the label of event t. `wmax_t = 1/q_t`
  holds exactly, so every increment satisfies the Lemma 1 range. Unrecorded events are chosen by a
  predictable coin, which is optional skipping of the hedged wealth process. Under the pointwise
  promotion null `E[l0-l1 | F_{t-1}, preds_t] <= 0`, each recorded factor has conditional mean
  <= 1, so Ville applies at level alpha. Caveat: under non-stationary alternatives the CS averages
  over *recorded* events, not all events.
* **C4 and C6@discern (PrPl-EB, `c = 4`).** `q` is clamped to `>= pi_min = .25`, so
  `|Z| <= c`. `q` is predictable, and the WSR theorem needs only predictable lambda and bounded
  increments.
* **C3 (QSG).** Evidence is query-conditional with weight one, so any predictable `q` is valid for
  the QCE null. This is unchanged from QSG.
* **Not covered.** The F5 Markov-dependence null is outside every one of these nulls. Its rates
  below are empirical only.

## Tuning (dev seeds only; declared values)

Objective: the mean over the 10 screening regimes of mean net cost, using 20 seeds at
DEV_SEED_BASE. The grids and scores are in `tuning.json`, and the selected values are in
`tuned.json`.
gated pacing: k=6. discern pacing: k=1.5. C1 kappa=2. C2 gamma=3, zeta=.25. C3 f=1, tau=.5. C4
k=2, beta=.5. C6 f2=.75. C6 inherits C2's gamma and zeta; its f2 was re-tuned after those were
fixed (stage 2, `tune3`).

## Screen (dev, 10 regimes x 20 seeds = 200 pairs; mean net, lower is better)

The full table is in `contrasts_screen1.json` / `screen1.json(.md)`. Pooled paired differences are
candidate minus comparator, [95% CI].

| | mean net | vs host | vs +front | vs tuned pacing | vs QSG |
|---|---|---|---|---|---|
| C1 | 417.9 | -0.05 [-.09,-.02] (host=+front) | = | +0.1 [-2.5,2.7] | +6.1 [3.0,9.2] |
| C2 | 414.6 | -15.8 [-21.5,-10.2] | -3.4 [-5.2,-1.6] | -3.2 [-6.4,-0.05] | +2.8 [-0.9,6.4] |
| C3 | 411.8 | 0.0 (= QSG) | -6.2 | -3.4 [-5.9,-1.0] (QSG-r25) | 0 |
| C4 | 427.0 | -0.1 [-1.1,1.0] | -6.2 [-9.4,-3.0] | +0.2 [-2.3,2.6] | n/a |
| C5 | 415.0 | -15.4 | -2.9 [-4.6,-1.2] | -2.7 [-5.9,0.4] | +3.3 [-0.2,6.7] |
| C6 | 416.2 | -14.2 [-19.6,-8.9] | -1.8 [-3.7,0.2] | -1.6 [-4.7,1.5] | +4.4 [0.9,8.0] |
| C6@discern | 429.0 | +1.9 [-1.2,5.1] | -4.2 [-6.3,-2.0] | +2.2 [-0.6,4.9] | n/a |

Reference means: gated_adaptive_range 430.4, +front 417.9, gated pace_tuned 417.8, QSG 411.8,
discern_design_floor 427.1, discern pace_tuned 426.8, xu 422.0, SMCS 418.7, never-switch 422.3.

**Gain source (C2 vs +front, dev).** Net -3.39 = label cost -2.60 + decision cost -0.79.
* Nulls and hopeless cases account for most of it. F0_null, F5_dep_null_r8 and F1_late_800 each
  gain -6 to -7, all from labels: C2 uses 68/64/41 labels where +front uses 200/184/178.
* Reserve allocation. On F9_highdis C2 gains -7.8 in decisions: budget no longer runs out
  (`exhaust_t` 2000 vs 557), and it promotes in 0.20 of seeds vs 0.10.
* No earlier deployment: median first_deploy is not earlier anywhere.
* Pending credit does nothing. `max_pending` is unchanged (it is set by delay x disagreement
  rate). C1's credit never fires at kappa >= 2, and at kappa = 1 it costs +2.4.

**C6 ablation.** Deadline value and two-stage both *add* decision cost on F0_better and F6_delay400.
On S_delay800 the deadline saves labels (-2.2 vs +front). Net: C6 - C2 = +1.6.

**Null promotion.** On dev (20 seeds), every candidate has 0.00 on F0_null. Gated variants have
0.10 on F5_dep_null_r8, the same as +front. With 300 seeds at base 2026110513 (check only):

| | F0_null | F5_dep_null_r8 |
|---|---|---|
| C2 | 2/300 = .007 (Wilson up .024) | 18/300 = .060 (up .093) |
| C5 | .007 (.024) | .063 (.097) |
| C6 | .007 (.024) | .057 (.089) |
| gated_adaptive_range+front | .007 (.024) | .073 (.109) |

**Held-out descriptive check.** 20 seeds at 2026110513, the same 10 regimes, not used for tuning
(`contrasts_heldout_check.json`):
* C2 vs +front +0.5 [-2.2,3.1]. The dev gain does **not** replicate. Null savings replicate
  (-6.4, -5.9, -7.7), but on F0_better@B100 C2 loses +24.4 [6.3,42.6] (promote .50 vs .70). The
  gamma=3 shadow price throttles exactly when the budget is tight.
* C6 vs +front -1.7 [-4.3,0.9]; vs tuned pacing -3.5 [-6.1,-0.9]; vs C2 -2.2 [-4.4,0.0]; vs QSG
  +2.6 [-0.6,5.7]. On B100 C6 also loses (+15.6).

## Dispositions

* C1: SCREENED_NEGATIVE. At the tuned kappa it is identical to `+front`, and the aggressive
  setting is harmful. Pending labels rarely settle a gated verdict: the betting CS narrows slower
  than the 1/sqrt(n) extrapolation.
* C2: SCREENED_PROMISING (weak). It saves labels on null and hopeless streams at no false-promotion
  cost, but the overall dev gain did not hold on fresh seeds, and it fails under a tight budget.
  Next: make the price budget-tightness-safe (cap gamma, or set the price from B/(D T)), then
  re-screen B100/B400 on fresh seeds.
* C3: SCREENED_NEGATIVE. Calibration selected "no split" (f=1), which is QSG. Every protected
  split costs 2 to 6.
* C4: SCREENED_NEGATIVE. It ties both its host and the tuned pacing baseline. Corrected DISCERN is
  limited by the event clock (lam_max) more than by labels.
* C5: SCREENED_NEGATIVE. It is no better than C2 (+0.5).
* C6: SCREENED_PROMISING (weak) on gated, the best gated variant on held-out seeds, though not
  significantly better than +front. The transfer to DISCERN is negative (+1.9 vs host).
* Neither candidate beats QSG (internal) on mean net. Against the per-regime best certified
  published method, C2 wins 4 regimes (nulls, F1_late, S_delay800) and loses F3_reversal.

Assessment: **pivot.** The economics in Family C mostly buys label-cost savings of about 6 to 7
units per null episode. It does not repair certification latency, because the gated host is
information-limited at B=200 (+front exhausts its budget before certifying in about 30% of
F0_better seeds). It is still worth carrying a budget-safe C2/C6 price as an attachable
label-saver on top of a stronger evidence engine (QSG/QCE). It is not a standalone contribution.

## Reproduce

```
uv run python scripts/sota_sprint/screen.py --regimes $R10 --policies CONTROL_never_switch,gated_adaptive_range,gated_adaptive_range+front,discern_style,discern_design_floor,discern_design_floor+front,gated_deployment+QCE+front,xu_acquisition_only,SMCS+retain-incumbent,QSG,model_picker_adapter,economic_replacement --seeds 20 --workers 3 --out outputs/sota_sprint/C/comparators
uv run python scripts/sota_sprint/screen.py --regimes $R10 --policies <48 grid policies> --seeds 20 --workers 3 --out outputs/sota_sprint/C/tune   # tune2, tune3 likewise
uv run python scripts/sota_sprint/fam_c.py tune ...  (see tuning.json "note")
uv run python scripts/sota_sprint/screen.py --regimes $R10 --policies C1,C2,C3,C4,C5,C6,C6@discern,gated_adaptive_range+pace_tuned,discern_design_floor+pace_tuned,C1-uniformbase,C2-noadapt,C2-floorskip,C6-no_deadline,C6-no_shadow,C6-no_two_stage,C6@discern-unrecorded,C4-style,QSG-r25 --seeds 20 --workers 3 --out outputs/sota_sprint/C/screen1
uv run python scripts/sota_sprint/analyze.py outputs/sota_sprint/C/screen1 outputs/sota_sprint/C/comparators --candidates C1,C2,C3,C4,C5,C6,C6@discern --hosts C1=gated_adaptive_range+front,C2=gated_adaptive_range,C3=QSG,C4=discern_design_floor,C5=gated_adaptive_range,C6=gated_adaptive_range,C6@discern=discern_design_floor --out docs/sota_sprint/family_c/screen1.json
uv run python scripts/sota_sprint/fam_c.py report outputs/sota_sprint/C/screen1,outputs/sota_sprint/C/comparators,outputs/sota_sprint/C/tune,outputs/sota_sprint/C/tune2 docs/sota_sprint/family_c/contrasts_screen1.json
uv run python scripts/sota_sprint/screen.py --regimes F0_null,F5_dep_null_r8 --policies C2,C5,C6,gated_adaptive_range+front --seeds 300 --seed-base 2026110513 --workers 3 --out outputs/sota_sprint/C/null300
uv run python scripts/sota_sprint/screen.py --regimes $R10 --policies C2,C6,gated_adaptive_range+front,gated_adaptive_range+pace_tuned,QSG,xu_acquisition_only,SMCS+retain-incumbent,discern_design_floor,CONTROL_never_switch --seeds 20 --seed-base 2026110513 --workers 3 --out outputs/sota_sprint/C/heldout_check
```
`R10=F0_better,F9_highdis_better,F0_better@B100,F7_near_better,F6_delay400_better,S_delay800_better,F0_null,F5_dep_null_r8,F1_late_800,F3_reversal_800`
