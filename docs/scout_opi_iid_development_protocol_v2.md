# Source-matched finite-class OPI versus contextual scout on IID contexts v2

**Frozen:** 2026-11-04 before execution. **Status:** exploratory development only. The prior v1 adapter was invalid because it assigned different rewards to each policy while using a single query/skip logger action. Its output is retained as an invalid adapter smoke result and is excluded from evidence.

## Research question and target

Compare the contextual scout with Molitor's anytime-valid optimal policy identification on IID-context profiles (`rho=0`). Each event has an action set consisting of the incumbent plus the distinct candidate classifiers used by the finite policy class. The finite policies map context groups to one of these classifier actions: incumbent/no-change, pooled rank, validation-selected context mapping, and scout-selected context mapping; duplicate mappings are removed before certification.

The behavior logger samples one classifier action uniformly, independently of the label-query coin. The bounded observed reward is zero when no query is made; on a queried event it is the nonnegative normalized net gain `U_t(a)=clip((Z_t(a) - switching_cost/deployment_horizon)/M,0,1)`, with `M=max(FN,FP)+switching_cost/deployment_horizon`. Thus `R_t=Q_t U_t(A_t)` is in `[0,1]` and is observed even on skipped events (then it is known to be zero). Query rates are fixed by the recorded stream within each run; OPI maximizes query-weighted net gain and ranks these fixed policies. Reward predictions are pre-certification, group-specific validation estimates multiplied by the certification query rate. The action propensities are known and uniform over the action set. The action-arm randomization is generated independently of query and outcome streams with the frozen seed offset below.

Apply source DR-LIL policy-value CSs at alpha `0.05/(2m)` for `m` unique mappings, then Molitor's simultaneous candidate-set rule. Deploy only when a unique non-incumbent policy is identified. The target class and reward predictors are fixed before certification outcomes. The policy-value theorem is applied only to IID-context profiles, conditional on the pre-certification history.

## Frozen experiment

- 60 matched seed clusters `22,100,000–22,100,059`, disjoint from prior screens.
- 18 IID profiles: prevalence `{0.10,0.50,0.90}` × signal `{0,0.05,0.10}` × proxy error `{0,0.25}`; persistence zero.
- Two hard label budgets `{0.20,0.40}`; `n=3,200`, `d=16`, FN cost 5, FP cost 1, switching charge 0.05, alpha 0.05, uniform query rule, and exact propensity floor.
- OPI policy-arm assignment uniform over distinct classifier actions, using a separate RNG stream `seed + 31,009,417 + query_index`. The same action-arm uniforms are shared across the two budget rates; query uniforms remain the existing registered stream.
- Compare OPI with the existing fixed-mixture scout on the same context and query streams. OPI utility begins after its unique-identification event. Record class size, arm count, stopping time, labels, promotion, selected mapping, future utility, and fixed-mixture outcomes.
- Six zero-signal profile/budget cells are diagnostics only, not null calibration. Positive utility intervals are descriptive seed-cluster bootstrap summaries. Require 6,480 rows, protocol hash integrity, complete unique keys, and no hard-cap violations.
- No tuning or confirmation on these seeds. Any positive claim requires independent null calibration, disjoint confirmation, and real/deployment validation.

## Reproduction

```powershell
uv run python scripts/run_scout_opi_iid_development.py `
  --seeds 60 --seed-offset 22100000 --n 3200 --d 16 --device cpu --workers 6 `
  --protocol docs/scout_opi_iid_development_protocol_v2.md `
  --output outputs/scout_opi_iid_development_v2
```
