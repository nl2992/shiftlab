# 05 Confirmation results (registration 04_EXPERIMENT_PROTOCOL.md, commit 2190f95f)

Run 2026-11-10 at HEAD ad5a6dab (2190f95f plus one docs-only commit; no code, config or seed change; worktree
had only the new `scripts/paper3/confirm/` drivers, ledger/confirm.jsonl and appended atlas/dualuse ledger rows).
Python: shift-research-starter .venv, PYTHONPATH=src, OPENBLAS_NUM_THREADS=1. Each seed range opened once; no crashes,
no retries, no resumes. Raw: `outputs/paper3/confirm/h1..h5/` (uncommitted), per-run records in `ledger/confirm.jsonl`.
Drivers: `scripts/paper3/confirm/h{1_joint,2_payback,3_atlas,4_dualuse,5_transfer}.py`. H1-H3 reuse the existing harness /
run_pilot / analyze_inversions code unchanged; H4 calls `scripts/paper3/dualuse/run_kill.py`; H5 lifts the sealed-loader
guard only via `open_sealed=True` inside the driver. H1/H3/H5 ran concurrently on one 24-core machine (wall clocks inflated).

## Summary
| H | registered statistic | result | decision |
|---|---|---|---|
| H1 | pooled dJ = A0 - wald_cut, lower CI bound > -1% of J(wald_cut)=68.23 (-0.682) | +1.277 [+0.923,+1.621] (+1.87% [+1.35,+2.38]) | SUPPORTED |
| H2 | Wilson lo(B0w), lo(B0b) > .1 and hi(B2) <= .1 (flat null, alpha=.1, N=1000) | B0w .635 [.605,.664]; B0b .857 [.834,.877]; B2 .001 [.0002,.0056] | SUPPORTED |
| H3 | inversion freq CI lo > .25 and tau(EDD,J) CI hi < 0 | inv .514 [.448,.541]; tau -0.174 [-0.198,-0.132] | SUPPORTED |
| H4 | both prequential Wilson hi <= .05 | m=5 .0311 [.0294,.0328]; m=40 .0305 [.0288,.0322] | SUPPORTED |
| H5 | mean dJ (MLP+OOD - global fixed) >= -1% of J(global fixed)=433.90 (-4.34) | mean -1.28 (-0.30%) | SUPPORTED (descriptive, 4 streams) |

## H1 (A): 100 seeds (5303000000-5303000099) x 24 regimes x T=300 = 14,400 paired tapes per method; 1,448 s wall
Pooled J: never 75.77, wald_cut 68.23, A0 69.50, A1 73.25, A3 72.36, A5 71.86. Bootstrap: 10,000 seed-cluster resamples,
percentile 95%. dJ vs wald_cut (positive = worse than wald_cut): A0 +1.28 [+0.92,+1.62] (+1.9%); A1 +5.02 [+4.57,+5.46]
(+7.4%); A3 +4.13 [+3.77,+4.50] (+6.1%); A5 +3.64 [+3.24,+4.03] (+5.3%). Labels: wald_cut 38.0, A0 22.5 (A1 12.9, A3 38.8,
A5 27.7); switches wald_cut 0.97, A0 0.67. A0 better than wald_cut in 9/24 regimes (stationary_null -1.2, delayed_onset -2.0,
dep_rho_0.95 -1.9, expensive_switch -1.1, ...), worse by 4-7 in informative_delay, random_delay, label_scarcity, long_persistent,
abrupt_beneficial, stationary_better. Dev result replicated (dev: A0 +0.82, +1.2%). The rule only requires no meaningful
improvement; here A0 is in fact reliably worse.

