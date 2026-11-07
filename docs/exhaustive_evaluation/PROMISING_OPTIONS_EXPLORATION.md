# Promising-options exploration checkpoint

2026-10-30. Registered development diagnostics executed locally. Ponytail and HKUSTDial evidence/fatal-flaw rules applied. No reserved outcomes loaded and no workers spawned. These studies investigate action headroom, not a new switching algorithm.

## Real-data action headroom

Two new scripts write a registration before fitting/scoring, reject silent reruns, hash their inputs and source, and reuse the existing task contracts. The scripts read already downloaded local archives/development Parquet only. Source archives were previously agent-pulled from official UCI hosts.

### Bike and Beijing: little actionable headroom

`explore_action_headroom.py` compares three standardized logistic models (C=1/.01/100), two histogram gradient boosting models (7/15 leaves), and constant positive/negative actions. Fit uses the original training period; target threshold is the training median. Minimum calibration cost selects a challenger, excluding the original incumbent. Calibration selection is itself development: no independence or safety claim follows.

| Task | Calibration-selected challenger | Development excess cost versus incumbent | Finding |
|---|---|---:|---|
| Bike | HGB 15 leaves | +419.8 | Worse in every development month |
| Beijing | Logistic C=.01 | 0 | Identical actions to incumbent |

Bike's best hindsight bank member improves only 0.4 loss units; it was not selected. Beijing has no bank member with a positive aggregate gain. These findings concern this small calendar-only bank, not all possible predictors. They reinforce that an alarm cannot make an unhelpful candidate useful. Expanding monitor tuning on these frozen pairs is low priority.

Artifacts: action_headroom_registration.json and action_headroom_results.json.

### Gas sensors: useful challenger, but limited rollback headroom

`explore_gas_headroom.py` verifies SHA256 and ZIP CRCs, parses all ten official batches, checks 13,910 rows and six-class training support, and fits train-only scaled logistic models. Incumbent: batches1–3, C=1. Candidates: batches1–5, C=.01/.1/1. Selection uses batch6 and includes keeping the incumbent. This is a new exploratory model family, not reproduction of the earlier PyTorch-softmax protocol.

Batch6 selects C=.1 for each prespecified cost scenario. Under symmetric error cost:

| Evaluation batch | Incumbent mean cost | Selected challenger mean cost | Benefit per observation |
|---|---:|---:|---:|
| 7 | .3615 | .2843 | +.0772 |
| 8 | .3605 | .4660 | −.1054 |
| 9 | .3809 | .3745 | +.0064 |
| 10 | .5033 | .4564 | +.0469 |
| Row-weighted aggregate | .4266 | .3740 | +.0527 |

There are 7,977 evaluation observations: 3,403 incumbent errors versus 2,983 selected-challenger errors, a **12.342% gross reduction**. This is a stronger-model result before charging additional training labels/compute, evaluation queries or deployment switches. It is not evidence of an improved monitor. Cost sensitivities with class6 false-negative multipliers2/5 also have lower pooled selected-model cost, but remain imposed benchmark utilities.

A deliberately optimistic **post-hoc descriptive** check limits the rollback interpretation. Give an oracle all realized batch costs and allow switches only at batch boundaries, with cost1 per switch and initial incumbent deployment. Standard two-state dynamic programming gives sequence challenger/incumbent/challenger/challenger, total cost2,955. Always deploying the selected challenger costs2,984 including its initial switch. Thus even this clairvoyant batch controller saves only29 units (0.972%) over the simple challenger policy before paying for any labels. This is an empirical batch-path optimum, not an expected-value or online regret bound; within-batch policies are outside this comparison. Four exposed batches cannot support an independent inference.

**Disposition:** retain gas as a useful coarse-domain stress test of candidate usefulness and reversal. Do not promote its pooled12.3% predictive gain into a new acquisition/switching claim. The batch-level rollback story has little practical headroom under this cost setting. Do not select the hindsight-better C=.01 as if batch6 chose it.

Artifacts: gas_headroom_registration.json and gas_headroom_results.json. Raw archive remains ignored; no individual observations were added to Git.

## Temporal theory/source check

The existing `docs/switching_problem_v1.md` already separates global-null false promotion from future economic benefit, proves a delayed indistinguishability obstruction and gives the elementary drift-envelope inequality. `docs/switching_source_audit_v2.md` explicitly credits average sample-age drift correction to MLDemon. Therefore a sliding window plus an age penalty does not reopen a novel-method claim.

Primary sources checked in this continuation:

- [Ginart, Zhang and Zou, MLDemon (2022)](https://proceedings.mlr.press/v151/ginart22a.html): on-demand labels and current performance monitoring. Existing repo full-text audit records the sample-age correction; no new full-proof verification in this continuation.
- [Vernade, Gyorgy and Mann (2020)](https://proceedings.mlr.press/v119/vernade20b.html): delayed nonstationary learning with intermediate observations. Its published setting makes intermediate signals a mandatory reduction/comparison target if we propose exploiting them. Metadata/abstract inspected here; full theorem mapping remains open.
- [Jia, Xie, Kallus and Frazier (2023)](https://proceedings.mlr.press/v202/jia23c.html): smooth two-arm nonstationary learning. Smoothness alone is not an unexplored premise; full feedback/budget/safety mapping remains open.

No claim of duplication or novelty follows from a related title. The remaining question must specify a mechanism and result beyond established querying/tracking and the existing elementary algebra.

## Updated priorities and next bounded actions

1. **Highest information value: finish the precise reduction audit.** Compare paid common-outcome feedback, pending labels and costed reversible switching against the strongest published compatible learner. State the exact comparator and risk event. Do not implement a generic rollback controller before this gate survives.
2. **Controller synthesis remains open, not confirmed promising.** Fixed-policy DP correctness/speed is established; investigate only whether a structured synthesis rule and useful unrestricted value bounds survive robust-FSC reduction. Standard DP is a baseline. A loose bound or no algorithmic residual closes the claim.
3. **Gas is now the best available action-headroom diagnostic, with a restricted role.** It can test abstention versus useful switching and batch heterogeneity. It cannot establish natural delay performance; timestamps within batches are unverified and all batches were previously exposed. Further data acquisition should target a genuinely timestamped task with multiple useful actions and sufficient reversal cost headroom, registered before outcome inspection.
4. **Stop cosmetic betting sweeps on the current real pairs.** They cannot overcome the absent challenger benefit. Keep all negative results and matched-tuning failures.

HKUSTDial verdict: reject a substantial-gain claim for the existing finalist; restrict gas to exploratory utility/headroom evidence; continue bounded source/synthesis work. No new method or real net-utility result has been validated.

## Reproduction and checks

From the exhaustive-evaluation worktree, with PYTHONPATH=src;. and single-thread BLAS/OpenMP:

    python scripts/exhaustive_evaluation/explore_action_headroom.py
    python scripts/exhaustive_evaluation/explore_gas_headroom.py

Both commands have completed; their registrations prevent overwriting them. For reproduction, use a separate output namespace and retain original hashes. Ruff0.17.1 checks/format passed. Assert-based self-checks verified binary asymmetric costs and multiclass zero-error costs. Existing independent results were not rerun. Novelty and end-to-end cost efficiency remain unresolved.
