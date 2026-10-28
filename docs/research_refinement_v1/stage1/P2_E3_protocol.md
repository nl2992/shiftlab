# P2: E3 matched-opportunity intervention factorial (H-B3)

**Status: protocol DRAFT with implementation and CPU development smoke done (2026-10-28).** Not frozen:
a SHA-256 freeze record and a Codex protocol review are still required before the confirmation block
may run (the runner refuses `--block confirmation` without a freeze record whose `protocol_sha256`
equals the hash of this file). No confirmation seed has been used.

Charter alignment (`AGENTS.md`): this study compares **state machines under evaluator-side oracle
utility**. It does not establish decision-harm validity, and Q1 alarms alone are not evidence of harm.
Oracle truth is evaluator-only and never reaches a monitor, certifier or rollback policy.

## 1. What is claimed, and what is not

| Item | Statement |
|---|---|
| Primary quantity | Expected (oracle) net decision gain versus the incumbent over the horizon, minus intervention costs. Column `expected_net_gain_vs_incumbent`; name it exactly this way wherever quoted. |
| Definition | `U = sum_{t<3200} [E c(incumbent_t) - E c(deployed_t)] - 0.05 * (#switches) - 0.05 * (#rollbacks)`, expectation under the oracle `P(y_t=1 | x_t)`, costs FN 5, FP 1. A switch is any change into reference or candidate (revert, promote, promote-after-revert). |
| Reported alongside | `realized_net_gain_vs_incumbent` (same, realised labels); labels by stage (`labels_q1`, `labels_cert`, `labels_rollback`, `labels_total`); `compute_units` (e-process updates + K x scout events + certification events, K = 13 candidates); `switches`, `rollbacks`, `intervention_cost`; alarm, certification, infeasibility and rollback indicators. No monetisation. |
| **Certify arm estimand** | The certification step is the integrated Q2 scout + certification (`budgeted_promotion._monitor_scout_context_policy`). It tests the code-defined null `E[I_t (g_t - s) | F_{t-1}] <= 0` (`VALIDITY_TABLE.md` rows 22-23), where `g_t` is the **candidate-versus-incumbent** gain, `I_t` is the selected-context indicator and the amortised switch rate `s = 0.05 / (3200 - window_end)` is charged **only on selected contexts**. It is **not** a full-cost net-benefit certificate (`E[I_t g_t - s]`), it does not compare the candidate with the reference, and its guarantee (conditional on Q2 validity, uniform-query path) says nothing about `U`. The Q1 revert arm acts on a different object (incumbent-minus-reference harm). **`U` is an oracle quantity evaluated on realised state machines; H-B3 is a statement about `U`, not about a certificate.** |
| Composition | Monitor -> certify -> promote **composition is not controlled and is not claimed** (`VALIDITY_TABLE.md` row 26). Certification here starts after a data-dependent Q1 alarm; no conditional-validity result is asserted for that. |
| Matching | **L1** (same events, same information types) **+ L2** (same stream, same query uniforms, i.e. coupled replay) **+ L3** (common per-stage label caps within a cell). **Not L4**: realised spend differs by arm and is reported. |
| Not claimed | No attribution percentages; no statement that the crossover generalises beyond the registered generator; no real-data transfer. Main effects of single factors are descriptive. |

## 2. Executable timeline (state machine)

Stream length `n = 3200`. Events are indexed from 0. Fixed stage boundaries: fit/validation ends at 800 (the Q1
window opens at 800); the legacy Q1 window ends at 1600; the legacy deployment began at 2400.

| Symbol | Meaning | Value |
|---|---|---|
| `t_a` | Q1 trigger: first event whose ungated HT e-process (alpha 0.02, rate 0.40, margin 0.10) crosses 1/alpha; the monitor stops there. `None` if no crossing before the coverage end or the monitor label cap | learner-side |
| `t_r` | revert start | `t_a + 1` (the alarm-event decision is unchanged) |
| `t_c` | certification start | `t_a + 1` (immediate; no stage alignment) |
| `W` | certification window: scout `[t_c, t_c+400)`, fresh certification `[t_c+400, t_c+800)`, label cap 320 at rate `320/800` | 800 |
| `t_e` | certification completion | `t_c + W` |
| `t_d` | candidate deployment | `t_e` if certified with a nonempty selection (optional waiting: the candidate does not act between the crossing and `t_e`; a registered alternative `deploy_rule = crossing`, i.e. `crossing + 1`, is implemented but **not** used) |
| `t_x` | rollback alarm for the policy being monitored | learner-side |

