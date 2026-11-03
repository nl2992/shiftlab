# Failure Atlas v2: SOTA failure atlas (discovery stage)

2026-11-03. Protocol: [failure_atlas_v2_protocol.md](failure_atlas_v2_protocol.md). Contract
T=2000, B=200, c_q=.05, c_s=5, alpha=.05. Discovery seeds 0-99 (seed base 20261103) on 20
synthetic regimes; 9 real replay streams (168 episodes x 20 replay seeds). 15 policies, 80,400
episode runs, 58 minutes on 9 CPU workers. Raw records:
`outputs/failure_atlas_v2/discovery_v2contract/records.jsonl` (git-ignored; manifest has code and
data SHA-256). Summary committed at
[discovery_summary.json](failure_atlas_v2_results/discovery_summary.json); full tables (net-cost
gap, promotion rate, expected-oracle regret, labels/switches, first-promotion time) in
[discovery_tables.md](failure_atlas_v2_results/discovery_tables.md).

Reproduce:

```bash
uv run python scripts/failure_atlas_v2/run_atlas_v2.py --regimes all --real rialto,openml_ldpa,spam,weather,uci_occupancy,airlines,bank,elec2,criteo --n-seeds 100 --real-seeds 20 --workers 9 --policies gated_deployment,discern_style,SMCS+retain-incumbent,model_picker_adapter,model_selector_causal,online_llm_picker,xu_acquisition_only,cams_adapter,variance_min_ipw,P7s_settled,CONTROL_never_switch,economic_replacement,gong_zhang_paid_obs,qiu_movement_oco,delayed_ftrl_capacity --extra-module registry_additions --out outputs/failure_atlas_v2/discovery_v2contract
```

## Fidelity of what was run

Names follow [SOTA_IMPLEMENTATION_VALIDATION.md](promising_directions/sota/SOTA_IMPLEMENTATION_VALIDATION.md).
Verified against author code (native): CAMS, Model Picker, variance minimisation, SMCS (vs R),
Model Selector. Everything in this atlas is the ADAPTER to the common contract. Starred methods
(Qiu*, Gong*, DFTRL*) were ported on 2026-11-03 from algorithm boxes only; no author code
exists, nothing is numerically verified, and the Qiu adapter in particular may be weaker than
the paper (its parameter-free step sizes are tuned for L = 1/p_min + c_s and barely move the
deployment weight). Not run: Sawade calibrated, Xu prediction-assisted, CAMS contextual (need
features absent from loss streams); The Challenger (retraining learning-curve setting).

**Known adapter weakness, recorded before the repair work:** Gated and DISCERN were run with
the shared uniform budget pacer. Front-loaded acquisition (q=1 on every disagreement until a
verdict) is a stronger reading of both papers and is carried as an additional comparator in
development and validation, so any repair must beat it.

## The matrix (net cost minus row best, discovery seeds)

