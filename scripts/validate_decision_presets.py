"""Execute descriptive, replicated action and risk checks for decision presets."""

import json
from pathlib import Path

import numpy as np

from shiftlab.data.synthetic import decision_stress_catalogue, generate_chunks


def main() -> None:
    seeds = [31, 43, 59, 71, 89]
    records = []
    for preset in decision_stress_catalogue(seed=seeds[0], n=12000):
        for seed in seeds:
            config = preset.config.model_copy(update={"seed": seed})
            for frame, oracle in generate_chunks(config):
                positive = frame.target.to_numpy() > 0
                action = oracle.oracle_action.to_numpy(dtype=bool)
                fn_cost = oracle.fn_cost.to_numpy()
                realized_loss = np.where(action, ~positive, fn_cost * positive).astype(float)
                weights = oracle.weight.to_numpy()
                for regime, selected in (
                    ("baseline", weights < 0.5),
                    ("shifted", weights >= 0.5),
                ):
                    if not np.any(selected):
                        continue
                    p = oracle.probability_positive.to_numpy()[selected]
                    action_regime = action[selected]
                    cost = fn_cost[selected]
                    records.append(
                        {
                            "preset": preset.name,
                            "scenario": config.scenario,
                            "seed": seed,
                            "regime": regime,
                            "n": int(selected.sum()),
                            "oracle_action_rate": float(action_regime.mean()),
                            "oracle_expected_risk": float(
                                oracle.oracle_risk.to_numpy()[selected].mean()
                            ),
                            "realized_loss": float(realized_loss[selected].mean()),
                            "realized_loss_se_oracle": float(
                                np.sqrt(
                                    np.sum(np.where(action_regime, 1.0, cost) ** 2 * p * (1 - p))
                                )
                                / selected.sum()
                            ),
                        }
                    )
    summary = []
    for preset in sorted({record["preset"] for record in records}):
        for regime in ("baseline", "shifted"):
            group = [
                record
                for record in records
                if record["preset"] == preset and record["regime"] == regime
            ]
            if not group:
                continue
            summary.append(
                {
                    "preset": preset,
                    "regime": regime,
                    "replicates": len(group),
                    "mean_n": float(np.mean([r["n"] for r in group])),
                    "mean_oracle_action_rate": float(
                        np.mean([r["oracle_action_rate"] for r in group])
                    ),
                    "mean_oracle_expected_risk": float(
                        np.mean([r["oracle_expected_risk"] for r in group])
                    ),
                    "mean_realized_loss": float(np.mean([r["realized_loss"] for r in group])),
                    "mean_oracle_standard_error": float(
                        np.mean([r["realized_loss_se_oracle"] for r in group])
                    ),
                }
            )
    report = {
        "description": "Five-seed descriptive oracle decision diagnostics by regime.",
        "replicates_per_preset_regime": len(seeds),
        "n_per_seed": 12000,
        "utility_status": "Imposed research cost matrices, not application-grounded estimates.",
        "records": records,
        "summary": summary,
        "limitations": [
            "Seed-level summaries are descriptive; no across-seed confidence intervals are claimed.",
            "The reported standard error uses the known per-row Bernoulli oracle variance and is conditional on generated requests.",
            "These are evaluator-oracle results, not fitted-policy performance or causal effects.",
        ],
    }
    output = Path("data/reports/decision_stress_validation.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for row in summary:
        if row["regime"] == "shifted":
            print(
                f"{row['preset']}: action={row['mean_oracle_action_rate']:.3f} "
                f"risk={row['mean_oracle_expected_risk']:.4f} "
                f"loss={row['mean_realized_loss']:.4f}"
            )
    print(output)


if __name__ == "__main__":
    main()
