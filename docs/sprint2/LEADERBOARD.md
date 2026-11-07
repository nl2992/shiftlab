# Sprint 2 research leaderboard and supported verdicts

Updated 2026-11-05 from the frozen sprint specification, candidate ledgers, Round-5 outputs, WP1/WP2
reports, and the amended Xu comparator-class analyses. This is a decision aid, not a pooled ranking
across incomparable regimes. Lower `J` is better. Empirical risk rates are not theorem guarantees.

## A. Economic performance

| Rank / candidate | Evidence and economic result | Scope and verdict |
|---|---|---|
| 1. P6_LRMD_U | Round-5 100-seed ΔJ vs parent M_LRMD_SUI: −10.9 [−13.2,−8.5] F1 late-800; −8.7 [−10.6,−6.8] F1 late-1200; −11.8 [−14.3,−9.2] W late-1000. Corrected 100-seed comparison vs same-sample selected certificate ports: −24.1 [−28.5,−19.8], −12.2 [−15.1,−9.3], −23.1 [−27.2,−18.9] on late regimes; a paired max-statistic bootstrap across the five certificate ports in that run gives simultaneous one-sided 95% upper bounds −20.37/−9.57/−19.26 for those late contrasts. Reversal contrasts were +25.9 [+19.5,+32.3], +4.9 [+1.0,+8.9], with no simultaneous superiority. Xu's larger -15.5/-12.4/-15.2 contrasts were against the acquisition adapter, not the parent. | Scoped synthetic late benefit against common-contract certificate ports, with a reversal cost penalty. Comparator multiplicity is adjusted only within that five-port set and regime; post-development, cross-regime/candidate selection remains, and ports are not author-native. The completed post-development twin-bike replay gives P6 promotion .076 (20-split-cluster bootstrap 95% CI [.036,.122]), which does not clear the .0936 screening convention; P6−parent cost CI includes zero. The post-development 20-seed all-14-source real replay also shows no equal-source cost advantage: P6 costs 24.41 more than M_LRMD_SUI (higher on 11/14 sources, lower on 2, tied on 1) and costs more than D2, RMM and gated adaptive-range on the equal-source mean. These are reused-stream cost diagnostics with no late-event labels or independent transfer. |
| 2. R5 risk-aware economic deployment | All-14-source post-development real replay (20 policy seeds/episode; 230 episodes) gives equal-source mean J 404.22 for R5 vs 404.91 D2 (mean of source means Δ −0.68), vs 412.39 economic replacement and 414.14 gated adaptive-range; source-level effects are mixed. It is descriptive on exposed streams and has no pooled uncertainty. Prior development-selected Track-R points: R15/R20/R25 alpha .02 risk .138 [.079,.230], cost 357.5 [351.3,363.7]. New-seed fixed-alpha follow-up (100 seeds/regime) found promotions 15/100 on F0 null, 26/100 on rho=.8 null, 24/100 on rho=.95 null; paired six-alternative net cost was 10.23 lower than D2 (95% CI for the advantage [8.05,12.41]), but R5 lost to D2 on late and strong-persistence alternatives. | Mixed simulator evidence; the fixed-alpha sensitivity does not validate the selected frontier or establish risk control. Selection uncertainty remains, and R6 gives no better joint frontier. See `family_r/R5_round5_results.md`. |
| 3. H2 D2+A5b with spacing | V2-scoped candidate; 1,000-seed follow-up had 1–8/1,000 promotions on four tested first-order Markov nulls, while D2 had .192/.660/.815 on persistent nulls. | Its 100-seed screen loses to D2 by +67 to +84 on persistent alternatives; 14-source equal-weight real cost is +81.2 vs D2 and +71.7 vs `gated_adaptive_range+front`. Post-development and reused data; no transferable economic advantage. |
| 4. E_rb rollback extension | On 16 real reversal episodes, E_rb minus RMM was −13.0 gated, −12.4 DISCERN, −19.6 SMCS, −17.1 GAR; only 2/4 intervals excluded zero. A preregistered 100-seed post-development synthetic follow-up found −6.65 (95% t CI [−7.31,−6.00]) averaged over three reversals and four matched hosts. | Supported in these simulator reversals; real-reversal evidence remains descriptive and low-cluster. Not a general null or real-transfer guarantee. |

