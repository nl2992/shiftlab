# Monitoring-to-decision value programme

When does a better statistical monitor improve deployment decisions? **Outcome: Decision D**
(workshop or preliminary). See [the final decision](09_FINAL_RESEARCH_DECISION.md) and the
[claim–evidence matrix](CLAIM_EVIDENCE_MATRIX.md).

| File | Content |
|---|---|
| `00_MASTER_PROTOCOL.md` | scope, isolation, formal setting, hypotheses |
| `01_EVIDENCE_AUDIT.md`, `claim_registry.json` | audit of historical findings F1–F6 |
| `02_PRIOR_ART_AND_NOVELTY.md` | literature and novelty matrix |
| `03_REAL_DATA_AUDIT.md`, `manifests/datasets.json` | dataset eligibility and reserved windows |
| `04_THEORY.md` | propositions P0–P6 with proofs |
| `05_EXPERIMENTAL_CONTRACT.md` | engine interfaces, clocks, tests |
| `06_STATISTICAL_ANALYSIS.md` | development mechanism checks TH-1..TH-4 |
| `07_ADVERSARIAL_REVIEW.md` | red-team self-review and falsification probes |
| `08_PUBLICATION_PLAN.md` | publication recommendation |
| `10_REAL_DATA_DEV_RESULTS.md` | OPSD, Monash and Binance development replay |
| `11_TYPE2_TUNED_CONTROLLERS.md` | equal-budget tuning, symmetric and asymmetric regimes |
| `12_CONFIRMATION_PROTOCOL.md`, `13_CONFIRMATION_RESULTS.md` | frozen confirmation and its results |
| `RESEARCH_LEDGER.md`, `LIMITATIONS.md` | append-only log and limitations |

Verification:

```bash
PYTHONPATH=src python -m pytest tests/decision_value -q
```
