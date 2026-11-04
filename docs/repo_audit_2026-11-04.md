# Repository audit — 2026-11-04

## Snapshot and scope

Audited `shiftlab-current-2026-11-04`, branch `research/continuation-2026-11-04`, HEAD `f303d90b`. Fetched origin and ran `git pull --ff-only`: already up to date. HEAD equals its upstream and contains origin/main with two additional commits. Before this report, status contained 76 changed/untracked entries. Existing work was preserved. Scope: current research decisions, selected uncommitted evaluation changes, and repository quality checks; not an exhaustive theorem or literature review. No scientific results were regenerated.

## Findings

1. **P1: exhausted-budget path crashes.** In `src/shiftlab/dive/budgeted_promotion.py:1399`, an eventwise scout with no remaining certification budget bypasses all assignments to `opi_result`. The return unpacks it at line 1717, raising `UnboundLocalError`. This also affects runs with OPI disabled. Initialize the result before branching and exercise exhaustion during the scout stage.

2. **P2: OPE gains do not use OPE promotion times.** In the same file, lines 1633–1661 compute gains from `stop_index` (the end of processed certification), then copy them into both OPE result families. Their reported crossing times can differ. Thus those gain fields do not represent utility beginning at the reported OPE promotion event. Compute each comparator's deployment interval from its own decision convention, or explicitly rename these as common fixed-window diagnostics and exclude them from claims about stopping-time utility.

3. **P1: aggregate test collection has a module-name collision.** `scripts/sota_sprint/bench.py:23` imports bare `regimes`; aggregate pytest resolves an already cached `scripts/failure_atlas_v2/regimes.py`, which lacks `ALL_REGIMES`. Three sprint modules fail collection. Manipulating sys.path does not override sys.modules. Use explicit package imports to keep the regime families distinct.

4. **P2: policy filtering can break the SOTA runner.** `scripts/promising_directions/sota/run_vs_sota.py` accepts arbitrary `--policies`, but later unconditionally indexes `per_ep["P7s_settled"]` (line 267). A valid requested subset omitting that policy fails after running its experiments. Validate the required policy before execution, or support reports without it.

5. **Evidence blocker: archived B3 runner attribution remains unresolved.** The current claim ledger reports a runner hash mismatch and unsuccessful recovery across local repositories. Reproduced arithmetic does not establish runner-to-row provenance. Retain descriptive status until the exact archived runner is recovered and verified. This audit inspected that disclosure; it did not independently repeat the archive-wide recovery scan.

## Verification

- `python -m pytest -q`: 15 collection errors; three are the regime collision above and the remainder report missing `river`.
- `python -m pytest -q tests/test_anytime_policy_identification.py tests/test_dive_scout_eventwise_bound.py tests/test_dive_budgeted_promotion.py`: 27 passed, 30 deprecation warnings. These passes do not cover every new OPE/OPI branch.
- `ruff check . --output-format concise`: 324 errors.
- `ruff format --check .`: 96 files require formatting; 874 already formatted.
- The checkout's `.venv` lacks pytest and ruff; checks above used the available system Python and Ruff. System Python lacks mypy and river; environment validation fails because installed shiftlab package metadata is absent. These are local checks, not a locked-environment CI reproduction.

## Research assessment

The current research-direction document explicitly records SOTA_NOT_MET and closes the current algorithm leads. It retains scoped benchmark/validity–power evidence and exact finite-instance acquisition comparisons, with provenance, real-world timing/cost, and novelty limitations. This is consistent with preserving a benchmark/validity study as the supported output, rather than promoting a novel SOTA method.

Recommended order: repair evaluation correctness and test isolation; reproduce checks in the locked development environment; checkpoint the reviewed local work with its source/data manifests; then consolidate claims using the existing evidence ledger. Do not launch another parameter sweep to compensate for these audit gaps.
