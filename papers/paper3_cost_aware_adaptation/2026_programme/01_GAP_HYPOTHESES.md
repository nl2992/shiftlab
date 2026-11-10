# 01 Gap hypotheses (falsifiable) and H/F/S/C/B scoring

All entries are HYPOTHESES. No result is claimed. Procedure followed manually (fatal-flaws-first) from `~/.claude/skills/idea-evaluator/SKILL.md` and `references/fatal-flaws.md`: ground F1 in retrieval, then apply the data-refuted rule (a core mechanism already matched or beaten by a baseline in the user's own data is CRITICAL: Reject and Pivot, no defense written, no scores). `~/.claude/skills/deep-research/SKILL.md` was not applied beyond its principle (frozen questions; adversarial multi-perspective; per-citation verification); no survey-grade synthesis was attempted. Scores use the skill's discipline (start at 5; move only on reported data or a mechanism argument, labelled "mechanism-based, not confirmed"). H = Higher (effectiveness), F = Faster (efficiency), S = Stronger (robustness), C = Cheaper (labels/annotation), B = Broader (transfer/unification).

## Step 1: fatal-flaw gate

| Cand | F1 (no novelty vs closest) | Data-refuted core mechanism? | Gate result |
|---|---|---|---|
| A | High: Chick 2017, Cheng 2023, Atan 2016, Drift2Act 2026, G1 kill | **YES for the performance claim**: calendar exactly optimal at tight risk (alpha .05, B<=4); joint planner gap 0.7-1.2% at alpha .10; 12 mechanisms tie tuned Wald (MANDATE settled findings, repo evidence, not re-run) | **CRITICAL: Reject and Pivot as an advantage-claiming paper. No scores assigned.** Residue (tractable A2 with proved gap) goes to baseline/ablation status. |
| B | Medium: envelope already internal; variation-budget literature unretrieved | No: only the *unrestricted-reversal* version is refuted (a restriction, not a falsification of the bounded-drift claim) | pass; score |
| C | Medium: Ahmed 2026, Cerqueira 2026 | Not refuted; but atlas numbers have a known fidelity defect (a validity defect, not a refutation of the mechanism) | pass with warning; score |
| D | Medium-high: Lopes, Cerqueira LODO, Sow, Chen | Not directly tested; adjacent evidence (tuned Wald ties) lowers expected headroom | pass with warning; score |
| E | Unknown: single bounded search; adjacent sources unread | Untested | pass; score |

## Step 2: candidate hypotheses

**HA-1 (A2, kept only as residual).** There exists a tractable two-law controller with value within epsilon of the exact constrained oracle on a family where every fixed calendar + threshold is >= 3% worse. *Falsifier:* exact oracle (small instance) shows calendar within 1.2% on every family cell searched, as already seen at alpha .05/.10. Prior evidence leans toward falsification.

**HB-1 (B1).** For Z_t with total variation <= Delta over the horizon, a time-uniform lower confidence bound on payback over horizon h is non-vacuous (certifies net-positive switches) for at least a nontrivial region of (B, d, h, Delta, k). *Falsifier:* region empty at all realistic Delta (certificate never fires before the bound's slack exceeds the payback).

**HB-2 (B4).** A lower bound of order matching the upper bound (up to logs) exists in at least 3 of the 5 parameters. *Falsifier:* upper bound strictly dominated by a simple window CS + Delta*age bound that already meets the lower bound (then B reduces to the internal envelope).

**HB-3 (B2).** The naive batch certificate (decide after a fixed batch) is invalid under optional continuation; the adaptive-batch version is valid. *Falsifier:* naive rule's type-I error <= alpha in an adversarial-stopping simulation.

**HC-1.** After fidelity repair, one isolated dependence factor flips the economic ranking of >=2 monitors without changing alarm AUROC/delay rankings (CI excludes 0), and an attributable repair removes the flip. *Falsifier:* no inversion survives with n >= registered seeds.

**HD-1.** A controller whose parameters are chosen by a frozen map from stream meta-features, trained on other families, achieves net cost within 1-3% of per-domain tuned (at zero held-out tuning labels) and >= 3% below a pooled default. *Falsifier:* within noise of the pooled default (no transfer value) or worse than per-domain tuning by > 3%.

**HE-1.** There is a stream/label regime where prequential certification of the running candidate yields promotion of a harmful frozen candidate with probability > alpha under the stated conditional null, and a split/cross-fit scheme fixes it. *Falsifier:* promoting the last running model while continuing its e-process is valid and equals the best allocation within 1% (then E reduces to Challenger + prequential monitoring).

**HE-2.** The optimal label-split schedule beats fixed 50/50 and always-train by >= 3% net cost (CI excl. 0) across >= 3 shift types. *Falsifier:* flat optimum (curve within 1% across splits).

## Step 3: H/F/S/C/B scores (hypotheses, mechanism-based, not confirmed by data; start 5)

| Cand | H | F | S | C | B | Basis and two highest-ceiling dimensions |
|---|---|---|---|---|---|---|
| A | not scored | not scored | not scored | not scored | not scored | short-circuit: data-refuted core mechanism (see gate) |
| B | 5 | 5 | 7 | 6 | 5 | S: a certificate with stated persistence + a lower bound is a robustness statement (mechanism-based). C: bounds quantify label need, but gain over a plain CS is unknown. H stays 5: no data that payback certification improves net cost over a hurdle rule; internal screens say the age-corrected envelope is not novel alone. Ceiling: S, C. |
| C | 5 | 4 | 6 | 5 | 6 | S/B: a validated protocol that reveals when monitors fail is broadly reusable; F is lowered because the atlas needs a rebuilt pipeline (known fidelity fix). H stays 5 (no new algorithm). Ceiling: S, B. |
| D | 5 | 6 | 5 | 6 | 7 | B: transfer is the stated purpose. C/F: zero tuning labels at deployment is a real cost saving *if* transfer works; adjacent evidence (tuned Wald ties) holds H and S at 5. Ceiling: B, C. |
| E | 5 | 5 | 6 | 7 | 5 | C: it directly targets label scarcity by removing the train/certify duplication (mechanism-based). S: validity for the promoted object is a robustness property. No data yet; unverified novelty prevents raising any score above 7. Ceiling: C, S. |

Reviewer comment: these scores order *ceilings*, not probabilities of success. No candidate here exceeds 7, consistent with the repo's pattern of negative results; they do not support a claim of the 2.5% stretch target.

## Step 4: fatal-flaw defences (non-critical only)

- B: defence = lead with the lower bound and the optional-continuation counterexample; treat the envelope as a corollary.
- C: defence = rebuild atlas on corrected DISCERN variance/psi_E and dependence-safety caveats before any reuse of headline numbers.
- D: defence = LOFO with parameters frozen pre-access; per-domain tuning at equal label cost as mandatory comparator.
- E: defence = find or construct the running-vs-final counterexample first (cheap, CPU, one afternoon); if absent, stop.

## Pre-registration hooks (to be locked by the coordinator before any confirmatory run)

Primary metrics: net cost J, false-promotion rate under the global null, label spend; comparators labelled NATIVE_SOURCE_FIDELITY / DOCUMENTED_ADAPTER / IN_HOUSE_HEURISTIC per MANDATE. Real streams in `data/c4_sealed` and `data/saes_dev` are dev-exposed (exploratory only).
