# 01 Baseline audit (existing published-baseline implementations)

Audit of code already in the repo (read-only; no existing files edited). Date: 2026-10-31, branch `main`.
Facts below come from reading the source and running the test files; "reproduced" is claimed only
where a comparison against upstream/source code was actually executed (recorded in repo artifacts,
not re-run here unless stated).

## Test run (this audit)

Command: `python -m pytest tests/test_prediction_powered_evalues.py tests/test_pprm_risk_monitor.py tests/test_pprm_block_mixture_confirmation.py tests/test_timans_unknown_shift_monitor.py tests/test_xu_active_betting.py tests/test_dive_eprocess.py tests/test_comparison_betting_engines.py tests/test_reference_implementations_manifest.py -q`
Result: **90 passed in 144.6 s**, 0 failed. (`tests/test_comparecast_*` was not located by name; see section 7.)

Fidelity classes: SOURCE_REPRODUCED (executed numerical match to official code), SOURCE_FORMULA_VERIFIED
(formula checked against paper equations by tests/derivation, no upstream-code run), TASK_ADAPTED,
SOURCE_INSPIRED, INVALID_OR_UNSUPPORTED.

Common vectorisation note: nothing here is vectorised across seeds; every class is a per-step Python
object (scalar `update`). Exceptions are noted per section.

## 1. Prediction-powered e-values (Csillag et al., ICML 2025)

- File: `src/shiftlab/dive/prediction_powered_evalues.py` (126 lines). Tests: `tests/test_prediction_powered_evalues.py` (6 tests). Consumers: `risk_proxy_monitor_grid.py`, `gated_monitor_comparison.py`, `data_efficient_source_panel.py`, `scripts/analyze_ppe_paired_cost_confirmation.py`. No dedicated paper-to-code doc found in `docs/`.
- API (all scalar, keyword-only):
  - `minimum_query_probability(*, lower, upper) -> float` = `1 - lower/upper`.
  - `prediction_powered_factor(*, proxy_factor, queried, propensity, lower, upper, observed_factor=None) -> float`.
  - `PredictionPoweredEProcess(*, lower, upper)`; `.update(*, proxy_factor, queried, propensity, observed_factor=None) -> wealth`; attrs `wealth`, `log_wealth`, `updates: list[PPEUpdate]`.
- Formula: factor `E~ = Ehat + (xi/q)(E - Ehat)` i.e. `proxy + (observed - proxy)/propensity` if queried, `proxy` otherwise; wealth = product. Base factor is supplied by the caller (the module does not build betting factors; the docstring notes `1 + lambda z/B`, floor `q >= 2*lambda/(1+lambda)`).
- Null/direction: none built in. Validity delegated to the caller: the base factor must be an e-value under the caller's null (in repo use, eventwise conditional-mean excess-cost null `E[Z|past] <= 0`, harm = positive Z).
- Calibration rule: none (no threshold; alarm done by caller at `1/alpha`).
- Query/propensity: propensity must be predictable, in `(0,1]`, `>= 1 - lower/upper` (enforced, raises). Unqueried event may not be passed an observed factor (raises). Propensity is recorded per update.
- Tests check: floor formula, unqueried=proxy / queried=corrected, exact conditional-mean preservation by enumeration, extreme-correction nonnegativity at the floor, rejection of leaked outcome, product of factors.
- Test result: 6/6 pass.
- Gaps vs published: only the missing-label transformation is implemented; the paper's other constructions (e.g. choice of proxy/predictor training, the paper's own experiments, anytime-valid combination with learned propensities) are not. No upstream-code run found. Predictability, randomised querying, and base-factor validity are unchecked assumptions.
- Proposed class: **SOURCE_FORMULA_VERIFIED** for the factor transform (formula-level; tests are self-consistency/enumeration, not an upstream numerical match). Whole pipelines using it for paired cost are TASK_ADAPTED.
- Vectorisation: scalar Python per step; trivially vectorisable (elementwise numpy) since the factor is a closed form, but the class is not.

