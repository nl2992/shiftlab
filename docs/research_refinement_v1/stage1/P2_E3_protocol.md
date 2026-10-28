# P2: E3 matched-opportunity intervention factorial (H-B3), v2 dose-response

**Status: protocol v2 DRAFT, implementation and CPU development runs done (2026-10-28). Not frozen.**
v2 replaces the v1 selected-point crossover (shift 0.6) with a registered dose-response operating-region
estimand, following `CODEX_PROTOCOL_REVIEW_1.md` (P2/E3: "fresh-seed confirmation at the
development-selected 0.6 point would be valid replication of that constructed point"). The
confirmation run is gated by `shiftlab.freeze.require_freeze` on `P2_E3_freeze.json` (section 9); the
freeze record has not been written. No confirmation seed has been used.

Charter alignment (`AGENTS.md`): this study compares **state machines under evaluator-side oracle
utility**. It does not establish decision-harm validity; Q1 alarms alone are not evidence of harm.
Oracle truth is evaluator-only and never reaches a monitor, certifier or rollback policy.

## 1. What is claimed, and what is not

| Item | Statement |
|---|---|
| Utility | `U = sum_{t<3200} [E c(incumbent_t) - E c(deployed_t)] - 0.05 (#switches) - 0.05 (#rollbacks)`, oracle expectation, costs FN 5 / FP 1. Column `expected_net_gain_vs_incumbent`. Because `U` is measured against the incumbent, **`U` is already the incremental utility versus `continue`** (`continue` has `U = 0`). A switch is any change into reference or candidate. |
| Reported alongside | `realized_net_gain_vs_incumbent`; labels by stage; `compute_units`; `switches`, `rollbacks`, `intervention_cost`; alarm, certification, deployment, abstention, infeasibility and rollback indicators. No monetisation. |
| **Certify-arm estimand** | The certification step is the integrated Q2 scout + certification. It tests the code-defined null `E[I_t (g_t - s) | F_{t-1}] <= 0` (`VALIDITY_TABLE.md` rows 22-23): `g_t` is the **candidate-versus-incumbent** gain, `I_t` the selected-context indicator, and the amortised switch rate `s = 0.05 / (3200 - window_end)` is charged **only on selected contexts**. It is **not** a full-cost net-benefit certificate (`E[I_t g_t - s]`) and does not compare the candidate with the reference. The Q1 revert arm acts on a different object (incumbent-minus-reference harm). **`U` is an oracle quantity of realised state machines; the E3 estimands below are statements about `U`, not about any certificate's guarantee.** |
| Composition | Monitor -> certify -> promote composition is **not controlled and not claimed** (`VALIDITY_TABLE.md` row 26). |
| Matching | **L1** (same events and information types) + **L2** (same stream and query uniforms: coupled replay) + **L3** (common per-stage label caps within a cell). These match **opportunities and caps, not expenditure**; realised spend differs by arm (no L4) and is reported in every table. |
| Not claimed | No attribution percentages (the decomposition is in utility units); no claim that the crossover generalises beyond this generator; no real-data transfer; single-factor main effects are descriptive. |

## 2. Executable timeline (state machine)

Stream length `n = 3200`, events indexed from 0; fit/validation ends at 800 (Q1 opens at 800).

| Symbol | Meaning | Value |
|---|---|---|
| `t_a` | Q1 trigger: first event whose ungated HT e-process (alpha 0.02, rate 0.40, margin 0.10) crosses `1/alpha`; the monitor stops. `None` if none before the coverage end or the monitor label cap | learner-side |
| `t_r` | revert start | `t_a + 1` |
| `t_c` | certification start | `t_a + 1` (immediate) |
| `W` | certification window: scout `[t_c, t_c+400)`, fresh certification `[t_c+400, t_c+800)`, 320-label cap, rate `320/800` | 800 |
| `t_e` | certification completion | `t_c + W` |
| `t_d` | candidate deployment | `t_e` if certified with a nonempty selection (optional waiting: nothing changes between a crossing and `t_e`); `deploy_rule = crossing` is implemented but not used |
| `t_w` | matched-wait revert | `t_a + 1 + W` (= `t_e`) |
| `t_x` | rollback alarm of the monitored policy | learner-side |

Certification (and the wait) is **infeasible** when `t_c + W >= n`: no labels are spent and no policy changes; this is an outcome, counted and reported, never an exclusion.

| Response | After alarm | Certification | Rollback (parity) |
|---|---|---|---|
| `continue` | incumbent always | none | none |
| `revert` | **reference from `t_r`** | none | reference-vs-incumbent monitor from `t_r`; alarm at `t_x` returns to incumbent after `t_x` (cost 0.05) |
| `certify_promote` | incumbent while certifying; **candidate from `t_d`** if certified (otherwise **abstain**: stay on incumbent) | `[t_c, t_e)` | candidate-vs-incumbent monitor from `t_d` |
| `revert_while_certifying` | **reference from `t_r`**; candidate from `t_d` if certified (switch charged again) | `[t_c, t_e)` in the background, identical to `certify_promote` | reference monitor from `t_r` until `t_d` or alarm; candidate monitor from `t_d`; one shared allowance |
| `wait_revert` (**matched-wait control**) | incumbent until `t_w`, then **reference from `t_w`** unconditionally | none (labels not spent) | reference monitor from `t_w` |

The matched-wait control isolates timing from certification: it idles for exactly the certification duration, then does what `revert` does. `continue` is the matched "wait forever" control. Certification's value is therefore read as `U(certify_promote) - U(wait_revert)` and `U(certify_promote) - U(continue)` together, never from `revert` alone.

Rollback monitor (identical wherever attached): ungated HT, rate 0.20 on the shared uniforms, alpha 0.015, bound `5/0.2 + 0.05/(n - start)`, harm = deployed minus incumbent cost, amortised threshold `0.05/(n - start)`, **one 160-label allowance per arm shared by its monitors**. After a rollback the arm stays on the incumbent, except that `revert_while_certifying` may still promote at `t_d`.

**Rollback parity is parity of attachment, not of protection.** In `revert_while_certifying` the reference monitor can consume the shared allowance before `t_d`, leaving the candidate unmonitored (`candidate_monitor_starved`); `revert` and `wait_revert` carry a monitor for the whole run, `certify_promote` only from `t_d`. Effective rollback firing (`p_reference_rollback`, `p_candidate_rollback`, `p_candidate_monitor_starved_given_deploy`) is reported at every dose and is never summarised as "parity" alone.

Per-stage label caps (L3, identical for all arms in a cell): Q1 `0.40 x` window length (320 at coverage 1600, 960 at 3200); certification 320; rollback 160. Expenditure by arm is reported.

## 3. Factors and exact levels

| Factor | Levels |
|---|---|
| response | `revert`, `certify_promote`, `revert_while_certifying`, `wait_revert`, plus `continue` |
| rollback | `off`; `parity` (section 2) |
| monitoring coverage | `short`: Q1 window `[800, 1600)`; `long`: `[800, 3200)` (same rate; cap scales with the window) |
| harm onset (incumbent becomes all-positive) | `before` = **800**, `at` = **1600** (legacy monitor end), `after` = **2000** |
| **dose of post-alarm reference deterioration** | **{0, 0.15, 0.3, 0.45, 0.6, 0.8, 1.0}** (section 3.1) |

84 cells (3 x 2 x 2 x 7) x 5 responses = **420 rows per seed**. With `short` coverage and onset `at`/`after` the Q1 window closes before harm is visible, so no alarm occurs and every arm equals the incumbent by construction (descriptive control). **Coverage can change the subsequent environment**: the deterioration start is keyed to each cell's own Q1 trigger, so the two coverage levels share a deterioration time only when they share an alarm; coverage effects are therefore a bundle of monitoring and environment timing, and are descriptive.

Incumbent: `1{x0 - 0.9 x1 >= 0}` until the onset, all-positive afterwards. Reference: the frozen source cost-optimal rule. Candidates: the existing 13-policy logistic family fitted on events `< 800` only.

### 3.1 Dose of reference deterioration (evaluator side only) and why this grid

Let `t_a^safe` be the cell's Q1 trigger computed on the dose-0 labels and `T_d = t_a^safe + 1` (`T_d = n` if no alarm). For dose `delta > 0` and `t >= T_d` the latent target is shifted, `target'_t = target_t + delta`, `y'_t = 1{target'_t > 0}`, `p'_t = Phi((score_t + delta)/0.3)`; features are unchanged (pure concept shift). Labels before `T_d` are identical at every dose, so the Q1 history and trigger are identical across doses by construction (tested).

