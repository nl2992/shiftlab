# Failure Atlas v1: failure-guided discovery loop on the delayed budgeted switching contract

**Date:** 2026-10-30. **Status:** EXPLORATORY discovery/development (R4). Written before any Atlas
code exists. No novelty, theorem, efficacy or confirmatory claim follows from discovery,
development or mechanism-validation stages. Code: `src/shiftlab/dive/failure_atlas.py`,
`scripts/run_failure_atlas_loop.py`, `tests/test_failure_atlas.py`. Outputs (git-ignored):
`outputs/failure_atlas_v1/`. Ledger: `docs/failure_atlas_v1_ledger.md`.

## Purpose

**Current direction (2026-11-01):** see Amendment 9 and
[the evidence and decision review](failure_atlas_review_2026_11_01.md). Earlier locked
definitions remain the rules for their historical runs. The current objective is a useful,
modestly novel repair on a declared shared-failure region, compared against strong matched
competitors; a new theorem or universal dominance is not required.

Reverse the order of earlier ShiftLab work. Earlier work built a candidate, then looked for cells
where it won. Here we first look for reproducible failures shared by the strongest available
methods under one matched contract, and only then search for mechanisms. Three outputs:

1. **Failure Atlas.** Cells where every safety-gated baseline loses materially to a feasible,
   information-matched reference.
2. **Mechanism engine.** Typed compositions of reusable components, generated for a specific
   failure mechanism and ablated.
3. **Explanation ledger.** For each failure: whether it is avoidable, which single environment
   factor causes it, and whether a proposed component repairs that factor (ablation-confirmed).

Earlier candidates (C1, C2, H2c, HG) are benchmark anchors, not targets.

## Contract

The contract is unchanged from `docs/switching_c1_c2_exploratory_protocol_v1.md`:

- Labels are selective and paired: `D_t = l1_t - l0_t`.
- Release delay is fixed at `d`.
- The budget `B` is hard and counted at request time.
- Deployment is reversible, with switch cost `s` and query cost `c`.
- The hurdle `h = 0.1` and `alpha = 0.1`.
- False promotion is defined evaluator-side, in the current regime.

Methods see only `(t, released labels)`. Truth objects are evaluator-only (R5).

## Failure family 1: late or transient candidate advantage

The regime path is scripted but randomized: the candidate is favourable on `[tau, tau + L)` and
otherwise in an "off" state. Axes and levels:

| Axis | Levels |
| --- | --- |
| onset fraction `tau/T` (jitter ±0.05, uniform) | 0.1, 0.3, 0.6, 0.8 |
| duration `L/T` (truncated at `T`) | 0.15, 0.3, 0.6, to-end |
| effect `(P(Y=1)|off, P(Y=1)|on)` | strong (.1,.9), medium (.3,.7), weak (.4,.6) |
| off-state type | neutral (.5) or harmful (= off value of the effect pair) |
| delay `d` | 1, 10, 50 |
| budget `B/T` | 0.05, 0.1, 0.25 |
| switch cost `s` | 0.05, 0.1, 0.5 |

`T = 1000` and `c = 0.01` throughout. This gives 4·4·3·2·3·3·3 = 2592 cells.

Each cell has a **null twin**: the same axes, but the candidate is never favourable. The off
state is harmful, so every promotion is false. Null twins measure false promotion.

## Methods

**Safety-gated baselines.** These are the methods that carry a false-promotion control:

- `episode_geo`, `episode_equal`, `episode_front`
- `allonset_edetector`
- `c2_rho0.75`
- `c1_hmm_cs`

**Ungated baselines.** These are reported but cannot define a failure, because they buy their cost
with false promotions:

- `periodic_mean`
- `dal_restart`
- `pacing_bernoulli`

`no_switch` is the floor.

**Not implemented.** The Gong–Zhang, Qiu et al. and Ryabchenko delayed wrappers and the online
FWER comparator are R6 baselines that are not yet in the harness. Every atlas entry carries this
limitation until they are added. Adding them is a loop task (stage 0).

## References (evaluator side)

The references are feasible policies, not clairvoyant ones.

- **R_law (law-aware filter).** Knows the cell's generating law: the onset and duration
  distribution, the effect pair and the off type. It does not know the realized jitter or the
  outcomes. It runs the exact posterior over the scripted-path hypothesis grid from released
  labels only. It uses the same budget and delay, and a uniform query calendar. It promotes when
  the posterior expected remaining benefit exceeds `s` plus a margin, and demotes symmetrically.
  R_law bounds what any information-matched method could achieve if the law were known. It is
  not safety-matched.
- **R_family (family-Bayes filter).** The same policy with a uniform prior over the whole
  family-1 hypothesis grid, including the null members. Its posterior promotion threshold is
  calibrated on discovery null twins, so that its null false-promotion rate is `<= alpha`. It is
  the information-matched, safety-calibrated reference. It is Bayesian, and its calibration is
  empirical on the declared family only. It is a reference, not a method claim.
