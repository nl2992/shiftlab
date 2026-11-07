# GAVE-R investigation: summary, grading and assessment (WP6)

Branch `research/gave-r-2026-11-06`, cut from `main@7354480a`, 2026-11-06. Development/screening
only: no confirmation seeds consumed. Every number below is copied from a results document in
`docs/gaver/` (the source file number is given in each row). Plan and progress log:
[00_PLAN_AND_TODO.md](00_PLAN_AND_TODO.md). The source report's scores are hypotheses; nothing here
is a confirmatory result.

## 1. Bottom line

The full GAVE-R combination (Gap-Mix evidence x delay-gated PAVE acquisition, with FreshCheck dropped
before integration) does **not** pass screening, so there is no integrated method to promote. Two
fragments survive as smaller, separate findings. (i) Gap-Mix with a declared dependence bound
rho_bar = 0.8 is a valid evidence process under that bound, including under adaptive acquisition
(worst null upper bound 0.051-0.055 vs 0.395 for the frozen DSS evidence), and it is *substantially*
more powerful than the existing valid Markov-LR evidence (14.7% lower J/T, a post-hoc arm), but it is
not cheaper than the invalid iid DSS evidence (5.1% worse). (ii) A delay-gated PAVE rule gives a
*meaningful* 4.4% gain in one long-delay cell family (d = 50) and is safer than DSS under dependence,
but nothing outside that niche. Extending Gap-Mix beyond rho 0.8 (WP1b) and FreshCheck as a value
component (WP3) were eliminated. Recommendation: **stop the joint method; pivot to reporting the two
fragments and the side-findings as baselines/findings for the decision-ranking benchmark paper**,
keeping a narrow evidence paper open only if the Sethi et al. overlap leaves room (sections 7-8).

## 2. Per-component table

Grades: substantial >= 10%, meaningful 3-10% with CI excluding 0, small 1-3%, negligible < 1%
(relative reduction of mean cost J/T unless a detection difference is stated). "Screening verdict" is
the registered bar in 00_PLAN (null UCB <= 0.1 at rho <= 0.8; at least a small gain over the strongest
in-repo comparator in target cells; not materially worse in neighbouring cells).

