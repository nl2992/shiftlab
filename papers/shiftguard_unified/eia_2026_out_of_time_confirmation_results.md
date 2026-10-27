# EIA 2026 out-of-time comparison — results

**Status:** completed as a frozen retrospective event-time replay on 2026-10-26. The period was not present in earlier ShiftLab EIA result manifests or result text according to the readiness audit. EIA publication and revision times remain unknown, so this is not verified prospective performance.

## Frozen task and provenance

The source was the official EIA EBA archive retrieved 2026-10-20, SHA-256 `3a6143c4bd853c3d6a9d9d3bb3ca7f1603a641835e9c7a050e5c8a927101936f`. The learner predicts next-hour demand from the four contemporaneous EBA series. Eligible training and calibration events are 2019–2024 and 2025 respectively; final test is 2026-01-01 through the last complete forecast on 2026-10-19. Rows with missing values in the four predictors or next-hour target are excluded; source gaps are preserved. Models and policy settings are unchanged from the EIA development protocol.

The final test included 6,943 CISO and 6,797 ERCO forecast rows. Policies were frozen Ridge, weekly refit, monthly refit, and the 24-hour error-trigger heuristic, under assumed feedback delays of 0, 24, and 168 hours. The RTX 4060 executed the fits on CUDA. No row-level predictions or labels were written to outputs.

## Findings

Across all three delay assumptions, each adaptive policy had lower test RMSE and MAE than the frozen model in each authority. For CISO, frozen RMSE was `2235.80`; weekly refit ranged from `1651.21` to `1672.10`, monthly from `1686.21` to `1705.05`, and error-trigger from `1652.70` to `1672.87`. The paired RMSE differences versus frozen ranged from `−584.59` to `−530.75`; all corresponding descriptive 95% fixed-week-block intervals were below zero.

For ERCO, frozen RMSE was `2013.63`; weekly refit ranged from `2004.16` to `2005.08`, monthly from `2005.55` to `2006.63`, and error-trigger from `2005.11` to `2006.14`. Paired RMSE differences ranged from `−9.47` to `−7.01`, again with descriptive block intervals below zero. Thus the observed adaptation gain transferred to this period in both authorities, but its magnitude differed sharply by authority.

Weekly refitting performed 41 updates per authority, monthly refitting 9, and error-triggered refitting 9–38 depending on authority and delay. Error-triggered updates were close to weekly RMSE for CISO with fewer updates, while ERCO gains over frozen were modest. These are resource counts, not converted operating costs. The error-trigger rule is a heuristic and the results do not validate a false-alarm guarantee.

Uncertainty uses 42 populated 168-hour blocks per authority and delay. Intervals are descriptive, paired, and not multiplicity-adjusted. CISO and ERCO are separate historical cases, not independent deployment replications. The source lacks verified label-release times; delay values are sensitivities. No downstream action or electricity-system utility was measured.

## Interpretation and remaining gates

This is one previously unscored real temporal period for predictive-risk and retraining-resource comparison. It supports a narrow statement that the frozen weekly, monthly, and error-trigger adaptation rules reduced retrospective prediction error on this EIA period under the stated event-time and delay conventions. It does not establish decision-harm reduction, causal intervention benefit, real-time performance, or general future benefit.

The Upworthy fixed-horizon package-selection evaluation is now a second task family with a project-relative randomized holdout and measured CTR outcome. Together, Upworthy and this EIA replay provide two task-specific final-period/split evaluations: direct package choice with observed click utility, and retraining-resource allocation against forecast risk under assumed delays. This satisfies the objective's two-family count at the component level, but neither evaluates the full monitor–certify–intervene system. EIA release timing remains unknown; update counts are resource proxies without converted operating cost. Hillstrom's test split is exposed; CUVET's official test remains unread because its released outcome means violate CUVET's published response assumptions and exact arm propensities are undocumented. The complete-system and manuscript gates remain open. See [`real-data confirmation gate audit`](real_data_confirmation_gate_audit.md).

Artifacts: [`eia_2026_out_of_time_confirmation_protocol_v1.md`](eia_2026_out_of_time_confirmation_protocol_v1.md), [`readiness audit`](../../data/reports/eia_2026_holdout_readiness.json), and [`aggregate outputs`](../../outputs/shiftguard_unified/independent_real_data/eia_2026_v1/).
