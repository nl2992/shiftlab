import json

from shiftlab.sota_search import g6

res = {}
for frac in (0.10, 0.20):
    for kind in ("fixed", "random", "late_if_good", "late_if_bad"):
        for mode in ("pooled", "disc", "h2c"):
            r = g6.null_and_power(frac, kind, mode)
            res[f"{frac}/{kind}/{mode}"] = r
            print(frac, kind, mode, {k: round(v, 3) for k, v in r.items()}, flush=True)
# hard-budget audit: budget = half the expected number of queries over T=2000
for frac in (0.10, 0.20):
    B = int(0.5 * frac * 2000)
    for rule in ("naive", "stop"):
        for mode in ("disc", "h2c"):
            r = g6.null_and_power(frac, "fixed", mode, budget=B, rule=rule)
            res[f"budget{B}/{frac}/{rule}/{mode}"] = r
            print("budget", B, frac, rule, mode, {k: round(v, 3) for k, v in r.items()}, flush=True)
with open("outputs/h2c_next/g6_delay_budget.json", "w") as fh:
    json.dump(res, fh, indent=2)