| Component | What was tested | Null validity | Value | Fair grade | Screening verdict | Commits | Doc |
|---|---|---|---|---|---|---|---|
| Gap-Mix (`exact0.8_s4`; envelope `env0.8_s4` as ablation) | Exact-gap Markov LR, certified null sup, 4-start restart mixture, declared rho_bar = 0.8; uniform calendar, T = 1000, d = 10, B in {100, 250}; null 500 streams x 8 cells; power 24 cells x 60 seeds | UCB <= 0.078 at rho <= 0.8 (envelope <= 0.067); fails at undeclared rho = 0.95 (FP .87-1.00); iid gates UCB .42-.54 at rho .8, B 250 | Detection +0.367 [.342, .394] vs existing Markov LR with cost -0.074 [-.080, -.068]; envelope +0.295; 10.7 points below the invalid iid_repo32 (-0.107 [-.123, -.090]) | Substantial vs the strongest valid in-repo comparator, conditional on declared rho_bar | PASS (within rho <= 0.8) | `d636765e` `81c41c4e` `6100091e` | 10 |
| Gap-Mix rho-robust extension (WP1b) | Constructions valid to rho = 0.99 (fixed cap, CS plug-in, gated ladders, envelope+CS) plus plain-mixture negative control; null 500 x 10 cells, power 1440 streams | Valid variants UCB <= 0.041 incl. rho .99; plain mixture invalid (FP .79-1.00) | Best valid (`exact0.99_s4`) detection -0.059 [-.076, -.042] vs Markov LR; gain fraction -0.16 against required >= 0.5; gated ladders -0.18 to -0.22; envelope+CS -0.39 | Meaningful to substantial loss | ELIMINATED (pre-declared criterion failed) | `a924a0a0` `6d9e71b2` `23dc2248` `5eb85631` | 11 |
| PAVE (as specified) | Rollout value-of-label governor on unchanged DSS evidence; 31 cells x 60 seeds vs DSS, uniform, undecided-only, `episode_front`; 7-cell ablation; null grid | UCB <= 0.0283 (reserve on, n 210-500) and <= 0.0586 (reserve off, n 120-140) at rho <= 0.8; DSS up to 0.269; not safe at rho .95 | d <= 10: 13 of 22 cells worse than DSS (CI excl. 0), 0 better; f3_rho0 d1 regression cell 16-19% worse than DSS. d = 50 regression cell, reserve off: 8.2% better than uniform = DSS, 6.0% better than `episode_front` (CIs excl. 0); d = 50 mean 3.4% over uniform, 5/9 cells better | Meaningful, scoped to d = 50 (post-hoc reserve-off); worse elsewhere | FAIL as specified; one narrow positive | `a7116a16` `9912008e` `c4b1e0b6` | 20 |
| PAVE, delay-gated (WP5 form) | PAVE iff d >= 2T/(B+2) (exactly where DSS already falls back to uniform), reserve off; else DSS; 9 gate-on cells (all d = 50, B/T .05-.1) | Raw PAVE worst UCB 0.039 at rho <= 0.8 (DSS 0.196), 500 streams/cell; gated 0.036; at rho .95 raw 0.468 (not safe) | Gate-on: -0.0186 [-.0237, -.0137], 4.4% better; regression cell .4095 -> .3584 (12.5%); pooled over all 31 cells 1.4% (identical to DSS in the other 22 cells) | Meaningful (one cell family) | Passes only as a niche rule | `a52a52ae` `8fe567a7` `dfdb7cb8` | 50 |
| FreshCheck (fresh post-switch e-process, optional 20% reserve) | 12 cells x 60 seeds (persistent, reversal, transient; d in {1, 10}); boundary-null and keep-null studies, 500 streams per cell | Boundary-null false promotion pooled UCB 0.017 (1000 streams); keep-null false rollback 2/584 (upper 0.012) | Reversal harm -79% (CI 71-88%) vs promotion-only, but harm 0.0527 vs existing Page-CUSUM 0.0094; persistent value lost 17.7% with reserve (~5% without); equal-weight mean J/T: CUSUM .488, E_rb .489, FreshCheck .496, two-phase .518 | Substantial loss in persistent value; no gain over CUSUM | FAIL on value, PASS on null safety | `2a8b695b` `bd8316ba` | 30 |
| E_rb (ported comparator) | Port of `origin/codex/sprint2-leaderboards@297a706e`, same cells and seeds | Boundary-null FP 10/1000 (UCB 0.018); persistent false rollback 0/2000; keep-null 1/775 (UCB 0.007) | Reversal J/T .508, equal to FreshCheck without reserve; FreshCheck with reserve beats it by 5.4% on reversal, loses 11.9% on persistent | Meaningful gain offset by substantial loss | Comparator, not a candidate | `5521a269` `199eb22b` | 30 |
| Two-phase persistence (adaptive port) | `dive/persistence_promotion.py`, adaptive phase boundary | 0/1000 boundary-null FP (UCB 0.004) | Reversal harm 0.0027 only because it almost never promotes (0.01 switches per stream; 58/775 keep-null streams promoted); persistent 17.8% worse than FreshCheck; worst equal-weight J/T | Substantial loss | Comparator, not a candidate | `5521a269` | 30 |
| Integrated GAVE-R (Gap-Mix x delay-gated PAVE) | 2x2 evidence x acquisition in the DSS shell; 31 alternative cells x 60 seeds; 29 null cells x 500 streams | Gap-Mix worst UCB 0.051 with DSS acquisition, 0.055 with delay-gated PAVE (rho <= 0.8); frozen DSS evidence 0.395; both Gap-Mix arms fail at rho .95 (up to .998) | vs DSS, all 31 cells: joint +0.0161 [+.0138, +.0186] (4.2% worse). Gate-on: joint 1.7% better than DSS but 2.8% worse than PAVE alone; interaction -0.0064 [-.0106, -.0026] (sub-additive); worse than `episode_front` pooled (+0.0052 [+.0013, +.0089]) | Worse; adverse interaction | FAIL on value | `a52a52ae` `8fe567a7` `dfdb7cb8` `d722c059` `692caef5` | 50 |

Notes. Gap-Mix against iid DSS evidence in the DSS shell: +0.0197 [+.0176, +.0217], 5.1% worse, worse in
28 of 31 cells, better in none. Against the valid Markov-LR evidence in the same shell (post-hoc
amendment A1): -0.0704 [-.0734, -.0675], 14.7% better (substantial); gate-on 7.4% (meaningful). The mlr
arm detects only 21.8% of alternatives and costs 23.2% more J/T than DSS (50).

## 3. Positive findings worth keeping

