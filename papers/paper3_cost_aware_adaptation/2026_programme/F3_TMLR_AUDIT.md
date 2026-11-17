# F3 TMLR draft audit (2026-11-17, HKUSTDial tech-paper-template + pre-submission-reviewer)

Draft audited: `paper/f3_tmlr/main.tex` (20 pages; main text to p.11).

## 1. Positioning
New Problem/Setting paper with a method and a matching lower bound. The goal (a pathwise budget on
realised intervention harm under delayed, missing and sampled feedback) carries the narrative; the
shield shows the goal is achievable and the lower bound shows it is achieved without waste.

## 2. Thinking template (as the draft stands)
| Stage | Content |
|---|---|
| Background | Promoting a challenger model is an intervention judged through delayed, sampled, missing labels, with switching costs. |
| Limitation 1 | Alarms and sequential tests certify "better now", not what the switch costs by the time labels arrive. |
| Limitation 2 | Future-payback certificates are impossible without restricting the future (Prop. nocert). |
| Limitation 3 | Safe-exploration work (conservative bandits, Prudent-Banker) assumes immediate or passive feedback, no switching fee, no label budget, guarantees in expectation or as reward ratios. |
| Goal | With prob. >= 1-delta, harm (excess loss vs never switching + fees) never exceeds R, for every tape and delay/missing mechanism. |
| Challenge 1 | Harm is revealed only after a delay or never: a rollback triggered on observed harm is late. |
| Challenge 2 | Labels are scarce and chosen adaptively: inference must stay valid under the controller's own sampling and arbitrary dependence. |
| Challenge 3 | Undoing a promotion costs a fee: stopping harm itself adds harm. |
| Challenge 4 | Is any such guarantee wastefully conservative? |
| Module A (C2) | Design-based anytime IPW bound (Lemma 1 / 1'), settlement accounting for sampled rounds. |
| Module B (C1) | Pending-feedback reserve: worst case for every round in transit and the current round. |
| Module C (C3) | Rollback reserve k held while deployed; ride-out when the horizon cannot exhaust R. |
| Module D (C4) | Lower bound (Prop. reserves) + attainment; ruin bound; regime-map prediction. |
| Contributions | (1) formulation + nocert, Sec 2; (2) shield + Thm, Sec 3-4; (3) lower bound + ruin, Sec 4; (4) regime map, Sec 4-5; (5) registered + real evidence, Sec 5. |

## 3. Self-consistency checks
1. Limitations -> Goal: pass.
2. Goal -> Challenges: pass in substance, but the draft names only one challenge explicitly
   ("harm becomes known only after its delay"). MAJOR: state the four challenges in the intro.
3. Challenges -> Methodology: pass (one module per challenge).
4. Methodology -> Contributions: pass.

## 4. Questions a reader will ask, and whether the draft answers them
Answered = A, partly = P, not answered = N.

Setting
- Q1 Why measure harm against never switching, not against the better model? P. Needs: the incumbent is the status quo whose risk the team already accepted; the budget is "how much worse than doing nothing are we willing to be".
- Q2 Why do fees count as harm? P. Needs: migration, retraining, cache invalidation, user-visible changes.
- Q3 Why is Z_t = 0 when the models agree, and why does one label reveal both losses? N. This needs the explicit assumption that a loss is a function of the model's prediction and the common outcome (e.g. 0/1 loss), and that both predictions are logged.
- Q4 How can the controller see disagreement before the label? N. Both predictions are computed at serving time.
- Q5 What does O3 mean in plain words? P. The delay of a round may depend on its outcome or on the past, but not on whether that round was sampled.
- Q6 How should a practitioner choose R and delta, and what does headroom h = R - 2k mean? N.
- Q7 Why is the probability only over the controller's coins, and why is that a strength? A.

Method
- Q8 Why reserve k for a rollback that may never happen, and why charge the current round at 1/pi? P. Needs a worked numeric example.
- Q9 What does the inner rule do, and what does the shield change about its queries? P.
- Q10 What are the variants (full sampling, paced, blind-round, v3) and when to use which? N (scattered).
- Q11 Algorithm box omits ride-out and the label reserve. P.

Theory
- Q12 What does the reserves proposition mean in one sentence? P. "No valid controller can hold a new promotion through a feedback-blind window longer than R - 2k exposed rounds; the shield holds exactly that long."
- Q13 Intuition for m = R - 2k - d in the ruin bound? N.
- Q14 Why is the regime prediction informal? A.

Experiments
- Q15 What are the 30 regimes? N (names only). Needs an appendix table with each path and parameter.
- Q16 What exactly are Wald with cutoff, CUSUM, the gate, CUSUM rollback, stop-loss? N. Needs an appendix description with tuned parameters.
- Q17 Why T = 300, B = 60, k = 3, and T = 2000, B = 200, k = 5 on real streams? N.
- Q18 What are the real streams: tasks, incumbent and challenger models, how losses and delays were built? N. Needs the source description, and that the delays are simulated constants, not real release times.
- Q19 What randomness do the 20 policy seeds per episode cover? N.
- Q20 Why is never-switch the reference for "keeping the budget"? P.
- Q21 What do the stress regimes stress and who chose them? P.
- Q22 Code and data availability, compute used, broader impact? N.

## 5. Severity summary
0 CRITICAL; 8 MAJOR (challenges not explicit; Q3/Q4 assumption; no worked example; variants
scattered; comparators undescribed; regimes undescribed; real streams undescribed; no figures);
the remaining items MINOR.

## 6. Actions
Text revision (explanations) and figures (figures4papers house style, matplotlib, data from the
committed result files) run in parallel; calibrated-comparator results fill Section 5.2.
