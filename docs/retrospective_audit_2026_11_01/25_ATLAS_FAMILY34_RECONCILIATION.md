# Amendment-6 family3/4 reconciliation

`python -B scripts/retrospective_audit/audit_atlas_family34.py`: exit 0. Archived nullbase counts agree with all state count fields for 12 null twins per family. State-only rho/delay/base-delay annotations are additional metadata; the initial audit reader incorrectly compared whole records, then was corrected to compare the archived fields and twin IDs. This was an audit-tool schema issue, not an experiment mismatch.

Reproduced point criteria: D1 PASS, c1_hmm_cs 69/400=.1725 at rho=.8; D2 FAIL, monotone in rho for 5/7 gated methods; I1 FAIL, I2 PASS. Original reports label these exploratory, not new confirmation. D1's reported Wilson lower bound .139 is below the .15 advancement threshold; the registered point-estimate pass is not a confidence statement exceeding that threshold. The dependence family can violate the eventwise conditional null while preserving a stationary/marginal mean; this is misspecification evidence, not a contradiction of a theorem under the stronger conditional null. Counts were not regenerated from raw per-seed label paths. Pooling/independence and source hash/code parity remain open.

See ATLAS_FAMILY34_COUNTS.json for method rates and source hashes. No historic result or registered verdict changed. W09/G09 remain incomplete.
