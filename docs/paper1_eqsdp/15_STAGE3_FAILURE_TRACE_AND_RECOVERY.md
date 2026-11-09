# 15 — Stage 3 failure trace and recovery protocol

Written 2026-11-08. This document has two sources:
- the user-supplied failure analysis and recovery protocol ("Paper 1 — Stage 3 failure analysis and recovery protocol", based on HEAD 30640063);
- the trace that protocol requested, run here.

The Stage 3 failure and the frozen protocols (13, 14) are unchanged. Stage 3 is not reopened, and the frozen candidate is not retuned.

## 1. Trace (evaluator-side diagnostic, development data)

**Command**

```
export OPENBLAS_NUM_THREADS=1 PYTHONIOENCODING=utf-8
python scripts/paper1_eqsdp/stage4_failure_trace.py   # kc_311, episodes 37 and 39, 10 seeds
```

- The script is the user-supplied utility, installed as given. The only change is an ASCII-safe final print, needed for the non-ASCII path.
- Outputs are in `outputs/paper1_eqsdp/stage3_failure_trace/` (gitignored).
- **Replay check:** all 40 seed-level net costs (20 each for `s3_candidate` and `s2armr_H1100`) equal the Stage 3 records in `outputs/paper1_eqsdp/stage3/run/records.jsonl`. Max |diff| = 0.0.

**Per-seed results (Δ = candidate − reference)**

| episode | mean Δ net | seeds with Δ > 0 | candidate first deployment | reference first deployment | labels before t=800, candidate vs reference |
|---|---|---|---|---|---|
| 39 | +607.8 | 10/10 (+433 … +892) | 1306–1821, or never (seed 1) | 560–692 | 12–26 vs 66–89 |
| 37 | +216.1 | 7/10 (−322 … +724) | 101–115 (same) | 101–115 | 16–36 vs 73–88 |

**Evaluator-side gain path** (mean l0−l1 per 400-event block; positive means the challenger is better):
- ep 39: −.36, +.64, +.64, +.64, +.70. The challenger becomes better at about t=400.
- ep 37: +.26, −.22, −.66, −.55, −.63. The challenger is better early, then worse after about t=400.

Both failures are **mid-episode regime changes**.

## 2. Answers to the five questions

1. **Why was the pivotal label rejected?** Because p_cross was low; neither a depressed budget nor a time cutoff was involved.
   - In ep 39 (worst seed), the gate kept 17 of 24 draws in t ≤ 200, while p_cross = .43. In t ∈ (200, 1000] it rejected 100% of draws: p_cross ≈ 0.0000 against ρ_eff ≈ .045.
   - The virtual budget was not exhausted (166 → 106). The candidate has no time cutoff.
   - The same pattern holds in ep 37 for t ∈ (200, 1000].
2. **Last informative label before the delayed adoption.**
   - In ep 39 the candidate bought 1, 1 and 2 labels in the 200-event blocks between 200 and 800. The reference bought 20, 26 and 18, and adopted at t=641.
   - In ep 37 the reference rolled back at t=823, after 46 labels in (200, 800]. The candidate bought 5 labels there, never rolled back, and accumulated +730 excess loss after t=800.
3. **Purchases after the gate starved itself.** 11 labels after t=800 in ep 39 (worst seed), 12 in ep 37. Most came after t=1400, when the remaining horizon could no longer pay back.
4. **Does the failure repeat?** Ep 39 fails on 10/10 seeds, so it is systematic and not query randomness. Ep 37 fails on 7/10, with mixed sign and the same adoption time; it depends on whether a later label lands during the reversal window.
5. **Was a precursor available?** Yes, from released labels alone. The reference detected both changes using only labels it had bought before t=800, so no future ground truth is needed. Prediction-only signals were not examined.

**Diagnosis**
- The C1 reachability score `p_cross` is computed from the current posterior under a **stationary** model.
- Once early evidence puts the posterior far from the switching threshold, the score says no affordable block of labels can cross it. The gate then stops buying, and it can never observe a later change.
- This is change-blind self-starvation of evidence. It matches the user's "misaligned value score" hypothesis, with stationarity as the specific cause. The budget-debit ("self-starvation via virtual budget") hypothesis is **not** supported: the budget stayed at more than 100.
- This also explains why the even-episode gain did not replicate: the gain comes from fee savings on stationary episodes, and the loss from rare change episodes.

## 3. Recovery plan (adopted from the user protocol; predeclared before any run)

**Development data**
- All nine datasets, both parities. These are now development-exposed.
- New held-out data must be new chronological periods of the nine sources. It is built, registered with hashes, and opened once, only after a candidate meets the advance criterion below.

**Common setup**
- Same evidence engine.
- Same cutoff options: H ∈ {1100, none}.
- Contract B=200, c_q=.05, c_s=5, T=2000, 10 seeds.

**Fair references** (tuned on development, same effort as candidates):
- EQSDp arm R + cutoff (`s2armr_H1100` family);
- Wald λ.97/γ.2 + cutoff (`s2wald_l0.97_g0.2_H*`).

**Factorial** (small grids; each arm against its matched control):

| arm | mechanism | matched control |
|---|---|---|
| F0 | cutoff only, on EQSDp and on Wald | — |
| R1 | cutoff + evidence-insurance floor: a minimum query rate on disagreement events and a maximum gap between purchased labels before the cutoff; selective suppression only beyond the floor | equal-label-count calendar |
| R2 | cutoff + one-label economic EVSI. Query iff c_q + λ_t < E[J skip] − E[J query], integrating the unseen label and **pending labels as uncertain futures**, with release at t+d. **The predictive model must include a change hazard (persistence/hazard mixture)**, because §2 shows a stationary posterior is exactly what failed. Use a one-step approximation first. | equal-label-count uncertainty (entropy) sampler |
| R3 | R2 + tail penalty: withhold a query only if the CVaR of (J_skip − J_query) is acceptable | each ablation (R2 without tail; tail without EVSI) |
| R2-roll | short joint rollout vs one-step R2 | built only if R2 or R3 helps |

R4 (post-promotion checks) is not built: §2 locates the failure in information acquisition, not in the deployment rule. The C2 and C5 implementations are not rerun.

**Metrics:**
- mean J (primary; equal-dataset paired);
- L/T, labels, switches;
- late adoption, false promotion;
- paired worst-dataset mean;
- the per-episode excess-cost tail: p95, p99 and CVaR95 of J(arm) − J(reference).

**Advance criterion** (for any candidate, before held-out data are built):
- lower paired mean J, with a 95% CI excluding 0, against **both** fair references;
- ΔL/T ≤ +0.1 pp;
- CVaR95 of the per-episode excess cost no worse than the reference by more than 10%;
- no dataset with a paired mean worse than +1% of its J.

Best-of-grid optimism is reported, and a candidate is chosen on even episodes and checked on odd episodes before any held-out data are built. A ≥ 2% gain is a goal, not a gate.

**Stop rule:** if no arm meets the advance criterion, close this method search. Paper 1 keeps the benchmark, the decision-harm measures, and the corrected-baseline finding (cutoff fee fix, −0.91% held out).

**Novelty note (from the user protocol):** hard cutoffs, finite-horizon VOI, Bayesian optimal switching and CVaR all have prior art. Any claim must rest on the interaction of hard paid-label budgets, delayed feedback, pending observations, reversible deployment and tail loss, with gains over equally equipped Wald/EQSDp.
