# Reproducible simulation screening plans

Preview the requested parameter ranges without generating observations:

```powershell
python -m uv run python scripts/plan_synthetic.py --config configs/data/synthetic/balanced_initial.yaml
```

The executed preview is in `data/reports/sampling_plan.json`. It selects twelve profiles,
crossed with four mechanisms and thirty paired seeds: 1,440 streams, 405 million total
observations and 418,262,400,000 uncompressed feature bytes. This last figure excludes
metadata, targets and evaluator oracles; it is not a disk-space guarantee. Generation
requires adding `--execute`. This large screening plan was previewed, not materialized.
Use the existing smoke configuration for inexpensive generation.

Each requested level appears at least once and marginal counts differ by at most one.
Independent seeded permutations prevent ordered axis coupling. The design does not
exhaust interactions, establish statistical power, or promise that every selected
combination is scientifically informative. In particular, `rho` affects dependence
mechanisms only, and one regime or zero severity suppresses shifts. For dependence
experiments select `ar1`, `arma` or `dependent_errors` in the scenario list.

The same profile and DGP seeds are used for every selected scenario and should be
reused across competing algorithms. Algorithm random seeds are a separate choice;
paired DGP seeds do not make results from different mechanisms identical. Profile IDs
hash the selected configuration. Chunk size, backend and precision remain part of the
stored dataset identity. Use `[42]` for debugging; the initial plan lists thirty seeds.
For selected final experiments, specify at least one hundred distinct seeds and reduce
profiles/scenarios to the scientific contrasts of interest. No Cartesian grid is built.

## Interactive feedback validation

`PerformativeEnvironment` models policy-induced dynamics, separately from exogenous
streams. Both next-state features and current targets depend on the mean joint action.
`specification(slope)` records causal equations and the local linear stability multiplier.
Tests independently verify the stable AR1 variance, exact joint-action effects, local
growth followed by bounded-action saturation, and global divergence with explicitly
unstable state dynamics. A local multiplier above one must not be reported as inevitable
global divergence when bounded actions and a contracting state term limit growth.

## Download resumption

Partial HTTP downloads resume only with a stored strong ETag and `If-Range`, or a
publisher SHA256 for final verification. Unvalidated partials restart. Range endpoints,
total lengths, declared byte budgets and response encoding are checked before publication.
A server returning a fresh full response replaces only the unfinished partial file.
Changed validators on a partial response fail rather than splice different versions.
Completed payloads remain immutable and their checksummed acquisition receipts include
source validators when present. Local HTTP tests exercise these failure modes.

## Gas-sensor domain evidence

```powershell
python -m uv run python scripts/group_diagnostics.py --dataset-path <gas-version-directory>
```

`data/reports/gas_sensor_groups/` contains feature summaries for every batch and all
128 features, class balances, a protocol with input version and costs, and classification
evidence. The model uses batches 1–5 for fitting, including imputation and scaling;
batches 6/7 are validation/calibration domains and 8–10 test domains. Predictions are
fixed across all domains. Training performance is explicitly apparent fit, not held-out
performance. No hyperparameters are chosen using later batches. The calibration partition
is assessed here but not used to fit prediction sets.

Multiclass Brier and log loss describe probability quality without claiming conditional
calibration. Decision costs (five for a class-6 error, one for other errors, zero correct)
are research-imposed. Accuracy includes any unseen training classes; probability and
decision-loss estimates are restricted to known classes, with excluded counts reported.
IID descriptive standard errors are not dependence-robust confidence intervals. Batch
order is known but within-batch order is not, so no timestamps or causal changepoints
are invented. Class mixture and domain selection may confound differences.
