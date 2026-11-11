# theory_v2 — experiment results registry

**Branch:** `research/paper4-causal-premium-theory-2026-11-10`. **Hardware:** Apple M4, 10 cores, 16 GiB, macOS 15.5
(arm64). **Software:** Python 3.12.2, NumPy 2.5.4, SciPy 1.18.1 (HiGHS via `scipy.optimize.linprog`; float LP
followed by exact-rational certification). **Exact tool:** `scripts/paper4_continuation/theory_C/gamma_lib.py`
`gamma_cell`, which returns a certified interval [Γ_lo, Γ_hi] in exact rationals (FCG-fast when the repaired IID
optimum is not causal-safe). "Γ > 0 certified" means Γ_lo > 0 in exact arithmetic; "Γ = 0" means Γ_hi ≤ ~1e-13
(float dual rounding) unless stated exact. No randomised seeds affect any certified value; random cell draws record
their seed in the output JSON. All runs are development/verification evidence on synthetic models; nothing here is
confirmatory evidence about real deployments.

## Campaign summary

| Campaign | Producer | Cells | Outcome | Validation |
|---|---|---|---|---|
| A: N1 re-implementation vs certified | `wpA_audit_checks.py` | 1,905 (α ≤ 1/2) + 40 (α > 1/2) | 1,905/1,905 exact; N1 fails for α > 1/2 | independent code; lead spot-checks |
| A: C3′/C3″ alternation grids | `wpA_audit_checks.py` | 468 even-T + 384 odd-T | C3′ wrong at T=2 (24/156); C3″ 468/468 | lead re-computed CE-13 |
| A: plan enumeration (tape vs z-monotone) | `wpA_zc_enum.py` | 19,970 plans | classes incomparable; no monotone plan with R_causal ≠ R_IID | — |
| B: falsification + Lemma U premise | `wpB_*.py` | ≈ 30k cells (T ≤ 12, B ≤ 6) | Z2 falsified at B=4 (CE-12) | lead re-computed CE-12 + α sweep |
| B: hull-targeted α ≤ 1/2 scan | `wpB2_halfscan.py` | 5,142/5,400 sym (time cap) + 6,480 static + 4 large | 53 sym cells / 300 pairs Γ>0 at α ≤ 1/2; 0 static | lead re-computed CE-14 |
| G: S0 red team | `rev1_s0_redteam.py` | 472 cells, 2,272 λ-checks, 2,862 certificates | none positive | independent reviewer |
| C: SP1 vs certified | `wpC_*.py` | 5,400 certified + 25,920 DP | all match | lead spot-checks (6 cells exact) |
| G: SP1 red team | `rev1_sp1_*.py` | 2,420 certified + 3,000 exact | all match; CE-18, CE-19 | lead re-computed CE-18 |
| E: A3 runtime campaign (other session) | `ablation_campaign.py` (other worktree) | 75 runs | no FCG cut-generation gain | read-only summary |
| C2: relative-premium scaling | `wpC2_relative_premium.py` | 1,808 planned | IN PROGRESS (3 workers) | — |

Negative results recorded: Z2 / U-M (CE-12, CE-14), C3′ at T=2 (CE-13), SP1-D at T=d+1 (CE-18), d-monotonicity
(CE-19), even-d ⇒ 0 at B=2 (CE-15), k lowers Γ (CE-16), Γ monotone in B (CE-17); FCG runtime advantage (A3).

## Provenance (generated from git, 2026-11-10)

Commands: each script is run as `uv run --no-sync python scripts/paper4_continuation/theory_v2/<script> [args]`
from the repo root; arguments and grids are recorded inside each output JSON and in the producing document's
reproduction section (`THEOREM_PROOF_AUDIT.md`, `MULTILABEL_ZERO_PREMIUM.md`, `STOCHASTIC_POSITIVE_PREMIUM.md`,
`REVIEW_S0.md`, `REVIEW_SP1.md`). Outputs are refuse-overwrite.

