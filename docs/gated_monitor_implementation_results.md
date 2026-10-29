# WP1 S0 implementation verification

**S0: PASS, 2026-10-27.** This is code verification, not evidence of calibration or detection gains.
The [frozen protocol](gated_vs_ungated_monitor_comparison_protocol.md) fixes the estimand,
panel, endpoints, seed blocks, and pre-run predictions. No registered stage had run at S0.

The new path reuses the hard-budget generator and existing ungated runner. All selective-label
arms share events, uniforms, training/validation slices and the pathwise dollar cap. Gated arms
spend nothing on agreements and retain their known centered contribution. Past-only pacing is
seeded by validation tariffs/actions. Oracle probabilities enter evaluator summaries only.

The panel includes fixed and adaptive common engines, replay-verified Timans formulas, source
PPE/Xu fixed-factor adaptations, a conservative no-action row and an ADWIN feature diagnostic.
PPE/Xu algebraic path aliases are explicit. The feature sentinel has its own target and is excluded
from same-null harm rankings. Its delta is a registered configuration, not a claimed proof of 5%
pathwise control. New SR/CUSUM and subgroup-composition modules have separate formula audits.

## Checks and source provenance

Final verification after the historic-schema adapter correction:
`uv run --no-sync pytest -q`: **1,750 passed, 1 skipped, 665.55 seconds**.
This final run includes the added fidelity-I/O, exact-null design and allocation tests and
supersedes the intermediate mixed-collection verification described below. No research
code changed between that run's collection and this record.

- `uv run --no-sync pytest -q`: 1,711 passed, 1 skipped, 673.04 seconds. The background suite
  collected before the last censoring/ratio clarification; current focused checks below cover
  those final changes and their integration. This is not a claim that the old suite collected
  subsequently added test cases.
- `uv run --no-sync pytest tests/test_gated_monitor_comparison.py tests/test_gated_monitor_analysis.py -q`:
  55 passed, 23.92 seconds, after the final endpoint guard changes.
- Focused comparator/design checks passed, including 16 exact-null/pilot-contract tests.
- Targeted Ruff and the repository's configured mypy check passed. Git commit hooks passed.

The deterministic unit fixture verifies exact reuse of the existing U1/U2 crossing outputs,
unchanged learner outputs when oracle probabilities are perturbed, every arm's hard-cap
constraint, and horizon censoring of nondetections. Other tests enumerate conditional-mean
identities, bound extremes, agreement skips, past-only pacing, and pairwise growth prefixes.
Historic stream fidelity remains S1; this fixture alone does not establish 6/60 or 47/60.

Implementation commits: `523a49b` (matched replay/tests), `09c95b7` (stage runner), `6f52316`
(analysis/guards), `84d4cb9` (historic `ppi_increment` schema and CLI import guard).
The protocol's specification freeze is `50c4314fbca7183ef4860204925d07e2776151b4`,
with its hash-header follow-up and visible pre-stage clarification. Stage manifests record full
source/output SHA-256 values, HEAD, dirty paths, configuration, device, hardware and runtime.

**Assessment: continue to S1 on the historic checksum-verified increments.** Do not open fresh
smoke/comparison/calibration streams unless fidelity passes. No figure was generated.
