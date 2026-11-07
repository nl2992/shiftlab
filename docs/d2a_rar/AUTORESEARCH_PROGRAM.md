# AUTORESEARCH_PROGRAM (Drift2Act / RAR hosts)

Operating program for the autonomous method-search agents, in the spirit of karpathy/autoresearch's
`program.md` (fixed budget per experiment, keep/discard, append-only log) but **without its single-metric
rule**: here a change is kept on a *Pareto* judgement of J under validity, never on one scalar. Read first:
`AGENTS.md`, `MANDATE.md`, `BENCHMARK_CONTRACT.md`, `CANDIDATE_REGISTRY.md`, `PRIOR_ART_LEDGER.md`,
`FAILURE_ATLAS_CORRECTED.md`, `registry/null_assumptions.yaml`.

## 0. Hard rules (non-negotiable)

1. **Read-only for method agents:** benchmark definitions (`src/shiftlab/bench/contract/`, `configs/d2a_rar/`,
   `configs/seed_registry.yaml`), the frozen dev suite (`src/shiftlab/autoresearch/dev_suite.py`,
   `registry/DEV_SUITE.json`), cost vectors, the confirmation families and the holdout. Method agents edit only
   their candidate code behind a host hook (and tests for it). Missing stream family => write a TODO for the
   coordinator; do not edit the configs.
2. **Holdout hygiene:** the confirmation seed block (`d2a_rar_confirmation_reserved`, 120000000-120099999) is
   refused by the ledger unless `stage == "D"`. Agents do not share holdout outcomes and never tune on a failed
   confirmation and relabel it. Stage D needs a registered `CONFIRMATION_PROTOCOL.md` first.
3. **Record every negative result**, including crashes, invalid, duplicate and unverified runs, in
   `registry/EXPERIMENT_LEDGER.jsonl`. A dropped run is a protocol violation.
4. **Never compare invalid-aggressive with valid-conservative as equals.** Each method is judged on false
   promotion only under *its own* `target_null` (cond / marg / absolute_risk). A cond method is never scored
   on a marg-null false-promotion rate (the P2 error); such cells are labelled out-of-contract stress.
5. **No fabrication:** no invented results, theorem validity, prior-art conclusions or hardware numbers. A failed
   search is not novelty. Fidelity tier (AUTHOR_NATIVE / PAPER_RECONSTRUCTION / COMMON_CONTRACT_PORT /
   CONCEPTUAL_PROXY) is recorded on every run; Drift2Act and RAR are PAPER_RECONSTRUCTION hosts.
6. CPU-sized runs only; no large downloads; long compute is detached with checkpoints (see plan).

## 1. Objects

* **Candidate identity** (`registry/CANDIDATE_REGISTRY.jsonl.gz`): host x question x mechanism x null x knobs,
  with hypothesis, predicted win/failure regions, falsification test, required baselines and prior-art status.
  Pick from `registry/stage_b_batch_001.jsonl` (200 identities, highest priority first). Identities with
  `blocked_by` (a failure-ledger `do_not_repeat_without` match) need a written `new_mechanistic_hypothesis`;
  Q3 identities are `blocked_until: Q1 and Q2 winners`.
* **Primary metric J** (after all costs, `BENCHMARK_CONTRACT.md` section 3), reported with a paired bootstrap CI
  over shared seeds, always **with its components** (loss, c_q N_q, c_s N_s, c_r N_r, c_b N_b, c_a N_a, c_h N_h).
* **Validity under the claimed null** (false promotion / false rollback on streams where *that* null holds;
  absolute-risk violations for Drift2Act-type gates), safety violations, power/delay, label use and pending
  utilisation, unnecessary retrain, canary overhead / rollback latency, compute.

## 2. The loop

```
for candidate in batch (priority order, skipping blocked):
  A  PREFLIGHT   shiftlab.autoresearch.preflight.preflight(candidate)       -> verdict (below)
  B0 IMPLEMENT   minimal diff behind the candidate's hook; unit test; ruff
  B  SCREEN      <= 300 s active compute, fixed timeout, frozen light dev suite (section 3)
  L  LOG         shiftlab.autoresearch.ledger.append(record)               (every outcome, incl. crashes)
  D  DECIDE      KEEP / DISCARD / CRASH / INVALID / DUPLICATE / UNVERIFIED by the rules in section 4
checkpoint review after 200 experiments  ->  Stage C (<= 20)  ->  Stage D (<= 3)
```

