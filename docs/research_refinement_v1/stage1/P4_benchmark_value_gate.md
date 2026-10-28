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

**Isolation (Codex review 1: an AST import check cannot establish isolation, because `pathlib`,
`sys` or `inspect` can still read files and process state).** Isolation is by execution
environment, not by lint:

- `shiftlab.contract.sandbox` builds an **implementation packet**: a temporary directory holding
  only a standalone copy of `interface.py`, the adapter file, this protocol and
  `CONTRACT_README.md`, and a small runner (its sha256 manifest is recorded).
- The adapter runs in a separate interpreter: `python -I`, `cwd` = the packet, a stripped
  environment (no `PYTHONPATH`; only the variables Python needs to start), `shiftlab` removed from
  `sys.path` and blocked by a meta-path finder. Events and feedback cross as JSON lines over
  stdin/stdout; the harness stays in the parent and is the sole owner of the coin, prices,
  reserve and costs. The adapter imports the contract as `from interface import ...` and defines
  `build_monitor()`.
- The AST import check (`shiftlab.contract.isolation`) stays as an extra **lint** only: standard
  library, `numpy`, `scipy`, `interface`.
- Before the adapter loads, the runner installs a `sys.addaudithook` guard (audit hooks cannot be
  removed from Python code). It denies opening files outside the packet (read-only access is
  allowed only under the Python prefixes needed for stdlib, numpy and scipy), `os.listdir`,
  `os.scandir` and `glob.glob` outside the packet and those prefixes, subprocess, `os.system`,
  `os.exec*`, `os.spawn*`, `os.posix_spawn`, fork, `socket.*`, `ctypes.*`, and importing
  `ctypes`/`_ctypes`/`cffi`. **Residual:** audit hooks are a strong in-process guard, not an OS
  sandbox. A determined native-extension escape is out of scope, and the adapter can still tamper
  with in-process state. Full isolation therefore additionally requires the **implementer session to be
  given only the packet** (procedural). The session identifier and the packet manifest are
  recorded as provenance. A tested malicious adapter (`import shiftlab`, reading
  `../../src/...`, absolute paths to evaluator files, subprocess, socket, ctypes) fails inside the
  sandbox (`tests/test_contract_sandbox.py`).
- Harness semantics are locked: reserve stop when the remaining reserve is below
  `price_range[1]` (default, recorded in `HarnessResult.reserve_stop_rule`); NaN or infinite
  `log_e_value` is rejected.

## 2. External method

- **Primary: Comparecast-style comparison e-process** (Choe and Ramdas, "Comparing sequential forecasters").
  It is applied to the paired-cost stream with the eventwise null `E[Z_t − ε | F_{t−1}] ≤ 0`, using
  Horvitz–Thompson weighting for gated queries. Its native null is a running-average null. The adapter
  must test the eventwise null or disclose the difference, per Codex round 2. The paper's GRAPA/mixture
  construction is acceptable if implemented from the paper.
- **Fallback, if the Comparecast adapter cannot be made to fit the interface:** a WATCH-style
  (Prinster et al., ICML 2025) weighted conformal test martingale. This needs a stated score bridge
  from paired cost to conformity score. Its null is distributional, not a decision-cost mean, and
  disclosure does not transfer decision-mean validity. A WATCH adapter is reported as a
  **different-null comparator only**: it is not scored on the validity criterion for the
  eventwise-mean null and cannot count as the gate's primary method.

**Required submission contents (a generic betting reimplementation or an always-zero statistic must
not pass):**
- **Paper-faithful numerical fixture:** the adapter must reproduce at least one worked example or
  figure value from the paper (or a derivation-checked fixture written by the implementer, with the
  derivation), as a runnable test inside the packet that passes without the repository.
- **Explicit HT / null / bound argument:** a written argument that the Horvitz–Thompson weighting
  is unbiased for the paired cost, which null the statistic is an e-process for, and that its
  bound is valid for the propensities it returns (global bound, or the stronger context-conditional
  null when the propensity depends on the current event; see `CONTRACT_README.md`).

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

1. **Interface:** the adapter passes the import lint, runs inside the sandbox (implementation
   packet) end to end through the harness on every reference cell without harness changes made
   for that adapter, and ships the numerical fixture and written argument of section 2.
2. **Validity:** on R5-null, the per-cell exact one-sided Clopper–Pearson upper bound on the
   false-alarm rate, with Bonferroni across the 8 cells, is ≤ α = 0.05. If this fails, the adapter is
   reported as invalid and the gate fails on validity. A bug found and fixed is rerun on a new seed
   block, and both blocks are reported.
3. **Hashed results:** per-stream outputs, manifest (git HEAD, adapter sha256, seed block, config
   sha256) and summary are written, and their SHA-256 values are recorded in a results file.
4. **Functionality (power floor):** on R5-alt, the pooled detection rate over the three cells must
   exceed a minimal power floor `F` registered in the freeze record before the implementer session
   starts (it must sit clearly above alpha; a statistic that never alarms has detection 0). If it
   does not, the adapter is reported as **non-functional** and the gate fails on functionality.
   **Registered value (lead, 2026-10-28): `F = 0.25`.** On E2 development seeds, the weakest valid
   contract baseline, uniform HT, pooled 0.27 over these cells (0.00 / 0.06 / 0.74), and the gated
   arms about 0.85. `F` is set just below the weakest baseline and five times alpha, so it rules out
   non-functional statistics without requiring the adapter to compete.
5. **Comparable reporting:** R5-alt detection rates and labels spent are reported next to the
   contract baselines on the same streams. This is descriptive only, and no ranking claim is made.

**Outcome:** PASS if 1–4 hold (5 is reporting). FAIL otherwise, and the failure mode is recorded.

## 5. What this gate does not show

- It does not show that the external method is good, novel or the best comparator.
- It does not show the contract handles action-dependent feedback (out of scope) or delayed feedback
  (not part of this gate).
- One external method is the minimum. A second (the WATCH fallback) strengthens the claim but is not
  required.

## 6. Order of work

1. Implement `src/shiftlab/contract/` and the harness, and port in-repo baselines through it
   (gated HT fixed and paced; uniform HT with `q = r` passed explicitly) as a parity check. They
   reproduce `replay_gated` and E2's `replay_uniform` log-e paths exactly on shared inputs
   (`tests/test_contract.py`). Done.
2. Freeze this protocol, the contract source hashes, the power floor `F` and the seed blocks.
3. Start the separate implementer session with only the packet (sandbox `build_packet`).
4. Run R5 and record the results.
