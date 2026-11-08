# PAVE on the episode_front engine (Track C decisive follow-up)

Date 2026-11-08, branch `research/methods-recovery-2026-11-07`. Development evidence only. Script
`scripts/methods_recovery/pave_ef.py`; outputs (gitignored) `outputs/methods_recovery/pave_ef/`.

## Question

Doc 41: on the frozen DSS-shell evidence PAVE beats the best matched simple schedule by 2.2% of uniform, but
native `episode_front` (uniform calendar, own evidence/decision engine) is 2.2% cheaper than DSS-shell + uniform
and ties PAVE. Does PAVE's acquisition still help when it drives `episode_front`'s own engine (a drop-in test)?

## Arms (all 27 long-delay cells; identical evidence/decision engine = `EpisodeComposition("front")`)

- `episode_front` native: uniform calendar `uniform_calendar(T,B,d)`; comparator.
- `pave_ef`: `EpisodeComposition("front")` with the request rule replaced by PAVE's governor, unchanged:
  `PaveMethod._query` / `_rollout` / `_posterior` / `pending_capacity` / `_b_eff` with `PAVE_TUNED`
  (pending on, deadline on, reserve off, kappa .1, q .03), active under the same delay gate `d >= 2T/(B+2)`
  (always on in these cells). The engine's promotion logic (started-mixture e-process at alpha spent entirely on
  episode 0, economic check, window-mean rollback with no further alpha) is untouched.
- `pave_ef_nopendinfo`: same, pending labels hidden from the rollout only (adaptive capacity kept).
Port notes (documented mismatches, no re-tuning): PAVE's rollout evidence model (Normal belief on benefit,
reachability factor `INC*(labels)/log-wealth-needed`) is kept as is; it reads the engine's `ep_labels`/`post`,
window `m = max(3, B//8)`, and the e-process log-wealth through `ep.log_e_value` (the `.proc` alias of the DSS
shell does not exist here). After a rollback episode j >= 1 `episode_front` has no e-process (alpha 0), so the
promotion-reachability factor is set to 0 for those labels (a tiny alpha is substituted in the rollout only).
DSS's spend-pace cap is inherited as in PAVE (`acquisition.burst_frac` .1, `pending_cap` 2 when `pending` off).
The rollout therefore mismatches the engine; this is the intended drop-in test.

## Cells and seeds

Same 27 cells as doc 41 (`GATE_ON_50` x d in {50,100,200}). Seeds `pave_ef_eval` 102100000 + 100 x cell_index + k,
60 per cell (registered before running). PAVE has no tuning. Null: the 9 GAVE-R null-grid cells with d >= 50
(`dep_rho{0,.5,.8,.95}_bt{.05,.1}_d50`, `f1null_d50_b0.05`), 500 streams each, seeds `pave_ef_null`
102200000 + 500 x cell_index + k; arms `pave_ef`, `episode_front`; false promotion = `fp_regime > 0` (as in the
WP5 runner), Clopper-Pearson 95% UCB.

## Registered decision rule (written before any run)

Estimand: pooled J/T over the 27 cells, equal cell weights, paired bootstrap (4000 resamples over seeds within
cells), differences as % of native `episode_front` pooled J/T.
- ADVANCE PAVE as the Track-C candidate iff `pave_ef - episode_front <= -2%` with 95% CI excluding 0 AND
  `pave_ef - pave_ef_nopendinfo < 0` with CI excluding 0.
- STOP iff `pave_ef` is within 1% of `episode_front` (advantage < 1%) or worse.
- Otherwise WEAK.
Per-delay contrasts, labels used, arrival-before-T, pending inventory and the null false-promotion table are
descriptive. The null check is a screen (500 streams/cell; dependence cells are outside the e-process's claimed
validity), not a validity result.

(Results are filled in after the run.)

## Amendment (coordinator, 2026-11-08, written before any pave_ef eval result was inspected)

**Confound.** `pave_ef` builds `EpisodeComposition("front")` with the DSS evidence spec (`_p` →
`comp.dss_spec(4, True)`), whereas native `episode_front` is built by
`fa.make_method("episode_front", fa.bernoulli_grid_spec(), cfg)`. `pave_ef − episode_front`
therefore changes both the acquisition **and** the evidence spec.

**Added matched comparator `ef_dss`.** This is the identical `PaveEF` engine and spec with PAVE
switched off: the delay gate is forced off, so the engine's own uniform calendar is used. It runs
on the same eval seeds and cells (`scripts/methods_recovery/pave_ef_matched.py`).

**Amended rule.** ADVANCE requires every one of:
1. the registered conditions;
2. `pave_ef − ef_dss` ≤ −2% of `ef_dss` J/T, with paired-bootstrap 95% CI excluding 0, pooled
   over the 27 cells.

STOP if `pave_ef` is within 1% of `ef_dss` or worse. Native `episode_front` is reported as before.