### Stage A: preflight (no compute beyond hashing)

`preflight()` returns one of: `ELIGIBLE`; `INVALID` (grammar violation or identity not reproducible from the
grammar); `BLOCKED_BY_LEDGER` (matches a `do_not_repeat_without` and declares no new mechanistic hypothesis;
recomputed from the grammar, a record cannot hide its own block); `BLOCKED_UNTIL_WINNERS` (Q3);
`DUPLICATE` (same candidate and stage already decided in the ledger; a CRASH may be retried);
`INELIGIBLE_NULL_MISMATCH` (scoring null differs from claimed null, null not allowed on the host, or no required
baseline shares the claimed null); `BLOCKED_HOST_NOT_PORTED` (no importable COMMON_CONTRACT_PORT adapter; this
is a blocked state, **not** INVALID); `BLOCKED_HOOK_MISSING` (hook not exposed by the host package). The verdict
carries the config hash, the hook-module source sha256, the adapter-module sha256, the git commit and the
validity plan (which dev-suite cells score false promotion for this null, which are stress-only); store these in
the ledger. Leakage/release/budget/cost guards are *not* reimplemented: run them with
`preflight(..., smoke=True)` or `run_named_smoke()` (a named subset of `tests/d2a_rar/test_contract.py`) and run
the full contract tests before the first Stage-B run of a new adapter. Only `ELIGIBLE` proceeds. Unsupported
adaptations are logged as `INVALID` with `invalid_reason`; ported-host gaps are logged `UNVERIFIED`.

### Stage B: screen (initial budget 200 experiments)

* **Budget:** <= 300 s active compute per experiment, hard timeout (a timeout is a `CRASH` with `error`, not a
  silent truncation). Fixed workload and shared seeds for the whole batch (section 3).
