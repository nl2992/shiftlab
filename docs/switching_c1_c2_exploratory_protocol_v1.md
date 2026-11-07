# Exploratory protocol: C1 and C2 against R6 baselines on one shared harness

**Date:** 2026-10-30. **Status:** EXPLORATORY, development-only (R4). Written before any run of the
new code. No novelty, theorem, efficacy or confirmatory claim follows from anything here. Code:
`src/shiftlab/dive/switching_explore.py`, `scripts/run_switching_c1_c2_exploratory.py`,
`tests/test_switching_explore.py`. Results: `docs/switching_c1_c2_exploratory_results_v1.md`.
Outputs (git-ignored): `outputs/switching_c1_c2_exploratory_v1/`.

## Purpose and non-claims

Under the 2026-10-30 acceptance revision (R1-R6), C1 (delayed-HMM predictive confidence-set gate with
a new query rule) and C2 (promotion-versus-reversal-monitor budget split) were reopened. This
protocol registers one runnable harness to see whether either shows any signal against strong,
matched-access baselines. Everything is labelled exploratory: seeds, cells, thresholds and
hyper-parameters below were fixed before the first run, but tuning of the single C2 hyper-parameter
`rho` uses development seeds only, and no confirmatory or familywise testing plan is registered. The
killed one-step sign-ambiguity VOI score is not used. The exact two-law solver is a reference
only (R1). Oracle truth is evaluator-side only (R5).

## Contract (implemented exactly)

* Horizon `T`, hard query budget `B` (integer), fixed release delay `d >= 1`, query cost `c`,
  switch cost `s`, hurdle `h >= 0`, level `alpha`.
* Two frozen policies, incumbent `f0` and candidate `f1`. At round `t = 1..T` a common outcome is
  realized and gives losses `l0_t, l1_t in [0,1]` (after a train-only scale; clipped). The paired
  difference is `D_t = l1_t - l0_t` in `[-1,1]`. Negative `D` means the candidate is better.
* **Event order inside round t:** (1) labels whose release round equals t are delivered, in event
  order; (2) the learner chooses the deployed action `a_t in {0,1}` and a query flag `q_t`, using
  only delivered labels and its own past (predictable); (3) the outcome is realized and `a_t` pays
  `l_{a_t,t}`.
* `D_t` is observed only if `q_t = 1` and only at the start of round `t + d`. A query made at
  `t` with `t + d > T` is never released (the harness still charges it; the methods avoid it).
* The budget is counted at request time and includes pending queries. A request beyond `B` raises
  an error in the harness (no silent truncation).
* Net cost = `sum_t l_{a_t,t} + c * (#queries) + s * (#switches)`, with `a_0 = 0` (incumbent), so a
  first promotion is a switch.
* **False promotion (evaluator-side).** A promotion is a transition `a_{t-1}=0 -> a_t=1`. It is
  false if the current-regime conditional mean of `D` at round `t` is `>= -h` (candidate not
  beneficial in the regime in force at `t`). Reported per run as "any false promotion" and as a count.
  A second evaluator-side flag uses the true-model filtered predictive mean (the object C1's
  coverage statement is about) on HMM-sampled cells. The true parameters, regime path and conditional
  means live only in the evaluator-side `Truth` object; method code receives only `(round,
  released-label list)`.
* No oracle truth, no unreleased label, no unqueried label and no loss of the not-deployed policy
  other than via a released `D` is ever passed to a method.

## Methods

Shared defaults: `alpha = 0.1`; pending-query cap for adaptive query rules = 2; economic check for
every e-process or window promotion = (remaining rounds) x (estimated per-round benefit) `> s`;
benefit = `-D`.

