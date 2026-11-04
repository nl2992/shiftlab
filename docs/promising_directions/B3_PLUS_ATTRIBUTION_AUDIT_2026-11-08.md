# B3+ attribution and prior-art update — 2026-11-08

## Frozen evidence audit

The source-matched ablation artifacts are `docs/promising_directions/results/b3_plus/ablation/{spam,rialto,weather}__S0__h2000.jsonl`. They were produced with 100 paired query seeds per episode on the frozen S0 settings. `provenance.json` records the run command and code hashes; the policy, baseline, and experiment source hashes match the current files. All JSONL SHA-256 digests match `SHA256SUMS.txt`. The independent analysis is reproducible with:

```powershell
uv run python scripts/promising_directions/b3_plus_attribution_audit.py
```

The script checks source and row hashes, matched method presence, and the identity `net cost = deployment loss + query price × labels + switch price × switches`; maximum absolute reconstruction error is recorded in `outputs/b3_plus_attribution_audit/audit.json`.

| Stream | K | P3b cost | P7b hopeless-only Δ | P7a promotion-only Δ | P4ref Δ | P7s settled-state Δ | P7s labels saved |
|---|---:|---:|---:|---:|---:|---:|---:|
| spam | 1 | 254.09 | 0.00 | +23.79 | +127.87 | -6.66 [-6.77, -6.54] | 133.2 |
| rialto | 16 | 103.73 | 0.00 | +8.97 | +106.29 | -5.31 [-6.00, -4.60] | 106.2 |
| weather | 3 | 475.77 | 0.00 | +17.57 | +37.15 | -3.20 [-3.33, -3.08] | 64.0 |

Intervals are paired bootstrap intervals: episodes for rialto; query seeds for spam and weather, which are low-power diagnostics and not episode-level uncertainty. P7s has zero average change in deployment loss and switching cost on all three records; its cost difference is exactly the label-cost term. P7b equals P3b, while P7s adds the settled-state gate. P7a and P4ref lose on all three.

This attribution remains limited to those three streams. In particular, openml_ldpa has no matching P7a/P7b/P4ref records here, and must not be used to claim mechanism isolation.

## Prior-art boundary

Setoudehtanzangi and McLachlan (2026), [*Large Classification-Risk-Optional Label Acquisition*](https://arxiv.org/abs/2609.06873), is material prior art for any broad claim that decision-relevant label acquisition is new. It derives a cost-sensitive, Fisher-information acquisition design for reducing leading asymptotic classification risk by aligning acquired-label information with directions that move the active Bayes boundary. That objective allocates labels to fit/improve a classifier. P7s instead keeps two fitted classifiers fixed and uses delayed paired labels to maintain sequential promotion/rollback evidence under a hard per-episode budget. The distinction is the monitoring target and sequential feedback contract, not the generic idea of valuing labels for downstream decisions.

The existing evidence is a scoped real-stream efficiency result against a paired anytime-valid certificate. It does not establish SOTA superiority: the fixed-sample P6 comparator wins on weather, uncertainty is low on two ablation streams, and novelty versus value-of-information/acquisition methods still needs a full source-level audit. Any next confirmatory work should specifically test the cost and delay trade-off of post-promotion rollback monitoring against fixed-sample and always-on sequential baselines under a stated stochastic contract.
