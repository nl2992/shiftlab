# Exhaustive candidate evaluation: execution registration

Registered 2026-10-30 before new efficacy runs. Base: `71ad2b3`.
User authorizes implementation, published-baseline comparisons, real-data acquisition and at least 500 combinations, followed by bottleneck-driven iteration if needed. The minimum refers to distinct executed algorithm configurations, not multiplying seeds or datasets. It does not mean 500 novel algorithms.

## Preservation and scope

This isolated worktree preserves prior results and reserved holdouts. Candidate J originals are copied unchanged from the risk-approx worktree and hashed before execution. No automatic merge/push. Local CPU only; bounded development jobs. The proposed earlier planning caps may be revised prospectively for the user's explicitly requested larger search, with costs recorded.

Two primary questions: (A) can compact-controller computation improve end-to-end certified planning rather than only fixed-policy verification? (B) can guidance/adaptation improve cost-null risk monitoring against faithful published competitors with matched information and costs? Mathematical novelty remains a separate source-reduction obligation.

## Run order

1. Snapshot inputs/environment; run J correctness tests and its existing T18/B18/d2 single benchmark, enforcing the registered 120-second reference cap externally. Keep timeout/error artifacts. No retuning this cell.
2. Retrieve primary source texts/code, inventory existing grids, and produce an explicit finite baseline coverage matrix with omissions. No unqualified claim to exhaust all literature.
3. Register at least 500 unique valid configurations in a hashed JSON manifest before screening. Unit-test delayed feedback, budget and evidence semantics. Smoke/profile before full development screen. Method, guidance, memory/discount, allocation and evidence restart parameters count as combinations only when behavior can differ. Duplicates/inactive parameters are excluded.
4. Evaluate all registered configurations on a shared, declared development battery including null, harmful, nuisance, delayed and guidance-failure worlds. Record per-seed outcomes, failures, runtime and all query costs. The first screen is exploratory, not alpha-calibration evidence or confirmation. Rank with safety and resource constraints before efficacy.
5. Diagnose common failure cells versus strong eligible baselines. Register a second round of bottleneck-targeted combinations before its execution if no candidate meets the plan's gate; do not present another blind grid as mechanism discovery.
6. Freeze a shortlist using development only; power fresh synthetic confirmation; prepare chronological real replay from agent-downloaded sources after leakage/exposure audit. Existing reserved holdouts stay closed. Record whether each new real period is exploratory or confirmatory.

## Baseline and statistical discipline

Map the estimand/null, label access, calibration cost, delay, hard versus expected budget, threshold guarantee and tuning for every baseline. Separate original code, verified reproduction, faithful adaptation and source-inspired implementations. Brier risk and cost risk are not directly interchangeable. Empirical PH/CUSUM thresholds require independent calibration; SR ARL is not finite-horizon FWER.

Do not select a metric after confirmation. Primary B target: lower total decision/query/switch cost at fixed resources; monitoring power and delay diagnose mechanism. A requires exact feasibility and a useful independently certified value gap plus end-to-end runtime. No winner is established by this registration.

Maintain an append-only ledger and machine-readable run status. A live process handle is required to treat a job as running. The goal stays active until implementation, baseline coverage, >=500 executed distinct combinations, bottleneck iteration where required, real-data validation, and independent confirmation/review are evidenced.
