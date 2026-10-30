# Candidate D: scalarized one-sided POSG with risk-bracket recovery

**Date:** 2026-10-29. **Status:** conditional recovery theorem proved below;
algorithmic complexity and novelty unresolved. **Decision:** retain as the next
candidate-generation baseline; do not claim a new method yet.

## Why this is the next test

The previous Candidate C result only rules out a universal quotient that must
reproduce every null response kernel. It does not rule out an implicit
policy-search method. The existing exact hidden-root reduction turns every
Lagrange scalarization of the original two-law problem into a one-sided
partially observable stochastic game (OS-POSG). Horák et al. give an HSVI-style
value-approximation algorithm for OS-POSGs and strategy extraction that carries
an explicit strategy gadget; their paper warns that a belief point alone is not
enough to choose a safe strategy. This suggests a stronger candidate baseline
than posterior-only planning, but the OS-POSG solver's output still needs
risk-aware primal recovery.

## Recovery theorem

Let

`V* = inf{ C(pi) : R(pi) <= alpha }`,

where the policy class is the original randomized, nonanticipating,
pathwise-budget class, `0 < alpha < 1`, `C(pi) >= 0`, a never-promote policy has
risk zero and cost at most `T`, and `R(pi) = sup_nu P_nu(first promotion by T)`.
The latter cost bound holds in this repository because incumbent per-round
decision loss is at most one and the never-promote policy can avoid both query
and switching charges; it does not assert that every policy's cumulative cost
is at most `T`. The finite constrained sequence-form LP is strictly feasible
because never-promote has risk zero. Define

`g(lambda) = inf_pi { C(pi) + lambda (R(pi) - alpha) }`.

Strong LP duality gives `V* = max_(lambda >= 0) g(lambda)`. Let `lambda*` be a
maximizer. Because `g(0) >= 0`, while the never-promote policy gives
`g(lambda) <= T - lambda alpha`, there is a maximizer in `[0,T/alpha]`.

Assume either:

1. `lambda*=0` and an `epsilon`-optimal scalarized policy at zero is exactly
   verified to have risk at most `alpha`; or
2. there are multipliers `lambda_- <= lambda* <= lambda_+` with
   `lambda_+ - lambda_- <= delta` and two policies `pi_-`, `pi_+` whose exact
   worst-case risks bracket the target,
   `r_- = R(pi_-) >= alpha >= r_+ = R(pi_+)`, and whose scalarized values obey
   `C(pi_i) + lambda_i (r_i-alpha) <= g(lambda_i) + epsilon` for `i in {-,+}`.

In case 2, draw a private root coin selecting `pi_-` with probability
`w=(alpha-r_+)/(r_--r_+)` and `pi_+` otherwise (if both risks equal `alpha`,
any weight is valid). The mixture respects the pathwise query cap and
nonanticipation, has full causal-null risk at most `alpha`, and satisfies

`0 <= C(pi_mix) - V* <= epsilon + delta`.

### Proof

For either endpoint policy, `|R(pi_i)-alpha| <= 1`; hence

`C(pi_i)+lambda*(r_i-alpha)`
`= C(pi_i)+lambda_i(r_i-alpha)+(lambda*-lambda_i)(r_i-alpha)`
`<= g(lambda_i)+epsilon+delta`
`<= V*+epsilon+delta`.

Rearranging gives
`C(pi_i) <= V*+epsilon+delta-lambda*(r_i-alpha)`. The selected weight makes
`w r_- +(1-w)r_+ = alpha`, so the mixture's expected alternative cost is the
same weighted average and is at most `V*+epsilon+delta`. For every causal-null
response, promotion risk under the root mixture is at most the weighted sum of
the component worst-case risks, even if the null learns the active branch.
Therefore the mixture is feasible. Every feasible policy has cost at least
`V*`, which proves the lower side of the gap.

The `lambda*=0` case follows directly: if `g(0)=V*` and the returned
epsilon-optimal cost-minimizer is feasible, its cost is at most `V*+epsilon`.
The theorem is conditional on a risk bracket in case 2; it does not prove that
an approximate solver will find one.

## What the theorem does not establish

- The scalarized OS-POSG value approximation is established prior art. Horák et
  al. prove epsilon-equilibrium value bounds and strategy extraction, but do not
  solve this robust constrained primal-recovery problem.
- Lagrangian duality, multiplier search, root mixing and exact robust
  verification are established generic ingredients. The recovery lemma alone
  is not a novelty claim.
- No uniform bound is established for the number of belief points, alpha-vector
  gadgets, strategy memory, null-risk verifications, or runtime. The augmented
  game state count is at most a product of root mode, HMM state, delayed queue,
  remaining budget, deployment, promotion flag and time; the continuous belief
  search can still dominate and strategy extraction must preserve perfect recall.
- An approximate scalarized equilibrium at one multiplier can be feasible but
  economically poor. In the exact two-policy example `(C,R) in {(1,0),(0,1)}`
  with `alpha=1/2`, `lambda*=1` and `V*=1/2`, both pure policies minimize the
  scalarized objective `C+R-1/2`; returning the safe policy alone costs `1`, a
  gap of `1/2`. The risk-bracketing mixture is needed even with an exact solver.
- If the risk endpoint evaluations are only approximate, the bracket must use
  rigorous upper/lower risk bounds; empirical calibration is insufficient.

## Prior-art comparison and status

| Result | Closest source | Shared guarantee | Remaining technical delta | Status |
| --- | --- | --- | --- | --- |
| Scalarized hidden-root game | `switching_lagrangian_posg_reduction_v1.md`; Horák et al., [primary source](https://arxiv.org/abs/2010.11243) | Exact finite-game value representation under asymmetric information | Generic OS-POSG recursion does not supply a size advantage for this expanded state | Established reduction |
| Approximate scalarized game solution | Horák et al., HSVI and strategy extraction, Theorem 4 and §10 | Epsilon value/equilibrium approximation for OS-POSG | Must match finite-horizon augmented state, bounded payoff and the learner's hard budget; strategy gadget must be independently evaluated | Relevant established baseline; exact mapping still required |
| Constrained primal recovery | Khonji et al., [IJCAI 2019](https://www.ijcai.org/proceedings/2019/0775.pdf); robust FSC verification in Cubuktepe et al., [AAAI 2021](https://cdn.aaai.org/ojs/17401/17401-13-20895-1-2-20210518.pdf) | Approximate planning under probability constraints and post-synthesis exact verification | Full causal-null family, strategy bracket and end-to-end computational advantage remain unaddressed by this adaptation | UNRESOLVED — EXACT REDUCTION REQUIRED |

**Current assessment:** mathematically sound recovery wrapper, but likely a
standard composition. Its value is to expose the exact output requirement for
any approximate game solver: return two near-minimax policies with verified
risks bracketing `alpha`, or a directly feasible policy with a small
primal-dual gap. Do not implement it as the proposed novel algorithm until the
source-equivalence and complexity screens survive.

## Next discriminating test

Before implementation, verify the finite-horizon OS-POSG model match and derive
the HSVI state/belief and strategy-gadget representation with the query budget,
delayed queue, hidden root, and first-promotion payoff. Then register one small
development instance where both exact oracles complete. The pilot passes only if
it independently verifies the returned policies' risk and cost, captures the
recovery bracket, and reduces end-to-end runtime or memory while maintaining the
certified `epsilon+delta` cost gap. If the augmented-state search is larger than
the existing sequence-form LP, stop this solver as an implementation route and
keep it only as a baseline. No real-data access is authorized before G1–G3 pass.