**C1: delayed-HMM predictive confidence-set gate.**
Finite family of 2-state recurrent HMMs, state 1 = candidate-favourable, with Bernoulli emissions
for `D = 1 - 2Y` (synthetic) or Gaussian emissions on `D` (real). Parameters: switch rates
`a = P(0->1)`, `b = P(1->0)`, state emission means, noise level. The family is a fixed grid declared
before running (synthetic: `a,b in {0.01,0.03,0.1,0.25}` and emission pairs
`(P(Y=1|S=0),P(Y=1|S=1)) in {(.02,.98),(.1,.9),(.3,.7),(.5,.5),(.3,.3),(.1,.1)}`, 96 models; real:
fitted by EM on the calibration block, then perturbed, see Real data). The likelihood of the
released transcript is the HMM forward likelihood in event order with pending and unqueried
outcomes marginalized (`switching_hmm_predictive_cs_candidate_v1.md`). With uniform prior `pi`,
`E_t(theta) = sum pi(theta') L(theta') / L(theta)` and `C_t = {theta: E_t(theta) < 1/alpha}`.
Let `ben_t(theta) = -E_theta[D_t | released]` be the filtered current benefit, `lo`/`hi` its
min/max over `C_t`, and `G_lo` the min over `C_t` of the remaining-horizon benefit.
* Promote when `a_{t-1}=0`, `lo > h` and `G_lo > s`. Roll back when `a_{t-1}=1` and `hi <= h`
  (symmetric hurdle; no economic test on rollback). Otherwise hold.
* Query rule (not the killed VOI score): query if (i) `lo <= h < hi` (set straddles the hurdle) or
  (ii) no query for `G = max(d+1, ceil(4T/B))` rounds (keep-alive), subject to pacing
  `used < 1 + floor(2 B t / T)`, pending `< 2`, `used < B`, and `t + d <= T`.
* Coverage statement being exercised: on the event `theta* in C_t`, a promotion implies
  `mu_t(theta*) < -h`; so `P(any promotion with predictive mean >= -h) <= alpha` under a correct
  family. This is the standard Ville argument and is not claimed to be new. It is checked by the
  evaluator-side predictive flag, not assumed.

