"""Value-sensitive safe pruning screen (CANDIDATE_E_VALUE_SHIELD_SCREEN_PROTOCOL_V1).

Development-only structural calculation. For every exact public pre-promotion history k, computes
W(k) (permanent incumbent, no queries) and J_lower(k) (fully-observed-state relaxation), then the
first-entry pruning sets S_delta = {k : D(k) <= delta}, D = W - J_lower. Exact Fraction arithmetic.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from fractions import Fraction as F
from itertools import product
from pathlib import Path

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/risk_preserving_approx/CANDIDATE_E_VALUE_SHIELD_SCREEN_PROTOCOL_V1.md"
OUTPUT = ROOT / "docs/risk_preserving_approx/candidate_e_value_shield_screen_v1.json"
DELTAS = (F(1, 100), F(1, 20))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def enumerate_keys(game: CausalSwitchingGame):
    """Exact public keys with P(key) weights and P(s_t = 1 | key) = B/A (pending labels marginalised)."""
    horizon = game.config.horizon
    weight_sum: dict = defaultdict(F)
    state_sum: dict = defaultdict(F)

    def visit(history, outcomes, posterior, weight):
        time = len(history) + 1
        if time > horizon:
            return
        key = game.information(history, outcomes)
        state1 = game.model.propagate(posterior, 1)
        weight_sum[key] += weight
        state_sum[key] += weight * state1
        positive = game.model.emission(state1)
        for action, query in game.choices(history):
            if action:
                continue  # pre-promotion only
            next_history = history + ((action, query),)
            if query:
                for y, probability in ((0, 1 - positive), (1, positive)):
                    if not probability:
                        continue
                    likelihood1 = game.model.emission1 if y else 1 - game.model.emission1
                    next_posterior = state1 * likelihood1 / probability
                    visit(
                        next_history, outcomes + ((time, y),), next_posterior, weight * probability
                    )
            else:
                visit(next_history, outcomes, state1, weight)

    visit((), (), game.model.prior1, F(1))
    posterior = {key: state_sum[key] / weight_sum[key] for key in weight_sum}
    return posterior


def relaxed_value_table(game: CausalSwitchingGame):
    """V[t][(s, old)]: fully-observed-state relaxation, queries removed, switching charged."""
    model, horizon, switch = game.model, game.config.horizon, game.config.switch_cost
    table = {horizon + 1: {(s, a): F(0) for s in (0, 1) for a in (0, 1)}}
    for t in range(horizon, 0, -1):
        table[t] = {}
        for s in (0, 1):
            p_next_one = model.propagate(F(s), 1)  # P(s_{t+1} = 1 | s_t = s)
            emit = model.emission(F(s))
            for old in (0, 1):
                best = None
                for a in (0, 1):
                    cost = emit if a == 0 else 1 - emit
                    cost += switch * (a != old)
                    cont = (1 - p_next_one) * table[t + 1][(0, a)] + p_next_one * table[t + 1][
                        (1, a)
                    ]
                    value = cost + cont
                    best = value if best is None or value < best else best
                table[t][(s, old)] = best
    return table


def lower_bound_and_w(game, table, time, q):
    """q = P(s_time = 1 | key). Returns (W, J_lower)."""
    model, horizon = game.model, game.config.horizon
    w, state = F(0), q
    for _ in range(time, horizon + 1):
        w += model.emission(state)
        state = model.propagate(state, 1)
    j = (1 - q) * table[time][(0, 0)] + q * table[time][(1, 0)]
    return w, j


def columns_for(game, history):
    remaining = game.config.budget - sum(query for _, query in history)
    return len(tuple(product((0, 1), (0, 1) if remaining else (0,))))


def ancestors_of(key, time, delay):
    """Keys at each earlier decision time t' <= time, restricted to labels released by t'."""
    history, released = key
    out = []
    for tp in range(1, time + 1):
        prefix = history[: tp - 1]
        rel = tuple((s, y) for s, y in released if s + delay <= tp)
        out.append((tp, (prefix, rel)))
    return out


def screen(game, posterior, values):
    rows = {}
    for key, q in posterior.items():
        time = len(key[0]) + 1
        w, j = lower_bound_and_w(game, values, time, q)
        if not (0 <= j <= w):
            raise AssertionError(f"lower-bound validity failed at {key}")
        rows[key] = {"time": time, "W": w, "J": j, "D": w - j}
    total_columns = sum(columns_for(game, key[0]) for key in rows)
    results = []
    for delta in DELTAS:
        selected = {key for key, row in rows.items() if row["D"] <= delta}
        entries = set()
        removed = set()
        for key, row in rows.items():
            chain = ancestors_of(key, row["time"], game.config.delay)
            # a key is pruned if it or any ancestor is selected; an entry is a first selected key
            hits = [k for _, k in chain if k in selected]
            if hits:
                removed.add(key)
                if hits[0] == key:
                    entries.add(key)
        removed_columns = sum(columns_for(game, key[0]) for key in removed)
        per_depth = {}
        for depth in range(1, game.config.horizon + 1):
            keys = [k for k, r in rows.items() if r["time"] == depth]
            if keys:
                per_depth[depth] = {
                    "keys": len(keys),
                    "min_D": str(min(rows[k]["D"] for k in keys)),
                    "entries": sum(1 for k in keys if k in entries),
                }
        results.append(
            {
                "loss_tolerance_delta": str(delta),
                "selected_keys": len(selected),
                "first_entry_keys": len(entries),
                "collapsed_public_histories": len(removed),
                "prepromotion_realization_columns_removed": removed_columns,
                "prepromotion_realization_columns_total": total_columns,
                "fraction_prepromotion_columns_removed": (
                    str(F(removed_columns, total_columns)) if total_columns else "0"
                ),
                "theorem_value_loss_bound": str(delta),
                "per_depth": per_depth,
            }
        )
    return results, len(rows), total_columns


def exact_sanity_cell():
    """T=5, B=2, d=1: check J_lower(root) <= exact free optimum (risk constraint removed)."""
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 20),
        emission1=F(19, 20),
        prior1=F(1, 2),
    )
    config = GameConfig(
        horizon=5, budget=2, delay=1, alpha=F(1), query_cost=F(1, 100), switch_cost=F(1, 10)
    )
    game = CausalSwitchingGame(config, model)
    posterior = enumerate_keys(game)
    values = relaxed_value_table(game)
    root = ((), ())
    w_root, j_root = lower_bound_and_w(game, values, 1, posterior[root])
    game_free = CausalSwitchingGame(config, model)
    solution = game_free.solve()
    free_cost = solution[0][
        "solver_objective"
    ]  # LP objective with the risk constraint inactive (alpha=1)
    return {
        "cell": "T=5,B=2,d=1, transition 1/4, emissions (1/20,19/20), alpha=1 (constraint removed)",
        "J_lower_root": str(j_root),
        "J_lower_root_float": float(j_root),
        "W_root": str(w_root),
        "exact_free_optimum_reference_float": float(free_cost),
        "lower_bound_holds": bool(float(j_root) <= float(free_cost) + 1e-9),
    }


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")
    sanity = exact_sanity_cell()
    if not sanity["lower_bound_holds"]:
        raise SystemExit(
            "Sanity check failed: J_lower exceeds the exact free optimum. Screen stopped."
        )
    config = GameConfig(
        horizon=10,
        budget=4,
        delay=2,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
        max_nodes=200_000,
    )
    model = RegimeModel(
        transition01=F(1, 10),
        transition10=F(1, 10),
        emission0=F(1, 50),
        emission1=F(49, 50),
        prior1=F(1, 2),
    )
    game = CausalSwitchingGame(config, model)
    posterior = enumerate_keys(game)
    values = relaxed_value_table(game)
    results, n_keys, total_columns = screen(game, posterior, values)
    payload = {
        "protocol": PROTOCOL.name,
        "protocol_sha256": digest(PROTOCOL),
        "runner_sha256": digest(Path(__file__)),
        "game_source_sha256": digest(ROOT / "src/shiftlab/dive/causal_switching_game.py"),
        "config": {
            "horizon": 10,
            "budget": 4,
            "delay": 2,
            "alpha": "1/10",
            "query_cost": "1/100",
            "switch_cost": "1/10",
            "transition": "1/10",
            "emissions": ["1/50", "49/50"],
            "prior1": "1/2",
        },
        "exact_pre_promotion_public_histories": n_keys,
        "pre_promotion_realization_columns": total_columns,
        "validity_sanity_T5": sanity,
        "screens": results,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2), flush=True)


if __name__ == "__main__":
    main()
