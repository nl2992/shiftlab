# Paper 4 decision: value-shielded causal planning (Candidate E value screen)

**Date:** 2026-11-09. **Branch:** `research/paper4-value-shielded-causal-planning`, created from
`origin/research/risk-preserving-switching-approx-2026-10-29` (`2bd2e8e4`). **Nothing committed or
pushed. Nothing merged. No reserved holdouts, real data, or CRSP accessed.**

**Decision: NO-GO for building the value-shielded solver (Work Packages E/F).** The value-sensitive
pruning hypothesis fails its pre-registered screen on the registered T=10 stress cell. The
theorem is sound but is a sharpening of Candidate E, not a new contribution.

## 1. Problem

Two-law budgeted switching with a hard pathwise query budget, delayed feedback hidden from the
learner, a full-history adaptive causal null with `Pr(first promotion) <= alpha`, and alternative-HMM
economic cost. Prior exact tree sizes and certificates are in
`docs/risk_preserving_approx/`. The directive asks whether a value-sensitive safe pruning rule can
shrink the pre-promotion tree while keeping risk exact and bounding cost loss against the
unrestricted optimum `V*`.

## 2. Theorem candidate (Work Package B)

For a pre-promotion public history `h`, let `W(h)` be the expected alternative cost of permanent
incumbent deployment with no further queries, and `J_lower(h) <= J_free(h)` a certified lower bound
on the free continuation optimum. Let `D(h) = W(h) - J_lower(h)`. Let `S_delta = {h : D(h) <= delta}`,
with first-entry semantics. Let `pi^S` be `pi` with the safe continuation (incumbent, no queries, no
promotion) at first entry into `S`.

**Claim 1 (risk, pathwise).** For every causal-null strategy `nu`, `R_null(pi^S, nu) <= R_null(pi, nu)`.
Hence `sup_nu` also decreases. *Proof:* the two policies agree until first entry into `S`. After
entry, `pi^S` never promotes. The first-promotion event under `pi^S` is therefore a subset of that
under `pi` on the same coupled randomness and null responses. Since the null is causal, its
responses depend only on public information and are identical until entry. **Holds.** It needs no
sign or nonnegativity assumption on costs.

**Claim 2 (value).** Under `pi`, `E[cost-to-go | h] >= J_free(h) >= J_lower(h)` at every entry `h`.
Under `pi^S` it equals `W(h)`. So the conditional excess at `h` is at most `D(h) <= delta`. Summing
over first-entry events gives `C_alt(pi^S) - C_alt(pi) <= delta * P_alt^pi(reach S) <= delta`.
This holds for signed continuation costs, including rollback, re-promotion and switching. The
bound is per-history with uniform tolerance, which is sharper than Candidate E's `L*T*p_S` envelope.
Applying it to an optimal `pi*` gives `0 <= C_alt(restricted optimum) - V* <= delta`, because the
restricted optimum is no worse than `pi*^S` and `pi*^S` is feasible for the original problem by
Claim 1. **Holds.**

**Counterexample search.** No counterexample found for the stated finite-horizon, exact-arithmetic
setting. Two points need care in any implementation. (i) `J_lower` must be a true lower bound on
`J_free(h)` conditioned on the public key, and the pending-label posterior must be marginalised
(§4 does this). (ii) The theorem bounds the *restricted* optimum only, so a practical gain must
come from a restricted solver that is faster than the unrestricted one.

**Assessment.** Claims 1–2 are correct and sharpen `CANDIDATE_E_SAFE_HISTORY_PRUNING_THEOREM_V1.md`
(its lemma uses `L*T*p_S`; this uses `delta`). The sharpening is incremental.

## 3. Prior-art reduction (partial)

Admissible value-bound pruning, branch-and-bound on chance-constrained POMDPs, and hypothesis-pruning
value bounds are known. The directive's comparators (RAO*, NeurIPS 2023 anytime deterministic POMDP
guarantees, JAIR 2025 oracle-guided synthesis, AAAI 2026 SAB, NeurIPS 2025 robust POMDP evaluation)
are cited from the directive and the existing Candidate E document. **I did not re-verify these
sources in this session.** Claims 1–2 have the form of standard admissible pruning plus a
policy-restriction certificate. Under the directive's own novelty rule, the theorem does not
establish a new contribution.

