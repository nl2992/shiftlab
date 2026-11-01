# Confirmation results, G4 (single run of the frozen protocol; `outputs/hg_v2/g4_confirmation.csv`)

984 of 1000 seeds reach the harmful regime. Power over those seeds; false alarm (FA) = alarm before the first harmful step over all seeds; null = 400 seeds that never leave the source regime.

| labels | arm | power | FA | null FA | harm before alarm |
|---|---|---|---|---|---|
| 10% | **F1 H2c (cost null)** | .642 | .007 | .005 | 178.2 |
| 10% | **F2 gated ONS hard200** | .813 | .015 | .015 | 118.0 |
| 10% | **F3 gated ONS multi** | .796 | .009 | .010 | 126.4 |
| 10% | HG_unifcap | .809 | .011 | .008 | 128.9 |
| 10% | ONS | .825 | .027 | .025 | 102.8 |
| 10% | parent (pprm_tight) | .744 | .016 | .010 | 142.3 |
| 10% | cost parent | .374 | .009 | .002 | 247.2 |
| 10% | cost + discounted Kelly | .484 | .008 | .008 | 225.3 |
| 10% | discounting only | .827 | .021 | .015 | 114.6 |
| 20% | F1 | .812 | .011 | .002 | 119.3 |
| 20% | F2 | .878 | .039 | .020 | 73.4 |
| 20% | F3 | .887 | .027 | .018 | 76.6 |
| 20% | HG_unifcap | .900 | .026 | .012 | 78.7 |
| 20% | ONS | .867 | .059 | .025 | 64.6 |
| 20% | parent | .857 | .030 | .008 | 92.9 |
| 20% | cost parent | .636 | .010 | .012 | 183.5 |
| 20% | cost + discounted Kelly | .732 | .012 | .020 | 155.9 |
| 20% | discounting only | .897 | .040 | .015 | 70.7 |

**Frozen hypotheses**
| hypothesis | 10% labels | 20% labels | verdict |
|---|---|---|---|
| C1: F1 − cost parent ≥ +0.10, CI lower > 0 | +.268 [lower .240] | +.176 [lower .151] | **PASS** |
| C2: F2 power ≥ ONS − .03 and FA ≤ ONS FA | −.012 power, −.012 FA | +.011, −.020 | **PASS** |
| C2b: F2 − HG_unifcap ≥ +0.03 | +.004 [lower −.008] | −.022 [lower −.038] | **FAIL** |
| C3: F3 satisfies C2 | −.029, −.018 | +.020, −.032 | **PASS** |
| C3b: F3 − HG_unifcap ≥ +0.03 | −.013 | −.013 | **FAIL** |
| C4: null FA ≤ .07 for F1–F3 | ≤ .015 | ≤ .020 | **PASS** |

**Reading.**
1. H2c is the clearest result: on a new generator, a cost-null monitor with Brier-guided bets improves the strongest cost-null comparator by +0.27 / +0.18 power at false alarm ≤ .011, with a proved guarantee for the cost null (fixed known delay). It does not match Brier-evidence methods on raw power (.642 vs .81 at 10% labels), but those controls are for a different null.
2. Gated ONS ties ONS on power (within 0.03) while having lower false alarms, **but does not beat HG_unifcap**: C2b and C3b fail. On G4, HG_unifcap, discounting-only and gated ONS are all within ≈ 0.03 of each other. The development-pool advantage of gated ONS over HG did not replicate.
3. G4's benign regime produces almost no false alarms for any method (all FA ≤ .059), so the study cannot discriminate benign-shift robustness; the hoped-for niche (decision-aware gate avoiding alarms on benign shifts) remains unproven.
Limits: one new family (G4), one transition matrix, binary-label surrogate for returns, fixed delay 5, no transaction costs; G5/G6 confirmations and real data not run. No hyperparameters were changed after seeing results.
