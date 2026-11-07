# CAMS-MAX source fidelity and matched validation

## Method and scope

The NeurIPS 2024 paper defines CAMS-MAX as the stochastic-setting ablation that selects the most
probable policy under the policy weights, then that policy's most probable model (Appendix G.7).
The benchmark supplies two constant policies from paired model losses and no contexts. This is the
paper's context-free special case. The source-reproduced `CAMSDeploymentAdapter` core now has a
registered `cams_max_adapter` factory selecting `variant="CAMS-MAX"`; the same core is covered by
the existing author-source comparison tests.

The measured policy is a common-contract deployment adapter: it uses deterministic argmax model
deployment with incumbent retention on ties, a hard label cap, delayed feedback, and switching
costs. The advice set contains only the two constant model policies; there are no contextual policy
features or paper-specific datasets. It is therefore a CAMS-MAX algorithm-core comparison under
ShiftLab's deployment contract, not a reproduction of the complete CAMS paper system.

## Results

All comparisons pair CAMS-MAX and CAMS on the same stream and seed. Synthetic intervals bootstrap
independent seeds within each regime; real-data intervals bootstrap independent source datasets
after averaging seeds within episodes and episodes within a source. The synthetic regimes are
reported separately because they are distinct stress designs, not a single target population.

| Panel | Matched jobs | CAMS-MAX minus CAMS |
|---|---:|---|
| 21 synthetic validation regimes, 100 seeds each | 2,100 | Mean ΔJ across the 21 regime means: +4.34; CAMS-MAX has higher mean cost in 20/21 regimes. Per-regime paired-seed estimates and intervals are in the JSON. |
| Five fresh real datasets, 20 seeds | 1,240 (62 episodes) | Equal-source ΔJ +1.99 [−0.51, +4.41]; labels −5.53 [−10.21, −0.85]; first-promotion delay +3.11 [+0.51, +7.48]. |
| Nine cached real datasets, 10 seeds | 1,680 (168 episodes) | Equal-source ΔJ +4.24 [+1.95, +6.92]; labels −8.88 [−12.49, −5.01]; first-promotion delay +23.32 [+8.06, +42.76]. |
| WP1 real replay, 14 source clusters, three seeds | 1,044 episode-seed rows per method | All 348 episodes: ΔJ +3.73 [+1.30, +5.60]. Late improvement: +5.29 [−2.33, +17.00]; reversal: −6.49 [−27.26, +17.67]. See `wp1/cams_max_comparison.json`. |

The matched 1,000-seed in-class null replay gives CAMS-MAX/CAMS promotion rates of 95.4%/96.7%
on V_null, 95.7%/96.2% on V_null_dep_r5, 94.0%/93.9% on V_null_dep_r8, 94.6%/95.0% on
W_null_dep_r9, and 93.3%/92.8% on W_null_dep_r95. On the two out-of-class 1,000-seed nulls,
rates are 95.2%/95.4% (O_null_order2) and 94.7%/94.3% (O_null_semimarkov). CAMS and CAMS-MAX
do not claim the registered V1 or V2 certificates; these high empirical promotion rates are a
descriptive warning for deployment under marginal-null and misspecified streams, not a formal
validity assessment or guarantee.

Across these matched panels, CAMS-MAX uses fewer labels but generally has higher net cost and
slightly later deployment than CAMS. The selected-seed intervals and same-data class definitions
are descriptive. None of these comparisons is an independent confirmation or a claim that either
method is universally inferior.

## Reproduction

All run commands use the exact seed bases and panels from the original validation manifests. The
outputs are gitignored; each manifest records the settings, source hashes, and run time.

```sh
uv run python scripts/sota_sprint/screen.py --kind synthetic --regimes V_better_a,V_better_b,V_better_c,V_dep_better_r5,V_near,V_bursty,V_null,V_worse,V_null_dep_r5,V_null_dep_r8,V_late_600,V_reversal_1000,V_recurrent,W_better_dep_r7,W_better_dep_r9,W_null_dep_r9,W_null_dep_r95,W_worse_dep_r8,W_late_1000,W_reversal_700,W_delay600_better --policies cams_max_adapter --seeds 100 --seed-base 2026110601 --workers 4 --out outputs/sprint2/CAMS_MAX/validation_synth100
uv run python scripts/sota_sprint/screen.py --kind synthetic --regimes V_null,V_worse,V_null_dep_r5,V_null_dep_r8,W_null_dep_r9,W_null_dep_r95,W_worse_dep_r8 --policies cams_max_adapter --seeds 1000 --seed-base 2026110602 --workers 4 --out outputs/sprint2/CAMS_MAX/validation_null1000
uv run python scripts/sota_sprint/screen.py --kind synthetic --regimes V_null,V_worse,V_null_dep_r5,V_null_dep_r8,W_null_dep_r9,W_null_dep_r95,W_worse_dep_r8 --policies cams_adapter --seeds 1000 --seed-base 2026110602 --workers 5 --out outputs/sprint2/CAMS_MAX/validation_null1000_cams
uv run python scripts/sota_sprint/screen.py --kind synthetic --regimes O_null_semimarkov,O_null_order2 --policies cams_max_adapter --seeds 1000 --seed-base 2026110605 --workers 2 --out outputs/sprint2/CAMS_MAX/validation_ooc1000
uv run python scripts/sota_sprint/screen.py --kind synthetic --regimes O_null_semimarkov,O_null_order2 --policies cams_adapter --seeds 1000 --seed-base 2026110605 --workers 3 --out outputs/sprint2/CAMS_MAX/validation_ooc1000_cams
uv run python scripts/sota_sprint/screen.py --kind real --regimes rialto,spam,weather,openml_ldpa,uci_occupancy,airlines,bank,elec2,criteo --policies cams_max_adapter --seeds 10 --seed-base 2026110603 --workers 3 --out outputs/sprint2/CAMS_MAX/validation_real_exposed10
uv run python scripts/sota_sprint/screen.py --kind real --regimes metro,beijing_pm25,bike_hour,appliances,household_power --policies cams_max_adapter --seeds 20 --seed-base 2026110604 --workers 3 --out outputs/sprint2/CAMS_MAX/validation_real_fresh20
uv run python scripts/sota_sprint/analyze_cams_max_validation.py --out docs/sprint2/CAMS_MAX_VALIDATION.json
```

The per-regime metrics and intervals are in `CAMS_MAX_VALIDATION.json`. The focused CAMS source
tests pass: `uv run pytest -q tests/promising_directions/test_sota_cams.py` (10 passed, 6 skipped).
