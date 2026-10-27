# ShiftGuard unified research goal

**Status:** active research programme; this file records scope and decision gates, not a novelty claim.

ShiftLab will determine whether one coherent system can improve decisions under distribution shift through (Q1) monitoring downstream decision harm, (Q2) selecting and statistically certifying candidate adaptations, and (Q3) allocating labels, monitoring, updates, retraining, switching, and fallback resources. The primary objective is cumulative net decision cost relative to a declared incumbent, subject to explicit information, statistical, and resource constraints.

The work order is benchmark first, diagnose second, optimise only if a reproducible gap remains, and independently confirm last. The immediate gate is repository consolidation, real-data availability, literature fidelity, frozen reference implementations, and matched development comparisons on synthetic and real data. Do not start RIVE, ASC, or another speculative method before that gate. At the gate, choose one of: confirm the existing framework, develop one targeted extension, narrow the paper, or stop the current formulation.

Keep distributional discrepancy, predictive degradation, and decision harm as separate estimands. Every claim must state its data, comparator, information and feedback assumptions, resource budget, uncertainty unit, and evidence strength. Synthetic oracle quantities remain evaluator-only. Real-data timings and costs must be marked verified or assumed; historical replays do not establish deployment validity or causal harm.

The unifying publication objective is one evidence-backed study of detection, certification, and resource-constrained intervention. It may narrow to a benchmark or empirical paper if the methods do not support one integrated contribution. Negative findings and established-method wins are valid outcomes.

Source charter: user-provided `goal-objective.md`, read in full on 2026-10-25. Repository foundation at that audit: branch `main`, HEAD `525c79e`; private remote `nl2992/shiftlab`.