Certification is **infeasible** (no labels spent, no promotion) when `t_c + W >= n`; this is an outcome, counted and reported, not an exclusion.

| Response | t < t_a+1 | After alarm | Certification | Rollback (parity) |
|---|---|---|---|---|
| `continue` | incumbent | incumbent | none | none |
| `revert` | incumbent | **reference from `t_r`** | none | monitor reference-vs-incumbent from `t_r`; alarm at `t_x` returns to incumbent after `t_x`, cost 0.05 |
| `certify_promote` | incumbent | incumbent while certifying; **candidate from `t_d`** if certified | `[t_c, t_e)` | monitor candidate-vs-incumbent from `t_d`; alarm returns to incumbent |
| `revert_while_certifying` | incumbent | **reference from `t_r`**; candidate from `t_d` if certified (switch cost charged again) | `[t_c, t_e)` in the background, identical to `certify_promote` | reference monitor from `t_r` until `t_d` or alarm; candidate monitor from `t_d`, sharing one cap |

Rollback monitor (identical wherever it is attached, so "rollback with parity" means every arm that deploys something carries the same monitor): ungated HT, rate 0.20 on the shared query uniforms, alpha 0.015, bound `5/0.2 + 0.05/(n - start)`, harm = deployed cost minus incumbent cost, amortised threshold `0.05 / (n - start)`, **one 160-label cap per arm** shared by its monitors. On alarm the policy acts until the alarm event, then the incumbent acts. After a rollback the arm remains on the incumbent (no re-entry), except that `revert_while_certifying` may still promote a candidate at `t_d`.

Per-stage label caps (L3, identical for all arms in a cell): Q1 monitor `0.40 x` window length (320 at coverage 1600, 960 at coverage 3200); certification 320; rollback 160. Total hard cap = sum (`e3.total_label_cap`). Unlike the legacy pipeline the certification cap is not reduced by Q1 spend.

## 3. Factors and exact levels

| Factor | Levels |
|---|---|
| response | `revert`, `certify_promote`, `revert_while_certifying` (plus `continue` as the zero-utility anchor and resource baseline) |
| rollback | `off`; `parity` (every deploying arm carries the section 2 monitor) |
| monitoring coverage | `short`: Q1 window `[800, 1600)`; `long`: `[800, 3200)` (same rate 0.40; cap scales with the window, so `long` costs more labels when no alarm occurs, reported) |
| harm onset (incumbent becomes all-positive; harmful adaptation) | `before` = **800** (monitor start); `at` = **1600** (legacy monitor end, equals the `short` coverage end); `after` = **2000** (inside the legacy scout/certification stage, after the short window closed) |
| post-alarm reference | `safe`; `deteriorating` (section 3.1) |

24 cells (onset x coverage x rollback x reference) x 4 responses = 96 rows per seed. With `short` coverage and onset `at` or `after` the Q1 window closes before the harm can be seen, so no alarm occurs and all arms equal the incumbent by construction; this is retained as a descriptive control.

Incumbent and reference. Incumbent: `1{x0 - 0.9 x1 >= 0}` until the onset, all-positive afterwards (the existing `harmful_adaptation` mechanism with a movable onset). Reference: the frozen source cost-optimal rule (`decision_harm_experiment._source_action`). Candidate family and target scout: the existing 13-policy logistic family fitted on events `< 800` only, unchanged by onset or reference state.

### 3.1 Reference deterioration (evaluator side only)

Let `t_a^safe` be the Q1 trigger computed on the **safe** labels for the cell's onset and coverage, and `T_d = t_a^safe + 1` (`T_d = n` if there is no alarm). In the `deteriorating` state, for `t >= T_d` the latent target is shifted: `target'_t = target_t + 0.6`, `y'_t = 1{target'_t > 0}`, `p'_t = Phi((score_t + 0.6) / 0.3)` with `score_t = x0 - 0.9 x1`. Features are unchanged (pure concept shift). Consequences:

