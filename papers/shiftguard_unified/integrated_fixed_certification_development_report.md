# Fixed-candidate versus scout-selection development comparison

**Status:** exploratory CUDA development grid; not a calibration or efficacy confirmation.  
**Date:** 2026-10-26.

## Question and setup

Does fixing the candidate from initial validation before monitoring change the staged pipeline's behavior relative to selecting a candidate on a separate scout split? The runner compares nine methods on eight common synthetic profiles and two matched stream seeds (144 method-stream rows). The methods include continue, scheduled promotion, two-gate Target-Scout, controller-gated variants, Q1 fallback, the Q1→Target-Scout full pipeline, and Q2-only plus Q1-triggered fixed-candidate certification. Candidate identity for both fixed arms is chosen before the Q1 monitor. All methods share generated stream seeds and query uniforms; the maximum queried-label count is 632 of 640.

Run on the NVIDIA GeForce RTX 4060 Laptop GPU, PyTorch 2.9.1, CUDA 13.0:

```powershell
uv run python -m shiftlab.dive.integrated_pipeline `
  --seeds 2 `
  --seed-offset 2026102700 `
  --device cuda `
  --output outputs/shiftguard_unified/integrated_development/pipeline_fixed_certification_dev_v1
```

## Selected descriptive results

Entries show promotion rate, mean labels, and mean expected / realized incremental utility, averaged over two streams per profile. Utility subtracts the declared intervention charges; labels are reported separately because no compatible conversion into utility units is justified.

| Profile | Method | Promotion | Mean labels | Expected utility | Realized utility |
|---|---|---:|---:|---:|---:|
| Boundary-local harm | Continue | 0/2 | 0.0 | 0.00 | 0.00 |
| Boundary-local harm | Q2-only fixed candidate | 2/2 | 317.0 | 242.83 | 234.45 |
| Boundary-local harm | Two-gate Target-Scout | 1/2 | 390.5 | 157.37 | 141.48 |
| Boundary-local harm | Q1→Target-Scout | 1/2 | 523.5 | 157.37 | 141.48 |
| Boundary-local harm | Q1→fixed candidate | 1/2 | 523.5 | 121.71 | 111.98 |
| Boundary-local harm | Q1 fallback | 0/2 | 173.5 | 672.49 | 674.95 |
| Harmful adaptation at monitor | Q2-only fixed candidate | 2/2 | 317.0 | 283.94 | 279.45 |
| Harmful adaptation at monitor | Two-gate Target-Scout | 1/2 | 396.0 | 139.03 | 142.48 |
| Harmful adaptation at monitor | Q1→Target-Scout | 1/2 | 556.0 | 139.03 | 142.48 |
| Harmful adaptation at monitor | Q1→fixed candidate | 2/2 | 629.5 | 283.94 | 279.45 |
| Native event-1,600 adaptation | Q1→Target-Scout | 0/2 | 318.0 | 0.00 | 0.00 |
| Native event-1,600 adaptation | Q1→fixed candidate | 0/2 | 318.0 | 0.00 | 0.00 |
| Post-promotion reversal | Two-gate Target-Scout | 1/2 | 327.5 | −160.05 | −160.05 |
| Post-promotion reversal | Q1→Target-Scout | 1/2 | 487.5 | −160.05 | −160.05 |
| Post-promotion reversal | Q1→fixed candidate | 2/2 | 504.0 | −345.10 | −345.10 |

The two-stream paired bootstrap intervals are descriptive and too unstable for inference. For example, full Target-Scout minus full fixed-candidate mean expected utility was +35.66 in boundary-local harm, −144.91 in aligned harmful adaptation, 0.00 in native timing, and +185.05 under reversal. The reversal and Q1-aligned cells show that a candidate that certifies on fresh data may still be harmful after the post-promotion regime change; the rollback gate is not instantaneous protection. In the controlled harm profiles the simple Q1 fallback had much larger utility than candidate promotion, but this reflects the benchmark's imposed reference policy and does not establish application-level superiority.

The fixed-candidate null calibration covers `full_pipeline_fixed_certification` under its registered pointwise-null calibration family; it does not validate efficacy, and this two-seed grid cannot calibrate error rates. The Q2-only arm is an exploratory comparator here. The current evidence does not support an integrated-method superiority or novelty claim.

## Provenance and next gate

The checksummed run artifacts are [`manifest.json`](../../outputs/shiftguard_unified/integrated_development/pipeline_fixed_certification_dev_v1/manifest.json), [`integrated_pipeline_seed_metrics.parquet`](../../outputs/shiftguard_unified/integrated_development/pipeline_fixed_certification_dev_v1/integrated_pipeline_seed_metrics.parquet), [`integrated_pipeline_summary.csv`](../../outputs/shiftguard_unified/integrated_development/pipeline_fixed_certification_dev_v1/integrated_pipeline_summary.csv), and [`integrated_pipeline_paired_contrasts.csv`](../../outputs/shiftguard_unified/integrated_development/pipeline_fixed_certification_dev_v1/integrated_pipeline_paired_contrasts.csv). The manifest records source snapshots and hashes, protocol hash, CUDA environment, per-event learner/evaluator parquet logs, and the development-only status.

Next, use fresh development seeds to quantify the fixed-versus-scout selection difference and benchmark against resource-matched no-adaptation, scheduled promotion, Q1 fallback, and required published comparators. Freeze only after the information and cost contract is stable, then run a disjoint efficacy confirmation. Keep real-data confirmation and source-based comparator fidelity as separate open gates.
