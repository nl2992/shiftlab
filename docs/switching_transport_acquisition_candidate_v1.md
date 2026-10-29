# Movement-compatible acquisition: screened and rejected as the contribution

2026-10-28. Previous turn: progress (causal-risk planner audit). Register the construction and
checks below before implementation. This is a specific acquisition/switching mechanism screen.
It does not nominate a paper or reopen the stationary rollout grid.

## Rule and precise information boundary

Work with two actions and an oblivious bounded paired-loss stream. Initially action 0 is installed.
Partition T=mL rounds into m<=B equal blocks, request exactly one common-outcome label per block,
and hold one deployed action throughout each block. Labels arrive at event+d, d>=1; use only
labels available at block start. Each requested label identifies both fixed-policy losses.

Let H be the history of requests, their announced sampling probabilities and arrived labels,
excluding realized deployment actions and deployment coins. Condition on the entire oblivious
loss path for the proof; it is not supplied to the learner. Suppose the previous action has
conditional probability r of being 1 given H. Choose the next target probability p from H.
Choose two query-location distributions a_j=P(J=j|old action=0,H) and
b_j=P(J=j|old action=1,H), each with mass at least gamma/L, 0<gamma<=1. They may use H,
but cannot otherwise depend on private deployment history. The acquisition component may read
the previous installed action to sample J. Announce J and its marginal probability

    pi_j = (1-r)*a_j + r*b_j.

After seeing J, the old-action posterior is r_j=r*b_j/pi_j. Couple the old action to the new
Bernoulli(p) by a maximal Bernoulli coupling **conditional on J**. If p>=r_j, retain an old 1
and turn an old 0 into 1 with probability (p-r_j)/(1-r_j). If p<r_j, retain an old 0 and
retain an old 1 with probability p/r_j. Zero-mass branches are never sampled. Use a fresh
independent coin for this transition. Hold the resulting action, and request event J when due.

This differs from reusing an unconditioned uniform after an action-dependent query. Induction
gives P(new action=1|H,J)=p. Arrived outcomes do not disclose new action randomness under the
conditioned oblivious path. Therefore this invariant is available at the next block. It does
not hold by assertion for action-dependent outcomes, reactive losses, or acquisition accessing
additional private deployment history. Those information structures are excluded.

## Exact acquisition cost and a concrete selection rule

Conditional on H, the minimum expected switch count of any transition preserving p in every
announced query stratum is

    S(a,b;r,p) = sum_j pi_j*abs(p-r_j)
              = sum_j abs(p*(1-r)*a_j - (1-p)*r*b_j).

The coupling above attains it. The lower bound follows separately in every stratum from the
Bernoulli coupling inequality. Triangle inequality gives S>=abs(p-r). Equality holds exactly
when every summand's signed argument has the sign of p-r (all zero if p=r). Thus select query
channels by the following explicit rule:

    maximize (1-r)*sum_j a_j*v0_j + r*sum_j b_j*v1_j
    subject to row sums 1, a_j,b_j>=gamma/L,
               p*(1-r)*a_j >= (1-p)*r*b_j for all j if p>=r,
               reverse these inequalities if p<r.

The v values are declared predictable economic continuation scores, not hidden oracle utilities.
The present implementation accepts supplied scores and makes no claim that a one-step VOI score
captures delayed certification bundles or reversals. This is a small linear program. It exploits
the exact switching cost, rather than charging an independent information penalty. A soft-priced
variant may instead subtract k*S from its score; it is not evaluated in this screen.

When p=r in (0,1), equality forces a=b: action-dependent querying cannot be free while keeping
that conditional deployment marginal. When p changes, nontrivial channels can be free. For
r=1/2,p=3/4,L=2,gamma=1/2, a=(3/4,1/4), b=(1/4,3/4) has S=1/4, exactly abs(p-r).
With v0=(1,0),v1=(0,1), it scores 3/4; every action-independent channel scores 1/2.
This is a strict **local score** separation at equal switch cost and one query, not evidence
of lower cumulative regret or a new optimal-transport theorem.

For L=2, write a=(x,1-x),b=(y,1-y), A=p*(1-r),C=(1-p)*r and z=A*x-C*y. Then

    S=abs(z)+abs((p-r)-z).

The free region is the box gamma/2<=x,y<=1-gamma/2 intersected with
min(0,p-r)<=z<=max(0,p-r). Its linear-score optimum occurs at a box corner or an intersection
of a box edge with z=0 or z=p-r. Enumerating these vertices is an exact two-slot implementation;
the polytope is always feasible because a=b=uniform satisfies the constraints.

## Supporting finite-budget/delay bound

This bound is a derivation for the **ungated reference version**, not the full safe/dynamic goal.
At each block start, set p_b=sigmoid(eta times the sum of arrived estimated paired differences).
Store pi_J at acquisition. On its eventual arrival use loss estimates

    hat_l_b(a) = l_(b,J)(a)/(L*pi_J).

They lie in [0,1/gamma]. Conditional on pre-query H their expectation equals the block average
loss of action a. Since the recoupling keeps p_b in every query stratum, its actual deployment
loss has exactly the mixture expectation. Old-action-dependent queries do not invalidate that
unbiasedness statement. Every request is charged at its event; pending and resolved together
are exactly m<=B, including outcomes arriving after T.

