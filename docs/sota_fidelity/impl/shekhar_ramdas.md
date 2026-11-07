# Implementation: Shekhar & Ramdas RCS-Detector (ICML 2024)

Status: implemented 2026-11-06, NOT yet registered in `bench.py` / `suite.py` (lead session does that after review).
Decision record: `LEDGER.md` (IMPLEMENT). Spec/check: `specs/` and `checks/shekhar_ramdas_cs_change_detection.md`
(check overrides spec).

## Files

- `scripts/promising_directions/sota/competitors/shekhar_ramdas.py`
- `tests/sota_fidelity/test_shekhar_ramdas.py`

## What was built, and tier

| Class | Tier | Source tie |
|---|---|---|
| `HoeffdingCS` | T2 | Appendix C (P14) / Section 2.4 (P6): midpoint `sum lam X / sum lam`, half-width `(log(2/a)+sum lam^2/8)/sum lam`; `lam_i = min(1, sqrt(8 log(2/a)/(i log(i+1))))` (main, default) or `i(i+1)` (`schedule="appendix"`); Remark 1.5 running intersection; clipped to [0,1]. |
| `RCSDetector` | T2 | Definition 2.1 (P3): one CS per start `m` (uses `X_m` onward; no skipped observation, no pseudo-weight), stop when `cap_m C^(m)_n` (with `C^(0)` = `[0,1]` or Theta0) is empty. `level="constant"` (paper default) or `"spending"` (Remark 2.5, level `1-6a/(pi^2 m^2)`). Optional `window` (Remark 2.3). Vectorised state; tests assert CS `m` equals a scalar `HoeffdingCS` started at `m`. |
| `ShekharRamdasDeploymentAdapter` | T3 | Partitioned RCS promotion trigger (Theta0 = `{E[Y] >= 1/2}`) then a fresh partitioned RCS rollback trigger (Theta0 = `{E[Y] <= 1/2}`, deployed-vs-previous). Table name: "Shekhar-Ramdas RCS, common-contract adapter (T3)". Not the authors' algorithm. |

## Deviations

Native core: two printed schedules disagree (both capped at 1; main default, appendix selectable); the paper's
Figure 1 width shrinking and every-10/20-step checking are NOT reproduced (guaranteed widths, check every step);
Hoeffding CS only (no betting/EB RCS); official code read but not ported (it skips the first observation, uses a
pseudo-weight of 1 at value 0, lacks the `min(.,1)` cap, defaults to a window of 500).

Adapter: label clock = delivery order (delay honoured exactly, never resorted); simulator losses are 0/1 so
`D = l_challenger - l_incumbent in {-1,0,1}` and `Y=(D+1)/2` needs no extra rescale beyond the stated map
(model 0 = incumbent, 1 = challenger); acquisition = shared `PacedDisagreementAcquisition` under the hard budget
(disagreement-only); alpha from the contract with Remark 2.5 spending in each arm; no cost awareness (`cs`, `cq`
unused by the decision); after rollback the adapter stays on the incumbent (`rearm=False`; `rearm=True` restarts
and then no combined error guarantee holds); delay bounds (Thm 2.7, Prop 2.10) are vacuous at B=200 and are
measured, never claimed.

Null validity scope: the Hoeffding CS is valid for the label-delivery-order filtration when the labelled
subsequence has conditional mean in Theta0 given its past. The pacer's selection uses predictions and past query
counts, never labels, so selection is label-independent. Because only disagreements are queried, the tested mean
is the disagreement-conditional `E[Y | disagree]` (same sign as the all-event gain, different magnitude). Serial
dependence of outcome signs (Atlas `rho > 0`) is outside any theorem; no claim there. Promotion and rollback
are separate tests with separate nulls and bounds.

## Tests

`uv run pytest tests/sota_fidelity/test_shekhar_ramdas.py -q` -> 19 passed (about 19 s). `uv run ruff check` on both files: clean.
Covered: lambda schedules and cap; hand-computed midpoint/half-width; CS started at `n` includes `X_n` and RCS
equals scalar CSs; nested intervals in [0,1]; time-uniform coverage on iid Beta (alpha=0.2, n=300, 1500 reps,
miscoverage <= alpha + 3 s.e.); Remark 2.5 false-alarm bound at the boundary null (alpha=0.5 and 0.05) plus the
pathwise superset property of constant-level alarms; detection under a large change (partitioned and
non-partitioned); Proposition 3.1 Lorden equivalence for singleton Theta0 (40 streams); window never stops earlier;
state round-trip; adapter budget/delay/determinism on a null and a reversal regime; adapter decisions invariant to
events after `t0`; adapter promote-and-rollback on an easy synthetic reversal (qualitative only).

