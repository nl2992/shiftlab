# R1 results: payback certificates on real c4 streams

Tier: **exploratory real-data evidence** (all streams previously used; not a fresh confirmation).
Protocol: `04_EXPERIMENT_PROTOCOL_R1.md` @0e41146c. Code: `src/shiftlab/paper3/payback/real.py`,
`scripts/paper3/payback/run_real.py`, `scripts/paper3/payback/analyze_real.py`; test
`tests/paper3/payback/test_real.py` (4 pass). Outputs: `outputs/paper3/payback/real_r1/`
(`per_episode.csv`, `per_stream.csv`, `summary.json`, `ep_h{50,100}.csv`). Ledger: `ledger/payback.jsonl`
(two `R1_real_run` records, git 0e41146c+dirty).

Commands (PYTHONPATH=src, OPENBLAS_NUM_THREADS=1):
`run_real.py --data ../shift-research-starter/data/c4_sealed --h {100,50} --alpha 0.1 --cq 0 --workers 22 --out outputs/paper3/payback/real_r1`
then `analyze_real.py`. Run time 166 s (h=100) + 185 s (h=50) on 22 workers. Bootstrap seed 20261110.

## Decision: **R1-INCONCLUSIVE**
Rule: SUPPORTED needs CI lower bound > 0 for B2-B0w or B2-B0b at h=100; REVERSED needs CI upper < 0 for all three.
B2-B0a and B2-B0w have upper bounds < 0, but B2-B0b's CI straddles 0, so neither condition holds.
Per the registered consequence: no anchor; fresh data are required before any decision.

## Primary contrasts (h=100, c_q=0; mean realised net payback per episode, B2 minus B0x; 27 streams, 2,169 episodes (PI recount from per_episode.csv))
| contrast | mean | 95% CI | p (boot) | p Holm |
|---|---|---|---|---|
| B2 - B0a | -1.70 | [-3.51, -0.32] | .0006 | .0018 |
| B2 - B0w | -2.74 | [-5.17, -0.81] | .0010 | .0020 |
| B2 - B0b | -1.16 | [-3.75, +1.02] | .359 | .359 |

Mean net per episode by certificate (stream-equal weights): B0a 1.73, B0w 2.77, B0b 1.19, B1 0.027, B2 0.029.

## Secondaries
Contrasts B2 - B0x, mean [95% CI]:
| setting | B0a | B0w | B0b |
|---|---|---|---|
| h=50, c_q=0 | -0.68 [-1.42,-0.11] | -0.95 [-1.93,-0.13] | +0.54 [-0.76,+1.62] |
| h=100, c_q=.05 | -1.74 [-3.60,-0.31] | -3.26 [-5.73,-1.20] | -2.24 [-4.90,+0.01] |
| h=50, c_q=.05 | -0.71 [-1.49,-0.13] | -1.37 [-2.54,-0.43] | -0.53 [-1.85,+0.57] |

With c_q=.05 every certificate is net negative (mean about -4 to -7.5 per episode) because ~150 labels cost 7.5 and few
episodes pay back; B2 and B1 almost always certify nothing so they pay the label bill and earn nothing.

Certification behaviour (h=100; stream-mean rate / wrong-sign fraction among certs, pooled / mean delay, pooled / mean labels per episode):
| cert | cert rate | n certified | wrong-sign (pooled; stream-mean) | delay | labels |
|---|---|---|---|---|---|
| B0a | .077 | 179 | .061; .354 | 161 | 149 |
| B0w | .381 | 809 | .342; .534 | 134 | 140 |
| B0b | .843 | 1822 | .617; .627 | 138 | 128 |
| B1 | .0005 | 1 | 0 | 214 | 150 |
| B2 | .0008 | 2 | .5 (1 of 2) | 155 | 150 |