* **Preregister before the run** (written into the ledger record's `preregistered_predictions`): the primary
  metric and region (from the identity's `predicted_win_region`), the null, the strongest comparator, the
  expected sign/size category (substantial / meaningful / small, section 4) and the failure region.
* **Comparators:** every `required_baselines` entry that is implemented in the contract (uniform, pending cap,
  fixed schedule, front-loaded, Drift2Act native audit, ASI-inspired, Gong-Zhang paid-obs, PAVE for Q2; Markov-LR,
  Sethi plug-in on thinned chain, fixed spacing, restart-without-gaps, conditional-null certifier, Page-CUSUM for
  Q1; unmodified RAR **and** Cost-Aware Binary for RAR-gate candidates). Unimplemented comparators are listed
  in the record as `missing_baselines`; a result without the strongest *implemented* comparator is `UNVERIFIED`.
* **Mechanistic ablation** (hook restored to the host default) is part of every screen that claims an effect.

## 3. Frozen light dev suite

Definition: `src/shiftlab/autoresearch/dev_suite.py` (checksum in `registry/CANDIDATE_REGISTRY.sha256.json`);
families from `configs/d2a_rar/stream_families.yaml`, cost vectors from `configs/d2a_rar/cost_vectors.yaml`
(frozen, checksum-verified at load). Seeds: block `d2a_rar_dev` (110000000-110099999),
`seed = start + cell_index*1000 + replicate`, 20 replicates per cell, identical across all methods
(`run_paired`), T = family default (1000), label cap 50, retrain duration 20. RAR-family hosts use cost vector
`intervention_dear`; others use the cell's vector.

| Question | correct-null cell | adverse stress cell | alternative | neighbouring / negative control |
|---|---|---|---|---|
| Q1 (gap evidence) | `iid_null_boundary` (cond+marg hold), `balanced` | `markov08_marg_null_only` (marg holds, cond fails), `balanced` | `markov05_shift_d10`, `balanced` | `iid_null_lognormal_delay`, `balanced` |
| Q2 (acquisition / decisions) | `iid_null_boundary`, `label_dear` | `iid_shift_informative_missing` (selective feedback), `label_dear` | `iid_shift_geo20` (long right-tailed delay), `label_dear` | `iid_null_lognormal_delay`, `label_dear` |

Reading rules: false promotion is computed on `validity_cells` for the candidate's own null only
(`dev_suite.cells_for`); the adverse-dependence cell is a *validity* cell for marg methods and *labelled
out-of-contract stress* for cond methods. The neighbouring/negative control must show no extra promotion or
spend versus the host. Negative and neighbouring controls are cells of this frozen suite, **not** candidates.

**TODO for the coordinator (missing families; not edited here):** a reversal stream (F9 / FL-043); a hazard or
semi-Markov regime-duration family; a subgroup-shift family; proxy/side-information streams and
`ObservableState` proxy predictions (WP2c); a tight-deadline family with a hard promotion window shorter than the
delay tail (`iid_shift_geo20` is the nearest proxy); a RAR-native persistent-drift family with label-frontier
semantics (canary candidates currently run on the contract `route()` split only); informative gap choice (only
approximated by `iid_shift_informative_missing`). Candidates that need an absent family are `UNVERIFIED` until it exists.

### 3a. Amendment A1: DEV_SUITE_v2 for Stage-B tranche 2 (registered 2026-11-07, before any tranche-2 run)

Why: the v1 suite (B/T = 5%, label cap 50) makes both hosts' statistical thresholds unreachable
(`status/wp6_host_audit.md`), so host-hook candidates were inert (40 DUPLICATE). v1 results stand unchanged; v2 is
used **alongside** v1, not instead of it.

- **Suite:** `registry/DEV_SUITE_v2.json` (sha256 `414eacd0…630659`), families `configs/d2a_rar/stream_families_v2.yaml`
  (sha256 `9cd53491…40f898`). 15 cells S1a-S4c, each triple = alternative / correct null / neighbouring negative
  control; per-cell T, label cap and cost vector as recorded in the JSON. Seeds: `110050000 + cell_index*1000 +
  replicate`, 20 replicates, paired across methods.
- **Hosts:** profile `calibrated_v1` for Drift2Act, RAR, Cost-Aware Binary and Binary (frozen at commit
  `87772d33`; no constant revisited after any result). `native_v0` is run once per cell as a reported reference.
- **Comparator set (every v2 cell):** the candidate's host (`calibrated_v1`), `uniform_query`, `fixed_schedule`,
  `pending_cap`, `episode_front`, `never_switch`, and two valid conditional-null certified promoters from
  `adapters_inrepo`: Gap-Mix `exact0.8_s4` and the gap-10 thinned gate. "Strongest applicable comparator" in §4 is
  the comparator with lowest mean J on that cell **among comparators valid for the candidate's claimed null on its
  validity cells**; naive GainSwitch controls that false-promote on S2e/S2f do not count as the strongest comparator
  on those cells.
- **Scope of tranche 2:** (i) identities decided `DUPLICATE` of a host-identical behaviour in tranche 1; (ii) identities
  `UNVERIFIED` for a missing family that v2 now provides; (iii) Q1 evidence identities once the label-outcome evidence
  hook exists (they enter with a further amendment line naming the hook commit). Budget: at most 140 experiments,
  bringing the Stage-B total to the registered 200.
- **Decision rule:** §4 unchanged, applied per suite; a candidate must not be worse than its host on any v1 cell it
  ran on. Mandate Q2 stop rule: if Q2 candidates on v2 at best match `pending_cap` / `fixed_schedule`, Q2 is
  recorded NEGATIVE and its line stops.
- **Frozen after registration:** any change to cells, seeds, comparators or hosts after the first tranche-2 record
  requires amendment A2 with a fresh seed sub-block; results under A1 are never re-labelled.

## 4. Keep / discard (preregistered; no single-metric rule)

A candidate is **KEEP** (promote to the Stage-C queue) iff all of:

1. **Validity under its claimed null:** on its validity cells the false-promotion (or absolute-risk violation)
   rate is within the level it claims (n = 20 paired seeds per cell is a screen, so report the Clopper-Pearson
   upper bound and mark "screen-level" if it cannot resolve alpha).
2. **Pareto on J:** paired difference in J (after all costs) versus the strongest *applicable* comparator is not
   worse on the neighbouring/negative-control cell, and is better on at least one target cell. A candidate that
   improves J only by relaxing validity (invalid-aggressive) is `DISCARD` against a valid comparator and is
   reported on a validity-J Pareto plot, never as a win.
3. **Graded effect label** (labels, **not** pass/fail gates; relative to the strongest comparator's J):
   *substantial* >= 10%; *meaningful* 3-10% with the paired CI excluding 0; *small* 1-3%; below 1% or CI
   containing 0 is *none*. Substantial and meaningful effects rank first for Stage C; small effects are kept only
   if cheap (complexity <= 2) and the mechanism ablation erases them; *none* is `DISCARD`.
4. **Simple controls:** if the candidate does not beat the pending cap / fixed schedule (Q2) or the thinned/
   fixed-spacing Markov-LR (Q1), record `DISCARD` with a NEGATIVE note (Mandate Q2: stop that line, do not tune).
5. Records `counterexamples`: the worst cell and any validity or regression-cell failure, including the two
   mandatory regression cells inherited from the Atlas (long-delay family-1; rho = 0 earlier-onset B/T 0.1).

`DUPLICATE`: same behavioural signature already decided. `INVALID`: protocol/guard violation, null mismatch or
leakage. `CRASH`: timeout/exception. `UNVERIFIED`: ran but a mandatory comparator or cell was unavailable.
`CONFIRM`: Stage D only.

## 5. Stages after B

* **Checkpoint review after 200 Stage-B experiments:** coordinator and Opus review the ledger (survivors,
  negative results by family, null-mismatch incidents, duplicate rate); decide continue / pivot / stop; update
  the batch (batch_002) only from the registry, with new identities appended, never silently altered.
* **Stage C (<= ~20 promoted):** more seeds and regimes, more baselines, ablations, paired CIs, separated cost
  components, validity under the claimed null, power/delay, robustness (dependence, delay law, informative
  missingness), strongest SOTA host plus simple controls. Seeds still from `d2a_rar_dev` (disjoint cell indices
  from Stage B) or fresh registered blocks; never the confirmation block.
* **Stage D (<= ~3 frozen finalists):** `CONFIRMATION_PROTOCOL.md` is written **before** the holdout is touched:
  implementation/version (git commit, hook source hashes), primary metric and region, baselines and how the
  strongest is selected, data/seeds/periods (untouched sources where possible), the null, confidence level,
  multiplicity correction, accept/reject rule, negative controls. Run once; results to `CONFIRMATION_RESULTS.md`
  and ledger decision `CONFIRM`/`DISCARD`. A failed confirmation is reported, not tuned and relabelled.
* **Q3 factorial** (J00/J10/J01/J11, `I = (J00-J11) - [(J00-J10)+(J00-J01)]`) is unlocked only after a Q1 and a
  Q2 winner exist; no synergy claim if the combination is approximately the best single; negative interactions
  are reported (GAVE-R FL-030 is the prior).
* Exit state per Mandate: `METHODS_CANDIDATE`, `BENCHMARK_ONLY` or `NEGATIVE_RESULT`; never manufacture a positive.

## 6. Ledger record (Phase 8) - one JSON line per run

Required: `candidate_id`, `run_id` (unique), `stage` (A-D), `git_commit`, `method`, `host`, `fidelity_tier`,
`data_hashes`, `seed_group {block, seed_start, seed_end, exposure in smoke|dev|confirmation}`, `hardware`,
`runtime_s`, `null_class`, `assumptions`, `preregistered_predictions` (non-empty for stages B-D unless
CRASH/INVALID/DUPLICATE), `results`, `uncertainty` (for KEEP/DISCARD/CONFIRM), `baseline_relative`,
`counterexamples`, `prior_art_status`, `decision`; plus `error` (CRASH), `invalid_reason` (INVALID),
`duplicate_of` (DUPLICATE). `timestamp`, `prev_sha256`, `record_sha256` are set by `ledger.append`, which verifies
the whole hash chain first and only appends. Pin `ledger.head()` in the commit message after each checkpoint to
detect tail rewrites. Verify: `python -c "from shiftlab.autoresearch import ledger; print(ledger.verify())"`.

## 7. Commands

```
PYTHONPATH=src python scripts/d2a_rar/build_candidate_registry.py          # rebuild registry + batch + md (deterministic)
PYTHONPATH=src python scripts/d2a_rar/build_candidate_registry.py --check  # confirm committed files match the code
PYTHONPATH=src python -m pytest tests/d2a_rar/test_autoresearch.py -q
```

## 8. What this program does not claim

It selects and screens hypotheses. It does not establish novelty (prior-art status is the WP4 spot-check, with
unmapped families UNVERIFIED), validity of any proposed certificate, or superiority over any host. Dev-suite
screens are development evidence on exposed seeds; only a registered Stage-D run is confirmatory.