- Labels for `t < T_d` are identical in both states, so the Q1 history, trigger, labels and the whole pre-alarm state are identical across the reference factor (tested: `test_reference_deterioration_starts_after_trigger_and_keeps_history`). The deterioration cannot create or suppress the alarm.
- "Post-alarm" is defined by the cell's common Q1 trigger, which every arm shares (L1). The deterioration time is therefore the same for all arms. This makes the generator depend on a function of the labelled history up to `t_a`; it affects only events after `t_a`.
- The fixed reference then misses boundary-region positives (FN cost 5): its expected per-event cost rises from about 0.13 to about 0.46, against about 0.33 for the all-positive incumbent and about 0.14 for the best frozen candidate (one development seed, `t3` check, not a population claim).

The shift 0.6 was chosen **after** inspecting oracle costs on dev seed 100200003 and the first dev outputs. It is one registered operating point. Sensitivity runs at 0.3, 0.45 and 1.0 (dev only) are in section 8.

## 4. Hypothesis H-B3 and the registered contrasts

Per seed `s`, let `U_r(cell)` be the utility of response `r`. Define the primary stratum **S\* = {onset = before} x {rollback = parity}**, with the per-seed value averaged over the two coverage levels (the two cells are not independent; averaging keeps one scalar per seed). Let `d_state = U(revert) - U(certify_promote)` in S\*.

| ID | Statement (one-sided, alternative) | Per-seed scalar |
|---|---|---|
| **C1** (interaction, the H-B3 contrast) | `Delta = d_safe - d_deteriorating > 0` | `d_safe - d_det` |
| **C2** | revert beats promote when the reference stays safe: `d_safe > 0` | `d_safe` |
| **C3** | promote beats revert when the reference deteriorates: `d_deteriorating < 0` | `-d_det` |
| **C4** | background certification adds to reverting when the reference deteriorates: `U(revert_while_certifying) - U(revert) > 0` in the deteriorating state | difference |

Test: one-sided paired t-test on the per-seed scalars (paired by seed, df = n - 1). **Holm over {C1, C2, C3, C4} at 0.05.** A paired percentile bootstrap (10,000 draws, seed 20261030) is a sensitivity interval; the confirmatory decision is the Holm-adjusted t-test, and a disagreement with the bootstrap is reported. Outcomes: **crossover supported** if C1, C2, C3 all reject; **interaction without full crossover** if only C1 rejects; otherwise H-B3 is withdrawn and the finding is reported as "ranking set by timing and rollback only". C2 is a superiority test (stricter than the "revert >= promote" wording); failing C2 alone does not withdraw C1.

Everything else is **descriptive**: single-factor main effects, all-cell interaction table (`all_cell_interactions_descriptive.csv`), per-cell means with SD, realised-versus-expected, label/compute/intervention tables, the non-primary onsets and rollback levels. No attribution percentages. **All seeds are analysed**, including no-alarm streams and infeasible certifications; the analysis asserts a complete seed x cell x response grid.

## 5. Seeds, mapping and sample size

| Block | Registry id | Range | Use |
|---|---|---|---|
| dev | `e3_dev_smoke` | 100200000-100200999 | CPU smoke, parameter and variance study, development only |
| confirmation | `e3_confirmation` | 100300000-100309999 | one registered run |

**Seed-to-cell mapping (exact).** Seed `s = block_start + i`, `i = 0 .. n-1`. Every seed enters **all 24 cells and all 4 responses** (96 rows), so seeds are paired across every factor and "n per cell" equals the number of seeds. Stream seed is `s`; query uniforms are `default_rng(s + 700001).random(3200)` (shared by every arm and cell: L2); the candidate family is fitted from the stream of seed `s`. No seed is dropped or replaced. Confirmation uses seeds `100300000 .. 100300000 + n - 1`; the unused tail stays reserved.

**Power / n.** From the dev block (n = 200 seeds, section 8): per-seed S\* means and SDs give, for power 0.9 at one-sided level 0.05/4 with effects shrunk by 25%, n = 3 (C1), 5 (C2), 2 (C3) and **304 (C4)**. **Registered confirmation n = 1000** (about 3.3 x the largest requirement; it keeps power 0.9 for C4 if the true effect is as small as about 0.4 x the dev estimate). Cost: about 9 minutes with 3 workers on CPU. The sample size is fixed in advance; there is no interim look and no optional stopping.