- **Clairvoyant.** Uses `ref_regime_clairvoyant`. It is reported only as the outer bound.

## Failure definition (locked)

All quantities are per-round cost, paired by seed.

- `best_safe` is the safety-gated baseline with the lowest mean cost in the cell. It is chosen on
  the same seeds, which is conservative: it favours the baselines.
- **Headroom (avoidability).**
  `H = cost(best_safe) - cost(R_family)`. The cell has material headroom when both hold:
  - the lower 95% paired-CI bound of `H` is above `0.01`;
  - `R_family` has a null-twin false-promotion rate `<= alpha + 0.05` (upper Wilson bound
    reported).
- **Shared failure.** The cell has material headroom, and every safety-gated baseline individually
  has a lower paired-CI bound for `cost(method) - cost(R_family)` above `0.01`.
- **Information limit.** `cost(no_switch) - cost(R_law) < 0.01` (CI upper bound). In such a cell,
  no information-matched policy gains much even knowing the law. The cell is recorded as
  information-limited and is not pursued.
- **Severity.** Mean `H`. Ranking uses severity times the number of neighbouring failing cells.

## Seed partitions (locked)

| Stage | Seeds | Adaptive use allowed |
| --- | --- | --- |
| Discovery | `[0, 10^5)` | yes |
| Development | `[10^5, 2·10^5)` | yes |
| Mechanism validation | `[2·10^5, 3·10^5)` | limited. Reuse is logged and the result is reclassified as development. |
| Confirmation | `[9·10^5, 10^6)` | no. Only for a frozen manifest. The loop refuses a second confirmation of a manifest hash. |

## Loop stages

The loop is resumable. It keeps a checkpoint in `outputs/failure_atlas_v1/state.json` and an
append-only JSONL archive of every run.

0. **Registry.** List the baselines with status `implemented`, `missing` or `wrapper-needed`.
1. **Discover.** Run a random sample of 240 cells (seeded) plus their null twins, 20 discovery seeds
   each, on all methods and references. Then refine adaptively: a further 120 cells sampled near
   the shared failures.
2. **Reproduce.** Rerun the top 12 failure cells on 100 fresh discovery seeds. Re-apply the
   definition and keep only cells that survive.
3. **Avoidability.** Check the information-limit test against R_law.
4. **Isolate.** For each surviving cell, move one axis at a time to its easiest level: delay to 1,
   budget to 0.25, switch cost to 0.05, effect to strong, duration to to-end, onset to 0.1.
   Record which single moves remove the failure (headroom CI no longer above 0.01). That axis is
   the candidate mechanism for the controlled simulator.
5. **Mechanism search (development seeds).** Build typed compositions of components, prioritized
   by the isolated axis:
   - acquisition: uniform calendar, Bernoulli pacing, reserve pacing, posterior-straddle
   - evidence: started-mixture e-process, horizon CUSUM e-detector, window mean
   - memory: none, discount, restart on rollback
   - decision: certificate plus economic check, hysteresis, rollback monitor

   Only compositions whose promotion passes through an e-process evidence component count as
   safety-gated. Each candidate states a mechanistic hypothesis. Every candidate is archived,
   including rejections.
6. **Mechanism validation.** For the best candidate per failure, run it on validation seeds:
   - in the failure cell and on its null twin;
   - with the hypothesized component ablated (swapped for its default);
   - in two neighbouring cells.

   A repair counts only if all of these hold:
   - the gap to R_family closes by at least 50%;
   - null-twin false promotion stays `<= alpha + 0.05`;
   - the ablation removes most of the gain.
7. **Stop.** The loop stops on resource ceilings: 4 h wall time and 2·10^6 method-runs by
   default. It also stops when no failure survives stage 2, or when stage 6 is reached for all
   failures. Confirmation is never run automatically.

## Non-claims and known limits

- R_family is calibrated empirically on one declared family. It is not a valid anytime test.
- The family covers 2-state Bernoulli `D` only. There are no covariates, no drift and no
  dependence beyond the regime path.
- Several R6 baselines are missing (see Methods).
- Choosing `best_safe` on the evaluation seeds biases toward the baselines, which is the
  conservative direction for a failure claim.
- The GPU is not used in v1. The harness is a per-round Python loop, so CPU process parallelism is
  used instead. Vectorizing the references on GPU is a later option, taken only if runtime binds.

## Amendment 1 (2026-10-30, after cycle 1, before cycle 2)

Cycle 1 ran on 360 cells and produced 92 discovery shared failures. 11 of them survived
reproduction. Every survivor is a late-onset or to-end cell with a strong effect and a harmful off
state. Moving onset earlier removed the failure in 5 of the 11 cells; moving delay, budget, switch
cost or duration never removed it. No candidate passed stage 6. The ledger is
`docs/failure_atlas_v1_ledger.md`.

Changes, registered before cycle 2 runs:

