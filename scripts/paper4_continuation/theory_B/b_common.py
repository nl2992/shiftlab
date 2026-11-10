"""Shared exact helpers for WP B (implicit learner-side optimisation) theory tests.

Everything here is exact rational arithmetic on the first-promotion decomposed game
(`FirstPromotionDecomposedGame`).  The learner tree is used only as a *measurement
device* on small instances: we count how many distinct candidate pricing states a
state-merged dynamic program would need, and we verify by brute force that the merge
is exact.  No new solver is claimed.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.dive.causal_switching_game import GameConfig  # noqa: E402
from shiftlab.dive.delayed_regime_information import RegimeModel  # noqa: E402
from shiftlab.paper4.frontier_cuts_fast import FastGame  # noqa: E402

RESULTS = ROOT / "docs/paper4_continuation/theory_B/results"
HALF = F(1, 2)


def cell(horizon, budget, delay, trans, emis, alpha=F(1, 10)):
    config = GameConfig(
        horizon=horizon, budget=budget, delay=delay, alpha=alpha,
        query_cost=F(1, 100), switch_cost=F(1, 10), max_nodes=2_000_000,
    )
    model = RegimeModel(transition01=trans, transition10=trans, emission0=emis[0],
                        emission1=emis[1], prior1=F(1, 2))
    return config, model


def describe(config, model):
    return {"T": config.horizon, "B": config.budget, "d": config.delay,
            "alpha": str(config.alpha), "transition": str(model.transition01),
            "emissions": [str(model.emission0), str(model.emission1)]}


def built_game(config, model):
    game = FastGame(config, model)
    game._alternative((), (), 0, F(1), model.prior1, F(0))
    game.built = True
    return game


def release(game, time, belief):
    """Release labels due at `time`: list of (outcome, alt branch mass, conditioned belief)."""
    due = {r for _, pending, _ in belief for r, _ in pending if r <= time}
    if not due:
        return None
    assert len(due) == 1, "one query per event and fixed delay => at most one due label"
    (d,) = due
    out = []
    for y in (0, 1):
        masses = defaultdict(F)
        total = F(0)
        for state, pending, mass in belief:
            if (d, y) in pending:
                total += mass
                masses[state, tuple(i for i in pending if i != (d, y))] += mass
        if total:
            out.append((y, total, game._canonical(masses)))
    return d, out


def initial_belief(game):
    p1 = game.model.propagate(game.model.prior1, 1)
    return game._canonical({(0, ()): 1 - p1, (1, ()): p1})


def positive(game, belief):
    m = game.model
    return sum(mass * (m.emission1 if s else m.emission0) for s, _, mass in belief)


def jsonable(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def write_result(name: str, payload: dict, script: Path) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / name
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    payload = {"script": str(script.relative_to(ROOT)),
               "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
               **jsonable(payload)}
    path.write_text(json.dumps(payload, indent=1))
    return path
