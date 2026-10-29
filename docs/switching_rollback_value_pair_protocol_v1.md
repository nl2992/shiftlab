# Registered reversal-value diagnostic: fixed acquisition/test with a rollback label

**Registered:** 2026-10-28 before execution. This is a mechanism-attribution calculation, not an algorithm-efficacy study.

Hold T=6, B=3, d=2, alpha=1/10, query price c=1/100, switch charge k=1/10, emissions (1/50,49/50), and prior P(S0=1)=1/2 fixed. Compare two hidden-state models: (A) recurrent symmetric transition 0->1=1/10 and 1->0=1/10; (B) one-way transition 0->1=1/10 and 1->0=0. The one-way model supplies a no-reversal control with similar onset opportunities.

Request common outcomes at events 1,2,4, each label released at start event s+2. The first two labels are available at round 5; choose a randomized promotion function f(Y1,Y2) then. Event-4 feedback arrives at round 6 and is used only for rollback. Compare a controller that must hold action 1 through round 6 with one that rolls back at round 6 if its current-model predictive gain from action 1 is below -k. Both hold action 0 when not promoted; there is no re-promotion. Both pay all three query costs and the same promotion charge. The HMM forecasts determine expected action value and the rollback decision only; the null-risk proof uses no HMM assumption.

For each action rule, optimize f in [0,1]^4 against the HMM expected net economic value, subject to worst-case promotion risk <=alpha under the global causal null. Enumerate all eight endpoint kernels for Y1,Y2 (p1 in {0,1/2}, p2(y1) in {0,1/2}); Y4 cannot affect the round-5 promotion and does not enter its risk. Rationalize each returned LP test and recompute risk exactly. Compare: (i) optimized no-rollback test, (ii) the same test evaluated with rollback enabled, and (iii) optimized rollback-enabled test. This separates rollback value for a fixed promotion rule from value recovered by redesigning that rule.

Report both HMM cells, exact safe costs and risks, and the three differences. This is one predeclared pair, no tuning or Monte Carlo. The fixed test/cost optimization and optimal stopping concepts have prior art; no novelty claim follows. The result can reject or motivate, but cannot by itself validate, repeated reversible switching as the missing methodological contribution.

Reproduce with `PYTHONPATH=src python scripts/evaluate_switching_rollback_value_pair.py`; results and hashes go to `outputs/switching_rollback_value_pair_v1/results.json`.
