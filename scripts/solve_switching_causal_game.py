"""Run the single registered classical causal-game development reference."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from fractions import Fraction as F
from pathlib import Path

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel

if __name__ == "__main__":
    config = GameConfig()
    model = RegimeModel(emission0=F(1, 20), emission1=F(19, 20))
    target = Path("outputs/switching_causal_game_v1")
    target.mkdir(parents=True, exist_ok=True)
    try:
        report, _, policy = CausalSwitchingGame(config, model).solve()
    except RuntimeError as error:
        failure = {"status": "registered_reference_failed", "reason": str(error)}
        (target / "failure.json").write_text(json.dumps(failure, indent=2) + "\n", encoding="utf-8")
        raise
    report["config"] = asdict(config)
    report["working_model"] = asdict(model)
    paths = (
        "src/shiftlab/dive/causal_switching_game.py",
        "src/shiftlab/dive/delayed_regime_information.py",
        "scripts/solve_switching_causal_game.py",
        "tests/test_causal_switching_game.py",
        "docs/switching_causal_game_reference_v1.md",
    )
    report["source_sha256"] = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}
    (target / "results.json").write_text(
        json.dumps(report, default=str, indent=2) + "\n", encoding="utf-8"
    )
    (target / "policy.json").write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, default=str, indent=2))
