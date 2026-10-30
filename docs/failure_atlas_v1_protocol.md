# Failure Atlas v1: failure-guided discovery loop on the delayed budgeted switching contract

**Date:** 2026-10-30. **Status:** EXPLORATORY discovery/development (R4). Written before any Atlas
code exists. No novelty, theorem, efficacy or confirmatory claim follows from discovery,
development or mechanism-validation stages. Code: `src/shiftlab/dive/failure_atlas.py`,
`scripts/run_failure_atlas_loop.py`, `tests/test_failure_atlas.py`. Outputs (git-ignored):
`outputs/failure_atlas_v1/`. Ledger: `docs/failure_atlas_v1_ledger.md`.

## Purpose

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