## 2. PPRM (Zhang et al., ICML 2026) predictive-risk monitor

- File: `src/shiftlab/dive/pprm_risk_monitor.py` (320 lines); relies on `PPIBlockConfidenceSequence` in `src/shiftlab/dive/eprocess.py`. Tests: `tests/test_pprm_risk_monitor.py` (8), `tests/test_pprm_block_mixture_confirmation.py` (5). Docs: `docs/pprm_block_mixture_confirmation_protocol.md`, `docs/pprm_paired_decision_benchmark.md`; scripts `run_pprm_predictive_risk_benchmark.py`, `run_pprm_block_grid.py`, etc.; outputs `outputs/shiftguard_unified/sota_reproductions/pprm_predictive_risk_{dev,confirmation}_v1`.
- API:
  - `prediction_powered_batch_risk(true_labeled_loss, proxy_labeled_loss, proxy_unlabeled_loss, *, reliance) -> PPRMBatchEstimate(estimate, reliance, labeled_count, unlabeled_count)`; inputs 1-D arrays in [0,1].
  - `source_prediction_powered_values(true_L, proxy_L, proxy_U, *, reliance=1.0) -> ndarray` (disjoint equal-size U blocks, App. A.2).
  - `source_risk_upper_bound_betting(values, *, max_reliance, alpha_source=0.025, grid_size=1000, truncation=0.5) -> float`; `source_risk_upper_bound_cm_eb(...)` (explicit deviation: reflected CM-EB).
  - `PredictableReliance(window_rounds=60, max_reliance, initial_reliance, ...)`: `.choose(labeled_count, unlabeled_count) -> eta`, `.update(true_L, proxy_L, proxy_U)`.
  - `PPRMRiskMonitor(*, source_upper_bound, tolerance, max_reliance, alpha_test=0.025, lambda_count=128, root_iterations=48)`: `.update(PPRMBatchEstimate) -> alarm bool`, `.lower_bound`, `.alarm`.
- Formula: batch estimate `eta*mean(proxy_U) + mean(true_L - eta*proxy_L)`; eta from sliding-window `cov(true,proxy_L) / ((1+n/N) var(proxy_U))` clipped to [0, eta_max] (Eq. 27); test side: one-sided finite-mixture CM-EB lower confidence sequence of running mean of normalised block estimates; alarm when lower bound crosses `source_upper_bound + tolerance`.
- Null/direction: running test risk <= source risk upper bound + tolerance; alarm on risk increase (one-sided). Predictive risk of one model, NOT paired decision cost.
- Calibration: alpha split `alpha_source=alpha_test=0.025`; source bound from betting UCB (ConfSeq-style, grid of 1000 candidates); test bound via CM-EB mixture over `lambda_count` geometric lambdas in [1e-4, .99] with bisection for the radius.
- Query/propensity: none; PPRM uses fixed labeled/unlabeled split per round (callers must ensure disjoint, same-distribution). No inverse-propensity handling.
- Tests check: estimator definition/support/validation; source pairing preserves mean; eta predictable and capped; source UCBs cover the empirical mean; **betting source bound matches pinned ConfSeq reference** (`test_source_betting_bound_matches_pinned_confseq_reference`); monitor threshold/sequence; block-mixture confirmation helpers (paired summary, Holm, vectorised recursion equals scalar production process).
- Test result: 13/13 pass.
- Gaps: test side uses the repo's finite-mixture CM-EB (docstring: "published CM-EB construction using a finite discrete mixing distribution"), so the exact mixing law differs from the paper's continuous mixture; no run against the authors' official PPRM code was found; the cm_eb source bound is a deviation (the betting one follows ConfSeq). Paired-cost "PPRM" uses in repo (`PPIBlockConfidenceSequence`, block-mixture) are adaptations that explicitly "do not include the source-risk upper bound" and test only a running-mean null.
- Proposed class: **SOURCE_FORMULA_VERIFIED** for predictive-risk PPRM (source betting UCB matched to a pinned reference; test CS finite-mixture, not matched to official PPRM code). Paired-cost block-mixture: **TASK_ADAPTED**.
- Vectorisation: scalar per-round Python; `_radius` is a bisection with a doubling loop per update (costly). A vectorised block-mixture recursion exists for the registered mixture (tested to equal the scalar process, `tests/test_pprm_block_mixture_confirmation.py`), but the CM-EB `PPIBlockConfidenceSequence` itself is per-step. Source UCB loops over 1000 candidates in Python.

