"""Print the reached pre-promotion part of the IID-optimal policy and marginals for a cell."""
import sys
from fractions import Fraction as F
from gamma_lib import iid_solve, make


def show(T, B, d, t01, t10, e0, e1, prior, c, k, alpha):
    config, model = make(T, B, d, t01, t10, e0, e1, prior, c, k, alpha)
    r = iid_solve(config, model)
    game, pol = r["game"], r["policy"]
    print("lambda", r["lambda_float"], "R_iid", r["R_iid_raw"], "R_causal", r["R_causal_raw"],
          "L_IID", float(r["L_IID"]))

    def visit(history, outcomes, depth):
        t = len(history) + 1
        if t > T:
            return
        probs = pol(history, outcomes)
        info = game.information(history, outcomes)[1]
        for (a, q), m in zip(game.choices(history), probs):
            if not m:
                continue
            print("  " * depth + f"t={t} seen={info} pend={[o for o in outcomes if o not in info]} -> a={a} q={q} p={m}")
            if a:
                continue
            nh = history + ((a, q),)
            if q:
                for y in (0, 1):
                    visit(nh, outcomes + ((t, y),), depth + 1)
            else:
                visit(nh, outcomes, depth + 1)

    visit((), (), 0)


if __name__ == "__main__":
    args = [F(a) for a in sys.argv[1:]]
    show(int(args[0]), int(args[1]), int(args[2]), *args[3:])
