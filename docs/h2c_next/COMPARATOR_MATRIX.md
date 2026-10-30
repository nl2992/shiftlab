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

## Results (checkpoint A; fresh development seeds; `outputs/h2c_next/dev_summary.csv`, `dev_per_seed.parquet`, `h2c_paired_dev.csv`)
Dev-pool harm power / benign FA / null FA, then G3-dev and G4-dev power over all seeds (G4-dev is exploratory):
| labels | method | dev power | benign FA | null FA | G3dev | G4dev |
|---|---|---|---|---|---|---|
| 10% | C0 cost parent | .153 | .010 | .020 | .066 | .408 |
| 10% | C1 cost disc. | .280 | .012 | .015 | .110 | .526 |
| 10% | C2 cost ONS | .342 | .029 | .010 | .176 | .612 |
| 10% | C3 guided ONS | .417 | .028 | .020 | .198 | .664 |
| 10% | **C4 H2c** | **.422** | .016 | .015 | .178 | .676 |
| 10% | C5 mixture of 8 | .309 | .028 | .025 | .176 | .582 |
| 10% | C6a multi cost | .256 | .016 | .020 | .120 | .526 |
| 10% | C6b multi guided | .381 | .016 | .010 | .170 | .678 |
| 10% | C7a cost SR (empirical threshold) | .510 | .044 | .045 | .262 | .742 |
| 10% | C7b PR-style CS | 0 | 0 | 0 | 0 | 0 |
| 20% | C0 | .363 | .012 | .005 | .150 | .656 |
| 20% | C1 | .526 | .019 | .010 | .218 | .758 |
| 20% | C2 | .511 | .034 | .015 | .246 | .758 |
| 20% | C3 | .557 | .038 | .045 | .286 | .786 |
| 20% | **C4 H2c** | **.656** | .027 | .025 | .300 | .828 |
| 20% | C5 | .473 | .032 | .025 | .260 | .734 |
| 20% | C6a / C6b | .473 / .617 | .019 / .025 | .020 / .030 | .204 / .296 | .754 / .814 |
| 20% | C7a cost SR | .715 | .055 | .055 | .420 | .838 |
Reference (different null): HG_unifcap .578 / .818, ONS(Brier) .659 / .816 at dev-pool power 10% / 20%, with benign FA .043–.141.

**Paired H2c − X (G3-dev / G4-dev, 500 independent regime paths each, 95% CI).** vs C0: +.11 / +.27 (10%), +.15 / +.17 (20%), all CIs exclude 0. vs C1: +.07 / +.15, +.08 / +.07 (exclude 0). vs C2 (cost ONS): +.002 [−.03, .03] / +.064 [.030, .098] at 10%; +.054 / +.070 at 20% (exclude 0). vs C3 (guided ONS): −.020 [−.044, .002] / +.012 at 10%; +.014 / +.042 [.018, .068] at 20% — a tie at 10%, small edge at 20%. vs C5 (mixture): +.002 / +.094, +.040 / +.094. vs C6b: all CIs include 0 (−.002 to +.014). vs C7a (cost SR): **−.084 / −.066 at 10%, −.120 at 20% on G3-dev (CIs exclude 0 against H2c)**; −.010 on G4-dev at 20% (tie).

**Reading.**
1. Among *theory-threshold* cost-null methods H2c is the best or tied-best in every cell. Its advantage over the earlier "strongest comparator" (C0) is large; over cost-only ONS (C2) it is real in 3 of 4 cells; over Brier-guided ONS (C3) it is a tie at 10% labels and small at 20%.
2. The cost-null SR e-detector (C7a) has **higher power than H2c** (up to +.12), but uses a null-calibrated empirical threshold, has benign/null FA .044–.055 (vs .016–.027) and carries no guarantee; the earlier phase already found this family fails to hold false alarms on some configurations. So it is a higher-power, unguaranteed alternative, not a dominated one.
3. C7b returned zero detections everywhere (pr_cs at its theory threshold with the cost loss); it is treated as a degenerate/uninformative comparator, not a defeated one.
4. No comparator is a verified reproduction; the Podkopaev–Ramdas-style and SR rows are source-inspired approximations.
