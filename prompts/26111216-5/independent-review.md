# Independent audit: explicit bounded-budget S-1 corollary

**Verdict: ACCEPT**, conditional on component theorems M1, M4, and M6–M9.

Corollary M10 correctly gives `rho_Gamma>=0.10` for every integer `1<=B<=6`, `T>=20`, on
`alpha=1/10`, `d=1`, `c=k=0`, `r in (1/200,1/100)`, `g in (2/5,1/2)`.

M1's B=1 bound is stronger than needed. Substituting `d=1`, `delta=2`, and zero costs into M4 gives the stated
B=2 expression. Its numerator is positive at the worst endpoint, decreases with r, and its denominator increases
with r; for fixed r the bound increases with T. At `r=1/100`, `T=20`, the exact endpoint is
`35349928571428571428571428571428557/215000000000000000000000000000000000`, strictly above `1/10`. The M6–M9
component lower bounds also exceed `1/10`, completing the finite union.

This matches S-1's explicit bounded-budget form with `Bbar=6`, `T0=20`, and an open parameter rectangle. The
reviewer cautions that calling `B<=6` “label-scarce” is interpretive unless a separate scarcity definition is given;
the corollary does not establish B>=7, growing-budget behavior, or other parameter regimes. This is a separate
same-family mathematical review, not external validation.
