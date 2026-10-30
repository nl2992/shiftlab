# 06 Selected method and theory
Code commit at start: `8552911`; sprint branch `research/shiftlab-dependence-gates-2026-10-31`. Inputs: docs 02-05. **No new algorithm was selected**, because Gates A-C did not permit one (Case 1 not entered).
What exists, with status:
* **Theorem B1** (persistence obstruction), PROVED (elementary), scope: bounded {0,1} losses, lazy-resample chains, any observation scheme; unreviewed; probably folklore. See 03.
* **Reformulation:** use H0-cond; the repaired conditional-null e-process monitors (`shiftlab.gap.engine`) are the validated tool; their guarantee scope is in `VALIDITY_SUPPORT_MATRIX.md`. Status: KNOWN methodology.
* **LRV bet scaling (F2):** CASE 4 → **EMPIRICAL_ONLY**. Transfer test (`lrv_transfer.json`, 1000 paths): HG@20% false alarms on persistent-regime marginal nulls — plain 0.15 / 0.95 / 0.97 / 0.84 and with LRV(100 lags) 0.08 / 0.70 / 0.71 / 0.66 and LRV(300) 0.07 / 0.86 / 0.84 / 0.70 for delta = 0.5 / 0.05 / 0.01 / 0.003. It helps only mildly-persistent dependence and fails to restore alpha where persistence is long, so it is a null-specific diagnostic, never a valid detector.
Unresolved obligations: independent check of B1; a sharper (sqrt-type, ~1/eps^2) lower bound than the coupling bound; hidden-Markov alpha-correct test (open per Sethi et al.).
