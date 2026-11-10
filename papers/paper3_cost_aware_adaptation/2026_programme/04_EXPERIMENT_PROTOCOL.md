# Paper 3 confirmation registration v1 (locked before any confirmation seed is opened)

Registered 2026-11-10 by the PI session. All methods and configurations below are frozen at the
commit that adds this file. Nothing after this commit may change a method, configuration, metric,
threshold or seed range for these hypotheses. Any later change defines a new exploratory
hypothesis that needs new independent data.

## Why these hypotheses
Development (commits dfda60a6, f8f5d470, d3f8a4de, 8d62545d, f3525867) produced no method with
an attributable gain. The defensible contribution is a set of limits/benchmark findings. These
hypotheses test whether those findings replicate on unopened seeds. They are confirmatory for the
benchmark claims only; no method-superiority claim is registered.

## Seeds (unopened before this commit)
Block `confirmation` = [5303000000, 5303999999] in `configs/paper3/seed_registry_v1.json`.
- H1: `seeds_for('confirmation', n)` offsets 0-99 (100 seeds per regime, all 24 regimes).
- H2: base 5303100000, N = 1000 streams per class.
- H3: atlas stream seed SeedSequence[5303200000, seed, cell, null], seeds 0-59, same 32 Sobol
  cells as `C_ATLAS_PROTOCOL.md`.
- H4: base 5303300000, R = 40000.
- H5: sealed real group `civic_records_sealed` (sha256 f37dc40f..., see 03D) opened once.

## Hypotheses, frozen objects and decision rules
**H1 (A: joint planning does not beat tuned Wald+cutoff).** Frozen configs: tuned A0 and tuned
`wald_cut` from `outputs/paper3/joint/tuning/*.json` (as used for `results/joint/dev_summary.json`),
T = 300, all 24 regimes, equal regime weights. Statistic: pooled ΔJ = J(A0) − J(wald_cut),
seed-cluster bootstrap 95% CI (10,000 resamples). SUPPORTED if the CI lower bound > −1% of pooled
J(wald_cut) (no meaningful improvement by the best joint planner). Secondary (descriptive):
the same for A1, A3, A5; A0 label count vs wald_cut.

**H2 (B: repeated-look payback hurdles are invalid; B2 is valid).** Frozen certificates
B0a, B0w, B0b, B1, B1n, B2 with the parameters of pilot `pilot1` in `03B_...md`; flat-null class,
α = 0.1. SUPPORTED if the Wilson 95% lower bound of the wrong-sign certification rate exceeds 0.1
for B0w and B0b, and the Wilson 95% upper bound for B2 is ≤ 0.1.

**H3 (C: alarm ranking and cost ranking disagree).** Frozen 12-method atlas set and grid from
`C_ATLAS_PROTOCOL.md`. Statistic: inversion frequency among EDD/FA-dominance pairs and mean
per-cell Kendall τ(EDD rank, J rank), seed-cluster bootstrap. SUPPORTED if the inversion-frequency
CI lower bound > 0.25 and the τ CI upper bound < 0. Secondary: Spearman(dwell, τ) > 0.
Known limitation registered in advance: `never_switch` was cheapest in every dev cell, which may
inflate inversions; the real-stream analysis did not reproduce them.

**H4 (E: prequential certification with same-label retraining is valid).** Frozen gates from
`03E_...md` (prequential m=5 and m=40), boundary null, α = 0.05. SUPPORTED if both Wilson 95%
upper bounds ≤ 0.05.

**H5 (D: no attributable transfer gain on unseen real families).** Frozen D2-MLP + OOD fallback
and global-fixed configuration from `D_RESULTS.md`, evaluated on the four sealed streams.
Statistic: per-stream ΔJ (MLP+fallback − global fixed) and its mean. SUPPORTED (no gain) if the mean
ΔJ ≥ −1% of J(global fixed). With four streams this is descriptive; no CI-based claim.

## Multiplicity and reporting
Five registered hypotheses, each with its own decision rule; report all outcomes, including
any that fail. No hypothesis here is a superiority claim for a new method. Effects are graded
with the user's scale (substantial/meaningful/small/negligible).
