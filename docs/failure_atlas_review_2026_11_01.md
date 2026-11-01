# Failure Atlas: evidence review and current direction

Date: 2026-11-01. Status: development evidence and prospective decision record.

**Cycle-7 completion:** the 200-seed full-registry validation and artifact audit are now
complete. A1 and whole-acquisition A4 pass; neighbourhood A2 and dependence A3 fail.
See [the cycle-7 decision](failure_atlas_cycle7_decision_v1.md) and
[complete validation tables](failure_atlas_cycle7_validation_results_v1.md).
Earlier next-step language below records the pre-validation review, not outstanding cycle-7 work.

## Location and provenance

The live Atlas is in `shift-research-starter`, branch `main`, starting HEAD
`e61a3b0`. The older `research/monitoring-to-decision-value-2026-10-30` worktree
contains its early implementation; the six-cycle ledger and DSS work are on main.
Relevant commits: `88f7687` (cycle-6 findings), `6a019ea` (acceptance Amendment 8),
`2bfdd64` (DSS positioning), `d37a938` (DSS and tuning), `e61a3b0` (dependence baselines).
The pre-existing untracked `docs/hgxh2c/FINAL_REPORT.md` is unrelated and preserved.

This review follows the renewed user instruction: find a common failure among strong
algorithms, diagnose it, and seek a useful repair with modest novelty and competitive
performance. A revolutionary mechanism or new theorem is not required. The historic
benchmark-only recommendation is superseded as a future-work direction, not as evidence.

## What has actually been found

| Finding | Evidence | What it means |
|---|---|---|
| Reproducible cost weakness in delayed, label-budgeted switching | Ledger cycles 1–5; 11 family-3 cells reproduced in cycle 5 | A useful target within the implemented comparator set, not all SOTA everywhere |
| Safety accounts for part of the cost gap | Cycle-5 exact constrained solver, T=6–8; RC exceeds CoV in 0/144 cells | Do not treat the entire gap to a less constrained Bayes policy as removable; no extrapolation to T=1000 |
| Concentrated undecided-state queries can help | Cycle-3 straddle and cycle-4 delay study | Acquisition timing is a plausible practical lever; gain is delay-sensitive |
| Dense correlated labels cause promotion inflation | Cycle 6: rho=.8, B/T=.5, six gates at .405–.970 pooled false promotion | An out-of-contract application failure, not a contradiction of conditional-null guarantees |
| Release-order explanation did not reproduce | Cycle-6 V3 failed | Keep this negative result; it is not an established failure mechanism |
| DSS gap 4 survives its development tuning screen | `outputs/failure_atlas_v1_cycle7/tuning/summary.md` | Candidate worth evaluating, not a validated SOTA win |

DSS tuning used null seeds [160000,160200) and cost seeds [161000,161040).
At rho=.5 and d=1, gap 4 had false-promotion frequencies .010, .035, .015
for budgets .05, .10, .25. Gap 1 had .130, .195, .405. Mean cost across
16 tuning failure cells increased from .342852 (gap 1) to .368797 (gap 4).
This is the actual safety/speed tradeoff; the tuning table has no best-SOTA comparison.
Frozen DSS spec is `5b5c77b635e5`; no retuning is implied by this review.

## Acceptance and claim discipline

Continue toward a method contribution. Known blocking, betting and active-acquisition
ingredients are allowed. Identify the precise new decision rule, explain its practical
effect with an ablation, and compare against the strongest applicable existing rule.
Do not kill a candidate solely because its ingredients or mechanism explanation are known.
Conversely, a contract-specific combination is not automatically novel.

Amendment 8 already removed theorem novelty and 50% Bayes-gap closure as acceptance
requirements. Its registered A1–A4 tests have not been completed. Preserve those thresholds
for cycle 7. A failed threshold may motivate a prospectively registered narrower claim;
it must not be relabelled as a historical pass. Amendment 9 clarifies this distinction.

Keep an absolute safety target. Looking better than an unsafe competitor at rho=.8 does
not establish validity. Fixed thinning does not make dependent labels independent, and
the implemented Markov gate assumes a homogeneous skeleton. Unequal query gaps and
within-run changes are material limits. Strong-baseline names in code are not verified
reproductions of every published SOTA algorithm.

## Next decision

**Completion update:** the Amendment-9 pilot completed the full grid and alternative-cost
comparisons. DSS had lower mean cost than the best of its three pilot comparator gates in
9/11 alternative cells, averaging -0.03908 cost per round across cells. Its maximum null
false-promotion frequency reached 1.00 under strong dependence. The practical timing repair
is promising; unrestricted dependence safety is unsupported. See the dated ledger entry
and `failure_atlas_dependence_pilot_2026_11_01.md` for complete tables and uncertainty.
Promotion bookkeeping is completed by replaying the same alternatives, with no independent
evidence added. The next step is a scoped, frozen full-registry comparison, not new gap tuning.
Markov LR made no promotions in 10/11 alternative cells, whereas DSS correctly promoted
in 17–20 of 20 streams per cell. Thus the promising null comparator is costly in this
late/transient-change setting; its strong null table alone would hide this practical weakness.

The registered pilot covers all 32 dependence configurations and costs on all 11 family-3
failure cells, including adverse cells. Its n=20 frequencies cannot certify alpha=.1 or pass acceptance.
Use its record to decide whether a full frozen cycle-7 comparison is informative.
Before that comparison, freeze the complete comparator registry, neighbour list and
paired aggregation procedure. Match label access, delay, request-time budget, switching
cost and the safety contract. Keep [290000,290200) and confirmation seeds reserved.

If fixed-gap DSS remains unsafe, the next concrete repair to investigate is coupling its
acquisition rule to evidence that models each actual query gap, rather than increasing a
gap until development nulls happen to pass. A gap-aware Markov likelihood is one candidate
under a declared binary Markov model; adaptive acquisition and composite-null likelihood
maximisation need checking before any guarantee. This is a proposed experiment, not an
implemented solution or novelty result. Keep acquisition, evidence and rollback ablations
separate so a gain can be attributed to a specific change. A scoped useful gain is enough
to continue; no universal dominance or revolutionary mechanism is demanded.

## HKUSTDial / ARIS workflow and review limitations

Local skill instructions inspected:
`C:/Users/nigel/.claude/skills/experiment-audit/SKILL.md` and
`C:/Users/nigel/.claude/skills/result-to-claim/SKILL.md`, with reviewer routing and
independence references. A fresh native reviewer is used for a provisional result-to-claim
assessment from primary files. No external cross-family reviewer transport is exposed
in this session; cross-family experiment integrity audit is **REVIEW_UNAVAILABLE**.
Do not present native review as that independent audit or as a novelty acquittal.
The returned assessment and its limitations are retained in
`failure_atlas_native_claim_review_2026_11_01.md`.

## Change trail

This review adds Amendment 9, a development-pilot runner, full result tables and results entry, current-direction
links in the governing documents, and a qualification to the premature DSS positioning claim.
Earlier protocols and ledger entries are retained. Outputs stay under the ignored outputs
directory; a compact evidence summary is retained in the ledger. No commit, merge or publication
is performed by this review.
