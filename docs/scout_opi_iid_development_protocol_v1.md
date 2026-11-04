# WITHDRAWN: invalid OPI adapter protocol v1

**Status:** invalid; results excluded from evidence. The implementation did not construct a common logged contextual-bandit reward policy class. It assigned different rewards per policy while using only one query/skip logging action. This protocol and `outputs/scout_opi_iid_development_v1/` are retained only to document the failed adapter and must not be cited as a comparator result. Use v2 for the corrected exploratory construction.

# Finite-class OPI versus contextual scout on IID contexts

**Frozen:** 2026-11-04, before execution. **Status:** exploratory development only.

## Research question

Does the context-specific scout's selected mapping retain value when compared with anytime-valid optimal-policy identification over a finite class of mappings under the same missing-label stream and hard cap? The OPI comparator follows Molitor (2026) and is applied only to IID-context profiles (`rho=0`), where the simulator's policy values are time-invariant conditional on the pre-certification history. Persistent Markov profiles are excluded because the fixed-value OPI theorem does not cover them.

## Frozen policy class and estimator

At the certification start, freeze these mappings: incumbent/no-change, pooled rank candidate applied in both context groups, validation-selected candidate by group, and scout-selected candidate by group. Deduplicate identical maps per stream. The class and each mapping are fixed before certification outcomes are observed. Each label query reveals the realized decision gain for every mapping. Encode each mapping's net gain as a bounded `[0,1]` reward with zero gain at `1/2`; logging actions are skip/query with known `h=(1-q,q)`, target always queries, and source DR truncation is `k=1`. For `m` unique mappings, compute lower and mirrored upper source LIL CSs at `alpha/(2m)` and form the OPI candidate set. Stop/deploy only when the candidate set is a unique non-incumbent mapping. This is an OPI baseline, not a novel algorithm.

## Frozen experiment

- 60 matched seed clusters `22,000,000–22,000,059`; no overlap found in current local protocols/manifests.
- 18 IID profiles: prevalence `{0.10,0.50,0.90}` × signal `{0,0.05,0.10}` × proxy error `{0,0.25}`; persistence fixed at zero.
- Cross the same uniform query label caps `{0.20,0.40}`. Use `n=3,200`, `d=16`, FN cost 5, FP cost 1, switching charge 0.05, alpha 0.05, and exact `q_min=q_t=budget_rate`.
- Pair OPI with the current eventwise fixed-mixture scout on the same context, query, queried-label, and cap-limited streams. OPI's deployment begins at its identification stopping event; use the selected mapping's evaluator-known future net utility from that event onward. Report OPI class size, singleton stopping rate/time, labels used, promotion, selected map, utility, and fixed-mixture comparison.
- The six zero-signal profile/cap cells are diagnostics only; this is not null calibration. Positive utility contrasts are descriptive seed-cluster bootstrap summaries only.
- Require 6,480 complete rows, unique keys, finite bounds/utilities, protocol hash integrity, and no hard-cap violations. No tuning or confirmation on these seeds. Any positive claim needs independent calibration, a disjoint confirmation, and real/deployment validation.

## Reproduction

```powershell
uv run python scripts/run_scout_opi_iid_development.py `
  --seeds 60 --seed-offset 22000000 --n 3200 --d 16 --device cpu --workers 6 `
  --protocol docs/scout_opi_iid_development_protocol_v1.md `
  --output outputs/scout_opi_iid_development_v1
```
