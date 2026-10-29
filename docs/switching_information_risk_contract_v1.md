# Budgeted delayed switching: information and risk contract v1

**Status:** development contract, 2026-10-29. This is a scoped problem definition, not a validated
novelty claim, algorithm, theorem, or confirmatory protocol. It is intended to close ambiguity in
G1 before any new solver or efficacy study.

## Environment and event order

There are two frozen predictors/actions, incumbent 0 and challenger 1, over events `t=1,...,T`.
For each event an evaluator can eventually observe a bounded paired loss difference
`X_t = loss_0,t - loss_1,t` in `[-1,1]`; positive values favor the challenger. The label is requested
before it is observed, costs `c_t >= 0`, and is released exactly `d` events later. One query may be
requested per event and a pathwise hard cap requires `sum_t Q_t <= B`, counting labels still
pending. The action `A_t` and query `Q_t` are predictable from covariates, past actions/queries,
and labels released by the start of event t. The event order is: receive due labels; update state;
choose action/query; incur that event's decision utility and query charge; enqueue queried label;
release it at the fixed delay. Querying does not affect the paired losses or arrival process.

The current-regime benefit forecast is `mu_t = E[X_t | F_{t-1}]`. Gross decision utility is
`(A_t-0) X_t`; net utility subtracts query charges and `k_t 1{A_t != A_{t-1}}`. Evaluator-only
paired losses may score either frozen predictor on the same event. This is a predictive-loss proxy;
it does not identify trading profit, market impact, or action-dependent outcomes. Those require a
separate deployment design and data contract.

## Information, risk, and comparator

The learner observes covariates and released queried outcomes, never hidden regime state or
unreleased labels. Latent benefit may reverse; no stationarity or persistence is implicit. The
hard safety event under consideration is `F = {there exists a promotion time t with mu_t <= h}`
for a declared economic hurdle `h >= 0`. This is a current-value false-promotion event, distinct
from the historical test-epoch null `E[X_t | F_{t-1}] <= h` throughout an evidence epoch. An
anytime-valid e-process under the epoch null does not by itself control `P(F)` after an unmodeled
reversal and must never be described as doing so. Before a method can claim current-value safety,
it must specify a persistence/transition model or obtain contemporaneous information sufficient to
certify `mu_t`; otherwise it may claim only test-epoch false-promotion control and must separately
measure post-reversal exposure/loss.

Primary utility comparator: the best predictable two-action switching policy in a declared class
with at most `S` switches, the same per-switch penalty, and the same initial action, but no query
budget or information restriction only if it is explicitly labeled an evaluator upper bound. The
operational comparator must be learner-feasible, obey the same `B,d,c,k` and observable filtration,
and use a specified acquisition policy. Report both separately. Decision regret is net-cost
excess, including comparator query cost if it queries; no free clairvoyance or uncharged switches.
The baseline and candidate share the identical potential-loss stream, timing, random seeds, budget,
fees, and risk definition.

## Candidate method requirements and nonclaims

A candidate may jointly allocate queries and switching, but must state whether its certificate is
for (i) the test-epoch conditional null, or (ii) current-value false promotion. It must charge each
query at request time, reserve budget for pending requests, and log current-regime estimates
separately from cumulative evidence. Reversal evaluation reports detection/rollback delay and
loss accumulated before rollback; rollback does not retroactively make a promotion valid.

The exact finite causal-game sequence-form LP in `src/shiftlab/dive/causal_switching_game.py` is
the small-instance oracle. Its null is a worst-case event-time conditional Bernoulli response
process and its objective is known-HMM expected loss plus fees. It is finite-horizon and numerically
optimized; recovered policies receive separate exact risk verification. It is a reference, not a
scalable candidate or current-value false-switch guarantee.

## Source-level novelty boundary

Prabhu et al., “Sequential Multi-Hypothesis Testing in Multi-Armed Bandit Problems,” IEEE TIT 68(7),
2022, [IEEE Xplore](https://ieeexplore.ieee.org/document/9734025/) and [arXiv:2007.12961](https://arxiv.org/abs/2007.12961),
already combine adaptive sensing, switching cost, a false-detection constraint, a lower bound and
an asymptotically optimal sequential policy for unknown parameters in vector exponential families.
Therefore adaptive sampling + switching cost + false-alarm control + a sequential likelihood rule
is not a novelty delta. That paper's stated setup observes one arm each round and stops on a fixed
hypothesis decision; the ShiftLab target additionally requires a hard pathwise query cap, delayed
feedback, ongoing deployment, possible recurrent reversals, and a distinct current-value objective.
These differences identify a comparator contract, not an unoccupied gap. Audit the paper's exact
assumptions and theorem before making a narrower claim.

## G1 decision

G1 remains open. The only acceptable next candidate must provide a source-audited delta and a
nontrivial theorem or counterexample for the above information structure, with separate bounds for
statistical risk and economic regret. The method must beat the strongest equally informed scalable
baseline on a registered synthetic family and remain below the exact sequence-form oracle cost on
small cells. Current-value safety cannot be borrowed from historical promotion validity. G2-G5
remain held; no confirmatory or real-data study is authorized by this contract alone.
