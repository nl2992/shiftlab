# Engineering audit (WP A)

## A1 — Reproduction: COMPLETE

At `affd5077`, all 25 Paper 4 tests pass. The FCG certificates for C1–C6 (`U`, `L`, exact robust risk, row count)
regenerate **identically** (exact strings) to `docs/paper4/experiments/results/fcg_dev_v1.json`. Gaps are at most
8.2e-15. Command: the lead's scratch check `a1_recheck.py`, which calls `paper4.frontier_cuts.frontier_cut_generation`
on each saved configuration and compares strings. The saved file was not overwritten.

## A2 — Stochastic root mixture: COMPLETE (fix + regression; lead-verified)

- **New shared helper** `src/shiftlab/dive/root_mixture.py::mix_root_lottery`. It implements the Kuhn root lottery
  for arbitrary behavioural policies:
  `mix(I,a) = [q ρ_π(I) π(I,a) + (1-q) ρ_safe(I) safe(I,a)] / [q ρ_π(I) + (1-q) ρ_safe(I)]`, where `ρ` is the
  plan's own realization probability. It uses exact Fractions. Choices always come from `game.choices`, so the budget
  is preserved. It falls back to the raw policy at information sets neither plan reaches.
- **Guard** in `eprocess_gated_planner.mix_with_never_promote`. It raises `ValueError` when `0 < activation < 1` and
  the policy is stochastic at a reachable *pre-promotion* information set. Post-promotion sets are reached only by
  the raw branch, so the old weighting is exact there. The deterministic path is unchanged. A private
  `_allow_stochastic` flag exists only to reproduce the defect in the regression test.
- **Regression** (`tests/test_root_mixture.py`, 9 tests). On C2's FCG iteration-6 policy (robust risk 13/100,
  `q = 10/13`), the old helper yields exact risk **280952/2779205 > 1/10**. `mix_root_lottery` yields exactly
  `q · 13/100 = 1/10`, and its cost equals `q C(raw) + (1-q) C(never)` from separate evaluations. The helper agrees
  with `paper4.frontier_cuts.mix_root_never_promote` on C2 and C3. The defect also appears on C3 (iterations 7, 11)
  and C6 (iterations 13, 17). Some of those cases are below alpha: they are the wrong lottery, not safety violations.
- **Caller audit.** Seven callers pass one-hot (deterministic) policies and run unchanged. Three LP-based scripts
  (`iid_relaxation_certified_pipeline.py`, `iid_relaxation_t8_grid.py`, `iid_relaxation_t10_stress.py`) can pass
  stochastic policies and would now raise whenever raw robust risk exceeds alpha.
- **Historical results are unaffected.** The lead checked every saved activation in their result JSONs
  (`iid_relaxation_certified_pipeline_v1.json`, `iid_relaxation_t8_grid_v1.json` ×5, `iid_relaxation_t10_stress_v1.json`):
  all equal **1**, so the old helper never mixed. No historical artifact was modified.
- **Tests:** `pytest tests/test_root_mixture.py tests/paper4 tests/test_eprocess_gated_planner.py` passes (37).

## A3 / A4 / A5 — pending (harness under construction; campaign run by the lead on a quiet CPU)
