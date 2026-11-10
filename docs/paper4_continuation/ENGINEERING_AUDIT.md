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

## A3 — harness built (lead-verified); timing campaign pending a quiet CPU

The harness lives in `src/shiftlab/paper4_continuation/{ablation,runner}.py` and
`scripts/paper4_continuation/{ablation_one,ablation_campaign,a4_feasibility}.py`. Per-child peak RSS comes from
`os.wait4`, which reports exactly that child. The smoke test `tests/paper4_continuation/test_ablation_smoke.py`
passes: R0, R1, R2 and F0 agree exactly on C6 (39589/10000). I0 returns `U0` = 6357803/1600000 (IID + repair, an
upper bound strictly above V*). F0 generates 21 cuts and I0 none, and every method's exact risk is at most 1/10.

- **R2 = R1, with justification.** FCG-fast and R0 already share the same float cost vector, the float HiGHS LP, and the
  exact belief, continuation-DP and certificate code. The only other difference is R0's null-sequence block, and
  replacing that block is FCG itself, not a numeric choice.
- **Spec error by the lead.** The A3 brief asked for I0 to equal both R0's cost and `U0`. Those cannot both hold, and
  the builder correctly asserts `I0 = U0 > V*`.

## A4 — T=10, d=1 anti-persistent cell (T10D1): exploratory feasibility (single runs, concurrent CPU load)

`results/a4_feasibility_v1.json` (fresh processes):

| | R0 reference | F0 FCG-fast |
|---|---|---|
| Exact cost | 49589/10000 | 49589/10000 (identical) |
| Exact risk | 1/10 | 1/10 |
| Learner / null sequences | 5,681 / 2,451 | 5,681 / 0 |
| Non-IID cuts / iterations | — / 1 | **33 / 34** |
| In-process seconds | 10.81 | 14.18 |
| Peak RSS (MiB) | 217 | 264 |
| Split | build 10.56 (belief 10.1), LP 0.09 | build 8.82 (belief 8.52), LP 3.15, separation 1.03, certificate 0.38 |

**Findings.** Cuts **do fire at T=10** when d=1 (33 cuts), which resolves the delay confound from the earlier
review. At d=1 the null tree is small (2,451 sequences), so FCG has little to replace, and its repeated LPs cost
more than the null block they remove. Belief computation dominates both methods (more than 90% of R0's time). V* and
`U0` both exceed C6's by exactly 1, which was passed to WP C as a hypothesis.
