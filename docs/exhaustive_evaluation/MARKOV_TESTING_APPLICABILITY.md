# Observed-Markov baseline: native pilot and scope

2026-10-30. Previous goal turn: progress (504-setting epoch round committed). Current continuation executes native functions and checks the information-contract boundary. Goal remains active; full SOTA inventory and novelty work are incomplete.

## Primary source and native execution

[Sethi et al., Asymptotically Optimal Sequential Testing with Markovian Data](https://arxiv.org/html/2602.17587), v3, Section1 problem, Section4 design and AppendixG.3 notebook inspected. The [ICML proceedings page](https://proceedings.mlr.press/v306/sethi26a.html) identifies the final publication. The publisher's raw PDF endpoint did not parse through the web tool, so the primary arXiv full text was used; exact final-PDF equivalence is not claimed.

Author repository https://github.com/Alhad-Sethi/Sequential-Markovian-Testing pinned at9414edf5938127c80544261212e28b95a4ffc287. Its G3_ParametricFamily.ipynb supplies build_P_theta and SequentialMarkovChainTest. The pilot extracts and executes those definitions unchanged, omitting notebook plotting and large-run cells. Local data generation uses the native family with2 states rather than64, fixed base matrix[[.8,.2],[.3,.7]], feature[−1,1], null interval[.4,.8], theta=.6/null and−.6/alternative, alpha.05, seeds17/29/43, cap2000 transitions. Original notebook and algorithms are untouched. This is a reduced native-task execution pilot, not a paper-scale reproduction.

All3 null paths remain unstopped at2000 transitions; their final statistics are.281/.028/.119 against thresholds16.484/16.360/16.612. All3 alternative paths stop at6 transitions (statistic7.741, threshold7.481). Repeated alternative times arise from these simulated paths, not independent efficacy precision. Six paths cannot establish5% error control, power-one, asymptotic optimality or a matched-cost superiority result. Transition counts, finite numerical outputs and stochastic-matrix checks pass.

Artifacts: markov_native_pilot_registration.json, markov_native_pilot_results.json. Script: pilot_markov_testing.py. Source notebook SHA and script SHA frozen before execution. Ruff0.17.1 check/format and embedded assertions pass; no external optimizer/service or visual generation required.

## Why unchanged chronological loss testing is excluded

The source's model is a time-homogeneous ergodic finite-state chain observed every transition; the hypothesis concerns its transition matrix. The criterion is stopping time, not query/switch deployment cost. ShiftLab has selectively observed/delayed common outcomes and an explicit conditional paired-mean null. A Markov chain generating covariates/outcomes does not make the observed losses a fully observed chain with the same kernel.

Two exact checks accompany the pilot:

1. For P=[[.9,.1],[.2,.8]], observing every second state gives P²=[[.83,.17],[.34,.66]], maximum entry difference.14. Treating consecutive observed states as one-step transitions tests the wrong model. A known fixed-gap transformation can be modeled, and independent geometric sampling can also admit a transformed kernel under suitable conditions; this is not a universal impossibility. Adaptive selection depending on hidden history and varying delays needs its own observation model.
2. For a3-state chain with rows[.8,.1,.1],[.1,.2,.7],[.2,.3,.5], map hidden states0/1 to loss0 and state2 to loss1. Hidden states0 and1 have the same loss but different next-loss1 probabilities.1 and.7. The partition fails the strong lumpability condition, so homogeneous Markov behavior of the aggregated loss is not guaranteed for arbitrary initial/history laws. The example does not say that every aggregation fails or prove a failure for our particular datasets; it refutes the unsupported automatic reduction.

Disposition: **EXCLUDED_UNCHANGED_OBSERVATION_AND_NULL_CONTRACT** for the general queried-loss comparison. Include a native Markov method only where the actual state, chain structure and query observation law are justified, or establish a reduction with its own proof. In finite-state fully observed synthetic cells, a restricted operational comparison is possible and should not be confused with general dependent real-data safety. Native pilot completion is recorded separately from this exclusion.

This resolves the direct applicability question, not every extension. Robust-Markov testing is also established prior art for claims based merely on Markovian evidence plus decision costs; existing switching_markov_robust_sequential_testing_prior_audit_v1.md remains authoritative.

## Fourth-round mechanism finding

Post-hoc factorial summaries of the retained paced_epochs_results.json show mean late-case excess cost for free pacing:−7.817 at1 epoch,−11.256 at2,−24.975 at4,−15.136 at5,−6.077 at10 (averaging the registered discount/bet/cap/allocation cells within each group). Overall macro excess worsens from−71.644 at1 epoch to−44.033 at4 and−17.965 at10. Thus shorter evidence history can help late benefit while losing across the full case family. This is descriptive, conditional on the designed grid, not a causal generalization or independent hypothesis test.

The best late-only configuration is EP_0057 (uniform/free,4 epochs,gamma1,FTL,cap.75), late excess−85.527. It was selected after looking at that case and cannot be called a new confirmed finalist. It also does not beat every strong reference in that same cell. The all-case winner remains the original Kelly parent. Keep both observations: global failure does not imply every mechanism is useless, and a favorable selected cell does not establish a useful new method.

Next bounded work: inspect the robust-synthesis residual and distinct e-detector family; then consider a prospectively selected adaptive temporal mechanism only if it has an irreducible source-level difference and survives matched equally informed controls. Do not start another grid solely to chase the best exposed late cell. Reserved real windows remain unopened; no novel or real net-utility result established.
