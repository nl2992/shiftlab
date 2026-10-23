# Predictable online mixture of valid promotion monitors

**Protocol lock:** 2026-10-23, before the fresh evaluation seed block. This tests a
project-derived monitor-combination baseline. It does not claim a new e-process
merging theorem or algorithmic novelty; sequential e-value merging and predictable
betting mixtures are established ideas (see [Vovk and Wang, *Merging sequential
e-values via martingales*](https://arxiv.org/abs/2007.06382)).

## Candidate algorithm

For each candidate, let `E[j,t]` be one of four nonnegative supermartingales under
the same bounded history-conditional no-harm null: fixed-stake mixture, predictable
Kelly, PM-EB, and one-sided positive betting. Before event `t`, set

`w[j,t-1] = 0.10 / 4 + 0.90 * softmax(0.5 * log(E[j,t-1]))`.

The weights are predictable, strictly positive, and sum to one. Starting at
`M_0=1`, update

`M_t = M_(t-1) * sum_j w[j,t-1] * E[j,t] / E[j,t-1]`.

Every component ratio has conditional expectation at most one because each `E[j]`
is a nonnegative supermartingale and `E[j,t-1]` is positive and measurable from
past evidence. A convex combination using past-measurable weights therefore also
has conditional expectation at most one. Thus `M_t` is a nonnegative
supermartingale starting at one, and Ville's inequality applies at threshold
`1 / alpha_i`. This combines *process increments*, not the terminal decisions of
several tests. The 10% uniform floor and softmax temperature 0.5 are fixed in this
protocol, not optimized on evaluation streams.

This result assumes all four component processes use the same globally valid
support bound, candidate policy, information filtration, and null. It does not
repair an invalid component. The familywise guarantee still comes from the frozen
Bonferroni candidate levels `alpha_i=0.05/C` and the union bound.

## Frozen comparison

- 2,000 independent streams, horizon 1,000, seed `27102026`, alpha 0.05.
- Same nondegenerate aggregate-zero, +0.12 positive, and −0.12 strict-negative
  DGPs used in the preceding locked calibration protocol.
- 1, 5, and 13 distinct frozen candidate policies; 10%, 20%, and 40% hard label
  caps; valid global support multipliers 1, 1.5, and 2.
- Compare the online predictable mixture with all six established component
  monitors. Common random numbers are shared across rules, scenarios, budgets,
  bounds, and candidate counts.
- Primary outcomes: familywise false promotion on the aggregate-zero DGP and
  familywise detection on the +0.12 alternative. Strict-negative false promotion,
  first-crossing time, and mean number of candidates crossing are secondary.
- Use pointwise Wilson intervals and paired-stream differences against fixed
  mixture. Do not choose a winner or tune the mixture from these results.

The prior 2,000-stream grid used seed `26102026`; this evaluation block is fresh.
Run on CUDA and store seed-level Parquet, cell summaries, paired differences,
figure, report, and hashes.

## Reproduction

```powershell
uv run python scripts/calibrate_repeated_candidate_nulls.py `
  --streams 2000 --horizon 1000 --seed 27102026 --device cuda `
  --output outputs/online_process_mixture_2000
```
