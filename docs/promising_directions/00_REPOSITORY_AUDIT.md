# 00 Repository Audit (2026-10-30)

Status vocabulary: VERIFIED (re-derived from the raw artifact in this audit session), DOC-ONLY (stated in a repository document, not re-derived), MISMATCH (document and artifact disagree), NOT FOUND.
Remote: https://github.com/nl2992/shiftlab. Paths below are relative to the repo root on the stated branch/commit.

## 1. Git state

| Item | Finding | Status |
|---|---|---|
| Working branch | `research/shiftlab-promising-directions-2026-10-30`, created from the LOCAL `research/exhaustive-candidate-evaluation-2026-10-30` HEAD `9cb4a1d6053e809665fc7e43040fcaafa14d75e2` | VERIFIED |
| Local vs origin | Local exhaustive HEAD is 9 unpushed commits ahead of origin's `a7c88d8` (the commit the task prompt referenced) | VERIFIED |
| Unpushed commits | `c3806a2` verify prediction betting statistic; `594e79c` native Markov test pilot; `e10241d` paired SR/CUSUM e-detector threshold contracts; `6a152ef` 504 paced epoch compositions negative; `1fb4db8` nonpartitioned PFA pilot; `ac02734` exact finite controller class + root mixture; `405bb79` controller vs unrestricted sequence-form reference; `6047afd` evaluation abandonment as missing controller option; `9cb4a1d` abandonment class validated on prospective overlap cases | VERIFIED |
| Exhaustive worktree, uncommitted | `src/shiftlab/dive/causal_switching_game.py` modified; `src/shiftlab/dive/sequence_dual_certificate.py` untracked. Another agent's work; not included in this branch | VERIFIED (presence only) |
| Main worktree, uncommitted | User-approved revision of `docs/budgeted_switching_research_goals.md` adding acceptance criteria R1-R6 (oracle is a reference; prior-art kill only if a source theorem states or implies the result under the same contract; partial contracts allowed; exploratory prototypes allowed; safeguards unchanged; strong baselines mandatory). Main HEAD is `c789593` | VERIFIED (presence) |
| New remote branch | `origin/claude/sweet-lovelace-pznpjq` (`d1b173b`, 2026-10-30), directory `research/novelty_validation_2026-10-30/`; conclusion BENCHMARK_OR_NEGATIVE_RESULT_ONLY (files `12_FINAL_PUBLICATION_DECISION.md`, `LEDGER.md`) | DOC-ONLY for its conclusion |

Branches relevant to this audit (HEADs at audit time): h2c-strong-baselines `60930a4`; h2c-restart-risk-certified `d4673d9`; shiftlab-mandate-gap-closure `8552911`; hg-validation-and-novelty `1299c1c`; rpoq-s1-fatal-flaw-audit `0b1ce99`; shiftlab-dependence-gates `026500d`; risk-preserving-switching-approx `2bd2e8e`; exhaustive-candidate-evaluation `9cb4a1d`.

## 2. Data inventory

Local data in `shift-research-starter/data`: criteo_privatead 32.5 GB; CRSP CIZ 2.6 GB raw + 2.6 GB processed (licensed; per-year SHA manifests); criteo_attribution; eia; folktables; wilds; opsd; monash; open_bandit; noaa; upworthy; gas_sensor (`uci-224.zip` + receipt); hillstrom; elec2; binance; fred. Sizes are stated only for the three listed above.
Not present locally: Bike and Beijing raw data (only URLs recorded). NOT FOUND.
Real-data headroom (`docs/exhaustive_evaluation/PROMISING_OPTIONS_EXPLORATION.md` @ `ad6cedf`, exhaustive branch): Gas challenger 3403 -> 2983 errors over 7977 observations = 12.342% (recomputed, VERIFIED); clairvoyant batch switching 2955 vs always-challenger 2984 = 0.972% (switch cost 1, no label cost, exposed holdout; DOC-ONLY); Bike and Beijing show no headroom (DOC-ONLY).

## 3. Code components (as audited)

| Component | Path | Tests | Note |
|---|---|---|---|
| Paired/CAMS monitors | `src/shiftlab/gap/q2.py` (paired_e, paired_e_bonf, paired_cs, seqmcs, pp_paired, cams, S09a-e) | NONE | Simulated FWER max 0.023 (paired_e, K=10), cams 0.0029; wrong promotion after reversal 0.012-0.038 (DOC-ONLY) |
| Gated monitor comparison | `src/shiftlab/dive/gated_monitor_comparison.py` | yes | structural-zero agreements, HT disagreement queries |
| Active betting | `xu_active_betting.py` | yes | formula adaptation |
| Promotion | `promotion.py` `CandidatePromotionTest`, alpha_i = alpha/[i(i+1)]; `budgeted_promotion.py` | not assessed here | |
| Contract layer | `src/shiftlab/contract/` | not assessed here | |
| H2c statistic | `src/shiftlab/sota_search/detectors.py` `pp_cost_guided(mode="guided_disc", gamma=0.995)` lines ~570-610 (h2c `60930a4`) | no supermartingale unit test | validity argued in `docs/h2c_next/COST_NULL_VALIDITY.md` |
| Cap repair | `tests/gap/test_engine.py::test_exact_finite_support_cap` (`8552911`) | 18 tests pass | VERIFIED |

## 4. Baseline coverage

`docs/exhaustive_evaluation/BASELINE_COVERAGE.md` @ `9cb4a1d`: coverage is incomplete. Eleven source-fidelity obligations remain open: robust FSC; finite-window CPOMDP; Active RCPS full reproduction; PR monitoring; PPRM faithful CS; Hsu-Shekhar native (obstruction); Betting on Predictions native; PH/CUSUM/SR e-detector mapping; nonpartitioned PFA; Sethi Markov; controller synthesis certificates. (DOC-ONLY.)

## 5. Loop infrastructure

No `claude` CLI on PATH (VERIFIED). `codex exec` 0.163.0-alpha at `C:/Users/nigel/.codex/plugins/.plugin-appserver/codex.exe`, exec/resume flags verified. ARIS (wanshuiyin Auto-claude-code-research-in-sleep) vendored as skills in `research/codex-autoresearch` (`.agents/skills`, `.aris/upstream` at `a3a847b`); prompt-driven, no daemon. A native loop was built at commit `20544b7` (`scripts/promising_directions/research_loop.py`; 7 tests pass; one smoke cycle completed).

## 6. Audit limitations

Simulation-level results were not re-run in full (see `06_H2C_AND_HG_REPRODUCTION.md`). Statuses not marked VERIFIED are DOC-ONLY. Nothing here constitutes confirmatory evidence.
