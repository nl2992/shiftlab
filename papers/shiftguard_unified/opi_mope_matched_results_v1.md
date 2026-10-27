# Matched OPI, MOPE, and fixed-horizon results v1

**Status:** complete and independently checked, 2026-10-26. This is a
registered synthetic comparison, not a real-data evaluation or a result for
the integrated ShiftGuard system. The protocol was frozen in
[`opi_mope_matched_protocol_v1.md`](opi_mope_matched_protocol_v1.md).

## Design and provenance

We generated 1,000 all-tied null streams and 300 unique-best alternatives,
each with 200 logged actions and binary rewards. The logger assigned each
action probability 0.5; three target policies assigned action-1 probabilities
0, 0.5, and 1. In the null, both action means were 0.5. In the alternative,
the means were 0.35 and 0.65, so the fixed action-1 policy exceeded the logger
by 0.15 in expected reward. Each method received the same stream within each
replication. Stream hashes, run configuration, method source hashes, and
outputs are recorded in the run manifest.

Streams were generated on the NVIDIA GeForce RTX 4060 Laptop GPU. The pinned
MOPE confidence-sequence routine ran on CPU, preserving the author numerical
implementation. The run produced 5,200 method-stream rows and eight summary
cells. [`Independent verifier`](../../scripts/verify_molitor_mope_matched.py)
checks the paired keys, hashes, exact intervals, and saved Parquet/CSV outputs;
[`the full run report`](../../outputs/shiftguard_unified/sota_reproductions/molitor_mope_matched_v1/report.md)
and [`manifest`](../../outputs/shiftguard_unified/sota_reproductions/molitor_mope_matched_v1/manifest.json)
preserve the detailed artifacts.

## Results

Intervals below are two-sided exact 95% Clopper–Pearson intervals.

| Endpoint | Result |
|---|---:|
| MOPE false promotion, all-tied null | 11/1,000 = 1.10% (0.55%, 1.96%) |
| MOPE empty confidence path, all-tied null | 3/1,000 = 0.30% (0.06%, 0.87%) |
| Fixed-horizon Hoeffding false promotion, null | 0/1,000 = 0% (0%, 0.37%) |
| OPI any false elimination of a true optimum, null | 0/1,000 = 0% (0%, 0.37%) |
| Fixed-horizon class selector false exclusion of a true optimum, null | 0/1,000 = 0% (0%, 0.37%) |
| MOPE promotion, +0.15 alternative | 279/300 = 93.00% (89.50%, 95.62%); mean labels 114.04 |
| Fixed-horizon Hoeffding promotion, +0.15 alternative | 92/300 = 30.67% (25.50%, 36.22%); 200 labels |
| OPI unique stopping / correct final singleton, alternative | 0/300 / 0/300; each exact upper 95% bound 1.22% |
| Fixed-horizon class selector correct singleton, alternative | 0/300; exact upper 95% bound 1.22% |

The three null MOPE confidence paths that became empty were reconstructed from
the registered CUDA seed and replayed with the pinned author implementation.
Their first empty events were 15, 17, and 67. One path promoted at event 63
before becoming empty at event 67; the other two did not promote. The
reconstructed stream hashes, event counts, and bound violations are preserved
in [`the anomaly audit`](../../outputs/shiftguard_unified/sota_reproductions/molitor_mope_matched_v1/mope_empty_confidence_set_audit.json).
These paths are counted as empty-set coverage failures rather than discarded.

## Interpretation and limits

In this design, the official MOPE fixed-candidate gate found the prespecified
candidate much more often than the fixed-horizon Hoeffding gate, while using
fewer labels on average. Both tested the same candidate-versus-logger value
improvement. The comparison is descriptive at this operating point; the
observed MOPE null promotions and empty confidence paths must remain visible.

OPI and the fixed-horizon class selector answered a different question: whether
they could identify the best member of a three-policy class. Neither produced
a singleton in the 200-event alternative. Their zero false-exclusion results
and their low observed identification power are specific to this short horizon,
the registered LIL/Bonferroni bounds, and this policy class. Do not rank these
selection methods against the candidate gate as if they shared an endpoint.

The experiment is a stationary context-free Bernoulli bandit with immediate
feedback and no intervention costs, model updates, delayed labels, or shift.
It does not validate dependent/slate feedback, OBD timing, adaptive candidate
selection, real-data utility, or the joint ShiftGuard controller. Empirical
calibration on these streams is not a replacement for a theorem or its
assumptions. The result establishes no general superiority or novelty claim.
