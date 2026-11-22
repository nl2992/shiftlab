# B=3 uniform-premium proof attempt

**Date:** 2026-11-11. **Scope:** one bounded analytic attempt following the user's amended acceptance range.
**Target:** a positive lower bound on `rho_Gamma(T)` uniform over the horizon for `B=3`, at least on an explicit
nonempty open parameter set with `t<1`. The concurrent certified `B=3`, `T=13..15` extension is separate and is
not used as proof evidence here. **Status:** no new uniform-in-T theorem proved; no counterexample found.

## 1. Model and available reduction

Use the symmetric stationary anti-persistent family from `MIXING_PREMIUM_THEOREM.md`: `r=2t-1 in (0,1)`,
`g=(1-2e)^2 in (0,1)`, prior `1/2`, symmetric emissions, delay `d`, query cost `c`, switch cost `k`, and budget
`B`. The target is `rho_Gamma = Gamma / VOI_IID`, with the paper's convention when the denominator is zero.

The strongest general reduction available in this attempt is Theorem M3. For any IID-feasible reference plan with
risk at least `alpha` and gain/risk ratio `zeta`, it gives

```text
Gamma >= alpha * (zeta - S')
rho_Gamma >= (zeta - S') / S_I
S' = max(H_empty^+, s_1^+, (s_0^+ + s_1^+)/2)
S_I = max(H_empty^+, s_0^+, s_1^+).
```

Here `s_y` is the best IID gain/risk slope of a continuation conditioned on the first released label being `y`,
and `H_empty` is the best unconditional-promotion gain. The proof uses the causal null which forces the first queried
label to zero and makes subsequent labels fair. Thus it controls only the first label's contribution to the
promotion constraint.

## 2. Exact comparison of two B=3 continuation witnesses

For `B=3`, `d=1`, `c=k=0`, the existing ledger gives the following `T -> infinity` values for two explicit
continuations (they are lower bounds on the respective optimal branch slopes, not upper bounds):

```text
A0 = Gbar_0^infinity + 2 v1
   = g r/(1-r) * (2+r)/(1+r)

A1 = g r/(1-r) + (1+g r) v1
   = g r/(1-r) * (3+g r)/2

v1 = g r/(2(1-r)).
```

The first is branch 0 followed by immediate promotion with the two remaining labels used without further
promotion-risk restriction. The second is a branch-1 continuation using the two-label pattern `(1,0)` at adjacent
query times, with the last label's value approached by placing it arbitrarily far later. Direct algebra proves

```text
A0 - A1 = g r/(1-r) * [1 - (1+g)r - g r^2] / [2(1+r)].
```

Consequently these *witness values* are ordered `A0>A1` whenever `g r^2 + (1+g)r < 1`; the inequality holds on
a nonempty open subset of `g,r in (0,1)` (for example, sufficiently small positive `r` for any fixed `g<1`).
This is a proved comparison of the two displayed plans only.

It does **not** establish `s_0>s_1`: both `A0` and `A1` are lower bounds on optimal branch slopes, so a third
continuation could raise either optimum and reverse the ordering. Nor does it bound `H_empty` or the denominator
`S_I`. Therefore this comparison cannot yet be inserted into M3 to obtain a positive lower bound.

## 3. Attempt to close the M3 relaxation

The natural sufficient conditions would be horizon-uniform upper bounds on `s_1` and `H_empty`, together with a
lower bound on a high-risk IID plan's `zeta`, such that `zeta>S'`. The B=2 proof obtains such bounds by enumerating
the three possible branch events after one remaining label (empty, all, or a singleton) and using the positive-part
geometric-series formula. At B=3, each first-label branch has two labels remaining. Its promotion event can be any
subset of four label histories, and the timing of the second query can depend on the first released label. The
corresponding event slope includes both the continuation value and the alternative's likelihood-ratio boost from
the second label. The B=2 enumeration does not extend by simply adding `v1` per unused label: the boost multiplies
the free continuation value (as already identified in §5 of `MIXING_PREMIUM_THEOREM.md`).

I considered using nulls `nu_j` that force the `j`th queried label to zero. These are valid causal nulls when the
query index is observable, but the first-label M3 proof does not supply the needed joint decomposition for an
arbitrary policy that re-times or skips later queries. In particular, the risk under `nu_2` is not just the mass of
one fixed IID label-pattern event when later query times depend on earlier outcomes. A multi-null bound would need
to retain this adaptive timing tree and its continuation gains; no valid reduction eliminating that tree was
derived in this bounded attempt.

The already-proved M2 bound, `VOI_X(T) <= alpha U_B`, only converts a lower bound on `Gamma/alpha` to a lower bound
on `rho_Gamma`; it does not produce such a lower bound. Existing M4 supplies one for B=2, but its two-label branch
calculus does not cover B=3.

## 4. Findings and unresolved obligations

- **PROVED (inherited, not reproved here):** M2 and M3 apply to B=3 under the symmetric stationary model and the
  stated causal-null regime.
- **PROVED (this attempt):** the algebraic difference `A0-A1` for the two explicit B=3 infinite-horizon branch
  witnesses is the expression in §2, and is positive on the stated open set.
- **CONJECTURED (not proved):** for fixed `B=3`, `d=1`, `c=k=0`, there is a nonempty open set of `t<1`, `e in
  (0,1/2)`, and `alpha in (0,1/2]` on which `rho_Gamma(T)` has a strictly positive lower bound for every sufficiently
  large horizon (and hence, after a finite-prefix argument, every admissible horizon with positive denominator).
  Finite-horizon certified data in the existing reports are consistent with this but cannot prove the limit.
- **FALSIFIED:** none. This attempt found neither a counterexample nor evidence that the premium vanishes.

To turn the witness comparison into a theorem, the next proof obligation is an exact upper bound on every two-label
branch event slope, uniform over adaptive query gaps and horizons, plus a compatible upper bound on `H_empty` and
`S_I`. Alternatively, construct and prove a multi-null dual certificate that covers the full adaptive timing tree.
The numerical extension to `T=13..15` can test the previously locked collapse screen, but it cannot discharge
these asymptotic proof obligations.

**Assessment:** the bounded attempt did not prove the amended positive milestone. Keep the research decision open
unless the separate certified extension reaches the locked NO-GO threshold or a later proof/review satisfies a
positive criterion. Do not interpret the failed closure attempt as evidence that the conjecture is false.