**Interpretation:** Do not call this an overall economic SOTA ordering. P6, R5, H2 and E_rb target different settings and use different evidence maturity. No candidate has a confirmed broad economic win over the strongest applicable published comparator.

## B. Statistical reliability and predictive/economic outcomes

| Method / result | Measured reliability | Harm / limitation |
|---|---|---|
| A5b (V2) | As the comparator arm in the 1,000-seed P6 null follow-up: promotions 1/1,000 F0; 2/1,000 Markov rho=.8; 3/1,000 rho=.95; 16/1,000 order-2; 60/1,000 semi-Markov; 176/1,000 HMM. | Only the tested first-order stationary Markov cells are in-class for A5b. Order-2, semi-Markov and HMM cells are misspecification stresses, not theorem-failure tests. In the same P6 run, P6_LRMD_U recorded 10, 2, 6, 13, 79 and 139 promotions, respectively; its separate P4 HMM follow-up result is reported in `family_p/P4_hmm_round5.md`. Twin-bike and WP2 bike uncertainty remain. |
| WP2 real twins / V1 comparator pool | The amended WP2 pool excludes Xu from published-method rankings and powered sets; it retains Xu in descriptive pooled V1 tables as a ShiftLab certificate + Xu acquisition composite. A5b's twin2-bike V2 promotion estimate is .125 [.058,.192], while metro .000, Beijing .014, appliances .042 and household .033. | Bike upper bound exceeds .0936; V2 marginal null is distinct from the V1 conditional-null target under its stated assumptions; empirical rates do not establish validity. Pooled H2/H4 summaries are descriptive; dependence-robustness is not universal. |
| RMM | On the primary WP1 real late class, 10 episodes / 5 source clusters; amended best published-certificate comparator remains gated-adaptive-range+front. | H_late remains **NOT_SUPPORTED**: no host meets the interval criterion against that comparator. The real-late result is descriptive and selection is same-sample. |
| E_rb | Rollback improves reversal cost on four hosts, with 2/4 CIs below zero in the existing real sample; post-development 100-seed synthetic reversal follow-up averages -6.65 versus matched RMM (95% t CI [-7.31,-6.00]). | Supported in the registered simulator reversal setting only. It does not correct RMM's first-promotion twin-null rate or establish real-data transfer. |

These rows do not compare error rates across different nulls as if they were the same estimand. Consult [SOTA_BENCHMARK_AUDIT.md](SOTA_BENCHMARK_AUDIT.md) and [WP2 decision-flag audit](wp2/DECISION_FLAG_AUDIT.md) for exact construction and implementation limits.

## C. Main-track contribution potential

| Rank | Contribution direction | Current verdict | Main missing evidence |
|---|---|---|---|
| 1 | **Dependence-aware deployment evaluation / P2**: separate conditional and marginal nulls, known-null twins, paired prediction-loss outcomes, and all-in excess economic cost. | Strongest paper opportunity; credible empirical-methodology direction, not yet a completed main-track contribution. | Independent reviewer findings; author-code comparisons where feasible; independent untouched-data confirmation; application utility data are needed for any application-level decision-harm claim; final claims/reproduction package. Application-level decision harm is not identified from current records. A universal theorem is optional. |
| 2 | **RMM + certified rollback / P1**: restart monitoring and post-switch reversal repair. | Scoped synthetic RMM benefit is preserved. Real late-improvement test is not supported against the best applicable certificate; E_rb has a modest real reversal signal. | Register/run fresh-seed reversal check; more real reversal/late clusters or state insufficiency; formal joint error accounting for promote-then-rollback; amended result-to-claim review. |
| 3 | **A5b × D2 hybrid / H2, R5** | Useful design and cost-risk diagnostics, but not currently a contribution claim: H2 loses on fresh-real cost; R5 has an exploratory selected frontier and a mixed fixed-alpha follow-up with elevated tested-null promotions. | Resolve the elevated R5 null promotions; any further claim needs a prespecified operating point and independent evaluation, plus real-transfer evidence. |
| 4 | **Published-host transfer / T family** | Negative and compatibility evidence. T1 is worse economically than MP, D1 and D6; T2–T6 show host/evidence trade-offs rather than a transferable gain. | No broad algorithmic claim is supported. Preserve as benchmark and negative evidence. |