1. **iid/DSS evidence is miscalibrated under dependence.** Frozen DSS evidence: null UCB 0.269 at rho 0.8
   (WP2, B/T .1, d 1), 0.395 at rho .8, B/T .25, d 10 (WP5), 0.983 at rho .95. The WP1 repo-default iid gate
   has UCB .542 at rho .8, B 250 and .997 at rho .95, B 250 (10). Consistent with the earlier Atlas
   dependence-safety failure; a descriptive result, not a new method.
2. **Gap-Mix is the best valid evidence at a declared rho_bar of 0.8.** +36.7 points detection over the
   existing Markov LR with lower cost (substantial). The 4-start restart mixture is essential (exact0.8 late
   detection .939 vs .511 with a single start). Gap-10 thinning is a cheap strong baseline at rho <= .8
   (UCB <= .098, detection .693).
3. **Gap-Mix stays valid under adaptive acquisition**, empirically: worst UCB .051 (DSS acquisition) and
   .055 (delay-gated PAVE), 500 streams x 29 cells. This cannot rule out true rates of a few percent.
4. **PAVE gives a meaningful long-delay gain** (regression cell 12.5% in WP5; 8.2% vs uniform on fresh seeds
   in WP2) and is **safer than DSS** under dependence: raw PAVE worst UCB .039 vs DSS .196 at rho <= .8 (500
   streams), though mostly because it promotes less often, not through a certificate.
5. **Ablation signal.** Pending-aware state and deadline value together improve PAVE by -0.018 [-.025, -.011]
   cost per round (reserve off); the rollback reserve hurts (+0.034 [+.026, +.041]) (20).
6. **Heuristic rollbacks lack level control; E_rb and FreshCheck have it.** At the keep-null boundary (benefit
   exactly h) existing Page-CUSUM, hysteresis and the cost-threshold rule roll back in 772/773, 713/722 and
   706/775 promoted streams (91-100%), versus 2/584 (FreshCheck) and 1/775 (E_rb). The reused-wealth
   ablation rolls back in 47-62% (no level argument). Level control is therefore not unique to FreshCheck
   (correction recorded in the WP3 rerun). A safety property, not a cost gain.
7. **Process findings.** The d = 50, B/T .05 regression cell is a uniform-acquisition cell because DSS's
   delay switch reduces to uniform when d >= 2T/(B+2) (01); the PAVE niche is exactly that regime.
   `episode_front` is a strong in-repo comparator that the joint method does not beat pooled. A cross-branch
   search found the E_rb and two-phase comparators that a single-branch search had declared missing.

## 4. Negative findings and unrepaired cells

- Full GAVE-R fails on value. The joint gain in gate-on cells is smaller than PAVE alone (interaction
  -0.0064 [-.0106, -.0026]; all-cell -0.0019 [-.0031, -.0007]). A plausible reason, untested: Gap-Mix needs
  more evidence per promotion, which removes part of the earlier-detection benefit PAVE supplies.
- WP1b: removing the rho limit costs the whole power advantage. The CS for rho cannot certify rho below about
  .81-.96 even when the truth is 0 (mean final upper bound), so data-driven variants behave like a fixed
  rho_bar of ~.95-.99. Plain rho_bar mixtures are invalid (negative control). A mis-declared rho_bar is
  Gap-Mix's dominant risk (FP .87-1.00 at rho .95, .95-.99 at rho .99).
- No gap-aware variant beats the invalid iid gates in power.
- PAVE as a general governor fails: 0 of 22 d <= 10 cells improved over DSS, 13 worse (CI excl. 0). Early
  development iterations (v0, v1) never promoted (20).
- FreshCheck: worse post-reversal harm than the existing Page-CUSUM (0.0527 vs 0.0094); two-phase avoids
  harm only by not promoting.
- **Regression cells unrepaired.** `f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1`: PAVE alone is 16-19%
  worse than DSS in WP2; in WP5 the gate is off (PAVE equals DSS, .3964), Gap-Mix worsens it by 3.5%
  (.4101), and `episode_front` is better (.3415). The d = 50 cell
  `on0.6_L1_strong_harmful_d50_b0.05_s0.1` is improved by PAVE alone (.4095 -> .3584) but not by Gap-Mix
  (`gapmix:dss` .4161, joint .3791). Pooled over the 9 gate-on cells `episode_front` beats the joint method
  (+0.0067 [+.0015, +.0118]).

## 5. Limitations

- Development/screening seeds only (registered blocks inside 101000000-101259999); no confirmation seeds, no
  2,000-stream null escalation (nothing passed on value).
