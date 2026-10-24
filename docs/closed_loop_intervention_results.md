# Closed-loop promotion and rollback results

**Run:** 24 October 2026, registered 2,000 seeds per scenario, horizon 800 events per stage,
GPU-generated paired costs and query streams, two total label caps, six scenarios, four
policies. This is a simulated development result. It does not establish deployment validity or
novelty.

Reproduce with the command in the [protocol](closed_loop_intervention_protocol.md). The run
used an NVIDIA RTX 4060 Laptop GPU, PyTorch 2.9.1+cu130 and CUDA runtime 13.0. All 96,000
policy-stream rows respected their hard label budget. The metric Parquet SHA-256 is
`d00ac685f61609f4f361d7a63e100d13418dc7d46603e0e68823dacd023d28cb`; the complete run
configuration, environment, and source hashes are in
[`outputs/closed_loop_intervention/manifest.json`](../outputs/closed_loop_intervention/manifest.json).

## Results that change the next experiment

The two-gate policy helped in the designed reversal: it rolled back 364/2,000 (18.2%) of
promoted streams and improved expected net utility by **3.07** over promotion-only under the
20% label cap (seed-paired 95% bootstrap interval **[2.48, 3.70]**). Utility was still strongly
negative (**−81.50**) versus continuing (**0**), so this is partial damage control, not a
successful intervention policy.

For a persistent candidate, promotion-only achieved expected net utility **95.43**; adding
rollback monitoring reduced it to **93.44** because the policy spent more on labels and no
rollback occurred. The two-gate policy also reduced expected utility under persistent weak
benefit by about **0.40**. Monitoring has a real price even when it is correctly quiet.

Shadow-only benefit exposed the extrapolation failure directly. Every stream passed promotion,
but deployment had zero expected benefit. Promotion-only yielded **−0.57** utility and the
rollback policy yielded **−2.55**; rollback occurred on 20/2,000 streams. A positive shadow
contrast alone does not certify benefit in the future deployment environment. In the
late-benefit scenario, the gate promoted only 15/2,000 streams (0.75%), despite the candidate
being beneficial after deployment; deployment-only benefit cannot be learned from the shadow
period without further assumptions or evidence.

| Calibration target | Events | Estimate | Simultaneous one-sided 95% upper bound |
| --- | ---: | ---: | ---: |
| False promotion under zero shadow gain, 20% cap | 20/2,000 | 1.00% | 1.70% |
| False promotion under zero shadow gain, 40% cap | 20/2,000 | 1.00% | 1.70% |
| False rollback under zero deployment gain after strong shadow benefit, each cap | 20/2,000 | 1.00% | 1.70% |
| False rollback under persistent positive deployment gain, each cap | 0/2,000 | 0.00% | 0.25% |

Bounds use exact one-sided Clopper-Pearson intervals with Bonferroni adjustment across the
eight reported calibration cells. Each stage allocates alpha 0.025; the displayed simultaneous
limits are conservative relative to per-test alpha. The two cap settings often produce the
same error count because the lower cap was not binding in the shadow-only calibration streams.

Unconditional promotion had the highest expected utility when benefit was present, but it
promoted every stream under the zero-benefit null (2,000/2,000 false promotions). Continue was
best in the zero-benefit and shadow-only deployment scenarios. The certificate gate sharply
reduced unnecessary deployment there, at the cost of labels and missed opportunities when
benefit appeared only later.

## Interpretation and next milestone

These results support two conclusions for the implementation. First, frozen shadow evidence
can gate an intervention under a bounded paired-cost model, and a separate forward process can
limit rollback escalation under its own conditional null. Second, those controls do not
guarantee that a candidate's shadow benefit persists into deployment. The zero-gain
post-promotion null also shows that rollback can impose a small error rate and additional
label cost even with the e-process gate.

Before calling the controller useful, run an independent-seed confirmation with a frozen
scenario grid varying label propensity, label price, promotion and rollback costs, reversal
time, and reversal severity. Calibrate the selected policy on non-harmful deployment streams
first, then compare net utility against continue, promotion-only, immediate promotion, and a
cost-aware finite-action baseline. Use a separate time block for candidate construction and
promotion evidence if the candidate is selected adaptively. Retain the present controller as
a transparent reference policy, not a selected winner.

The paired bootstrap contrasts are descriptive and are not adjusted across all scenario,
budget, and method comparisons. The synthetic cost law is independent across time and between
shadow and deployment, unlike financial panels and many operational streams. The run does not
address delayed labels, serial dependence, miscalibrated propensities, adaptive repeated
candidate search, or off-policy uncertainty. No figure was generated for this benchmark.
