"""Summarize risk-monitor exp_uci outputs.
Usage: python rm_summarize.py <run_dir> [<run_dir> ...] [--merge] [--json out.json]
Per tracker: trials, mean false-alarm rate over psi, mean detection delay (steps vs the point-risk stop), mean valid-psi set size at
t=2500/12500/end. --merge treats all dirs as trial chunks of ONE setting (concatenates trial axes); otherwise one entry per dir."""

import json
import sys

import torch

TRACKERS = ["point_risk", "running_risk", "eprocess", "naive_eprocess", "pmeb_eprocess"]


def summarize_dirs(dirs, merge=False):
    groups = {"merged": dirs} if merge else {d: [d] for d in dirs}
    out = {}
    for name, ds in groups.items():
        res = {}
        for n in TRACKERS:
            try:
                rs = [torch.load(f"{d}/{n}.pt", weights_only=False) for d in ds]
            except Exception as e:  # noqa: BLE001 - missing/corrupt/unpicklable result file; recorded as error
                res[n] = {"error": repr(e)[:80]}
                continue
            fa = torch.cat([r["false_alarms"] for r in rs])
            dd = torch.cat([r["detection_delay"] for r in rs])
            cs = torch.cat([r["psi_cs_size"] for r in rs])
            res[n] = {
                "trials": int(cs.shape[0]),
                "false_alarm_rate": fa.mean().item(),
                "mean_delay": dd[dd >= 0].mean().item() if (dd >= 0).any() else None,
                "cs_size_2500": cs[:, 2500].mean().item(),
                "cs_size_12500": cs[:, 12500].mean().item(),
                "cs_size_end": cs[:, -1].mean().item(),
            }
        out[name] = res
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    jpath = None
    if "--json" in args:
        i = args.index("--json")
        jpath = args[i + 1]
        del args[i : i + 2]
    merge = "--merge" in args
    args = [a for a in args if a != "--merge"]
    out = summarize_dirs(args, merge)
    for name, res in out.items():
        print("##", name)
        for n, r in res.items():
            if "error" in r:
                print(n, "ERR", r["error"])
                continue
            md = "nan" if r["mean_delay"] is None else f"{r['mean_delay']:.1f}"
            print(
                f"{n:15s} trials={r['trials']} false_alarm_rate={r['false_alarm_rate']:.3f} mean_delay={md} "
                f"cs_size@2500={r['cs_size_2500']:.1f} @12500={r['cs_size_12500']:.1f} @end={r['cs_size_end']:.1f}"
            )
    if jpath:
        with open(jpath, "w") as fh:
            json.dump(out, fh, indent=1)
