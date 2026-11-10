# 07 — Confirmation protocol (DRAFT TEMPLATE)

**Status: DRAFT. This is a template, not a registration.** No confirmation window has been opened under it. The real
registration is a later, committed document (with sealed hashes) that fills every `<...>` field below *before* any
confirmation window is built or opened, and appends the corresponding `register` rows to
[`confirmation_attempts.csv`](confirmation_attempts.csv) ([08](08_CONFIRMATION_LEDGER.md)). Statistical method and
power: [09](09_STATISTICAL_CERTIFICATION.md).

## 0. Identity
- Protocol id: `<P1-SCALE25-CONF-n>`; registration commit: `<sha>`; registered UTC: `<ts>`.
- Method under test (frozen, code SHA): `<method id, sha>`. New method versions get new confirmation data.
- Contract (unchanged): T = 2000, B = 200, c_q = .05, c_s = 5, label delay 100, 10 policy seeds `<seed base>`.
  Mean net cost is the objective. No CVaR, tail or worst-case gate.

## 1. Estimand and reference
- `J(d, p) = 100 * mean over episodes (net/T)`. Episode value = mean over the policy seeds, per episode.
- `r_d = 100 * (J_ref,d - J_new,d) / J_ref,d`, positive = better. Cohort `R(S) = mean_{d in S} r_d`.
- Reference rule per dataset (fixed before opening): `<rule, e.g. the strongest of the panel on the development window,
  chosen from development data only>`. The reference policy list, with code SHAs, is part of this registration.
- The inference is conditional on the fitted model pair and the realised stream of each dataset.

## 2. Datasets and windows
- Candidate datasets: `<list with dataset_id, parent_source_id>`; confirmation windows defined mechanically from the
  dataset eligibility protocol, unbuilt at registration; sealed array hashes recorded at build time.
- A dataset is *opened* when any policy is run on its confirmation window. Each opened dataset is exactly one
  attempt. A window is opened once.
- Datasets that fail the unchanged eligibility gates are reported as ineligible, not replaced. Ineligibility is
  decided from validation data and episode counts only, never from policy results.

## 3. Statistics (frozen; see 09)
- Per-dataset bound: primary block-Fieller lower bound, the minimum over block lengths `ceil(n^(1/3))` and
  `ceil(n^(1/2))` (n = number of episodes), t reference with `n_blocks - 1` degrees of freedom, at level
  `1 - alpha_i`. Sensitivity (reported, not decisive): cube-root only, studentised block bootstrap at the levels where it is
  resolvable.
- Level: `alpha_i = .05 / (i (i+1))`, `i` = the chronological ledger index assigned at registration of that dataset,
  including the 7 legacy indices. The planned indices for this protocol are `i = <first> .. <last>`.
  *Alternative to be chosen here, once, before registration:* the batch variant (09 section 6), where datasets
  registered together share `alpha = .05 / (j (j+1) M_j)`. The default is the per-attempt rule of the brief.
- Success (all required): at least 25 distinct datasets (distinct `parent_source_id`) in the selected set `S`; `L_d > 0`
  for every `d` in `S`; `R_lower(S) = mean_{d in S} L_d >= 2.5`; ledger integrity valid; no deviation from this
  protocol. `S` may be chosen after seeing the results; the union bound covers every `S` simultaneously.
- Also reported, whatever the outcome: counts (registered, opened, positive, supported, selected), the mean
  reduction over *all* opened attempts and its simultaneous lower bound, and the mean of the selected cohort labelled as
  selected (winner's curse applies to its point value).

## 4. Integrity checklist (all must hold to certify)
- [ ] Ledger `validate()` returns no problems; every index was assigned before the window was built.
- [ ] Sealed hashes match; train-only preprocessing; chronological splits; no confirmation information reached any
      tuning, reference selection or screen.
- [ ] Method, reference, policy seeds and code SHAs match this registration; no changed threshold, margin or contract.
- [ ] Failures, ineligible datasets and unopened registrations are listed in the report.

## 5. Deviations
Any deviation is stated in the result document and makes the outcome exploratory unless it is shown to be
decision-irrelevant by an analysis fixed here: `<list>`.
