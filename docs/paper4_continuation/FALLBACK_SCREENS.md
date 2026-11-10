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

## D3 — Certified economic policy compression: COMPLETE WITH NEGATIVE RESULT

**Screen.** Exact safety of a compressed policy is cheap: verify it with the 56–72-state product verifier and repair
by root mixture. The *economic* bound against the unrestricted `V*` needs a valid lower bound. WP B shows that every
tree-free lower bound stalls at the IID optimum on reversal cells, and that the coupling bound for distillation
contains the teacher's tree.

**Bounded tests (WP B, lead-verified where stated):**
- **B2 grid certificate.** Finite controllers with 10–22 memory states attain `V*` exactly as an upper bound in all 6
  reference cells. The lower bound stalls at the IID optimum on reversal cells: C2 gives 2.4002 against
  `V*` = 2.4419.
- **B3 distillation.** A belief-threshold student certified directly is optimal on C1, C4 and C5 and is 0.08–0.11%
  above `V*` on C2 and C3. Coupling bounds were loose or useless. Students v1–v3 collapsed to never-promote and
  are kept as failures.

**Prior art.** Robust FSC synthesis with verification (Cubuktepe et al. AAAI 2021, repo audit), oracle-guided FSC
synthesis (Andriushchenko et al. JAIR 2025, abstract read), and SMT-based constrained robust synthesis (Heck et al.,
AAAI-26 / arXiv:2511.08078, read by the literature agent) all cover compression with verified safety. None of them
supplies a tree-free unrestricted-optimum certificate, and neither did we.

**Empirical regularity (EMPIRICALLY SUPPORTED, 6 cells).** `V*` is attained by a ≤22-state deterministic controller
root-mixed with never-promote. No proof was obtained, and none is known to generalise.

**Decision: NO-GO — prior art.** The open problem is precisely a tree-free lower bound tighter than IID on reversal
cells.

## D4 — Lower bounds and impossibility

| Target | Result | Status |
|---|---|---|
| Separation between causal-null and IID-constrained optimisation | Corrected C3: `Γ = α·min{(g−k)/2−c, g−2k} > 0`, uniform in even T. N1: exact `Γ` for B=1 in any HMM. Γ > 0 occurs only in (M)-violating cells across 27,648 TP2 cells | PROVED (agent) + review-corrected; a decision-theoretic separation, but a single family plus a B=1 formula. The reviewer and the idea-evaluator both judge it a characterisation, not a standalone theorem |
| Memory requirements for safe approximate policies | No lower bound found. Candidate C (universal quotient) is not a bound on optimisers, and the observed optima need ≤22 states | NOT ESTABLISHED (screened; no candidate statement survived) |
| Complexity of unrestricted causal-null optimisation | Finite-horizon POMDP planning is PSPACE-complete in general (Papadimitriou & Tsitsiklis 1987, cited from memory, unverified). Our instances fix a 2-state HMM, so that reduction does not apply. No hardness proof for the fixed-model family | NOT ESTABLISHED |
| Hardness / value from pending-outcome asymmetry | Test B: pending access raises the null's risk (3/4 vs 1/2) for a fixed policy. Bounded test of the *value* effect (V* with a pending-visible null vs a released-only null) is run after the A3 campaign (CPU kept quiet) | PENDING bounded test |
