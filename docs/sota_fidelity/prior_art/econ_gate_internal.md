# Economic gating: internal sweep of earlier repo work (2026-11-07)

This is a read-only sweep of the repo's earlier switching work. Paths and line numbers are the ones
the sweep reported; the lead spot-checked the atlas and EconomicReplacement entries. Every earlier
attempt was closed or failed its gate.

| # | Mechanism | Where | Outcome |
|---|---|---|---|
| 1 | P4 persistence-aware certified switch: LCB × min(hazard mean, T−1−t) > c_s, hazard 1/150 | `docs/promising_directions/protocols/B1-certified-switching.md:16,51`; results `08_SYNTHETIC_DEVELOPMENT.md:54` | W3 reversal +0.24–0.82% (bar 10%); W1 persistent −9.5 to −23.9%. "NOT SUPPORTED … Stop" (`12_NOVELTY_DECISION.md:12`) |
| 2 | B3+ break-even promotion: LCB × (T−t) > c_s + expected label spend | `docs/promising_directions/B3_PLUS_METHOD.md:78-125`, `B3_PLUS_NOVELTY.md:15-18,66,90-91` | Synthetic at c_s=20: W3 wins (−7.2), W1 losses (+24.9). Real: loses on spam +23.8, rialto +9.0, weather +17.6. Its novelty note: "Any claim that 'break-even promotion' is new would be false" |
| 3 | EconomicStop: gated CS with bar c_s/(T−t) | `scripts/promising_directions/sota/competitors/economic_stop.py:8-69`; `docs/promising_directions/sota/SOTA_REAL_DATA_RESULTS.md:10-13,53-58` | +1.85 [0.99, 3.39] rialto, +9.59 [5.32, 14.68] ldpa vs gated. Registered STOP. Diagnosis: saving capped at c_s per avoided switch, waiting cost unbounded per round (`SOTA_FAILURE_DIAGNOSIS.md:16-26`) |
| 4 | Uncertified economic switchers (Atlas v2): `gong_zhang_paid_obs` (switch/rollback when remaining gain > c_s), `economic_replacement` (δ̂(T−t) > c_s, promote only) | `scripts/failure_atlas_v2_flq/r6_policies.py:67-91`; `scripts/promising_directions/sota/competitors/controls.py:185-245` | F3_reversal_800: never 344.4, gong_zhang 349.1, economic_replacement 411.6. gong_zhang beats never on V_reversal_1000 (349.7 vs 360.2) but promotes on 99% of V_null runs: invalid |
| 5 | Sprint-2 R5: (T−t)·d̂·(2p̂−1) − c_s − κ·penalty > 0 | `scripts/sota_sprint/fam_r.py:52-58` | No anytime guarantee; promoted on 15/100 F0-null seeds (`docs/sprint2/family_r/results.md:64`) |
| 6 | Sprint-2 H family: shadow price g_eff(T−t−delay) − c_s, deadline c_s/g_hi | `scripts/sota_sprint/fam_h.py:21-28` | Lost to D2 and gated_adaptive_range (`docs/sprint2/family_h/README.md:37-41`); not run as a rollback gate on reversal |
| 7 | (T−t)·margin ≥ c_s filter before promotion | `src/shiftlab/sota_search/paired_control.py:200-202`, `paced_epochs.py:105`, `paired_edetectors.py:65` | No reversal result found |
| 8 | Atlas v1 R_law: posterior expected remaining benefit > s + margin | `docs/failure_atlas_v1_protocol.md:89-100` | Never promoted in 57 transient cells (`failure_atlas_v1_ledger.md:114-119`) |

External prior art the repo already recorded as closing parts of the idea: Bayraktar–Ludkovski
(HMM optimal switching with paid reversible switches;
`switching_hidden_markov_optimal_switching_prior_audit_v1.md`), Chick–Forster–Pertile and
Chick–Frazier / Hampson–Jennison (economic adoption and stopping), Ferrari–Zhao–Scaglione
(remaining-horizon value of information), Bayraktar–Yao (robust optimal stopping), Digalakis
"Challenger" and LCB(gain − amortised c_s) compositions (`PRIOR_ART_AND_NOVELTY_MATRIX.md:316-326`).

Untested before 2026-11-07: a horizon- or cost-aware gate wrapped around a valid detector on the
four sprint reversal regimes. That gap motivates the bound in
[../econ_gate_bound_protocol.md](../econ_gate_bound_protocol.md).

Atlas context (`docs/failure_atlas_v2_results/discovery_tables.md:13-14`): on F3_reversal_800
never switching is the cheapest of all 15 policies, certified or not; on F3_reversal_1200 the best
policy (an uncertified online selector) beats never switching by 10.6.
