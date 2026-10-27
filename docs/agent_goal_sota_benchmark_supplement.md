# Supplement to the agent goal: benchmarking against, and trying to beat, the state of the art

**Issued:** 2026-10-27. Read this together with
[`agent_goal_stratified_monitor_phase.md`](agent_goal_stratified_monitor_phase.md), especially
Section 3A, the comparator panel. If anything here conflicts with `AGENTS.md`, the charter, or a
frozen protocol, those win.

---

## 1. Prompt (paste into the agent)

> You are benchmarking our candidate decision-harm monitors against the strongest published
> methods. Your goal is to **beat the state of the art honestly, or show clearly where and why we
> cannot.**
>
> For every registered cell (feedback regime × budget × harm type), first identify the strongest
> applicable published method or composition of published methods. Give it the same information,
> labels, false-alarm level, and betting engine as our candidate. Then test whether our candidate
> beats it by the pre-registered margin.
>
> Before any run, write down a falsifiable **regime map**: where you expect us to win, tie, or
> lose, and the mechanism behind each expected win. Anchor it in the derivations and the G1-style
> analytic pre-screen.
>
> A win counts only on fresh seeds, after null calibration, against the strongest baseline in that
> cell. Ties and losses are results: report them in the leaderboard with the same prominence.
>
> Never strengthen our arm or weaken a baseline through unequal labels, bounds, stake grids, tuning
> seeds, or estimands. If our candidate wins only because it tests a different null (for example
> the stratum-wise intersection null), say so in the claim and also report the pooled-null
> comparison.
>
> Use cheaper subagents for literature reads, paper-to-code audits, boilerplate tests, and run
> babysitting. Keep the regime map, thresholds, and interpretation yourself. Use the RTX 4060 via
> the pinned `uv` environment for stream generation.
>
> Stop at the checkpoint defined in the goal.

---

## 2. What to beat: the incumbent leaderboard by regime

For each regime, the **target** is the strongest applicable baseline (bold). Our candidate is
compared with it, not with weaker arms. "Composed" baselines combine published pieces; we must
beat the composition, otherwise our gain is just that known composition.

| Regime (cell) | Strongest incumbent to beat | Repository evidence so far | What we realistically aim for |
|---|---|---|---|
| R1. Full feedback, pooled eventwise null | **Timans GRAPA** (official) | Our fixed-stake monitor showed no adjusted advantage over Timans | **Non-inferiority only** (no worse than −3 pp detection, equal false alarms). Don't claim a win here. |
| R2. Selective labels, budget ≥ disagreement rate (for example 20%), pooled null | **Gated HT (DISCERN-style) + GRAPA or plug-in adaptive bets** (composed) | Uniform PPI with the correct bound detects 47/60; G1 predicts gating gives 7.5× uniform's growth; the anchor adds nothing when `q_D = 1` | Tie expected. Our ideas give no structural edge when every disagreement is labelled. Report the tie. |
| R3. Selective labels, scarce budget (2–6%), pooled null | **Gated HT + adaptive bets**; also **Xu et al. active betting** and **PPE** | G1: the anchor adds at most 1.23× over gating (ratio of means) | Modest gains at most. Not a headline unless the measured gain is at least 1.5× growth, or +10 pp detection, over the composed incumbent. |
| R4. Localised harm (one or a few strata harmed; pooled mean above `epsilon` but diluted) | **Chugg-style group-wise betting** + gating; **gated pooled** | Not yet measured | **Primary win target for the stratified monitor:** +10 pp detection or 1.5× faster detection at equal labels |
| R5. Mixed-sign harm (pooled mean ≤ `epsilon`, some stratum harmed) | **Chugg-style group-wise betting** (same intersection-type null) | Pooled monitors should be nearly blind by construction | Win against pooled methods is **expected but uses a different estimand**. The real test is against Chugg-style group auditing on the same null. |
| R6. Late onset (≥ 50% of horizon) under a hard label budget | **Horizon-calibrated SR/CUSUM e-detector on gated increments**; started mixtures | 4% detection at 75% onset in the delayed-PPI study (different design) | **Primary win target for the data-efficient e-detector (WP3):** +10 pp at 75% onset or 1.5× lower delay at equal labels |
| R7. Policy change mid-stream (harmful adaptation; disagreement rises from 9% to 42%) | **Paced gated monitor**; Timans on full feedback | Not yet measured | Robustness: no cap exhaustion, and no worse than −3 pp versus paced gating |
| R8. Real live data (EIA CISO/ERCO; plus Binance or NOAA if added) | The **same panel**, on the same streams and label coins | Not yet measured | Validity first (per-path random-orientation null ≤ 5%), then injected-harm detection matching the synthetic regime map |

**Strongest-baseline rule.** In every cell, the incumbent gets the best of: its published
configuration; the same gating, pacing, and correct policy-specific bounds we use; and the same
betting engine (fixed-stake grid up to 1, or GRAPA / plug-in adaptive). A candidate that beats
only the published configuration, but not the equally equipped composition, has not beaten the
state of the art.

---

## 3. How to beat it: mechanisms, each tied to a structural limit of an incumbent

These are the only legitimate sources of advantage we know of. For each, give the incumbent's
limitation, our mechanism, the regime where it should pay, and the ablation that isolates it.

