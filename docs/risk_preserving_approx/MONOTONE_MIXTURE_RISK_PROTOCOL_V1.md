# Aggregate monotonicity versus branch-observing causal null

Registered 2026-10-29 before the exact arithmetic check. This is a two-branch
counterexample check, not a solver or efficacy comparison. No model data or seeds.

## Frozen construction

Use horizon `T=4`, hard query budget `B=3`, delay `d=1`, and an upfront private
coin selecting branch A or B with probability `1/2` each. Both branches keep the
incumbent deployed until event 4. At event 1, branch A requests a label and branch
B does not; the public query choice reveals the selected branch to the causal-null
opponent before the event-1 outcome is generated. Both branches request labels at
events 2 and 3. Branch A ignores the event-1 label and promotes at event 4 iff
`(Y_2,Y_3)=(0,1)`. Branch B promotes at event 4 iff `Y_2=1`. Thus every path uses
at most three requests and all labels used by the terminal decision are released
in time.

The null may choose each conditional success probability in `[0,1/2]` after seeing
the public branch and its full generated history. Compute (i) the average
promotion-event function over the two branches on the `(Y_2,Y_3)` tape, (ii) its
IID fair-coin expectation, and (iii) the exact full causal-null risk of the public
root mixture.

## Frozen pass/fail check

The marginal event table is expected to be `g(00)=0`,
`g(01)=g(10)=g(11)=1/2`, which is coordinatewise monotone and has IID risk `3/8`.
Because the branch is public before the tested labels are generated, the causal
null can use a branch-specific response: on A choose `p_2=0,p_3=1/2`, giving
risk `1/2`; on B choose `p_2=1/2`, also giving risk `1/2`. The mixture's exact
causal-null risk is therefore expected to be `1/2`, strictly above the IID value.

The check passes only if the exact enumerator returns all four table values, IID
risk `3/8`, branchwise risks `1/2`, and mixture causal-null risk `1/2`. This would
falsify replacement of the robust null by an IID row based solely on aggregate
monotonicity of randomized promotion probabilities. It does not invalidate the
fixed-pure-plan monotonicity lemma or an upfront mixture whose every branch is
individually monotone and risk-certified.