1. **Reference plan value (fix of a reference defect).** R_law and R_family used the expected
   benefit of staying promoted until `T`. That rule counts the harmful tail after a transient window
   closes, so R_law never promoted in 57 cells. Both references now use a promote-then-revert plan
   value: the maximum over a revert round `u` of the posterior expected benefit summed over
   `[t, u)`, minus `2s`. The `p_on_now` gate and the kappa calibration rule are unchanged. Kappa is
   recalibrated. All stage-1 classes are recomputed, and the cycle-1 classes are kept in the
   archive for comparison.
2. **Diagnostic decomposition (evaluator-side, descriptive only).** For every surviving failure
   cell and each gated e-process baseline we record:
   - the number of labels released after onset;
   - the time to the first promotion;
   - the final log e-value;
   - the analytic label requirement, `log(1/alpha_episode) + log(#starts) + log(#stakes)` divided
     by the per-label log growth at the best fixed stake.

   We also run three oracle-ablated versions of the started-mixture gate:
   - known onset, with a single start at the first post-onset label;
   - the known Kelly-optimal fixed stake;
   - both together.

   These versions see truth and are never methods. They split the gap into three parts: an
   onset-uncertainty penalty, a stake-mismatch penalty, and the label count.
3. **New evidence components (all predictable, all valid as e-processes):**
   - `started_kelly`, the repository `MultiTimescaleStartedKellyEProcess`;
   - `weighted_starts`, a started mixture whose start weights are fixed before data and declared
     from the family's onset levels. A family-informed prior is declared as such, and validity
     does not depend on it;
   - `wide_stakes`, a stake grid that extends to 0.95.

   Stage 5 proposes these components for the onset axis, and for survivors with no single
   removing axis.
4. **Stage 6 runs on all 11 survivors.** It uses the same locked repair criteria. Fresh validation
   seeds come from offset 50000, so cycle-1 validation uses do not collide.

## Amendment 2 (2026-10-30, after cycle 2, before cycle 3)

This amendment implements ledger section 7. It is registered before any cycle-3 code exists.

1. **Validity-matched reference R_valid.** R_valid is a valid gated method that receives the
   declared family prior only as fixed mixture weights, set before data:
   - start weights equal the family onset prior, mapped to label indices through the acquisition
     calendar;
   - stake weights are a mixture over the Kelly stakes for each family effect level, against the
     boundary null;
   - alpha spending, the economic check and rollback are the same as for `episode_front`.

   R_valid never sees truth. It is listed as a reference because it uses family knowledge.

   New classes:
   - **`shared_failure`** now also requires that `best_safe - R_valid` has a lower CI bound
     above 0.01.
   - **`cost_of_validity`** covers cells with headroom against R_family but not against R_valid.
     These are recorded and not pursued.
   - **`prior_gap`** covers cells where R_valid beats every prior-free gated baseline. It is
     recorded separately, because the advantage there comes from declared prior knowledge.
     A repair counts only if it is prior-free, or if it states its prior.
2. **R6 baselines.** These are added in `src/shiftlab/dive/atlas_r6_baselines.py`, following the
   repository source audits:
   - `gong_zhang_paid_obs`, a paid-observation switching-cost controller with a free-observation
     allowance, under a delayed wrapper;
   - `qiu_delayed_movement`, dynamic regret with movement cost and delayed feedback;
   - `ryabchenko_capacity`, a fixed-delay batch-representative method with `b=ceil(T/B)`;
   - `online_fwer_spending`, online alpha spending with fallback (Tian–Ramdas) over sequential
     promotion tests.

   Methods without a false-promotion guarantee go in the ungated group. `online_fwer_spending` is
   gated. Each wrapper documents where it departs from its source.
3. **Lower-bound audit.** `docs/failure_atlas_onset_multiplicity_bound_v1.md` contains:
   - a stated, checked lower bound, or a counterexample, on the expected post-onset label count
     any gate needs. The setting is a finite-horizon any-false-promotion constraint `alpha`, with
     an onset unknown among `m` label positions;
   - a source audit (e-detectors, conformal-martingale change detection, finite-horizon QCD with a
     PFA constraint), applying the R2 kill rule.

   A bound counts only after review.
4. **Failure family 2: recurrent regimes and reversals.** The regime path is a 2-state Markov chain
   in which the candidate is favourable in the "on" state. Axes:

   | Axis | Levels |
   | --- | --- |
   | switch rate `a=b` | 0.002, 0.005, 0.02 |
   | effect | strong, medium, weak |
   | off type | neutral, harmful |
   | `d` | 1, 10, 50 |
   | `B/T` | 0.05, 0.1, 0.25 |
   | `s` | 0.05, 0.1, 0.5 |

   The initial state is off, and `T=1000`. That gives 486 cells, each with a null twin that is
   never on. R_family is an exact HMM filter over the family grid, using the promote-then-revert
   plan value and a calibrated kappa. R_valid is a per-episode started gate with family-Kelly
   stakes plus a Page-CUSUM rollback.

   Family 2 uses cell-indexed seeds that are disjoint from family 1. It runs through stages 1–6
   unchanged, with 200 sampled cells plus 100 refinement cells.