- One synthetic family (the Atlas stationary two-state Markov `Family3CellSpec` cells, plus WP3's own iid
  Bernoulli generators), T = 1000, constant fixed delays, boundary nulls; no real data, no informative delay.
- Post-hoc choices: PAVE reserve off (chosen after the ablation, replicated on fresh seeds for the
  evaluation); the d >= 50 scope and delay gate; the `mlr` arm (amendment A1, added after alternative-cell
  results were seen); WP3's own generators; the envelope arms as ablations.
- The gate-on evidence (9 cells) is effectively one d = 50, B/T <= .1 cell family; d = 10 with B/T .25 and
  d = 50 with B/T .25 have no alternative cells.
- No Holm or simultaneous correction; CIs are per contrast. "Valid" means the null UCB passed at 500 streams
  per cell, not a proof.
- Validity arguments cover the declared stationary Markov null with deterministic calendar and constant
  delay. **Closed-loop validity (requests depending on observed values), informative delay and
  non-stationary nulls are unproven**; the adaptive-acquisition result is empirical.
- PAVE is a hand-built heuristic with two scalars tuned on 7 cells; FreshCheck stakes and mixture were not
  tuned; no source-faithful external comparators (Banerjee-Veeravalli, ASI-style controllers).

## 6. Decision-tree outcome (report section "Decision tree after the first experiments")

Full GAVE-R is ruled out (interaction negative with CI excluding 0; FreshCheck failed). "PAVE wins
strongly" is not met (meaningful only, one cell family). "FreshCheck uniquely fixes reversal" is not met.
The closest branch is **"Gap-Mix safe + powerful, PAVE neutral"**, in a qualified sense: safe within
declared rho <= 0.8 under adaptive acquisition and substantially more powerful than the existing valid
evidence, but not cheaper than the invalid DSS default. The practical outcome is the report's last branch,
**"all fail but the Atlas trade-off survives: feed the benchmark paper"**, with the evidence-paper branch
held open pending the prior-art check (50, section 1).

## 7. Prior-art positioning (40_PRIOR_ART_CHECK.md; abstract/snippet level only)

| Component | Closest threats (overlap rating in 40) |
|---|---|
| Gap-Mix | Sethi et al., arXiv 2602.17587 (HIGH; Markov sequential testing, optimal stopping); Lau & Tay, arXiv 1912.11693 (MEDIUM-HIGH; switching-cost sampling with GLR CuSum); Gafni, Iyengar & Zeevi, arXiv 2602.11406 (MEDIUM; restart-style CUSUM) |
| PAVE | Gong & Zhang, ICML 2026 (HIGH; paid observations with cost-aware regret); Zrnic & Candes, ICML 2024 (MEDIUM-HIGH; budgeted label acquisition); The Challenger, arXiv 2512.18390 (MEDIUM) |
| FreshCheck | The Challenger (MEDIUM-HIGH; incumbent/challenger switching); Drift2Act, arXiv 2603.08578 (MEDIUM); WATCH, ICML 2025 (MEDIUM) |

Gap-Mix's distinct elements would have to be realised gaps between actively queried delayed labels, the
certified composite null and the restart mixture, positioned against Sethi et al. and Lau & Tay.
**Unverified:** whether Sethi et al.'s optimal test is likelihood-ratio or e-process based (the abstract does
not say; this decides whether the Markov claim survives); Gong & Zhang, Zrnic & Candes, WATCH, Gafni et al.,
Lau & Tay, The Challenger and Csillag et al. are SNIPPET-level only (no full texts read); the PPRM (arXiv
2602.02229) ICML 2026 venue is not confirmed; the report's `cite...` tokens were never resolved; phrasings
such as "post-promotion evidence reset" and "restart e-process Markov" were not searched exhaustively.
Nothing in this branch is a novelty claim.

## 8. Continue / pivot / stop assessment

| Item | Assessment |
|---|---|
| Joint GAVE-R | **Stop.** Fails value, sub-additive, does not repair the f3_rho0 d1 regression cell. |
| FreshCheck as a value component | **Stop.** Optional certified-rollback wrapper only; E_rb is an equally good existing option. |
| Gap-Mix rho-robust extension | **Stop.** Eliminated (WP1b). |
| Gap-Mix at declared rho_bar = 0.8 | **Continue, narrowly**, as a baseline/finding (valid, substantial vs the valid comparator). A stand-alone evidence paper only if the Sethi et al. full-text check leaves room, and then it needs fresh seeds, a 2,000-stream null, mis-declared-rho_bar tests and a closed-loop validity argument. |
| Delay-gated PAVE | **Pivot to a niche finding.** Needs fresh seeds, more cells with d >= 2T/(B+2) (d = 10 and d = 50 at B/T .25) and a 2,000-stream null before any claim. |

