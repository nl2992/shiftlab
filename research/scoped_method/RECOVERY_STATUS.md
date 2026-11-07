# Recovery and headroom checkpoint (2026-11-06)

## Phase 0 — CI recovery

The reported GitHub Actions run was `42179919497` at commit
`e7f4dca60c3a39c5a97ceb21efb4b311d2d96e8b`. Its `uv run ruff check .` step failed with 506
findings (332 automatically fixable), primarily import ordering/formatting, unused `noqa`
directives, and redundant casts. Retrieved with:

```sh
gh run view 42179919497 --log-failed
```

The repair is already present in ancestor commit `82e1c48e` (`Fix Ruff lint and formatting checks`);
it changes Ruff formatting/lint findings across 137 files. This checkpoint does not redo that
repair or overwrite any experiment artifacts. Current branch: `codex/scoped-method-research-results-2026-11-06`,
starting commit `28e21f2c`.

Commands run on the current checkout:

```sh
uv run ruff check .
```

Result: **passed** (`All checks passed!`). Current GitHub Actions run `42307382928` also reports
success for locked dependency setup, Ruff lint, Ruff format check, and mypy. At checkpoint time its
full `uv run pytest -q` step was still in progress; environment validation was pending. Do not
interpret the full suite as passed until that run completes. No experiment or test output was
modified by this recovery note.

## Phase 1 — Reconciliation of prior evidence

| Observation to verify | Reconciled evidence |
|---|---|
| E_rb and B2 matched exactly on 90 pilot episodes | `research/scoped_method/pilots/rollback_acquisition_30seed_20261106/summary.json` records exact equality on the common-seed regime; the prior pilot covers three 30-seed environments (90 paired episodes). This is a specific implementation/pilot result, not general equivalence. |
| Never-switch beat E_rb in all three pilot environments | Same summary: E_rb minus never-switch is positive in `F3_reversal_800` (+46.20, 95% CI [+38.46,+53.94]), `F4_recurrent` (+34.53 [+26.04,+43.03]), and `S_reversal_400` (+26.93 [+17.48,+36.38]). |
| Conventional SR/CUSUM guarantees are incomparable absent calibration | `docs/scoped_method_research_2026-11-06/BASELINE_FIDELITY.md` distinguishes E_srr's ARL target from per-horizon/any-false-promotion probability. The economic matrix's E_srr port promoted on all 30 null streams; it cannot support an equal-safety advantage without separately calibrated null control. |
| Direct front-loaded acquisition + E_rb was not evaluated | This was true at the first headroom decision, but has since been evaluated in `research/scoped_method/pilots/direct_frontload_erb_20261106/`. The exploratory 20-seed/cell composition did not clear its economic gate and was worse than never-switch under reversal; protocol timing was not independently verifiable. |
| Adaptive-range correction changes historical provenance | Confirmed in `docs/failure_atlas_v2_flq/results/comparator_validity_audit_20261105.md` and `docs/scoped_method_research_2026-11-06/CORRECTED_REPLAY_AUDIT.md`. Pre-fix comparison tables are historical and must not be pooled with corrected results. |
| No independent real-data confirmation has been performed | No repair has independent real-data confirmation. A single-source chronological HuffPost replay was opened and was adverse to canonical PFA-SR; this is a negative transfer case study with simulated 24-hour label release, not positive confirmation of a repair. |

## Phase 2 — Economic opportunity decision

The precommitted five-cell, 30-paired-seed development matrix is in
`research/scoped_method/pilots/economic_headroom_matrix_20261106/`. It covers persistent gain,
economically worthwhile and unfavorable reversals, null, and delayed/scarce feedback under shared
horizon, budget, delay, query cost and switch cost. The feasible reference is never-switch; the
truth-aware oracle is evaluator-only. Main results and full cost decomposition are in
`run/RESULTS.md` and `run/summary.json`.

