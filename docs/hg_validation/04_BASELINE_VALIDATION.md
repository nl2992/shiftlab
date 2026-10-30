# 04. Baseline validation: adaptive-betting comparators (partial Goal 4)

Added two standard adaptive-betting e-processes on the same uniform-cap PP increment (valid under the marginal null by construction, doc 02): `pp_mixture` (equal-weight mixture of 8 constant bets, LOCAL_HEURISTIC adaptation) and `pp_ons` (online-Newton-step betting, SOURCE_INSPIRED, standard constants, bet frozen before each X_s and updated from resolved labels only). Configurations were fixed before running; they were evaluated on the **already-exposed** G1/G2 held-out pools, so this is exploratory, not confirmation. Source: `outputs/hg_validation/04_ADAPTIVE_BETTING_COMPARATORS.csv`.

Mean harm-power / benign-world false alarm / null false alarm (400 seeds per world):
| gen, labels | parent | HG_unifcap | mixture8 | ONS | discounting only (unifcap) |
|---|---|---|---|---|---|
| G1, 10% | .513 / .021 / .012 | .582 / .026 / .008 | .626 / .044 / .032 | **.658** / .054 / .028 | .648 / .038 / .012 |
| G1, 20% | .715 / .042 / .012 | .806 / .053 / .010 | .738 / .071 / .038 | .789 / .090 / .035 | **.825** / .090 / .025 |
| G2, 10% | .617 / .018 / .008 | .673 / .020 / .010 | .728 / .043 / .038 | **.772** / .052 / .028 | .741 / .032 / .010 |
| G2, 20% | .857 / .034 / .012 | .898 / .040 / .020 | .872 / .061 / .032 | .888 / .068 / .038 | **.922** / .065 / .022 |

**Findings.**
1. A standard adaptive-betting method (ONS) matches or beats HG's power in three of four cells (G1 10% +.076, G2 10% +.099, G2 20% −.010, G1 20% −.017 relative to HG_unifcap) **but at 2–3× the benign-world false alarm** (.052–.090 vs .020–.053) and higher null false alarm (up to .038).
2. Discounting alone is the strongest power source; the gate is what holds benign false alarms down (disc-only benign FA .032–.090 vs HG .020–.053). So HG occupies a *lower-false-alarm point on the power/false-alarm frontier*, not a uniformly better one.
3. HG is therefore not shown to beat the best established adaptive-betting comparator; its distinguishing claim must be "similar adaptation with materially fewer benign alarms", which needs a formal frontier comparison (matched benign FA) before it can be claimed. Not yet done.
4. The mixture of constant bets is dominated by ONS on G1 and by disc-only on most cells.
**Still missing from Goal 4:** published PPRM/Podkopaev–Ramdas/WATCH reproductions (sources unreachable), ADWIN, BOCPD, restart/multi-start variants, ASI/Robust ASI/growth-aware querying, runtime accounting (the 2.31 s parent time includes first-call overhead and is not comparable). Provenance remains SOURCE_INSPIRED or LOCAL_HEURISTIC for every arm; none is a VERIFIED_REPRODUCTION.

## Matched-false-alarm frontier (dev pool, threshold sweep; `outputs/hg_validation/04_FRONTIER_DEV.csv`)
Each arm's threshold was swept (1/α from 2 to 500, so these are *empirical* operating points, not theory-valid thresholds) on the 19-world development pool (200 seeds, not a held-out pool). Best harm power with benign-world false alarm ≤ cap and null false alarm ≤ .07:

| labels | benign FA cap | HG_unifcap | ONS | discounting only | mixture8 | parent |
|---|---|---|---|---|---|---|
| 10% | .02 | **.488** | .461 | .449 | .362 | .372 |
| 10% | .03 | **.546** | .461 | .510 | .429 | .428 |
| 10% | .05 | **.603** | .581 | .559 | .524 | .485 |
| 10% | .08 | .663 | **.667** | **.667** | .577 | .537 |
| 20% | .03 | **.659** | – | – | – | .512 |
| 20% | .05 | **.757** | – | – | .607 | .569 |
| 20% | .08 | **.818** | .759 | .758 | .688 | .687 |
(– = no swept threshold met the cap; at 20% labels no arm reaches benign FA ≤ .02.)

**Reading.** At matched benign false alarm HG_unifcap is on or above the frontier of every comparator at every cap except a tie at 10%/.08, with gains over ONS of +.027 to +.085 at 10% labels and +.059 at 20%/.08. This supports the narrower claim "HG gives more power than ONS and disc-only when benign false alarms must stay low", the first evidence for a defensible niche. It is development-pool evidence only: the swept thresholds forfeit the theory guarantee, the dev pool defines the benign worlds, and the same sweep has not been run on a held-out pool.