5. **Family 1 rerun.** The same 360 cells and seeds are rerun with the new classes and with the R6
   baselines. The output directory is `outputs/failure_atlas_v1_cycle3/`.

## Amendment 3 (2026-10-30, before the cycle-3 full run)

This amendment adds the reviewed lower-bound audit finding
(`docs/failure_atlas_onset_multiplicity_bound_v1.md`). In harmful-off cells the onset share is not
provably unavoidable, and a valid history-triggered bettor showed headroom in a toy setting.

1. **New evidence component `triggered_kelly`, for development only.** It is a single wealth
   process started at label 0, with no start mixture. Its stake is
   `lambda_t = lambda_k * 1{the last r released labels are all favourable}`. The process is a
   fixed-weight mixture over `r` in {1, 2, 3, 4} and `lambda_k` in {0.3, 0.6, 0.9}. All weights,
   and the trigger rule itself, are fixed before data, so every stake is predictable. Alpha
   spending across episodes is the same as for the other gated components. The component must pass
   the boundary-null test and a harmful-off null test, both at 300 seeds with a limit of alpha
   plus 2 SD.
2. **Proposal rule.** Stage 5 proposes `triggered_kelly` for every survivor in both families, with
   `started_mixture_eprocess` as the ablation partner.
3. **Status of the mechanism.** It is a mechanism hypothesis, not a reference: adapting the stake
   quickly from recent released labels avoids paying the start-multiplicity penalty when pre-onset
   data are informative (harmful off state). The hypothesis predicts gains in harmful-off cells and
   none in neutral-off cells. Both predictions are checked.
4. **Prior art.** Predictable plug-in or adaptive-stake betting is established (Waudby-Smith and
   Ramdas). No novelty is claimed for the component itself.

## Amendment 4 (2026-10-30, after cycle-3 family 1, before running these checks)

Cycle-3 family 1 produced one stage-6 repair: `b1a17927d9ad` on
`on0.6_L0.6_strong_harmful_d1_b0.05_s0.1`. The candidate is straddle acquisition (it queries only
while the decision is undecided) with started-mixture evidence and a rollback monitor. Its ablation
partner uses uniform acquisition. The same (cell, spec) pair was already examined on cycle-2
validation seeds. In addition, cycle-3 validation seeds overlap the cycle-1 range, and the
per-directory log cannot see reuse across cycles. The repair is therefore reclassified as
development evidence. The checks below run on mechanism-validation seeds that no cycle has used:
`[280000, 280200)`, 200 seeds. The criteria are locked now.

1. **Straddle repair check.** In the repair cell and its null twin, compare:
   - `b1a17927d9ad`;
   - its uniform-acquisition ablation;
   - `best_safe`, re-selected on these seeds;
   - R_family and R_valid.

   It passes only if all of the following hold:
   - the gap closure to R_family is at least 0.5;
   - null false promotion is at most alpha + 0.05;
   - ablation removes at least half the gain;
   - the candidate is no worse than `best_safe` in both registered neighbours (CI upper bound
     below +0.01).
2. **Straddle mechanism prediction.** Straddle saves labels only when feedback arrives before the
   decision becomes clear. The candidate-minus-ablation gain is predicted to shrink as delay grows:
   - Grid: onset 0.6, L 0.6, strong, harmful, b 0.05, s 0.1, with d in {1, 10, 50}.
   - Report the gain at each d.
   - The prediction holds if gain(d=1) > gain(d=50), with a paired CI on the difference.
3. **Neutral-off arm of the `triggered_kelly` prediction.** Take the five harmful-off survivor
   cells and their neutral-off counterparts (identical axes, `off_type` neutral). In each, compare
   `8ac25a41d4a8` with its started-mixture ablation. The prediction holds if:
   - the mean gain is above 0 with CI excluding 0 in harmful cells;
   - the neutral mean gain has CI upper bound below 0.01, or is significantly smaller than the
     harmful gain.

All of these are mechanism-validation results. They are not confirmatory, and no confirmation
seeds are used.

## Amendment 5 (2026-10-31, cycle 4, registered before any cycle-4 code or run)

All runs in this amendment use development seeds `[100000, 200000)` unless a stage says
otherwise. Results are descriptive or development-grade. Nothing here is confirmatory.

1. **Straddle mechanism map.** Compare `b1a17927d9ad` (straddle) with its uniform-acquisition
   ablation on 40 development seeds per cell, with a null twin per cell.
   - Cells: 400 family-1 cells drawn uniformly from the 2592-cell grid with a fixed rng (seed
     4040), plus 200 family-2 cells drawn the same way. Family-2 cells use the family-2 adapter
     of the same spec.
   - Per cell, report the gain (ablation cost minus candidate cost) with its paired CI.
   - Report mean gains by level of every axis.

   Locked predictions:
   - (P1) In family 1, the mean gain at d=1 exceeds the mean gain at d=50. The paired-by-cell CI
     of that difference must exclude 0.
   - (P2) Straddle's pooled null-twin false-promotion rate is at most alpha.
   - (P3, descriptive) List the region where straddle hurts, meaning the gain's CI upper bound is
     below -0.01, by axis levels.
