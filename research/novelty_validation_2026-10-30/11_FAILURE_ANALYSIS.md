# 11. Failure analysis

1. **H2c's only advantage is synthetic and within-class** (13/14, 14/14 harmful cells vs cost-only Kelly/ONS). Absolute power with a
   realistic economic tolerance is .136 / .256 and the nominal risk, when estimated, removes it below ~5,000 calibration events (repo).
2. **Mechanism is a bet-sizing heuristic.** X1: guidance helps (+.03 to +.14 power) only at 10–20 % labels (binding caps) and only when the Brier
   statistic shifts with the cost; the gain is the same when they are independent (ρ = 0) ⇒ it acts as a shift-timing signal. It loses up to .59 power when the
   guide is flat or opposed, and its relative-position map over-bets with full labels. No growth-rate theorem.
3. **Real-data reversal (D2).** With an estimated nominal risk the tested cost statistic has a large negative margin, while the Brier guide
   does not; H2c bets before drift, reaches the onset 7–30 nats behind, and alarms 242–824 events later than cost-only Kelly/ONS (CIs exclude 0).
   Contributing design choices I made and could not revisit without tuning on exposed data: Hoeffding (not empirical-Bernstein) nominal bound, half-batch calibration (n=622), guide without a tolerance/margin, exposed dataset.
4. **Stream-A validity check is vacuous** (0 alarms because the nominal margin ≫ cost). So there is *no* real-data evidence of calibrated validity from my run.
5. **Joint switching has no non-DP content found.** Gap ≤ 1.1 % on 192 exact toy instances, needs B ≥ 2, equals closed-loop VOI. Unconstrained version is textbook; the
   risk-constrained, learned-model version is open but has no candidate theorem here, and the repository has closed seven sub-ideas already.
6. **Coverage gaps I did not close:** CAMS, Challenger, Drift2Act, robust-FSC not re-read/re-run; PPRM CM-EB and Podkopaev–Ramdas CS not implemented; Betting-on-Predictions not mapped to the cost null; no TLC, WILDS, CRSP run; Phase F not entered.
7. **Process risks.** Single-agent lineage; per-seed variability in D2 is label-mask only; X1/X2 worlds are my own design.
