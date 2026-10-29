# Causal finite-game reference for joint queries and reversible deployment

2026-10-28. Registered before implementation/execution. Previous goal turn: progress (a
concrete channel-selection mechanism rejected by dominance). This reference removes its
conditional-marginal restriction. It is a classical sequence-form optimization, not a new method.

## Information, costs and risk

Two installed actions start at 0. At the start of each round t, labels requested at s=t-d
arrive. Choose (installed action,query indicator) jointly using the full history of past choices
and released labels, with private fresh randomization. Outcomes are action independent. A query
costs c and immediately consumes one of B rights, including pending requests. Action changes
cost k, including initial promotion and later rollback. No switch gate, fixed test or conditional
deployment marginal is imposed. Both losses Y and 1-Y are identified by a queried common outcome.
No unqueried outcomes enter learner observations.

Optimize expected total decision/query/switching cost under the declared known recurrent working
model from `delayed_regime_information.py`. The learner never receives hidden regimes or pending
outcomes. Alternative probabilities are computed by exact hidden-state filtering at generated
events on the evaluator side. These are known-model development values, not dynamic-oracle regret.

Statistical risk is P(any action 1 by T)<=alpha for every causal law satisfying
P(Y_s=1 | full past and current choices)<=1/2. The environment sees previous outcomes, including
pending ones, and current public choices. It cannot see future private policy coins. Current
outcomes are generated after choices and released after fixed delay. Feedback availability is
the separate start-round research clock, not the old platform's end-round API.

This is a global-no-benefit-null false-promotion bound over the finite horizon, not a certificate
that a switch is profitable now or that losses before rollback are bounded.

## Classical finite-game formulation

Build a perfect-recall learner information set from time, all past (action,query) choices and
all released (event,outcome) pairs. Different pending outcomes and different unobserved null
probability choices must share that information set. The null opponent knows its own previous
choices, all generated queried outcomes and all public learner choices. At each request it
chooses the success probability 0 or 1/2, then chance generates that outcome at the event time.
Multilinearity gives an endpoint maximizer for every finite causal null strategy. Unqueried
hidden outcomes can at most provide opponent randomization, already allowed by mixed strategies.
Stop the null branch at the first promotion, whose risk payoff is 1. Continue the alternative
branch through T so rollback and further acquisition remain available.

Let x and y be learner/opponent realization plans, Ex=e and Fy=f their sequence flow equations,
and N the null-risk payoff matrix, including chance probabilities. Alternative expected cost
is g'x. The worst risk is max_{y>=0,Fy=f} x'Ny. Dualizing just this opponent optimization yields

    minimize g'x
    subject to Ex=e, x>=0,
               F'v >= N'x, f'v <= alpha, v free.

This preserves causal order without choosing the null law at feedback arrival. It permits
joint stochastic acquisition/action policies and keeps the hard cap on every history. Its
size may be exponential in the research horizon; no scalability claim is made.

The sequence form is established game theory: see the authors' manuscript
[Koller, Megiddo and von Stengel (1996)](https://ai.stanford.edu/~koller/Papers/Koller%2Bal%3AGEB96.pdf).
Read its realization-plan/flow description and behavior-strategy recovery before relying on
the formulation. No new LP method or conditional-planning theorem is proposed here.

## Frozen bounded execution and verification

Implement `scripts/solve_switching_causal_game.py`, using SciPy HiGHS for the sparse LP.
Recover one behavioral policy shared across all hidden histories. Numerically returned weights
must be normalized into exact rational behavior probabilities before verification. Independently
re-evaluate that policy by forward alternative expectations and a causal-null endpoint best
response, rather than treating solver success as a safety certificate. If exact recovered risk R
exceeds alpha, mix with the no-query/always-0 policy at probability alpha/R. That correction
preserves the pathwise budget and yields an exact risk bound; record any correction and value gap.
Do not call the corrected floating-point solution an exact rational optimizer.

First run tests for:

- identical visible histories sharing information sets despite different pending labels;
- a stationary T=2,d=1,B=1 analytic optimum, theta in {1/4,3/4} equally weighted, c=1/100,
  k=1/10: cost 187/200=0.935 at alpha=1 and 987/1000 at alpha=1/10;
- B=0 and no within-horizon label arrivals giving the continue cost and no queries;
- a policy passing IID calibration at 1/4 but having conditional-null risk 1/2;
- a future-coin/pending-label policy having causal risk 1/2, not the arrival-relaxed 3/4;
- alternative value versus the sequence-form objective and explicit hard-cap action availability.

Then execute only one main development cell: T=5,B=2,d=2, c=1/100,k=1/10,alpha=1/10,
transition01=transition10=1/10, emissions 1/20 and 19/20, prior S0=1/2. Stop tree construction
at 200,000 recursive nodes and stop LP at 60 seconds; preserve a resource-limit failure rather
than increasing limits or silently shrinking the registered cell. Save policy, code hashes,
sequence/node counts, solver residuals, exact recovered/calibrated risk, expected decision/query/
switch costs and query/switch counts to `outputs/switching_causal_game_v1/`.

This is a reference/correctness calculation, not a new efficacy sweep or confirmatory result.
The sequence-form LP represents the optimum over the declared finite policy class, so a candidate
under the identical cell cannot be required to beat that mathematical optimum. Use the exact LP
as an oracle upper bound on achievable utility (or lower bound on achievable cost), and compare
the candidate with scalable, non-oracle methods. A candidate should provide a nontrivial
computational or approximation guarantee to this oracle plus a strict performance advantage over
the strongest scalable baseline under the same contract. The recovered HiGHS policy is numerical,
not an exact optimality certificate; report solver bounds/gaps before treating it as the oracle
value. G1 and G2-G5 remain open.
