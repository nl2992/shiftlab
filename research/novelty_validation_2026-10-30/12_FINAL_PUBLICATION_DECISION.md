# 12. Final publication decision

## Classification: `BENCHMARK_OR_NEGATIVE_RESULT_ONLY`

Applying the task's decision logic in order:
1. *Statistically invalid under its claimed null?* **No** for H2c's own (zero-tolerance conditional cost) null — validity is the generic predictable-betting argument (08 S1). HG's earlier marginal-null failure is a recorded, repaired counterexample, not a new finding.
2. *Reduces to existing methodology?* **Yes** — composition of PP-IPW increment (Xu et al.; PPRM), predictable discounted Kelly/ONS, a side-information bet fraction, and Podkopaev–Ramdas α-split (02). **STOP novelty claim. Preserve engineering and benchmark findings.** This branch decides the classification.
3. (Corroborating, not needed to decide) the gain did not hold against an equally equipped comparator on the one real stream I ran (D2), and the joint-policy gap is DP-implied (X2).

Not `NO_GO` for the whole programme: the repository's evidence-bearing parts (estimand corrections, label-waste/gating correction, calibration-size dominance, exact-solver kills, evaluator-bug records) are publishable as a benchmark/negative-results contribution. Not `NO_DEFENSIBLE_METHOD_YET` as the final label only because that label would hide the preserved benchmark value; the *method* verdict is exactly that: **no defensible method.**

## Answers to the nine questions

1. **Strongest confirmed result.** The frozen G5 run: H2c − better of cost-only discounted Kelly/ONS = +0.086 [.059,.113] (10 % labels) and +0.094 [.063,.125] (20 %), 13/14 and 14/14 harmful cells, synthetic, one generator family, zero-tolerance null (repository run; I replayed none of the simulation). My own strongest results are negative/diagnostic (see 3, 5).
2. **Published methods demonstrably outperformed: none.** No faithful published cost-null comparator was reproduced; within-class local comparators lost to H2c in the synthetic frozen run and beat it on D2.
3. **Proposed contribution, precisely.** None that survives: H2c is a heuristic composition. What I can state is a characterisation: Brier-guided bet selection is a bet-sizing/shift-timing heuristic that helps at 10–20 % label rates when the guide co-shifts and harms when it is flat/opposed or lacks the tested statistic's nominal margin (07 §1, §3; DEVELOPMENT_ONLY / EXPLORATORY).
4. **Assumptions behind the guarantee.** Conditional cost null `E[L_t|F_{t−1}] ≤ U_0+ε`; known query probability, query independent of the outcome given the past; context-free support caps; predictable bets from released labels; fixed/outcome-independent delay; nominal bound with explicit `δ_S` (04, 08).
5. **Strongest null/adversarial tests revealed.** Validity is insensitive to the guide (counterexamples CE2/CE3 keep false alarms < .03); *power* is highly sensitive to the guide's alignment (up to −.59). The real-data null (stream A) was vacuous and tested nothing about calibration.
6. **Transfer to real data?** On the single exposed real stream (UCI gas), **no — reversal**: H2c is 242–824 events later than cost-only Kelly/ONS. One domain only; the two-domain requirement is unmet; TLC, WILDS, CRSP not executed.
7. **Downstream economic decisions?** Not improved: H2c accumulates 2–4× the realised excess cost before alarm on D2; no switching policy was evaluated on real data in this programme; X2's joint-vs-separate net-cost gap is ≤ 1.1 % on a toy.
8. **Paper type.** Benchmark / negative-results (estimand and null-class accounting, calibration-size dominance, gating/label-waste correction, guidance-alignment failure mode, DP kill tests). Not a method paper; not a theory paper (no separation theorem).
9. **Single experiment/theorem that would most change the verdict.** A *proved* separation: a class of streams in which the growth-optimal predictable bet is a function of an auxiliary statistic's history and any cost-only predictable bet has a provable log-wealth regret, **together with** one registered, fresh-seed run on a second real domain (with a tight, pre-declared nominal bound) beating faithful PPRM/Podkopaev–Ramdas CM-EB under the same cost null and α allocation. Without the theorem, no experiment moves the novelty verdict.

## What was not done (scope disclosure)
Phase F was not entered (nothing to freeze), so `09_FROZEN_CONFIRMATION_PROTOCOL.md` and `10_FROZEN_CONFIRMATION_RESULTS.md` are deliberately absent. D1 (TLC), D3 (WILDS), D4 (CRSP) not executed; PPRM/PR CM-EB and CAMS/Challenger/Drift2Act not reproduced; no scalable joint-policy algorithm built; Holm correction not applicable (no confirmatory family). Materiality threshold (+0.05 power or 10 % relative pre-alarm harm reduction, with validity intact) is proposed, unregistered, and **unmet** by D2 (H2c is worse).

## Next step if anyone continues (ordered)
(1) Do not extend H2c. (2) If a monitoring contribution is still wanted, first search for a *theorem* (regret lower bound for auxiliary-statistic-sized bets); (3) otherwise write the benchmark/negative-results manuscript from the preserved findings; (4) any new real-data test must pre-register the nominal-bound method and use an unexposed domain (TLC is the unexposed candidate: CDN reachable, event-time vs publication-time and the counterfactual-replay label must be declared).
