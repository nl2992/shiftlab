# Algorithm portfolio: master plan (directive of 2026-11-08)

Three independent algorithm tracks plus the EQSDp fallback. Each track has its own ledger,
comparators, protocol and verdict. One track's success never validates another.

| Track | Question | Where | Status |
|---|---|---|---|
| A: BCR | Joint challenger ranking + economically relevant acquisition for K≥3 models | branch `research/multimodel-bcr-2026-11-08` | **feasibility FAIL** ([04](04_BCR_PLAN_AND_RESULTS.md)) |
| B: Gap-Mix+ | Evidence-adaptive querying for dependence-aware Gap-Mix evidence (declared ρ̄=.8) | branch `research/methods-recovery-2026-11-07` | preregistered C3 development eval; alt stage resumed after Amendment A1 ([05](05_GAPMIX_PLAN_AND_RESULTS.md)) |
| C: PAVE+ | Can a simple delay-aware rule capture PAVE's long-delay gain? | same branch | bounded feasibility running ([06](06_PAVE_PLAN_AND_RESULTS.md)) |
| Fallback: EQSDp | Confidence-bound reversible payback switching vs point-estimate adapters | main checkout | C3 historical PASS; **C4 target reached under A2 (9/16)** ([10](10_C4_REAL_DATA.md)) |

Order of work:
1. Recover state ([01](01_RECOVERED_STATE.md)).
2. Run the bounded feasibility or development stage for each track.
3. Rank by actual headroom ([07](07_METHOD_RANKING.md)).
4. Only a track that passes its gate moves to novelty audit, C3 freeze and its own C4.
5. If none passes, the new-algorithm programme is INCOMPLETE and the publication decision
   covers the EQSDp/Failure Atlas asset ([12](12_FINAL_PUBLICATION_DECISION.md)).

Scope rule: about 20–60 paired development seeds per screen; no broad hyperparameter sweeps; no
fourth broad search launched automatically.