| Script | sha256 (12) | Commit |
|---|---|---|
| `rev1_s0_redteam.py` | `a6a10aad8f4a` | `fe7d9a35` |
| `rev1_sp1_brute.py` | `30f22d8aa902` | `0d0427b2` |
| `rev1_sp1_lib.py` | `03e42f9c5ed3` | `0d0427b2` |
| `rev1_sp1_redteam.py` | `f03275bf2c98` | `0d0427b2` |
| `rev1_sp1_witness.py` | `8ff4f7d5014e` | `0d0427b2` |
| `wpA_audit_checks.py` | `a135c424f9cc` | `96dd637a` |
| `wpA_formula_search.py` | `46db4afaf9b3` | `96dd637a` |
| `wpA_zc_enum.py` | `33d61baf341b` | `96dd637a` |
| `wpB2_halfscan.py` | `c840c513db1b` | `67d2d4ce` |
| `wpB2_record.py` | `02fb8457cea3` | `67d2d4ce` |
| `wpB_ce_record.py` | `37327be79ef6` | `6051f2b6` |
| `wpB_dual_check.py` | `c3a1b4f07e62` | `6051f2b6` |
| `wpB_falsify.py` | `885d2e444d7d` | `6051f2b6` |
| `wpB_lib.py` | `096c136f4ac8` | `6051f2b6` |
| `wpB_multiW.py` | `648f4094a9a0` | `6051f2b6` |
| `wpB_static.py` | `56e45e49228c` | `6051f2b6` |
| `wpB_static_falsify.py` | `5f5ca5c565f6` | `6051f2b6` |
| `wpB_static_patterns.py` | `cf56c9bf5de8` | `6051f2b6` |
| `wpB_static_proofcheck.py` | `dddf478fcbf7` | `6051f2b6` |
| `wpB_symce.py` | `194f3c7e9b8f` | `6051f2b6` |
| `wpB_u1_check.py` | `43e628ecf729` | `6051f2b6` |
| `wpB_validate.py` | `9eba4a12123c` | `6051f2b6` |
| `wpC2_relative_premium.py` | `0cc20539f704` | `uncommitted` |
| `wpC2_summarize.py` | `750e0d351ed2` | `uncommitted` |
| `wpC_asym.py` | `35262cae2c82` | `df2ffcd6` |
| `wpC_budget.py` | `3c99623901b6` | `df2ffcd6` |
| `wpC_sp1_certified.py` | `0fabf6a38528` | `df2ffcd6` |
| `wpC_sp1_sweep.py` | `68addb4d0343` | `df2ffcd6` |
| `wpC_sym_lib.py` | `835bb6bdd4cb` | `df2ffcd6` |
| `wpC_sym_verify.py` | `cca867f85c35` | `df2ffcd6` |

