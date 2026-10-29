# WP3 implementation and scope audit

The [frozen protocol](data_efficient_edetector_prescreen_protocol.md) governs the
data-efficient prescreen. `data_efficient_prescreen.py` adds observation control
alongside existing paths; it does not modify the validated WP1 implementations.

The optional-sampling learner receives feature/observed-cost arrays and validation
pilot information, with no oracle argument. Theta is computed from the lagged pacer,
lagged SR and known calendar time, before current disagreement, tariff or outcome
is accessed for a decision. Selected agreement scores are -0.10; unselected scores
are zero and all detector factors are one. Maximum-tariff reservation occurs before
the current event. This avoids the invalid current-covariate-dependent scaling of
a pooled-null score described in the marginal-null audit.

The fixed-stake SR/CUSUM implementation and its horizon guarantee were already
[audited separately](horizon_edetectors_paper_to_code_audit.md). All fixed stakes,
including1, are given to all observation policies. Adaptive evidence rules are
the verified common replay functions. Adaptive SR/CUSUM uses their predictable
one-step factors; started mixtures restart each engine at each specified start.
Neutral zeros advance predictable engine history, as clarified before outcomes.
These are compositions of known methods, not claimed new betting engines.

`data_efficient_source_panel.py` generates a shared CUDA path at the exact monitor
relative onset and reuses `_one_method` and `replay_gated` for the existing panel.
PPE/Xu source factors are independently checked against their normalized-score
aliases; gated empirical Bernstein retains its original engine. Every compatible
raw-score path also gets the common engine/detector panel. Full feedback is label
unmatched. Feature ADWIN has a feature-change target and is not a harm incumbent.
Oracle expectations remain evaluator inputs to the existing source-method wrapper;
they do not enter optional observation or gated learner APIs.

The runner records starting source hashes before scheduling tasks and writes one
completed shared-path CSV at a time. It refuses existing output directories and
requires committed, clean sources and a committed protocol freeze. Evaluator
endpoints use the scheduled synthetic onset, never an alarm-inferred onset.
Early alarms and cap stops receive the full remaining-horizon delay when they do
not constitute a post-onset detection.

Before the registered run, 29 focused tests passed, including the15 existing
horizon-detector tests. They check past-only control, support/caps, neutral skip
recursions, start-mixture accounting, monitor-relative onset mapping and censoring.
Full-suite verification is required before a results commit. This implementation
audit does not establish empirical null calibration or an efficiency advantage.
