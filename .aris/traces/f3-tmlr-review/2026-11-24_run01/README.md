# Adversarial review of the F3 TMLR draft (2026-11-24, run 01)

Reviewed: `paper/f3_tmlr/main.tex` at commit e418865f (`reviewed_main.pdf`, 39 pages).
Route: Claude Code reviewers (ARIS research-review / paper-claim-audit / novelty-check protocols).
review_independence: same-family; acceptance_status: provisional. Reviewers did not read
`PAPER_IMPROVEMENT_LOG.md` or earlier traces, and were read-only on the repository.

| file | reviewer | verdict |
|---|---|---|
| R1_senior_reviewer.md | senior TMLR reviewer (Opus) | Major revision, confidence 4/5 |
| R2 (missing) | theory and proof audit (Opus) | did not finish: API usage limit; to be re-run |
| R3_claim_audit.md | claim audit vs result files (Sonnet) | ~104/115 verified; 4 mismatches, 4 overstatements |
| R4_novelty.md | novelty check (Sonnet) | no prior work contains the headline result; ~5-6/10 |

Top issues (checked against the repository by the lead session):
1. The registered 100-stream screen (`05G_F3_REAL_SCREEN100_PROTOCOL.md`, results in
   `outputs/paper3/riskbudget/screen100/tally.json`) was removed from the paper in commit 5b9a91ad.
   Shield: 0 violations on 100 streams; Wald+cutoff exceeds the budget on 94; shield costs more than
   never switching on 43 and less than Wald+cutoff on 30.
2. Two of the 14 pre-registered real streams (openml_ldpa, uci_occupancy) were removed after the run;
   disclosed in one appendix sentence only. Both were costly streams for the shield.
3. The "64-99% worst regime" headline rests on a fee-above-budget regime and the authors' stress
   regime; pooled original-regime exceedance is 1-6%.
4. Regime-map: only "L increases with x" was committed before the test; the threshold wording is post hoc;
   headroom alone correlates 0.45-0.68; 88-96% retention holds for paced arms only.
5. Claim-audit wording fixes (0.96 -> 0.95; "within 10.0 units" -> "10.0 units better"; compute
   appendix stream counts; "five tuned comparators" -> three tuned; calibrated CUSUM best grid value).
6. Missing citations: Xu-Karampatziakis-Mineiro 2024; Deb et al.; delayed/censored bandits;
   Sinha-Vaze 2024; Zhao et al. 2019 staged rollout.
