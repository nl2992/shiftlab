# Calibrated E-SR late-improvement screen

**Status:** development screen on fresh synthetic streams; not confirmation. The frozen primary gate did not pass, so no real or locked dataset was opened.

## Primary cell: F1_late_800

Candidate is the unchanged `E_srrSR:gated_deployment` implementation at the previously selected alpha 0.0005. It cost 365.60 mean net units (351.40 predictive loss + 10.00 label cost + 4.20 switching cost), promoted in 84/100 streams, and promoted at mean event 1,430 among those promotions. Candidate minus reference paired net-cost differences are over 100 shared streams; negative favors candidate.

| Reference at alpha 0.05 | Mean net cost | Candidate minus reference [95% paired CI] |
|---|---:|---:|
| Never-switch | 388.26 | −22.66 [−26.97, −18.35] |
| Gated adaptive range | 397.84 | −32.24 [−36.54, −27.94] |
| Gated adaptive range + front | 396.94 | −31.34 [−35.69, −26.98] |
| DISCERN-style adapter | 398.24 | −32.64 [−36.95, −28.34] |
| SMCS adapter | 398.25 | −32.65 [−36.95, −28.34] |
| E_swcert | 382.65 | −17.06 [−21.81, −12.30] |
| E_rb:Gated adaptive range | 371.80 | −6.20 [−10.96, −1.44] |
| Matched-host RMM | 371.80 | −6.20 [−10.96, −1.44] |
| PFA-SR:Gated deployment | 389.78 | −24.18 [−28.48, −19.88] |
| PFA-SR:Gated adaptive range | 389.23 | −23.63 [−27.86, −19.40] |
| Qiu-inspired delayed movement port | 344.59 | +21.01 [+16.64, +25.39] |
| Gong-inspired paid-observation port | 351.21 | +14.39 [+8.89, +19.89] |

The candidate improves on the registered certificate and PFA-SR panels, including the paired
RMM/E_rb comparison, but misses the frozen requirement against both Qiu/Gong-inspired ports. Those
ports are explicitly not author-native reproductions; in this same screen they promoted on 100/100
and 99/100 `F0_null` streams, respectively, so their cost advantage is not an equal-safety result.
The candidate's independent 100-stream null screen had 2 promotions; its one-sided 95% Wilson
upper bound is 5.86%, just above the frozen 5% gate. A prior separate 1,000-stream null evaluation
at the same alpha was 20/1,000 (upper 2.87%). Preserve both rather than pooling after viewing this
screen.

## Other registered cells

| Regime | Candidate mean cost | Selected paired contrast |
|---|---:|---:|
| F1_late_1200 | 375.19 | −12.13 [−15.45, −8.81] vs PFA-SR:Gated adaptive range; +21.34 [+17.33, +25.35] vs Qiu-inspired port |
| F0_better | 369.01 | +5.44 [+0.15, +10.73] vs PFA-SR:Gated adaptive range; +37.81 [+33.69, +41.94] vs Gong-inspired port |
| F3_reversal_800 | 387.79 | +45.07 [+40.13, +50.01] vs never-switch |

The candidate is beneficial only in the late-improvement target against certificate-style baselines;
it is materially harmful in the registered reversal adverse regime. The apparent narrow advantage
is an application of existing E-SR prior art and does not establish a new algorithm. The failed
development gate blocks confirmation and real-data access under this protocol.

## Reproduction and decision

Run `uv run python research/scoped_method/analyze_srr_late_improvement.py` to regenerate
`evaluation_summary.json`. Exact run arguments, source hashes and runtimes are in the paired
`candidate/manifest.json` and `references/manifest.json`; raw rows are in the adjacent
`records.jsonl` files. Hashes are in `EVALUATION_HASHES.txt`.

**Decision:** candidate fails the frozen primary gate against Qiu/Gong-inspired comparators and
the 100-stream null precision gate. No confirmation or real-data validation follows from this
screen. This does not erase the strong scoped contrast against published certificate adapters, but
it is insufficient for a new-method or generalizable-transfer claim.
