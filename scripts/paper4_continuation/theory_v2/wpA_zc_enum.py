"""Independent brute-force check of Lemma Zc / R: enumerate all deterministic pre-promotion plans
(T,B,d small), compute IID risk and causal (endpoint best-response, null sees pending labels and
public actions) risk; check z-monotone => equal, tape-monotone => equal; count violations."""
import itertools, sys
from fractions import Fraction as F

T, B, d = map(int, sys.argv[1:4])




def info(hist, outs, t):
    return hist, tuple((s, y) for s, y in outs if s + d <= t)


def enumerate_plans():
    # Build list of information states reachable for some plan; enumerate recursively.
    results = []

    def rec(stack, plan):
        # stack: list of pending (hist, outs) nodes to decide
        if not stack:
            results.append(dict(plan))
            return
        hist, outs = stack[0]
        rest = stack[1:]
        t = len(hist) + 1
        if t > T:
            rec(rest, plan)
            return
        key = info(hist, outs, t)
        rem = B - sum(q for _, q in hist)
        if key in plan:
            choices = [plan[key]]
        else:
            choices = [(a, q) for a in (0, 1) for q in ((0, 1) if rem else (0,))]
        for ch in choices:
            new = key not in plan
            if new:
                plan[key] = ch
            a, q = ch
            if a == 1:
                nxt = []
            else:
                nh = hist + (ch,)
                nxt = [(nh, outs + ((t, y),)) for y in (0, 1)] if q else [(nh, outs)]
            rec(nxt + rest, plan)
            if new:
                del plan[key]

    rec([((), ())], {})
    return results


def run(plan, tape_fn):
    """Return (promoted, z-order labels used) running plan with labels given by tape_fn(j, t)."""
    hist, outs, z = (), (), []
    for t in range(1, T + 1):
        a, q = plan[info(hist, outs, t)]
        if a == 1:
            return 1
        if q:
            y = tape_fn(len(z), t)
            z.append(y)
            outs = outs + ((t, y),)
        hist = hist + ((a, q),)
    return 0


def iid_risk(plan):
    return F(sum(run(plan, lambda j, t: tape[t - 1]) for tape in itertools.product((0, 1), repeat=T)), 2 ** T)


def causal_risk(plan):
    def visit(hist, outs):
        t = len(hist) + 1
        if t > T:
            return F(0)
        a, q = plan[info(hist, outs, t)]
        if a:
            return F(1)
        nh = hist + ((a, q),)
        if q:
            z0, z1 = visit(nh, outs + ((t, 0),)), visit(nh, outs + ((t, 1),))
            return max(z0, (z0 + z1) / 2)
        return visit(nh, outs)
    return visit((), ())


def z_event(plan):
    return {zz: run(plan, lambda j, t: zz[j]) for zz in itertools.product((0, 1), repeat=B)}


def tape_event(plan):
    return {tp: run(plan, lambda j, t: tp[t - 1]) for tp in itertools.product((0, 1), repeat=T)}


def monotone(ev, n):
    for x in ev:
        for i in range(n):
            if x[i] == 0:
                y = x[:i] + (1,) + x[i + 1:]
                if ev[x] > ev[y]:
                    return False
    return True


P = enumerate_plans()
stats = dict(plans=len(P), zmono=0, tapemono=0, tape_not_z=0, z_not_tape=0, zmono_gap=0, tape_gap=0, nonmono_gap=0)
for pl in P:
    zm, tm = monotone(z_event(pl), B), monotone(tape_event(pl), T)
    ri, rc = iid_risk(pl), causal_risk(pl)
    stats["zmono"] += zm; stats["tapemono"] += tm
    stats["tape_not_z"] += tm and not zm; stats["z_not_tape"] += zm and not tm
    stats["zmono_gap"] += zm and rc != ri; stats["tape_gap"] += tm and rc != ri
    stats["nonmono_gap"] += (not zm and not tm) and rc != ri
print((T, B, d), stats)
