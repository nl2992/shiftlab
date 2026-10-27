# One-step Certification Exponent comparator protocol v1

**Status:** frozen before running the registered comparison.  
**Source:** Wang, *The Certification Exponent: Instance-Optimal Sequential Certification of Policy Improvement from History-Dependent Logs*, arXiv:2610.24345v1 (2026-10-17), §§3–5 and Algorithm 1. This is a preprint, not a peer-reviewed publication.  
**Question:** Under an IID, context-free, two-action logged-bandit contract, does the paper's projected plug-in Kelly certifier provide a useful source-faithful Q2 comparator to the pinned MOPE gate and the fixed-horizon bounded-score gate?

## Mathematical restriction

Each episode consists of one action `A_t ~ μ=(1/2,1/2)` and one binary reward `R_t∈{0,1}`. The target policy is fixed before evaluation and deterministically chooses action 1. For action-1 target and logger, define

\[
X_t=\left(\frac{\pi(A_t)}{\mu(A_t)}-1\right)R_t
 = \begin{cases}R_t,&A_t=1,\\-R_t,&A_t=0.\end{cases}
\]

The value improvement is `Δ=E[X]=(θ_1−θ_0)/2`. The null is `θ_1≤θ_0`. The action-fair bet has one free coordinate `h`, taking `+h` on the target action and `−h` on the other action. Thus the full-tree bet is `1+λX+h(2A−1)` for target action 1, with `λ≥0` and leafwise nonnegativity on all four action/reward leaves. Equivalently, `−1≤h≤1` and `−1≤λ+h≤1`. This specializes the paper's `1+λX+Bν` construction; it is not the history-dependent tree or scalable cushion algorithm.

At refit times `ceil(1.15^k)` (`k≥1`), the learner projects the empirical episode law onto the action-neutral family by fixing the logger's action probabilities and estimating each action's Bernoulli reward conditional. It maximizes projected expected log wealth over the feasible set. Before both action arms have appeared, the adaptation uses the trivial bet `(λ,h)=(0,0)`; this conservative warm-up handles an undefined empirical conditional. At event `t`, it uses the predictable shrinkage `s_t=1−t^{-1/2}` and multiplies wealth by `1+s_t(λX_t+h(2A_t−1))`. Certification occurs at wealth `1/α`, with `α=0.05`.

The online rule sees only prior logged actions and rewards, known propensities, and the current completed episode. Reward means and the scenario label are evaluator-only. Full four-leaf feasibility is checked whether or not a leaf has been observed.

## Frozen comparison

- **Projected Kelly adaptation:** implementation in `src/shiftlab/dive/certification_exponent_one_step.py`; use the protocol above.
- **MOPE:** unmodified `wealth_lb_gd` from `tmp/mope_reference` at commit `a4b8584b622f3a8296932568c520c1bb3e1957f0`; inputs are `(w,R)` with `w=2` when `A=1`, else `0`; known bounds `[0,2]`; one-sided `α=0.05`.
- **Fixed horizon:** at `T=200`, certify only if `mean(X)−2 sqrt(log(1/α)/(2T))>0`. This is not an anytime-valid comparator.
- **Shared streams:** one uniform two-action logger and binary rewards, horizon 200; use the same generated stream for every method. Generate streams on CUDA when available; use CPU for the tiny convex fit and pinned MOPE NumPy/SciPy implementation.
- **Null:** `θ_0=θ_1=0.5`, 1,000 independent streams.
- **Alternative:** `θ_0=0.35, θ_1=0.65`, 300 independent streams.
- **Seeds:** null `101026`, alternative `202026`; use the repository's fixed CUDA stream generator in the dedicated runner. No post-hoc changes to endpoints, target, seed ranges, or horizon.

## Endpoints

For the null, report false certification by horizon with exact two-sided 95% Clopper–Pearson intervals. For the alternative, report certification probability and exact interval, mean/median certification event with censored time `T+1`, and the paired difference in certification indicators against MOPE. For all methods report empty/inverted MOPE paths, mean final e-process wealth where meaningful, and the fixed-horizon decision. Report complete per-stream outputs and hashes. Do not infer superiority from overlapping or unadjusted comparisons; adjust the single prespecified paired Kelly-versus-MOPE promotion contrast.

## Validity boundary and stopping rule

The paper's result assumes the known logger, the declared null class, bounded episode reward, and episodes satisfying its sampling/environment assumptions. The experiment evaluates only IID stationary Bernoulli streams; it is a source-faithful one-step restriction plus the stated warm-up implementation detail. It does not validate OBD's unknown user/slate dependence, feature timing, or click-release timing. It says nothing about delayed feedback, candidate selection after observing the same stream, contextual logging, multistep histories, or business utility. Stop after one clean run and independent artifact reconstruction. If calibration or numerical checks fail, diagnose the failure without tuning the registered primary comparison.

## Provenance

The source-level interpretation is recorded in `certification_exponent_fidelity_audit.md`. The protocol is frozen before its runner and experiment outputs are created. The adaptation is a baseline implementation, not a new ShiftLab method or novelty claim.
