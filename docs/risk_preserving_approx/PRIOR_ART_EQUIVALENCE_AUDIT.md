# Prior-art equivalence audit: initial source-level boundary

2026-10-29. This is a focused initial audit, not a complete novelty determination.
Original repo source audits remain unchanged. Read primary passages listed below;
absence of an identical statement does not prove a result novel.

| Source and inspected scope | Shared structure | Difference / remaining reduction | Status |
| --- | --- | --- | --- |
| [Kara and Yüksel, JMLR 2022](https://jmlr.org/papers/volume23/20-1152/20-1152.pdf), Theorems 16–17 and surrounding assumptions | Finite-memory approximation and explicit near-optimality bounds for known-model POMDPs | Discounted single-model objective and filter stability do not directly bound a separate causal-null worst-case event. Need prove whether an augmented hidden-root game plus constraint recovery transfers the claimed joint error/rate. | UNRESOLVED — EXACT REDUCTION REQUIRED |
| [Cubuktepe et al., AAAI 2021](https://cdn.aaai.org/ojs/17401/17401-13-20895-1-2-20210518.pdf), model and Algorithm 1 verification discussion | Uncertain partially observed model, finite-state controller and robust verification; paper explicitly uses exact verification to check the synthesized specification | An exact history-augmented safety model exists; the two-law objective can be encoded with mode/cost augmentation, but a uniform bound against the unrestricted oracle and improved compact scaling are not established by this comparison. Need model-match and complexity reduction. | UNRESOLVED — EXACT REDUCTION REQUIRED |
| [Horák et al., one-sided POSGs](https://arxiv.org/abs/2010.11243), as mapped in `switching_lagrangian_posg_reduction_v1.md` | Hidden-root scalarization maps the finite game to established strategy composition and value recursion | Shared policy, asymmetric information and two-law objective alone do not establish a new method; recovery of a constrained optimizer and scalable compression require additional work. The current checkpoint checked the source identity and existing reduction, not the full proof independently. | Generic scalarized representation: established equivalence in repository; compact approximation: unresolved |
| Khonji, Jasour and Williams, IJCAI 2019, as audited in `switching_ccpomdp_approximation_audit_v1.md` | Finite-horizon chance constraint and approximation | Existing source audit describes a fixed-law, constant-horizon result. A causal-null family can be expanded into multiple fixed null constraints but may be exponential; a one-constraint FPTAS cannot simply be invoked. Recheck the primary proof before claiming a separation. | UNRESOLVED — EXACT REDUCTION REQUIRED |

The safety-repair lemma in `PROBLEM_AND_THEOREM_TARGET.md` is elementary mixture
algebra, not a methodological novelty claim. It is useful only if a separate
construction supplies a uniformly valid small risk excess, a value bound against
V*, and favorable end-to-end complexity. The posterior-alias counterexample
rejects the posterior-only representation, not all compact controllers.

A candidate-specific audit must fill in shared/different assumptions, necessity
of each difference, proof adaptation and the missing lemma; only then decide
proved equivalent, proved distinct, unresolved or falsified. Candidate A has not
yet provided that theorem or representation.

## Candidate G: scalarized Bellman DP for the IID relaxation (2026-10-29)

For a fixed multiplier, the IID-relaxed objective is a scalar reward on a finite
POMDP whose belief includes the hidden alternative-versus-IID root mode, regime,
and pending labels. Time, remaining query rights, deployment and the existing
exact post-promotion alternative continuation complete the state. This is a
standard constrained-POMDP Lagrangian/dynamic-programming reduction, not a new
recurrence. Isom, Meyn & Braatz give exact dynamic-programming updates for
constrained POMDPs ([AAAI 2008](https://cdn.aaai.org/AAAI/2008/AAAI08-046.pdf));
Kim et al. give exact and approximate dynamic programming for randomized
constrained-POMDP policies ([IJCAI 2011](https://ijcai.org/proceedings/2011/329)).

The ShiftLab model-specific implementation retained the standard null-model
limitation: it optimized IID risk, not the full causal-null supremum, so exact
null verification and root safety repair remained mandatory. A fixed-grid root
mixture exactly matched the known Candidate B/reference cost and risk and beat
the best calendar cost on one synthetic instance. Its 60.7995-second end-to-end
time failed the preregistered 29.0069-second threshold and was slower than the
58.0139-second decomposed reference. The reachable belief graph also had the
same 4,867 decision states as the public-history tree. Thus the candidate has
neither a source-level novelty delta nor a measured end-to-end computational
advantage. Close it as a lead; retain the code/result as a comparator. See the
exact audit, frozen screen protocol and result artifact for complete hashes and
metrics.

## Candidate G: scalarized Bellman DP for the IID relaxation (2026-10-29)

For a fixed multiplier, the IID-relaxed objective is a scalar reward on a finite
POMDP whose belief includes the hidden alternative-versus-IID root mode, regime,
and pending labels. Time, remaining query rights, deployment and the existing
exact post-promotion alternative continuation complete the state. This is a
standard constrained-POMDP Lagrangian/dynamic-programming reduction, not a new
recurrence. Isom, Meyn & Braatz give exact dynamic-programming updates for
constrained POMDPs ([AAAI 2008](https://cdn.aaai.org/AAAI/2008/AAAI08-046.pdf));
Kim et al. give exact and approximate dynamic programming for randomized
constrained-POMDP policies ([IJCAI 2011](https://ijcai.org/proceedings/2011/329)).

The ShiftLab model-specific implementation retained the standard null-model
limitation: it optimized IID risk, not the full causal-null supremum, so exact
null verification and root safety repair remained mandatory. A fixed-grid root
mixture exactly matched the known Candidate B/reference cost and risk and beat
the best calendar cost on one synthetic instance. Its 60.7995-second end-to-end
time failed the preregistered 29.0069-second threshold and was slower than the
58.0139-second decomposed reference. The reachable belief graph also had the
same 4,867 decision states as the public-history tree. Thus the candidate has
neither a source-level novelty delta nor a measured end-to-end computational
advantage. Close it as a lead; retain the code/result as a comparator. See the
exact audit, frozen screen protocol and result artifact for complete hashes and
metrics.

## Candidate B: IID relaxation plus exact causal-null verification (2026-10-29)

The tested pipeline minimizes alternative cost subject to learner flow constraints
and one IID fair-label chance constraint, then exactly verifies full adaptive
causal-null risk and repairs any unsafe policy by an upfront lottery with the
never-promote plan. Its rational dual supplies a lower bound and the repaired
policy supplies a feasible upper bound. This is a standard primal/dual relaxation
and verification pattern. The branch-specific content is an exact lower/upper
interval for this two-law ShiftLab game, not a new general optimization principle.

| Source | Exact relevant result | Candidate relation | Status |
| --- | --- | --- | --- |
| Khonji, Jasour & Williams, IJCAI 2019, Theorem 5.4 / Corollary 5.5 | FPTAS for constant-horizon constrained and chance-constrained POMDP via And-Or / precedence-knapsack formulation; policy approximation and complexity assume fixed horizon and a single known model. [Primary paper](https://www.ijcai.org/proceedings/2019/0775.pdf) | The fixed IID boundary fits the single-law chance-constrained form after a finite-horizon encoding. The target supremum ranges over causal responses that see pending outcomes; encoding all response constraints is not the single-constraint reduction used here and may be exponential. No transfer of the FPTAS to the two-law robust target is proved. | UNRESOLVED — EXACT REDUCTION REQUIRED; no novelty established for relaxation/repair |
| Cubuktepe et al., AAAI 2021, robust FSC synthesis and verification | Approximate synthesis for uncertain POMDPs is followed by exact robust verification of the fixed policy. [Primary paper](https://cdn.aaai.org/ojs/17401/17401-13-20895-1-2-20210518.pdf) | Confirms that separating candidate synthesis from exact robust verification is established. Their finite-state-controller and transition-uncertainty model does not provide the current hard query budget, two-law economic continuation, or this exact dual interval. This is a model-specific engineering delta, not an established new theorem. | Exact guarantee not equivalent; algorithmic novelty remains unestablished |
| ShiftLab sequence-form duality and exact first-promotion decomposition | Full causal-null response is a one-sided partially observable game; decomposition separates first-promotion risk from alternative continuation. | IID relaxation lower-bound direction and root-mixture repair are elementary. T=10 branchwise monotonicity is a coupling certificate for the returned policy, not a compact optimizer. | PROVED for saved finite results; no general approximation complexity |

The T=8 and T=10 experiments return a policy with the same exact cost as the
robust reference and beat calendar/cap/gate baselines in the low-persistence
cells. At T=10 the pipeline is slower end to end and has no measured memory
advantage over the reference. Thus no computational or novelty claim is
established. Retain the exact certificate as a candidate-generation diagnostic;
continue to Candidate A or a structurally distinct Candidate C before any
real-data gate.

## Candidate C: universal quotient of causal-null response histories (2026-10-29)

The tested proposal maps histories with the same time, query budget, deployment,
pending outcomes and alternative belief to a common state, then asks that this
state preserve every full-history null response kernel. The result is a
strategy-independent quotient lower bound, not a risk/value approximation
lower bound.

| Source | Closest established result | Shared assumptions / mechanism | Difference and remaining scope | Status |
| --- | --- | --- | --- | --- |
| Rabin & Scott (1959), *Finite Automata and Their Decision Problems*, Theorem 2 / Corollary 2.1 ([primary PDF](https://www.cs.miami.edu/home/burt/learning/csc427.222/docs/rabin-scott.pdf)) | Myhill–Nerode continuation equivalence characterizes the minimum states of deterministic automata | Distinct histories are separated by a continuation that produces different outputs; finite state maps must identify equivalent histories | We distinguish conditional Bernoulli response kernels, with a one-step separation of 0 versus 1/2. This is an elementary application of the same state-distinguishability principle, not a new automata result. | Equivalent proof principle; no method novelty |
| Horák et al. (2020), *Solving Zero-Sum One-Sided Partially Observable Stochastic Games* ([primary paper](https://arxiv.org/abs/2010.11243), §§6–7, §10 Example 10.1) | Strategy composition/value recursion; explicit example where belief is insufficient for the imperfect-information player | Asymmetric information and history-dependent strategy selection in finite games | Their work supplies approximate game-value machinery, while our statement is a finite conditional-kernel quotient bound; it does not establish a bound on robust policy value or runtime. | Adjacent prior art; no algorithmic novelty |
| Chatterjee, Doyen & Henzinger (2011), *Partial-Observation Stochastic Games: How to Win when Belief Fails* ([primary paper](https://arxiv.org/abs/1107.2141), §3, Theorem 3.1) | Belief insufficiency and memory bounds for qualitative one-sided games | Imperfect observation with an opponent that has full observation | Different reachability objective and strategy assumptions; it is background for memory requirements, not a direct theorem for quantitative causal-risk optimization. | Related but not an equivalence proof |

**Conclusion:** the quotient theorem is a proved diagnostic no-go only for
uniform, strategy-independent preservation of every conditional null kernel.
The final-query continuation's robust risk supremum is 1/2 at both histories,
so the witness gives no robust-risk or economic-value separation and need not be
alpha-safe. It does not rule out null-specific abstractions, direct robust
optimization, implicit separation, or policy-specific approximation. Its state
count is not a runtime lower bound; for fixed `q`, `binom(T-2,q)` is polynomial
in T. Full scope and proof are in
`CANDIDATE_C_RESPONSE_QUOTIENT_LOWER_BOUND_V1.md`.