Grid rationale, from development evidence only (first dev run, seeds 100200000-199, and v2 dev, seeds 100200200-599): dose 0 is the safe anchor; 0.15, 0.3 and 0.45 lie below the dev transition (revert still better); the dev transition falls between 0.45 and 0.6 (0.6 is the first dose with certify-promote clearly ahead); 0.8 and 1.0 are the degenerate regime in which certification almost never succeeds and rollback of the reference becomes frequent. The grid is **locked here**; no dose is added, dropped or moved after the freeze. The grid steps are coarse (0.15), so the threshold is reported as a bracket, not a point.

## 4. Registered estimands and tests

Primary stratum **S\* = {onset = before} x {rollback = parity}**, coverage averaged within seed (the two coverage cells of a seed are not independent), one value per seed and dose. `D(delta) = E[U(revert) - U(certify_promote)]` at dose `delta`.

**Primary estimand: the dose curve `D(delta)` over the 7-dose grid with 95% simultaneous paired-bootstrap max-t bands.** Seeds are resampled (10,000 draws, seed 20261030); for each draw the studentised deviation of each dose mean is computed, and the critical value `c` is the 95% quantile of the maximum absolute value over the 7 doses; the band at each dose is `mean +/- c * se`. Coverage is simultaneous (family-wise 0.05) across all 7 doses. Classification: **revert side** if the band lies above 0, **promote side** if below 0.