| source | Gated | DISCERN | SMCS | Xu | Qiu* | P7s | MPick | MSel | OLP | CAMS | VMin | Gong* | DFTRL* | Never | best |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| F0_better | 101.0 | 103.3 | 56.5 | 51.9 | 103.3 | 52.9 | 0.0 | 0.4 | 8.7 | 5.3 | 7.1 | 4.7 | 7.5 | 93.3 | 327.5 |
| F0_null | 10.0 | 10.0 | 9.9 | 9.7 | 10.0 | 9.9 | 43.7 | 39.3 | 47.1 | 67.0 | 62.6 | 31.9 | 18.7 | 0.0 | 359.1 |
| F0_worse | 9.8 | 10.0 | 10.0 | 9.8 | 10.0 | 9.5 | 20.3 | 18.5 | 23.5 | 24.5 | 26.7 | 19.9 | 21.7 | 0.0 | 301.1 |
| F1_late_400 | 85.0 | 85.0 | 77.4 | 58.8 | 85.0 | 37.6 | 18.3 | 13.1 | 24.8 | 25.0 | 28.1 | 90.7 | 23.6 | 75.0 | 332.1 |
| F1_late_800 | 45.6 | 45.7 | 44.2 | 38.6 | 45.7 | 14.9 | 14.8 | 9.7 | 21.1 | 23.3 | 23.3 | 54.5 | 17.1 | 35.7 | 360.3 |
| F1_late_1200 | 16.1 | 16.1 | 16.1 | 15.4 | 16.1 | 0.0 | 14.6 | 15.3 | 19.1 | 23.5 | 20.8 | 28.1 | 13.1 | 6.1 | 371.9 |
| F2_transient | 15.4 | 15.4 | 23.5 | 33.3 | 15.4 | 31.8 | 19.2 | 15.4 | 22.1 | 25.1 | 32.3 | 26.5 | 8.6 | 5.4 | 367.6 |
| F3_reversal_800 | 13.9 | 10.0 | 70.5 | 62.4 | 10.0 | 57.1 | 39.4 | 42.4 | 30.7 | 50.0 | 48.1 | 62.6 | 51.5 | 0.0 | 342.2 |
| F3_reversal_1200 | 26.1 | 20.6 | 31.4 | 42.9 | 20.6 | 42.5 | 5.1 | 4.5 | 0.0 | 6.7 | 8.9 | 5.7 | 7.9 | 10.6 | 367.8 |
| F4_recurrent | 10.0 | 10.0 | 27.1 | 27.2 | 10.0 | 28.3 | 31.2 | 27.4 | 26.9 | 39.4 | 39.7 | 17.4 | 17.6 | 0.0 | 365.5 |
| F5_dep_null_r8 | 10.0 | 10.0 | 11.4 | 11.1 | 10.0 | 12.0 | 38.0 | 40.6 | 39.1 | 50.8 | 50.7 | 24.7 | 20.6 | 0.0 | 360.3 |
| F5_dep_better_r8 | 93.3 | 100.7 | 43.0 | 48.0 | 100.7 | 39.2 | 0.3 | 0.0 | 7.8 | 3.8 | 3.4 | 6.5 | 0.7 | 90.7 | 330.2 |
| F5_dep_null_r95 | 9.6 | 10.0 | 12.6 | 10.8 | 10.0 | 11.7 | 26.7 | 36.5 | 34.1 | 36.6 | 35.1 | 20.9 | 14.9 | 0.0 | 361.2 |
| F6_delay400_better | 87.8 | 88.6 | 45.8 | 62.6 | 88.6 | 65.3 | 3.8 | 3.2 | 0.0 | 3.4 | 8.1 | 3.4 | 15.0 | 78.6 | 343.9 |
| F6_delay400_late | 35.5 | 35.5 | 35.5 | 35.3 | 35.5 | 32.9 | 12.5 | 21.0 | 20.4 | 26.8 | 28.0 | 40.4 | 0.0 | 25.5 | 367.4 |
| F7_near_better | 45.3 | 45.3 | 40.3 | 38.3 | 45.3 | 40.5 | 23.3 | 10.6 | 28.5 | 17.6 | 30.1 | 15.0 | 9.5 | 35.3 | 356.9 |
| F7_near_tiny | 14.4 | 14.4 | 13.8 | 13.1 | 14.4 | 13.1 | 24.7 | 25.4 | 38.7 | 44.9 | 44.7 | 18.0 | 10.9 | 4.4 | 366.6 |
| F8_rare_better | 18.4 | 41.3 | 10.7 | 17.0 | 41.3 | 23.8 | 3.2 | 1.2 | 1.6 | 0.8 | 4.0 | 9.6 | 0.0 | 38.3 | 208.4 |
| F9_highdis_better | 131.4 | 131.4 | 105.0 | 114.1 | 131.4 | 105.9 | 24.2 | 16.7 | 35.5 | 19.0 | 30.2 | 16.6 | 31.8 | 121.4 | 559.0 |
| F9_bursty_better | 88.2 | 100.3 | 46.6 | 56.6 | 100.3 | 62.0 | 1.8 | 0.0 | 2.6 | 4.0 | 4.3 | 8.6 | 6.1 | 90.7 | 336.1 |
| rialto | 21.6 | 137.4 | 17.4 | 26.9 | 137.4 | 26.2 | 1.9 | 5.3 | 0.5 | 2.2 | 6.7 | 7.8 | 0.0 | 129.5 | 72.6 |
| openml_ldpa | 102.7 | 225.3 | 34.1 | 59.0 | 240.8 | 48.9 | 0.0 | 3.7 | 1.1 | 3.1 | 3.7 | 51.0 | 2.0 | 231.7 | 431.3 |
| spam | 179.7 | 344.1 | 41.1 | 50.8 | 591.6 | 42.9 | 0.3 | 4.9 | 0.0 | 5.9 | 14.8 | 4.9 | 2.2 | 643.9 | 205.1 |
| weather | 50.7 | 72.6 | 26.6 | 30.4 | 72.6 | 33.4 | 8.4 | 0.0 | 7.0 | 11.2 | 2.7 | 6.0 | 1.7 | 63.7 | 440.3 |
| uci_occupancy | 69.5 | 105.8 | 20.5 | 50.5 | 152.1 | 46.7 | 0.0 | 4.6 | 2.3 | 3.6 | 9.6 | 8.6 | 0.7 | 350.1 | 131.2 |
| airlines | 5.7 | 9.3 | 4.2 | 4.5 | 9.3 | 3.7 | 12.2 | 14.3 | 17.4 | 16.6 | 24.1 | 14.3 | 12.6 | 0.0 | 776.8 |
| bank | 5.1 | 5.7 | 8.5 | 8.3 | 8.8 | 8.2 | 13.3 | 6.0 | 19.7 | 15.2 | 21.3 | 7.1 | 46.1 | 0.0 | 419.4 |
| elec2 | 5.6 | 5.7 | 4.3 | 5.1 | 5.7 | 7.7 | 9.4 | 21.0 | 12.0 | 10.1 | 18.9 | 9.5 | 9.3 | 0.0 | 389.5 |
| criteo | 15.6 | 16.9 | 13.9 | 15.0 | 16.9 | 15.5 | 9.0 | 4.6 | 12.3 | 10.9 | 9.6 | 10.6 | 6.7 | 10.4 | 683.5 |

