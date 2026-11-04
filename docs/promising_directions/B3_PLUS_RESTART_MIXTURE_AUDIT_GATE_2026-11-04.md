# Candidate gate: restarted reversal evidence for budget-aware auditing

**Date:** 2026-11-04. **Status:** analytical screen plus a completed negative development pilot; no confirmatory result, broad validity claim, or novelty claim.

## Evidence driving this candidate

The B3+ development comparator found that P7s reduced stable-period label use but lost to both Cao-style controls after reversal. Its P7s-sentinel did not close the reversal-cost gap; its e-process sentinel did not either. In the abrupt-reversal scenario, the current per-seed records show P7s averaging 75.6 queries in the first half and 120.5 in the second, versus 89.0 and 106.1 for Cao-L. The reversal outcome remains slow even though P7s shifts queries later. See [the frozen development report](B3_PLUS_CAO_DEVELOPMENT_FINDINGS_2026-11-08.md) and [the comparator gate](B3_PLUS_CAO_COMPARATOR_GATE_2026-11-08.md).

A trace of the registered development seed `20261108` suggests a specific weakness: P7s remains at its `.05` propensity floor immediately after the reversal while its discounted signed mean is still negative; Cao-L requests at a materially higher propensity from the beginning of the post-reversal segment. In that seed, the first queried harmful paired outcome is issued at event 1011 under P7s (`q=.05`) versus event 1001 under Cao-L (`q≈.402`); rollback occurs at events 1587 and 1285, respectively. This single-seed trace is diagnostic only and does not establish a population mechanism.

## A model-specific restart-mixture screen

In the registered synthetic generator, conditional on a disagreement and on the challenger being deployed, let `U_i=1` indicate a paired outcome favoring rollback. Outcomes are IID with

```text
P_0(U_i=1)=p_0=.30  (persistent challenger benefit)
P_1(U_i=1)=p_1=.70  (after reversal).
```

For a queried-label index `i`, define the likelihood factor

```text
L_i = (p_1/p_0)^U_i * ((1-p_1)/(1-p_0))^(1-U_i).
```

For each candidate onset `k` in `1,...,B`, let `L_{k:n}=product_{i=k}^n L_i` (one before `k`), and define the finite uniform mixture `M_n = (1/B) sum_{k=1}^B L_{k:n}`. Under the known no-reversal model, each component and the mixture are nonnegative martingales in queried-label order. Therefore `P_0(sup_n M_n >= 1/eta) <= eta`; a monitor can use this crossing to restore a higher acquisition rate without changing the existing promotion/rollback rule. With fixed ordered delay, labels can be processed in release order. If the high-rate trigger affects actions, or if the `.30` null model is used for a rollback guarantee, a separate proof is required. The existing paired conditional-mean e-process must remain the sole action gate in any first pilot.

The likelihood factor is not valid for the repository's full conditional-mean rollback null, which allows `P(U_i=1|history)` up to `1/2`, nor for unknown or outcome-dependent conditional disagreement rates. It is only a model-based acquisition signal for the IID development generator. A real-data or broad-null claim cannot rely on it without replacing the model assumption.

For a candidate onset `k`, the mixture includes its component with weight `1/B`. At reversal, that component reaches the mixture threshold if its likelihood ratio is at least `B/eta`. Its mean log growth under `P_1` is

```text
KL(Ber(.70) || Ber(.30)) = 0.338919 nats per queried disagreement label.
```

With `B=200` and `eta=.05`, the first-order label-count estimate is `log(B/eta)/KL ≈ 24.5` labels. This is a planning approximation, not an expected-stopping-time theorem. At disagreement probability `.30` and common delay 50, a constant audit propensity `q=.05` yields only `0.30*.05*950 = 14.25` expected post-reversal releases within a 1,000-event residual horizon; `q=.10` yields `28.5`. The `.05` floor is therefore unlikely to activate this conservative anytime sentinel early enough in the registered cell. The frozen pilot used `q_audit=.20` to leave capacity for the paired action gate after the warning. Results are negative; see [`B3_PLUS_RESTART_MIXTURE_DEVELOPMENT_FINDINGS_2026-11-04.md`](B3_PLUS_RESTART_MIXTURE_DEVELOPMENT_FINDINGS_2026-11-04.md).

## Prior-art and novelty boundary

This is not a new change detector or controlled-sensing principle. Cao, [*The First-Order Value of Free Covariates in Budgeted Risk Monitoring*](https://arxiv.org/html/2611.00576), already uses free covariates and label-history sleep/wake acquisition with a shared e-detector. Veeravalli, Fellouris, and Moustakides, [*Quickest Change Detection With Controlled Sensing*](https://arxiv.org/abs/2310.17223), jointly control sensing and change detection and give an asymptotically optimal WCC rule under an MTFA criterion. A restart mixture over onset candidates is also standard e-detector machinery. The residual mismatch is the narrow contract: paired frozen-model utility, delay, a request-time pathwise hard cap, and reversible deployment cost, with finite-horizon false-promotion control. Those differences alone do not establish novelty.

## Development gate result

The frozen 200-seed-per-scenario pilot is complete on a disjoint block. P7s-RM improves over P7s after reversal but fails the registered primary gate against Cao-L and Cao-Hybrid: mean reversal costs are higher by `2.578` and `2.736`, respectively, and rollback is slower. Stable-state costs also rise versus P7s. The source and row-level summary are in the [findings report](B3_PLUS_RESTART_MIXTURE_DEVELOPMENT_FINDINGS_2026-11-04.md); the unchanged protocol is [here](B3_PLUS_RESTART_MIXTURE_DEVELOPMENT_PROTOCOL_2026-11-04.md). Do not tune this seed block or run confirmation. Close the current candidate; only reconsider it after a different source-audited structural gap, not by shifting `eta` or the audit floor on these data.