Let h=ceil(d/L). Compare to Hedge on all previous estimated losses, even ones not yet arrived.
Its pathwise bound is log(2)/eta+eta*m/(8*gamma^2). At most h previous estimates are missing
at a block start, so the sigmoid derivative bound gives a probability discrepancy <=eta*h/(4*gamma).
Conditional expected abs(hat_l_b(0)-hat_l_b(1))<=1. Delayed mixture regret therefore adds at
most eta*m*h/(4*gamma). Multiply by L to convert block averages to round losses.

Under the channel constraints, expected switches are exactly E sum_b abs(p_b-p_(b-1)),
with p_0=0 and p_1=1/2. Each arrived estimate changes the paired score by at most 1/gamma,
and each is incorporated once; expected switches are <=1/2+eta*m/(4*gamma). Hence

    E[J_total] - min_a sum_t l_t(a)
      <= L*log(2)/eta + eta*T/(8*gamma^2) + eta*T*h/(4*gamma)
         + k*(1/2+eta*m/(4*gamma)) + c*m.

At gamma=1 the channels are uniform and this recovers the previous reference bound. This is
a fixed-comparator bound, may be vacuous, and is not an improved minimax rate. A gate p=0
before valid evidence can separately prohibit early promotion, but one cannot claim this same
regret bound after adding that gate: its waiting cost requires a separate analysis. No combined
false-switch/dynamic-regret theorem has been proved here.

## Novelty audit and disqualifiers

Maximal coupling and its total-variation optimality are classical; see the author's
[Roch coupling notes](https://people.math.wisc.edu/~roch/teaching_files/833.f14/slides-chap4-web.pdf).
[Cheng et al., ICML 2023](https://proceedings.mlr.press/v202/cheng23f/cheng23f.pdf), Algorithm 1,
already uses batching, unbiased feedback estimates and shrinking-dartboard switching control;
its displayed query time is uniform. Those ingredients and the rate above are not new.
The exact query-stratified transition and economic channel constraint are the only proposed
technical delta. A uniform-time algorithm alone is not an equivalence audit of the entire paper.
Public/private online learning and adaptive correlated sampling remain audit obligations.
Search results alone do not establish absence of this construction.

The candidate fails if existing conditional coupling/controlled observation methods already
provide the same acquisition rule and guarantee, or if the movement-compatible restriction
eliminates its economic benefit against the strongest equally equipped method. The local-score
example does not pass that test. Do not promote it to a contribution by renaming classical coupling.

## Frozen checks before efficacy

Implement an exact Fraction kernel and two-slot vertex solver. Enumerate r,p and channel slot
probabilities on {0,1/4,1/2,3/4,1}. Verify every query-stratum marginal, exact expected switches,
the lower bound abs(p-r), and equality precisely for the signed constraints. Independently solve
the 2x2 joint marginal constraints by its feasible interval to verify the coupling lower bound.
Check the strict local-score example, gamma=1 reduction, endpoints r,p in {0,1}, infeasible
probability inputs, and optimal score against all feasible points on a finite comparison grid.
The grid supports implementation fidelity; the vertex proof establishes the continuous optimum.
No tuned simulation grid, efficacy comparison or real-data claim is registered.

Next audit the exact conditional acquisition/switching delta, then evaluate a complete rule
with a justified continuation score and risk contract if it survives. G1 remains open.

## Pre-efficacy rejection: the apparent value is removed by averaging

The counterfactual continuation check disqualifies the candidate **within its own contract**.
Keep p fixed before J and the repaired marginal P(new=1|H,J)=p. Replace the action-dependent
channel by sampling J independently of the old action from pi_j=(1-r)*a_j+r*b_j. Couple the
old action to Bernoulli(p) maximally, independently of J. This replacement has

    P_replacement(J=j,new=a|H)=pi_j * Bernoulli_p(a)
                             =P_original(J=j,new=a|H),

but switch probability abs(p-r)<=S(a,b;r,p). It also preserves the per-slot probability floor,
request count, query timing, pending feedback and each block's expected decision loss for every
fixed oblivious loss path. Announced original channel metadata can be retained; it contains no
extra randomness beyond H. A backward/inductive application preserves the future law of the
state (H,new installed action), so expected future utility is unchanged. The compatible-channel
candidate attains equality in the switching comparison: it has no advantage over this simpler
action-independent replacement.

This argument assumes old deployment history is discarded except for the currently installed
action, as required by the candidate's probability invariant. It does not cover constraints
depending on realized cumulative loss, switch count, or an unrecorded past-promotion flag.
It is not a theorem that arbitrary action-dependent acquisition is useless. In particular,
allowing the next action distribution to vary with J removes the displayed equality and requires
a new actual-marginal/belief calculation. Gated false-promotion probabilities are not preserved
by this expected-cost argument without an additional state/risk proof.

The local score example is therefore an **inadmissible efficacy argument**: v0 and v1 reward
distinctions in the discarded old-action variable. Under the declared continuation state,
actual continuation reward is a function of (H,J,new action); its conditional expectation after
repair cannot acquire that old-action dependence. Current switching charges are already included
in S. Arbitrary supplied scores can differ, but their mathematical optimization is not evidence
for actual economic improvement. Keep the example as a warning, not a motivation to tune a grid.

Decision: no-go for this rule as the contribution, before any efficacy run. The coupling kernel,
exact local optimization and supporting static bound remain useful reference mathematics. The
next hypothesis must jointly choose acquisition and a query-dependent deployment distribution,
carrying the actual conditional action belief rather than forcing every query stratum to have
the same target p. It still needs source-level equivalence checking, a meaningful new result,
statistical risk analysis and matched synthetic/real evidence; none is supplied by this rejection.