**Grid-bracketed crossover threshold:** the first grid dose `delta*` whose band lies on the promote side, **provided** some lower dose is on the revert side; reported as the bracket `(previous grid dose, delta*]`. **Monotone trend (predefined, secondary):** the per-seed OLS slope of `D` on dose, one-sided t-test for slope `< 0`; it supports but does not replace the bands.

**Decision rule.** "Crossover located" iff the bracket exists. If it does not, the report states **"no crossover detected on the grid at this n"** with the full curve and bands. **It must not be reported as "ranking set by timing and rollback only"**: absence of detection is not evidence for any named mechanism.

**Attribution (exact decomposition in utility units, per dose, each with its own simultaneous band):**
`U(promote) - U(revert) = [U(continue) - U(revert)] + [U(promote) - U(continue)] = abstention component + promotion component`
because `U(continue) = 0`. A promote-side dose is **promotion-supported** only if additionally the promotion component's band lies above 0; otherwise it is **abstention-only**. The report lists both sets. Further registered curves (secondary, same band procedure): `U(promote) - U(wait_revert)` (certification versus a blind delayed revert), `U(wait_revert) - U(revert)` (pure timing), `U(revert_while_certifying) - U(revert)` (background certification), `U(revert)` versus `continue`.

**All seeds are analysed**, including no-alarm and infeasible streams; **certification-conditional utility is descriptive only** (reported as `mean_utility_given_certified`, never tested or used in a decision). Everything not named above (other onsets, rollback `off`, single-factor main effects, per-cell tables, realised-versus-expected, resource tables) is descriptive. The analysis script **rejects** incomplete seed grids, duplicate seed x cell x response rows, unregistered levels and non-finite utilities.

## 5. Seeds, mapping and sample size

| Block | Registry id | Range | Use |
|---|---|---|---|
| dev | `e3_dev_smoke` | 100200000-100200999 | seeds 0-199: first smoke and parameter exploration; 200-599: v2 dev; **600-999 untouched** |
| confirmation | `e3_confirmation` | 100300000-100309999 | one registered run |

**Exact mapping.** Seed `s = block_start + first_index + i`, `i = 0..n-1`. Every seed enters **all 84 cells and all 5 responses** (420 rows), so seeds are paired across every factor and "n per cell" = number of seeds. Stream seed `s`; query uniforms `default_rng(s + 700001).random(3200)` shared by every arm and cell (L2). No seed is dropped or replaced. Confirmation starts at `100300000` (the runner enforces first index 0); the unused tail stays reserved.

**Power / n from dev (v2 dev, n = 400).** For each decisive dose, `n = ((c + z_0.9) sd / (0.75 |mean|))^2` with the dev critical value. Largest requirements: promotion component at dose 0.6, **n = 295**; at 0.45 the primary curve needs 47 and the promotion component 170; doses 0.8 and 1.0 are not powered for the promotion component (0.8 would need 1,737; 1.0 is exactly 0) and are descriptive for that curve. **Registered confirmation n = 1000** (about 3.4 x the largest requirement). Fixed in advance; no interim looks or optional stopping. Cost: about 2 s per seed with 3 workers, so about 35 minutes on CPU.

## 6. Stop rules