## 6. Stop rules

1. **Implementation stop (before and during the run):** any failing test in `tests/test_e3_intervention_factorial.py`; a label cap violation; a row count other than `n x 96`; a Q1 trigger that differs across reference states or across arms in a cell; non-finite utilities. Fix the implementation, then rerun the **dev** block, never the confirmation seeds; record the failure.
2. **Freeze gate:** the confirmation run needs (a) this protocol frozen with a SHA-256 freeze record, (b) a Codex protocol review, (c) a clean git tree. Parameters in section 3 and the contrasts in section 4 may not change after the freeze.
3. **Feasibility gate (dev, re-checked before freeze):** S\* alarm rate at least 0.9 under `short` coverage and certification not infeasible in S\*. Dev: 0.98 and 0.00.
4. **Claim rules:** H-B3 is withdrawn independently if C1 fails (proposal section 8). A power shortfall is reported as inconclusive only if the achieved precision of C1 is worse than registered; it is not a rule for adding seeds.
5. **No adaptive follow-up on confirmation seeds:** no change of shift, onsets, caps or contrasts after any confirmation output has been seen. Post hoc analyses are labelled as such.
6. **Compute:** CPU only. The factorial is CPU-feasible (section 8); no CUDA is needed or approved.

## 7. Known limitations (carried into any write-up)

- **Crossover mechanism is largely abstention.** In the deteriorating state the certify arm certifies in only about 7% of dev streams; its advantage over reverting comes mostly from staying on an incumbent that has become better than the deteriorated reference, not from a promoted candidate (at shift 1.0 it certifies in 0% and the contrast is entirely "do not revert"). The registered `certified` indicator and the conditional utility (mean +206 when certified in dev) must accompany any C3 statement.
- **Generator-constructed operating region.** The shift 0.6 and the post-trigger timing were chosen to make a crossover possible; section 8 shows it is absent at 0.45 and below and degenerate at 1.0. H-B3 at one point does not locate a region.
- **Rollback parity is nearly inert here** (reference rollback in about 2% of deteriorating revert streams; utility change under 3 per seed). Parity is satisfied by construction; its power at these caps is low.
- **Coverage is bundled with label spend** (cap proportional to the window); onsets `at`/`after` with `short` coverage are undetectable by design.
- Synthetic stationary-outcome stream, immediate labels, non-performative; the oracle utility is not a real application utility; the switch/rollback cost scale (0.05) is imposed.
- The certification step is the existing Q2 (uniform-query path); the full-cost net-benefit question is not tested (section 1).
- Seed reuse: the registry marks the two E3 blocks `reserved_unused`; they must be updated to record the dev runs below.

## 8. Implementation and smoke record

**Files (new, uncommitted):** `src/shiftlab/dive/e3_intervention_factorial.py`, `scripts/run_e3_intervention_factorial.py`, `scripts/analyze_e3.py`, `tests/test_e3_intervention_factorial.py`. `integrated_pipeline.py` and every existing file are unmodified. Reused by import: `_generate`, `_source_action`, `_fit_candidate_family`, `_monitor_scout_context_policy`, `_candidate_outcome_contrasts`, `BoundedMeanEProcess`, and the Q1 / rollback / cost constants. Copy-adapted (because `run_seed` is monolithic and bakes in the stage boundaries): the Q1 loop, the rollback loop, the onset transform, the policy timeline, the revert-while-certifying arm, rollback parity and the deterioration generator. The learner family passed to the scout has `h_truth` and `h_proxy` replaced with zeros (decoy), so the scout cannot read oracle quantities.

**Quality checks:** `uv run --no-sync pytest tests/test_e3_intervention_factorial.py -q` gives 11 passed (timeline indices, matched trigger, revert-while-certifying equals revert and certify on the shared parts, rollback parity and off, per-stage caps, deterioration keeps pre-alarm history and Q1 result, learner functions take no oracle argument and decisions are unchanged when the oracle is NaN-poisoned, rollback monitor behaviour, certification infeasibility, exact registered levels). `ruff check` and `ruff format --check` are clean on the four files.

**Commands (HEAD `ef60fc0` at run time; working tree dirty only with these new files):**

