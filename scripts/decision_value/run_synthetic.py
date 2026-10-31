"""Run one synthetic cell: calibrate thresholds on separate null seeds, run all monitors under CRN with
identical data/acquisition, plus references and oracles; write per-episode records + summary JSON.

Example (smoke, development):
  python scripts/decision_value/run_synthetic.py --family s1 --params '{"p0":0.2,"delta":0.05,"Delta":0.15,"L":400}' \
    --q 0.2 --d 50 --c-s 5 --c-q 0 --n 500 --seed-base 1000 \
    --monitors cusum,page_hinkley,batch,sr_betting,kelly_h2c_inspired --controller permanent
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.decision_value import controllers as C
from shiftlab.decision_value.calibration import calibrate_threshold, null_maxima
from shiftlab.decision_value.contracts import CostContract, FeedbackContract
from shiftlab.decision_value.evaluation import POWER_HORIZONS, run_episode_batch
from shiftlab.decision_value.monitors import monitor_factory, nominal_log_threshold
from shiftlab.decision_value.oracles import oracle_costs
from shiftlab.decision_value.registry import append_run
from shiftlab.decision_value.statistics import paired_bootstrap_diff
from shiftlab.decision_value.synthetic import Family

DEV_SEED_LIMIT = 7_000_000
REFERENCES = ("never", "always", "calendar", "static")


def check_seeds(seeds, confirmation, protocol_hash):
    if max(seeds) >= DEV_SEED_LIMIT and not (confirmation and protocol_hash):
        raise SystemExit(
            f"refusing seed >= {DEV_SEED_LIMIT} without --confirmation and --protocol-hash"
        )


def build_controller(spec, n, T, c_s, mon_factory, thr):
    name, _, arg = spec.partition(":")
    if name == "permanent":
        return C.Permanent(n, T, c_s)
    if name == "hold":
        return C.Hold(n, T, c_s, H=int(arg or 200))
    if name == "reverse":
        return C.Reverse(
            n, T, c_s, rev_factory=mon_factory, rev_threshold=thr
        )  # reuses main threshold
    if name == "never":
        return C.NeverSwitch(n, T, c_s)
    if name == "always":
        return C.AlwaysChallenger(n, T, c_s)
    if name == "calendar":
        return C.CalendarBatch(n, T, c_s, K=int(arg or 200))
    if name == "static":
        return C.StaticThreshold(n, T, c_s, W=int(arg or 100))
    raise SystemExit(f"unknown controller {spec}")


def summarise(rec, ref_cost, oracle, is_monitor, B, seed):
    f = lambda v: float(np.mean(v))
    out = {
        "cost_exp": f(rec["cost_exp"]),
        "cost_exp_se": float(np.std(rec["cost_exp"], ddof=1) / np.sqrt(len(rec["cost_exp"]))),
        "cost_real": f(rec["cost_real"]),
        "N_s": f(rec["N_s"]),
        "N_q": f(rec["N_q"]),
        "switch_prob": f(~np.isnan(rec["first_switch"])),
        "harm_before_switch": f(rec["harm_before_switch"]),
        "t_chal_in_opp": f(rec["t_chal_in_opp"]),
        "t_chal_out_opp": f(rec["t_chal_out_opp"]),
    }
    if is_monitor:
        out["detection"] = {
            "power_T": f(rec["power_T"]),
            "power_opp": f(rec["power_opp"]),
            **{f"power_h{h}": f(rec[f"power_h{h}"]) for h in POWER_HORIZONS},
            "delay_censored_mean": f(rec["delay_cens"]),
            "delay_median_detected": float(np.nanmedian(rec["delay"]))
            if np.isfinite(rec["delay"]).any()
            else None,
            "false_alarm_pre_tau": f(rec["false_alarm_pre_tau"]),
            "any_alarm": f(rec["any_alarm"]),
        }
    out["paired_diff_vs_ref_cost_exp"] = paired_bootstrap_diff(
        rec["cost_exp"], ref_cost, B=B, seed=seed
    )
    out["gap_to_dynamic_oracle"] = f(rec["cost_exp"] - oracle["dynamic_exp"])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--family", required=True, choices=["s1", "s2", "s3"])
    ap.add_argument(
        "--params", default="{}", help="JSON of factor values overriding family defaults"
    )
    ap.add_argument("--q", type=float, default=0.2)
    ap.add_argument("--d", type=int, default=0)
    ap.add_argument("--c-q", type=float, default=0.0)
    ap.add_argument("--c-s", type=float, default=0.0)
    ap.add_argument(
        "--monitors",
        default="cusum,page_hinkley,batch,sr_betting,kelly_h2c_inspired",
        help="comma list; suffix @nominal uses the 1/alpha log-threshold (e-detectors only)",
    )
    ap.add_argument("--target", default="paired", choices=["paired", "incumbent"])
    ap.add_argument("--controller", default="permanent", help="permanent | hold:H | reverse")
    ap.add_argument("--references", default=",".join(REFERENCES))
    ap.add_argument(
        "--reference", default="never", help="declared reference for paired differences"
    )
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--seed-base", type=int, default=1000)
    ap.add_argument("--cal-seed-base", type=int, default=5_000_000)
    ap.add_argument("--n-cal", type=int, default=2000)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--bootstrap", type=int, default=10_000)
    ap.add_argument("--out-dir", default=str(ROOT / "outputs" / "decision_value" / "development"))
    ap.add_argument("--confirmation", action="store_true")
    ap.add_argument("--protocol-hash", default=None)
    ap.add_argument("--monitor-hp", default="{}", help='JSON {"cusum":{"k":0.02}, ...}')
    args = ap.parse_args(argv)
    check_seeds(
        [args.seed_base, args.cal_seed_base, args.cal_seed_base + 1],
        args.confirmation,
        args.protocol_hash,
    )

    t0 = time.time()
    fam = Family(args.family, json.loads(args.params))
    fb, cost = FeedbackContract(args.q, args.d), CostContract(args.c_q, args.c_s)
    n, T = args.n, fam.T
    batch, truth = fam.generate(args.seed_base, n, fb)
    orc = oracle_costs(batch, truth, cost)
    hps = json.loads(args.monitor_hp)
    ref_name = args.reference
    records, specs, thresholds, summary = {}, {}, {}, {"methods": {}}
    trace_idx = tuple(range(min(3, n)))

    for mspec in [m for m in args.monitors.split(",") if m]:
        name, _, mode = mspec.partition("@")
        fac = monitor_factory(name, target=args.target, **hps.get(name, {}))
        if mode == "nominal":
            thr = nominal_log_threshold(args.alpha)
        else:
            thr = calibrate_threshold(fac, fam, fb, args.alpha, args.n_cal, args.cal_seed_base)
        fresh = null_maxima(fac, fam, fb, args.n_cal, args.cal_seed_base + 1)
        mon = fac(n)
        mon.threshold = thr
        ctrl = build_controller(args.controller, n, T, cost.c_s, fac, thr)
        records[mspec] = run_episode_batch(batch, truth, fb, cost, mon, ctrl, trace_idx)
        specs[mspec] = {
            **mon.spec(),
            "threshold": thr,
            "threshold_mode": mode or "calibrated",
            "controller": ctrl.spec(),
            "null_alarm_rate_fresh_seed": float((fresh > thr).mean()),
        }
        thresholds[mspec] = thr

    for r in [r for r in args.references.split(",") if r]:
        ctrl = build_controller(r, n, T, cost.c_s, None, np.inf)
        records[r] = run_episode_batch(batch, truth, fb, cost, None, ctrl, trace_idx)
        specs[r] = {"reference": True, "controller": ctrl.spec()}

    if ref_name not in records:
        raise SystemExit(f"declared reference {ref_name} not among methods")
    ref_cost = records[ref_name]["cost_exp"]
    for k, rec in records.items():
        summary["methods"][k] = {
            **specs[k],
            **summarise(rec, ref_cost, orc, k in thresholds, args.bootstrap, 7),
        }
        summary["methods"][k]["traces"] = rec["_traces"]
    mean = lambda v: float(np.mean(v))
    summary["oracles"] = {k: mean(v) for k, v in orc.items()}
    summary["headroom_H_T"] = {
        "exp": mean(orc["headroom_exp"]),
        "real": mean(orc["headroom_real"]),
        "vs_static_exp": mean(orc["headroom_static_exp"]),
        "min_exp": float(np.min(orc["headroom_exp"])),
    }
    summary["declared_reference"] = ref_name

    run_id = f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{args.family}_n{n}_s{args.seed_base}"
    out = Path(args.out_dir) / run_id
    out.mkdir(parents=True, exist_ok=True)
    df = pd.concat(
        [
            pd.DataFrame({k: v for k, v in rec.items() if k != "_traces"}).assign(
                method=m, episode=np.arange(n)
            )
            for m, rec in records.items()
        ],
        ignore_index=True,
    )
    try:
        df.to_parquet(out / "episodes.parquet")
        ep_path = out / "episodes.parquet"
    except ImportError:  # pyarrow missing
        ep_path = out / "episodes.csv.gz"
        df.to_csv(ep_path, index=False)
    config = {k: v for k, v in vars(args).items()}
    config.update(params=fam.params, label="smoke, development" if n <= 500 else "development")
    summary["config"] = config
    summary["stage"] = "confirmation" if args.confirmation else "development"
    with open(out / "summary.json", "w", encoding="utf8") as f:
        json.dump(
            summary, f, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)
        )
    runtime = time.time() - t0
    seeds = {
        "eval": args.seed_base,
        "calibration": args.cal_seed_base,
        "calibration_check": args.cal_seed_base + 1,
    }
    append_run(
        run_id, config, seeds, n, runtime, [ep_path, out / "summary.json"], args.confirmation
    )
    print(f"run_id={run_id} runtime={runtime:.1f}s out={out}")
    return out, summary


if __name__ == "__main__":
    main()
