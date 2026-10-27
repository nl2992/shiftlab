# Certification Exponent one-step comparator: registered results

**Status:** Registered primary run and independent full-seed reconstruction passed.

**Protocol:** [`certification_exponent_one_step_protocol_v1.md`](certification_exponent_one_step_protocol_v1.md). The protocol froze a one-step, context-free specialization of Wang's Certification Exponent for a known uniform two-action logger, deterministic target action, binary rewards and immediate IID feedback. It is not a reproduction of the paper's history-dependent tree algorithm. MOPE uses the pinned official implementation; the third arm is a fixed-horizon Hoeffding bound and is not anytime-valid.

## Registered outcomes

| Scenario | Method | Streams | Certifications | Rate (exact 95% interval) | Mean labels |
|---|---|---:|---:|---:|---:|
| Equal-value null | Projected Kelly one-step | 1,000 | 16 | 1.60% [0.92%, 2.59%] | 197.44 |
| Equal-value null | Fixed-horizon Hoeffding | 1,000 | 0 | 0.00% [0.00%, 0.37%] | 200.00 |
| Equal-value null | Official MOPE gate | 1,000 | 11 | 1.10% [0.55%, 1.96%] | 198.84 |
| Target improves | Projected Kelly one-step | 300 | 270 | 90.00% [86.03%, 93.15%] | 96.18 |
| Target improves | Fixed-horizon Hoeffding | 300 | 92 | 30.67% [25.50%, 36.22%] | 200.00 |
| Target improves | Official MOPE gate | 300 | 279 | 93.00% [89.50%, 95.62%] | 114.04 |

On the paired alternative streams, Kelly certified 5 streams that MOPE did not, while MOPE certified 14 that Kelly did not. The paired rate difference was −3.0 percentage points (Kelly minus MOPE; exact two-sided McNemar *p*=0.0636). This does not establish a detection-rate difference. Kelly used 17.85 fewer labels on average in this specific alternative, a descriptive comparison without a registered uncertainty interval. Three MOPE null paths had empty confidence sets; the primary run records them rather than dropping them.

## Interpretation and scope

The one-step Kelly adaptation and MOPE both certified most alternatives while rarely certifying the registered equal-value null; MOPE had the higher alternative certification rate, while Kelly used fewer labels on average in this design. The fixed-horizon arm certified none of the null streams but had substantially lower power at the same 200-event horizon. These are Monte Carlo results for the frozen IID Bernoulli contract, not a proof of calibration or a general method ranking.

The experiment does not resolve the validity of any method on Open Bandit Dataset logs. It has no context, history-dependent logger, delayed feedback, adaptive candidate selection, multiple-candidate correction, or real downstream utility. The projected Kelly implementation is a labeled one-step comparator with a conservative warm-up and numerical optimization; it is not a new ShiftLab method or a novelty claim.

## Reproducibility artifacts

The output directory is [`../../outputs/shiftguard_unified/sota_reproductions/certification_exponent_one_step_v1_parallel/`](../../outputs/shiftguard_unified/sota_reproductions/certification_exponent_one_step_v1_parallel/). It contains the complete per-stream metrics, summary, manifest, exact runner snapshot and [`independent_verification.json`](../../outputs/shiftguard_unified/sota_reproductions/certification_exponent_one_step_v1_parallel/independent_verification.json). The verifier regenerated all 1,300 streams, reconstructed all 3,900 method-stream rows and matched all 1,300 pinned MOPE paths. The verification record's SHA-256 is included in the manifest artifact hashes.
