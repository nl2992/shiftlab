# Seed provenance correction: fixed-split development comparison

**Recorded:** 2026-10-26. This is an append-only correction to the provenance of
`outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_dev_v1/`.
The frozen protocol and original artifacts are retained unchanged so their
historical hashes remain verifiable.

The development comparison used seed IDs `20,265,000–20,265,059`. These IDs
overlap the separate Target-Scout Markov-context null calibration, which used
`20,265,000–20,265,999` under a different data-generating configuration
(persistence 0.80, zero signal, proxy errors 0/0.25, switching costs 0/0.05,
and 20%/40% caps). Therefore, the development comparison is **not seed-disjoint
from all prior experiments**, contrary to the broad wording in its historical
protocol and early inventory notes.

The overlap does not change the within-run matched comparisons: each method in
the development comparison received the same generated stream and query
uniforms for each seed/cell. It does mean that this development block must not
be described as independent of, pooled with, or used as fresh confirmation
against the earlier Markov-null block. The Markov calibration tested a different
configuration and does not calibrate this exact three-method comparison.

The comparisons remain exploratory only. Any new error-rate calibration and
paired confirmation use seed ranges disjoint from both blocks. The provenance
annotation is recorded in the development `manifest.json` and
`verification.json`; the verified data artifacts themselves are unchanged.
