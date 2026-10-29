# Capacity-constrained delayed feedback: close online-learning comparator

2026-10-28. **Status:** primary arXiv source inspected; close comparator added. No novelty
conclusion or new algorithm is claimed.

## Source and result

Ryabchenko, Attias and Roy, [*Capacity-Constrained Online Learning with Delays: Scheduling
Frameworks and Regret Trade-offs*](https://arxiv.org/abs/2503.19856), arXiv:2503.19856 (2025).
The cached primary PDF is
`outputs/switching_source_audit_v1/capacity_constrained_delayed_learning_2025.pdf`; SHA256 and
byte count are in `switching_source_manifest_v16.json`. I inspected the formal Delay Scheduling
protocol in Section 1.1, the batch partitioning algorithm, Theorems 3.1–3.2 and their stated
proof reductions, and the scheduler/learning separation in Section 4.1.

The paper studies oblivious loss vectors with feedback delay. A pathwise capacity `C` bounds how
many past rounds are simultaneously tracked; the learner chooses actions and may select a round
for observation, receiving either that selected action's loss (bandit) or the full loss vector
(full information) when the delay expires. The objective is expected regret to the best fixed
action. For fixed delay `d`, Theorem 3.1 gives, for batch size `b` satisfying
`b >= d_max/(C-1)`, a full-information upper bound
`12 sqrt(T b log K) + 3 sqrt(D log K)`, with `D=Td`; the bandit bound is
`14 sqrt(T b K) + 3 sqrt(D log K)`. Theorem 3.2 gives the corresponding fixed-delay minimax
rates `Theta(sqrt(T K(1+d/C)) + sqrt(Td log K))` in bandit feedback and
`Theta(sqrt(T(d+1)log K))` in full information at its capacity-matched operating point. The
batch-partition algorithm samples one uniform representative round per contiguous batch and runs
delayed FTRL at the batch level; its batch size ensures the capacity is respected.

## Exact overlap and limits

For two frozen candidate models, one queried common outcome reveals both model losses. It can
therefore be encoded as a full-information observation of a two-action loss vector on the sampled
round. Let `B>=1` be ShiftLab's total query cap and set `b=ceil(T/B)`. The batch-representative
schedule then makes `q=ceil(T/b)<=B` queries deterministically. Their capacity condition
`b>=d_max/(C-1)` is met by `C>=1+ceil(d/b)`; thus the adaptation accounts for both total requests
and concurrent pending labels. With `K=2`, their full-information theorem gives the explicit
fixed-comparator loss-regret bound

    12 sqrt(T b log 2) + 3 sqrt(T d log 2).

Adding the ShiftLab costs gives a direct expected net-cost bound no worse than this expression
plus `c q + k q`, since there are `q` paid requests and at most `q` action changes from initial
action 0 across `q` held batches. This cost accounting is our reduction, not a theorem from their
paper. Since `b=ceil(T/B)` and `B<=T`, `T b <= 2T^2/B`; hence the explicit looser form is

    12 sqrt(2 log 2) * T/sqrt(B) + 3 sqrt(T d log 2) + (c+k)B.

Their capacity constraint is not the total query budget: with `b=1`, observing every round needs
capacity about `d+1`, while the total-query cap limits how many rounds are selected over the whole
horizon. The mapping preserves both limits rather than identifying them.

This gives only a fixed-comparator expected net-cost bound. A dynamic comparator with `S` switches
and a false-promotion gate require additional analysis. Simply gating the batch learner by an
e-process also does not preserve the stated regret bound for free.

The result has no priced query, switching-cost term, dynamic comparator, global conditional-null
false-promotion event, or deployment reversal. Its stated regret is to the best fixed action and
the adversary is oblivious. Those differences leave the full ShiftLab contract unresolved, but
they close generic claims that batch sampling or delayed hard-cap learning alone provide a new
mechanism. The batch representative baseline is especially relevant to any equal-budget synthetic
comparison: it has an explicit delay-capacity feasibility condition and a minimax characterization
in its own model.

## Research consequence

The candidate movement-compatible query coupling is already rejected by its continuation-state
dominance proof. The suggested next step in `switching_transport_acquisition_candidate_v1.md`—
allowing query-dependent deployment marginals—is inside the causal full-policy reference's policy
class, so it cannot alone define a novelty delta either. A viable G1 target must now prove a
strict improvement over (i) risk-valid paired e-process plus a costed delayed batch/switching rule,
(ii) the best scalable episode-wise sequential design, and (iii) capacity-constrained delay
scheduling where capacities can be matched. In small instances, the causal sequence-form LP is an
oracle bound, not a beatable baseline. If no scalable theorem-level separation survives these
comparisons, revise or stop the methodological hypothesis before G2–G4.

## Provenance

Primary PDF URL, byte count and SHA256 are recorded in `switching_source_manifest_v16.json`.
This focused scope audit does not claim an exhaustive literature search or independent proof
verification beyond the inspected portions. The conversion inequalities `q<=B`,
`b>=d/(C-1)`, and `Tb<=2T^2/B` were exhaustively checked for all integer
`1<=B<=T<=200` and `1<=d<=T` (2,686,700 triples); this checks the bookkeeping only, not the
published regret proof or the safety wrapper.
