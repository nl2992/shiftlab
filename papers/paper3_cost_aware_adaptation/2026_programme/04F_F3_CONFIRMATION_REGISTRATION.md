# F3 confirmation registration v1 (locked before any F3 confirmation seed is opened)

Registered 2026-11-15. Methods, configurations, metrics, thresholds and seeds below are frozen at
the commit that adds this file. Any later change defines a new exploratory hypothesis that needs
new independent seeds. This registration is separate from H1-H5 in `04_EXPERIMENT_PROTOCOL.md` and
does not touch their seed sub-ranges or the sealed real group.

## What was seen before freezing (all exploratory)
Design and theorem: `03F_RISK_BUDGET_DESIGN.md`. Dev runs on dev-block seeds only: pilot offsets
20000-20199, dev v1 30000-30999 (`results/riskbudget/dev_summary.json`), tuning offsets 0-5, dev v2
40000-40999 (`results/riskbudget/dev_v2_summary.json`). The frozen arms were chosen after looking
at both dev runs. The six stress regimes (`configs/paper3/regimes_f3_v1.json`) were specified in
03F section 5 before any F3 run; they were built to stress delayed and missing feedback and are
reported separately from the 24 original regimes.

## Frozen objects
- Arms: exactly the specs in `configs/paper3/f3_confirmation_arms_v1.json` (18 arms; no dependence
  on `outputs/`). F3 arms: `f3_pi1_R{12,20,30}` (v1 shield over tuned Wald+cutoff, full sampling,
  delta = 0), `f3v2_R20_blind8` (v2, full sampling plus optional blind rounds), `f3v2d_R{20,30}`
  (v2, label-paced sampling, delta = .05). Comparators: never, tuned wald_cut, cusum, gate_wald,
  cusum_rb_h{4,8}, stoploss_R{12,20,30}. Ablations at R = 12: no pending reserve, no rollback
  reserve, no confidence width.
- Code: `src/shiftlab/paper3/riskbudget/`, runner `scripts/paper3/riskbudget/run_confirm.py`,
  analysis `scripts/paper3/riskbudget/analyze_confirm.py` (the statistics below, as coded).
- Regimes: the 24 of `regimes_v1.json` plus the 6 of `regimes_f3_v1.json`; T = 300.
- Seeds: `seeds_for("confirmation", 1000, 500000)` = 5303500000-5303500999, unopened before this
  commit and disjoint from H1 (offsets 0-99), H2 (100000+), H3 (200000+), H4 (300000+).
  Policy seed = tape seed. The run is made once (`--open-confirmation` refuses to overwrite).
- Harm: sup_t H_t, H_t = k N_t - sum_{s<=t} a_s Z_s (`riskbudget.metrics`); a violation is
  sup_t H_t > R + 1e-9. Intervals: Wilson 95% per regime (n = 1000); Delta J by seed-cluster
  bootstrap (10,000 resamples) of the equal-weight regime mean.

## Hypotheses and decision rules
**C1 (deterministic budget).** `f3_pi1_R12`, `f3_pi1_R20`, `f3_pi1_R30`, `f3v2_R20_blind8`: zero
violations in all 30 regimes. SUPPORTED iff the total count is 0. (Theorem 2 predicts exactly 0;
one violation refutes the implementation or the proof.)

**C2 (sampled budget).** `f3v2d_R20`, `f3v2d_R30` (delta = .05): SUPPORTED iff the Wilson upper
bound of the violation rate is <= .05 in every regime.

**C3 (comparators break the budget).** For each of wald_cut, cusum, gate_wald, cusum_rb_h8 and
stoploss_R20, the exceedance rate of R = 20 in its worst regime has Wilson lower bound > .05.
SUPPORTED iff this holds for all five. Known in advance: the worst regime in dev was
`dropout_adverse` for most arms, a stress regime.

**C4 (price of safety).** Pooled over 30 regimes: Delta J(`f3_pi1_R20` - wald_cut) has CI upper
bound < 3% of J(wald_cut), and Delta J(`f3_pi1_R20` - never) has CI upper bound < 0. SUPPORTED iff
both. Secondary, descriptive: Delta J(`f3v2d_R30` - wald_cut) (dev: +0.30).

**C5 (gain under adverse feedback).** Pooled over the 6 stress regimes, Delta J(`f3_pi1_R20` -
wald_cut) has CI upper bound < 0. The original-24 Delta J is reported next to it (dev: +2.55,
i.e. worse there).

**C6 (reserves are needed).** Each ablation at R = 12 has a worst-regime violation rate with
Wilson lower bound > .05. SUPPORTED iff all three.

## Not claimed
No superiority in mean cost over tuned Wald+cutoff (dev shows F3 is 0.3-2.8% worse pooled). No
claim for real data, for actions that change outcomes, or for the label-saving value of sampling
at R <= 20. C1-C6 are reported in full whatever the outcome, with the descriptive table of every
arm (J, labels, q95/q99/max harm, deployed fraction).