| # | Incumbent limitation | Our mechanism | Should pay in | Isolating ablation |
|---|---|---|---|---|
| M1 | Pooled tests dilute harm concentrated in part of the covariate space | **Stratified evidence**: one e-process per pre-registered stratum, combined by weighted Bonferroni (FWER) or a fixed mixture | R4, R5 | Stratified versus pooled, same engine and labels. `K = 1` must reproduce pooled. |
| M2 | A single global label floor forces a large bound `M(2/q_min - 1)`. Event-level adaptive `q` (Xu et al.) inherits it | **Per-stratum constant bounds** `B_k` from stratum-level label probabilities `q_k`. Valid because the stratum is known before the outcome and `B_k` is constant within it | R3, R4 | Per-stratum `B_k` versus a common `B` on identical paths and labels (a matched-path bound ablation, as in earlier repository work) |
| M3 | Uniform or paced spending wastes labels on low-value strata | **Optimal stratum allocation** `q_k`, derived in closed form from the stratum-wise growth approximations under a label-dollar budget, in both the capped and uncapped regimes | R3, R4 | Optimal `q_k` versus proportional `q_k`, same strata |
| M4 | Uniform spending over time wastes labels before onset | **Data-efficient e-detector**: intensity rises with the SR/CUSUM statistic and with label-free sentinels; skipped events have factor 1 | R6 | DE intensity rule versus uniform or paced, same e-detector |
| M5 | Agreement events carry no information (`Z ≡ 0`) | **Gating** (DISCERN). Use it as the foundation of every arm, ours and theirs | R2–R7 | Already isolated in WP1. **Not our contribution.** |
| M6 | The fixed stake grid caps growth (G1: the best stake sat at the 0.8 cap in most arms) | **A better betting engine** (stakes up to 1; GRAPA or plug-in adaptive) | Everywhere | **Give it to every arm.** It is a fairness requirement, not a contribution. |
| M7 | A PPI anchor with a symmetric bound | **Boundary or interior anchor mixture** | R3 only, when `q_D < 1` | G1 found at most 1.23×. Keep it only as an option inside M2 and M3 arms; don't headline it. |

**Expected contribution, if any:** M1 + M2 + M3 together, meaning stratified evidence with
per-stratum bounds and optimal stratum allocation, for the stratum-wise estimand; and/or M4 for
late onset. Everything else is foundation (M5, M6) or marginal (M7).

---

## 4. Forbidden ways to "win"

- Comparing against an incorrectly bounded baseline (for example the shared 96.9 bound for uniform
  at `q = 0.20`).
- Unequal label budgets or query randomness. Gated arms that underspend must report their spend;
  never give our arm unspent budget the baseline couldn't use.
- Giving our arm a better betting engine, stake grid, or proxy than the baselines.
- Tuning strata, `K`, `q_k`, stakes, or thresholds on development seeds and then reporting them on
  the same seeds. Selection happens on development data; claims come from fresh confirmation
  blocks only.
- Using oracle strata or evaluator-only fields in learner-side decisions. An oracle-strata arm is
  allowed only as an upper reference.
- Silently switching estimands. An intersection-null win must be labelled as such, with the
  pooled-null comparison reported next to it.
- Counting pre-onset alarms as detections; dropping budget-censored streams; choosing cells after
  seeing outcomes.
- Calibrating the stratum-wise null on `stationary` or `benign_nuisance`, which are only
  population-average nulls.

---

## 5. Win definition and leaderboard

**Before the first development run,** freeze the following in the protocol:
- the regime map (Section 2, plus your predicted win, tie, or loss per cell);
- the primary cell for each candidate: R4 for the stratified monitor, R6 for the DE e-detector;
- the margins.

**Default margins:**
- Primary win: ≥ +10 pp detection by horizon, **or** ≥ 1.5× lower censored delay, against the
  strongest applicable incumbent, at equal or fewer labels. Lower 95% paired bound > 0 at
  confirmation.
- Non-inferiority in every other registered cell: no worse than −3 pp detection, with equal
  false-alarm control.
- Validity: null calibration ≤ 5% (simultaneous exact upper bound). Real-data per-path
  random-orientation null ≤ 5%.

**Outcome labels for the report:**
- **Dominates:** primary win and non-inferior everywhere.
- **Regime-specific win:** primary win; a loss in some other cell, reported.
- **Tie:** no primary win.
- **Loss.**

Only "dominates" and "regime-specific win" support a method claim. The rest go into the benchmark
manuscript as findings.

**Leaderboard template** (one per regime; development and confirmation reported separately):

| Arm | Estimand / null | Information (labels, `q`, gating) | Bet engine | Detection (95% CI) | Delay | Labels / $ | False-alarm rate | Fidelity (faithful, adapted, analytic) |
|---|---|---|---|---:|---:|---:|---:|---|
| Strongest incumbent (named) | | | | | | | | |
| Our candidate | | | | | | | | |
| Ablations M1–M4 | | | | | | | | |
| Excluded comparators + reason | — | — | — | — | — | — | — | — |

---

## 6. Order of work, fitting the goal's commit budget

1. Implement the missing panel members (Xu et al. active betting, SR/CUSUM e-detectors, Chugg
   group-wise audit) with paper-to-code audits. About 4–5 commits, already budgeted in the goal.
2. Build the **composed incumbents**: gated + adaptive bets; gated + e-detector; gated +
   group-wise audit. These are arms, not new methods.
3. Write the regime map and margins into each protocol, and freeze.
4. Run the analytic pre-screen of M1–M3 (and M4 in WP3) against the composed incumbents. Stop if a
   pre-screen fails.
5. Run the development grids with all ablations. Then null calibration. Then real-data validity
   checks.
6. Fill in the leaderboards in the checkpoint report: every cell, every arm, every exclusion.
