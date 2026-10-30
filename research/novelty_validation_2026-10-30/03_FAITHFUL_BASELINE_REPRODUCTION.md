# 03. Faithful baseline status (Phase B)

I reproduced **no** published method from the paper text in this programme. The table separates what the repository
had already established from what I ran. Labels: VERIFIED_REPRODUCTION / FAITHFUL_ADAPTATION / SOURCE_INSPIRED / UNVERIFIED.

| comparator | status | basis |
|---|---|---|
| Active-RCPS fixed-target FTL component (Xu et al.) | **VERIFIED_REPRODUCTION of a component** (repository, not by me): author code at `a67f85d`, max log-wealth diff 1.3e-15 at delay 1; learned querying / grid inversion **not** reproduced | `docs/exhaustive_evaluation/BASELINE_COVERAGE.md` |
| Podkopaev–Ramdas supervised monitor | **SOURCE_INSPIRED** — local Hoeffding-stitched CS (`d2` `pr_style`, repo `pr_cs`); the paper's empirical-Bernstein/betting CS is **not** implemented; MAPIE `RiskMonitoring` is binary-risk only (repo audit), so no faithful cost-loss comparator exists in released code | repo audit + my D2 |
| PPRM (Zhang et al.) | **SOURCE_INSPIRED** — repo's `pprm`/`pprm_tight` are betting adaptations; PM-EB / PPRM eq. 19/22/27 *formula adapters* exist (repo round 2). The paper's CM-EB with sliding-window η_t is **not** reproduced; its experiments (CIFAR10-C, LLM, telecom) were **not** attempted | repo + my reading of §3 |
| Betting on Predictions (Tenzer et al.) | **UNVERIFIED** — different null (label/concept shift) and needs unlabeled marginal; no adaptation to the cost null exists | my reading of abstract/§3–4 |
| Hsu–Shekhar | **excluded** with a recorded measurability obstruction (repo `HSU_SHEKHAR_APPLICABILITY.md`) | repo |
| CUSUM / Page-Hinkley | **SOURCE_INSPIRED**; repo shows PH cumulative-minimum ≡ CUSUM; threshold-calibrated paired CUSUM ran on 11,500 paths (repo) — "no equal-safety superiority" | repo |
| SR / e-detectors | **FAITHFUL_ADAPTATION candidate** (`sr_edetector`), ARL ≠ finite-horizon error | repo; not independently re-run here |
| Pooled Kelly, discounted Kelly, ONS (cost-only) | local reference implementations (`pp_cost_tight`, `fix_cost`, `pp_cost_guided cost_ons`); exact-reduction checked in my test | repo + `tests/` |
| CAMS, Challenger, Drift2Act, robust-FSC / CPOMDP | **UNVERIFIED** (not re-implemented; robust-FSC code retrieved at `0cc828d` but Storm/Gurobi imports unaudited) | repo |

## Gate B

> IF H2c does not outperform the strongest faithful published comparator on a registered, matched problem THEN report the failure and stop H2c-specific method development.

* **No faithful published cost-null comparator exists** to be outperformed, so superiority over a published method is **UNVERIFIED** and cannot be claimed.
* The matched, registered problem I could run (D2, same stream/proxy/labels/delay/calibration/α) **does** have a faithful *within-class* comparator set (cost-only Kelly/ONS): H2c is **later** than them in every label-rate (07 §3).
* Matched-null caveat: a Brier-risk detector tests a different null; I did not call any Brier method economically inferior, and none was run on D2.

**Gate B: FAIL (no demonstrated advantage over a matched comparator on real data; no published comparator beaten). H2c-specific method development stops.**
