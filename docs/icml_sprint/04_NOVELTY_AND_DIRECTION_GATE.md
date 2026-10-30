# 04. Direction gate (no new algorithm implemented in this pass)
| criterion | A: calibration-efficient monitoring | B: budgeted switching, delayed feedback | C: tight valid restart evidence |
|---|---|---|---|
| source-level novelty | low: α-splitting and empirical Bernstein are standard (PR/PPRM line, MAPIE) | **unresolved but no direct hit found** | low: e-detector mixtures are the core of the e-detector paper |
| feasible theorem | tighter bounds ≠ theorem; a separation under matched assumptions is not identified | unidentified; regret/lower-bound docs exist on `main` (unread this session) | restart weights proved valid but showed no gain |
| observed advantage | calibration size dominates power (large, but a property of the problem) | none yet (nothing implemented in this lineage) | valid restarts +0.003–0.023, noise-level |
| generalisability | – | unknown | empirical SR advantage fails calibration transfer |
| baselines available | PR/MAPIE (binary risk only) | repo exact solvers | e-detector (R pkg) |
| compute | low | high | low |
| ICML-method fit / finance | moderate | **highest** | low |
**Kill tests.** A: a tighter nominal bound is a lemma, not a result; killed unless a lower bound shows the n_cal requirement is unavoidable under matched assumptions (not attempted). C: killed — valid restart schedules do not beat ordinary H2c and the SR advantage needs a threshold with no guarantee. B: *not killed, not supported*. Obligation before any implementation: show, with the repository's exact small-instance solvers, an instance where the optimal **joint** acquisition-and-switching policy strictly beats the best policy that tunes acquisition and switching separately **with equal information**; the repository's own ledger records several apparent gains that reduced to futility stopping or standard planning, so that reduction must be tested first.
**Selection.** B, by default and by elimination, as a *research question* — with no method, no theorem, and no experiment yet. Nothing was implemented.