2. **Second explanation for `triggered_kelly`'s gain in neutral-off cells.** The registered
   hypothesis is H-TK2: a single wealth process started at label 0 avoids the start-mixture
   multiplicity cost when the onset is early, so the neutral-off gain should shrink as onset
   moves later. Test on all 4 onset levels × L {0.6, 1} × d {1, 10} × B {0.05, 0.1}, with strong
   effect, neutral off-state and s = 0.1. That gives 32 cells, each run with 40 development seeds.
   - The prediction holds if the mean gain at onset 0.1 exceeds the mean gain at onset 0.8, with
     a paired CI that excludes 0.
   - Also record first-promotion time and the number of promotions per run.
   - Re-entry after rollback cannot occur in family 1, because there is a single window, so the
     cycle-3 "re-entry" conjecture is withdrawn.
3. **Stronger validity-matched reference, R_valid2.** It keeps the same prior weights as R_valid
   and replaces fixed stakes with predictable Kelly-adaptive stakes:
   - a mixture of a discounted plug-in Kelly stake and the family-Kelly stakes;
   - stakes clipped to [0, 0.95);
   - the same alpha spending, economic check and rollback as R_valid.

   It must satisfy two checks:
   - boundary null at 300 seeds: false-promotion rate at most alpha + 2 SD;
   - pooled null-twin false-promotion rate reported. The aim is to use more of alpha than
     R_valid's 0.

   Re-run classification of the cycle-3 family-1 cells (same seeds) and family-2 cells (same
   seeds), substituting R_valid2 into the shared_failure, cost_of_validity and prior_gap
   conditions. Report the class transitions against cycle 3.
4. **Hard-budget pacing comparator.** Add `hard_budget_pacing` (ungated), following
   `docs/switching_budget_pacing_prior_audit_v1.md`. It is a budget-feasible pacing controller
   that spends B along a target trajectory, with dual-variable adjustment and the same
   window-mean decision as `pacing_bernoulli`. It is included in the R_valid2 reclassification
   run. This completes R6.
5. **Theory and prior art for straddle** (`docs/failure_atlas_straddle_theory_v1.md`):
   - (a) An R2 audit of uncertainty-driven or undecided-only acquisition for sequential tests and
     anytime-valid procedures, under delay and a hard budget. The audit covers active sequential
     hypothesis testing, testing by betting with adaptive sampling, and the repository's prior
     audits.
   - (b) A written validity argument. The query indicator is predictable with respect to released
     labels, so the e-process remains a test supermartingale under the conditional null with
     delayed release.
   - (c) A stated label-saving bound as a function of `d`. It is either proved, or marked
     heuristic with a numeric check against the P1 map data.

   Novelty is claimed only if (a) finds no source theorem that covers the result.

Stopping rule for cycle 4: stop when items 1–5 are reported, or when ceilings of 4 hours of wall
time per run are hit.

## Amendment 5b (2026-10-31, registered while the cycle-4 map is running, before its summary exists)

This amendment adds a test of the latency explanation in `docs/failure_atlas_straddle_theory_v1.md`
section (c). Under that explanation, straddle's request rate is about `P/d`, where the pending cap
is `P = 2`, and uniform pacing's rate is `B/T`. Straddle's advantage over uniform acquisition
should therefore change sign near

`d* ≈ P·T/(B + P)`,

which gives `d* ≈ 38` at B/T = 0.05, `≈ 20` at 0.1 and `≈ 8` at 0.25.

Locked predictions on the family-1 map data (mean gain over cells, paired CIs):

- **(L1)** At d = 10, the mean gain at B/T = 0.25 is below the mean gain at B/T = 0.05, with the
  CI of the difference excluding 0.
- **(L2)** At d = 10 and B/T = 0.25, the mean gain has CI upper bound < 0.005 (no material
  benefit).
- **(L3)** At d = 1, the mean gain is positive at every budget level.

If L1 or L2 fails, the latency explanation is rejected as stated.

## Amendment 6 (2026-10-31, cycle 5, registered before any cycle-5 code or run)

Cycle 4 left one question open: is `cost_of_validity` an unavoidable cost of the guarantee, or does
it come from conservative valid references? Cycle 5 measures that cost exactly on small instances.
It also opens the dependence-aware row of the failure table: failure families where gated baselines
may break their *validity*, not only cost more.