## 24-candidate execution matrix

The registry is [candidates.json](candidates.json), with exact code/results and dispositions linked to each family ledger. All 24 brief IDs have recorded outcomes; 23 are algorithm candidates with implementation and development-screen evidence, while P2 is an analysis-only workstream row. Statuses are not equivalent to success: negative findings remain negative, and development screens do not count as Round-5 validation.

The family cost-risk points are consolidated in [COST_RISK_PARETO.md](COST_RISK_PARETO.md). Internal
review scope and unresolved external review are in [INDEPENDENT_REVIEW.md](INDEPENDENT_REVIEW.md);
commands and run provenance are indexed in [REPRODUCIBILITY.md](REPRODUCIBILITY.md). The focused
combination decision is documented in [ROUND6_FOCUSED_COMBINATIONS.md](ROUND6_FOCUSED_COMBINATIONS.md).

| Family | Candidate disposition summary |
|---|---|
| H1–H6 | H2 is scoped promising on synthetic V2 evidence; H4 has limited delay/label effect without power gain; remaining variants are negative or not advanced. No independent Round-5 validation. |
| R1–R6 | R1/R5 provide development-selected risk-cost points (R5 follow-up is mixed); R2 has a distinct conditional-mean target; R3/R4 are costly; R6 does not establish a better joint frontier. |
| T1–T6 | T1 required comparisons are present but negative economically; remaining work maps host/evidence compatibility, dependence sensitivity and no supported interaction gain. |
| P1–P6 | P1/P3 negative; P2 objective analysis; P4 misspecification study; P5 exploratory multi-model extension; P6_LRMD_U synthetically promising but has stationary, misspecification and twin-null concerns; P6_RRD negative. |

## Supported final verdicts

- **No universal SOTA claim.** The Xu policy in these runs is an acquisition adapter combined with ShiftLab's certificate, not Xu et al.'s published risk-control method.
- **Best current contribution opportunity:** empirical evaluation of conditional versus marginal deployment validity, paired predictive outcomes, and excess economic cost under dependence (P2). Its scope is empirical and benchmark-based; current records do not identify application-level decision harm.
- **Best scoped method opportunity:** RMM for synthetic late improvement; E_rb now has a preregistered 100-seed post-development simulator reversal sensitivity (-6.65 net cost, 95% t CI [-7.31,-6.00] versus matched RMM across three regimes and four hosts). P6's corrected certificate-port comparison is complete; the reused twin-bike replay does not clear the null screening convention. The WP1 real-late claim is not supported, and the reversal result is not real-world or untouched confirmatory evidence.
- **Continue / pivot / stop:** continue P2 as a benchmark paper candidate; pivot P1's real-world claim to the measured negative/limited result and prioritize rollback validation; stop advancing H/T configurations as broad economic winners absent a new mechanism.

## Reproduction and audit commands

```sh
uv run pytest -q tests/sota_sprint tests/sprint2
uv run python scripts/sota_sprint/analyze_validation.py --amendment-dir docs/sprint2/validation_amendment_20261104
uv run python scripts/sota_sprint/late_real.py report --primary outputs/sprint2/WP1/primary --twin outputs/sprint2/WP1/twin --sens outputs/sprint2/WP1/sens_* --classes outputs/sprint2/WP1/classes.json --amended-no-xu --out docs/sprint2/wp1/results_amended_no_xu.json
uv run python scripts/sota_sprint/wp2_analyze.py --amendment-dir docs/sprint2/wp2/amended_no_xu
```

The separate amended outputs are post-hoc comparator-class sensitivities. They preserve the registered
results and do not correct for same-evaluation-sample comparator choice. Raw data remain under
gitignored `outputs/` or the dataset directories; do not add licensed/raw/large artifacts to Git.