**Recommendation: pivot to reporting.** Give the benchmark paper the dependence-miscalibration finding, the
Gap-Mix validity and price-of-validity result, the PAVE d >= 50 niche and the rollback level-control finding
as graded baselines and findings, each labelled development/screening. Small and meaningful verified effects
are kept, but the evidence does not support a new-method claim. The planner decides between this and the
evidence-paper branch.

## 9. Reproduce

Branch head when this file was written: `5be2fa99` (this file's own commit follows it; see
`git log -1 -- docs/gaver/90_SUMMARY.md`). Seed blocks are registered in `configs/seed_registry.yaml`
(allocated in WP0, `a458a21d`). Interpreter: the shift-research-starter `.venv`. Data are synthetic and
generated on the fly. Long stages ran detached and are resumable.

```bash
cd "C:/Users/nigel/OneDrive/桌面/ICML/shiftlab-gave-r-2026-11-06"
export PYTHONPATH="$PWD/src:$PWD/scripts" PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
PY="C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/.venv/Scripts/python.exe"

# WP1 Gap-Mix (10): hours on a busy machine
$PY scripts/gaver/run_gapmix_null.py --workers 10
$PY scripts/gaver/run_gapmix_power.py --workers 8
$PY scripts/gaver/run_gapmix_summarize.py
# WP1b (11)
$PY scripts/gaver/run_gapmix_rho_power.py --workers 4
$PY scripts/gaver/run_gapmix_rho_null.py --workers 4
$PY scripts/gaver/run_gapmix_rho_summarize.py
# WP2 PAVE (20): first copy outputs/failure_atlas_v1_cycle5/family3 and cycle7/tuning from main (read-only)
$PY scripts/gaver/run_pave_eval.py --stage tune   --workers 14
$PY scripts/gaver/run_pave_eval.py --stage eval   --workers 14 --kappa 0.1 --q 0.03
$PY scripts/gaver/run_pave_eval.py --stage ablate --workers 14 --kappa 0.1 --q 0.03
$PY scripts/gaver/run_pave_eval.py --stage eval2  --workers 10 --kappa 0.1 --q 0.03
$PY scripts/gaver/run_pave_eval.py --stage null   --workers 12 --kappa 0.1 --q 0.03
$PY scripts/gaver/run_pave_eval.py --stage null2  --workers 10 --kappa 0.1 --q 0.03
$PY scripts/gaver/make_pave_tables.py
# WP3 FreshCheck (30)
$PY scripts/gaver/run_freshcheck_main.py --workers 10
$PY scripts/gaver/run_freshcheck_main.py --workers 12 --methods erb,erb_a05,two_phase --tag ext
$PY scripts/gaver/run_freshcheck_analyze.py
# WP5 integration (50)
$PY scripts/gaver/run_gaver_factorial.py --stage alt      --workers 8
$PY scripts/gaver/run_gaver_factorial.py --stage pavenull --workers 8
$PY scripts/gaver/run_gaver_factorial.py --stage null     --workers 8
$PY scripts/gaver/run_gaver_analyze.py
# tests and lint
$PY -m pytest tests/test_gaver_gapmix.py tests/test_gaver_gapmix_rho.py tests/test_gaver_pave.py \
  tests/test_gaver_freshcheck.py tests/test_gaver_integrated.py -q
$PY -m ruff check src/shiftlab/gaver scripts/gaver tests/test_gaver_*.py
```

Raw outputs are in the gitignored `outputs/gaver/{wp1,wp1b,wp2,wp3,wp5}/`. Code commits: WP0 `a458a21d`;
WP1 `d636765e`, `81c41c4e`; WP1b `6d9e71b2`, `23dc2248`; WP2 `a7116a16`; WP3 `2a8b695b`, `5521a269`;
WP5 `a52a52ae`, `8fe567a7`, `dfdb7cb8`. Result documents: WP1 `6100091e`, WP1b `5eb85631`, WP2
`9912008e`/`c4b1e0b6`, WP3 `bd8316ba`/`199eb22b`, WP5 `d722c059`/`692caef5`.
