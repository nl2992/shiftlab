Reviewer-Model: GPT-5

Overall verdict: FAIL

A. Ground Truth Provenance — PASS

Evidence:

- `scripts/promising_directions/sota/simulator.py:129-145` keeps labels evaluator-side and only exposes purchased feedback.
- `scripts/sota_sprint/screen.py:101-110` generates synthetic evaluator-side losses from registered regimes.
- `scripts/sota_sprint/screen.py:105-110` explicitly labels real-data `gain` as `PROXY`; primary `net` remains based on observed cached losses.
- `scripts/sota_sprint/fresh_real.py:182-205` builds frozen model losses from dataset labels.
- `scripts/sota_sprint/ooc_regimes.py:30-50` generates evaluator-side out-of-class nulls.

Details: No evidence that ground truth is derived from model predictions without disclosure. Real-data oracle diagnostics are explicitly proxy-labeled. No applicable official benchmark evaluator exists for this custom simulator; the common simulator is registered in `docs/sota_sprint/benchmark_spec.md:6-7`.

B. Score Normalization — PASS

Evidence:

- Raw cost is computed as `loss + label_price * labels + switch_cost * switches` in `scripts/promising_directions/sota/simulator.py:235-243`.
- Raw `net` is reported directly in `scripts/sota_sprint/screen.py:76-90`.
- Comparisons use paired raw-cost differences in `scripts/sota_sprint/analyze_validation.py:49-56` and `scripts/sota_sprint/analyze_real.py:32-39`.

Details: No metric is normalized by a model’s own max/min/mean prediction statistic. Wilson bounds and confidence intervals use sample counts, not prediction-derived denominators. Some promotion rates are exactly 1.0 on real data, but these are raw behavioral rates, not normalized scores.

C. Result File Existence and Claim Matching — FAIL

Evidence:

- Listed validation claims generally match the committed result files: `docs/sota_sprint/REPORT.md:41-61`.
- Gate audit reports 24/24 PASS, and `docs/sota_sprint/gate_audit.json` contains 24 passing entries.
- Raw validation manifests record the registered seed counts, e.g. `outputs/sota_sprint/validation/synth/manifest.json:2-19` and `outputs/sota_sprint/validation/null1000/manifest.json:2-19`.
- However, `docs/sota_sprint/validation_protocol.md:203-223` contains an additional Amendment 5 test with new seed bases `2026110611` and `2026110612`.
- Its expected raw outputs are incomplete: `outputs/sota_sprint/amend5/synth/records.jsonl` has only 575 lines, with no manifest, and `outputs/sota_sprint/amend5/null1000/` is absent.
- No Amendment 5 result JSON/Markdown appears under `docs/sota_sprint/validation/`.
- The final report still says there were four amendments: `docs/sota_sprint/REPORT.md:7`, while the protocol contains Amendment 5.

Details: The final report is not synchronized with the protocol and raw experiment state. Amendment 5 is a registered final-validation claim with no complete result artifact or report disposition. This is a result-file/protocol-integrity failure, even though the earlier reported numbers appear consistent.

D. Dead Code Detection — WARN

Evidence:

- Main metric functions are used: `screen.metrics` (`scripts/sota_sprint/screen.py:53`, called at `:118`), `analyze_validation.diff/wilson/holm` (`:49`, `:42`, `:59`), and transfer/real analysis helpers.
- `validation_spec.py:17-20` defines `VAL_SEEDS` and `NULL_SEEDS`, but the runner scripts use literal seed counts instead, e.g. `docs/sota_sprint/run_scripts/run_validation.sh:8-20`.

Details: No material unused metric function was found. There are unused configuration constants and duplicated protocol literals, which create drift risk.

E. Scope Assessment — WARN

Evidence:

- Synthetic validation: 21 regimes × 100 seeds, documented in `docs/sota_sprint/REPORT.md:47-50`.
- In-class nulls: 7 regimes × 1000 seeds; out-of-class nulls: 2 × 1000.
- Fresh real data: 5 datasets, 62 episodes, with 20 policy seeds per episode, `docs/sota_sprint/fresh_real_protocol.md:81-95`.
- The report acknowledges optimistic intervals and only 6/62 harmful-switch episodes in `docs/sota_sprint/REPORT.md:117-125`.
- Real episodes are consecutive windows, not independent datasets.

Details: The scope supports a substantial synthetic stress test and descriptive real-data validation. It does not support broad generalization from real data or unconditional robustness claims. The report is mostly candid, but “transfer” and “robustness” language should remain explicitly conditional and synthetic/class-scoped.

F. Evaluation-Type Classification

- Synthetic validation, nulls, OOC nulls: `simulation_only`.
- Fresh real-data losses: `real_gt`; dataset labels provide ground truth, while frozen model predictions produce the scored loss pairs.
- Real-data `gain`, `frac_on_wrong`, and related oracle diagnostics: `synthetic_proxy` / evaluator-side proxy, explicitly labeled in `screen.py:107-110`.
- Real persistence summaries: `self_supervised_proxy` or descriptive diagnostic; no causal change labels.
- Gate audit and leaderboard views: secondary aggregation of the underlying evaluation type.
- Human evaluation: none.

Primary integrity finding: the completed Amendment 1–4 results are largely traceable and honestly caveated, but Amendment 5 introduces an undisclosed/incomplete final-validation branch. Until that test is either completed and reported or formally withdrawn with an audit trail, the sprint cannot pass experiment-integrity review.