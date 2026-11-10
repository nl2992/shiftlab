"""Print the reached pre-promotion tree of the certified causal optimum (exact FCG, repaired)."""
import sys
from fractions import Fraction as F
from gamma_lib import make
from shiftlab.paper4.frontier_cuts import frontier_cut_generation, learner_only_game

args = [F(a) for a in sys.argv[1:]]
T = int(args[0])
config, model = make(T, int(args[1]), int(args[2]), *args[3:])
r = frontier_cut_generation(config, model)
pol = r["policy"]
game = learner_only_game(config, model)
print("U", r["U"], "L", float(r["L"]), "rows", r["n_rows"])


def visit(history, outcomes, depth, mass):
    t = len(history) + 1
    if t > T or mass == 0:
        return
    info = game.information(history, outcomes)[1]
    for (a, q), m in zip(game.choices(history), pol(history, outcomes)):
        if not m:
            continue
        print("  " * depth + f"t={t} seen={info} -> a={a} q={q} p={m}")
        if a:
            continue
        nh = history + ((a, q),)
        if q:
            for y in (0, 1):
                visit(nh, outcomes + ((t, y),), depth + 1, mass * m)
        else:
            visit(nh, outcomes, depth + 1, mass * m)


visit((), (), 0, F(1))