## H2 (B): N=1000 flat-null streams, SeedSequence[5303100000, 2, i], pilot1 parameters, alpha=.1; 109 s
| cert | wrong-sign rate | Wilson 95% | cert rate | labels | delay |
|---|---|---|---|---|---|
| B0a | .149 | [.128,.172] | .149 | 135 | 51 |
| B0w | .635 | [.605,.664] | .635 | 73 | 29 |
| B0b | .857 | [.834,.877] | .857 | 45 | 29 |
| B1 | .001 | [.0002,.0056] | .001 | 150 | 155 |
| B1n | .021 | [.014,.032] | .021 | 148 | 36 |
| B2 | .001 | [.0002,.0056] | .001 | 150 | 40 |
Dev pilot values (B0a .127, B0w .537, B0b .810, B2 0) replicated qualitatively; B0w/B0b exceed alpha by 6x/8x. Note B2 and B1
each had one wrong certification in 1000 (dev pilot: 0/300), still far below alpha.

## H3 (C): atlas, seed base 5303200000, seeds 0-59, 32 cells, alt + null twin, 17 methods run (12-method core set analysed); 1,596 s
Core-12 (never_switch excluded, so the registered limitation does not apply to the primary statistic), 300-rep seed-cluster
bootstrap as in C_ATLAS_PROTOCOL: inversion frequency among EDD/FA-dominance pairs .514 [.448,.541] (189/368 dominated pairs);
mean per-cell tau(EDD,J) -0.174 [-0.198,-0.132]. Secondary: Spearman(dwell fraction, tau_EDD) over 32 cells = +0.906 (p=1e-12)
(+0.830 for the composite tau), holds. Sensitivity with never_switch added: inv .571 [.508,.592], tau -0.238 [-0.256,-0.198].
Descriptive: mean tau(FA,J) = +0.195 (FA ranking agrees with cost ranking, EDD ranking does not). The registered
real-stream caveat (inversions not reproduced on c4 streams) is unaffected by this synthetic confirmation.

## H4 (E): base 5303300000, R=40,000, boundary (noise-label) null gamma=0, alpha=.05, horizon 100; 69 s
Prequential: m=5 1243/40000 = .0311 [.0294,.0328]; m=40 1219/40000 = .0305 [.0288,.0322]. Controls as in dev: resub 1.0,
peek_z .300, split .0253, holdout .0291; forward value of every promotion was 0 (noise labels).

## H5 (D): sealed group civic_records_sealed opened once, 865 s
Group sha256 recomputed = f37dc40f3bdea96f1e2e54baa212c8a2391fec1ca37f0368108bd8504c7ae460 (MATCH with 03D and seal_hash.json);
per-stream array hashes match seal_hash.json (austin_animal 7d0d948f..., dallas_animal_shelter fde54af0..., la_crime b3a717be...,
sf_building_permits ff2f7bf4...); raw-file sha256 in `outputs/paper3/confirm/h5/hash_check.json`. Training: 33 real dev streams + 30
synthetic, scope 'all', primary scenario; global fixed = config 129 (lambda .99, gamma .2, H 1100). OOD fallback did not trigger on any
stream (Mahalanobis 1.7-2.4 vs threshold 3.49), so MLP+fallback = MLP.
| stream | J global fixed | J MLP+OOD | dJ | J per-stream tuned | hindsight (unattainable) |
|---|---|---|---|---|---|
| austin_animal | 408.10 | 409.59 | +1.49 | 407.60 | 402.32 |
| dallas_animal_shelter | 605.17 | 600.93 | -4.24 | 601.42 | 592.28 |
| la_crime | 290.74 | 289.58 | -1.16 | 289.55 | 289.51 |
| sf_building_permits | 431.59 | 430.36 | -1.23 | 431.19 | 430.36 |
Mean dJ = -1.28 (-0.30% of mean J global fixed 433.90); threshold -4.34. By the registered rule H5 is SUPPORTED (no gain
>= 1%); the point estimate is a small MLP advantage (3 of 4 streams better, 0.3%), negligible grade. Mean per-stream-tuned vs
global fixed -1.46. Four streams, descriptive only, no CI claim. Disclosure from 03D (shapes/marginals of sealed files printed
before development) stands.