1. **Exact cost of validity (R1, oracle as reference only).** Use
   `src/shiftlab/dive/causal_switching_game.py` on every cell it can solve. Cells are tiny HMM
   analogues of family 1:
   - the regime starts off;
   - switch-on probability `a` in {0.1, 0.25};
   - effect: strong (0.02/0.98) and medium (0.2/0.8);
   - harmful and neutral off states;
   - T in {6, 7, 8}, B in {2, 3, 4}, d in {1, 2}.

   For each cell, record:
   - **V_free:** the optimal expected cost without the null-risk constraint. Use alpha = 1, or a
     variant of `solve` with the risk row removed.
   - **V_valid:** the optimal cost under the causal-null risk constraint at alpha = 0.1.
   - Monte Carlo cost (at least 5000 seeds, same HMM and contract, evaluator-side) and null-risk
     estimates for:
     - R_valid, adapted to the HMM cell with a uniform onset prior over rounds;
     - `best_safe` among the gated baselines and `no_switch`;
     - straddle, `b1a17927d9ad`.

   Derived quantities:
   - true cost of validity: `CoV = V_valid - V_free`;
   - reference conservatism: `RC = cost(R_valid) - V_valid`;
   - baseline gap: `cost(best_safe) - V_valid`.

   Locked reading:
   - If `RC > CoV` in a majority of solved cells, the cycle-3/4 `cost_of_validity` labels are
     attributed mainly to reference conservatism, and the family-1 headroom question is reopened.
   - Otherwise the labels stand at small T.
   - Extrapolation to T = 1000 is not claimed.
2. **Family 3: within-regime dependence.** The candidate-benefit indicator follows a 2-state
   Markov chain inside each regime. Its stationary mean equals the family-1 effect value, and its
   lag-1 autocorrelation is `rho` in {0, 0.5, 0.8}. All other axes follow family 1, restricted to:
   - onset {0.3, 0.6};
   - L {0.6, 1};
   - effect {strong, medium};
   - off {neutral, harmful};
   - d {1, 10};
   - B {0.05, 0.1};
   - s = 0.1.

   That gives 3 × 2 × 2 × 2 × 2 × 2 × 2 = 192 cells. Each has a null twin whose regime is never on
   and whose stationary benefit sits exactly at the hurdle boundary (`E[-D] = h`), with the same
   `rho`.

   Under `rho > 0` the conditional null `E[X_t | F_{t-1}] <= 0` can fail even though the
   stationary mean satisfies the null. This is a declared model-misspecification stress test. It
   is not a bug in the methods.

   Locked predictions:
   - **(D1)** The pooled null-twin any-promotion rate of at least one safety-gated baseline exceeds
     alpha + 0.05 at `rho = 0.8`.
   - **(D2)** For each gated baseline, the null false-promotion rate is non-decreasing in `rho`
     (descriptive; report it).

   The regular atlas classes are also reported, with R_family and R_valid built as for family 1.
   R_family ignores the dependence, which is a declared misspecification.
3. **Family 4: informative label release.** Release delay depends on the outcome:
   - favourable labels (`D = -1`) are released after `d_f`;
   - unfavourable labels are released after `d_u`;
   - `(d_f, d_u)` in {(d, d), (d, 3d), (3d, d)} with base d in {2, 10}.

   Other axes are as in family 3 with `rho = 0`, giving 3 × 2 × 2 × 2 × 2 × 2 × 2 = 192 cells,
   with null twins at the boundary.

   Event order is otherwise unchanged. A query's label is released at `t + d(outcome)`, and the
   budget is still charged at request time. The harness change must be a subclass or hook; the
   existing harness behaviour must not change.

   Locked predictions:
   - **(I1)** With `d_u = 3d > d_f`, so that favourable labels arrive first, at least one gated
     baseline's null false-promotion rate exceeds alpha + 0.05 for base d = 10.
   - **(I2)** With `d_f > d_u`, null false promotion stays at or below alpha.
4. **Shared settings.**
   - Families 3 and 4 run stages 1–4 only: discovery uses all cells with 20 seeds; reproduction
     uses the top 12 with 100 fresh seeds. Mechanism search waits until the validity failures are
     understood.
   - Null-twin false-promotion rates use 100 dedicated seeds per twin.
   - All R6 baselines and `hard_budget_pacing` are included.
   - Outputs go to `outputs/failure_atlas_v1_cycle5/`.
   - Nothing is confirmatory.

## Amendment 7 (2026-11-01, cycle 6, registered before any cycle-6 code or run)

**Purpose.** Test the sampling-density explanation from the cycle-5 assessment. The explanation:
published e-process gates kept validity under within-regime dependence and informative release
because sparse queries decorrelate the labels that are actually observed.

This cycle is a validity study, run on boundary null streams only. Cost atlas stages are not run.

**Streams.**
- Family-3 null twins: never on, stationary `E[-D] = h`, Markov benefit indicator with lag-1
  autocorrelation `rho`.
- Family-4 null twins: favourable-first release.
- T = 1000, alpha = 0.1.

**Seeds.** 200 dedicated null seeds per configuration, drawn from development seeds `[150000, 160000)`.
None of these seeds has been used before.

**Methods.** Every safety-gated baseline (episode_geo / episode_equal / episode_front,
allonset_edetector, c2_rho0.75, c1_hmm_cs, online_fwer_spending), plus R_valid, plus straddle
`b1a17927d9ad` and its uniform ablation.

