Reviewer-Model: gpt-5

Overall verdict: FAIL

A. Ground Truth Provenance — WARN

Evidence:

- `scripts/failure_atlas_v2_flq/regimes.py:3-13,53-55,57-81`
- `scripts/sota_sprint/screen.py:98-104`
- `scripts/sota_sprint/screen.py:107-108`

Details:

- The milestone records are simulation-only. Synthetic losses are generated from registered regime parameters, with evaluator-only truth (`truth_gain`); policies receive predictions and delayed labels, not the truth.
- However, the real-data branch derives `gain` from realized model losses at `screen.py:107`, then uses it for diagnostic metrics such as oracle regret and wrong-deployment fractions. This is a model-output-derived proxy and is not explicitly labeled as proxy evaluation.
- No listed milestone raw record used `kind="real"`; all 61,264 parsed rows were `synthetic`.

B. Score Normalization — PASS

Evidence:

- `scripts/sota_sprint/screen.py:53-91`
- `scripts/sota_sprint/analyze.py:53-69`
- `scripts/failure_atlas_v2_flq/suite.py:118-129`

Details:

- Primary score `net` is the raw simulator cost.
- Reported ratios are promotion/fraction metrics with legitimate denominators such as number of episodes or horizon.
- No primary score is divided by a model’s own maximum, minimum, mean, or prediction statistic.
- Raw `net` values are retained in records and result JSON.

C. Result File Existence and Claim Consistency — PASS

Evidence:

- `scripts/sota_sprint/leaderboard.py:33-50`
- `docs/sota_sprint/candidates.json:8-20`
- `docs/sota_sprint/leaderboard.json:2-28`

Details:

- All referenced result artifacts exist and all listed JSON/JSONL files parse successfully.
- I independently parsed 22 JSON artifacts and 24 raw JSONL files containing 61,264 records.
- Spot recomputations matched the narrative, including:
  - C2 on `F0_better@B100`: `+24.445`, CI `[+6.25,+42.64]`, matching `+24.4 [6.3,42.6]`.
  - D1 on `F5_dep_null_r8`: `53/300 = .1767`.
  - C2 null checks: `2/300` on `F0_null`, `18/300` on `F5_dep_null_r8`.
- The tracker uses terminal dispositions `SCREENED_PROMISING` / `SCREENED_NEGATIVE`, not literal `DONE`; nevertheless, it contains no TODO/IN_PROGRESS entries, and `leaderboard.py` treats these as executed.

D. Dead Code Detection — WARN

Evidence:

- `scripts/failure_atlas_v2_flq/suite.py:103-136`
- `scripts/sota_sprint/screen.py:53-91`

Details:

- `suite.run_metrics()` is defined but has no caller in the audited evaluation pipeline. The active runner uses `screen.metrics()` instead.
- This creates a second, potentially divergent metric implementation that is not exercised by the reported results.
- Other major metric helpers, including `hindsight_oracle_cost`, are called.

E. Scope Assessment — WARN

Evidence:

- `scripts/sota_sprint/bench.py:25-44,76-83`
- `docs/sota_sprint/benchmark_spec.md:6-15`
- `docs/sota_sprint/family_a/RESULTS.md:3-5`
- `docs/sota_sprint/family_b/README.md:3-12`
- `docs/sota_sprint/family_c/README.md:8-10`
- `docs/sota_sprint/family_d/README.md:3-10`
- `docs/sota_sprint/combos/README.md:3-15`

Details:

- Development evidence is generally 20 seeds per regime, with candidate-specific screens covering roughly 9–14 environments; combinations cover 8 regimes.
- Null checks use 300 seeds, but the milestone is entirely synthetic.
- No listed milestone result is real-data evidence.
- The documents correctly call this development screening and repeatedly state that it is not validation, so the scope language is mostly appropriately restrained. It is insufficient for broad robustness or generalization claims beyond the registered synthetic regimes.

F. Evaluation Type Classification — PASS

Evidence:

- `scripts/sota_sprint/screen.py:98-108`
- `scripts/failure_atlas_v2_flq/regimes.py:1-18,53-81`
- Raw records’ `kind` fields: independently checked across all listed JSONL files.

Classification:

- A/B/C/D/X development screens: `simulation_only`.
- Null checks and combination screens: `simulation_only`.
- `fresh_real.py`: intended `real_gt` data construction from UCI targets, but it produced no listed milestone evaluation records.
- `screen.py --kind real`: contains an unlabelled model-output-derived proxy diagnostic, as noted under A.
- No human evaluation or self-supervised evaluation was used in the milestone records.

Critical integrity failure

Evidence:

- `scripts/sota_sprint/gate_audit.py:60-75`
- `scripts/sota_sprint/gate_audit.py:79-118`
- `docs/sota_sprint/gate_audit.json:17-23`
- `docs/sota_sprint/candidates.json:12-20`

Details:

- `gate_audit.py` aggregates records globally by policy name across every family directory.
- Policy names are reused across families. The reported A1 audit row includes:
  - `outputs/sota_sprint/A/...`
  - `outputs/sota_sprint/D/screen1`
  - `outputs/sota_sprint/D/smoke_d5`
- Consequently, A1’s reported 14 environments and pass status are contaminated by D-family runs. The same flaw affects other reused names and can inflate scope, paired-seed coverage, and gate compliance.
- The gate report itself shows only 6/24 candidates passing, with 17 false; it is not a trustworthy family-isolated execution audit until records are keyed by family/run, not just policy name.

Independent verification was performed read-only. The required ChatGPT planning connection could not initialize because the managed environment denied bridge-log access with `EPERM`; no repository files were modified.