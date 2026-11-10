# 03E Dual-use labels: design and exact null statements (kill-test stage)

Status 2026-11-09: kill test run; verdict STOP (see E_RESULTS.md). Code: src/shiftlab/paper3/dualuse/{sim,jpilot}.py.

## Setting
Fixed incumbent f0; challenger version g_t (logistic regression, minibatch SGD every m labels) is a function of labels
released before t. Z_t = l0_t - l_{g_{t-1}}(t) in [-1,1] (0-1 loss). Evidence E_t = mean_j prod_{s<=t}(1+lam_j Z_s),
lam_j in {.05,...,.5} fixed (mixture of predictable betting martingales). Promote at first E_t >= 1/alpha.

## Null statements (which test controls what)
- N_round (per-round predictable-version null): E[Z_t | F_{t-1}] <= 0 for all t, F_{t-1} = all (x,y) before t, g_{t-1} in F_{t-1}.
  Under N_round, E_t is a nonnegative supermartingale for ANY retraining schedule on the same labels (train after test), so by Ville
  P(exists t: E_t >= 1/alpha) <= alpha. Cross-version accumulation is free, and promoting "the latest version" does not change this
  probability, because the event concerns the evidence, not the promoted object.
- N_fwd(h) (promoted frozen version, forward null): E[ sum_{s=tau+1}^{tau+h} (l0_s - l_{g_tau}(s)) | F_tau ] <= 0 at promotion time tau.
  * Stationary target: N_fwd(h) for g_tau follows from N_round at tau+1 plus stationarity (a fixed classifier's per-round value does not
    depend on s). No gap.
  * Non-stationary target: N_round and N_fwd(h) are different statements. A gap exists, but it is the generic past-evidence vs future-value
    problem (candidate B, drift envelope), not a label-reuse problem: an externally trained frozen candidate certified on a pure holdout
    (no label reuse) fails identically (holdout gate).
- Validity failures observed are due to (a) non-predictable versions (resub), (b) peeking without an e-process (peek_z), (c) per-version restart
  tests without spending (restart_naive); none is specific to training on the certification labels.

## Evaluator-side truth
Regime schedule and conditional label probabilities p(y|x) are used only in forward_gap (exact Rao-Blackwellised risk on a shared 20000-point
bank). Gates see only (x_t, y_t) and their own predictions.

## Allocation question and what was tested
Route a fraction f of paid labels to train-only and 1-f to certify-only (splits 25/50/75) vs dual-use (every label trains and certifies).
Under N_round the dual-use gate is valid with all labels in both roles, so splitting only removes evidence: dual-use weakly dominates in power
at equal fee. Delay: labels are processed at release; Z_t uses the prediction stored at query time; lam_t uses released Z only.
