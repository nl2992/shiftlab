# Pre-opening analysis amendment — primary family and outlet uncertainty

**Written:** 2026-11-06, before Q4 predictions, losses, or policy outcomes were computed.  
**Amends:** `protocol.md` and `PROTOCOL_AMENDMENT_PREOPENING.md`.

## Primary comparator family

The five primary candidate contrasts are against `PFA-SR:gated_adaptive_range`,
`rmm:gated_adaptive_range+RMM`, `E_rb:gated_adaptive_range`, `E_swcert`, and
`validation_selected_source_static`. The candidate must save at least 5 net-cost units per 1,000
events against **each** of these five, with a familywise 95% paired interval below zero. Use
Bonferroni simultaneous intervals for this fixed family: the two-sided per-contrast interval is
99% (`0.05/5` total error, `0.005` in each tail) from the registered 7-day moving-block bootstrap.
This avoids choosing a “best” global monitor after viewing Q4. The other ten registered baseline
comparisons are secondary and use unadjusted 95% moving-block intervals; they remain fully
reported.

The candidate must also have no point-estimated cost penalty above 5 units per 1,000 events in any
of the three named source contexts and must have lower net cost than the validation-selected static
rule in at least two of those three contexts. These are descriptive scope checks, not a second
familywise test. Failure of any primary comparator gate means this source does not advance to a
positive repair-transfer claim.

## Event-weighted and publisher-cluster uncertainty

Keep the event-weighted per-1,000 net-cost difference as the primary estimand. In addition, report
publisher-level cost differences and a publisher-cluster bootstrap interval: resample the distinct
Q4 `source` values with replacement (same number of sources as observed), sum each selected
publisher's paired event costs and counts, and form the resampled event-weighted ratio. Use 2,000
replicates and seed `2026110643`. This interval quantifies variation across publishers within this
single corpus; it does not quantify transfer across datasets. Report the three named contexts
separately with their 7-day time-block intervals and identify that each is one publisher cluster.
Do not call this multi-dataset generalization.

The opening manifest must record the number and names of test publishers before any outcome
metrics are computed. All criteria, source definitions, and comparators remain frozen thereafter.

## Baseline fidelity labels

Registry names are operational IDs, not a claim that every constructor is author-native. PFA-SR is
the published restart e-detector attached to a ShiftLab deployment host; RMM is ShiftLab's matched
restart-mixture wrapper; E_rb is the existing ShiftLab rollback wrapper; E_swcert is a ShiftLab
sliding-window certificate. Gated and DISCERN are corrected common-contract ports, and SMCS is an
adapter. Xu is an acquisition-only component paired with the host certificate, not Xu et al.'s
published certificate. The Qiu and Gong entries are method-inspired ports and not author-native
implementations. CAMS uses a constant-policy adapter. Preserve these distinctions when describing
whichever baseline is strongest in the results. The full audit is
`docs/scoped_method_research_2026-11-06/BASELINE_FIDELITY.md`.