## 4. Pre-registered screen (new)

Protocol: `CANDIDATE_E_VALUE_SHIELD_SCREEN_PROTOCOL_V1.md` (registered before the run). Runner:
`scripts/research_risk_approx/screen_value_shield_pruning.py`. Output:
`candidate_e_value_shield_screen_v1.json`.

Frozen cell: T=10, B=4, d=2, transition 1/10, emissions (1/50, 49/50), prior 1/2, alpha 1/10,
query fee 1/100, switch fee 1/10. Exact enumeration over public pre-promotion keys. `W(h)` uses the
pending-marginalised posterior. `J_lower(h)` uses a fully-observed-state relaxation with queries
removed.

**Validity checks passed:**
- 0 <= `J_lower(h)` <= `W(h)` for all 4,867 keys (the script raises on violation).
- Enumeration counts match the earlier mass screen (4,867 histories, 13,420 pre-promotion
  realization columns), which independently checks the enumeration.
- Sanity at T=5, B=2, d=1 with the risk constraint removed: `J_lower(root) = 2/5`, while the exact
  free LP optimum is `2.002375`. The bound holds, but it is very loose (about 20% of the optimum).

**Screen results (registered tolerances):**

| delta | keys selected | collapsed public histories | removed columns | fraction removed |
|---|---:|---:|---:|---:|
| 1/100 | 0 | 0 | 0 / 13,420 | 0 |
| 1/20 | 0 | 0 | 0 / 13,420 | 0 |

**Diagnostic (post hoc, not a pass):** the smallest `D(h)` over all keys is about **0.156**, reached
at decision time 10. Every depth's minimum is at least 0.156 (depth 1: 4.66; depth 10: 0.156). A
uniform tolerance would have to exceed about 0.156 before any history is selected. That is
several times the registered 1/20, and is not a threshold to adopt now.

## 5. Decision rule and outcome

Registered rule: fail if the maximum removed-column fraction is below 5% at every tolerance. **Met
(0% at both). The value-sensitive screen fails.** The earlier mass-envelope screen failed too (max
5/122 ≈ 4.1%).

Paper-level stop condition: the screen enumerates the full public pre-promotion tree to compute
`W` and `J_lower`. The directive stops any candidate that needs the full history tree merely to
identify safe regions. Even with a pass, that condition would apply.

Both screens are consistent with the existing record. The Early Pruning adapter
(`EARLY_PRUNING_RESULTS_V1.md`) found no tree or cache reduction. The IID-relaxation pipeline
(`IID_RELAXATION_CERTIFIED_PIPELINE_RESULTS_V1.md`) gave a certified bound but no end-to-end speedup.

## 6. Why the hypothesis fails here

The relaxation that makes `J_lower` computable is loose: it drops the query budget and the
unobserved state, so it cannot certify that a history is economically negligible. Histories with a
near-deterministic posterior are rare in this cell (a likely explanation, not separately tested), because labels are delayed by 2 and the
symmetric transition (1/10) keeps reopening uncertainty. Certifying a region without enumerating
histories (Work Package C, Step B) would need a tighter, belief-based lower bound. No such bound
exists yet, and building one is a new research problem, not a tuning step.

## 7. Work packages not executed

- **Work Package D** (compact finite-state controllers): not implemented. The directive limits this
  path to a precise, non-standard contribution, and none has been identified.
- **Work Package E** (implementation in `first_promotion_decomposition.py`): not implemented. The
  pruning gate failed.
- **Work Package F** (T=5/T=6 exact-agreement runs, T=8/T=10 scaling, end-to-end timing): not run.
  Existing reference data are in `FULL_T8_DECOMPOSED_CERT_RESULTS_V1.md` and the pre-promotion
  counts above.

## 8. Reproduction

```bash
uv run --no-sync python scripts/research_risk_approx/screen_value_shield_pruning.py
uv run --no-sync ruff check scripts/research_risk_approx/screen_value_shield_pruning.py
```

The script refuses to overwrite its output. Runner hash is recorded inside the JSON.

## 9. Continue / pivot / stop

**Stop** the value-shielded solver line for Paper 4 at this cell. **Pivot** only if a belief-based
lower bound can be certified without history enumeration. That is a separate, pre-registered
research question, not a Paper 4 implementation. The mass-envelope route is closed.
