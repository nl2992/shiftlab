# Cycle-7 follow-up diagnostic: uniform-fallback interaction

2026-11-01. Registered before execution, after cycle-7 results were observed.
This is a bounded development diagnostic, not another attempt at cycle-7 acceptance.

Question: when the delay switch routes acquisition to a uniform calendar, does bypassing
the gap branch materially affect null false promotions, and does imposing the same gap
on fallback resolve either observed cost regression?

Keep frozen DSS, its existing no-delay-switch ablation, and episode_front. Add one diagnostic
subclass: only when `dss_uniform` is true, reject a query within four rounds of the last
request. Otherwise invoke the unchanged DSS query rule. Do not change evidence, rollback,
budget, thresholds or the frozen candidate. Name it `fallback_gap4_diagnostic`.

Use T=1000, 40 unused development seeds [181000,181040), four configurations:
boundary null rho=.8,B/T=.25,d=10; boundary null rho=.5,B/T=.5,d=10;
the cycle-7 long-delay harmful primary cell; and the rho=0,B/T=.1 earlier-onset harmful
primary cell. These are selected because the exposed cycle-7 results and reviewer identified
them. No independent generalisation claim or hyperparameter selection is allowed.

Report per-stream cost, false promotion, correct promotion and actual minimum request gap.
Use paired cost differences and Wilson null intervals. Hypothesis: applying the gap to
fallback reduces dense-sampling inflation but does not address all failures; it may save
query cost by discarding scheduled requests. Do not interpret fewer labels as a free
algorithmic advance or claim a nominal guarantee. No acceptance threshold, confirmation,
or repaired-method contribution follows from this diagnostic alone.

Runner: `scripts/run_atlas_fallback_diagnostic_v1.py`; outputs:
`outputs/failure_atlas_v1_cycle7/fallback_diagnostic/`; compact table appended below after run.