1. **Implementation stop:** any failing test in `tests/test_e3_intervention_factorial.py` or `tests/test_e3_analysis_and_freeze.py`; a label-cap violation; a row count other than `n x 420`; a Q1 trigger that differs across doses or arms in a cell; non-finite utilities. Fix, rerun **dev** only, record the failure.
2. **Freeze gate:** `--block confirmation` calls `shiftlab.freeze.require_freeze(P2_E3_freeze.json)`; it refuses unless every listed file (protocol, code, config, tests, dependencies) matches its recorded SHA-256 and has no uncommitted change, and the registered config file equals the code's config (section 9). The freeze also needs a Codex protocol re-review.
3. **Feasibility gate (dev, re-checked before freeze):** S\* alarm rate at least 0.9 at `short` coverage (dev 0.984) and certification not infeasible in S\* (dev 0).
4. **Claim rules:** a failed bracket is "no crossover detected on the grid at this n". Inadequate precision is reported as such and is not a licence to add seeds. If the bracket exists but no dose is promotion-supported, the finding is "crossover driven by abstention".
5. **No adaptive follow-up on confirmation seeds;** no change of grid, onsets, caps or analysis after any confirmation output; post hoc analyses are labelled.
6. **Compute:** CPU only. No CUDA needed or approved.

## 7. Known limitations (carry into any write-up)

- **Constructed operating region:** the post-trigger shift family is a synthetic generator; the dose grid was set from dev. The estimand locates the transition on this generator; it is not a general law.
- **Abstention dominates the crossover.** In dev at dose 0.6, certify-promote's advantage over revert (256.6) splits into an abstention component of 233.8 and a promotion component of 22.7; promotion is supported only at 0.6 on dev and is not decisive at 0.8 and 1.0.
- **Rollback parity is parity of attachment** (section 2); effective firing is 0 to 2% below dose 0.6 and 49% / 92% of reverting streams at 0.8 / 1.0. The candidate monitor was starved in 51-57% of deployed `revert_while_certifying` streams at doses 0-0.6.
- Coverage is bundled with label spend and with environment timing (section 3). Onsets `at`/`after` with `short` coverage are undetectable by design.
- Synthetic stationary-outcome stream, immediate labels, non-performative; imposed 0.05 cost scale; certification is the existing Q2 uniform-query path (estimand in section 1).
- The registry entries for `e3_dev_smoke` and `e3_confirmation` still read `reserved_unused`; the dev use above should be recorded there.

## 8. Implementation and development record

**Files (new or changed in place):** `src/shiftlab/dive/e3_intervention_factorial.py`, `scripts/run_e3_intervention_factorial.py`, `scripts/analyze_e3.py`, `configs/e3_intervention_config.json`, `tests/test_e3_intervention_factorial.py`, `tests/test_e3_analysis_and_freeze.py`. `integrated_pipeline.py` and every other existing file are unmodified; reuse and copy-adaptation are as in v1 (the Q1/rollback loops, onset transform, policy timeline and deterioration generator are copy-adapted because `run_seed` is monolithic).

**Checks:** `uv run --no-sync pytest tests/test_e3_intervention_factorial.py tests/test_e3_analysis_and_freeze.py -q` (all pass) covers timeline indices, matched trigger, background arm equal to revert and certify on shared parts, matched-wait semantics, rollback parity/off, starved-monitor accounting, caps, deterioration keeps pre-alarm history, oracle isolation (NaN-poisoned oracle leaves every learner-side column unchanged), grid completeness, duplicate rejection, band/crossover logic, the decomposition identity, "no crossover is not timing-and-rollback-only", config-file equality and the freeze gate (missing record and changed file both refuse). `ruff check` and `ruff format --check` are clean.

**Commands:**
```
uv run --no-sync python scripts/run_e3_intervention_factorial.py --block dev --n-per-cell 400 --first-seed-index 200 --out outputs/e3/dev_v2_n400 --workers 3 --device cpu
uv run --no-sync python scripts/analyze_e3.py --rows outputs/e3/dev_v2_n400/e3_rows.parquet --out outputs/e3/dev_v2_n400/analysis
```
Dev v2: seeds 100200200-100200599, 168,000 rows, 807 s with 3 workers (about 2 s per seed; about 5 s per seed single process), HEAD `58761374` plus uncommitted E3 edits, config sha256 `dc70a91b...`. Workers above 3 died under memory pressure on this machine; the runner then finishes sequentially.

**Dev results (development-only; not confirmatory; S\*, n = 400, utility `expected_net_gain_vs_incumbent`, simultaneous 95% critical value 2.72 for D):**

