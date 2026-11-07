Reviewer-Model: gpt-5

Overall verdict: WARN

No direct numerical fabrication or nonexistent-result failure was found. The audit found integrity weaknesses that prevent a clean PASS.

### A. Ground Truth Provenance — PASS with caveat

Evidence:

- `scripts/sota_sprint/screen.py:101-110`
- `scripts/failure_atlas_v2_flq/suite.py:96-100`
- `scripts/promising_directions/sota/simulator.py:129-145,180-213`
- `scripts/sota_sprint/fresh_real.py:182-205`

Details:

- Synthetic regimes derive oracle gain from evaluator-side regime truth: `screen.py:101-103`.
- Real-data loss streams originate from dataset targets in `fresh_real.py`, but the policy simulator reconstructs balanced labels from cached model losses: `suite.py:96-100`.
- The real-data gain is explicitly labeled `PROXY` and `gain_is_proxy=True`: `screen.py:107-122`.
- Primary `net` is based on cached dataset-derived losses; oracle/proxy diagnostics are separate.

Classification:

- Synthetic validation/null/OOC/transfer: `simulation_only`.
- Fresh real/exposed validation: dataset-grounded loss construction, but policy replay is a `synthetic_proxy`/loss-stream evaluation rather than direct real-label online evaluation.
- No official benchmark evaluator was present in the repository.

### B. Score Normalization — PASS

Evidence:

- `scripts/sota_sprint/screen.py:53-90`
- `scripts/promising_directions/sota/simulator.py:235-243`
- `scripts/sota_sprint/analyze_validation.py:80-86`

Details:

- `net`, `loss`, labels, switches, regrets, and runtime are reported in raw units.
- No metric is divided by a model’s own prediction maximum, minimum, or mean.
- Wilson rates are computed from promotion counts and sample sizes, not prediction statistics.
- No suspicious universal 1.0/100% normalization was found.

### C. Result File Existence and Claims — WARN

Evidence:

- `docs/sota_sprint/REPORT.md:46-67`
- `docs/sota_sprint/validation/amend5_results.json:1-30,272`
- `docs/sota_sprint/validation/transfer_results.json:707-708,1372`
- `docs/sota_sprint/gate_audit.json:2-20`
- `docs/sota_sprint/leaderboard.json:36-50`
- `docs/sota_sprint/candidates.json:8`

Details:

- Reported result files exist.
- Headline values reconcile with artifacts:
  - HC is `true`: `amend5_results.json:272`.
  - HR is false with 3/5 hosts: `transfer_results.json:707-708`.
  - HD is false: `transfer_results.json:1372`.
  - Gate audit reports all 24 candidates passing: `gate_audit.json:2-20` and corresponding entries.
- Raw-record counts match the stated scope: 21 synthetic validation regimes, 7 in-class nulls, 2 OOC nulls, 5 fresh datasets, 62 fresh episodes.
- Fresh `.npz` array-content checksums all recomputed successfully.

Integrity weaknesses:

- The experiment tracker is stale for final validation: `leaderboard.json:36-50` retains `SCREENED_PROMISING` and `validation: null`; `candidates.json:8` likewise contains only development status.
- `analyze_validation.py:37-39` silently skips missing result files instead of failing closed.
- `analyze_real.py:47-48` silently constructs the “best certified” set from whatever comparator columns happen to exist.
- Manifests hash only `scripts/sota_sprint/*.py`: `screen.py:169-173`; imported dependencies and raw-data provenance are not fully hashed.
- `screen.py:126-130` checks Git dirtiness only under `scripts`, not the whole experiment configuration.

These are auditability risks, although I found no evidence that omission or mismatch was actually used to manufacture the reported numbers.

### D. Dead Code Detection — PASS

Evidence:

- `scripts/sota_sprint/screen.py:53-90,114-122`
- `scripts/sota_sprint/analyze_validation.py:42-66,80-164`
- `scripts/sota_sprint/analyze_real.py:32-60`
- `scripts/sota_sprint/analyze_transfer.py:27-79,82-113,151-185`
- `scripts/sota_sprint/leaderboard_views.py:39-87`

Details:

- The primary metric function is called by the screening pipeline.
- Analysis helpers (`wilson`, `diff`, `holm`, `contrast`, transfer CI functions) feed generated result files.
- No unused metric function with suspiciously disconnected output was found.
- Some factory/state helpers are not used in the audit path, but they are not metric functions.

### E. Scope Assessment — WARN

Evidence:

- `scripts/sota_sprint/validation_spec.py:17-39`
- `docs/sota_sprint/run_scripts/run_validation.sh:3-20`
- `data/sprint_fresh_losses/README.md:15-21,67-80`
- `docs/sota_sprint/REPORT.md:52-55,128-139`
- `docs/sota_sprint/publication_register.md:80-89`

Details:

- Final scope is substantial but narrow:
  - 21 synthetic regimes, generally 100 seeds.
  - 7 in-class null regimes and 2 out-of-class nulls, 1000 seeds.
  - 5 fresh real datasets, 62 episodes.
  - 9 exposed real datasets are descriptive only.
- The report correctly discloses optimistic episode-level CIs, exposed regimes, shared Family-C seed bases, few harmful real episodes, and lack of PaperBanana figures.
- Words such as “broadest,” “every,” and “all” are generally qualified, but the evidence remains one simulator, one contract, five fresh datasets, and loss-stream replay. Those claims should remain explicitly scoped.

### F. Evaluation Type Classification — PASS

| Evaluation | Classification | Evidence |
|---|---|---|
| Synthetic fresh-seed validation | `simulation_only` | `screen.py:98-103`; `validation_spec.py:34-39` |
| 1000-seed in-class nulls | `simulation_only` | `analyze_validation.py:80-86` |
| Out-of-class nulls | `simulation_only`, descriptive | `ooc_regimes.py:1-9,30-55`; protocol `validation_protocol.md:105-109` |
| Fresh real validation | `synthetic_proxy` over dataset-derived losses | `fresh_real.py:189-205`; `screen.py:105-122` |
| RMM transfer | `simulation_only` | `analyze_transfer.py:41-79` |
| Deploy-gate transfer | `simulation_only` plus fresh-real proxy | `analyze_transfer.py:82-113` |
| Human evaluation | Not present | No human-judge pipeline found |

Final assessment: the numerical record is internally consistent and the report is unusually candid about failed hypotheses and post-hoc Amendment 4. However, silent missing-file handling, incomplete provenance hashing, and a development-only tracker make the final evaluation insufficiently fail-closed for a clean PASS.

The required Codex-with-ChatGPT bridge could not be connected because its local bridge failed with `EPERM`; the audit was completed independently using read-only repository inspection and raw-record recomputation.