No certified/applicable policy passed the frozen gate of at least five net-cost units saved with a
paired 95% interval below zero in a worthwhile cell, while limiting harm in the unfavorable and
null cells. On the worthwhile reversal, E_rb was +25.63 cost units vs never-switch (95% CI
[+16.91,+34.36]) and E_swcert was +23.51 ([+14.34,+32.68]). On persistent and delayed/scarce gain,
E_rb's incremental savings against the frozen Xu-acquisition-only adapter were unresolved and
below the five-unit practical gate. The economic replacement reference is uncertified and does not
meet the null safety gate. Conventional E_srrSR reduced cost by 18.83 in the worthwhile reversal
cell (95% CI [-30.96,-6.71]) but promoted in 30/30 null streams; its ARL claim does not qualify it
for the same safety comparison.

**Decision:** tested environments do not identify safety-qualified economic headroom for a new
joint method. This rejects the tested candidates and compositions, not the whole research question
or all possible environments. Phase 3/4 novelty and candidate development gates are therefore not
entered. The smallest next step already specified in the matrix assessment is a prospective
any-false-promotion calibration of the conventional two-sided restart detector, then rerun only the
two reversal cells and null. No real-data confirmation should open before that gate.

## Reproduction

```sh
git status --short --branch
gh run view 42179919497 --log-failed
uv run ruff check .
gh run view 42307382928 --json status,conclusion,jobs
```

## Follow-up context-stratified MN-DS screen (2026-11-06)

A distinct Q3 source-heterogeneity screen was frozen in
`pilots/context_stratified_mnds_20261106/` and replayed once on Q4. The replay did **not** meet
the broader brief's synthetic economic-headroom and novelty gates before opening the data. For
that reason, despite its technical one-opening manifest, treat Q4 strictly as an exposed
descriptive screen and not as independent confirmation. Do not reuse Q4 as untouched evidence.

The publisher-stratified composition made no promotion, spent 5.00 in label cost, and cost 340.10
per 1,000, versus 338.47 for never-switch. Its point saving against the validation-selected static
policy was 2.29 per 1,000, below the registered 5-unit margin; the simultaneous 99% block interval
was [-5.75, +3.62]. It fails the frozen primary gate. Complete policy costs, source intervals,
limits, code/data hashes, and result checksums are in
`pilots/context_stratified_mnds_20261106/DECISION.md` and `run/RESULTS.md`.

This does not overturn the earlier conclusion that the calibrated conventional SR screen has a
narrow late-improvement advantage over certificate-style adapters, but it loses to the registered
Qiu/Gong-inspired cost ports and missed the independent 100-stream null precision gate. Its
1,000-stream calibration and the late screen are reported separately in
`pilots/srr_any_false_calibration_20261106/` and `pilots/srr_late_improvement_20261106/`.
No distinct method, independent real-data confirmation, or multi-dataset transfer result is
established. Current disposition remains `BENCHMARK_ONLY`; the smallest next work is a
claim-bounded case-study/manuscript outline, not another candidate search or holdout opening.

The research matrix reproduction command and frozen policy contract are preserved in
`research/scoped_method/pilots/economic_headroom_matrix_20261106/protocol.md`; this recovery
checkpoint does not rerun its prior experiment.

## Phase 3 — Calibrated CUSUM decision and external-source feasibility (2026-11-07)

The prospective any-false-promotion calibration was completed at
`pilots/cusum_any_false_calibration_20261107/`. Calibration and evaluation are separate frozen
runs; the 1,000-stream independent null evaluation had 6 false promotions (95% Wilson upper bound
0.01156), within its registered limit. The practical repair gate nevertheless failed: on
`F3_reversal_1200`, calibrated E-CUSUM cost 398.56 and was not better than E_swcert or E_rb within
the registered margin; on `F3_reversal_800`, its harm versus never-switch was +48.45 (95% CI
[+44.56,+52.33]), exceeding the adverse-regime limit. Full records, manifests, and decision are in
`pilots/cusum_any_false_calibration_20261107/EVALUATION_RESULTS.md`. This closes that calibration
lane; no threshold retuning or test substitution is supported by its outcomes.

