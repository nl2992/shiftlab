# DSS positioning (Amendment 8, condition A5): R2 check of the combination

Date: 2026-11-01. Status: COMPLETE (v1). Literature audit only; no code run, nothing committed.
Builds on, and does not redo: `failure_atlas_straddle_theory_v1.md`, `failure_atlas_dependence_prior_art_v1.md`,
`switching_budget_pacing_prior_audit_v1.md`, `switching_delay_capacity_audit_v1.md`,
`switching_online_active_model_selection_audit_v1.md`.

Rule under check (DSS): undecided-only (straddle) acquisition with a minimum inter-query gap g, plus a delay switch to
uniform pacing when d >= P*T/(B+P). It feeds a started-mixture anytime-valid gate with rollback, used for reversible
model switching. Contract: delayed selective paired labels, a hard request-time budget, false-promotion control.

Evidence labels: READ = primary text opened (this or the cited earlier audit); ABSTRACT = abstract or search summary
only this session; REPO = earlier repo audit's finding, relied on. "Not found" means not found in this search.

## 1. Focused search (the combination itself)

Queries run (web search, standard and extended): (a) minimum spacing / thinning combined with uncertainty-driven
sampling in sequential testing or active model selection; (b) delay-dependent switching between adaptive and uniform
acquisition; (c) active label acquisition for monitoring or switching with a minimum spacing; (d) champion-challenger
promotion with e-processes, delayed labels and uncertainty-driven labelling; (e) streaming active learning under label
latency; (f) e-process validity under thinning / mixing; (g) cooldown or minimum gap between queried samples.
Outcome: no result combined any two of {spacing rule, delay-dependent switch, uncertainty-driven acquisition inside an
anytime-valid test}. The search tool itself reported, for (a), (b), (c) and (g), that it found no source on minimum
spacing, on a delay-triggered adaptive-to-uniform switch, or on model switching / rollback / false promotion.

## 2. Closest sources

Columns: U = undecided/uncertainty-driven acquisition; G = minimum inter-query gap or thinning; D = delay-dependent
switch to uniform pacing; V = anytime-valid e-process gate; H = hard request-time budget; R = reversible switching /
rollback. "Y" covers it, "p" partial, "-" absent.

| Source | Contract | U | G | D | V | H | R | Basis |
|---|---|---|---|---|---|---|---|---|
| Xu, Karampatziakis, Mineiro, arXiv 2406.10490, active anytime-valid RCPS | iid stream; predictable randomized labelling policy q_t >= q_min; IPW e-process; expected-rate budget | Y | - | - | Y | p (expected) | - | READ (REPO) |
| Zrnic and Candes, arXiv 2403.03208, active statistical inference | iid; model-uncertainty sampling prob.; expected budget; CLT inference | Y | - | - | p (asymptotic) | p (expected) | - | READ (REPO) |
| Li et al., Active sequential two-sample testing, arXiv 2301.12616 (TMLR 2024) | adaptive query choice, finite label cap, anytime-valid p-value regardless of query scheme | p (bimodal rule) | - | - | Y | Y (cap) | - | Thm 5.1 REPO summary; abstract re-seen this session |
| Efficient Sequential Evaluation of LLMs, arXiv 2607.17409 | CS for a new model on a question set; growth-oriented active querying; mixture of adaptive, prediction refinement and uniform exploration; finds uniform can beat adaptive | Y | - | p (uniform fallback, not triggered by delay, no delay in setting) | Y (CS from test supermartingales) | not stated | - | ABSTRACT only |
| CELEUS, arXiv 2606.20820 | e-process CIs for LLM evaluation; uncertainty-guided sampling plus surrogate; conditional unbiasedness | Y | - | - | Y | p (fewer samples, not a cap) | - | ABSTRACT only |
| Oliveira, Orenstein, Ramos, Romano, arXiv 2203.15885, Prop 10, Thm 4 | split conformal, beta-mixing; blocking with gap a, penalty (m-1) beta(a); fixed sample, coverage | - | Y (gap/blocking, not for e-processes) | - | - | - | - | READ (REPO) |
| Saha and Ramdas, arXiv 2607.28322, Prop A.1 | Markov(p,q) likelihood e-process valid on the full chain; no thinning needed | - | alternative to G | - | Y | - | - | READ partial (REPO) |
| Ryabchenko, Attias, Roy, arXiv 2503.19856, capacity-constrained delayed learning | oblivious losses, fixed delay, pathwise capacity C, batch representative sampling, regret to best fixed action | - | p (one uniform representative per batch is a spacing-like schedule) | p (batch size b >= d_max/(C-1) scales with delay) | - | Y (capacity) | - | READ (REPO) |
| Braverman et al., arXiv 2610.11074, budget pacing | hard resource budget, pacing experts, regret | - | - | - | - | Y | - | READ (REPO) |
| Turrin et al., arXiv 2610.01592, Online LLM Picker | online active model selection, IID prompts, average budget, regret | Y | - | - | - | p (average) | - | READ (REPO) |
| Pham et al., Mach. Learn. 2022 (verification latency) and Castellani et al. (arXiv 2204.06822) | stream active learning with delayed labels; simulate pending labels; drift-dependent budget | Y | - | p (latency-aware utility, not a switch to uniform) | - | Y (budget per time unit) | - | ABSTRACT only (search summaries) |
| Repo lemma `switching_pending_null_information_lemma_v1.md` and `g1_deadline_aligned_acquisition_kill_v1.md` | predictable query times with pending labels, Ville; delay-aware acquisition as belief-state approximation | p | - | p | Y | Y | p | REPO |
| PACT, arXiv 2605.22324 (security alert streams) | triggered active learning with a cooldown between labels from correlated segments; no validity or delay analysis | p | p (cooldown, heuristic) | - | - | p | - | ABSTRACT only (search summary) |

