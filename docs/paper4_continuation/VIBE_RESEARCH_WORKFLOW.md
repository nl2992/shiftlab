# HKUSTDial vibe-research-workflow plan (applied 2026-11-10)

Skill: `vibe-research-workflow` (HKUSTDial Supervisor-Skills), invoked natively. Phase: **mixed** (coding,
theory, literature). Writing comes only if a result survives.

## Behavioural rules (acknowledged)

1. AI assistance covers literature search, code and debugging, and language.
2. **Research direction, novelty judgments and core conclusions belong to the user (Nigel Li).** In this
   autonomous programme, every candidate-level GO/NO-GO written by the lead agent is a *proposal with evidence*.
   It becomes a conclusion only after the user reviews `FINAL_DECISION.md`. Tension recorded: the directive asks the
   agent to decide autonomously. Decisions are therefore written with their full evidence chain so the user can
   verify or overturn them.
3. Every AI-produced result is verified against artifacts. The lead (Opus) independently re-runs or recomputes each
   subagent claim before it is recorded. Subagent prose is never copied into a ledger as fact.
4. No fabricated citations. A citation is marked "read (sections)", "abstract only" or "unverified". A paper counts
   for a novelty decision only if its relevant section was actually read.
5. No fabricated results. Every number traces to a committed JSON or script output. Failures are kept
   (for example, `fcg_scale_v2_run1_serialization_failure.json`).
6. AI disclosure: for ICML/NeurIPS/ICLR, the user must check the venue's current LLM-use policy before submission.
   This programme is substantially AI-executed, and that must be disclosed.

## Workflow plan

| Block | Phase | Activity | Tool / agent | Lead check |
|---|---|---|---|---|
| A | coding | Root-mixture fix; ablation harness; T10D1 feasibility | Sonnet builders | Re-run tests; recompute exact risk and cost independently; timing campaign run by the lead on a quiet CPU |
| B | theory | Implicit learner-side optimisation (B1–B4) | Opus theory agent | Re-derive every claimed theorem; rerun each small exact test; check bound validity against the unrestricted class |
| C | theory | Safety premium Γ (zero / positive / upper bound / adaptivity) | Opus theory agent | Recompute Γ on stated instances; attack proofs with counterexample search |
| E | literature | Source-grounded matrix | Sonnet literature agent (deep-research method) | Spot-read decisive sources myself |
| G | review | Fresh-context adversarial review | Opus subagents (same-family, provisional) | Verify each objection against code and data |

## Integrity gate plan

- **Verification points:** every ledger entry cites an artifact path plus the command that regenerates it.
- **[user-attest]** Items 2–7 of the skill's gate require the user. They are listed in `FINAL_DECISION.md` as
  open attestations.