The external-source audits are metadata-only: [ALFRED feasibility](ALFRED_SOURCE_FEASIBILITY_20261107.md)
and [electricity-market feasibility](ELECTRICITY_SOURCE_FEASIBILITY_20261107.md). ALFRED offers
historical vintages and issuer calendars but represents one U.S. macroeconomy. EIA-930 and ENTSO-E
are plausible distinct electricity domains, but EIA historical versions at decision time and
ENTSO-E product-level revision timestamp coverage remain unresolved. No observations or outcomes
were opened for these audits, and neither constitutes real-world validation.

**Current disposition remains `BENCHMARK_OR_CASE_STUDY_ONLY`.** The strongest current evidence does
not establish a repair that clears the frozen synthetic gate, so the required independent real-data
confirmation has not been run. The smallest next step is to stop expanding candidates and prepare
the complete honest case-study package with the negative gates intact. Any future repair claim
requires a newly justified, prospectively frozen candidate and independent evaluation protocol.

## Phase 4 — Bounded P6 restart-prior ablation (2026-11-07)

The one bounded follow-up was registered before outcomes at
`pilots/p6_beta2_bounded_development_20261107/PROTOCOL.md`: compare P6's uniform restart-start prior
with a conventional fixed Beta(2,1) weighted start prior across a late-improvement primary cell and
five delayed, reversal, ordinary-gain, and null controls. The run completed 600 paired episode
blocks (100 per regime; 4,800 policy records); the gzipped raw records, full runner manifest,
analysis script, paired results, and decision are included in that directory.

On `S_late_1500@B100`, Beta2's mean net cost was 361.797, versus 361.782 for
`gated_adaptive_range+front` and 361.817 for P6 uniform. Candidate-minus-comparator was +0.015
(paired percentile-bootstrap 95% CI [-0.318,+0.241]) against the lowest-mean applicable published
panel comparator, missing the registered five-unit saving and interval gates. It promoted in 5/100
streams at mean event 1937.6 among promotions and used 99.94 labels on average. Beta2 was also costly
on `F6_delay400_better@B100` (mean 423.254, compared with 384.230 for E_rb's front-loaded Gated
host) and `F0_better@B100` (415.743, compared with 372.940); it was favorable in the reversal cell
relative to other switching methods but remained more costly than never-switch. Candidate null
promotions were 0/100 (Wilson 95% CI [0.000%,3.699%]), a descriptive check only.

**Decision:** close this candidate lane. The weighted-start change is conventional prior selection,
does not create a distinct novelty claim, and does not clear the primary economic gate. No real
dataset was opened. The four-contribution assessment and analysis limitation are recorded in the
pilot `DECISION.md`; the overall disposition remains `BENCHMARK_OR_CASE_STUDY_ONLY`. Stop candidate
expansion and prepare the case-study manuscript package from registered results.

## Phase 5 — CI completion and repository checkpoint (2026-11-07)

The GitHub Actions run previously noted as in progress has completed successfully:
<https://github.com/nl2992/shiftlab/actions/runs/42307382928>. Locked dependency setup, Ruff lint,
Ruff format check, mypy, the full `uv run pytest -q` suite, and environment validation all passed.
The run tested commit `28e21f2cc3762d7d7e069531128e38deabc96676`. The current research branch is
`codex/scoped-method-research-results-2026-11-06`, at `f4800aac4243c16f03ebec41d440722b1fd75bfc`,
and matches its upstream branch. No merge to `main` was performed.

**Exit decision:** `NO_ECONOMIC_HEADROOM` for the tested, prespecified operating regions. The
five-cell economic screen failed its registered safety-qualified improvement gate; the calibrated
CUSUM follow-up failed its practical/adverse-regime gate; and the bounded Beta(2,1) restart-prior
ablation failed its paired improvement gate and is a conventional prior change. These are
candidate- and region-bounded findings, not evidence that no economic opportunity exists anywhere.
No distinct repair or independent real-data transfer is established. Do not enter another
candidate-development lane or open a confirmation source under the current evidence. The smallest
next action is to prepare the bounded benchmark/case-study package from the preserved reports,
including negative results, or stop if that package is not useful.

