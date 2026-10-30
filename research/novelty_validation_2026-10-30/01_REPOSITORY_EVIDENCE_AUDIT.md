# 01. Repository evidence audit

Date 2026-10-30. Auditor: this session (independent of the agents that wrote the H2c/HG lineage, but **not** a
different human or lab; every claim below marked "repository-reported" was produced by earlier agent sessions).

## 1. Branch ancestry (computed after `git fetch --unshallow`; the first clone was shallow and its merge-bases were wrong)

All research branches fork from `main` at `ec42a2d`; `main` (4cf3c73) has since moved on by Lane A/B work that the
research branches do not contain.

| branch (origin/research/…) | tip | relation |
|---|---|---|
| `hg-validation-and-novelty-2026-10-30` | 1299c1c | ancestor of h2c-strong, h2c-restart, icml-sprint |
| `h2c-strong-baselines-and-generalization-2026-10-30` | 60930a4 | ancestor of h2c-restart, icml-sprint |
| `h2c-restart-risk-certified-2026-10-30` | d4673d9 | ancestor of icml-sprint |
| `shiftlab-icml-method-sprint-2026-10-30` | 71ad2b3 | ancestor of `exhaustive-candidate-evaluation-2026-10-30` |
| `exhaustive-candidate-evaluation-2026-10-30` | a7c88d8 | **superset of the whole H2c/HG/sota-search line (102 commits ahead of main)** |
| `shiftlab-mandate-gap-closure-2026-10-30` | 8552911 | **not** in the exhaustive line; ancestor of dependence-gates |
| `shiftlab-dependence-gates-2026-10-31` | 026500d | sibling line (shares only `bb74057` sota-search with the others) |

**Working base chosen:** `exhaustive-candidate-evaluation` (a7c88d8), merged into this branch without conflicts
(commit 28f8a2d, `--no-ff`; no history rewritten; `main` untouched; no force-push). The mandate-gap/dependence line
was **not** merged (it is a sibling line); its documents were read via `git show` and are cited, not imported.
`main`'s Lane B documents (`docs/lane_b_burst_allocation/`, `docs/g1_*`) are present in this branch via the original
base.

## 2. Test baseline (before any change of mine)

`uv sync --all-extras` (Python 3.13.17, numpy 2.5.4, scikit-learn 1.9.1, pandas 3.0.6, scipy 1.18.1).
`pytest -q -x --ignore=tests/data`: **1475 passed, 4 skipped** (564 s). `pytest tests/data`: **899 passed, 4 skipped**.
No failures. (A first attempt without the synced environment failed at import; that is an environment fault, not a test fault.)
Programme tests added by this work: `research/novelty_validation_2026-10-30/tests` (4 passed).

## 3. Claim ledger (classification uses the task's vocabulary)

| claim (source) | class | what I did / why |
|---|---|---|
| H2c beats the better of cost-only discounted Kelly / ONS by +0.086 / +0.094 absolute power at 10 / 20 % labels, 13/14 and 14/14 harmful cells (`docs/h2c_next/FROZEN_CONFIRMATION_RESULTS.md`) | **CONFIRMED, narrowly** | Single run of a frozen protocol on fresh seeds. Caveats: 6 of 8 conditions were development conditions re-used with new seeds; runner crashed *after* simulation and analysis was redone from the saved file; one generator family; comparators are local adaptations. The icml-sprint replayed the cell file (+0.086 [0.061,0.110]); the exhaustive-evaluation branch reproduced one cell path-for-path (600 paths). **I did not re-run the G5 simulation.** |
| Tolerance-aligned (eps = 0.10) within-class gain retained, power only .136 / .256 (`docs/icml_sprint/07`) | **DEVELOPMENT_ONLY** | Fresh dev seeds, not a frozen confirmation. A coupling bug (tolerance passed to the guidance statistic) was found and fixed in that run. |
| "H2c is decision-aware with benign false alarm ≤ .067; Brier methods over-alarm" | **FALSIFIED as stated** | Estimand mismatch: zero-tolerance null scored against a 0.10 harm label (`icml_sprint/02`). Where cost does not increase, HG alarms at ~1 %. |
| H2c e-process valid under the zero-tolerance conditional cost null (fixed/independent delay) | **PROVED (by repository, re-derived in 08)** | Bounded increments, predictable bet, uniform support cap. |
| HG marginal-null validity with covariate-dependent cap | **FALSIFIED**; uniform-support-cap repair retained | `docs/hg_validation/02_VALIDITY_COUNTEREXAMPLES.md`. |
| Nominal-risk estimation removes power below ~5,000 calibration events | **DEVELOPMENT_ONLY** | `docs/h2c_restart/NOMINAL_RISK_UNCERTAINTY.md`; consistent with my D2 (n_cal = 622, Hoeffding margin 0.30 vs mean cost 0.011). |
| Valid restart / e-detector mixtures add +0.003–0.023 | **DEVELOPMENT_ONLY**, no gain | Known construction. |
| Paper-1 monitoring search NO-GO (`docs/algorithm_search_exit_ledger.md`) | registered **NO_GO**; **preserved** | I do not reinterpret any engine variant as a new monitoring algorithm. |
| Dependence-monitoring NO_GO (`dependence_sprint/05`) | registered **NO_GO**; **preserved, not reopened** | No new assumption class / theorem target proposed here. |
| Q2/Q3: disagreement-targeted certification ≈ CAMS-style; controllers do not beat recalibration/retraining/drift switching | **DEVELOPMENT_ONLY / negative** | Not re-run. |
| 1,836 effective combination tuples evaluated, best cost reduction 4.07 % (below its 10 % gate) (`exhaustive_evaluation/CORRECTIONS_AND_LEDGER.md`) | **DEVELOPMENT_ONLY** | Counts include withdrawn aliases (108 inactive aliases removed). |

## 4. Provenance cautions that matter for every number above
* Same agent wrote the code and the audits in the H2c lineage; independent reproduction = one cell path-exact (600 paths) plus a cell-file replay.
* Exhaustive-evaluation records a withdrawn count report, a withdrawn `harm_to_alarm` interpretation (v1 evaluator
  gave positive harm under the null), and a pandas `NA`-parsing hazard for the literal case name `null`. All retained.
* Real-data development streams (Bike, Beijing, UCI gas batches 3–10, CRSP 2020–2025) are **exposed**; none can confirm.
