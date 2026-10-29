# Risk frontier audit: an e-threshold is not the risk constraint

2026-10-28. Previous turn: progress (nonstationary reserve screen and latent-forward checks).
This audit takes precedence over interpretations that treat a fixed certificate engine as the
entire statistically admissible policy class. Historical numbers/protocols remain unchanged.

## Problem found before a shadow-price experiment

The goal requires a precisely specified statistical risk bound. The current nonstationary
contract's global null is E[Y_t|full event past and query choice]<=1/2; the desired bound is
P(any 0->1 promotion)<=alpha under this null. Requiring crossing of the **particular predictive
product chosen in the screens** is sufficient, not necessary, for this guarantee. This is not
an objection to e-processes generally: the alternative test below also has an e-representation.

The completed Bellman screens optimized only over actions admitted by a particular product
threshold. They are correctly described as gate-constrained optima. They are not optima over
all policies satisfying the error constraint. Likewise, the earlier one-step and fixed-depth
counterexamples prove failures *under the chosen gate*, not that statistical validity universally
requires those label bundles. This distinction was already present in the model definitions,
but it must now govern the next algorithm derivation and strongest-comparator choice.

## An equally error-controlled one-label policy

For 0<alpha<=1/2, request event 1 and observe Y_1 at the start of round 1+d. Independently draw
U uniform on [0,1]. If Y_1=1 and U<=2alpha, promote to 1 and hold through T; otherwise stay 0.
No later promotion or query occurs. It uses exactly one right, counted at request time, and
pays the same query/switch charges. If 1+d>T it never promotes.

Under every law in the declared global null,

    P(promotion) = 2alpha*P(Y_1=1) <= alpha.

This proof requires neither an IID null nor a correct alternative model. The only outcome
used is the requested label, released at the stated delay. The independent deployment coin
is part of the policy; randomization has not been prohibited by the research contract. This
is an elementary randomized test, not a proposed novel method or a current-benefit certificate.

If query decisions may also be randomized, the equivalent promotion distribution can be obtained
more cheaply: with independent probability 2alpha request the one label and promote iff it is
positive; otherwise request nothing and stay at 0. This still uses at most one label on every
path. It saves query cost on the inactive paths, rather than relaxing the hard cap. Its null
promotion probability is again <=alpha, including when the null mean bound is conditional on
the observed query coin. It is a standard risk-allocation construction, not our new method.

For this optional-query version, a test-supermartingale representation starts at wealth 1,
uses the independent coin to assign wealth 1/(2alpha) on active paths and zero otherwise,
then multiplies by 2Y_1 at label arrival on active paths. Wealth reaches exactly 1/alpha on
promotion. The first step is a fair lottery and the outcome step has null conditional expectation
<=1. Thus the method still fits testing by betting; it differs from freezing predictive p=3/4.

## Exact economic comparison in a stationary subcase

Freeze T=20,d=2,c=1/100,k=1/10,alpha=1/10. The working alternative prior puts equal mass
on stationary theta=1/4 and theta=3/4, with losses Y_t and 1-Y_t. This has the same global
conditional null as above, stronger than the simple theta=1/4 null used in the earlier
three-label toy screen. Do not pool those two different guarantee settings.

The one-label randomized policy has P(promotion)=alpha under the working prior. For any
future t>1, E[(2theta-1)*Y_1]=1/8. Its expected net improvement over continuing is therefore

    (T-d)*alpha/4 - alpha*k - c = 43/100,

so expected total cost is 957/100=9.57 rather than 10. Under the IID boundary null theta=1/2,
promotion probability is exactly alpha. All parameters and outcomes are shared with the
comparison below; there is no expected-budget relaxation or early feedback.

The optional-query version has the same promotion and decision-loss distribution but expected
query cost 2alpha*c. Its expected net cost is 4781/500=9.562. Only 1/5 of paths request a label,
and no path requests more than one. No optimality over all alpha-safe sequential policies is
claimed for either construction.

For contrast, the standard fixed predictive bet p_bet=3/4 against the same mean-1/2 null
has factors 3/2 (positive) and 1/2 (negative). Threshold 10 cannot be attained with at most
five labels, because (3/2)^5<10. Every policy *restricted to that gate* stays at 0 for B<=5.
With positive query cost its optimum is to request nothing and cost 10. The randomized
one-label policy is thus a strictly better admissible policy at exactly the same alpha and
any hard cap B in {1,...,5}. It proves the threshold class is not the whole safe frontier.

The one-label policy is not claimed to dominate all multi-label tests or the best gate policy
when more labels are available. Nor does it certify profit after arbitrary regime changes.
It is an indispensable fairness comparator for an objective allowing randomized decisions.

## Registered exact verification, before execution

Implement `scripts/check_switching_risk_frontier.py` to enumerate the one queried outcome,
the deployment-coin probabilities and fixed theta in {0,1/4,1/2,3/4,1}; compute all costs with
rational arithmetic. Check error<=alpha at theta<=1/2, exactly one request, no gain before
availability, prior expected cost=957/100 and (3/2)^5<10<=(3/2)^6. Also verify the analytical
formula on fixed T in {8,20}, d in {1,2}, alpha in {1/20,1/10}, with the same c,k; report all
eight formula checks. This is mathematical verification, not efficacy confirmation or novelty.

## Research decision and revised next step

Hold the proposed shadow-price/label-bundle experiment: a hard-versus-expected-budget
duality gap within a fixed e-gate could be an engine-specific fact, not the intended learning
problem's intrinsic frontier. Retain the existing within-gate results with their scoped meaning.

For the next method, explicitly choose whether the target class is all alpha-safe policies or
a prescribed certificate engine. The original objective favors the former; do not impose the
latter merely because it makes a mechanism easier to justify. A stronger small-model reference
should optimize under the actual null-probability constraint, including randomization, rather
than force every decision through one sufficient e-boundary. Such risk-constrained sequential
design/POMDP optimization is itself established territory; it supplies a comparator obligation,
not an unoccupied novelty claim. Its multi-null and nonstationary extensions need source-level
and mathematical work. A new acquisition rule still needs a distinct insight and provable gain.

## Verification and interpretation correction

All five fixed-theta checks, eight exact formula checks and the no-arrival boundary passed.
The optional-query extension was then checked by separately enumerating its active/inactive
coin, queried outcome and switch. Its cost was exactly 4781/500; its expected query count
was 1/5 and its pathwise cap remained one. The fair-coin wealth step and outcome step each
had null expected wealth at most their predecessor. Ruff, formatting and Git whitespace checks
passed. Output includes a source hash. This is not an independent proof review or a new method.

The general representation of a level-alpha test as an all-or-nothing e-variable is already
discussed in [Wang and Ramdas, FDR control with e-values](https://academic.oup.com/jrsssb/article/84/3/822/7056146)
and [Grunwald, Beyond Neyman–Pearson](https://pmc.ncbi.nlm.nih.gov/articles/PMC11441548/).
The relevant representation passages were inspected. No novelty is claimed from randomization,
this example or choosing a different e-variable.

The older numerical screens remain valid within their declared gates. Their implications must
now be narrowed: cold-start and finite-depth failures are sufficient-engine failures, not an
intrinsic label requirement for all valid switching policies. Their full Bellman results are
within-gate optima, not the actual alpha-safe frontier. The original all-policy budget/delay
coverage lower bound remains unaffected. The next candidate must compare against better test
design or calibrated randomized decisions, in addition to optimizing acquisition schedules.