## Phase 6 — Current-checkout CI repair and replay reconciliation (2026-11-07)

The original failed Actions run is still the 506-finding failure described above; its baseline repair
is already in ancestor commit `82e1c48e`. On this checkout, the exact CI command initially reported
13 remaining findings in the then-current uncommitted EIA/restart scripts. Fixed those Ruff findings
and applied Ruff's required formatting to seven files. This includes a latent analyzer loop bug
caught by lint (`dict.items()` iteration now appends through the bound list value); the existing
analysis output was regenerated and still passes all completeness and cost checks.

Commands and results on `codex/scoped-method-research-results-2026-11-06` at starting commit
`ba7bc4e6f5365a9b72b3b7c31cd46e58d132ea8a`:

```sh
uv run ruff check .                         # pass
uv run ruff format .                        # 7 reformatted, 2121 unchanged
uv run ruff format --check .                # pass, 2128 already formatted
uv run mypy                                # pass, 2 source files
uv run pytest -q                           # 3346 passed, 46 skipped in 1730.44s
git diff --check                            # pass
```

The phase is a lint/format repair only; no test code or scientific method was changed. The full
local test command completed successfully. `RUN_STATUS.md` for the separate frozen EIA 2026 replay
records its positive temporal result and four-row progress exposure. This replay is evidence for a
known static challenger control in one provider, not evidence for the rollback/acquisition repair
question or a novel method. It does, however, make the broad phrase “no economic opportunity” too
strong: retain `BENCHMARK_OR_CASE_STUDY_ONLY` as the overall scientific disposition, and describe
the prior `NO_ECONOMIC_HEADROOM` finding as scoped to the synthetic candidate regions and safety
contract that were actually tested.

This checkpoint was committed and pushed as `a098faf3` to the existing research branch. GitHub
Actions run `42357579417` was in progress when checked; the complete local lint, formatting, typing
and test checks above passed. No merge to `main` was performed.

## Phase 7 — F8 shared-horizon validation falsification (2026-11-07)

After the novelty audit identified free validation as a fairness risk, a single in-horizon gate was
frozen in `pilots/f8_fair_gate_20261107/PROTOCOL.md` before running its 50-seed-per-cell pilot. It
queries all disagreements during events 0–399, remains on the incumbent through the 100-event label
delay, and makes a one-look Clopper-Pearson gate at event 500. The common simulator charges the
validation losses, 0.05 per requested label, switch cost 5, and enforces the same horizon 2,000 and
pathwise budget 200 for every method. The upper-control fixed challenger is explicitly identified as
unimplementable because its target model identity is supplied.

The candidate failed its frozen primary criterion in `F8_rare_better`: mean net cost 226.439 versus
211.482 for CAMS, a paired difference of +14.957 (95% paired bootstrap CI [+11.379,+18.703]); the
criterion required savings of at least 5 units. It spent 12.38 labels and switched 0.74 times on
average; CAMS spent 30.44 labels and switched once. In the null cell, the gate promoted 1/50 times,
cost 4.300 more than never-switch (CI [+3.932,+4.942]), and used 80.4 labels. In the reversal cell,
it promoted 44/50 times and cost 71.616 more than never-switch (CI [+62.860,+79.744]). The
known-in-advance fixed challenger remained 20.939 cheaper than the gate in F8, confirming that its
advantage depends on the free identity assumption.

**Decision:** retain `BENCHMARK_OR_CASE_STUDY_ONLY`; do not advance a method claim or open a new
confirmation source. This single paid validation baseline failed to reproduce the static F8
advantage against CAMS, while the adverse regimes reinforce the need to report applicability limits.
It does not prove absence of headroom outside these frozen cells. See the full breakdown, confidence
intervals, adapter fidelity notes, and reproducibility artifacts in
`pilots/f8_fair_gate_20261107/DECISION.md`. The remaining research action is to stop candidate
expansion and prepare the benchmark/case-study package if desired.