Not found, searched for: a source with U and G together inside an anytime-valid test; a source whose acquisition switches
between adaptive and uniform on a delay threshold of the form P*T/(B+P); a source with any of U, G, D in a model
promotion / rollback contract.

## 3. Coverage by DSS piece

- Undecided-only acquisition: known (Chernoff and Naghshvar-Javidi for stop-when-clear; Xu et al., Li et al., CELEUS for
  uncertainty-driven acquisition under e-process validity). REPO audits already close this as a novelty basis.
- Predictable-query validity with pending labels: known (Waudby-Smith-Ramdas Prop 1, Xu et al. Prop 2, repo lemma).
- Minimum inter-query gap: known as a device (blocking in Oliveira et al.; heuristic cooldown in PACT; one representative
  per batch in Ryabchenko et al.). Not found as a spacing rule composed with uncertainty-driven acquisition. Note it is a
  predictable function of query history, so the e-process validity under an exact conditional null is unaffected; the gap
  is a dependence mitigation only (cf. dependence audit: the Markov-likelihood gate is the principled alternative).
- Delay switch at d >= P*T/(B+P): the threshold is the repo's own cycle-4 sign-change point. Delay-aware batching exists
  (Ryabchenko et al.), latency-aware utility exists (Pham et al., ABSTRACT), and uniform fallback exists (2607.17409,
  ABSTRACT), but none triggers the fallback on delay, and none sits in this contract.
- Hard request-time budget counting pending labels, rollback, false-promotion control: known as separate ingredients
  (Li et al. cap; Braverman et al.; repo gate). No source puts them with the above.

## 4. Verdict on A5

**PASS (mildly novel combination for this contract).** I found no single source that states DSS for delayed selective
paired labels, a hard request-time budget, reversible switching and false-promotion control. No source contains even two
of the three DSS-specific pieces (straddle acquisition, a gap, a delay-triggered fallback to uniform) together with an
anytime-valid gate.

**Closest source: Xu, Karampatziakis and Mineiro, "Active, anytime-valid risk controlling prediction sets"
(arXiv 2406.10490).** It has predictable uncertainty-driven labelling feeding an e-process, but iid data, no delay,
no gap, no uniform switch, an expected-rate budget, and no model switching. The closest on the delay-to-uniform piece is
arXiv 2607.17409 (uniform exploration mixed into active querying; ABSTRACT only), and on the gap/delay-capacity piece
Ryabchenko et al. (arXiv 2503.19856).

Caveats on the PASS: it rests on absence in a web search whose index is imperfect; three of the closest items
(2607.17409, CELEUS, Pham et al.) were read at abstract level only, so a full-text check of 2607.17409 is the one
re-open condition. Under the revised bar a PASS here is a statement about composition, not a theorem or a validity claim.
Novelty also depends on A1-A4 holding; if the gap or the delay switch ablation (A4) removes the gain, the "new" part
shrinks to the contract-specific combination of known pieces.

## 5. Positioning paragraph (paper-ready)

Uncertainty-driven label acquisition inside an anytime-valid test is established (Xu et al.; Li et al.; Zrnic and
Candes), as are predictable-query validity with pending labels, blocking or thinning for dependent data (Oliveira et
al.), and hard-budget and delay-capacity scheduling (Braverman et al.; Ryabchenko et al.). We combine three of these
into one rule for a contract we did not find treated together: delayed selective paired labels, a request-time hard
budget counting pending labels, and false-promotion control for reversible model switching. DSS queries only while the
gate is undecided, enforces a minimum gap g between queries, and falls back to uniform pacing when the delay reaches
the break-even point P*T/(B+P) found empirically in our own earlier study. We claim a workable, tested composition
that beats the strongest gated baselines on the reproduced failure cells, not a new theorem: validity under
dependence is only checked empirically, the gap is a mitigation not a guarantee (a Markov-likelihood gate is the
principled alternative and is included as a baseline), and we do not claim optimality, a label-saving bound, or novelty
of any single ingredient.

## 6. Limits

- Absence findings are from web search only; the index is not exhaustive and gives no proof of non-existence.
- ABSTRACT-only: 2607.17409, 2606.20820, 2204.06822 and Pham et al., 2605.22324. Other table rows rely on earlier repo
  audits and were not re-opened here.
- No source was found about *model switching with rollback* in an active-testing contract; this may reflect search
  vocabulary (champion-challenger, canary, shadow deployment) rather than true absence.

## Re-open check (2026-11-01, reviewer)

The verdict depended on a full-text read of arXiv 2607.17409 ("Efficient Sequential Evaluation of
Large Language Models"). The HTML version was read: sections 1–5.1 and appendices C.1–C.4
verbatim, the remainder from a summary.

**Contract.**
- Bernoulli questions, observed immediately.
- No label delay.
- No model-switching decision.
- An anytime-valid confidence sequence from test supermartingales (section 3; Propositions 4.1
  and 4.2).

**How it relates to the DSS pieces.**
- *Uniform mixing.* The practical rule (Eq. 37, read in the summary only) mixes uniform
  exploration on a t/N schedule. That schedule is not triggered by delay.
- *Gaps.* The only floor is a sampling-probability floor, `q_t(i) >= h`; it is not a time gap.
- *Combination.* No algorithm combines undecided-only querying, a minimum gap, and a
  delay-triggered fallback to uniform acquisition.

**Outcome.** The re-open condition is cleared, and the A5 verdict stays **PASS**.