| Output | Size | Commit | Recorded seed / config keys |
|---|---|---|---|
| `rev1_s0_redteam_rand_w0.json` | 196 KiB | `fe7d9a35` | n_cells |
| `rev1_s0_redteam_rand_w1.json` | 219 KiB | `fe7d9a35` | n_cells |
| `rev1_s0_redteam_rand_w2.json` | 209 KiB | `fe7d9a35` | n_cells |
| `rev1_s0_redteam_rand_w3.json` | 228 KiB | `fe7d9a35` | n_cells |
| `rev1_s0_redteam_w0.json` | 166 KiB | `fe7d9a35` | n_cells |
| `rev1_s0_redteam_w1.json` | 192 KiB | `fe7d9a35` | n_cells |
| `rev1_s0_redteam_w2.json` | 204 KiB | `fe7d9a35` | n_cells |
| `rev1_s0_redteam_w3.json` | 209 KiB | `fe7d9a35` | n_cells |
| `rev1_sp1_brute_v1.json` | 4 KiB | `0d0427b2` | seed |
| `rev1_sp1_redteam_s2_w0.json` | 300 KiB | `0d0427b2` | seed |
| `rev1_sp1_redteam_s2_w1.json` | 299 KiB | `0d0427b2` | seed |
| `rev1_sp1_redteam_s2_w2.json` | 299 KiB | `0d0427b2` | seed |
| `rev1_sp1_redteam_w0.json` | 46 KiB | `0d0427b2` | seed |
| `rev1_sp1_redteam_w1.json` | 48 KiB | `0d0427b2` | seed |
| `rev1_sp1_redteam_w2.json` | 47 KiB | `0d0427b2` | seed |
| `rev1_sp1_redteam_w3.json` | 48 KiB | `0d0427b2` | seed |
| `rev1_sp1_witness_v1.json` | 2 KiB | `0d0427b2` |  |
| `wpA_c3_grid_oddT35.json` | 471 KiB | `96dd637a` |  |
| `wpA_c3prime_grid_T246.json` | 710 KiB | `96dd637a` |  |
| `wpA_formula_search_static.json` | 0 KiB | `96dd637a` | seed |
| `wpA_formula_search_tp2M.json` | 0 KiB | `96dd637a` | seed |
| `wpA_inputs/` | dir | `96dd637a` | inputs |
| `wpA_n1_random_s101.json` | 217 KiB | `96dd637a` |  |
| `wpA_n1_random_s202.json` | 209 KiB | `96dd637a` |  |
| `wpA_n1_random_s303.json` | 549 KiB | `96dd637a` |  |
| `wpA_n1_scope_alpha_gt_half.json` | 60 KiB | `96dd637a` |  |
| `wpA_n1_targeted.json` | 231 KiB | `96dd637a` |  |
| `wpA_s1_static_certified.json` | 90 KiB | `96dd637a` |  |
| `wpA_zc_enum.txt` | 1 KiB | `96dd637a` | (non-JSON) |
| `wpB2_halfscan_static_shard0of1.json` | 0 KiB | `67d2d4ce` |  |
| `wpB2_halfscan_sym_shard0of5.json` | 79 KiB | `67d2d4ce` |  |
| `wpB2_halfscan_sym_shard1of5.json` | 80 KiB | `67d2d4ce` |  |
| `wpB2_halfscan_sym_shard2of5.json` | 65 KiB | `67d2d4ce` |  |
| `wpB2_halfscan_sym_shard3of5.json` | 57 KiB | `67d2d4ce` |  |
| `wpB2_halfscan_sym_shard4of5.json` | 64 KiB | `67d2d4ce` |  |
| `wpB2_halfscan_symbig_shard0of3.json` | 14 KiB | `67d2d4ce` |  |
| `wpB2_record_v1.json` | 5 KiB | `67d2d4ce` |  |
| `wpB_ce_record_v1.json` | 2 KiB | `6051f2b6` |  |
| `wpB_dual_check_symCE_T5B4.json` | 0 KiB | `6051f2b6` |  |
| `wpB_falsify_static_s1.json` | 72 KiB | `6051f2b6` | seed, n_cells |
| `wpB_falsify_sym_s1.json` | 74 KiB | `6051f2b6` | seed, n_cells |
| `wpB_falsify_sym_s2_T10B6.json` | 22 KiB | `6051f2b6` | seed, n_cells |
| `wpB_falsify_tp2any_s1.json` | 82 KiB | `6051f2b6` | seed, n_cells |
| `wpB_falsify_tp2m_s1.json` | 70 KiB | `6051f2b6` | seed, n_cells |
| `wpB_multiW_control_CE10.json` | 0 KiB | `6051f2b6` |  |
| `wpB_multiW_symCE_T5B4.json` | 0 KiB | `6051f2b6` |  |
| `wpB_static_falsify_s1_T12B6.json` | 0 KiB | `6051f2b6` | seed, n_cells |
| `wpB_static_falsify_s2_T9B4.json` | 0 KiB | `6051f2b6` | seed, n_cells |
| `wpB_static_patterns_s4.json` | 2 KiB | `6051f2b6` | seed |
| `wpB_static_proofcheck_s1.json` | 0 KiB | `6051f2b6` | seed, n_cells |
| `wpB_symce_sym_B23_T3-7.json` | 0 KiB | `6051f2b6` |  |
| `wpB_symce_sym_B4_T4-5.json` | 7 KiB | `6051f2b6` |  |
| `wpB_symce_sym_B4_T6.json` | 25 KiB | `6051f2b6` |  |
| `wpB_symce_sym_B5_T5-6.json` | 66 KiB | `6051f2b6` |  |
| `wpB_u1_static_s1.json` | 5 KiB | `6051f2b6` | seed, n_cells |
| `wpB_u1_sym_s1.json` | 6 KiB | `6051f2b6` | seed, n_cells |
| `wpC_asym_s7.json` | 387 KiB | `df2ffcd6` | seed |
| `wpC_budget_v1.json` | 740 KiB | `df2ffcd6` |  |
| `wpC_sp1_certified_p0.json` | 919 KiB | `df2ffcd6` |  |
| `wpC_sp1_certified_p1.json` | 913 KiB | `df2ffcd6` |  |
| `wpC_sp1_sweep_v1.json` | 37 KiB | `df2ffcd6` |  |
| `wpC_sym_verify_p0.json` | 153 KiB | `df2ffcd6` |  |
| `wpC_sym_verify_p1.json` | 138 KiB | `df2ffcd6` |  |
| `wpC_sym_verify_p2.json` | 134 KiB | `df2ffcd6` |  |
