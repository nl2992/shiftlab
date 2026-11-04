# Phase 7 cross-family combinations (lead)

Code: `scripts/sota_sprint/fam_x.py`. 20 dev seeds (base 2026110501), 8 regimes, run 2026-11-03 after the
24-candidate screen. Analysis: [combo_screen.md](combo_screen.md) / `combo_screen.json`.
Raw: `outputs/sota_sprint/X/combo_screen`.

| combination | built from | result vs parent (95% CI) | H4 advance? |
|---|---|---|---|
| X_A5B5 | A5b + B1 reserve .15 + rollback (A5+B5) | F0_better +10.1 [+1.3,+18.8]; no regime below 0 | no |
| X_A6B5 | A6b + reserve .15 (A6+B5) | F0_better +9.2 [-0.1,+18.4]; none below 0 | no |
| X_A5C | A5b + no labels after a discard verdict (A5+C label saving) | F1_late_800 -1.8 [-3.4,-0.1]; otherwise identical | **yes** |
| X_D4A1 | D1 gate + A1b evidence + rollback + reserve .10 (D4+A1) | F0_better +12.4 [+7.1,+17.6], bursty +31.8 | no |
| X_D6A1:mp / :cams | shared deploy gate with A1b evidence on Model Picker / CAMS (D6+A1) | mp: worse than D1 on 4 alternatives; cams: ties A5b (none below 0) | no |

All combinations held 0/20 promotions on F0_null, F5_dep_null_r8 and F5_dep_null_r95.

Not built:
- **A2+C3.** C3's calibration selected no split (f=1), so this is A2.
- **B5+C5 and B6+A1.** The B line (RMM host) fails the rho=.8 null, and C5 did not replicate on held-out seeds.
- **D6+C2.** C2's gain did not replicate, and it loses at B=100.
- **A6+B5+C5.** Reduced to X_A6B5, since C5 adds nothing to C2.

The reserve consistently costs 7-10 on stationary alternatives (it starves front-loaded certification under the binding budget), the same finding as B1 and D4.
