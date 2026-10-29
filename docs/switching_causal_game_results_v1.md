# Causal-game reference: completed development calculation

2026-10-28. The registered T=5,B=2,d=2 cell completed with 2,586 tree nodes, 1,509 learner
sequences and 71 opponent sequences. HiGHS reported objective 2.3565184 with zero reported
flow residual and inequality violation. The recovered rational behavioral policy independently
evaluated to cost 184103/78125, with worst causal-null promotion risk exactly 1/10. No calibration
mixture was needed. This is a numerical optimum plus exact recovered-policy evaluation, not an
exact rational optimality certificate.

Cost decomposition: decision 364381/156250, query 1/125, switching 103/6250. Expected queries
are 4/5, with at most two on every path; expected switches are 103/625. Continuing costs 5/2.
These are known-model tiny-horizon reference values, not meaningful efficacy evidence or
dynamic regret. The saved full behavior policy includes off-path decisions and is not a method
nominated for novelty or scalability.

## Source-read correction

The 1996 authors' PDF linked in the registration timed out in both the browser and direct
retrieval. It was not read. The accessible primary fallback was
[Koller and Pfeffer, IJCAI 1995, Section 4](https://ijcai.org/proceedings/1995/0153.pdf), which
describes sequence realization weights, chance-weighted payoff matrices, flow constraints and
the perfect-recall requirement; those passages and Theorem 4.1 were inspected. The reference
LP is our application of that established representation and standard LP duality. No new
sequence-form technique, independently verified game-theory proof or exhaustive novelty audit
is claimed. Preserve this distinction from the pre-execution link request.

## Registered post-solve verification and interpretation

Before additional evaluation, register the following diagnostic, keeping this same cell fixed.
The policy suggests a simple description: independently activate with probability 2/5; on
activation query events 1 and 2, promote at round 4 iff both labels are positive, and otherwise
stay at 0. Hold any promoted action through round 5. Evaluate this explicit rule separately and
compare all five expected metrics and worst causal-null risk with the recovered policy. This
is a post-solve simplification, not a preselected comparator or an independent efficacy test.
If it agrees, report that a standard randomized fixed-cohort rule reaches the returned value;
do not attribute a joint-acquisition/rollback advantage to the solver.

Also verify the recovered policy by explicit enumeration of all 2^(2T+1)=2,048 hidden
state/outcome worlds. Generate S0,...,ST with exact transition weights and all Y1,...,YT with
exact emission weights. Feed only requested/released labels to learner policy lookup. Accumulate
realized decision losses, query and switch charges, and counts. This evaluator must not call
the posterior-filtering recursion used by the optimization builder. Compare its exact metrics
to the filtered forward evaluator and saved output. This strengthens verification of the same
registered calculation; it is not another empirical scenario or solver run.

Record results and hashes in `outputs/switching_causal_game_v1/verification.json`. Preserve
the main output's pre-execution protocol hash; later interpretation is recorded here. Continue
only if the causal information boundary, expected values and hard cap all agree. The full
novel algorithm, new theorem, matched efficacy and real-data goals remain open.

## Verification completed and next decision

All 2,048 explicit hidden-state/outcome worlds reproduced every saved expected metric exactly.
The separately evaluated fixed-cohort simplification also matched all five metrics and risk
1/10 exactly. It activates with probability 2/5, queries twice only on active paths, and switches
once only after two positive labels. There is no rollback in that simplified policy. Thus the
case establishes neither an adaptive acquisition advantage nor a reversal advantage. It does
show that a conventional randomized cohort test can attain the value returned by a much more
general planner in this cell.

The targeted suite passed 11 tests, including the analytic optima, timing/causal-null checks,
hard-cap reservation, resource stop and separate charging for promotion and rollback. Ruff and
diff checks passed. The main output records the code/test hashes at execution; a later test
addition checks reversal charges and does not change the solver or its policy. The verification
script's current hash and the saved policy hash are in `verification.json`. Primary-source cache
provenance is in `switching_source_manifest_v5.json`.

Decision: retain the finite-game solver as a strong, computationally expensive known-model
reference, not the contribution. Stop this cell here. The next mechanism must have a proved
advantage attributable to contingent information/action decisions beyond a randomized cohort
rule or generic constrained planning; source audit and theory must motivate any new evaluation
family before more scenario runs. No methodological, confirmatory or real-data gate is passed.
