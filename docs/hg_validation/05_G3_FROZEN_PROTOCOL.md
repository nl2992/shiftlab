# 05. G3 (Markov-switching) confirmation protocol — frozen before running

**Generator.** `generators.simulate_g3`: 3 hidden regimes (0 source, 1 harmful concept shift δ=2, harm +0.233; 2 benign covariate shift δ=3, harm ≈ 0), T = 2000, asymmetric persistent transition matrix `G3_P`, start in regime 0, per-seed regime paths (so seeds are independent draws of a regime process, unlike the earlier fixed schedules). Not implemented from the brief: changing observation noise / loss scales.
**Candidate (frozen):** `HG_unifcap` = `fix_brier`, γ=.99, gate_w=100, uniform support cap, frac ∈ {0.10, 0.20}, delay 5, tol 0, threshold 1/α, α=.05. **Comparators:** `parent` (pprm_tight), `ONS`, `mixture8`, `disc_only` (γ=.99, uniform cap). All at theory thresholds; no tuning on G3.
**Data:** 1000 seeds, seed block 20000 (labels 21000); null control (transition matrix identity, regime 0 forever): 400 seeds, seed 20500.
**Scoring (per seed):** first harmful step f = first t with regime 1 (none → T). Detected: alarm ≥ f. False alarm: alarm < f (covers alarms in the source regime and in benign regime 2 before any harm). Harm before alarm: accumulated regime harm up to the alarm. Seeds that never reach regime 1 contribute false alarms only.
**Hypotheses (decided now):**
- H-G3-1: HG_unifcap − parent power gain ≥ +0.05 at **both** label rates, seed-bootstrap 95% CI lower bound > 0.
- H-G3-2 (niche claim vs ONS): HG power ≥ ONS power − 0.03 **and** false-alarm rate at least 0.02 lower than ONS, at both label rates.
- H-G3-3 (validity sanity): null-control false alarm ≤ 0.07 for HG_unifcap.
Outcome: each hypothesis reported pass/fail; no re-run, no retuning, failures reported as failures.
