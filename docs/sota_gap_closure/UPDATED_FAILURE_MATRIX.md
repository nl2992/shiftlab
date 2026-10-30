# Updated failure matrix (after S03-S12, Q2, Q3, G3-G6 and the stress matrix)
Built from the stored per-seed results. Severity is a judgement (5 = invalidates a headline guarantee).

| failure | methods affected | evidence | severity (1-5, judgement) | # families affected | reproducibility | fix tested | statistical-correctness note |
|---|---|---|---|---|---|---|---|
| F1 dependence-induced false alarms | all e-process monitors (pprm, HG, cost) | cluster-400: HG 0.190, pprm 0.121, cost 0.163; cluster-100: HG 0.088; GARCH null: HG 0.089, pprm 0.130 | 5 | 3 | G3-G6 stress (X03/X04/G4); 3 independent null families | tested: F2 | validity: heuristic only |
| F2 cap-floor penalty of non-uniform querying | variance/ASI, growth, mixtures with growth, pacing, balanced sampling, context variance (Q2), uniform certification (Q3) | HG 10% labels, floor frac/4: variance -0.145, growth -0.135, growth_oracle -0.082 power vs uniform; S08 balanced 0.056 vs uniform 0.143 | 4 | 7 | S04, S05, S06 v1, S08, Q2 S09a, Q3 cert_uniform | tested: F1 | valid by construction |
| F3 transient / recurrent harm | all monitors | X10 transient d=1.5/2/3, 20% labels: HG 0.34/0.62/0.86, pprm 0.17/0.31/0.59; recurrent HG 0.74 | 3 | 5 | previous phase F2 + X10/X11 + Q3 temp scenario | tested: F3 | valid |
| F4 label starvation | all labelled monitors | X12 power at 0.2/0.5/1/2% labels: HG 0.000/0.001/0.007/0.059 | 3 | 8 | previous phase F5 + X12 | none (information-limited) | - |
| F5 late-onset harm under a fixed budget | all pacing rules | S06: onset .8 power 0.0-0.125 vs 0.65 at onset .2 | 3 | 8 | S06 | none | - |
| F6 head-of-line blocking of in-order release | any prefix-release e-process | heavy-tailed delays: power drops (see FINAL results, C6 heavy) | 2 | 3 | G6 heavy | outcome-independent delay can use arrival-ordered release (valid under iid) | trade-off between validity scope and power |
| F7 proxy failure costs power | PP monitors | HG at 10% labels: blend0 0.79 -> blend1 0.67 | 2 | 2 | S03 | tested (S03): no improvement | - |
| F8 HG slower than PH under persistent harm when a blind promotion follows | HG-triggered switching | switches/seed HG 0.20 vs PH 0.30; regret +19..+26 in persistent-harm scenarios | 3 | 2 | Q3 | none | - |
| F9 certification after ranking reversal | e-process certification (all Q2 methods) | incorrect promotion after reversal up to 0.018 for CAMS-style; zero-gap FWER <= 0.023 | 2 | 8 | Q2 | windowed / forgetting evidence (no valid anytime form found) | open |
| F10 feature-space detectors cannot separate harm from benign shift | MMD, C2ST, BBSD | S12 and previous phase F1 | 4 | 4 | S12 + phase 1 | none (by design: sentinels) | - |