Real streams: per-episode mean over replay seeds, then mean over episodes (K = 16, 32, 1, 3, 4,
50, 8, 4, 50). spam (K=1), weather (3), elec2 (4) and uci_occupancy (4) are low-power.

False/ever promotion of the challenger (fraction of runs):

| source | Gated | DISCERN | SMCS | Xu | Qiu* | P7s | MPick | MSel | OLP | CAMS | VMin | Gong* | DFTRL* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| F0_null (p=.5) | .00 | .00 | .02 | .01 | .00 | .01 | .96 | .95 | .99 | .99 | .94 | .91 | .85 |
| F0_worse | .00 | .00 | .00 | .00 | .00 | .00 | .58 | .49 | .63 | .61 | .58 | .51 | .52 |
| F5 null rho=.8 | .00 | .00 | .10 | .09 | .00 | .13 | .96 | .97 | 1.00 | .97 | .98 | .90 | .86 |
| F5 null rho=.95 | .02 | .00 | .41 | .21 | .00 | .37 | .92 | .94 | .95 | .92 | .94 | .81 | .83 |
| F0_better | .07 | .00 | .72 | .90 | .00 | .89 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | .99 | 1.00 |
| F7_near_better | .00 | .00 | .14 | .32 | .00 | .19 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | .99 | .95 |

## Shared failures, ranked

Families: anytime-certificate (Gated/MOPE CS, DISCERN/EB-CS, Xu/active-testing betting,
P7s), e-value elimination (SMCS), online OCO (Qiu*), online selection (Model Picker, Model
Selector, OLP, CAMS, variance-min, Gong*, DFTRL*).

| # | Mechanism | Algorithms (families) | Economic size | Reproduces on real data | Repair feasibility |
|---|---|---|---|---|---|
| M1 | **Over-conservative certification**: error-controlled methods rarely or never promote a genuinely better challenger within T; evidence is cumulative and acquisition stops at the verdict, so late gains are diluted and never re-examined | Gated, DISCERN, Xu, P7s, SMCS, Qiu* (4 independent families) | mean gap to best method +65.6 on stationary synthetic alternatives, +102 on the 5 real streams with a better challenger; +36 to +85 on late improvement | yes: rialto +22, ldpa +103, spam +180, uci +70 (Gated) | high: a wrapper that changes evidence and recovery, not the base |
| M2 | **Unsafe fast selection**: online selectors promote on null/worse challengers 82-100% and thrash | MPick, MSel, OLP, CAMS, VMin, Gong*, DFTRL* (3+ families) | mean +18.2 on nulls; +20 to +67 on F0_null | yes: airlines/bank/elec2 +6 to +46 | requires adding error control, i.e. the opposite trade |
| M3 | **No rollback after reversal** | SMCS (+70), Xu (+62), P7s (+57); online selectors +31 to +63 | large but on synthetic reversals only | no real stream reverses sign | partial: rollback needs labels after the verdict |
| M4 | **Dependence inflates false promotion** | SMCS .41, P7s .37, Xu .21 at rho=.95 | safety, not cost | untested | a v1 problem; not addressed here |
| M5 | **Front-loaded budget exhaustion** | Gong* spends 200/200 labels by t=227 | +45 to +91 on late regimes | — | adapter-specific |

Two causes inside M1 were separated before choosing it (development seeds, Gated, 100 seeds;
`docs/failure_atlas_v2_development.md`): (a) inverse-propensity range under paced acquisition
(Gated 103 -> 34 with front-loaded acquisition, -> 57 with label-clock evidence on the
stationary-better stream) and (b) cumulative, stop-at-verdict evidence (front-loading leaves
late-improvement gaps at 66-67; only a restart mechanism reduces them).

**Selected target: M1 (with M3 as its rollback half).** It recurs across four independently
developed error-controlled families, is the largest real-data loss in the atlas, and is the one
failure whose repair could keep the property that makes these methods worth using: anytime
control of false promotion, which M2 methods lack (F0_null promotion .85-.99). The competitive
target is therefore the best *error-controlled* method, with the fast selectors as the cost
frontier to approach without paying their null-stream losses.
