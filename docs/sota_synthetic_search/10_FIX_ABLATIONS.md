# 10. Fix ablations (dev pool, from `outputs/sota_search/fix_decision_table_fix.csv`; Brier parent `pprm_tight`)

Rows are mean harm-power change vs parent (dpow) and mean benign false-alarm change (dfa) over the 19-world dev pool.

| variant | 10% dpow | 10% dfa | 20% dpow | 20% dfa | frozen rule |
|---|---|---|---|---|---|
| parent (γ=1, no gate) | 0 | 0 | 0 | 0 | – |
| discount only γ=.99 (DK) | +.162 | +.025 | +.124 | +.033 | fails (benign FA) |
| gate only (γ=1, w=100) | −.051 | −.022 | −.030 | −.042 | fails (power loss) |
| **discount + gate (γ=.99, w=100) = HG** | +.106 | −.007 | +.104 | +.007 | **meets both** |
| discount + gate (γ=.99, w=200) | +.125 | −.006 | +.113 | +.002 | meets 10%, fails 20% (ok=False by worse5/improved) |
| BD + discount (γ=.99) | ≤ +.098 | ≥ +.028 | ≤ +.097 | ≥ +.030 | fails (benign FA) |
| BD, no discount | −.06 to −.17 | ~0 | −.06 to −.12 | ~0 | fails (power loss) |

**Reading.** Neither component alone is acceptable on the Brier parent: discounting buys power and costs benign false alarms; gating removes false alarms and costs power; together they keep most of the power with false alarms at parent level. This is the evidence for HG being a *joint* fix and not a lucky setting: the interaction is visible across the γ and w grid (γ=.98/.995 behave like .99; w=200 similar to w=100). BD hurts the Brier parent in every configuration and is retained only for the cost parent (+.073–.079 marginal on dev, +.022/+.033 on G2, i.e. not confirmed).
Not yet ablated: gate threshold (sign only), the one-sided cap interaction, and gating on a different decision-cost window than the e-process window.
