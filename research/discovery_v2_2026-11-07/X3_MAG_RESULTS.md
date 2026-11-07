# X3 results — margin-aligned guidance (MAG)

Protocol: `X3_MAG_REGISTRATION.md` (committed 86ea0af2 before running). Runner `scripts/x3_margin_aligned_guidance.py`,
output `outputs/x3_mag.json` (2000 paths per cell, fresh seeds 700001–700042, paired bootstrap over paths, 2000 resamples).
Gas arm `scripts/x3_gas_in_sample.py` → `outputs/x3_gas_in_sample.json`. **Evidence class: EXPLORATORY.**

## Registered hypotheses
| hypothesis | result |
|---|---|
| H-MAG-1: MAG ≥ H2c in every harmful world, and ≥ C1 in aligned worlds | **FAILED (first half)**: MAG ≥ H2c in 13/30 harmful cells; paired MAG − H2c is −0.0030 to −0.0095 (CI excludes 0) in 9 of the 20 cells with n_cal ≥ 2000. **Passed (second half)**: MAG > C1 in every aligned cell with n_cal ≥ 2000, e.g. +0.1190 [+0.1040, +0.1340] (q 0.2, n_cal 10 000, aligned_strong) and +0.0680 [+0.0555, +0.0800] (q 0.1). |
| H-MAG-2: MAG's loss to C1 in masked/opposed ≤ H2c's | **Passed, trivially**: both lose by ≤ 0.011; MAG − H2c is between −0.0055 and 0 there. |
| H-MAG-3: pre-onset alarms ≤ α_T | **Passed**: maximum over every arm and cell = 0.0035. |

At n_cal = 500 every arm has power ≤ 0.012: the estimated nominal bound swallows the harm (consistent with the repository's
NOMINAL_RISK_UNCERTAINTY finding).

## Gas stream B (IN-SAMPLE; gas motivated the hypothesis — not evidence for MAG)
Median alarm index (5 / 10 / 20 % labels): C1 3968 / 3899 / 3861; C2 3915 / 3870 / 3842; H2c 4166 / 4121 / 4098; **MAG 3947 / 3889 / 3857**.
MAG removes the H2c reversal and lands between C1 and C2.

## Reading
MAG is a *do-no-harm* repair, not an improvement: in synthetic worlds it costs H2c ≈ 0.003–0.01 power and keeps most of
H2c's gain over cost-only Kelly when the guide co-shifts; on the motivating real stream it avoids H2c's large delay. My earlier
"margin asymmetry" diagnosis was incomplete: in the synthetic worlds the guide only moves at the cost onset, so the margin
rarely matters; on gas the guide drifts *before* cost harm exceeds its margin, and MAG's margin happens to absorb that drift.
**Candidate status: E (inconclusive)** — novelty is minimal (a centring choice within predictable betting), and the only
evidence it helps comes from in-sample data. Smallest resolving experiment: a frozen run on an unexposed chronological stream
where a guide drifts before economic harm (registered target: NYC TLC), comparing MAG, H2c, C1, C2.