## 3. Timans et al. (UAI 2025) risk monitor: approx-GRAPA and grid GRAPA

- Files: `scripts/reproduce_timans_risk_monitor_paired_cost.py` (core `_timans_logs`, `verify_upstream_replay`, run/report), `scripts/verify_timans_risk_monitor_paired_cost.py`; protocol `papers/shiftguard_unified/timans_unknown_shift_paired_cost_protocol_v1.md`; outputs `outputs/shiftguard_unified/sota_reproductions/timans_unknown_shift_paired_cost_v1/` (report, manifest; upstream commit `4bf66a37dc2a3d7959bb9dcb325b61e8bb3c28e5`). Engine wrapper `src/shiftlab/dive/comparison_betting_engines.py` (`timans_approx_grapa`, `timans_grapa`). Tests: `tests/test_timans_unknown_shift_monitor.py` (7 parametrised cases), `tests/test_comparison_betting_engines.py` (incl. `test_timans_engines_match_existing_verified_replay` and prefix-causality). The core lives in `scripts/` and is imported from `src` (`from scripts.reproduce_... import _timans_logs`), a fragile dependency.
- API: `_timans_logs(score, *, rule in {"approx_grapa","grapa"}, epsilon=0.5, alpha=0.05, burn_in=100) -> ndarray` of per-step log wealth (zero during burn-in); `score` 1-D in [0,1]. `replay_engine(values, bounds, engine, alpha=0.05) -> log-wealth ndarray` maps paired excess cost Z to `score = 0.5 + 0.5*Z/B` with epsilon 0.5.
- Formula: factor `1 + lambda_t (x_t - eps)`. approx-GRAPA: `lambda_t = clip((mu - eps)/(var + (mu - eps)^2) + 1e-10, 0, 0.5/eps)` from running mean and sample variance of past scores (1e-10 jitters as in code). Grid GRAPA: argmax over `lambda in {0.1,...,1.9}` of cumulative past log growth. Bet is 0 for the first 100 events.
- Null/direction: `E[x_t | past] <= eps`; via the affine map this is the eventwise conditional-mean excess-cost null. Alarm when log wealth >= `log(1/alpha)`; upward (harm).
- Calibration: none beyond Ville; no tuning. Upstream tracker window/stop counters are set to 0 and BATCH_TIMESTEP=1 in the replay, so only the scalar wealth rule is covered.
- Query/propensity: none. Needs a fully observed score every step (no missing-label or IPW handling).
- Tests check: wealth is 0 when score==eps; prefix independent of future scores; invalid inputs rejected; engine replay equals `_timans_logs` on the transformed score.
- Test results: pass (part of the 90).
- Upstream match: `verify_upstream_replay` compares local formulas to the official PyTorch `EProcessTracker` on a deterministic 137-point stream (needs pinned checkout + torch; NOT re-run in this audit). The recorded `report.md` states max abs log-wealth error 0.0 (approx-GRAPA) and 1.86e-7 (grid GRAPA), tolerance 2e-5.
- Gaps: scalar rule only (no tracker windows, no minibatch means, float32 upstream vs float64 local); paper tests unknown-shift model risk, not paired cost; fixed 100-event burn-in.
- Proposed class: **SOURCE_REPRODUCED** for the scalar approx-GRAPA/GRAPA rules (numerical match to pinned official code executed and recorded earlier; not re-run here). Paired-cost deployment: **TASK_ADAPTED**.
- Vectorisation: per-step Python loop (grid GRAPA does a 19-wide numpy op per step). Vectorising across seeds needs a rewrite as a (seeds x 19) recursion.

