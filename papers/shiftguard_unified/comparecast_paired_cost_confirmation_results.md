# Q1 direct paired-cost confirmation: results

**Status:** completed on CUDA, with independent artifact verification passed on
2026-10-26. This is a matched synthetic evaluation of the official Comparecast
e-process and ShiftLab's bounded conditional-mean monitor. It is not a test of
one method's statistical validity against the other's: Comparecast targets a
weak running-average score null, while ShiftLab targets an eventwise
conditional-mean null.

The run contains 300 fresh seeds in each of six scenarios and 3,600
method-stream rows. All streams processed the registered 1,600 monitoring
events. The official implementation is pinned to
`yjchoe/ComparingForecasters` commit
`52748c86e0429a9612dc79892c3be6156a524132`; its e-process file hash matched
the separately calibrated version. The independent verifier checked the
protocol and calibration hashes, all recorded artifact hashes, source
identity, seed block, row and cell counts, finite e-values, exact intervals,
and onset eligibility. Full metrics, manifest, results, and verification are
in [`outputs/shiftguard_unified/sota_reproductions/comparecast_paired_cost_confirmation_v1/`](../../outputs/shiftguard_unified/sota_reproductions/comparecast_paired_cost_confirmation_v1/).

| Alternative | Comparecast detections / 300 (simultaneous exact interval) | ShiftLab detections / 300 (simultaneous exact interval) | Mean delay: Comparecast / ShiftLab |
|---|---:|---:|---:|
| Boundary-local harm | 295 (95.1%, [95.1%, 99.7%]) | 300 (100%, [98.1%, 100%]) | 863.6 / 322.2 events |
| Residual-variance shift | 0 (0%, [0%, 1.9%]) | 17 (5.7%, [2.7%, 10.3%]) | not detected / 832.0 events |
| Recurring regimes | 212 (70.7%, [63.0%, 77.6%]) | 300 (100%, [98.1%, 100%]) | 1,404.4 / 167.3 events |
| Harmful adaptation | 300 (100%, [98.1%, 100%]) | 300 (100%, [98.1%, 100%]) | 601.5 / 282.5 events |

There were zero pre-onset alarms in these four alternatives and zero alarms in
the 300-stream stationary and 300-stream benign-nuisance controls for either
method. The separate 2,000-stream-per-control calibration supplies
Comparecast's registered weak-null calibration evidence; this run's control
counts do not replace it. Intervals are Bonferroni-adjusted over the eight
method-by-alternative cells. No cross-method superiority test was registered,
and the alarm-rate differences should be read descriptively because the nulls
differ.

One of the 300 residual-variance streams had no evaluator-defined
material-harm onset. The registered joint per-run rate and interval count that
stream as no post-onset detection (0/300 for Comparecast; 17/300 for ShiftLab).
Among the 299 streams with an onset, the descriptive counts are 0/299 and
17/299; those conditional rates are not the registered interval endpoint.
The exact eligibility counts are preserved in the output
`onset_eligibility.json` and independently checked in `verification.json`.

The results show weak power on residual-variance harm and substantially later
Comparecast crossings on recurring regimes in this particular simulator. They
do not establish broad superiority, validity under delayed or selectively
observed labels, performance on real data, or a novel method. The next research
decision still depends on the integrated Q3 comparison and the applicable
published-baseline audit.
