# Paper 1 algorithm search: mechanism ledger and exit condition

**Outcome (2026-10-27): all three exit conditions are met. The Paper 1 algorithm search stops at
an evidenced NO-GO (goal checkpoint B).**

**Written 2026-10-27, before WP1 S3 results existed.** This document applies
[the SOTA supplement](agent_goal_sota_benchmark_supplement.md), Section 3, and
[the phase goal](agent_goal_stratified_monitor_phase.md), Section 8. It records which legitimate
sources of advantage over the strongest equally equipped incumbent remain untested. It also fixes
the condition under which we stop looking for a new Paper 1 monitoring algorithm.

## 1. Mechanism ledger

| # | Mechanism (incumbent limitation targeted) | Registered test | Outcome | Status |
|---|---|---|---|---|
| M1+M2+M3 | Stratified evidence, per-stratum bounds, optimal stratum allocation | WP2 G1 exact growth pre-screen, 20 slices, 19,440 rows | Candidate equals the equally equipped Chugg-style subgroup composition to 4.4e-16; ratio at most 1.000 against a required 1.5 | **Failed**: it *is* the standard composition |
| M4 | Data-efficient e-detector (sampling intensity follows evidence) | WP3 frozen pre-screen, 39,200 rows | 55% versus 100% detection at the primary cell; all 7 secondary gates failed | **Failed** |
| M7 | Boundary/interior PPI anchor making the one-sided range free of `q` | ADG G1 analytic pre-screen | At most 1.23× over gating against a required 1.5× | **Failed** |
| M5 | Disagreement gating | WP1 S0–S3; WP4 real-data check | S2 null passed; WP4: fixed gating matches full-feedback delay from a 5% budget on EIA | **Foundation, credited to DISCERN**; not claimable |
| M6 | Better betting engine (stakes up to 1, adaptive engines) | Supplied to every arm in WP1 S3 | — | **Foundation (fairness)**; not claimable |
| M8 | Burst-robust budget allocation over time (observed in WP4: paced `q` collapses during disagreement bursts) | None. The derivation below places it outside Paper 1 | — | **Out of scope**: Paper 3 (finite label budget over time), and close to WP3's temporal schedule |

**M8 reasoning.** Under a hard label budget and an unknown disagreement count, a gated HT monitor
trades two costs:
- **Exhaustion:** a fixed `q` spends the reserve before late harm arrives. This is the WP4 failure
  at `r = 0.02`.
- **Bound inflation:** a paced `q` falls during bursts, and the bound `5/q` grows.

This is the allocation of a finite budget over time. It is the charter's Paper 3 question, and
both the DE-CuSum literature and WP3's temporal schedule already address it. A Paper 1 claim
built on it would relabel an allocation result as a monitoring algorithm. It may seed a Paper 3
protocol (see Section 4).

## 2. Exit condition for the Paper 1 algorithm search

Stop the search, and report an evidenced NO-GO (goal checkpoint B), when **all** of the
following hold:

1. **Mechanisms exhausted.** Every claimable mechanism in the supplement (M1–M4, M7) has a
   recorded registered failure against the strongest equally equipped incumbent. *Met.*
2. **S3 reveals no uncredited mechanism.** WP1 S3 completes under its frozen protocol. No arm or
   composition shows at least 1.5× growth or +10 detection points over the strongest equally
   equipped incumbent from a source not already credited to a published method (gating to
   DISCERN, engines to their authors). *Met (2026-10-27): the best selective arms are gated
   HT/PPI with Timans GRAPA and the PPE gated alias; see
   [S3 results](gated_monitor_comparison_results.md).*
3. **No new derivable candidate.** No mechanism outside the ledger has a derivation predicting at
   least 1.5× growth over the strongest incumbent that could be pre-screened within the phase's
   remaining commit budget (the hard stop is 60 commits; 41 were used before this session's
   uncommitted work). *Met as of this writing: M8 belongs to Paper 3.*

If condition 2 fails because S3 exposes an unexpected advantage, write a new pre-screen protocol
for that mechanism before any further run. Do not reinterpret S3 as a method result.

**What the exit does not mean.** It is not a claim that no better monitor exists. It says that,
on this generator and the registered real paths, every mechanism we could derive is either
already published or failed its pre-registered screen.

## 3. What the benchmark manuscript absorbs at exit

- **The gating correction.** The repository's ungated sparse-label conclusions are partly label
  waste: about 91% of labels go to events whose cost is known to be zero. WP1 S3 measures the
  size of this effect, and WP4 replicates it on real EIA paths.
- **The estimand distinction.** Stratified "wins" over pooled monitors change the null to the
  intersection null.
- **The real-data validity table** (WP4) and the pacing-under-bursts caveat.
- **Negative screens:** ADG, stratified allocation, and the data-efficient controller, with their
  registered margins.

## 4. Where an algorithmic contribution could still come from (outside this phase)

- **Paper 3 (allocation).** A predictable allocation of labels over time that targets the
  exhaustion-versus-inflation trade-off (M8). The incumbents are WP3's temporal schedule and
  DE-CuSum-style rules. It needs its own charter protocol and pre-screen.
- **Paper 2 (candidate promotion).** It has a different estimand and different incumbents (MOPE,
  OPI, Wang certification). It is unaffected by these Paper 1 failures.

Either needs the user's approval for a new phase.

## 5. Candidate D strategy-extraction adapter checkpoint (2026-10-29)

The frozen toy protocol `docs/risk_preserving_approx/CANDIDATE_D_GADGET_ADAPTER_PROTOCOL_V1.md`
passed: pinned HSVI gap `1.4567e-7`, extracted payoff `0.44000000000000017`
against exact `0.44`, gadget residual `8.3819e-10`, and correct probe/signal-
conditioned guesses. The run used the pinned upstream commit
`05eaf101b38c1c9b301a1a5fb298bfe8b97f757d`; output and source hashes are in
`CANDIDATE_D_GADGET_ADAPTER_RESULTS_V1.md`. This is only a one-action-opponent
toy software check. It does not verify strategic security, switching-game
semantics, causal-null risk or any efficacy/compute claim. No ShiftLab candidate
or real data was run. Do not proceed to D3 until a two-action adversarial toy
passes independent maximin evaluation and a multiplier bracket can be certified
without access to the exact benchmark LP. Candidate D remains an established-
algorithm baseline possibility, with novelty and utility gates open.