| dose | D = revert - promote [band] | abstention comp. = -U(revert) | promotion comp. = U(promote) [band] | promote - wait_revert | revert (rollback fires) | P(certified) = P(deployed) | P(abstain \| alarm) | U(promote) given certified (desc.) |
|---|---|---|---|---|---|---|---|---|
| 0 | +427.4 [402, 453] | -723.0 | +295.6 [268, 323] | -134.5 | 723.0 (0%) | 0.726 | 0.262 | 407.1 |
| 0.15 | +428.2 [403, 453] | -607.3 | +179.1 [153, 205] | -182.2 | 607.3 (0%) | 0.511 | 0.480 | 350.3 |
| 0.30 | +324.0 [305, 343] | -408.6 | +84.6 [65, 105] | -158.4 | 408.6 (0%) | 0.286 | 0.709 | 295.6 |
| 0.45 | +79.4 [66, 93] | -121.0 | +41.6 [27, 56] | -30.1 | 121.0 (0%) | 0.161 | 0.836 | 257.8 |
| 0.60 | -256.6 [-269, -244] | +233.8 | +22.7 [12.5, 32.9] | +162.9 | -233.8 (2%) | 0.100 | 0.898 | 227.3 |
| 0.80 | -498.9 [-538, -460] | +496.1 | +2.9 [-0.3, 6.0] | +344.1 | -496.1 (49%) | 0.020 | 0.980 | 142.6 |
| 1.00 | -344.5 [-381, -308] | +344.5 | 0.0 [0, 0] | +294.9 | -344.5 (92%) | 0.000 | 1.000 | n/a |

Dev crossover bracket **(0.45, 0.6]**; promote side {0.6, 0.8, 1.0}; **promotion-supported promote-side doses: {0.6} only**; dev trend slope -1021 per unit dose (p < 1e-200). The 0.45 -> 0.6 crossing is therefore real on 400 fresh dev seeds but is dominated by abstention, with a small, significant promotion benefit at 0.6. Doses 0.8 and 1.0 are abstention-only. Versus the matched wait, certify-promote loses at doses 0-0.45 (a blind delayed revert is better) and wins at 0.6-1.0. Full per-dose probability, rollback and resource tables are in `outputs/e3/dev_v2_n400/analysis/` (`dose_probabilities_stratum.csv`, `dose_curve_*.csv`, `cell_descriptives.csv`).

**Continue / pivot / stop.** Continue to the freeze step. The dose-response estimand is implemented and tested, the CPU factorial is feasible (no CUDA), and dev shows a bracketed transition with a mostly-abstention mechanism. Open items before freeze: Codex re-review of the v2 estimands; recording the dev seed use in the registry; decision whether to add a finer dose between 0.45 and 0.6 (would require a dev re-run before the freeze, since the grid is otherwise locked).

## 9. Freeze file list (for `P2_E3_freeze.json`)

Protocol: `docs/research_refinement_v1/stage1/P2_E3_protocol.md`. Files (all must be committed and clean when the record is written):

```
configs/e3_intervention_config.json
configs/seed_registry.yaml
scripts/run_e3_intervention_factorial.py
scripts/analyze_e3.py
tests/test_e3_intervention_factorial.py
tests/test_e3_analysis_and_freeze.py
src/shiftlab/freeze.py
src/shiftlab/seed_registry.py
src/shiftlab/dive/e3_intervention_factorial.py
src/shiftlab/dive/integrated_pipeline.py
src/shiftlab/dive/budgeted_promotion.py
src/shiftlab/dive/promotion_grid.py
src/shiftlab/dive/promotion.py
src/shiftlab/dive/experiment.py
src/shiftlab/dive/eprocess.py
src/shiftlab/dive/controller.py
src/shiftlab/dive/estimators.py
src/shiftlab/dive/evaluation.py
src/shiftlab/dive/proxy.py
src/shiftlab/dive/query.py
src/shiftlab/decision_harm_experiment.py
src/shiftlab/monitoring.py
src/shiftlab/data/decision_tasks.py
src/shiftlab/data/schemas.py
src/shiftlab/data/streaming.py
src/shiftlab/data/gpu/environment.py
src/shiftlab/data/synthetic/generators.py
src/shiftlab/data/synthetic/adaptation.py
src/shiftlab/data/synthetic/oracle_spec.py
src/shiftlab/data/synthetic/presets.py
```
Seed blocks: `e3_confirmation`. The list is the set of `shiftlab` modules loaded when the E3 module and runner are imported, plus the config, registry and tests; `__init__.py` files are not listed.
