# Synthetic evaluation status

## Evidence available

- **Failure Atlas discovery:** 15 policies, 20 synthetic regimes, 100 paired seeds per regime, contract T=2,000, B=200, label cost .05, switch cost 5 and alpha .05; the repository reports 80,400 episode runs including nine cached real streams. These runs are development-exposed.
- **Corrected FLQ validation:** corrected validation artifacts are in `docs/failure_atlas_v2_flq/results/validation_synthetic.md`; strict null criteria are not passed by all candidate families. These are reused, exposed validation regimes, not the fresh seed confirmation required by the brief.
- **WP1 E_rb follow-up:** `docs/sprint2/wp1/erb_reversal_postdev100.json` reports ΔJ = −6.65 with 95% t CI [−7.31, −6.00] versus RMM across three reversal settings and four hosts. This follow-up is post-development; its ablation points to alpha/start grid rather than the horizon gate.

## New bounded replay in this execution

We ran a new, post-development sensitivity for the existing E_rb result (not a new method evaluation): 20 paired seed blocks, 60 regime-seed episodes, four matched hosts, with the registered three reversal regimes `F3_reversal_800`, `W_reversal_700`, `S_reversal_400`; T=2,000, B=200, c_q=.05, c_s=5, alpha=.05. Seed base `2026110699`; exact argv and source hashes are in `outputs/scoped_method_research_20261106/erb_reversal_seed20/manifest.json`, raw records in that directory, and analysis in [synthetic_reversal_seed20.json](synthetic_reversal_seed20.json).

The paired primary contrast E_rb−RMM, equal-weighted over 3 regimes × 4 matched hosts per seed, is **−6.86 net-cost units**, 95% t CI **[−8.69, −5.03]**, n=20 seed blocks. Directionally, E_rb improves on this matched RMM wrapper in the replay. Each policy used a mean of 200 labels (label cost 10), so the paired label-expenditure difference is zero. The E_rb−RMM mean predictive-loss differences by host are −7.18, −6.90, −6.58 and −7.68; switch-cost differences are +0.08, +0.17, +0.17 and +0.50 respectively (`synthetic_cost_decomposition.json`). Thus the difference is attributable to lower prediction loss despite slightly higher switching cost in these runs.

The never-switch control mean net cost is **333.75**, versus E_rb host means of 369.55–377.68 and RMM means of 375.97–384.87. On this overall reversal suite, always retaining the incumbent is cheaper than either switching family. This makes the E_rb−RMM result a narrow relative improvement, not an overall deployment advantage. Regime/host contrasts are exploratory; some intervals cross zero.

This is **fresh seed evidence, but not untouched confirmation**: the E_rb and its comparisons were already selected/developed. It does not compare a newly proposed repair to strongest matched SR/CUSUM and corrected certificate baselines; it cannot establish novelty, a guarantee, or real transfer.

## Smallest bounded next experiment (if the method track is reopened)

If a distinct candidate is later proposed, freeze one reversal family at T=2,000, B=200, c_q=.05, c_s=5. Use paired fresh seeds and compare E_rb as-is, matched-alpha E_rb, candidate cost-to-go rollback gate, two-sided SR/CUSUM, and no rollback. Freeze the start grid, query policy, null, alpha allocation, net-cost estimand and seed range in advance. Report predictive loss, labels, switches, net cost, time-to-rollback and false rollback under the correctly specified null, with paired intervals. This can falsify incremental value; it cannot establish independent real transfer.
