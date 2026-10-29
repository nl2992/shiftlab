# Causal-null constraint generation: theory and diagnostic protocol

Registered 2026-10-29 at starting commit `f51250b`, before implementation or
execution. This is a sourced baseline and candidate-B feasibility diagnostic,
not a claim of a novel method or synthetic/real-data efficacy.

## Exact mathematical construction

Let X be the exact pre-promotion learner sequence-flow polytope, c its alternative
expected cost, Y the exact causal-null opponent flow polytope and A the terminal
promotion payoff matrix from the unchanged first-promotion game. The full problem is

    V* = min_{x in X} c'x  subject to x'Ay <= alpha for every y in Y.

Let y_1,...,y_m be admissible opponent strategies. The restricted master imposes
only their m inequalities. Its exact optimum L_m is a lower bound on V*, since its
feasible set contains the original feasible set. For an exact master optimizer x_m,
compute an exact null best response y*=argmax_{y in Y} x_m'Ay. If its risk exceeds
alpha, add y* to the master; otherwise x_m is feasible and L_m=V*. Since the
finite game has finitely many null pure endpoint strategies, adding a genuinely
new violated pure response at each iteration eventually terminates in exact
arithmetic, but the number of strategies and iterations may be exponential.
The best-response information structure must match the full null's access to
pending outcomes and its observation of current query decisions.

At any intermediate iteration, obtain a valid upper bound U_m from any
independently verified feasible policy; for example, randomize once at the root
between the recovered candidate and the never-promote policy using exact
probability min(1,alpha/R), where R is its exactly evaluated full causal-null
risk. This preserves the pathwise query cap and gives exact risk <=alpha. The
smallest verified upper bound seen so far minus any **rigorous** lower bound L_m
is an anytime suboptimality certificate. Approximate master objectives or
best-response values alone are not rigorous bounds. If solving stops early,
report the certified gap; failure to obtain a tight gap is a result, not a pass.

This is established cutting-plane / double-oracle structure; see the sequence-form
[double-oracle paper](https://www.cs.utep.edu/kiekintveld/papers/2013/bklcp-DO.htm)
and the original exact LP reduction `switching_two_law_game_duality_v1.md`. The
novelty of generic constraint generation is rejected. A useful residual question is
whether a contract-specific separation oracle or bound can avoid materializing the
expanded null tree and improve end-to-end complexity while preserving the original
information asymmetry. No such result is presently established.

## Registered bounded diagnostic

Use the unmodified `FirstPromotionDecomposedGame` to build the learner/null flow
and payoff matrix. This first implementation intentionally materializes that tree,
so it cannot demonstrate an asymptotic solution to the history bottleneck. Compare
iterative masters and full null best responses to the existing dualized LP at
T=5,6,7, B=3, d=1, alpha=1/10, c=1/100, k=1/10, transitions 1/4, emissions
1/20 and 19/20, prior 1/2, same 200,000-node and 60-second-per-LP limits.
Run once per horizon, at most 64 cuts, violation tolerance 1e-9. Preserve failures,
intermediate iterations and all resource-limit outcomes in a new result file.

Compare unrestricted numerical objective with the reference, independently
recovered exact-rational cost/risk, activation probability, query cap, master
size, cut count, build/master/separation times, and the recovered feasible
upper bound. Verify that each best-response vector satisfies opponent-flow
constraints and each generated cut is an admissible null response; compare LP
best-response objective against the independent exact policy-risk evaluator.
Numerical solver values and rationalized strategies are explicitly numerical
unless a separate rational certificate has been checked. If the claimed validity
or equality fails, preserve the failure; do not label the output safe or optimal.

Before any synthetic or real-data efficacy test, establish that the generator
returns an explicitly feasible policy, useful objective gap, and an actual
end-to-end advantage over the existing exact solver on matched cells. Capture
resource use in a later registered protocol with a verified worker-process memory
sampler. No data, seeds, user datasets, or historical outputs are opened here.
