# 11 Safe-switching integration and fallbacks
Code commit at start: `8552911`; sprint branch `research/shiftlab-dependence-gates-2026-10-31`. Inputs: `docs/sota_gap_closure/Q3_*`, `S11_*`, `e11_s11_amortized_test.csv`, round-2 confirmation. Theorem status: none.
Case 2 required asking whether a (known) valid monitor can be coupled to acquisition and costed switching with a new risk-regret theorem. Findings:
* **Evidence of a joint effect, no theorem.** In the exact toy (`rpoq_exact`), the state-dependent optimal acquisition policy has mean first-promotion power 0.115 over unseen alternatives versus 0.092 for always-query (the best state-independent policy tried) and 0.061 for the variance-optimal table, i.e. state-dependent acquisition is worth about +0.02 absolute (+25% relative to always-query) on this toy. But no compact learned policy captured it (S11) and no scalable rule confirmed (round 2). This is a *conjecture* about a strict separation between joint and decoupled policies, not a result; it would need a general reduction argument (it is a finite-horizon POMDP, hence standard constrained-POMDP structure unless a special property is found).
* **Economic usefulness of an alarm is not guaranteed by validity:** Q3 shows HG-triggered switching has higher regret than PH-triggered under persistent harm and lower regret under transient harm. Alarm timing, not statistical validity, drives the sign.
* **Fallback A (allocation-aware validity via structural zero increments):** the observation that increments vanish on model-agreement events is the disagreement/query-by-committee idea combined with importance weighting; the bound refinement ("cap needs only the inclusion probability on events with non-zero increments") is a one-line consequence of the predictable-bet argument. **Rejected as known/trivial.**
* **Fallback B (estimable alternative):** oracle-alternative gains (+0.09..+0.13 label-matched on dev) vanished with estimation (round 2: -0.02..+0.02); plug-in Neyman-style allocation with estimated variances is established (ASI-style). **Rejected.**
* **Fallback C (budgeted safe switching theorem):** no theorem found; the closest tractable object is the exact finite-horizon DP of the repository. **UNRESOLVED; not pursued without a candidate separation.**

## Update: estimand / switching study in cluster worlds (`scripts/dep_sprint/estimand_switching.py`, 600 paths, T=2000)
Stylised, fully observed: hidden bad/good regime (lazy chain, P(bad)=0.3=r0, cluster length 20 / 100 / 333); incumbent loss = regime indicator (mean r0); fallback loss 0.35 (A: regime-local benefit) or incumbent+0.05 (B: none); switch cost 1.0 each way; both monitors see every loss (q=1); hold after an alarm of 20 or 100 steps, then restart (two values tried, not optimised). Net cost (loss + switching):

| variant | cluster length | incumbent only | fallback only | oracle regime-aware | conditional alarm (hold 20 / 100) | marginal (Sethi) alarm |
|---|---|---|---|---|---|---|
| A | 20 | 595.9 | 701.0 | 250.9 | 527.5 / 551.6 | = incumbent (never fires) |
| A | 100 | 594.4 | 701.0 | 216.8 | 418.1 / 379.5 | = incumbent |
| A | 333 | 601.5 | 701.0 | 213.4 | 375.6 / **298.0** | = incumbent |
| B | 20 | 606.0 | 707.0 | 678.9 | 644.3 / 654.4 | = incumbent |
| B | 100 | 605.0 | 706.0 | 644.0 | 661.3 / 646.5 | = incumbent |
| B | 333 | 600.1 | 701.1 | 633.0 | 664.0 / 639.9 | = incumbent |

**Answer to the estimand question.** The "dependence false alarms" of conditional-null monitors are, for an economic user, *correct detections of actionable harm* exactly when an action with regime-local benefit exists (A: up to -50% net cost, still far from the oracle's -64%); when none exists (B) they cost +6..+10%. The marginal-null monitor is never wrong but also never useful at these persistences (consistent with Gate B). Limits: deterministic losses, full observation, no label cost, a hand-built fallback, hold lengths untuned, no rollback test — this shows the *direction* of the dependence of the answer on the action set, not a method.
