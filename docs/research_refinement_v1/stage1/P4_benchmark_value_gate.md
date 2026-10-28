# P4: benchmark-value gate (external method through the public interface)

**Drafted 2026-10-28 (Stage 1). Status: draft until the Stage 1 freeze record lists its hash.**
This protocol tests whether the evaluation contract can be used by someone who did not build it.
It is the decision rule in `FINAL_RESEARCH_PROPOSAL.md` §8: "the contract counts as delivered only if
an independently implemented method enters through the public interface without evaluator access and
produces hashed results on the reference suite." **Failing the gate triggers abandonment condition 3.**
The gate tests delivery, not performance; the external method does not need to win anything.

## 1. Public interface (to be implemented as `src/shiftlab/contract/`)

The contract module is the only surface the external method may use. It exposes plain dataclasses and
one `typing.Protocol`, and imports nothing from the evaluator or the generators.

```python
@dataclass(frozen=True)
class TaskSpec:  # fixed before the stream; no outcome information
    cost_bound: float  # C, |Z_t| <= C (5.0 on the synthetic suite)
    epsilon: float  # 0.1, the charter margin
    alpha: float  # 0.05
    horizon: int  # events after monitor start
    label_budget: float  # reserve, in label-price units
    price_range: tuple[float, float]


@dataclass(frozen=True)
class PublicEvent:  # what a deployed monitor can see before the label decision
    t: int
    x: np.ndarray  # covariates
    deployed_action: int
    reference_action: int
    disagreement: bool  # deployed_action != reference_action
    price: float  # label price for this event
    remaining_budget: float


@dataclass(frozen=True)
class Feedback:  # delivered after the query decision, only if queried
    t: int
    paired_cost: float  # Z_t = c(deployed) - c(reference); common-label contract
    propensity: float  # the q the harness actually used


class Monitor(Protocol):
    def reset(self, spec: TaskSpec) -> None: ...
    def propensity(self, event: PublicEvent) -> float: ...  # called before the coin; in [0, 1]
    def observe(self, event: PublicEvent, feedback: Feedback | None) -> None: ...
    @property
    def log_e_value(self) -> float: ...
```

**Harness obligations (evaluator side):**
- The harness draws the query coin from its own registered stream. It calls `propensity` before
  drawing the coin and refuses a value outside `[0, 1]`.
- It charges the price and refuses a query that would overdraw the reserve. A refused query counts as
  unqueried, and the refusal is recorded.
- It passes `Feedback` only for queried events, after the coin, and charges **every** query,
  agreements included. A queried agreement returns `Feedback(paired_cost=0.0)`. A monitor that
  exploits the free disagreement flag returns `q = 0` on agreements; one that does not (uniform HT)
  pays for agreement labels. This difference is what H-B1a measures.
- It records `log_e_value` after each `observe` and declares an alarm at `log_e_value >= log(1/alpha)`.
- **Oracle quantities never cross the interface.** These are the evaluator's expected costs, onset
  times and scenario labels.

**Isolation check (automated):** a test parses the external adapter's imports and fails if it imports
anything except the standard library, `numpy`, `scipy` and `shiftlab.contract`. Above all, it must
not import `shiftlab.dive`, `shiftlab.decision_harm_experiment` or the evaluator.

## 2. External method

- **Primary: Comparecast-style comparison e-process** (Choe and Ramdas, "Comparing sequential forecasters").
  It is applied to the paired-cost stream with the eventwise null `E[Z_t − ε | F_{t−1}] ≤ 0`, using
  Horvitz–Thompson weighting for gated queries. Its native null is a running-average null. The adapter
  must test the eventwise null or disclose the difference, per Codex round 2. The paper's GRAPA/mixture
  construction is acceptable if implemented from the paper.
- **Fallback, if the Comparecast adapter cannot be made to fit the interface:** a WATCH-style
  (Prinster et al., ICML 2025) weighted conformal test martingale. This needs a stated score bridge
  from paired cost to conformity score, and a disclosure that its null is distributional, not a
  decision-cost mean.

**Who implements it:** a separate agent session, given only:
- this document;
- the contract module's source and docstrings;
- the published paper.

It must not read `src/shiftlab/dive/comparecast_gamma_mixture.py` or any other repository
implementation. Its transcript or session identifier is recorded as provenance.

## 3. Reference suite (all on fresh registry seeds; no exposed test windows)

| Suite | Cells | Seeds | Purpose |
|---|---|---|---|
| R5-null | S2-style stationary and benign-nuisance nulls at budgets {0.02, 0.05, 0.10, 0.20} | 1,000 streams per cell from a fresh registry block | Validity |
| R5-alt | E2's H-B1 cells (`boundary_local_harm`, r ∈ {0.02, 0.05, 0.20}) | 200 streams per cell from a fresh block | Produces comparable detection results |

Seeds are allocated by `shiftlab.seed_registry.allocate` and registered before the run.

## 4. Gate criteria (all must pass)

1. **Interface:** the adapter passes the isolation check and runs end to end through the harness on
   every reference cell, without harness changes made for that adapter.
2. **Validity:** on R5-null, the per-cell exact one-sided Clopper–Pearson upper bound on the
   false-alarm rate, with Bonferroni across the 8 cells, is ≤ α = 0.05. If this fails, the adapter is
   reported as invalid and the gate fails on validity. A bug found and fixed is rerun on a new seed
   block, and both blocks are reported.
3. **Hashed results:** per-stream outputs, manifest (git HEAD, adapter sha256, seed block, config
   sha256) and summary are written, and their SHA-256 values are recorded in a results file.
4. **Comparable reporting:** R5-alt detection rates and labels spent are reported next to the
   contract baselines on the same streams. This is descriptive only, and no ranking claim is made.

**Outcome:** PASS if 1–3 hold (4 is reporting). FAIL otherwise, and the failure mode is recorded.

## 5. What this gate does not show

- It does not show that the external method is good, novel or the best comparator.
- It does not show the contract handles action-dependent feedback (out of scope) or delayed feedback
  (not part of this gate).
- One external method is the minimum. A second (the WATCH fallback) strengthens the claim but is not
  required.

## 6. Order of work

1. Implement `src/shiftlab/contract/` and the harness, and port two in-repo baselines through it
   (gated HT fixed; uniform HT) as a parity check. They must reproduce E2 results on shared seeds
   exactly.
2. Freeze this protocol, the contract source hashes and the seed blocks.
3. Start the separate implementer session.
4. Run R5 and record the results.
