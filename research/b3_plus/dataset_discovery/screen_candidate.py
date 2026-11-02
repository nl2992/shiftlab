"""Screen ONE candidate dataset under B3_PLUS_SCREENING_PROTOCOL.md (frozen; nothing tuned).

Pipeline: registry entry -> declared delay check -> load -> validate (eligibility, chronology) ->
binarise -> dev-only pair selection + headroom precheck -> [only if it passes] locked-window
evaluation of P0, P1 (hindsight), P2, P3b, P6, P7s at T=2000, B=200, c_q=0.05, c_s=5, 100 seeds,
seed base 20261101 -> SUCCESS rule -> status.

The locked window's losses are computed only after (i) validation passed, (ii) a pair passed the dev
headroom precheck, and (iii) the delay was declared with a justification. A dataset that fails any
stage is recorded and NOT retried with other settings.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "scripts/promising_directions"))

import b3_plus_analysis as ana  # noqa: E402
import b3_plus_experiments as exp  # noqa: E402
import construct_model_pairs as cmp  # noqa: E402
import dataset_sources as ds  # noqa: E402
import registry as reg  # noqa: E402
import validate_stream as vs  # noqa: E402

from b3_plus_policy import run_plus_policies  # noqa: E402

base = exp.base
b1 = base.b1

# --- the single pre-registered configuration (protocol section 2) -------------------------------
T_EP = 2000
BUDGET = 200
CQ = 0.05
CS = 5.0
N_SEEDS = 100
SEED_BASE = 20261101
VARIANTS = ("P0", "P1", "P2", "P3b", "P6", "P7s")
BASE_NAMES = ["P0", "P1", "P2", "P3b", "P6"]


def jsonable(o):
    return b1.jsonable(o)


# --------------------------------------------------------------------------- one episode
def run_episode(l0, l1, u, delay: int, base_err: float) -> tuple[dict, dict]:
    """All six policies on one episode (shared query draws). Returns (variant stats, mechanism)."""
    p = b1.Params(T=T_EP, delay=delay, base_err=base_err, eps=0.05)
    res = base.run_baselines(l0, l1, u, BUDGET, CS, CQ, p, BASE_NAMES)
    a0 = np.repeat(np.asarray(l0, dtype=np.int8)[:, None], u.shape[1], axis=1)
    a1 = np.repeat(np.asarray(l1, dtype=np.int8)[:, None], u.shape[1], axis=1)
    out, objs = run_plus_policies(
        a0, a1, u, BUDGET, CS, CQ, p, [exp._plus_params("P7s")], trace=True, return_objs=True
    )
    res["P7s"] = out["P7s"]
    stats = {}
    for v in VARIANTS:
        s = exp.summarise_variant(res[v], CQ, CS)
        s["max_queries"] = int(np.max(res[v]["queries"]))
        s["max_switches"] = int(np.max(res[v]["switches"]))
        stats[v] = s
    stats["P7s"]["q_issued_mean"] = float(np.nanmean(out["P7s"]["q_issued_mean"]))
    # mechanism for P7s: labels before / after promotion, from the saved acquisition trace
    ask = objs["P7s"].tr["ask"].astype(bool)  # (T, n_seeds)
    if not np.array_equal(ask.sum(0), np.asarray(out["P7s"]["queries"])):
        raise RuntimeError("P7s trace does not reproduce its query counts")
    tp = np.asarray(out["P7s"]["t_prom"], dtype=float)
    promoted = ~np.isnan(tp)
    cut = np.where(promoted, tp, T_EP).astype(int)
    before_mask = np.arange(T_EP)[:, None] < cut[None, :]
    before = (ask & before_mask).sum(0)
    after = (ask & ~before_mask).sum(0)
    mech = {
        "P7s": {
            "promotion_rate": float(promoted.mean()),
            "mean_promotion_time": float(tp[promoted].mean()) if promoted.any() else None,
            "mean_labels_before_promotion": float(before.mean()),
            "mean_labels_after_promotion": float(after.mean()),
            "mean_switches": float(np.mean(out["P7s"]["switches"])),
            "mean_rollbacks": float(np.mean(out["P7s"]["rollbacks"])),
        },
        "P3b": {
            "promotion_rate": stats["P3b"]["promotion_rate"],
            "mean_promotion_time": stats["P3b"]["mean_promotion_time"],
            "mean_labels": stats["P3b"]["mean_labels"],
            "mean_switches": stats["P3b"]["mean_switches"],
            "mean_rollbacks": stats["P3b"]["mean_rollbacks"],
        },
    }
    return stats, mech


# --------------------------------------------------------------------------- summary + SUCCESS rule
def read_rows(path: Path) -> list[dict]:
    rows = exp.read_rows(path)
    return list({r["episode"]: r for r in rows}.values())  # last row wins


def summarise(rows: list[dict], delay: int) -> dict:
    """Paired statistics and the pre-registered SUCCESS conditions, from the JSONL rows only."""
    rows = sorted(rows, key=lambda r: r["episode"])
    k = len(rows)
    per_ep = {v: np.array([r["variants"][v]["mean_cost"] for r in rows]) for v in VARIANTS}
    per_seed = {
        v: np.mean([r["variants"][v]["cost_seeds"] for r in rows], axis=0) for v in VARIANTS
    }
    mean = {v: float(per_ep[v].mean()) for v in VARIANTS}
    rng = np.random.default_rng(ana.BOOT_SEED)

    def diff(a, b):
        d = ana.boot_diff(per_ep[a] - per_ep[b], per_seed[a] - per_seed[b], rng)
        d["frac_episodes_a_below_b"] = float(np.mean(per_ep[a] < per_ep[b]))
        return d

    paired = {
        "P7s_minus_P3b": diff("P7s", "P3b"),
        "P7s_minus_P0": diff("P7s", "P0"),
        "P7s_minus_P6": diff("P7s", "P6"),
        "P7s_minus_P2": diff("P7s", "P2"),
        "P3b_minus_P0": diff("P3b", "P0"),
    }

    def avg(field, v):
        vals = [r["variants"][v][field] for r in rows if r["variants"][v][field] is not None]
        return float(np.mean(vals)) if vals else None

    diag = {
        v: {
            "mean_labels": avg("mean_labels", v),
            "mean_switches": avg("mean_switches", v),
            "mean_rollbacks": avg("mean_rollbacks", v),
            "promotion_rate": avg("promotion_rate", v),
            "mean_promotion_time": avg("mean_promotion_time", v),
            "max_queries_any_episode_seed": int(max(r["variants"][v]["max_queries"] for r in rows)),
        }
        for v in VARIANTS
    }
    mech = {
        key: {
            f: float(np.mean([r["mechanism"][key][f] for r in rows if r["mechanism"][key][f] is not None]))
            if any(r["mechanism"][key][f] is not None for r in rows)
            else None
            for f in rows[0]["mechanism"][key]
        }
        for key in ("P7s", "P3b")
    }
    # decomposition of P7s - P3b (per event, averaged over episodes)
    dec = {
        "d_loss": float(np.mean([r["variants"]["P7s"]["mean_loss"] - r["variants"]["P3b"]["mean_loss"] for r in rows])),
        "d_label_cost": float(CQ * np.mean([r["variants"]["P7s"]["mean_labels"] - r["variants"]["P3b"]["mean_labels"] for r in rows])),
        "d_switch_cost": float(CS * np.mean([r["variants"]["P7s"]["mean_switches"] - r["variants"]["P3b"]["mean_switches"] for r in rows])),
    }
    budget_ok = all(diag[v]["max_queries_any_episode_seed"] <= BUDGET for v in VARIANTS)
    finite = all(np.isfinite(per_ep[v]).all() for v in VARIANTS)
    d1 = paired["P7s_minus_P3b"]
    cond1 = bool(d1["hi"] < 0)
    cond2 = bool(mean["P7s"] < mean["P0"])
    mech_ok = bool(
        finite
        and mech["P7s"]["promotion_rate"] is not None
        and (diag["P7s"]["mean_switches"] > 0 or mean["P7s"] >= mean["P0"])
    )
    return {
        "episodes": k,
        "delay": delay,
        "config": {"T": T_EP, "budget": BUDGET, "cq": CQ, "cs": CS, "n_seeds": N_SEEDS, "seed_base": SEED_BASE},
        "mean_cost": mean,
        "paired": paired,
        "diagnostics": diag,
        "mechanism": mech,
        "p7s_minus_p3b_decomposition_per_episode": dec,
        "conditions": {
            "1_P7s_beats_P3b_CI_below_0": cond1,
            "2_P7s_below_P0": cond2,
            "3_no_leakage_budget_holds_pathwise": bool(budget_ok),
            "4_mechanism_records_complete_and_explicable": mech_ok,
        },
        "low_power": bool(d1["low_power"]),
        "bootstrap_level": d1["bootstrap_level"],
        "finite_costs": bool(finite),
        "p1_note": "P1 is a hindsight reference, not a deployable baseline",
    }


def decide(summary: dict, is_duplicate: bool = False) -> tuple[str, str]:
    """Apply the pre-registered SUCCESS rule; returns (status, reason)."""
    c = summary["conditions"]
    if not summary["finite_costs"] or not c["3_no_leakage_budget_holds_pathwise"]:
        return "USELESS_UNSTABLE", "non-finite costs or the label budget was violated pathwise"
    if not c["1_P7s_beats_P3b_CI_below_0"]:
        d = summary["paired"]["P7s_minus_P3b"]
        return "USELESS_NO_IMPROVEMENT", (
            f"condition 1 failed: P7s - P3b = {d['mean']:+.3f}, 95% CI [{d['lo']:+.3f}, {d['hi']:+.3f}] "
            "does not lie entirely below 0"
        )
    if not c["2_P7s_below_P0"]:
        return "USELESS_NO_HEADROOM", (
            f"condition 2 failed: mean P7s {summary['mean_cost']['P7s']:.2f} >= mean P0 "
            f"{summary['mean_cost']['P0']:.2f}; switching is not worth doing on this stream"
        )
    if not c["4_mechanism_records_complete_and_explicable"]:
        return "USELESS_UNSTABLE", "mechanism records incomplete; benefit not attributable"
    if is_duplicate:
        return "USELESS_DUPLICATE", "passes conditions 1-4 but is not a distinct dataset"
    return "SUCCESS", (
        "conditions 1-5 hold: P7s - P3b CI entirely below 0 and mean P7s < mean P0"
        + (" (LOW-POWER: seed bootstrap, K<5)" if summary["low_power"] else "")
    )


# --------------------------------------------------------------------------- provenance
def git(*args: str) -> str:
    r = subprocess.run(
        ["git", "-C", str(reg.ROOT), *args], capture_output=True, text=True, check=False
    )
    return r.stdout.strip()


def provenance(entry: dict, argv) -> dict:
    sdir = reg.ROOT / "scripts/promising_directions"
    frozen = [
        "b1_certified_switching.py",
        "b3_real_data.py",
        "b3_plus_policy.py",
        "b3_plus_baselines.py",
        "b3_plus_experiments.py",
        "b3_plus_analysis.py",
    ]
    pk = {}
    for p in ("numpy", "scipy", "pandas", "scikit-learn", "river"):
        try:
            pk[p] = metadata.version(p)
        except metadata.PackageNotFoundError:
            pk[p] = None
    return {
        "git_head": git("rev-parse", "HEAD"),
        "git_dirty": bool(git("status", "--porcelain")),
        "frozen_sha256": {f: ds.sha256_file(sdir / f) for f in frozen},
        "screening_protocol_sha256": ds.sha256_file(reg.ROOT / reg.PROTOCOL),
        "raw_files": entry.get("files", {}),
        "python": sys.version,
        "platform": platform.platform(),
        "packages": pk,
        "argv": list(argv),
        "utc": reg.now(),
    }


# --------------------------------------------------------------------------- the pipeline
def _finish(registry, entry, out_dir, status, reason, extra=None, reg_path=reg.REGISTRY_PATH):
    entry["status"], entry["status_reason"] = status, reason
    if extra:
        entry["screening"] = extra
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "status.json").write_text(
        json.dumps(jsonable({"dataset_id": entry["dataset_id"], "status": status, "reason": reason,
                             "timestamps": entry["timestamps"], "screening": extra}), indent=2),
        encoding="utf-8",
    )
    if reg_path is not None:
        reg.save(registry, reg_path)
    return {"dataset_id": entry["dataset_id"], "status": status, "reason": reason, "screening": extra}


def screen(
    dataset_id: str,
    *,
    reg_path: Path | None = reg.REGISTRY_PATH,
    registry: dict | None = None,
    out_root: Path = reg.OUT_ROOT,
    raw=None,
    n_seeds: int = N_SEEDS,
    seed_base: int = SEED_BASE,
    max_episodes: int | None = None,
    resume: bool = True,
    argv=(),
) -> dict:
    """Run the full screening for one dataset. ``raw`` may be injected (tests); else loaded."""
    registry = registry if registry is not None else reg.load(reg_path)
    entry = reg.get(registry, dataset_id)
    save_path = None if max_episodes is not None else reg_path  # debug runs never touch the registry
    out_dir = out_root / dataset_id / ("_debug" if max_episodes is not None else "")
    out_dir.mkdir(parents=True, exist_ok=True)
    delay = reg.declared_delay(entry)  # raises unless declared with justification
    family = entry["family"]
    if family in reg.EXPOSED_FAMILIES:
        return _finish(registry, entry, out_dir, "USELESS_DUPLICATE",
                       f"family '{family}' already in the programme: {reg.EXPOSED_FAMILIES[family]}",
                       reg_path=save_path)
    if any(e["family"] == family and e["status"] == "SUCCESS" and e["dataset_id"] != dataset_id
           for e in registry["candidates"]):
        return _finish(registry, entry, out_dir, "USELESS_DUPLICATE",
                       f"another variant of '{family}' is already a SUCCESS case", reg_path=save_path)
    # ---- load + validate -------------------------------------------------------------------
    if raw is None:
        raw = ds.load(dataset_id, openml_did=entry.get("openml_did"), opts=entry.get("load_options"))
    reg.stamp(entry, "loaded_at_utc")
    report = vs.validate(raw, entry)
    reg.stamp(entry, "validated_at_utc")
    order = report.pop("_order", None)
    (out_dir / "validation.json").write_text(json.dumps(jsonable(report), indent=2), encoding="utf-8")
    if not report["ok"]:
        return _finish(registry, entry, out_dir, report["status"], report["reason"],
                       {"stage": "validation", "validation_verdict": report["order"]["verdict"]},
                       reg_path=save_path)
    # ---- order, binarise, select pair on rows [0, 60%) only ---------------------------------
    n = raw.n
    w = cmp.windows(n)
    y_all = np.asarray(raw.y)[order]
    x_all = vs.take(raw.X, order)
    y01, bin_info = cmp.binarise(y_all, w["n30"])
    if bin_info["rule"] == "degenerate_single_class":
        return _finish(registry, entry, out_dir, "USELESS_DATA_QUALITY",
                       "single class in the training window", {"stage": "binarise"}, reg_path=save_path)
    x60 = x_all[: w["n60"]] if isinstance(x_all, np.ndarray) else x_all.iloc[: w["n60"]]
    sel = cmp.select_pair(x60, y01[: w["n60"]], w, T_EP, CS)
    reg.stamp(entry, "pair_selected_at_utc")
    pair_rec = {
        "windows": w,
        "binarisation": bin_info,
        "positive_rate_dev_window": float(y01[w["n30"] : w["n60"]].mean()),
        "featurizer": sel["featurizer_kind"],
        "options_tried_in_order": sel["tried"],
        "chosen": sel["chosen"],
        "inc_err_dev": sel["inc_err_dev"],
        "selection_inputs": "rows [0, 60%) only",
    }
    (out_dir / "pair.json").write_text(json.dumps(jsonable(pair_rec), indent=2), encoding="utf-8")
    last = sel["tried"][-1]["dev"]
    head = {"stage": "headroom_precheck", "options": [(t["name"], t["dev"]) for t in sel["tried"]]}
    if not sel["passes_headroom"]:
        why = "; ".join(
            f"option {t['name']} ({t['challenger']} {t['train']}): disagree={t['dev']['disagree']:.4f}, "
            f"inc={t['dev']['inc_err_dev']:.4f}, chal={t['dev']['chal_err_dev']:.4f}, "
            f"adv*T={t['dev']['adv_times_T']:.2f} (needs > {CS})"
            for t in sel["tried"]
        )
        head["last_option_dev"] = last
        return _finish(registry, entry, out_dir, "USELESS_NO_HEADROOM",
                       "dev-window headroom precheck failed, locked window never read: " + why,
                       {**head, "binarisation_rule": bin_info["rule"]}, reg_path=save_path)
    # ---- locked window ------------------------------------------------------------------
    # The delay was declared (and stamped) at registration, strictly before this point.
    reg.stamp(entry, "locked_window_read_at_utc")
    if entry["declared_delay"]["declared_at_utc"] > entry["timestamps"]["locked_window_read_at_utc"]:
        raise RuntimeError("delay declared after the locked window was read")
    starts = cmp.episode_starts(n)
    if max_episodes is not None:
        starts = starts[:max_episodes]
    jsonl = out_dir / "episodes.jsonl"
    done = {r["episode"] for r in read_rows(jsonl) if r["n_seeds"] == n_seeds} if resume else set()
    if not resume and jsonl.exists():
        jsonl.unlink()
    t0 = time.time()
    todo = [(i, s) for i, s in enumerate(starts) if i not in done]
    losses = cmp.locked_episode_losses(sel, x_all, y01, [s for _, s in todo], T_EP) if todo else []
    for (i, s), (s2, l0, l1) in zip(todo, losses, strict=True):
        assert s == s2
        u = exp.episode_u(i, n_seeds, T_EP, seed_base)
        stats, mech = run_episode(l0, l1, u, delay, sel["inc_err_dev"])
        row = {
            "dataset_id": dataset_id,
            "episode": i,
            "start": s,
            "delay": delay,
            "budget": BUDGET,
            "cs": CS,
            "cq": CQ,
            "n_seeds": n_seeds,
            "seed_base": seed_base,
            "err_incumbent": float(l0.mean()),
            "err_challenger": float(l1.mean()),
            "disagree": float((l0 != l1).mean()),
            "variants": stats,
            "mechanism": mech,
        }
        exp.append_rows(jsonl, [row])
        print(f"[{dataset_id}] episode {i + 1}/{len(starts)} {time.time() - t0:.0f}s", flush=True)
    rows = read_rows(jsonl)
    summary = summarise(rows, delay)
    summary.update(
        dataset_id=dataset_id,
        pair=sel["chosen"],
        binarisation_rule=bin_info["rule"],
        dev_headroom=sel["tried"][-1]["dev"],
        locked_episode_starts=[r["start"] for r in sorted(rows, key=lambda r: r["episode"])],
        n_seeds=n_seeds,
        episodes_complete=len(rows) == len(cmp.episode_starts(n)),
    )
    if max_episodes is not None:
        summary["debug_truncated"] = True
    status, reason = decide(summary)
    summary["status"], summary["status_reason"] = status, reason
    (out_dir / "summary.json").write_text(json.dumps(jsonable(summary), indent=2), encoding="utf-8")
    (out_dir / "provenance.json").write_text(
        json.dumps(jsonable(provenance(entry, argv)), indent=2), encoding="utf-8"
    )
    reg.stamp(entry, "evaluated_at_utc")
    return _finish(registry, entry, out_dir, status, reason,
                   {"stage": "evaluated", "mean_cost": summary["mean_cost"],
                    "paired": summary["paired"], "episodes": summary["episodes"],
                    "low_power": summary["low_power"]}, reg_path=save_path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset_id")
    ap.add_argument("--max-episodes", type=int, default=None, help="debug only; marks the run truncated")
    ap.add_argument("--no-resume", action="store_true")
    a = ap.parse_args(argv)
    r = screen(a.dataset_id, max_episodes=a.max_episodes, resume=not a.no_resume, argv=sys.argv)
    print(json.dumps({k: r[k] for k in ("dataset_id", "status", "reason")}, indent=2))


if __name__ == "__main__":
    main()
