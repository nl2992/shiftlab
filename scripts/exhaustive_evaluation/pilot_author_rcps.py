"""Registered multi-seed native-task pilot of the six original active-RCPS arms."""

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from scripts.exhaustive_evaluation.smoke_author_rcps import load_author_simulation

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"


def main():
    regpath = DOC / "author_rcps_pilot_registration.json"
    if regpath.exists():
        raise FileExistsError("inspect existing native process/artifacts before rerunning")
    vendor = ROOT / "outputs/exhaustive_evaluation/active-rcps"
    sources = [
        Path(__file__),
        ROOT / "scripts/exhaustive_evaluation/smoke_author_rcps.py",
    ] + sorted(vendor.glob("*.py"))
    reg = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "stage": "native-task descriptive pilot, NOT paper-scale reproduction or cost-switching confirmation",
        "seeds": [17, 29, 43],
        "parameters": {
            "label_ct": 200,
            "theta": 0.05,
            "q_min": 0.1,
            "target_rate": 0.3,
            "beta_dim": 3,
            "est_loss_dim": 3,
        },
        "source_commit": "a67f85d603df2bb3e32ef007f445191923ebd990",
        "primary": "reported and actual certified beta at equal200 labels; all6 arms, no selection",
        "truth": "native p uniform[0,1], Y|p Bernoulli(p); risk(beta)=(1-beta)^2/2; beta_star=1-sqrt(2theta)",
        "limits": "three seeds cannot validate alpha; no delay, no deployment switches; original expected-budget normalization retained; nominal label-all arm queries every observation",
        "repairs": "same declared inactive-branch syntax/type repairs as original smoke; original source unchanged",
        "source_hashes": {
            p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sources
        },
    }
    regpath.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    statuspath = DOC / "author_rcps_pilot_status.json"
    status = {"status": "running", "completed_seeds": []}
    statuspath.write_text(json.dumps(status), encoding="utf-8")
    test_once, _ = load_author_simulation()
    rows = []
    start = time.perf_counter()
    for seed in reg["seeds"]:
        result = test_once(seed=seed, **reg["parameters"])
        for name, agent, labels, betas, data in zip(*result, strict=True):
            mart = agent._primal_player._iwmart
            safe_beta = float(mart.curbeta[0])
            count = float(agent._primal_player._suml)
            assert count == 200 and len(agent._hist) >= 200
            history_q = np.array(
                [float(h["pred"][0][0].detach().reshape(-1)[0]) for h in agent._hist]
            )
            assert np.all((history_q >= 0.1) & (history_q <= 1))
            rows.append(
                {
                    "seed": seed,
                    "arm": name,
                    "labels": count,
                    "observations": len(agent._hist),
                    "reported_data_index": int(data[-1]),
                    "reported_beta": float(betas[-1]),
                    "certified_beta": safe_beta,
                    "true_risk_at_certified_beta": (1 - safe_beta) ** 2 / 2,
                    "mean_query_probability": float(history_q.mean()),
                    "realized_query_fraction": count / len(agent._hist),
                }
            )
        status["completed_seeds"].append(seed)
        statuspath.write_text(json.dumps(status), encoding="utf-8")
        (DOC / "author_rcps_pilot_results.json").write_text(
            json.dumps({"rows": rows, "elapsed_seconds": time.perf_counter() - start}, indent=2),
            encoding="utf-8",
        )
        print("Native six-arm seed", seed, "complete", flush=True)
    status["status"] = "completed"
    statuspath.write_text(json.dumps(status), encoding="utf-8")


if __name__ == "__main__":
    main()
