# Criteo Uplift v2.1 real-data eligibility audit

**Audit date:** 2026-10-26  
**Decision:** **no-go for causal policy-value / intervention evaluation under the current released-file documentation.** Keep it only for replications of the dataset's published uplift-benchmark protocol or descriptive prediction until Criteo clarifies the negative-label sampling mechanism and supplies any required inclusion weights.

## Source and reproducibility

The [Criteo AI Lab dataset page](https://ailab.criteo.com/criteo-uplift-prediction-dataset/) describes an advertising-treatment benchmark assembled from incrementality tests, with assignment, conversion, visit, exposure, and 12 anonymized features. It reports 13,979,592 rows and an 85% treatment ratio for corrected v2. The [accompanying paper](https://arxiv.org/abs/2111.10106) states that a random draw assigns users to treatment/control, the features are measured before assignment, and v2 was constructed to address feature/treatment confounding in v1. Its authors report a C2ST that did not reject treatment-feature independence (p=0.13667). They describe 14-day outcome collection after assignment, but the release has no individual event or label-release timestamps. It merges multiple tests without trial IDs, and the source has non-uniform negative-label sampling.

There is a material estimand issue in addition to the license discrepancy. The [paper's main dataset description and datasheet](https://arxiv.org/abs/2111.10106) explicitly state that **non-uniform negative-label sampling** was performed, while the datasheet's separate response to its sampling-strategy question says “N/A.” The public documentation does not specify the inclusion probabilities or fully define the resulting target population. The paper's i.i.d. notation and its treatment-feature C2ST do not establish that a causal policy-value estimator on the released, outcome-sampled records identifies value in the original advertiser population. Because selection depends on the realized label, the reported 85% marginal treatment fraction is not by itself an adequate propensity for this estimand. The live [official Criteo page](https://ailab.criteo.com/criteo-uplift-prediction-dataset/) states **CC BY-NC-SA 4.0**, while the paper's datasheet states CC BY-SA 4.0; follow the stricter official terms unless clarified.

The full compressed file was streamed from the pinned [Hugging Face dataset revision](https://huggingface.co/datasets/criteo/criteo-uplift/tree/2424920019e49d52d72c13ac1143ec5d53af276b), without writing the raw file locally. The audit verified 311,422,618 compressed bytes, SHA-256 `2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc`, all 13,979,592 records, the 16-field schema, finite feature values, and binary assignment/outcome fields. The observed treatment fraction was 0.85000013. A CUDA MLP treatment-predictability diagnostic on a seeded 349,911-row sample achieved AUC 0.5076. This is consistent with the paper's source validation but is not proof of the randomization mechanism or exact per-unit propensity. No record-level values or identifiers were saved. Reproduce with:

```powershell
uv run python scripts/audit_criteo_uplift_stream.py --device auto
```

The aggregate-only output is `data/reports/criteo_uplift_stream_audit.json`. Its feature-only treatment-predictability diagnostic trained a small MLP on a seeded sample of 349,911 records and evaluated on 69,983 held-out sampled records using the NVIDIA RTX 4060 Laptop GPU. Test AUC was **0.5076**. This is consistent with weak feature-based treatment predictability in that diagnostic, but it does not prove the assignment mechanism, establish a known propensity, or rule out trial-level dependence.

## What it can support now

The data can be used to reproduce established uplift-ranking metrics under the source paper's stated benchmark conventions, or for descriptive prediction. It cannot currently support the proposed causal policy-value / cost frontier: unknown label-inclusion probabilities prevent us from establishing the target population and whether standard treatment IPW or doubly robust values remain identified after outcome-dependent sampling. The outcome is recorded over a source-reported 14-day window, but there is no event-time release clock. The post-assignment `exposure` field must not be used as a policy feature.

It therefore does **not** close the real downstream-intervention gate. Do not run candidate-policy value comparisons on this source unless the sampling issue is resolved from primary documentation or the authors provide the needed inclusion mechanism/weights.

## Limits and holdout status

- The stream has no event or label-release chronology. Its 14-day outcome window is not an individual release clock, so the source cannot validate anytime-valid monitoring, feedback delay, or temporal distribution shift.
- The published file merges multiple randomized incrementality tests without a trial identifier. The observation-level randomization and independence conditions required by an OPE confidence sequence must be justified from the primary source before using one.
- The aggregate audit read the complete source and recorded overall arm-level rates and a treatment-predictability diagnostic. It did **not** compute candidate-policy values or compare adaptation methods. Any future final split must be frozen before method-specific evaluation; disclose this full-source aggregate audit and do not describe the whole file as never inspected.
- There is no source-grounded treatment cost. Report a predeclared cost sensitivity frontier and keep conversions, visits, and imposed cost units distinct.
- The noncommercial share-alike license must be preserved. Do not put the raw file in Git or redistribute it outside the license.

**Current status:** source bytes, schema, and aggregate structure verified; causal intervention eligibility **not established** because the label-sampling mechanism is undocumented. The CUDA treatment-predictability audit does not resolve that issue. This source does not close the independent real-data confirmation gate. No policy-value results have been computed.
