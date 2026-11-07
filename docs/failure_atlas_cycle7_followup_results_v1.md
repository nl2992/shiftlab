# Cycle-7 fallback diagnostic results

2026-11-01. COMPLETE; 640 method runs on 40 paired development seeds per cell.

The extra gap is a local diagnostic, not a new accepted method. It reduced false promotion
from 9/40 to 0/40 in the rho=.5, B/T=.5, d=10 null. At rho=.8, B/T=.25, d=10,
false promotion remained high: 11/40 for DSS and 12/40 with the fallback gap.
The two alternative cost regressions are unchanged by this extra gap.

**Decision:** do not promote this patch as a solution. The fallback interaction is real,
but a four-round gap alone is insufficient. Cycle 7 remains complete and failed under
its full acceptance claim; preserve the demonstrated scoped acquisition-cost improvement.
A future repair needs a separate protocol and new seeds, including both adverse cost settings.
No confirmation seeds were used.

The provisional native follow-up review checked all 640 records and reached the same
diagnostic-only conclusion. In the moderate-dependence null, the patch reduces requests
from 500 to 245, so spacing and reduced sample count are confounded; 0/40 has Wilson
upper bound .088. In both adverse cost cells the new branch is inactive (the existing
calendar is already sparse, or uniform fallback is not selected). This explains why
those regressions remain unchanged; it is not a test of a repair active in those cells.
The review and its independence limitations are preserved in `.aris/traces/result-to-claim/2026-11-01_run01/002-fallback-diagnostic.*`.

The protocol was committed as `98950d5`; this results note closes that stage. The raw
artifact manifest retains the pre-run protocol hash, before any results were added.


## Completed development diagnostic

40 paired development seeds [181000,181040), no new validation. Gap is measured on actual requested rounds.

| cell | method | cost/round | false promotion [Wilson 95%] | minimum observed query gap | paired cost minus DSS [95% CI] |
|---|---|---|---|---|---|
| f3_rho0.8_on0.3_L0.6_strong_harmful_d10_b0.25_s0.1_NULL | dss | 0.53696 | 11/40 [0.161,0.428] | 3 | +0.00000 [+0.00000,+0.00000] |
| f3_rho0.8_on0.3_L0.6_strong_harmful_d10_b0.25_s0.1_NULL | no_delay_switch | 0.53718 | 3/40 [0.026,0.199] | 4 | +0.00023 [-0.00281,+0.00326] |
| f3_rho0.8_on0.3_L0.6_strong_harmful_d10_b0.25_s0.1_NULL | fallback_gap4_diagnostic | 0.53827 | 12/40 [0.181,0.454] | 4 | +0.00131 [-0.00153,+0.00416] |
| f3_rho0.8_on0.3_L0.6_strong_harmful_d10_b0.25_s0.1_NULL | episode_front | 0.53897 | 15/40 [0.242,0.530] | 3 | +0.00202 [-0.00113,+0.00517] |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d10_b0.5_s0.1_NULL | dss | 0.55242 | 9/40 [0.123,0.375] | 1 | +0.00000 [+0.00000,+0.00000] |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d10_b0.5_s0.1_NULL | no_delay_switch | 0.54963 | 0/40 [0.000,0.088] | 4 | -0.00279 [-0.00362,-0.00197] |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d10_b0.5_s0.1_NULL | fallback_gap4_diagnostic | 0.55035 | 0/40 [0.000,0.088] | 4 | -0.00207 [-0.00288,-0.00126] |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d10_b0.5_s0.1_NULL | episode_front | 0.55051 | 12/40 [0.181,0.454] | 1 | -0.00191 [-0.00533,+0.00151] |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | dss | 0.39931 | 0/40 [0.000,0.088] | 19 | +0.00000 [+0.00000,+0.00000] |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | no_delay_switch | 0.42124 | 0/40 [0.000,0.088] | 4 | +0.02194 [+0.01238,+0.03149] |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | fallback_gap4_diagnostic | 0.39931 | 0/40 [0.000,0.088] | 19 | +0.00000 [+0.00000,+0.00000] |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | episode_front | 0.38634 | 0/40 [0.000,0.088] | 19 | -0.01297 [-0.01772,-0.00822] |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1 | dss | 0.38765 | 0/40 [0.000,0.088] | 4 | +0.00000 [+0.00000,+0.00000] |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1 | no_delay_switch | 0.38765 | 0/40 [0.000,0.088] | 4 | +0.00000 [+0.00000,+0.00000] |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1 | fallback_gap4_diagnostic | 0.38765 | 0/40 [0.000,0.088] | 4 | +0.00000 [+0.00000,+0.00000] |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1 | episode_front | 0.33844 | 0/40 [0.000,0.088] | 9 | -0.04920 [-0.07852,-0.01989] |

## Raw artifact provenance

- `manifest.json` SHA256 `ae30d68b6c3d18cd1abec2066d6459e20b1bf06640efa2f3c8fad7546824711f`.
- `records.json` SHA256 `b14ecb83e4cc86fcc35c2338a956ccb24ea0be49d891c91ad2f3ff6e5cf717af`.
- `summary.md` SHA256 `01410b80a9a3187a601212acf39b757117e3567c5744c762e9c824c206521007`.

Mechanical verification: 640 records, exact registered seed range per method/cell, and
minimum gap >=4 for the diagnostic variant. This is not an independent integrity audit.