```
uv run --no-sync python scripts/run_e3_intervention_factorial.py --block dev --n-per-cell 200 --out outputs/e3/dev_smoke_n200 --workers 3 --device cpu
uv run --no-sync python scripts/analyze_e3.py --rows outputs/e3/dev_smoke_n200/e3_rows.parquet --out outputs/e3/dev_smoke_n200/analysis
uv run --no-sync python scripts/run_e3_intervention_factorial.py --block dev --n-per-cell 100 --out outputs/e3/dev_sens_shift_<S> --workers 3 --shift <S>    # S in 0.3, 0.45, 1.0
```

**Runtime and feasibility.** About 2.4 s per seed (all 96 rows) single process, including stream generation and the 13-policy fit; 200 seeds took 104 s with 3 workers (seeds 100200000-100200199, 19,200 rows, config sha256 `3e6628d0...7ea9a0`, manifest in the output folder). Workers above 3 died with `BrokenProcessPool` under this machine's memory pressure (about 0.9 GB free at the time); the runner then finishes the remaining seeds sequentially. The confirmation at n = 1000 is about 9 minutes with 3 workers or about 40 minutes single process. **The full factorial is CPU-feasible; no CUDA is required and none was used.**

**Development results (development-only, not confirmatory; n = 200 seeds, S\*, utility `expected_net_gain_vs_incumbent`):**

| Contrast | mean | SD | one-sided p | bootstrap 95% CI | Holm |
|---|---|---|---|---|---|
| C1 interaction | 700.9 | 214.3 | < 1e-4 | [671.2, 730.1] | reject |
| C2 revert > promote (safe) | 439.4 | 192.6 | < 1e-4 | [412.8, 466.0] | reject |
| C3 promote > revert (deteriorating) | 261.5 | 75.6 | < 1e-4 | [251.4, 271.9] | reject |
| C4 background certification over revert (deteriorating) | 23.8 | 88.2 | 1e-4 | [12.6, 36.4] | reject |

Dev verdict `crossover_supported` (development only; the dev block informed the generator, so this is not independent evidence). Descriptive means, onset `before`, parity, `short` coverage:

| State | revert | certify_promote | revert_while_certifying | certified rate | mean labels (revert / promote / RWC) |
|---|---|---|---|---|---|
| safe | 723.5 | 289.5 | 704.0 | 0.69 | 319 / 579 / 625 |
| deteriorating | -244.9 | 14.4 | -221.2 | 0.07 | 318 / 480 / 625 |

Realised and expected net gain agree (revert 108.6 vs 109.5 pooled over all cells). Onsets `at` and `after` give alarms only under `long` coverage (alarm rates 1.00 and 0.93; certification infeasible in 20% and 85% of those streams) with the same sign pattern but smaller magnitudes (interaction 430 and 233); under `short` coverage they have no alarms and zero utility for every arm.

**Sensitivity of the deterioration shift (dev only, n = 100, onset `before`, parity, `short`; mean `U`):**

| shift | revert (safe / det) | certify_promote (safe / det) | certified rate (det) | crossover? |
|---|---|---|---|---|
| 0.30 | 719.0 / 399.7 | 287.0 / 54.0 | 0.17 | no (revert wins in both) |
| 0.45 | 719.0 / 109.4 | 287.0 / 29.7 | 0.11 | no (revert still wins) |
| 0.60 (n = 200 main run) | 723.5 / -244.9 | 289.5 / 14.4 | 0.07 | yes |
| 1.00 | 719.0 / -377.0 | 287.0 / 0.0 | 0.00 | yes, degenerate (promote never certifies) |

The crossover threshold lies between 0.45 and 0.60 on this generator.

**Continue / pivot / stop assessment.** Continue to the freeze step. The CPU factorial runs, the invariants hold and a crossover exists at the registered point. Two caveats must travel with it: the crossover is mostly the cost of reverting into a deteriorated reference rather than the benefit of promoting a candidate, and the operating region is narrow and constructed. Before freezing: (1) Codex protocol review, in particular of the definition of `T_d` (a generator keyed to the common Q1 trigger) and of the S\* choice; (2) decide whether the registry entries for the dev runs should be marked used; (3) decide whether a second deterioration level (for example 0.8) should be registered as a descriptive check.
