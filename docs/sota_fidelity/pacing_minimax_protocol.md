# Paper 3 pacing under change-time uncertainty: minimax target and stop rule (protocol, locked before run)

**Locked:** 2026-11-07, before any run under the seed bases below. **Status:** theory-first
screen. It is a feasibility test of a Paper 3 target, not confirmatory evidence and not a method
claim. Prior art for adaptive sampling is in [prior_art/README.md](prior_art/README.md) (lever a)
and `docs/switching_sampling_rights_qcd_audit_v1.md`.

## Question

Under the reference contract, can any label-pacing rule reduce the **worst-case regret over the
change time** by a useful margin relative to uniform pacing? If not, the Paper 3 pacing target
stops as a method contribution (the stop rule set in the track B prior-art review).

## Model (self-contained, matches the paired Bernoulli contract)

- Rounds t = 0..T−1, T=2000. Disagreement with probability dis=0.2; on a disagreement the
  challenger is right with probability p_t (D_t=+1), else D_t=−1. Deploying the challenger changes
  realised loss by −D_t on disagreement rounds, 0 otherwise.
- Late change at onset ν: p_t = 0.4 before ν, 0.7 from ν (as `F1_late_800`). Per-round advantage
  after onset G = 0.08.
- Labels: only disagreement rounds are worth buying. A request at t is released at t+d. Hard cap
  B=200 requests counted at request time. c_q=0.05, c_s=5.
- Detector (fixed for all pacers): one-sided mixture Shiryaev–Roberts e-detector on the label
  clock, R_n = mean over λ in {0.05, 0.1, …, 0.5} of SR_n(λ), SR_n(λ) = (1+SR_{n−1}(λ))(1+λD_n).
  Promote when R_n ≥ A, where A is calibrated once by Monte Carlo so that
  P(max_{n≤B} R_n ≥ A) ≤ alpha=0.05 for IID D with p=1/2 (the least favourable null for λ>0).
  Because every pacer chooses requests predictably and released D's are IID under the null, the
  label-clock statistic has the same null law under every pacer, so one calibration serves all.
  After promotion the policy stops buying. No rollback (no reversal in this model).
- Net cost relative to never switching: J = Σ_t a_t(−D_t)·1[disagreement] + c_q·requests +
  c_s·switches. Oracle (expected-cost) relative cost: min(0, c_s − G(T−ν)).
  Regret(ν) = E[J] − oracle(ν).

## Pacers (all predictable, all respect the cap, buy only on disagreements)

- **U (uniform):** request probability q_t = remaining / (dis·(T−t)), clipped to [0,1].
- **TU (truncated uniform):** the same with horizon T−τ and no requests after T−τ, with
  τ = d + c_s/G_design, G_design = 0.08 (τ = 162.5 at d=100; 72.5 at d=10). τ comes from Lemma A
  below; G_design is the effect size the detector is tuned for, not the realised one.
- **BURST(r, h)** (DE-CuSum / CuSum-AC style, evidence-gated intensity): q_t = r × U's rate when
  log R_n < h, and q_t = 1 when log R_n ≥ h, until promotion or the cap. Grid r in
  {0.25, 0.5, 0.75}, h in {log 2, log 5, log 10}; 9 configurations, tuned on development seeds by
  worst-case regret, separately per delay cell; the selected configuration is evaluated on test
  seeds.

## Lemma A (to be proved and independently checked; stated before the run)

Idealise detection as "promotion once m post-change labels are released" with a fluid schedule
N(t) of cumulative requests, N(T) ≤ B, and B/(T−τ) ≤ dis. Then, over deterministic schedules,
the minimax worst-case regret over ν is G(m(T−τ)/B + d) with τ = d + c_s/G, attained by
constant-rate pacing on [0, T−τ]; uniform pacing on [0, T] has worst case G(mT/B + d).
**Prediction:** under the contract the worst-case gain of TU over U is about G·m·τ/B, i.e. about
2–3 cost units (roughly 6%) at d=100.

## Seeds and cells

- Calibration of A: seed base `2026120813`, 200,000 null sequences of B labels.
- Development (BURST tuning only): `2026120811`, 200 seeds per onset.
- Test: `2026120812`, 1000 seeds per onset.
- Onsets ν in {0, 100, …, 1900} (20 onsets). Delay cells d = 100 (contract, primary) and d = 10
  (secondary; small-delay adaptive sampling is already published for QCD).
- Seed streams are shared across pacers within a (seed, onset, delay) cell (paired).

## Estimands

- Worst-case regret W(P) = max over ν of mean Regret(ν); also the onset-averaged regret.
- Relative gain of P over U: (W(U) − W(P)) / W(U), with a 95% paired bootstrap interval over
  test seeds (2,000 resamples; the max over ν is recomputed in each resample).
- Diagnostics: per-onset regret curves, labels used, miss rate (no promotion by T when
  G(T−ν) > c_s), null false-promotion rate of the detector under each pacer at ν = T (no change),
  1000 seeds, with Wilson upper limit.

## Decision rule (stated now), primary cell d = 100

- **Stop** the Paper 3 pacing target as a method contribution if neither TU nor the tuned BURST
  reduces worst-case regret relative to U by at least 10% with the bootstrap lower limit above 0.
- If only TU clears 10%: record Lemma A as a benchmark-hygiene result (do not buy labels that
  release too late to repay a switch); it is an elementary covering argument and not a method
  contribution. Stop the method target.
- **Continue** (new protocol, theory for delayed evidence-gated pacing) only if the tuned BURST
  beats both U and TU by at least 10% with the lower limit above 0 at d = 100.
- The d = 10 cell is descriptive. A BURST win there alone does not count (published regime).
- Validity check: any pacer whose null false-promotion Wilson upper limit exceeds 0.0936 is
  excluded.
- No pacer, grid value, onset, cell or threshold changes after the run.

## Reproduce

```bash
uv run python scripts/sota_fidelity/pacing_minimax.py calibrate --out outputs/sota_fidelity/pacing_minimax
uv run python scripts/sota_fidelity/pacing_minimax.py tune --out outputs/sota_fidelity/pacing_minimax
uv run python scripts/sota_fidelity/pacing_minimax.py test --out outputs/sota_fidelity/pacing_minimax
uv run python scripts/sota_fidelity/pacing_minimax.py analyze --out outputs/sota_fidelity/pacing_minimax
```