**Grids.**
- Dependence grid: `rho` in {0, 0.5, 0.8, 0.95} × `B/T` in {0.05, 0.1, 0.25, 0.5} × d in {1, 10}.
- Release grid: query spacing `g = T/B` for `B/T` in {0.1, 0.25}. For each spacing,
  `(d_f, d_u) = (g, 10g)` (favourable labels first) and the control `(10g, g)`. `rho = 0`.

**Locked predictions.** "Exceeds" means the point estimate is above the threshold. Wilson
intervals are reported alongside.

- **(V1)** At `rho = 0.8` and `B/T = 0.5`, pooled over d, at least one e-process baseline among
  episode_*, allonset_edetector, online_fwer_spending and c2_rho0.75 has a null false-promotion
  rate above alpha + 0.05.
- **(V2)** At `rho = 0.8`, pooled over B/T and d and paired by seed, straddle's null
  false-promotion indicator minus its ablation's has a 95% CI that excludes 0 on the positive side.
- **(V3)** Under favourable-first release with `d_u = 10g`, pooled over the two spacings, at least
  one gated baseline has a null false-promotion rate above alpha + 0.05. The control `(10g, g)`
  stays at or below alpha.
- **(V4, descriptive)** Across the dependence grid, each e-process baseline's null
  false-promotion rate is non-decreasing in the effective sampled-label correlation
  `rho^(T/B)`. Report Spearman correlations.

**Interpretation rule.** The sampling-density explanation is retained only if V1 holds and the
V4 Spearman correlation is positive for most e-process baselines. If V1 fails, the e-process gates
are robust to Markov dependence at this boundary, and the dependence row of the failure table is
closed for published baselines.

**Execution.** The run executes as a detached, resumable OS process with a per-configuration
checkpoint. Output goes to `outputs/failure_atlas_v1_cycle6/`. Nothing here is confirmatory.

## Amendment 8 (2026-11-01, user-directed acceptance revision; cycle 7; registered before any cycle-7 code)

### Acceptance revision

The user reviewed six cycles and judged that the acceptance bar had been set too high. The aim of
the Failure Atlas is to find a failure shared by all SOTA methods, diagnose it, and propose a
workable solution that is mildly novel and beats the SOTA competitors. Theorem-level novelty and a
50% closure of the gap to the Bayes reference R_family are **no longer acceptance criteria**. R2
audits are kept, but they serve only to state honestly how the solution relates to prior work.
Matching prior art no longer kills a candidate. A candidate is **accepted as a workable solution**
when all five conditions below hold on fresh seeds:

- **(A1) Beats SOTA on the shared failure.**
  - Comparison set: the best SOTA gated baseline, selected per cell on the same seeds. The SOTA
    set is every published or R6 gated baseline plus the dependence-robust baselines below. The
    ShiftLab anchors C1 and C2 are excluded.
  - Cells: the reproduced shared-failure cells of family 1 (cycle 3) and family 3 (cycle 5).
  - Per-cell test: `cost(candidate) - cost(best SOTA)` has CI upper bound < -0.01.
  - Pass rule: the per-cell test holds in at least half of the cells, and the mean difference over
    cells has CI upper bound < 0.
- **(A2) No harm nearby.** Across each failure cell's registered neighbours, the mean of
  `cost(candidate) - cost(best SOTA)` has CI upper bound < +0.01.
- **(A3) Validity.**
  - Null false promotion must be at most alpha + 0.05 (point estimate) on boundary nulls with
    rho = 0, every B/T in {0.05, 0.1, 0.25}, and d in {1, 10}.
  - Null false promotion must be at most alpha + 0.05 on dependent nulls with rho = 0.5 and
    B/T ≤ 0.1.
  - At rho = 0.8, the candidate's false promotion must not exceed that of the best SOTA gated
    baseline by more than 0.05.
- **(A4) Mechanism.** Ablating the new component removes at least half of the A1 gain.
- **(A5) Mild novelty.** An R2 check finds no single source that states this specific rule for
  this contract: delayed selective paired labels, a hard budget, reversible switching, and
  false-promotion control. Known ingredients are allowed.

### Candidate (motivated by cycles 3–6)

**DSS: delay-aware, dependence-safe straddle.** Straddle beat the best gated baseline on fresh
seeds (cycle 3, Amendment 4). Two diagnosed weaknesses limit it:

- (i) **Delay.** Its gain changes sign at about `d* = P·T/(B+P)` (cycle 4).
- (ii) **Dependence.** It queries consecutive rounds, so under within-regime dependence its
  validity breaks (cycle 6).

DSS keeps straddle's undecided-only querying and adds two fixed rules:

- **Delay switch.** If `d >= d*`, use uniform calendar acquisition instead.
- **Minimum inter-query gap `g` rounds.** No query is issued within `g` rounds of the previous
  query.

Evidence is `started_mixture_eprocess` and the decision rule is `rollback_monitor`, both unchanged
from `b1a17927d9ad`. `g` is chosen on development seeds `[160000, 170000)` from {1, 4, 8, 16} by a
locked rule:

