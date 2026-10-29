# Online FWER as the repeated-promotion comparator

**Date:** 2026-10-29. **Status:** primary-source scope audit; no new algorithm claim.

## Source and results inspected

Tian and Ramdas, “Online control of the familywise error rate,” *Statistical Methods in Medical
Research* 30(4), 2021, DOI 10.1177/0962280220983381. I inspected the publisher's full article,
including its online alpha-spending and fallback rules, ADDIS-Spending, and the stated FWER results.

For an unbounded stream of hypotheses, alpha spending tests hypothesis `i` at `alpha * gamma_i`,
where the nonnegative weights sum to one, and controls FWER by Bonferroni under arbitrary dependence.
Online Fallback recycles a rejected hypothesis's allocated level forward and also controls FWER
under arbitrary dependence (Proposition 2). ADDIS-Spending uses adaptive discarding and the
proportion of non-nulls to improve power; Theorem 1 gives its PFER, hence FWER, control under
independent uniformly conservative null p-values. Their Theorem 2 extends the guarantee to the
paper's local-in-time dependence model. This is a materially stronger baseline than comparing a
candidate only with static Bonferroni spending.

## Consequence for ShiftLab

For the repeated any-false-promotion event, compare against at least (i) online alpha spending and
online fallback when only arbitrary-dependence validity is defensible, and (ii) ADDIS-Spending when
independence or the precise local-dependence assumptions hold. These procedures allocate error over
the stream of promotion hypotheses and target the same familywise event more directly than FDR.
Generic alpha recycling and adaptive spending therefore do not qualify as the algorithmic delta.

This source does not supply ShiftLab's observable delayed-label alpha recycling, pathwise query
budget including pending requests, causal-null validity under adaptive paired sampling, economic
switching objective, or reversible rollback. In particular, do not combine its validity statement
with GAIF's delayed feedback claim without proving that the resulting alpha levels and null p-values
satisfy one source's assumptions. The full comparison remains a resource-matched composition, not
an assertion that the separate sources compose automatically.

The novelty test is now sharper: a proposed rule must beat an online FWER controller under the same
delayed feedback and query cap, while optimizing the same switching/rollback utility. If applying
valid alpha spending or online fallback to sequentially valid per-promotion p-values and then using
the best switching controller matches the exact two-law oracle on the proposed family, stop that
candidate. Promotion validity remains separate from current challenger value following a regime
reversal; that requires new evidence or a stated persistence model.

## Decision

Online FWER control and (under stronger p-value assumptions) powerful adaptive discarding are
established. Use them as mandatory baselines. The source does not close the delayed, hard-budget,
reversible economic problem, but those mismatches alone do not demonstrate a research gap. G1
remains open; G2–G5 stay held.

## Provenance

- Publisher full article: [Sage full text](https://journals.sagepub.com/eprint/AYRRKZX7XMTVHKCFYBJY/full).
- DOI record: [10.1177/0962280220983381](https://doi.org/10.1177/0962280220983381).
- Selected source-scope audit, not an independent reproof.
