# Intervention sensitivity grid protocol

**Status:** Frozen exploratory development design. All grid seeds are disjoint from the
closed-loop benchmark and are reserved for development; no cell in this grid is confirmatory.

## Question and primary endpoint

Determine when cost-aware rollback improves net decision utility over promotion-only across
reversal timing and severity, and how that trade-off changes with query propensity, the hard
label cap, label price, and promotion/rollback costs. The primary development score is the
equally weighted mean expected net utility of `promotion_rollback` over six reversal profiles.
The secondary score is its paired mean difference from `promotion_only`. Continue and
unconditional promotion remain reference policies. Configuration ranking is exploratory;
the best setting must be frozen and evaluated on fresh seeds before any efficacy claim.

## Frozen grid

| Dimension | Values |
| --- | --- |
| Events per shadow/deployment phase | 800 / 800 |
| Bernoulli query propensity | 0.25, 0.50, 0.80 |
| Hard label cap as fraction of 1,600 total events | 0.20, 0.40 |
| Label price per query | 0.00, 0.01 |
| Promotion / rollback cost pairs | (0.05, 0.05), (0.25, 0.05), (0.05, 0.25) |
| Reversal onset as deployment fraction | 0.10, 0.50, 0.80 |
| Harmful candidate mean gain after reversal | -0.10, -0.20 |
| Development streams per cell | 60 |

The full factorial contains 216 reversal cells (36 resource/cost designs Ã— six reversal
profiles). Four controlsâ€”zero benefit in both phases, persistent benefit, shadow-only benefit,
and future-only benefitâ€”run at the reference setting `q=0.25`, 20% cap, label price 0.01, and
costs (0.05, 0.05). Total: 220 development cells. All four policies receive common paired
potential costs and common query uniforms within each cell. GPU generates costs and query
uniforms; monitoring updates and statistical summaries run on CPU.

## Controls and evaluator truth

Each event's incumbent cost is Bernoulli(0.5). Candidate cost is Bernoulli(0.5 minus the
scenario's evaluator-only mean gain). Positive gain favors the candidate. Reversal schedules
have mean gain +0.30 throughout shadow evaluation, +0.30 until the registered deployment onset,
and then -0.10 or -0.20 through the deployment horizon. Evaluator schedules are never passed to
the promotion or rollback gates. The feedback estimator is `I * G / q`, where `I` is the
query indicator and `G` is paired incumbent-minus-candidate cost.

The same two fixed-stake e-processes and 0.025-per-stage alpha allocations are used throughout.
Bounds include `1/q` and the per-event amortized stage cost; query propensity is fixed and
known before each event. The total realized label count may not exceed the specified hard cap.
All metrics include expected and realized net utility, promotions, rollbacks, label counts,
event durations, and paired differences. Seed-cluster bootstrap intervals with 2,000
replicates are descriptive and are not corrected over the development grid.

## Selection and confirmation boundary

Use the macro ranking to identify a candidate design, not to claim a winner. The ranking uses
all six reversal profiles with equal weight and includes every development stream. After
selection, freeze the design and run an independent confirmation with fresh seeds. That run
must include separately reported phase-specific null controls: zero shadow gain (including a
future-only deployment benefit) for promotion, and zero deployment gain after selected strong
shadow benefit for rollback. Report exact familywise upper limits, a paired utility interval,
hard-cap compliance, and power/delay across reversal profiles. If the selected design fails
the predeclared null gate or does not improve expected net utility over promotion-only, report
the negative result and do not retune on the confirmation block.

## Reproduction

```powershell
.\.venv\Scripts\python.exe -m shiftlab.dive.intervention_sensitivity `
  --device cuda --seeds 60 --horizon 800 --bootstrap-replicates 2000 `
  --output-dir outputs/intervention_sensitivity_development
```

Outputs include the complete seed-level metrics, cell summaries, paired bootstrap contrasts,
macro ranking, source and environment hashes, and metrics checksum. No figure is part of this
protocol. If a figure is later required, PaperBanana is the project-required dependency; do not
substitute another visual generator if that integration is unavailable.