1. Keep only the values of `g` whose development null false promotion is at most alpha at rho =
   0.5 for B/T in {0.05, 0.1, 0.25} and d = 1.
2. Among those, take the value with the lowest mean development cost over the failure cells.

`g` is then frozen.

**Ablations, run on validation seeds:**

- DSS without the delay switch;
- DSS with `g = 1`;
- uniform acquisition, which is the original ablation.

### Added SOTA baselines (dependence-robust)

- **`markov_lr_gate`.** A Markov-likelihood e-process on the queried-label skeleton chain. It is
  a mixture over a declared grid of 2-state transition matrices, tested against the boundary null
  in which the stationary favourable probability is `(1+h)/2`. Its promotion, alpha spending,
  economic check and rollback are the same as `episode_front`. The audit names it as the strongest
  dependence-robust baseline.
- **`thinned_hedged_gate`.** The repository started-mixture gate fed only queried labels at least
  `g_t` rounds apart. `g_t` is fixed before data from a declared mixing assumption: `g_t = 10`.

Both are added to the SOTA set for A1.

### Evaluation

- Validation seeds: `[290000, 290200)`, 200 per cell. They are fresh; no stage has used them.
- Cost cells: the family-1 and family-3 reproduced shared failures and their neighbours.
- A3 null grid: rho in {0, 0.5, 0.8} × B/T in {0.05, 0.1, 0.25} × d in {1, 10}.
- The run is a detached, resumable process. Outputs go to `outputs/failure_atlas_v1_cycle7/`.
- Nothing is confirmatory. If DSS passes A1–A5, a separate confirmation protocol is written before
  the confirmation seeds are touched.

### Dependence test (as requested)

The two added baselines are also reported across the full cycle-6 dependence grid:

- the null false-promotion table;
- power on family-3 failure cells against the published gates.

This answers whether robustness to dependence is cheap or costly in this contract.

## Amendment 9 (2026-11-01): clarify acceptance and register dependence pilot

This amendment follows the user's renewed instruction to diagnose a common failure and seek
a workable, mildly novel repair. It preserves Amendment 8 and all earlier results verbatim.
It does not retrospectively turn any failed experiment into a pass.

- A shared failure means every **implemented, contract-applicable comparator in the frozen
  registry** fails on the declared region. It does not mean every SOTA algorithm in existence.
- A new theorem, global dominance, and 50% closure to a Bayes reference are not prerequisites
  for continuing a candidate. Credit known ingredients; novelty must identify an actual rule
  difference with ablation evidence. A combination alone is not proof of novelty.
- Amendment 8 A1-A4 remain the registered cycle-7 evaluation, including its numerical margins.
  They are not a universal definition of publishability. If DSS fails them, retain the result;
  any narrower evaluation must be registered prospectively with new seeds.
- Safety cannot be relaxed by comparing with an unsafe best competitor. A3's rho=0.8 relative
  comparison is descriptive only: it cannot support a dependence-safe claim. Any accepted safety
  claim needs a declared null/dependence class and an absolute criterion with uncertainty.
- Fixed gap 4 and gap 10 are empirical mitigations, not exact independence. The Markov gate
  has a homogeneous-skeleton assumption; unequal query gaps and regime changes need explicit
  qualification. None is an unrestricted dependence-robust solution.

**Pilot registered before execution:** `scripts/run_atlas_dependence_pilot_v1.py`; development
seeds [170000,170020), T=1000, 32 cycle-6 dependence null configurations plus the 11 reproduced
family-3 alternative cells. Compare episode_front, Markov LR, gap-10 betting, frozen DSS gap 4,
and uniform DSS ablation on identical streams. Report per-cell false-promotion frequencies and
cost per round, retaining paired seed records. This n=20 pilot checks execution and identifies
tradeoffs; it cannot pass A1-A4 or establish nominal error control. It does not consume the
reserved [290000,290200) validation seeds or confirmation seeds. No new tuning is allowed from
these outputs without recording reuse. Output: `outputs/failure_atlas_v1_cycle7/dependence_pilot/`.

**Metric-completeness addendum, same date:** replay the 11 alternative cells on the identical
20 seeds to save any promotion, at least one correctly timed promotion (by evaluator regime),
and any false promotion separately. This repairs the pilot's initially incomplete power
bookkeeping; it adds no independent evidence and changes no decisions, candidate or thresholds.
Append replay records rather than deleting the original records. No acceptance verdict follows.

## Amendment 10 (2026-11-01): complete the registered cycle-7 evaluation

The user requested continuation and completion of cycle 7. Execution details, exact
neighbour definition, comparator registry, aggregation and A4 interpretation are frozen
in `docs/failure_atlas_cycle7_execution_v1.md` before validation seed use. This completes
Amendment 8 on [290000,290200); no candidate or numerical acceptance margin is changed.
The prior 20-seed development pilot is not pooled into validation. The full cycle-6 null
grid is included as the registered supplementary dependence study.