## Stop rule: `joint` (paper) vs `any_excludes` (ShiftLab deviation)

`RCSDetector(stop_rule=...)` and the adapter expose both. `joint` (default) is Definition 2.1. Its proof is for
Problem 1.2 with i.i.d. pre-change data. ShiftLab's null is composite and non-stationary: conditional means can
drift inside Theta0 (Y-mean 1.0 for 60 labels, then 0.5; both in [1/2, 1]). Then CSs started before and after the
drift are disjoint from each other while all stay in Theta0, and `joint` false-alarms. `any_excludes` stops when
one CS, at the current time, is disjoint from Theta0. It uses each CS's instantaneous interval, not its running
intersection: with drifting means the CS covers the lambda-weighted average of the means (inside Theta0 by
convexity), whereas a running intersection over time does not, because early narrow bounds survive a drift (a first
version that used the running intersection false-alarmed at 98% and was corrected). With Remark 2.5 levels the union
bound gives false-alarm probability <= alpha under the composite conditional-mean null. Every `any_excludes` alarm
is a `joint` alarm. For singleton Theta0 both reduce to the Lorden form (Proposition 3.1). Adapter variant names:
`shekhar_ramdas_rcs_t3` (joint, default) and `shekhar_ramdas_rcs_t3_anyexcl`.

New test results (MC): drift stream, alpha=0.05 spending, 300 reps: `joint` false-alarm rate 1.00,
`any_excludes` 0.00 (bound alpha + 3 s.e. = 0.0875). iid boundary null (E[Y]=1/2): both rules within
alpha + 3 s.e. at alpha=0.5 (n=120, 600 reps) and alpha=0.05 (n=200, 300 reps). `any_excludes` detects a mean-0.2
change within 100 labels, and agrees with `joint` for singleton Theta0 (stops no earlier).

## SMOKE (5 seeds, NOT evidence)

Regimes from `scripts/failure_atlas_v2_flq/regimes.py` (T=2000, B=200, cq=0.05, cs=5, alpha=0.05, delay=100),
run through `suite.run_metrics`. `net` = adapter net cost, `never` = net cost of a never-switch incumbent on the
same losses. Promotion/rollback events are label counts on the label clock.

| Regime | seed | first deploy (event) | promoted at label | rolled back | net | never |
|---|---|---|---|---|---|---|
| F0_null | 0 | 426 | 35 | no | 400.0 | 397.0 |
| F0_null | 1-4 | none | - | - | 368/395/391/405 | 358/385/381/395 |
| F0_better | 0-4 | 307, 249, 740, 260, 435 | 21, 12, 58, 14, 29 | no | 349/329/359/341/338 | 454/412/439/449/461 |
| F3_reversal_800 | 0-4 | 307, 249, 365, 260, 435 | 21, 12, 26, 14, 29 | no | 444/410/437/419/435 | 365/333/350/373/372 |

The table is IDENTICAL for `stop_rule="joint"` and `"any_excludes"`, as are the 400-episode null checks below (re-run for both rules on 2026-11-06): on these stationary regimes the earliest CS drives every alarm.

Reading: promotion happens at 12-58 labels on the better regime. On the reversal at event 800 no seed rolled back
within the 200-label budget (labels are mostly spent before the reversal and the rollback RCS has few left), so
the adapter loses to never-switch there. These are 5 seeds with development-free defaults; no conclusion about
power is drawn. Separate null diagnostic (also smoke, not confirmatory; same numbers for both rules): ever-promote rate 2/400 = 0.005 on
`F0_null` and 15/400 = 0.0375 on `F5_dep_null_r8` (serial dependence, no validity claim), against the
`NULL_PROMOTION_BOUND` of 0.0936.

## Registering (lead session)

`extra={"shekhar_ramdas_rcs": lambda T, B, cs, cq, alpha, delay, r:
ShekharRamdasDeploymentAdapter(T, B, alpha, rng=r("shekhar_ramdas_rcs"))}` in `build_suite`; the module inserts its
own `sys.path` entries like the other competitors.
