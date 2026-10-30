# Frozen confirmation protocol (v2) — written and committed BEFORE running

**Generator G4 (new family, never used for development or tuning):** `generators.simulate_g4`. Weak AR(1) signal factor, label = sign of the next return with logistic (heavy-tailed) noise, deployed model p = sigmoid(signal) calibrated for the source. Hidden Markov regimes: 0 source; 1 signal reversal (β = −0.7, decision harm ≈ +0.62, harmful); 2 volatility increase (σ = 1.6; Brier +0.039 but decision harm ≈ +0.079 < 0.10, **benign**). Own nominal risks from an independent source stream. Regime σ for regime 2 was chosen from a 4-point harm table to make it benign **before** any detector was run on G4. Not covered: transaction-cost regimes, model-replacement, G5 proxy-failure family, G6 delay/missingness.
**Data:** 1000 seeds, seed 50000 (labels 51000), T = 2000; null control (identity transition, 400 seeds, seed 50500); label rates 10% and 20%; delay 5; threshold 1/α, α = .05; no tuning.
**Finalists (frozen configurations from development, `outputs/hg_v2/`):**
- F1 = H2c: `pp_cost_guided`, mode `guided_disc`, γ = .995 (Objective B, cost null).
- F2 = gated ONS, hard gate, w = 200.
- F3 = gated ONS, multi-timescale gate (30, 200).
**References:** HG_unifcap, ONS, parent (pprm_tight), cost parent (`pp_cost_tight`), cost + discounted Kelly (γ = .995), disc_only (γ = .99).
**Scoring:** per seed, first harmful step f (first step in regime 1); detected = alarm ≥ f; false alarm = alarm < f (alarms in source or benign regime before any harm); power over seeds that reach regime 1; paired seed-bootstrap CIs (4000 resamples).
**Hypotheses (decided now; each reported pass/fail, no re-run, no retuning):**
- C1: F1 power − cost parent ≥ +0.10 at both label rates, CI lower bound > 0.
- C2: F2 power ≥ ONS power − 0.03 **and** F2 false-alarm ≤ ONS false-alarm, both rates.
- C2b: F2 power − HG_unifcap ≥ +0.03, both rates.
- C3: F3 satisfies C2 and C2b.
- C4: null-control false alarm ≤ 0.07 for F1, F2, F3 at both rates.
- C5 (descriptive): benign-regime discrimination: false-alarm rates of F1 vs Brier methods.
Legacy exit condition and the earlier frozen verdicts are untouched. Real data is not part of this protocol.
