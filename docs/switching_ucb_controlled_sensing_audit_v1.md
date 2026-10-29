# UCB-controlled quickest detection: single-stream reduction audit

2026-10-28. **Status:** primary-source theorem and procedure scope checked from the 2026
preprint; this is a reduction boundary, not an exhaustive novelty audit or a method claim.

## Source and verified result

Huang, Gerogiannis, Bose and Veeravalli, [“Learning Where to Look: UCB-Driven Controlled
Sensing for Quickest Change Detection”](https://arxiv.org/abs/2603.28563), arXiv:2603.28563 (2026).
The model in Section II has multiple mutually independent streams with known pre/post-change
distributions. An unknown deterministic change time and unknown nonempty subset of streams may
be affected. The controller chooses one stream per time step and receives its observation
immediately. The stopping objective is Lorden worst-case expected delay subject to mean time to
false alarm at least `gamma`.

UCB-CuSum treats each selected stream's log-likelihood ratio as a reward, restarts UCB every `W`
observations, and accumulates a CuSum statistic. Theorem 1 states first-order asymptotic
optimality with threshold `log(gamma)` as `gamma,W` grow and `W=o(log gamma)`. PA-UCB-CuSum keeps
separate CuSum statistics by stream. The source states known pre/post distributions in the formal
model; the unknown-distribution extension is an empirical section. This is direct prior for
jointly selecting informative sensing channels and detecting a change.

## Paired-query reduction

ShiftLab's basic cell has one common-outcome stream: each query reveals the same `Y_s` used to
score both fixed policies. Its observation law does not depend on which model is deployed. Thus
the channel-selection part of UCB-CuSum collapses to `K=1`; the largest-LLR-arm acquisition
advantage is identically absent. Choosing whether/when to request that one stream remains a
separate sampling schedule problem.

The theorem does not transfer to ShiftLab's target. UCB-CuSum samples one stream at every active
step until stopping, has immediate observations, and constrains mean time to false alarm. The
target has a finite horizon and pathwise cap on total requests (including pending requests), fixed
release delay, query charges, repeated costed deployment switches, and probability of any false
promotion under a conditional-mean null. Those differences are not novelty evidence; they specify
the remaining reduction obligations.

## Consequence

Do not claim that UCB-style allocation among queried paired models is a novel contribution when a
single common outcome supplies both losses. The unresolved acquisition problem is *when to spend a
finite query right on the sole stream*, accounting for the change-time uncertainty, release delay,
remaining useful economic horizon and switching cost while preserving the stated global risk.
Standard sampling-control and quickest-detection work remains relevant to that timing question.
No algorithm, theorem-level separation, or efficacy result follows from this audit. Promotion
validity must remain separate from current-regime forecasts after a reversal.
