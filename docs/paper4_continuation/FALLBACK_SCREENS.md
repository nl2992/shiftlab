# WP D — fallback screens

Each candidate gets a theorem/prior-art screen plus a bounded constructive or counterexample test (directive D5).
Status labels follow `THEOREM_REGISTRY.md`.

## D1 — Instance-dependent complexity parameter

**Candidates:**
- the number of binding safety constraints `|K|` (FCG cuts);
- the number of economically pivotal nonmonotone regions (≤ inversion-frontier size);
- the number of distinct economic continuation states.

**Bounded test.** These are FCG-fast time splits from saved artifacts
(`docs/paper4/experiments/results/fcg_scale_v2*.json`):

| Cell | `|K|` | Learner variables | Total s | Build s | LP s | Separation s | Separation share |
|---|---|---|---|---|---|---|---|
| C6 (T=8) | 22 | 2,273 | 2.26 | 1.05 | 0.64 | 0.31 | 13.7% |
| S1 (T=10) | 1 | 13,421 | 37.58 | 36.87 | 0.11 | 0.06 | 0.16% |
| S2 (T=10) | 1 | 13,421 | 53.79 | 50.87 | 0.23 | 0.09 | 0.17% |
| S3 (T=10) | 1 | 13,421 | 44.35 | 43.36 | 0.11 | 0.07 | 0.15% |

**Finding.** Runtime tracks the learner-tree size, not `|K|`. An upper bound of the form
O(|K| · LP(learner tree) + |K| · verifier) is immediate, because FCG is a cutting-plane method. It is dominated by
the learner tree, which every exact method in the repo builds. A matching lower bound in terms of `|K|` is impossible
in that form. Even with `|K| = 1`, the T=10 cost is about 37 s, because tree construction dominates. So `|K|` does
not control difficulty. The pivotal-region and continuation-state counts were measured earlier: the reachable belief
graph had 4,867 states, equal to the public-history tree size (Candidate G). They show no compression on the tested
cells.

**Prior art.** Output-sensitive bounds for cutting-plane and double-oracle methods (iterations bounded by support
size) are standard; see the Bošanský et al. framing.

**Decision: NO-GO — scientific significance.** The parameters either fail to control difficulty or are not small on
tested instances. If WP B finds an implicit representation, the complexity question reopens on *that*
representation's size; see the B decision.

## D2 — Specialised robust constraint separation

**Screen.** A new contribution needs a provably cheaper separation oracle. The current oracle is the exact
product-state best response, already linear in the reachable product states (56–72 at T=8–10).

**Bounded test (table above).** Separation takes 0.15–0.17% of end-to-end time at T=10 and 13.7% at T=8, where cuts
fire. Even an infinitely fast oracle would save at most 14% on C6 and less than 0.2% at T=10.

**Decision: NO-GO — computational feasibility (no leverage).** Warm-started LPs would only touch the LP share
(0.64 s on C6), which is engineering work by the directive's own definition.

## D3 — Certified economic policy compression

Pending WP B3 (certified distillation), which covers the same ground. Observation for the screen: the IID-optimal
policies in all IID-safe cells are root mixtures of two deterministic plans with a single randomised information set
(`docs/paper4/experiments/results/iid_tightness_v1.json`). Optimal policies are therefore *structurally* compact
(randomisation-wise), but the plans themselves are still history-indexed trees.

## D4 — Lower bounds and impossibility

Pending WP C3 (positive-premium family) and WP B. Existing related results:
- Candidate C, the universal response-quotient bound. It is not a bound on optimisers.
- Test B: pending-outcome access raises the null's risk (3/4 vs 1/2). This is an information-asymmetry witness, not
  a complexity bound.
