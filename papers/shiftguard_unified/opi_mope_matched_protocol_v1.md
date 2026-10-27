# Matched OPI, MOPE, and fixed-horizon policy comparison v1

**Status:** frozen before execution on 2026-10-26.  
**Question:** On identical stationary logged-bandit streams, how do finite-class policy identification, a preselected candidate-vs-incumbent gate, and a fixed-horizon comparator trade off false escalation, selection/promotion probability, and stopping time?  
**Comparators:** Molitor OPI (2026), official MOPE gated deployment (pinned source), familywise fixed-horizon Hoeffding selection, and fixed-horizon Hoeffding candidate-vs-logger gate.

## Shared task contract

- One context-free binary-action stream with logger `h=(0.5,0.5)`, binary rewards, horizon `T=200`, and three finite target policies with action-1 probabilities `(0,0.5,1)`.
- Null: both action reward means are `0.5`; all three policies are equally optimal and the fixed candidate's value equals the logging policy's value.
- Alternative: action means are `(0.35,0.65)`; policy values are `(0.35,0.50,0.65)`. Action 1 is the unique best policy and its gain over the logging-policy incumbent is `0.15`.
- Use 1,000 IID replications for the null and 300 for the alternative. Generate common action/reward streams on CUDA where available, then feed identical streams to all methods.
- The OPI learner receives action, reward, known logger probabilities, fixed candidate class, and predictable constant `rhat=0.5`; true reward means and best policy are evaluator-only. Use the paper's bounded DR scores with `k=1` and `alpha/(2m)` for each one-sided endpoint.
- Official MOPE receives only `(w_t,R_t)` for the preregistered target policy `pi(A=1)=1` against the logger, where `w=pi(A|X)/h(A|X)∈{0,2}`. The target is fixed before data. Promote when the official lower confidence sequence first exceeds zero. Pin the reference implementation and use its numerical routine unchanged.
- The fixed-horizon candidate-vs-logger control uses the same score `Z=(w-1)R∈[-1,1]` and promotes at `T` only if `mean(Z) - 2 sqrt(log(1/alpha)/(2T)) > 0`.
- The fixed-horizon finite-class selector uses the same bounded DR lower/mirrored upper scores as OPI, known policy-specific score ranges, Bonferroni allocation `alpha/(2m)` over two tails and `m=3` policies, and chooses only if its final candidate set is a singleton.

## Endpoints and interpretation

For OPI, report any false optimal-policy elimination at any time under the all-tied null, unique-best stopping probability, correct final singleton, and censored stopping time. For MOPE and the matching one-sided Hoeffding gate, report null false-promotion rate, alternative promotion rate, and labels used. The two policy-selection methods and candidate-vs-logger gates have different decision targets; compare them on their own prespecified endpoints and do not rank them as if the estimands were identical. Report exact binomial intervals and the complete paired per-stream results.

This benchmark is synthetic, IID, stationary, and has immediate feedback. It does not validate real OBD timing, slate interactions, delayed labels, model adaptation, costs, or the integrated ShiftGuard system. A successful null calibration is empirical evidence for this design, not a replacement for theorem assumptions or proof.

