# 13. Final comparison and leaderboards (synthetic only, Q1 only)

Scope: only Q1 (harmful-shift detection) was explored. Q2 (replacement certification) and Q3 (cost-aware intervention) were **not implemented** in this phase.

## Leaderboard A: empirical improvement over matched, fairly tuned baselines
Rank by held-out harm power at benign FA ≤ .07, null FA ≤ .07; mean over held-out harm worlds.

| rank | method | provenance | G1 power (10%/20%) | G2 power (10%/20%) | benign FA (G2, 10%/20%) | valid by theory |
|---|---|---|---|---|---|---|
| 1 | **HG_brier** (new) | LOCAL fix on SOURCE_INSPIRED parent | .566 / .801 | .668 / .892 | .020 / .040 | yes (T2–T3) |
| 2 | page_hinkley | SOURCE_INSPIRED | .570 / .731 | .651 / .831 | .073 / .069 (fails the .07 cap at 10%) | no |
| 3 | pprm_tight | SOURCE_INSPIRED (PPRM-style, tight cap) | .513 / .715 | .617 / .857 | .018 / .034 | yes |
| 4 | DK_cost | LOCAL fix | .244 / .482 | .386 / .611 | .010 / .013 | yes |
| – | cusum | SOURCE_INSPIRED | lower | .415 / .542 | .074 / .094 (fails) | no |

HG's gain over its parent: G1 +.053 / +.086, G2 +.051 / +.035 (frozen rule: ≥ +.05 at both rates → met on G1, **fails at 20% on G2**). Verdict: *Outcome A partially met* (consistent direction, no regression, one rule failure). No baseline is a VERIFIED_REPRODUCTION, so "SOTA" here means the best source-inspired baseline, not the published method.

## Leaderboard B: novelty-driven fixes
| fix | targeted failure | mechanism | parent | held-out status |
|---|---|---|---|---|
| HG (discount+gate) | F3 slow adaptation + F4 power/benign trade-off | discounted Kelly moments; bet only when same-label decision cost rises | pprm_tight | direction replicates; magnitude below rule on G2/20% |
| DK | F3 | discounted moments | pp_cost_tight | meets vs parent; below pprm_tight |
| BD | F5 label allocation | boundary-weighted querying | pp_cost_tight | marginal gain unconfirmed on G2 |

## Eight questions
1. Improvement on matched baselines? Yes for Q1 detection with HG over `pprm_tight`, modest (+.04 to +.09), partially confirmed.
2. Which hybrid? Discounting plus decision-cost gating, not either alone (doc 10).
3. Shared failure mechanism? Plug-in Kelly bets average all history (slow adaptation) and Brier evidence cannot tell benign from harmful change.
4. Is the fix valid? Yes by construction for fixed known delay (doc 12).
5. Held-out? G1 seeds and G2 family: direction holds, G2/20% below threshold.
6. Novelty? Unassessed against the literature (sources blocked; snippet-level only); likely a composition of known adaptive-betting ideas. Do not claim novelty.
7. Where did it fail? Transient/recurrent harm (best ≤ .64 at 20% labels), cost-based evidence, BD.
8. Real data? Not touched; see doc 14.
