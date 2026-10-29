# Asymmetric recurrent-HMM query-timing development screen

**Registered:** 2026-10-29 before execution. **Status:** bounded G1 development diagnostic only.

## Question and scope

The six-cell symmetric HMM calendar decomposition found no recovered-cost benefit from fully
adaptive query timing. This registered four-cell screen tests whether asymmetric regime entry/exit
rates and prior imbalance create an adaptive-timing value under the same hard budget, delay,
switching fee and robust false-promotion constraint. It is a candidate falsification screen, not a
method claim or efficacy confirmation.

## Frozen contract

Use `T=6`, pathwise `B=3`, fixed delay `d=2`, `alpha=1/10`, query fee `c=1/100`, switch fee
`k=1/10`, and emissions `P(Y=1|S=0)=1/20`, `P(Y=1|S=1)=19/20`. Compare four HMM cells:

| cell | transition 0→1 | transition 1→0 | prior P(S=1) |
|---|---:|---:|---:|
| entry-slow | 1/10 | 3/10 | 1/2 |
| exit-slow | 3/10 | 1/10 | 1/2 |
| entry-slow/high-prior | 1/10 | 3/10 | 4/5 |
| exit-slow/low-prior | 3/10 | 1/10 | 1/5 |

In every cell compare (a) unrestricted adaptive query/action planning over the exact finite
causal-null game and (b) all 15 deterministic query calendars of size at most three drawn from
events 1–4, each with the same adaptive action/query-skip decisions on calendar dates. Event 5
queries are excluded from fixed calendars because their labels release after the horizon; the
unrestricted solver may skip them. The null adversary uses the original full-history conditional
endpoint class and sees pending queried outcomes. Each recovered policy is independently evaluated
and root-activation calibrated to alpha exactly as in the reference solver. Report raw and
calibrated cost/risk/query/switch metrics, optimizer status/residuals, all calendar costs, node and
sequence counts, and hashes. The LP optimizer is numerical; recovered policy risk is exact, so do
not call cost gaps certified oracle gaps.

## Stop rule

If no positive recovered-cost gap appears, stop the adaptive-timing mechanism and do not broaden
the grid. If a gap appears, it only nominates an operating regime for a later source audit and
stronger comparator; it does not establish novelty. Preserve resource-limit failures without
raising limits. Reproduce with `python scripts/screen_switching_asymmetric_timing.py`.
