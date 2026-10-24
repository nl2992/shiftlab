# Closed-loop candidate promotion and rollback benchmark

**Status:** Development benchmark implemented and run on CUDA. This is a controlled
simulation of a two-gate intervention workflow, not a new algorithm or a real-data result.

## Question

Can a candidate that passes a frozen shadow evaluation be deployed and then withdrawn when
independent forward feedback shows material decision harm, while charging for labels and
interventions? The benchmark separates the evidence used to promote a candidate from the
evidence used to roll it back. It compares the two-gate workflow with continue, immediate
unconditional promotion, and promotion without rollback monitoring.

## Data and timing

Each stream has 800 shadow events followed by 800 deployment events. At each event, the
evaluator generates incumbent and candidate binary costs independently. The incumbent cost
is Bernoulli with probability 0.5; the candidate cost is Bernoulli with probability `0.5 -
mean_gain` for that event. Their difference `G = incumbent_cost - candidate_cost` lies in
`[-1, 1]`; positive values favor the candidate.
Scenario-specific mean gains are fixed before simulation and kept in evaluator code. The
controller receives only an inverse-propensity estimate of the paired cost difference, never
the scenario name or expected schedule.

Labels are queried with a predictable Bernoulli propensity `q=0.25`. Each observed paired
gain contributes the Horvitz-Thompson value `I * G / q`; unqueried events contribute zero to
that estimator. The run enforces hard total query caps of 20% or 40% of the 1,600 events
(320 or 640 labels). A queried label costs 0.01 utility units. Promotion and rollback each
cost 0.05 utility units.

| Scenario | Shadow mean gain | Deployment mean gain | Purpose |
| --- | ---: | ---: | --- |
| `no_benefit` | 0.00 | 0.00 | Promotion null and false-promotion calibration |
| `persistent_benefit` | 0.30 | 0.12 | Strong promotion and positive rollback-null control |
| `shadow_only_benefit` | 0.30 | 0.00 | Tests rollback after selection when the candidate has no deployment harm |
| `early_reversal` | 0.30 | +0.30 for 80 events, then -0.15 | Tests rollback after a beneficial start and later reversal |
| `late_benefit` | 0.00 | 0.30 | Tests whether shadow evidence appropriately blocks a future-only benefit |
| `weak_persistent_benefit` | 0.10 | 0.08 | Low-power promotion case |

The shadow and deployment potential-cost draws are independent in this simulator. That
independence is deliberate: it makes the rollback stream conditionally fresh after a
data-dependent promotion. The `shadow_only_benefit` scenario gives a stringent selected
candidate rollback-null check because promotion occurs on all streams, while deployment gain
is zero and independent of the shadow path.

## Decision rule and assumptions

The promotion process tests whether the candidate's expected paired gain exceeds the
promotion cost amortized over the fixed 800-event deployment horizon. The rollback process
tests whether candidate harm exceeds the rollback cost amortized over that same horizon.
Each is a fixed-stake mixture e-process with total alpha 0.05 split equally across the two
stages. The increments are centered by the corresponding per-event cost and bounded using
`1/q` plus that cost. Promotion stops the shadow process; rollback stops the deployment
process. Both use the first threshold crossing.

The stated crossing controls require the conditional-mean null, bounded paired costs, a
predictable and correctly recorded propensity, and the matching filtration. The rollback
claim additionally conditions on the selected promotion history; independent forward-time
deployment feedback is sufficient here. The simulator does not establish guarantees under
serial dependence, delayed or missing labels, misspecified propensities, adaptive candidate
search outside the frozen candidate, or real-world counterfactual cost estimation.

## Reproduction

The registered full run uses the RTX 4060 GPU for potential-cost and query-stream generation;
the sequential betting and summary calculations use NumPy/SciPy on CPU.

```powershell
.\.venv\Scripts\python.exe -m shiftlab.dive.closed_loop_intervention `
  --device cuda --seeds 2000 --horizon 800 --bootstrap-replicates 10000 `
  --output-dir outputs/closed_loop_intervention
```

Use `--device cpu` for a CPU run or reduce `--seeds` and `--horizon` for an implementation
smoke check. The output directory contains seed-level Parquet and CSV metrics, a cell summary,
paired seed-cluster bootstrap contrasts, a Bonferroni-adjusted exact binomial calibration
table, and a JSON manifest with seeds, configuration, versions, hardware, and source hashes.
The benchmark generates no figure. When figures are added, use PaperBanana as requested by
the project owner; that connector was not available in this execution environment.

## Interpretation limits

Expected utility uses the evaluator's known gain schedule and is a simulation-only estimand.
Realized utility uses generated paired costs. Utility contrasts use paired bootstrap intervals
over seeds and are descriptive; the contrast family is not multiplicity-adjusted. Error-rate
upper bounds are exact one-sided Clopper-Pearson limits with Bonferroni correction over the
registered calibration cells. Neither interval type supports a universal deployment claim.
