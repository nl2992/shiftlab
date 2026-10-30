# H2c mechanism ablations (checkpoint C; dev seeds 70000+, exploratory; same outputs as the comparator matrix)
Dev-pool harm power at 10% / 20% labels (benign FA ≤ .04 in all rows):
| variant | Brier guidance | discounting | 10% | 20% |
|---|---|---|---|---|
| C0 cost parent (pooled plug-in) | no | no | .153 | .363 |
| guided, pooled (γ = 1) | yes | no | .323 | .572 |
| C1 cost-only discounted (γ = .995) | no | yes | .280 | .526 |
| guided γ = .99 | yes | yes | .408 | .645 |
| **H2c γ = .995** | yes | yes | **.422** | **.656** |
| guided γ = .999 | yes | yes | .376 | .612 |
| C2 cost ONS / C3 guided ONS | no / yes | ONS | .342 / .417 | .511 / .557 |
| C6b multi-horizon guided | yes | mixture | .381 | .617 |
**Findings.** (i) Brier guidance and discounting are each worth roughly +0.13 to +0.17 power over the pooled cost parent, and they are additive (.153 → .323 → .422 at 10%; .363 → .572 → .656 at 20%). So H2c's advantage is genuinely from *Brier-guided bet selection*, not discounting alone (RQ4: yes, at least on these worlds). (ii) ONS selection with Brier guidance (C3) matches discounted-Kelly guidance at 10% labels and is worse at 20% (.557 vs .656), so the cheaper discounted Kelly is the better guide. (iii) γ in {.99, .995} is flat (±.014), .999 worse. (iv) Multi-horizon mixing does not beat a single good horizon. Not run: reliability-weighted guidance, clipping/variance decomposition, combined Brier/cost history for ONS.
RQ5 (the same mechanism improving another cost-evidence algorithm): guidance improves the pooled Kelly (+.17), the ONS (C2 → C3: +.075 / +.046) and both discounted variants, so the mechanism transfers across three cost-evidence parents on the development pool.