**C2: reversal-budget split.** A fraction `rho` of `B` (rounded down) is the gate pool; the rest is
the monitor pool. Gate: the repository's `BoundedMeanEProcess` (`src/shiftlab/dive/eprocess.py`,
bound `1+h`, default stakes) on `X = -D - h`, whose null is `E[D | past] >= -h`; one fresh process per
episode `j` with level `alpha_j = alpha 2^{-(j+1)}` (the repository's geometric alpha spending); updates
at release, event order; promote on alarm plus the economic check. Gate queries are uniformly paced
from the gate pool. Monitor (after promotion): queries uniformly paced from the monitor pool;
one-sided Page CUSUM on labels with event time at or after the promotion, `S <- max(0, S + D - ref)`,
`ref = (mean of the last <= 10 gate-episode D - h)/2`, alarm at `S >= 2`, then roll back and start episode
`j+1`. When the monitor pool is exhausted the policy keeps its action (declared; no free rollback).
`rho in {0.25, 0.5, 0.75}`, swept on development seeds only; `rho*` minimizes mean cost per round
across all development cells and is reported as "C2". All three are shown in appendix tables.

## Baselines (R6; each adapted, labelled "adaptation")

1. `no_switch`: always `f0`, no queries.
2. `periodic_mean`: uniform calendar of `B` queries; every `P = max(d+1, T//20)` rounds choose `f1` iff the mean `D` of
   the last `m = max(3, B//8)` released labels is `< 0`.
3. `episode_geo`, `episode_equal`, `episode_front`: fixed uniform calendar of `B` queries; per-episode fresh
   bounded-mean e-process with spending `alpha 2^{-(j+1)}`, `alpha/(B+1)`, and `alpha` for `j=0` only; rollback if
   the window mean benefit of the last `m` post-promotion labels `<= h` (needs `>= 3`). Adaptation of
   `compare_switching_episode_composition.py` (which uses a one-label test and an HMM forecast); the
   "optimized" composition is the best of the three, reported per cell.
4. `allonset_edetector`: uniform calendar; uniform mixture over onset query-index of bounded-bet processes (stake
   `0.5`); promote once at `1/alpha`, never roll back (adaptation of `evaluate_switching_uniform_safe_baseline.py`).
5. `dal_restart`: half the budget uniform background queries, half reserved for re-evaluation bursts of
   `n_b = max(3, ceil(B/10))` consecutive queries; two-sided CUSUM (allowance 0.25, threshold 3) around the post-burst
   mean triggers a new burst; action after a burst = `f1` iff benefit `> h` and economic check. DAL-style adaptation, not a
   reproduction of the published method.
6. `pacing_bernoulli`: hard-budget pacing, Bernoulli(`B/T`) queries with hard cap; exponentially weighted mean of
   released `D` (decay 0.9 per label); promote if benefit `> h` and economic check, roll back at benefit `<= h`.
   A generic pacing comparator, not the repository's pprm/mixture pacing family.

Not implemented here: the Gong-Zhang, Qiu et al. and Ryabchenko et al. delayed wrappers, and the online FWER
comparator. This is a gap in R6 coverage and is carried into the results as a limitation.

Evaluator-side references (never methods): `always_f1` (also a no-query policy), `regime_clairvoyant` (follows the
true better regime with zero queries, pays switches; synthetic only), and the exact two-law oracle on tiny cells.

## Cells

**Tiny oracle cells (reference only, R1).** Registered recurrent HMM, symmetric transitions 1/4, emissions
`P(Y=1|S)=(1/50, 49/50)`, prior 1/2, `alpha = 1/10`, `c = 1/100`, `s = 1/10`; `(T,B,d) in {(6,3,1), (6,3,2)}` and
`(7,3,2)`, `(8,4,2)` if the solver finishes inside 60 s each. The oracle value is the repository's
`CausalSwitchingGame.solve()` recovered-policy cost (numerical, no dual certificate). Methods are evaluated by Monte Carlo on the same
generative model (5000 paired seeds). Loss convention matches the solver: `l0 = Y`, `l1 = 1 - Y`, so `D = 1 - 2Y`. A null cell
(`P(Y=1)=1/2` iid, the causal-null boundary) gives each method's false-promotion frequency against the solver's `alpha`.

**Synthetic CPU cells.** `T in {200, 1000}`, `B in {10%, 25%} of T`, `d in {1, 10}`, `c = 0.01`, `s = 0.1`, `h = 0.1`
(64 cells = 8 scenarios x 8). Scenarios (`P(Y=1|S)` for state 0 / state 1, `D = 1 - 2Y`):

| Scenario | Regime path | Emissions |
|---|---|---|
| `persistent_std` | HMM `a=b=0.03` | .1 / .9 |
| `fast_std` | HMM `a=b=0.25` | .1 / .9 |
| `persistent_weak` | HMM `a=b=0.03` | .3 / .7 |
| `null_boundary` | HMM `a=b=0.03` | .5 / .5 (mean `D` = 0, inside the false-promotion region) |
| `null_harm` | HMM `a=b=0.03` | .3 / .3 (candidate always worse) |
| `late_onset` | scripted: state 0 until `0.6T`, then state 1 | .1 / .9 |
| `reversal` | scripted: state 0, then state 1 on `[0.2T,0.55T)`, then 0 | .1 / .9 |
| `offgrid_hmm` | HMM `a=b=0.05` | .15 / .85 (parameters not in the C1 grid) |

All HMM cells use prior `P(S_0=1) = 1/2`. The scripted cells are not draws of the C1 model class; that is the point
of the stress. The `offgrid_hmm` cell is the misspecification check on C1's coverage.

**Seeds.** Development seeds `0-7` (C2 `rho` selection and debugging); evaluation seeds `1000-1029`, paired across
methods (same stream). Unit of analysis = seed total; seeds are independent streams, so a paired-t interval over
seeds is dependence-appropriate within a cell. Rates use Wilson intervals.

## Metrics

* **Primary:** net-cost difference `C - best_baseline` per cell, where `best_baseline` is the baseline with the lowest
  mean evaluation cost in that cell (post-hoc best, which is conservative against C), with paired-t 95% interval over
  seeds, and its aggregation (mean per-round difference, count of cells with interval below/above zero). `C` in
  {C1, C2(`rho*`)}.
* **Secondary:** false-promotion frequency (regime-based and predictive-mean-based), queries, pending-at-end queries
  never released, switches, decision loss, query and switch costs.
* Never reported alone: lower label spend.

## Real data (development windows only; imposed timing and costs)

Rules: chronological order; forecasters, feature standardization and the loss scale are fit on the first 40% of a
series; the next 10% is a calibration block used only to declare C1's HMM family (EM) and nothing else; the replay
window starts at 50% of the series and uses at most 3000 consecutive rounds; **rows after the 80% mark are never
read into the evaluation (EIA, ELEC2) and CRSP stops at 2019-12-31, before the exposed 2020-2025 test split.** Release
delay `d in {1,10}` rounds, `B in {10%,25%}` of `T`, and two imposed cost settings `(c,s) = (0.005,0.05)` and `(0.02,0.2)`,
`h = 0`, are imposed assumptions, not observed facts; none of the streams has an observed label-release clock.

| Stream | Source | `f0` / `f1` | Loss |
|---|---|---|---|
| `eia_nyis` | `data/processed/eia/066f854744aea721eae5` (NYIS hourly demand, next hour) | persistence / ridge on `[D,DF,NG,TI]` + hour-of-day | squared error / train q99 |
| `elec2` | `data/raw/elec2/electricity-normalized.arff`, **file row order** (not a verified clock; `date`,`day` dropped per the ELEC2 audit) | logistic regression / histogram gradient boosting | 0/1 |
| `crsp_subset` | `data/processed/crsp_ciz_next_day/5211412140dcb86f08f9`, up to 10 fixed large-cap PERMNOs (10107, 14593, 12490, 11850, 22111, 55976, 47896, 66181, 18163, 22592; retained only if present for the full 2000-2019 range), columns `dlycaldt, permno, features, target, split`, rows with `dlycaldt < 2020-01-01` and `split != test` | train-mean constant / ridge on the 12 panel features | per-date cross-sectional mean squared error / train q99 |

CRSP is a retrospective stress test; its close-time ordering and release delay are assumptions, and execution
costs are not modelled. EIA hourly event time is not a publication time. Checksums: `observations.parquet` SHA-256 is
compared to each version's `dataset_manifest.json`; for ELEC2 the SHA-256 is recomputed and compared to the value
recorded in `papers/shiftguard_unified/elec2_candidate_audit.md`. A stream failing a check is dropped and reported. For the real C1 family, a 2-state Gaussian HMM is fit by EM on the
calibration block's `D`; the grid is the cross-product of centers `{mean of calibration D, 0}` x scales `{0.5,1,1.5}` applied to
the fitted state means, plus two static models, noise `sigma x {0.8,1,1.25}`, switch rates `x {0.5,1,2}` (clipped to
`[0.002,0.5]`). There is no oracle, so only realized net cost versus baselines, queries and switches are reported, with
moving-block-bootstrap (block 50 rounds, 500 resamples) intervals on the per-round cost difference to the strongest
baseline. References: `always_f0`, `always_f1`, hindsight best constant. If a dataset proves awkward it is dropped and the reason recorded.

## Verification and run discipline

CPU-fast tests cover: hard budget never exceeded including pending; no use of unreleased or unqueried labels (decisions are
invariant to them); deployed action predictable; oracle truth not visible to methods; false-promotion sanity on a small null cell.
Order: tests -> ruff -> smoke run -> full grid (target below 30 minutes CPU). `results.json` records git revision, dirty flag,
SHA-256 of the three new files, the full config, seeds and data checksums. Failures and negative results are reported.

## Deviation log

Recorded before the full grid was launched (after development smoke checks on seeds 0-5 only; none of the
evaluation seeds 1000-1029 had been run):

1. **Gate e-process.** The first smoke check used the plain per-episode `BoundedMeanEProcess` for C2 and the
   `episode_*` baselines. In recurrent-regime streams a long unfavourable phase crushes the plain product and the
   gate never promotes (all e-process methods stayed at the no-switch cost). Both now use the repository's
   `VectorizedStartedMixtureEProcess` (`eprocess.py`) with at most 32 prespecified, evenly spaced start
   positions in label index. This is a fixed mixture, so the conditional-mean-null validity argument is
   unchanged, and it makes the baselines stronger too. The protocol text above says `BoundedMeanEProcess`; read
   it as "started mixture of bounded-mean e-processes with fixed starts".
2. **C1 pacing offset.** Query pacing is `used < max(1, ceil(0.1 B)) + floor(2 B t / T)` instead of
   `1 + floor(2 B t / T)`. Seeds 0-5 on three scenarios showed a small cost difference in favour of the offset
   at `d=1` and no difference at `d=10`; this is a development choice, not a tuned optimum.
3. **Tiny cells.** All four tiny oracle cells `(6,3,1)`, `(6,3,2)`, `(7,3,2)`, `(8,4,2)` were solved
   (about 0.3 s, 0.3 s, 1.2 s and 10.6 s respectively) so none was dropped.
4. **Additional safety-gated contrast.** Besides the registered primary contrast (strongest of all baselines per
   cell), the tables also report the strongest safety-gated baseline per cell (`no_switch`, `episode_*`,
   `allonset_edetector`), because `periodic_mean`, `dal_restart` and `pacing_bernoulli` have no false-promotion
   control. The registered primary metric is unchanged.