h=50: B0a .062/.048, B0w .282/.376, B0b .805/.719 (cert rate / pooled wrong-sign), B1 and B2 again 1 and 2 certifications.
Wrong-sign = realised hold sum Z - k <= 0. Wrong-sign here is a realised-sample event, not a statement about the unobserved mean; B0b
certifies in 84% of episodes and is wrong 62% of the time, yet its mean net is positive because a minority of large-gain streams
(dc_311, sf_311, dallas_animal_shelter, boston_311, nola_311) dominate.

## Per-stream table (h=100, c_q=0: mean net per episode; certification rate)
| stream | eps | B0a | B0w | B0b | B1 | B2 | rate B0a | B0w | B0b | B2 |
|---|---|---|---|---|---|---|---|---|---|---|
| austin_311 | 100 | 0.10 | 0.26 | -0.98 | 0.00 | 0.00 | 0.02 | 0.27 | 0.83 | 0.00 |
| austin_animal | 43 | 0.00 | -1.09 | -1.63 | 0.00 | 0.00 | 0.00 | 0.35 | 0.86 | 0.00 |
| baltimore_311 | 83 | -0.02 | 1.01 | 0.42 | 0.00 | 0.00 | 0.01 | 0.47 | 0.88 | 0.00 |
| boston_311 | 42 | 3.36 | 8.31 | 7.76 | 0.00 | 0.00 | 0.19 | 0.67 | 0.93 | 0.00 |
| bts_ontime | 100 | 0.00 | 0.71 | -1.26 | 0.00 | 0.00 | 0.00 | 0.19 | 0.61 | 0.00 |
| chicago_311 | 100 | 0.00 | -0.29 | -1.97 | 0.00 | 0.00 | 0.00 | 0.20 | 0.88 | 0.00 |
| chicago_traffic_crashes | 54 | 0.00 | -0.02 | -2.39 | 0.00 | 0.00 | 0.00 | 0.06 | 0.78 | 0.00 |
| cincinnati_311 | 67 | 0.00 | 3.22 | 1.45 | 0.00 | 0.00 | 0.03 | 0.58 | 0.84 | 0.00 |
| dallas_311 | 100 | 0.52 | 2.96 | 1.41 | 0.00 | 0.00 | 0.05 | 0.54 | 0.93 | 0.00 |
| dallas_animal_shelter | 76 | 5.70 | 10.92 | 11.34 | 0.00 | 0.00 | 0.34 | 0.93 | 0.95 | 0.00 |
| dc_311 | 100 | 16.87 | 20.77 | 20.28 | 0.00 | 0.00 | 0.69 | 0.98 | 0.94 | 0.00 |
| denver_311 | 100 | 0.00 | -0.11 | -1.87 | 0.00 | 0.00 | 0.00 | 0.15 | 0.79 | 0.00 |
| kc_311 | 80 | 2.45 | 1.71 | -4.97 | 0.72 | 0.82 | 0.05 | 0.30 | 0.89 | 0.01 |
| la_crime | 100 | 0.00 | -0.07 | -1.76 | 0.00 | 0.00 | 0.00 | 0.05 | 0.69 | 0.00 |
| louisville_311 | 85 | 0.00 | -0.29 | -2.25 | 0.00 | 0.00 | 0.00 | 0.35 | 0.82 | 0.00 |
| miamidade_311 | 100 | 0.00 | -0.68 | -5.73 | 0.00 | 0.00 | 0.00 | 0.11 | 0.80 | 0.00 |
| minneapolis_311 | 53 | 0.00 | -0.38 | -4.30 | 0.00 | 0.00 | 0.00 | 0.11 | 0.81 | 0.00 |
| montgomery_traffic | 49 | 0.00 | -0.41 | -2.86 | 0.00 | 0.00 | 0.00 | 0.12 | 0.88 | 0.00 |
| nola_311 | 61 | 1.31 | 8.43 | 8.36 | 0.00 | 0.00 | 0.15 | 0.92 | 0.97 | 0.00 |
| nyc_collisions | 88 | 0.00 | -0.17 | -2.22 | 0.00 | 0.00 | 0.00 | 0.09 | 0.82 | 0.00 |
| oakland_311 | 55 | 0.00 | -0.22 | -0.45 | 0.00 | 0.00 | 0.00 | 0.25 | 0.75 | 0.00 |
| philly_311 | 100 | 0.00 | -0.22 | -0.95 | 0.00 | 0.00 | 0.00 | 0.18 | 0.85 | 0.00 |
| pittsburgh_311 | 48 | 1.12 | 1.02 | 1.33 | 0.00 | 0.00 | 0.04 | 0.67 | 0.83 | 0.00 |
| sacramento_311 | 100 | -0.09 | -0.10 | -0.80 | 0.00 | -0.05 | 0.02 | 0.23 | 0.90 | 0.01 |
| sandiego_311 | 100 | -0.07 | 0.66 | -1.28 | 0.00 | 0.00 | 0.01 | 0.43 | 0.86 | 0.00 |
| sf_311 | 100 | 15.39 | 19.04 | 18.77 | 0.00 | 0.00 | 0.48 | 0.91 | 0.91 | 0.00 |
| sf_building_permits | 85 | 0.00 | -0.32 | -1.45 | 0.00 | 0.00 | 0.00 | 0.16 | 0.76 | 0.00 |