## 4. Xu et al. (NeurIPS 2024) active anytime-valid risk control

- File: `src/shiftlab/dive/xu_active_betting.py` (167 lines); doc `docs/xu_active_betting_paper_to_code_audit.md`; query policy reuses `shiftlab.dive.query.AdaptiveQueryPolicy`. Tests: `tests/test_xu_active_betting.py` (10).
- API:
  - `xu_minimum_query_probability(*, stake)` = `stake/(1+0.5 stake)`; `xu_maximum_stake(*, minimum_propensity)` = `1/(1/q_min - 0.5)`.
  - `xu_paired_betting_factor(*, proxy_excess_cost, queried, propensity, stake, bound, observed_excess_cost=None) -> float`.
  - `XuActivePairedEProcess(*, bound, stake, minimum_propensity)`; `.update(*, proxy_excess_cost, queried, propensity, observed_excess_cost=None) -> wealth`; `.log_wealth`, `.wealth`.
  - `xu_variance_query_policy(*, target_rate, minimum_propensity, maximum_propensity, stake) -> AdaptiveQueryPolicy("variance", variance_power=0.5)`.
- Formula: source factor `1 + lambda(theta - rhat - (L/q)(R - rhat))` with `theta=1/2`, `R = 1/2 - Z/(2B)`, `rhat = 1/2 - h/(2B)`, i.e. `1 + lambda * [zhat + (xi/q)(z - zhat)]`, `z = Z/(2B)`. Product accumulated in log space.
- Null/direction: `E[Z|past] <= 0` (Xu's `E[R] >= 1/2`); grows under positive harm. Threshold 1/alpha left to the caller.
- Calibration: none; one fixed stake (no mixture); stake capped by the propensity floor.
- Query/propensity: Horvitz-Thompson correction with predictable propensity; floor enforced; skipped label cannot be passed. Query rule `q* ~ sqrt(E[(R-rhat)^2|X])` is approximated by a finite-slice multiplier fit, not the paper's population budget solution.
- Tests check: source equation after affine map; query/no-query average equals full-feedback factor; q=1 reduction; floor/cap inverse; positivity at floor; zero factor at the endpoint; log-product; no leaked label; query-policy wrapper.
- Test results: 10/10 pass.
- Gaps: the paper is about risk-controlling prediction sets (lambda-threshold selection); only the scalar betting factor is transferred. No upstream-code comparison. Docstring says "formula-level".
- Proposed class: **SOURCE_FORMULA_VERIFIED** for the factor; paired-cost use **TASK_ADAPTED**.
- Vectorisation: scalar per-step Python; factor is closed form and trivially vectorisable, the class is not.

## 5. Direct bounded-mean e-process (`eprocess.py`)

- File: `src/shiftlab/dive/eprocess.py` (956 lines). Tests: `tests/test_dive_eprocess.py` (27 tests). Related doc: `docs/horizon_edetectors_paper_to_code_audit.md`.
- Key classes (scalar `.update(value) -> log_e_value`; attrs `log_e_value`, `alarm`):
  - `BoundedMeanEProcess(*, bound, alpha=0.05, stakes=(0.05,0.1,0.2,0.4,0.8), weights=None)`: fixed-stake mixture.
  - `PredictableBoundMeanEProcess(alpha, stakes, weights)`; `.update(value, *, bound)`.
  - `PredictableVarianceAdaptiveEProcess(bound, alpha, ...)`, `PredictablePlugInEmpiricalBernsteinEProcess(bound, alpha)`, `PredictableHedgedPositiveEProcess`.
  - `StartedMixtureEProcess`, `VectorizedStartedMixtureEProcess` (vectorised over start times), `MultiTimescaleStartedKellyEProcess`, `HorizonHedgedStartedMixtureEProcess`.
  - `PPIBlockConfidenceSequence(max_reliance, threshold, alpha, lambda_count, root_iterations)`, `PPIBlockMixtureEProcess`.
  - `bounded_betting_factors(values, bounds, stakes) -> (T, K) ndarray`.
- Formula: component `prod(1 + s X_t / B)`; mixture log-wealth `logsumexp(log w_k + sum log(1 + s_k X/B))`; alarm at `log(1/alpha)`.
- Null/direction: `E[X_t | history] <= 0`, `|X_t| <= B`; upward alarm (harm). Event-specific bounds are valid only if predictable w.r.t. the null's filtration (docstring; `test_current_context_eventwise_bound_can_break_a_marginal_null`).
- Calibration: stake grid with equal weights is a repo default, not a published rule; Ville gives validity; empirical null crossing checked by Monte Carlo tests.
- Query/propensity: none inside; consumed by IPW/PPI callers (tests `..._direct_ipw_bound_has_valid_exact_factors`, `..._fixed_worst_case_bound_remains_safe_with_feature_adaptive_query_rates`).
- Tests check: stays 1 at zero; bound violation rejected; mixture arithmetic; predictability; small-null enumeration; independent Monte Carlo null crossing; vectorised == scalar; CM-EB formula for block CS.
- Test results: all pass.
- Gaps: generic betting e-process (Waudby-Smith/Ramdas style), not a reproduction of one paper; no upstream run for PM-EB.
- Proposed class: `BoundedMeanEProcess`, started/horizon mixtures: **SOURCE_INSPIRED**; `PredictablePlugInEmpiricalBernsteinEProcess`: **SOURCE_FORMULA_VERIFIED** (test against the published increment); `PPIBlockConfidenceSequence`: **TASK_ADAPTED** (PPRM CM-EB with finite mixture).
- Vectorisation: per-step Python with small numpy arrays over stakes; only `VectorizedStartedMixtureEProcess` and an endpoint-calibration helper are vectorised; no across-seed class. `replay_mixture_log_e` in `predictable_bound_replay.py` (not audited) is the batch replay path used by `comparison_betting_engines`.

## 6. Comparison betting engines (`comparison_betting_engines.py`)

- File: `src/shiftlab/dive/comparison_betting_engines.py` (102 lines). Test: `tests/test_comparison_betting_engines.py` (passes).
- API: `replay_engine(values, bounds, engine, alpha=0.05) -> per-event log wealth ndarray`; engines `fixed08`, `fixed1`, `plugin`, `pm_eb`, `timans_approx_grapa`, `timans_grapa`.
- Formula: normalised score `values/bounds`; mixtures/plug-in as in section 5; Timans engines as section 3 with score `0.5 + 0.5 v/B`.
- Null: conditional mean `E[Z|past] <= 0` with predictable bound (numerical support check only).
- Tests check: fixed08/fixed1 equal existing replay; scalar vs vector bounds; plugin/pm_eb use unit-normalised scores; Timans equal verified replay; prefix causality; invalid input rejection.
- Class: **TASK_ADAPTED** (common replay harness; per-engine fidelity as above). Vectorisation: per-step Python (plugin, pm_eb, Timans); the mixtures use `replay_mixture_log_e`.

## 7. Comparecast gamma-exponential mixture (Choe and Ramdas)

- File: `src/shiftlab/dive/comparecast_gamma_mixture.py` (62 lines), `gamma_exponential_log_mixture_paper(sums, intrinsic_times, rho, c) -> ndarray` (vectorised numpy/scipy `gammainc`/`loggamma`). Audit script `scripts/audit_comparecast_formula.py`; test `tests/test_comparecast_formula_audit.py` (3 tests, pass); outputs `comparecast_formula_audit_v1/v2`, `comparecast_paired_cost_*`.
- Formula: Appendix C Eq. (49) mixture; conservative bound when `z <= 0` (documented upper bound, test `test_negative_z_branch_is_the_documented_upper_bound`).
- Tests check: value 1 at zero sum/intrinsic time; positive-z branch equals independent numerical integral; negative-z branch is a bound, not equality.
- Gaps: formula-level only; z<=0 branch is not exact; no official-code run found; it is the mixture, not the full comparison test of the paper.
- Class: **SOURCE_FORMULA_VERIFIED** (independent integral for z>0), with the z<=0 branch conservative. Vectorisation: already vectorised over arrays of (sum, intrinsic time).

## 8. Items searched but not found / other change-detection code

- **Tenzer et al. "Betting on Predictions"**: no match in `src/`, `scripts/`, `tests/` (case-insensitive grep for "Tenzer", "Betting on Predictions"). **Not implemented** -> INVALID_OR_UNSUPPORTED as a baseline until implemented.
- **Ryu-Wornell multivariate gambling confidence sequences**: no match ("Ryu", "Wornell"). **Not implemented.**
- **Online Newton Step (ONS) bettor**: no ONS betting implementation found (`\bONS\b`/"Online Newton" hits only in unrelated text). **Not implemented.**
- **CUSUM**: (a) `shiftlab.monitoring.one_sided_cusum(values, *, baseline_mean, baseline_scale, slack) -> ndarray` (standardised Page CUSUM, `max(0, S + (x-mu)/sigma - k)`, thresholds need separate null calibration; per-step Python loop; used in `decision_harm_experiment.py`; heuristic, not an e-process) -> SOURCE_INSPIRED, no validity guarantee; (b) `src/shiftlab/dive/horizon_edetectors.py` `HorizonCalibratedEDetector` (Shin-Ramdas-Rinaldo SR/CUSUM e-detector recursion `f_t*max(1, C_{t-1})`; doc `docs/horizon_edetectors_paper_to_code_audit.md`; per-step Python with `update(value=None, *, skip=False)`) -> SOURCE_FORMULA_VERIFIED/TASK_ADAPTED; `atlas_components.py` uses it ("horizon_cusum") and a Page-CUSUM rollback. `tests/test_horizon_edetectors.py` and `tests/test_monitoring.py`: 20 passed.
- **Page-Hinkley**: no dedicated implementation found; only the CUSUM above.
- Other relevant docs: `docs/chugg_group_betting_paper_to_code_audit.md`, `papers/shiftguard_unified/reference_implementations_v1.json` (hash-pinned manifest verified by `scripts/verify_reference_implementations.py`; `tests/test_reference_implementations_manifest.py` 4 pass). There is no consolidated `*paper_to_code_audit*` for PPE, PPRM or Timans, and no standalone Timans module in `src/`.

## Summary table

| Method | Class | Vectorised over seeds? |
|---|---|---|
| PPE (Csillag) | SOURCE_FORMULA_VERIFIED | No (scalar; closed form) |
| PPRM predictive risk | SOURCE_FORMULA_VERIFIED (test CS finite-mixture) | No (bisection per update) |
| PPRM paired-cost block mixture | TASK_ADAPTED | Partly (registered recursion) |
| Timans approx-GRAPA / GRAPA | SOURCE_REPRODUCED (scalar rule; recorded) | No (per-step loop) |
| Xu active betting | SOURCE_FORMULA_VERIFIED / TASK_ADAPTED | No |
| BoundedMeanEProcess etc. | SOURCE_INSPIRED | No |
| Comparecast mixture | SOURCE_FORMULA_VERIFIED | Yes (array) |
| Horizon SR/CUSUM e-detector | SOURCE_FORMULA_VERIFIED/TASK_ADAPTED | No |
| one_sided_cusum | SOURCE_INSPIRED | No |
| Tenzer, Ryu-Wornell, ONS, Page-Hinkley | INVALID_OR_UNSUPPORTED (absent) | n/a |
