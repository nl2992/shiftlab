# R1: senior reviewer / action-editor report, F3 TMLR submission

- Paper: "A Pathwise Harm Budget for Reversible Model Promotion under Delayed, Missing and Scarce Feedback"
- Source reviewed: `paper/f3_tmlr/main.tex` + `tables/` + `figures/` at commit e418865f (compiled `main.pdf`, 39 pp.)
- Reviewer route: Claude Code reviewer (ARIS research-review protocol)
- review_independence: same-family
- acceptance_status: provisional
- Files checked against claims: `results/riskbudget/{exposure_ratio_test.json, screen100_not_supported.md, superseded_14stream/*}`, `04F_F3_CONFIRMATION_REGISTRATION.md`, `05F_F3_REAL_STREAM_PROTOCOL.md`, `05G_F3_REAL_SCREEN100_PROTOCOL.md`, `src/shiftlab/paper3/riskbudget/{shield.py, bounds.py, comparators.py, metrics.py}`, `scripts/paper3/riskbudget/exposure_ratio_test.py`, `outputs/paper3/riskbudget/screen100/tally.json`, git history of `paper/f3_tmlr/main.tex`. I did not read `PAPER_IMPROVEMENT_LOG.md` or other traces.

## Summary

The paper studies when to replace an incumbent model by a challenger under delayed, purchased or missing labels. It defines intervention harm H_t as excess 0/1-type loss of the deployed model against never switching plus switching fees k. It proposes a "shield" that wraps any promotion rule and deploys the challenger only if a pessimistic accounting check W_t (fees paid + a reserved rollback fee + resolved harm + pending labels booked at worst case + the current round + an anytime martingale width for sampled labels) is at most R. Theorem 1 gives P(sup_t H_t > R) <= delta (deterministic with full sampling) for every fixed loss/flag sequence and every admissible (possibly outcome-dependent, infinite) delay rule. Proposition 1 shows payback certification is impossible without restricting the future; Proposition 2 gives a lower bound showing a valid controller cannot hold a first promotion through more than R-2k disagreement rounds in a feedback-blind window, which the full-sampling shield attains; Proposition 3 is a ruin bound for forced rollback of a beneficial challenger. Experiments: a registered 30-regime simulation (1,000 seeds/regime), a calibrated-comparator study, 12 cached real streams with simulated delay/corruption, and a correlational "regime map" relating the share of gain lost to x = rd/h.

## Claims as I understand them

1. (Theory) Pathwise (R, delta) harm budget for any inner rule under O1-O4 and Assumption L.
2. (Theory) Matching lower bound on first-promotion exposure; the pending and rollback reserves are necessary.
3. (Empirical, safety) Shield arms had 0 violations (full sampling) / far below delta (paced), while five comparators exceed R=20 in 64-99% of runs in their worst regime.
4. (Empirical, utility) Pooled, the shield is cheaper than never switching; in stress regimes cheaper than tuned Wald; on real streams it keeps roughly half of Wald's gain at h=14.
5. (Empirical, regime map) A pre-stated prediction: share of gain given up L increases with x=rd/h, small for x<.5, near 1 for x>1; paced variants keep a median 88-96% of the gain at x<.5.

## What I verified and found correct

