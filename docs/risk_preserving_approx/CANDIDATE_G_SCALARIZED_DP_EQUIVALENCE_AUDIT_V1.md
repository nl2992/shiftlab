# Candidate G scalarized Bellman DP: source-equivalence audit

**Status:** `PROVED — STANDARD REDUCTION`; no method novelty identified.
**Decision:** allow one bounded end-to-end runtime/utility screen only. Treat the
implementation as a comparator unless that screen demonstrates a material,
reproducible computational advantage while retaining exact robust-risk
feasibility and the synthetic utility win.

## Model being reduced

Candidate B optimizes alternative expected cost subject to promotion risk under
the fixed IID fair-label null. Write its finite sequence-form LP as

\[
  \min_{x\in X} c^\top x
  \quad\text{s.t.}\quad r_{\rm iid}^\top x\le\alpha,
\]

where `X` is the learner realization-plan flow polytope with the hard query cap,
and `r_iid` is the first-promotion event probability under IID fair queried
labels. For any multiplier `lambda >= 0`, the Lagrangian subproblem is

\[
  \min_{x\in X}\{c^\top x+\lambda r_{\rm iid}^\top x\}.
\]

The finite-horizon state for this *relaxed single-law* problem is event time,
remaining requests, the alternative regime/pending-label belief, the IID-versus-
alternative hidden-root belief, and deployment status. A promotion contributes
the IID-mode event penalty and the alternative-mode post-promotion continuation
value. Request charges occur at request time; observations enter only on their
registered release events. For a fixed multiplier this is an ordinary finite
POMDP scalar-reward Bellman problem. Each solution gives a supporting point of
the cost/risk attainable set; randomization between policies is needed to
recover a constrained optimum at a risk boundary.

This exactly matches established constrained-POMDP dynamic programming in
structure. Isom, Meyn & Braatz describe exact dynamic-programming updates for
constrained POMDPs with objective and constraint valuations
([AAAI 2008](https://cdn.aaai.org/AAAI/2008/AAAI08-046.pdf)). Kim et al. describe
exact and approximate dynamic-programming methods for randomized optimal
constrained-POMDP policies, with exact updates requiring a minimax QCP
([IJCAI 2011](https://ijcai.org/proceedings/2011/329)). Candidate G adds a
ShiftLab-specific delayed-label state and hands off post-promotion continuation
to the existing exact DP; neither change alters the generic reduction.

## Scope boundary and guarantees

The recurrence optimizes the IID relaxation, not the original supremum over
history-adaptive causal nulls. For any fixed `lambda`, its scalarized optimum
provides a lower bound on the IID-constrained optimum after subtracting
`lambda*alpha`; it does not itself provide a full-null feasible policy or a
nontrivial value bound for the original robust problem. Any returned policy
still requires exact full-history null verification. If it is unsafe, the
existing never-promote root lottery is a safety repair, and its economic cost
must be included in the comparison. This is the existing Candidate B pattern,
not a new theorem.

The exact belief graph has 4,867 decision states, equal to the 4,867 public
history states on the registered `T=10, B=4, d=2` screen; its graph build took
0.340 seconds. Thus there is no state-compression delta. The sequence LP has
13,421 learner variables. A Bellman pass may reduce optimization overhead, but
that is an empirical implementation hypothesis, not a complexity improvement
proved by this graph count.

## G1 decision

The mathematical method is source-equivalent. The only remaining possible
delta is end-to-end computation on this instance. Proceed under
`CANDIDATE_G_SCALARIZED_DP_SCREEN_PROTOCOL_V1.md` only because the recorded
Candidate B end-to-end runtime is 114.845 seconds and the decomposed exact
reference took 58.014 seconds, leaving a measurable comparator. The test must
include graph construction, multiplier search, policy extraction, exact
alternative-cost evaluation, full causal-null risk evaluation and any safety
repair. A speedup on the scalarized recursion alone does not pass.

The method is closed if it fails the registered runtime or robust-feasible
utility gate. A pass would justify retaining an efficient implementation
baseline and considering broader candidate work; it would not by itself
establish a novel method, a general runtime theorem, a multi-instance result,
or real-data evidence.
