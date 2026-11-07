# A3b registered protocol: is the B = 4, alpha = 1/10 gap only a pre-label public coin?

Registered 2026-11-01. A3 is complete (`f92e586`; Part 2 returned the mechanical outcome GAP AT
B=4). This protocol was registered before running the check below. It is a theory verification
and makes no method claim.

## Observation motivating it

In A3 Part 2, at B = 4 and alpha = 1/10, all 54 cells are uncertified. Their pure-calendar gaps
are all positive, with a maximum of 1.41%. Condition (P) fails because the optimum promotes on 3
positive labels out of 4.

In the cell inspected, the optimum's only chain randomisation happens at t = 1, before any
label exists. It takes the chain paths [1,2,3,4] and [2,3,4,5]. Because a coin flipped before
any label is public and independent of every label, the optimum may simply be a mixture of
calendar policies.

## Proposition 6' (pre-label mixture certificate)

This proposition is proved here.

**Setup.** Call a history *label-free* if no label has been released by its time. The policy's
choices at label-free histories depend only on time and on the public coins. Decompose an
optimal policy `pi*` into branches `pi_i`. Each branch fixes one positive-mass sequence of
label-free choices. Branch i carries weight `lambda_i`, the product of the choice masses along
its prefix, and below that prefix it follows `pi*` unchanged.

**Linearity facts.**

- The solver's causal-null best response (`null_risk`) gives the adversary its move only
  *after* each learner choice. The risk is therefore linear in the learner's choice masses at
  every node, so `risk(pi*) = sum_i lambda_i risk(pi_i)` exactly.
- The cost is linear in the same masses: `cost(pi*) = sum_i lambda_i cost(pi_i)`.

**Claim.** If every branch has query support `|Q(pi_i)| <= B`, then `pi*` is a public-coin
mixture of calendar policies `pi_i ∈ Pi_{Q(pi_i)}`. Branch i has level `a_i = risk(pi_i)`, and
`sum_i lambda_i a_i = risk(pi*) <= alpha`. Hence `C_mix(alpha) <= J(alpha)`. With Lemma 2, this
gives `J = C_mix`.

## Check

For each of the 54 cells at B = 4, alpha = 1/10 (the A2 families, T = 8, d = 1, cq = 1/100,
solver `2bd2e8e`):

1. Re-solve J.
2. Enumerate the label-free branches.
3. For each branch, compute exactly its support (using A3's `enumerate_flags`), its cost
   (`sum(expected_metrics[:3])`) and its risk (`null_risk`).
4. Verify `sum_i lambda_i cost_i = J`. This applies when the activation is 1. If the activation
   is not 1, report the cell as not checkable.
5. Verify `sum_i lambda_i risk_i = raw_risk <= alpha`.
6. Check whether every branch support satisfies `|Q(pi_i)| <= B`.

## Outcomes

| Outcome | Condition |
|---|---|
| PRE-LABEL MIXTURE EXPLAINS | Every checkable cell is certified by Proposition 6'. In that case `J = C_mix` at B = 4, alpha = 1/10, and the A3 pure-calendar gap is a convexification artifact. |
| GENUINE ADAPTIVITY | Some checkable cell has a branch with support larger than B. Report those cells. A mixture-envelope computation would then be needed before any further claim. |

Run settings: a single process launched detached, resumable through a JSONL file, with a 2-hour
cap.
