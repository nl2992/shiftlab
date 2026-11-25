# R7 adaptation-strength sweep: results

Protocol and predictions: [r7_adaptation_strength_sweep_protocol.md](r7_adaptation_strength_sweep_protocol.md).
2,000 tasks (5 strengths x 4 budgets x 100 seeds, 61000000-61000099), CPU, 1,949 s.
Output `outputs/r7_sweep/`; tables from `scripts/analyze_r7_sweep.py`.

## Findings

1. **Pacing converts budget into horizon, not into detection.** Pooled over all 1,900 harm-path
   rows, fixed minus paced detection is +0.005 (95% bootstrap CI -0.006 to +0.016) with the
   historic engine and -0.006 (-0.018 to +0.006) with Timans GRAPA. Individual cells scatter by up
   to 8 points, within binomial noise at 100 seeds.
2. **The reserve horizon separates the two cleanly.** At s = 1.00, r = 0.05 fixed gating processes
   1,136 of 2,400 events before the reserve stops it; paced gating processes 2,111 (mean post-onset
   query rate 0.58 against 0.14) at the same label count (119 vs 119). Fixed horizon shrinks
   monotonically in s at every budget (r = 0.02: 1,929 -> 1,131); paced shrinks more slowly.
3. **Paced gating detects later.** Lower q raises each increment's support bound (5/q), so each
   label carries less evidence. Censored delay at s = 1.00: 598 (fixed) vs 1,166 (paced) at r = 0.10
   and 401 vs 637 at r = 0.20; at s = 0.75: 974 vs 1,347 and 567 vs 783.
4. **Detectability boundary in (s, r).** Full feedback detects from s = 0.50 (0.95) on. Gated
   monitors reach 0.95-0.99 at r = 0.20 for s >= 0.50, 0.56-0.86 at r = 0.10 for s >= 0.75, and stay at
   or below 0.29 at r <= 0.05 for every s. `uniform_ppi` detects 0.00 at r <= 0.05 across all strengths.
5. **Validity.** Worst pre-onset alarm rate is 1/100 in any cell for every primary arm (exact 95% upper
   bound 4.7%); `ppe_gated` has one cell at 3/100.

## Against the registered predictions

| Prediction | Outcome |
|---|---|
| P1: fixed within 3 points of paced everywhere, ahead at s = 1, r = 0.10 | Holds pooled (CIs within +-2 points); single cells vary +-8; at s = 1, r = 0.10 fixed leads by 6 (historic engine) and 1 (GRAPA), not significant |
| P2: fixed horizon shrinks faster in s | Confirmed at every budget |
| P3: low-budget detection falls with s, <= 0.35 at s = 1 | Level holds (<= 0.29); direction was misstated: stronger intervention is also stronger harm, so detection rises with s but stays low at r <= 0.05 |
| P4: pre-onset alarms <= 5% | Primary arms confirmed; `ppe_gated` worst cell 3/100 |

The earlier single-cell R7 reading ("fixed gating beats paced") is refined here: detection ties,
and the difference is horizon (paced) against delay (fixed).
