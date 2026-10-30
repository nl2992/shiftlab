# Cost-null comparator matrix (specification, written before running)
Common contract: target null E[cost_t | F_{t−1}] ≤ nominal cost + tol; PP increment X^c_t = ĥ^c_t + (Q_t/q)(C_t − ĥ^c_t) − c0 − tol with ĥ^c the decision-cost proxy; uniform support cap (5/6) unless stated; fixed known delay 5; α = .05 at threshold 1/α unless stated; label rates 10% and 20%; same seeds, same label mask per world.
| id | method | code | provenance | threshold |
|---|---|---|---|---|
| C0 | PP cost e-process, pooled plug-in Kelly | `pp_cost_tight` (context cap) | LOCAL_HEURISTIC adaptation of PP betting | 1/α |
| C1 | cost-only discounted Kelly γ=.995 | `fix_cost` + `uniform_cap` | LOCAL | 1/α |
| C2 | cost-only ONS | `pp_cost_guided` mode `cost_ons` | SOURCE_INSPIRED (ONS betting) | 1/α |
| C3 | Brier-guided ONS | mode `guided` | LOCAL | 1/α |
| C4 | **H2c** Brier-guided discounted Kelly γ=.995 | mode `guided_disc` | LOCAL | 1/α |
| C5 | mixture of 8 constant admissible bets on cost | `pp_mixture(risk="cost")` | LOCAL_HEURISTIC adaptation of mixture betting | 1/α |
| C6a | multi-horizon (γ ∈ {.9,.99,.999,1}) cost-only mixture | `pp_cost_multi` | LOCAL (mixture of valid e-processes) | 1/α |
| C6b | multi-horizon Brier-guided mixture | `pp_cost_multi(guided=True)` | LOCAL | 1/α |
| C7a | cost SR e-detector | `sr_cost_tight` | SOURCE_INSPIRED | empirical (null-calibrated; calibration-invalid risk flagged earlier) |
| C7b | Podkopaev–Ramdas-style stitched CS on cost | `pr_cs` | SOURCE_INSPIRED | theory (CS bound) |
| C8 | HG_unifcap, ONS (Brier), reference only | `fix_brier`, `pp_ons` | different null | 1/α |
No row is a VERIFIED_REPRODUCTION. A restart-only variant and a published decision-cost monitor beyond C7 are not available offline; C7 is therefore the strongest *obtainable* source-supported monitor, not a verified state-of-the-art one.
**Ablation set (checkpoint C):** guided pooled (γ=1) vs guided discounted γ ∈ {.99, .995, .999}; cost-only pooled (C0), cost-only discounted (C1); ONS cost (C2) vs ONS guided (C3); multi-horizon guided (C6b). Not run: reliability-weighted Brier guidance.
**Development data (fresh seeds):** dev pool 19 worlds × 200 seeds (seed 70000+), G3 stream 500 seeds (72000), G4 stream 500 seeds (71000, exploratory since the G4 family was used for confirmation). Metrics: harm power, benign FA, null FA by world role (decision-harm roles); per-seed outputs in `outputs/h2c_next/dev_per_seed.parquet`.