Reading (descriptive): B0 gains come from five streams with persistent challenger advantage; in about 15 streams B0w/B0b
are net negative. B2/B1 certify on essentially nothing: with binary losses (Z in {-1,0,1}, mean gap typically <= .1), the
declared envelope (v=.002, d=100) plus B=150 labels leaves no room above the k/h hurdle. The test therefore compares
"valid but almost never switches" against "invalid but sometimes right"; it does not show B2 buying anything on real data.

## Excluded streams
None (rule: fewer than 6 episodes; smallest stream has 42). Truncated holds: 0 (every certification occurred at t<=~1900 with
h<=100 rounds available; episodes are T=2000 rounds).

## Interpretation decisions
1. Episodes: every row of `l0`/`l1` (2,000 rounds each) is one episode, all rows used (not a subset); T=2000, Z = l0 - l1 in {-1,0,1}.
2. Label delay d = the stream's recorded `delay` = 100 for all streams (pilot1 used d=5); labels for round s arrive at s+100.
3. Pilot1 parameters unchanged: B=150, k=3, alpha=.1, v=.002, Envelope(v) (no jumps), n_plan=plan_batch_size(env, alpha/2, B), request-time booking, single switch then hold, per-batch query schedule as in `sim.run_one`.
4. Driver: copy of `sim.run_one` logic in `real.run_episode` (single hold horizon h; certificates untouched). Difference from `run_one`: `run_one` forbids certifying at t > T-h+1; the protocol says to truncate the hold instead, so certification is allowed at every t<=T and the hold is truncated. No truncation actually occurred.
5. Uncertified episode scores -c_q*labels (labels = requests made over the whole episode); certified episodes book labels requested up to the certification round.
6. Certification does not depend on c_q, so one run per h; c_q=0 and .05 nets are computed from stored gross sums and label counts.
7. Per-stream value = mean over that stream's episodes; contrast bootstrap resamples the 27 streams with replacement (10,000), percentile 95% CI, equal weights. p-values are two-sided bootstrap ((count+1)/(NB+1)); Holm on the three h=100, c_q=0 contrasts.
8. Wrong-sign fraction: realised gross hold sum - k <= 0 among certified episodes, reported both pooled and as a mean over streams that have certifications (streams with no certs are skipped in the latter).
9. "Certificates never receive future losses" is enforced by the driver (only (s, z[s], s+d) is passed) and tested with a spy certificate.

## Limitations
Exploratory; all streams previously exposed. Losses are 0/1, so the sub-Gaussian-1 scale used by B2 is conservative for the observed
Z. The d=100 delay with T=2000 is far from the pilot regime (d=5, T=400). B0 comparators are in-house adapters (B0b not source-faithful).
