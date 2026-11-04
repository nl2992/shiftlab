# B3+ comparator gate after Cao (2026) — 2026-11-08

## Decision

Do not run another broad P7s seed sweep yet. The closest prior art found is Cao, *The First-Order Value of Free Covariates in Budgeted Risk Monitoring*, arXiv:2611.00576v1, submitted 2026-10-31: <https://arxiv.org/html/2611.00576>.

Cao's work monitors one model's binary loss against a one-sided risk threshold. Covariate blocks can trigger labels; a label-history sleep controller supplies fallback monitoring; a shared e-detector controls false alarms. Its budget is an expected source-prefix rate, and it does not give a hard pathwise cap or a paired promotion/rollback contract. The gap is plausible but narrow: B3+ compares two frozen models using paired utility, takes promotion and rollback actions, and operates under delayed feedback and a hard per-episode cap. This is a comparator hypothesis, not novelty evidence.

## Registered comparison design

### Policies

1. **P3b:** current paired anytime-valid evidence and budget pacer.
2. **P7s:** frozen settled-state acquisition policy.
3. **Adapted label-history:** Cao's label-history sleep / DE-CuSum acquisition schedule, adapted to paired utility observations. Use P3b's paired e-process and action thresholds so only acquisition changes.
4. **Adapted hybrid:** Cao's covariate-block trigger OR label-history fallback, feeding the same paired e-process and action thresholds. Covariates may request labels but must not directly trigger promotion or rollback.

The two adapted policies must be specified and frozen before confirmatory runs. All four policies receive the same covariate sequence, label delay, initialization information, query-price accounting, and hard cap `B=200`. Pending requests count against the cap at issue time; no requests are permitted after the cap is exhausted. For cap fairness, transform Cao's expected-rate request schedules into a deterministic remaining-budget throttle, document the transformation, and report the original unconstrained schedule only as a diagnostic. Recompute propensity weights and bet caps using the actual issue-time propensity; if a valid paired e-process cannot be retained after adapting an acquisition policy, that policy cannot be treated as a valid control.

### Frozen first adaptation (development implementation)

The initial source-matched adaptation is implemented in `scripts/promising_directions/b3_plus_policy.py` and `scripts/promising_directions/b3_plus_cao_comparator.py`. Both controls share the P3b paired e-process and action threshold. An auxiliary directional score uses only delayed queried paired outcomes: positive means evidence favoring a switch away from the currently deployed model; negative resets the score and sleeps for 19 issue rounds. The label-history control queries while awake. The hybrid ORs that request with a covariate block trigger based on the *previous completed* 25-event block, thresholded at `|mean(X)| >= 1.96/sqrt(25)`. The trigger has approximately 5% two-sided false-trigger probability for IID standard-normal source covariates. The current-event covariate is never used to request its own label.

Both controllers apply the same remaining-budget pacer as P3b while awake/triggered, and use the actual issue-time propensity in inverse weighting and bet caps. During label-history sleep the propensity is zero and the bet is zero, so the evidence factor is neutral; these acquisition controls therefore do not satisfy P7s's positive propensity floor, but retain a nonnegative-wealth paired process. This is a deliberate source-inspired adapter of Cao's sleep/hybrid structure, not Cao's original risk-threshold method or a theorem reproduction. We do not report it as an exact reproduction. Development parameters are fixed above before running; confirmatory seeds are disjoint. Any refinement based on development results requires a new protocol version before confirmation.

### Scenarios

- **Stationary positive:** challenger has constant positive paired utility after promotion; measure unnecessary label cost and false rollback.
- **Abrupt reversal:** challenger advantage changes sign after promotion; measure time from reversal to rollback and resulting excess deployment loss.
- **Benign covariate shift:** inputs shift while paired utility remains positive; measure whether covariate-trigger acquisition wastes labels or causes a false rollback.

Use frozen classifiers and a synthetic generator with known change times. Include delayed feedback under the existing B3+ timing convention. Separate development seeds from confirmatory seeds; tune the adapted controls only on development seeds. Preserve a fixed horizon, per-episode budget, query price, and switch price across policies.

### Outcomes and gate

Primary outcomes: (i) paired net cost, (ii) false rollback probability in stationary-positive and benign-shift scenarios, (iii) reversal-to-rollback delay and excess deployment loss after reversal, (iv) pathwise cap violations. Also report labels requested and deployment switches.

Before confirmatory evaluation, choose and record acceptable false-rollback and rollback-delay limits based on the application objective. Advance P7s only if its paired net cost is lower than both adapted controls while meeting those limits and with zero cap violations. Otherwise revise the method or close the P7s novelty lead. No result from the existing selected streams substitutes for this comparator gate.

## Source-matched distinction

Cao's model and guarantees are not interchangeable with B3+: the paper's null is a conditional binary-risk upper bound for one deployed model, labels certify a one-sided risk alarm, and its source budget is expected rather than pathwise. B3+ uses paired loss differences for two fixed classifiers, with actions that promote and later roll back a replacement, and a hard episode cap with delayed labels. These differences make a concrete comparison worthwhile but do not prove that P7s is novel or superior.

Related source: Setoudehtanzangi and McLachlan (2026), [classification-risk-optimal label acquisition](https://arxiv.org/html/2609.06873), targets classifier fitting and asymptotic excess classification risk. It independently rules out broad claims that decision-oriented label acquisition itself is new.

## Development outcome and gate status

The first 200-seed-per-scenario matched run is recorded in `B3_PLUS_CAO_DEVELOPMENT_FINDINGS_2026-11-08.md`. P7s saves cost in stationary-positive and benign-shift scenarios, but its reversal cost is higher than both adapted controls and its rollback is slower. The sentinel and settled-rate development sensitivities did not close that gap. Do not run confirmatory seeds for the current method. The comparison runner rejects `--phase confirm` until a revised candidate and protocol pass the development gate.
