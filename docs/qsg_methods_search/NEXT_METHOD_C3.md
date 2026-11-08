# NM-C3: synthetic confirmation for the next method

**Status: NOT RUN. No candidate passed the development gate.** This is recorded as a blocker,
not marked complete.

- Reserved, unopened seeds: NM-dev replication 2026110941 (40), NM-C3 2026110977 (100).
- Historical C3 (EQSDp arms A/B vs tuned Gong–Zhang-style and Qiu-style adapters, `10ba0237`)
  stands as recorded. It was not re-run or rewritten.
- The closest candidate, E (ESS-adjusted Wald), has development Δ −0.81 [−1.62, +0.01] vs the
  best fixed Wald on the mixed 20-regime family. That is below the gate, so confirming it
  would mean testing a claim already known to be at most small.

## What a confirmation would look like if E were advanced anyway (not registered)

- Claim: on a mixed independent-plus-dependent family, one frozen ESS-Wald config has lower
  worst-domain regret than every fixed Wald config.
- Comparator: the fixed Wald config that minimises worst-domain regret on the development seeds.
- Metric: cross-domain minimax regret, with the paired contrast on the mixed family as the
  primary test.

Expected effect from development: ≈1 unit. That is a *small* effect under the
fair-evaluation scale, so it is not a methods-paper headline.
