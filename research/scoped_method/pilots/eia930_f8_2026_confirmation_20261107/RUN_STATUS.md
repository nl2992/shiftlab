# EIA-930 F8 2026 replay run status

**Status:** completed; temporal replay under the frozen simulated-feedback contract. This is one
provider, not independent-provider confirmation. The replay compares a preselected static challenger
control with the registered method panel. It does not test a novel rollback/acquisition mechanism.

## Execution and integrity

- Protocol: [`PROTOCOL_V2.md`](PROTOCOL_V2.md); test-opening marker was durably written before
  parsing the 2026 test rows or making predictions.
- Frozen test interval: 2026-01-01 00:00 UTC through 2026-10-19 17:00 UTC.
- Fixed registry: 11 balancing authorities; 17 complete 2,000-event episodes; 25 methods; five
  paired policy seeds; 2,125 episode/policy/seed records.
- Source receipts, frozen training models, policy registry, source/code digests and episode coverage
  are in `TEST_OPENING.json`, `run_manifest.json`, `PREFLIGHT.json`, and `MODEL_FREEZE.json`.
- The analyzer verifies the pathwise label cap, full policy/seed pairing, expected record count and
  net-cost identity. All passed; maximum cost identity residual was 0.
- The first analysis attempt stopped on a completeness-check bug in the analyzer before reporting
  metrics. The analyzer was corrected; no raw records or outcomes were changed. The corrected
  analyzer is `analyze_results.py`; reproduction command:

  ```sh
  uv run python research/scoped_method/pilots/eia930_f8_2026_confirmation_20261107/analyze_results.py
  ```

## Disclosure and result

While the runner was active, four `tail` checks exposed aggregate fixed-challenger costs for ERCO
episode 6, FMPP episode 8, FPC episode 9 and NYIS episode 14. No method, protocol, BA registry,
hyperparameter, comparator, or analysis choice was changed after these peeks. This exposure limits
the independence of the replay; it is disclosed in `ANALYSIS.json` and `RESULTS.md`.

The fixed challenger minus frozen primary comparator CAMS was **−12.239** net-cost units per
episode (hierarchical paired 95% CI **[−21.231, −7.218]**). Against the lowest-mean registered
published-panel method, `online_llm_picker`, it was **−9.191** (selection-aware hierarchical 95% CI
**[−13.958, −4.555]**). The registered five-unit advantage gate passed for both contrasts. Candidate
net cost decomposed to 47.606 predictive loss, 0 labels (label cost 0), and one switch (switch cost
5) per episode. `online_llm_picker` averaged 49.830 predictive loss, 58.4 labels (label cost 2.92),
and 1.81 switches (switch cost 9.05).

This is a favorable temporal replay for a conventional static validation-selected model choice.
It is not evidence of novelty and does not overturn the negative synthetic gates for the tested
restart/acquisition candidates. Scope is limited by one provider, a single partial year, revised
EIA values, simulated one-hour feedback maturity, hypothetical cost prices, 17 episodes across 11
BA clusters, and the disclosed four-row outcome exposure. The 11 balancing authorities are not 11
independent source providers.

## Analysis limitations

The failure of synthetic candidate gates remains the reason not to open another method search. The
static challenger result means the overall conclusion should be `BENCHMARK_OR_CASE_STUDY_ONLY`,
not a universal `NO_ECONOMIC_HEADROOM`: a meaningful comparison exists, but it is explained by an
ordinary frozen model-selection control and establishes no new method contribution.

No row-level predictions or demand outcomes are stored in Git. Raw EIA CSVs and serialized models
remain local/ignored. Source preflight v1's archive-hash mismatch and its safe stop are documented
in `SOURCE_PREFLIGHT_V1.md`; v2 used the official six-month balance CSV source.