- Theorem 1 proof (Steps 1-3) is correct as written. The decomposition chi_s = chi_s q_s/pi_s + xi_s, worst-case booking of pending rounds, monotonicity of D_delta, and the rollback argument (H_t' <= R-k at the last deployed round, then one fee) all check out. Ride-out is handled correctly.
- Lemma 1 (Bennett + finite mixture + Ville) is standard and correctly applied; the one-sided bound xi <= max(1, 1/pi_min - 1) is right. Lemma 2 (exact-coin convexity bound) is correct; the two pathwise caps in the paced controller (min with count of sampled rounds; min with sum of max{1, 1/pi-1}) are valid upper bounds.
- Proposition 1 is correct (indistinguishability). Proposition 2 is correct; the coupling to the all-harm tape E' is valid because actions through j+d-1 depend only on labels requested before j. Because the argument works for any E, the full-sampling shield's hold of exactly floor(R-2k) before any label returns is genuinely matching (Table 13 confirms in 12/12 cells).
- Proposition 3: Hoeffding with theta = 2 mu gives exactly 1; the +-1 gambler's-ruin martingale is right; the d=1 cells in Table 14 are essentially exact (0.2035 vs 0.1975, z = 0.7), as expected.
- Code: `shield.py` implements W_t as written (fees incl. promotion, rollback reserve, n_b + A + P, g/pi current round, D(V + g(1/pi-1))); `metrics.harm_path` computes H_t from the full tape. The naive stop-loss blocks promotion when k > R, so its worst regime is not the high-fee one, consistent with the table.
- Every number I spot-checked in `tables/numbers.tex` matches the result JSONs (registered C1-C6, Table 2, the regime-map bins and Spearman CIs, Table 4).
- The paper is unusually candid in places: it states that exceedance by comparators that are not told R "measures the absence of a guarantee, not a design flaw"; that real-stream runs share tapes; that the regime-map test ran on existing outputs; and that v3 is a second look.

## Strengths

- A clean, practically meaningful target (realised harm against the status quo, fees included, at every round) and a simple, auditable mechanism. The decomposition into a pending reserve and a rollback reserve is intuitive and is shown to be necessary (Prop. 2) and to matter empirically (ablations: 0.94 / 0.86 / 0.34 worst-regime violation without each component).
- The validity statement is strong and correctly scoped: oblivious loss sequences with arbitrary dependence/drift, outcome-dependent and infinite delays, design-based randomness only.
- Good experimental hygiene overall: frozen arms, disjoint seed blocks, paired tapes across arms, Wilson intervals, seed-cluster bootstrap, complete regeneration of numbers from result files.
- The comparison design isolates the constraint: every shield arm wraps the same tuned Wald rule that is also a comparator, so cost differences are the price of the shield.
- Likely of interest to the TMLR audience working on ML deployment, safe online decision-making and label-efficient monitoring.

## Weaknesses

### W1 (major). Pre-specified real-data evidence was removed from the paper: a registered 100-stream screen and the registered harmful-stream breakdown
- Evidence: `05G_F3_REAL_SCREEN100_PROTOCOL.md` (locked 2026-11-17) specifies a screen of 100 fresh public streams, "Every built stream is tallied; none is dropped after results", with "The tally is reported over every stream in the pool". The run exists (`outputs/paper3/riskbudget/screen100/tally.json`) and generated tables exist (`tables/screen_groups.tex`, `screen_numbers.tex`, `app_screen_supported.tex`), but `main.tex` never mentions it. Commit 5b9a91ad is titled "remove the 100-stream screen, harmful-stream table and paced-violation spotlights"; cd6f64e4 "drop harmful-stream sentence". `05F_F3_REAL_STREAM_PROTOCOL.md` also pre-specified pooling "separately over the 2 harmful and the 12 beneficial streams" ("Reported (all of it, whatever the outcome)"); `tables/app_real_clean_harm.tex` exists but is not in the paper.
- What the removed evidence says (my reading of `tally.json`): full-sampling shield 0 violations on all 100 streams; Wald exceeded R=24 on 94/100; the better h=50 shield arm cost more than never switching on 43/100 streams (32/32 FOREX streams are not useful challengers; 30 FOREX fail S2), and cost less than Wald on only 30/100. On the two harmful streams of the 12-stream study the shield costs +9.6 to +14.9 units more than never switching and +0.9 to +6.2 more than Wald (it caps the tail: max harm 24 vs 120 for Wald).
- Why it matters: the 12 streams were all previously used by the authors (protocol label EXPOSED_STREAMS_FROZEN_CONFIG); the screen is the only unexposed, larger-scale real evidence and it was pre-registered. Removing it, and the harmful-stream split, is a departure from the authors' own reporting plan and makes the real-data claims look selected, even though the removed material largely *supports* the safety claim. It also hides the most decision-relevant utility fact: for harmful or neutral challengers the shield protects the tail of H but not mean cost, because label purchases are outside the budget.
- Fix: restore the screen (main text: one paragraph + group table; appendix: all 100 streams) as the primary real-data evidence, report the harmful/beneficial split as registered, and state the 2-stream post-hoc exclusion with both 12- and 14-stream numbers (they barely differ: h=14 gain 82 vs 75; Spearman upper 0.80 vs 0.83). Effort: writing only, about 1 day; all outputs exist.

### W2 (major). Headline exceedance numbers are partly trivial and are foregrounded in the abstract, introduction and Figure 1(b)
- Text: abstract "five tuned comparators without a guarantee exceeded the budget in 64--99% of runs in their worst regime"; Fig. 1(b).
- The 99% (CUSUM, 0.987) comes from the high-switch-fee regime with k=30 > R=20, where *any* single switch violates the budget; this is a statement about an infeasible budget, not about delayed feedback. Three of the five comparators (Wald, CUSUM, gate) are never told R, so exceedance is expected by construction (the paper concedes this in Sec. 5 but not in the abstract). The other worst cases are all in "adverse dropout", a stress regime designed by the authors so that resolved-label checks fail. On the 24 original regimes the pooled rates are 1-6% (stop-loss 1.1%), which is the comparison a practitioner would weigh against the shield's +2.50 (3.7%) cost there.
- Also "five tuned comparators": the stop-loss and CUSUM rollback have no tuned parameters (they reuse tuned Wald).
- Fix: in the abstract and Fig. 1(b), lead with the budget-aware comparators (stop-loss, CUSUM rollback) and the pooled original/stress split; either exclude regimes with k >= R from worst-regime statistics or label them as infeasible; say "comparators not designed for the budget". Effort: rewording + regenerated figure, under 1 day.

### W3 (major). The regime-map "prediction" is weaker than presented and was not fixed before the data were seen
- Text: Sec. 4 "We predict that the share L ... is small for x<.5, and is near one for x>1 ... The prediction and test were fixed before the test run"; Fig. 4 caption "L ... is small when x<0.5 and close to 1 when x>=1"; abstract "paced variants retained a median 88--96%".
- Evidence: `exposure_ratio_test.py` was committed at 22:15 and its result at 22:16 on 2026-11-16, after the v3 runs that had already been inspected ("narrows real-stream cost gap only at large headroom", 21:07). The only registered criterion is Spearman(x, L) > 0 with CI above 0; the bins are "Descriptive". "Small below .5 / near one above 1" was not a registered pass/fail criterion.
- Spearman > 0 is close to guaranteed: units vary in headroom h within each regime, and L must fall as the budget loosens. From the JSON I computed Spearman(1/h, L) = 0.45-0.68 versus Spearman(x, L) = 0.69-0.80. x does add information (within fixed h, Spearman(rd, L) is mostly 0.3-0.7), so the association is real, but the registered test cannot distinguish "x is the right scaling" from "bigger budgets cost less".
- The "small for x<.5" claim fails for the full-sampling arm (median L = 0.40 in simulation, 0.32 on real streams) and the 88-96% range is computed from paced and v3 arms only; v3 was selected on the same 47-regime scarce family (different seeds). The real-stream analysis has 8 clusters; a cluster bootstrap with 8 clusters gives unreliable CIs.
- Fix: describe the analysis as exploratory/post hoc; report the comparison against h-only and rd-only predictors (or partial Spearman of L on x given h); state the full-arm numbers next to the paced ones in the abstract; drop "prediction" language or present the registered test (Spearman > 0) exactly. Effort: rewording + a few lines of analysis on existing JSON, about half a day.

### W4 (moderate). The utility story is weaker than the abstract/conclusion suggest, and dominated by a few streams
- Simulation: the full-sampling shield gives up about 31% of Wald's gain pooled (gain 2.10 vs 3.06) and is worse than Wald on the 24 original regimes by +2.50 (3.7%). It wins only in the six stress regimes it was designed around (C5).
- Real streams (Table 4): at h=14 (R=24) the shield gains 82 of Wald's 180 units (46%); at h=6 it is within 10 units of never switching. Pooled equal-weight means are dominated by spam (1 episode, Wald gain 636) and metro (604): together about 58% of the pooled Wald gain (my calculation from `app_stream.tex`). No pooled CI is shown in Table 4. On appliances (beneficial, d=144) the shield at h=50 is worse than never switching (836.7/848.3 vs 821.8).
- The budget excludes label costs, so the shield can cost more than never switching even though H <= R (harmful streams; 43/100 screen streams). The paper never states the implied bound J <= J_never + R + c_q * B, which a reader needs.
- Registered C4 tolerance (upper bound < 3% of J_wald) was chosen after dev runs showed the shield "0.3-2.8% worse pooled" (`04F`), so C4 was set to pass. C3 was likewise "known in advance" from dev. The registration is a replication on fresh seeds, which is valuable, but the paper should say these thresholds were set from dev results.
- Fix: add pooled CIs and a leave-one-stream-out or median-over-streams version of Table 4; state the J bound; note how the C3/C4 thresholds were set. Effort: about 1 day, existing outputs.

### W5 (moderate). Comparator set lacks any method with a guarantee and only one inner rule is tested
- The calibrated study (Sec. 5.2, Table 3) shows that one-parameter resolved-harm rules cannot reach the per-regime .05 target except by never promoting (selected stop-loss margins c = h+1 exactly block every promotion). This is a useful negative result, but it compares the shield with rules that lack its key ingredient by construction; the obvious engineering fix ("stop-loss + count in-flight labels at worst case") *is* the shield minus the rollback reserve, i.e. the ablation.
- Missing: (a) a delay-aware conservative-bandit-style baseline (e.g. Wu et al. 2016's check with a pending reserve), or the Prudent-Banker restart rule adapted to this setting, so the reader can see what is gained over the closest guaranteed method; (b) a fixed-duration canary / staged rollout baseline, which is what deployment teams use; (c) the shield wrapped around a second inner rule (CUSUM or the gate) to support "for any promotion rule" empirically.
- "Among controllers that keep the budget" framing: reasonable as stated in Sec. 5.2 provided the paper says that only shield variants and never-switching keep it, and that the calibration criterion included adverse-dropout regimes built to defeat resolved-harm checks.
- Fix: add (c) (cheap, a re-run of existing harness, under 1 CPU-hour) and one of (a)/(b) (1-3 days). Discuss traffic-splitting canaries, which change the action space.

### W6 (moderate). Realism and placement of assumptions
- Assumption L (shadow predictions logged on every round, common outcome, paired losses identifiable from one label) and O1 (exogenous outcomes) carry the whole guarantee. They exclude selective-labels settings in which the deployed model's decision determines whether an outcome exists (lending, fraud review, recommendation), which are the settings where delayed and missing feedback are most acute. O3 allows outcome-dependent delay, which is good, but the paper should say plainly in the introduction which common deployment settings are in or out of scope. The limitations section mentions O1 briefly but not selective labels.
- The fee k "in units of loss" and the single scalar R mix operational and predictive cost; guidance in "Choosing R and delta" is helpful but the experiments never vary k except in the infeasible k=30 regime.
- sup_t H_t counts transient excess even for good challengers (Wald exceeds R=24 in 289 runs on beneficial real streams). Whether sup harm or final harm is the right risk is a modelling choice that deserves one sentence of justification.
- Fix: one paragraph in Sec. 3 and the limitations. Effort: rewording.

### W7 (minor). Real-stream statistics
- Violation and exceedance counts are over runs (3,880 = 194 episodes x 20 policy seeds that share a tape). The paper says this, but Table 4 and Fig. 3(b) still report run counts. Report episodes-with-any-exceedance per stream.
- Zero shield violations with full sampling is implied by the theorem (the paper calls this a consistency check in Sec. 5.3 but lists it as evidence in the abstract and conclusion).
- Three looks at the same 12 streams (frozen arms, calibrated comparators, v3). Fine as labelled, but this strengthens W1: the screen is the clean evidence.

### W8 (minor). Clarity and self-containment
- The main text is dense with macro-generated numbers, internal names (v2/v3, "documented adapter", "atlas/sprint streams", "fidelity registry") and forward references; the contributions table and the running-example table sit at the end of the appendix. "Wald with cutoff" is "a documented adapter of an earlier study of ours", which a reader cannot check; give its full definition in the main text (it is the inner rule of every result).
- "Registered" means a dated file in the authors' repository, not a public registry; say so.
- Fig. 4(b) has an x-axis from 1e-3 with no data below 1e-1; the two panels use different ranges.
- Proposition 1 is close to definitional; present it as a motivating observation rather than a contribution bullet.
- Fix: rewording/reorganisation, 1-2 days.

## Questions for the authors

1. Why were the 100-stream screen and the harmful/beneficial split, both specified in your own protocols, removed? Will you restore them?
2. Which two streams were excluded post hoc, and when was the decision made relative to seeing their results?
3. Does x = rd/h predict L better than h alone or rd alone? Please report partial correlations or a model comparison.
4. With delta = .05 the paced arms show 2 violations in 60,000 runs. How much utility is lost to the conservativeness of the width, and would a smaller grid or a betting-style CS change Table 4?
5. How does the shield compare with a delay-aware conservative-bandit check or a fixed-length canary?
6. Can the guarantee extend to selective labels where the outcome is observed only under one action (O1/L violated)? If not, say so in the introduction.
7. What does Table 4 look like with stream-level medians or leave-one-out of spam and metro?
8. How were the C3 and C4 thresholds chosen relative to dev results?

## Recommendation

**Major revision.** Confidence: 4/5.

The theory is correct and the safety claim is well supported (including by evidence the paper omits). Under TMLR's criteria, the problem is criterion (1): several abstract/introduction claims are framed more strongly than the evidence (W2, W3, W4), and the real-data evidence presented is a selected subset of what the authors pre-specified and ran (W1). None of this needs new theory, and most fixes are reporting changes on existing outputs.

### What would move this to accept
1. Restore the registered 100-stream screen and the harmful/beneficial split, and disclose the 2-stream exclusion (W1).
2. Reword the abstract, introduction, Fig. 1(b) and conclusion: drop or label the k > R worst case; separate comparators that are told R from those that are not; report original-regime pooled rates alongside worst-regime ones (W2).
3. Present the regime map as exploratory, add the h-only comparison, and report full-sampling medians next to paced ones (W3).
4. Add pooled CIs / stream-robust summaries for real streams and state J <= J_never + R + c_q B (W4).
5. Add the shield over a second inner rule, and one guaranteed or practice-standard baseline (W5).
6. Explicitly scope Assumption L / O1 against selective-labels deployments in the introduction (W6).
