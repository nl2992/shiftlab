# Restart-mixture acquisition pilot — development findings

**Date:** 2026-11-04. **Status:** disjoint-seed development result with an implementation-specification deviation disclosed below; tested candidate fails its gate. No confirmatory result, SOTA claim, or novelty claim.

## Reproducibility and scope

The pre-run protocol is [`B3_PLUS_RESTART_MIXTURE_DEVELOPMENT_PROTOCOL_2026-11-04.md`](B3_PLUS_RESTART_MIXTURE_DEVELOPMENT_PROTOCOL_2026-11-04.md). The runner command is:

```powershell
uv run python scripts/promising_directions/b3_plus_restart_mixture_dev.py
```

It uses 200 seeds per scenario starting at `21261108`, disjoint from the earlier comparator's `20261108` block. The run produced 200 paired episodes per scenario. Source hashes in `outputs/b3_plus_restart_mixture_dev/dev.json` match the runner, policy and comparator used in the run; all methods had zero hard-cap violations. The runner did not embed a protocol checksum. After execution, the protocol wording was clarified to reflect the controller actually coded: after the mixture warning, the `.20` minimum is applied while the signed-mean state remains settled; outside that state, acquisition follows P7s, which restores its budget-paced rate. The pre-run prose said the higher rate would persist through the rest of the deployment segment. This is an implementation-specification deviation, so treat the result as a development screen of the coded controller, not as exact execution of that stronger latch rule. These bootstrap intervals quantify only variation across this block; they do not certify error rates.

**Post-run provenance check:** the runner manifest does not record the dynamically loaded B1 evidence implementation hash. The policy loader pins B1 to commit `041bc26fafeed1132f17ed762ddbfdcff02e34f2`; hashing the source bytes at `scripts/promising_directions/b1_certified_switching.py` from that commit gives SHA-256 `7565a647f3bb3f940d4fbd2a948597b9ffe42ef0485550a771d137e7930baebd`. This identifies the pinned implementation used by the loader, but the omission from the run manifest remains a provenance limitation.

## Outcomes

| Scenario | Policy | Mean net cost | Mean labels | Rollback probability | Rollback-delay RMST |
|---|---|---:|---:|---:|---:|
| Stationary positive | P7s | 262.518 | 131.4 | 0/200 | — |
|  | P7s-RM | 264.580 | 172.6 | 0/200 | — |
|  | Cao-L | 265.593 | 187.4 | 0/200 | — |
|  | Cao-Hybrid | 265.673 | 189.2 | 0/200 | — |
| Abrupt reversal | P7s | 340.020 | 195.4 | 0.760 | 740.1 |
|  | P7s-RM | 330.924 | 197.9 | 0.874 | 651.0 |
|  | Cao-L | 328.347 | 194.8 | 0.887 | 615.0 |
|  | Cao-Hybrid | 328.189 | 195.7 | 0.875 | 617.8 |
| Benign covariate shift | P7s | 265.713 | 132.1 | 0/200 | — |
|  | P7s-RM | 267.684 | 171.5 | 0/200 | — |
|  | Cao-L | 268.636 | 186.9 | 0/200 | — |
|  | Cao-Hybrid | 269.285 | 199.8 | 0/200 | — |

P7s-RM cuts P7s's reversal cost by `9.096` (paired bootstrap 95% interval `[-12.059,-6.133]`) and lowers its rollback-delay RMST by about 89 events. It does not beat the registered controls: mean paired reversal cost is `+2.578` versus Cao-L (95% interval `[-0.076,5.260]`) and `+2.736` versus Cao-Hybrid (`[0.184,5.406]`). Its rollback probability is `0.874`, below Cao-L's `0.887` and effectively tied with Cao-Hybrid's `0.875`; its RMST is 33–36 events longer. Thus the primary reversal-cost gate fails against both controls, and the delay comparison is also unfavorable.

P7s-RM spends about 41 more labels than P7s in the stationary-positive scenario, raising mean net cost by `2.061` (paired 95% interval `[1.906,2.219]`), and about 39 more labels in benign shift, raising cost by `1.971` (`[1.832,2.104]`). Its lower point cost than the two Cao adaptations in those scenarios is not enough to offset the reversal loss. The restart mixture crossed before any actual reversal in 0/200 reversal episodes; in the stable scenarios it crossed in 1/200 stationary episodes and 5/200 benign-shift episodes. These are descriptive diagnostics, not calibration proof beyond the model-specific Ville argument.

## Decision

Close the current restart-mixture candidate. The failure indicates that, at this audit rate and threshold, using an unknown-onset likelihood alarm to restore acquisition is less efficient than the adapted label-history controls once the hard cap and delay are priced. Do not tune this seed block or run confirmation. The current package still has no method that beats both matched controls while meeting the registered reversal criteria.

The remaining research objective stays open. Continue only if a new source-audited structural gap appears, or focus on a stronger attribution and real-data evidence package. The model-specific IID `.30/.70` acquisition alarm should not be generalized to the broader conditional rollback null.
