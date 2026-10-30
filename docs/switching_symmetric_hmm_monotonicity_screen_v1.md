# Registered screen: monotone promotion under symmetric persistent HMMs

**Registered:** 2026-10-29 before running the grid. **Question:** does symmetric positive
persistence restore a without-loss coordinatewise-monotone terminal promotion rule, despite the
already documented asymmetric counterexample?

## Frozen contract

Use the same exact terminal-testing game as
[`switching_monotone_restriction_counterexample_v1.md`](switching_monotone_restriction_counterexample_v1.md):
query labels at rounds 1–3, decide whether to promote at round 4, `T=4`, `B=3`, `d=1`,
`alpha=1/20`, query fee `1/100`, switch fee `1/10`, paired losses `(Y_t,1-Y_t)`, and the full
128 endpoint causal-null response trees. Compare the unrestricted randomized map
`q:{0,1}^3 -> [0,1]` with the coordinatewise-nondecreasing subclass under identical constraints.

The alternative HMM has prior `P(S_1=1)=1/2`, symmetric transitions
`P(S_{t+1} != S_t)=p`, and emissions `P(Y=1|S=0)=a`, `P(Y=1|S=1)=1-a`. Freeze the complete
grid `p in {1/10,1/4,2/5}` and `a in {1/20,1/10,1/4}`. Every transition is positively
persistent (`p<1/2`) and every emission is informative (`a<1/2`). No parameter additions or
grid refinement are allowed after seeing results in this screen.

## Analysis and stop rule

For each of the nine cells, enumerate the alternative tape probabilities and conditional round-4
positive-label probabilities using exact rational HMM filtering. Reuse the exact endpoint-null
risk matrix. Solve unrestricted and monotone LPs; recover rational feasible primal maps and
independently certify the monotone LP upper bound with a rational dual. Record a separation only
when the unrestricted feasible value exceeds that upper bound. If any cell has a strict certified
gap, reject the proposed symmetry-based without-loss monotonicity theorem. If no cell separates,
record only that this frozen finite grid did not refute it; do not infer a theorem. This screen
tests a structural simplification, not an algorithm, anytime guarantee, regret bound, or efficacy.

The comparison concerns accumulated labels and a fixed known HMM alternative. It does not claim
that past evidence certifies current benefit after a regime reversal.

## Results

The frozen run completed for all nine cells. Each cell's unrestricted feasible value equaled the
monotone LP's rational dual upper bound (all nine certified gaps were exactly zero). The
unrestricted/monotone common values, ordered by `p` then `a`, were:

| `p` | `a=1/20` | `a=1/10` | `a=1/4` |
|---:|---:|---:|---:|
| `1/10` | `53737/625000` | `39627/625000` | `93/5000` |
| `1/4` | `26861/800000` | `603/25000` | `33/6400` |
| `2/5` | `22871/5000000` | `1467/625000` | `0` |

This gives exact finite-LP evidence that the optimal objective value admits a monotone map on
this specific fixed-query horizon and grid. It neither proves a symmetry theorem nor transfers to
adaptive acquisition, longer horizons, hidden actions, other risk classes, or arbitrary
alternatives. In particular, the earlier asymmetric strict gap remains valid. Reproduce with
`python scripts/screen_symmetric_hmm_monotonicity.py`; machine-readable primal/dual certificates
and cell details are in `outputs/switching_symmetric_hmm_monotonicity_v1/results.json`.
