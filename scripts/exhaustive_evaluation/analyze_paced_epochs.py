"""Development ranking and realized-output alias diagnostic; no confirmation claim."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"


def main():
    assert json.loads((DOC / "paced_epochs_status.json").read_text())["status"] == "completed"
    reg = json.loads((DOC / "paced_epochs_registration.json").read_text())
    data = pd.DataFrame(json.loads((DOC / "paced_epochs_results.json").read_text())["rows"])
    null = (
        data[data["case"].isin(["harmful", "tie", "harmful_after_shift"])]
        .groupby("id")
        .promotion_rate.max()
    )
    means = data.groupby("id").delta_vs_incumbent.mean()
    eligible = means[(null <= 0.05) & means.index.str.startswith("EP_")].sort_values()
    winner = str(eligible.index[0])
    index = int(winner.split("_")[1])
    hashes = [hashlib.sha256() for _ in range(504)]
    for kind in reg["cases"]:
        with np.load(ROOT / f"outputs/exhaustive_evaluation/paced_epochs/{kind}.npz") as arrays:
            assert arrays["first"].shape == (508, 64)
            for i in range(504):
                for key in ["first", "labels", "total_cost", "delta_vs_incumbent"]:
                    hashes[i].update(arrays[key][i].tobytes())
    digest = [h.hexdigest() for h in hashes]
    result = {
        "stage": "development selection, independent confirmation required",
        "registered_configs": 504,
        "distinct_observed_output_signatures": len(set(digest)),
        "note": "identical observed outputs are not proof of algorithmic identity; structural one-epoch quota aliases removed prospectively",
        "selected_id": winner,
        "selected_config": reg["configurations"][index],
        "selected_macro_delta": float(eligible.iloc[0]),
        "selected_max_empirical_null": float(null[winner]),
        "ranked_top10": eligible.head(10).to_dict(),
        "rows": data[data.id.isin([winner] + reg["references"])].to_dict("records"),
    }
    (DOC / "paced_epochs_decision.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
