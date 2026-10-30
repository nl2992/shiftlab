"""Failure Atlas v1 loop (R4 exploratory discovery; no novelty, theorem or efficacy claim).

Protocol: docs/failure_atlas_v1_protocol.md. Resumable; run from the repository root:

    .venv/Scripts/python scripts/run_failure_atlas_loop.py --smoke --out outputs/failure_atlas_v1_smoke
    .venv/Scripts/python scripts/run_failure_atlas_loop.py            # full run (not launched by default tooling)

State: ``<out>/state.json``. Append-only archive: ``<out>/archive.jsonl`` (one row per evaluation,
with git head, dirty flag and source sha256). Stages 5-6 import ``shiftlab.dive.atlas_components``
lazily (override with env ATLAS_COMPONENTS_MODULE) and assume this contract:
``propose_candidates(axis) -> list[CandidateSpec]``, ``validate_spec(spec) -> (ok, reasons)``,
``build_candidate(spec) -> Method`` and ``ablation_of(spec, slot)`` (hypothesised slot swapped for its
default); a spec exposes ``spec_id``, ``focus``, ``hypothesis`` and ``is_safety_gated``.
Confirmation seeds are never touched by this script.
"""

from __future__ import annotations

import os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")  # one BLAS thread per worker process

import argparse
import hashlib
import importlib
import json
import random
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.dive import failure_atlas as fa
from shiftlab.dive.switching_explore import paired_ci

COMPONENTS_MODULE = os.environ.get("ATLAS_COMPONENTS_MODULE", "shiftlab.dive.atlas_components")
SOURCES = (
    "src/shiftlab/dive/failure_atlas.py",
    "src/shiftlab/dive/atlas_components.py",
    "src/shiftlab/dive/switching_explore.py",
    "src/shiftlab/dive/eprocess.py",
    "scripts/run_failure_atlas_loop.py",
)


class StopLoop(Exception):
    """A resource ceiling was reached; state is saved and the summary is written."""


# ------------------------------------------------------------------ worker functions (top level)


def isolate_worker(task: tuple) -> dict:
    cl = fa._isolate_task(task)
    cl["_runs"] = len(task[1]) * (len(fa.ALL_METHODS) + 3) * 2  # cell + null twin
    return cl


def null_fp_worker(task: tuple) -> dict:
    """ref_family any-FP count on one null twin over many seeds at one kappa."""
    twin, seed_list, kappa = task
    k = fa.null_fp_by_kappa((twin, seed_list, (kappa,)))[kappa]
    return {"twin": twin.cell_id, "k": int(k), "n": len(seed_list), "_runs": len(seed_list)}


def spec_info(spec) -> dict:
    return {
        "id": spec.spec_id,
        "slots": [spec.acquisition, spec.evidence, spec.memory, spec.decision],
        "focus": spec.focus,
        "gated": bool(spec.is_safety_gated),
        "hypothesis": spec.hypothesis,
    }


def mech_worker(task: tuple) -> dict:
    """Evaluate one mechanism candidate in a cell and on its null twin."""
    cell, spec, seed_list, kappa, ablate = task
    comp = importlib.import_module(COMPONENTS_MODULE)
    if ablate:
        try:
            spec = comp.ablation_of(spec, spec.focus)
        except ValueError as exc:  # focus slot already default: ablation is not defined
            return {"error": f"ablation unavailable: {exc}", "name": "ablated", "_runs": 0}
    name = "cand:" + spec.spec_id + ("|ablated" if ablate else "")
    try:
        res = fa.evaluate_cell(
            cell,
            seed_list,
            methods=(),
            refs=(),
            kappa=kappa,
            extra_methods={name: lambda: comp.build_candidate(spec)},
        )
    except Exception as exc:  # noqa: BLE001 - a rejected candidate is archived, not hidden
        return {"error": f"{type(exc).__name__}: {exc}", "name": name}
    m, nm = res["methods"][name], res["null"]["methods"][name]
    return {
        "_runs": 2 * len(seed_list),
        "name": name,
        "spec": spec_info(spec),
        "cost": m["cost"],
        "fp_null": nm["fp"],
        "queries": m["queries"],
        "switches": m["switches"],
    }


# ------------------------------------------------------------------ helpers


def git_info() -> dict:
    def g(*a):
        return subprocess.run(
            ["git", *a], cwd=ROOT, capture_output=True, text=True, check=False
        ).stdout.strip()

    return {
        "head": g("rev-parse", "HEAD"),
        "dirty": bool(g("status", "--porcelain")),
        "src_sha256": {
            Path(f).name: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in SOURCES
        },
    }


def compact(res: dict) -> dict:
    out = {k: res[k] for k in ("cell_id", "T", "B", "alpha", "kappa", "seeds")}
    out["methods"] = {
        m: {k: [round(float(x), 6) for x in v] for k, v in rec.items() if k != "promotions"}
        for m, rec in res["methods"].items()
    }
    out["null"] = None
    return out


def md_table(header: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    return "\n".join(out)


def fmt_ci(mean: float, ci) -> str:
    return f"{mean:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}]"


# ------------------------------------------------------------------ runner


class Runner:
    def __init__(self, args, pool):
        self.args = args
        self.pool = pool
        self.out = Path(args.out)
        self.out.mkdir(parents=True, exist_ok=True)
        self.state_path = self.out / "state.json"
        self.archive_path = self.out / "archive.jsonl"
        self.git = git_info()
        self.T = 200 if args.smoke else 1000
        self.cells = {c.cell_id: c for c in fa.all_cells(self.T)}
        self.state = {
            "stage": 0,
            "kappa": fa.KAPPA_DEFAULT,
            "calibration": None,
            "sample": [],
            "refine": [],
            "candidates": [],
            "survivors": [],
            "failures": [],
            "completed": {},
            "runs": 0,
            "elapsed_s": 0.0,
            "stopped": None,
            "mechanism": {},
            "smoke": bool(args.smoke),
        }
        if self.state_path.exists():
            self.state.update(json.loads(self.state_path.read_text(encoding="utf-8")))
        self.rows: dict[str, dict] = {}
        if self.archive_path.exists():
            for line in self.archive_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    self.rows[row["key"]] = row
        self.t0 = time.time()
        self.elapsed0 = self.state["elapsed_s"]
        reuse = getattr(args, "reuse_cells_from", None)
        if reuse and not self.state["sample"]:  # same sampled cells as a previous cycle
            prev = json.loads(Path(reuse).read_text(encoding="utf-8"))
            self.state["sample"], self.state["refine"] = prev["sample"], prev["refine"]
            self.state["reused_cells_from"] = str(reuse)

    def mark(self, name: str) -> None:
        """Record cumulative elapsed seconds at the end of a stage."""
        self.state.setdefault("stage_times", {})[name] = self.elapsed0 + time.time() - self.t0
        self.save()

    def prior_classes(self, prev_dir: str) -> dict[str, dict]:
        """Recompute the previous cycle's per-cell classes from its archive (same classify_cell)."""
        d = Path(prev_dir)
        pst = json.loads((d / "state.json").read_text(encoding="utf-8"))
        prows = {}
        for line in (d / "archive.jsonl").read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                prows[r["key"]] = r
        kappa, tag = pst["kappa"], self._tag(fa.seeds("discovery", self.args.n_seeds))
        out = {}
        for cid in [*pst["sample"], *pst["refine"]]:
            cell = self.cells[cid]
            res = json.loads(json.dumps(prows[f"cell|{cid}|{tag}|k{kappa}"]["payload"]))
            twin = cell.null_twin().cell_id
            res["null"] = json.loads(json.dumps(prows[f"null|{twin}|{tag}|k{kappa}"]["payload"]))
            nf = pst["null_fp"][f"{twin}|k{kappa}"]
            res["null"]["methods"]["ref_family"]["fp"] = [1] * nf["k"] + [0] * (nf["n"] - nf["k"])
            out[cid] = fa.classify_cell(res)
        return out

    # -- persistence ---------------------------------------------------------
    def save(self) -> None:
        self.state["elapsed_s"] = self.elapsed0 + time.time() - self.t0
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, indent=1, default=float), encoding="utf-8")
        tmp.replace(self.state_path)

    def archive(self, key: str, kind: str, stage: str, payload: dict, runs: int) -> None:
        row = {
            "key": key,
            "kind": kind,
            "stage": stage,
            "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "git_head": self.git["head"],
            "git_dirty": self.git["dirty"],
            "src_sha256": self.git["src_sha256"],
            "payload": payload,
        }
        with open(self.archive_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, default=float) + "\n")
        self.rows[key] = row
        self.state["runs"] += runs
        self.state["completed"].setdefault(kind, []).append(key)

    def check_ceiling(self) -> None:
        hours = (self.elapsed0 + time.time() - self.t0) / 3600
        if hours >= self.args.max_hours:
            raise StopLoop(f"max-hours {self.args.max_hours} reached")
        if self.state["runs"] >= self.args.max_runs:
            raise StopLoop(f"max-runs {self.args.max_runs} reached")

    # -- generic task execution ------------------------------------------------
    def run_items(self, fn, items: list[tuple], stage: str) -> None:
        """items: (key, kind, task). Skips keys already archived (resume)."""
        pending = [it for it in items if it[0] not in self.rows]
        step = max(1, self.args.workers * 3)
        for i in range(0, len(pending), step):
            self.check_ceiling()
            futs = {self.pool.submit(fn, it[2]): it for it in pending[i : i + step]}
            for f in as_completed(futs):
                key, kind, _ = futs[f]
                res = f.result()
                if isinstance(res, dict) and "methods" in res:
                    runs = sum(len(v["cost"]) for v in res["methods"].values())
                    self.archive(key, kind, stage, compact(res), runs)
                else:
                    self.archive(key, kind, stage, res, int(res.get("_runs", 0)))
            self.save()
            print(f"  [{stage}] {min(i + step, len(pending))}/{len(pending)} tasks", flush=True)

    # -- evaluation of cells with their null twins -------------------------------
    @staticmethod
    def _tag(seed_list) -> str:
        return f"{seed_list[0]}+{len(seed_list)}"

    def ensure_null_fp(self, cells: list[fa.CellSpec]) -> None:
        """100-seed ref_family FP estimate per distinct null twin (dedicated, disjoint seeds)."""
        kappa = self.state["kappa"]
        sd = fa.seeds("discovery", self.args.n_null_seeds, offset=5000)
        twins = {c.null_twin().cell_id: c.null_twin() for c in cells}
        items = [
            (f"nullfp|{tid}|{self._tag(sd)}|k{kappa}", "nullfp", (tw, tuple(sd), kappa))
            for tid, tw in twins.items()
        ]
        self.run_items(null_fp_worker, items, "null_fp")
        cache = self.state.setdefault("null_fp", {})
        for key, it in zip([i[0] for i in items], twins, strict=True):
            r = self.rows[key]["payload"]
            cache[f"{it}|k{kappa}"] = {"k": r["k"], "n": r["n"], "seeds": self._tag(sd)}

    def evaluate(
        self, cells: list[fa.CellSpec], seed_list, stage: str, methods=None
    ) -> list[tuple]:
        methods = tuple(fa.ALL_METHODS if methods is None else methods)
        kappa, tag = self.state["kappa"], self._tag(seed_list)
        twins = {c.null_twin().cell_id: c.null_twin() for c in cells}
        nulls = [
            (f"null|{tid}|{tag}|k{kappa}", "null", (tw, tuple(seed_list), kappa, methods))
            for tid, tw in twins.items()
        ]
        self.run_items(fa.evaluate_null_task, nulls, stage)
        plain = [
            (f"cell|{c.cell_id}|{tag}|k{kappa}", "cell", (c, tuple(seed_list), kappa, methods))
            for c in cells
        ]
        self.run_items(fa.evaluate_plain_task, plain, stage)
        self.ensure_null_fp(cells)
        return [self.classified(c, seed_list) for c in cells]

    def classified(self, cell: fa.CellSpec, seed_list) -> tuple:
        kappa, tag = self.state["kappa"], self._tag(seed_list)
        res = json.loads(json.dumps(self.rows[f"cell|{cell.cell_id}|{tag}|k{kappa}"]["payload"]))
        res["null"] = json.loads(
            json.dumps(self.rows[f"null|{cell.null_twin().cell_id}|{tag}|k{kappa}"]["payload"])
        )
        # per-cell reference_unsafe check uses the dedicated 100-seed twin estimate (protocol fix 1)
        nf = self.state["null_fp"][f"{cell.null_twin().cell_id}|k{kappa}"]
        res["null"]["methods"]["ref_family"]["fp"] = [1] * nf["k"] + [0] * (nf["n"] - nf["k"])
        return cell, res, fa.classify_cell(res)

    # -- stages --------------------------------------------------------------------
    def stage0_registry(self) -> None:
        self.state["registry"] = fa.BASELINE_REGISTRY
        self.state["stage"] = max(self.state["stage"], 1)
        self.save()

    def stage1_discover(self) -> None:
        a = self.args
        ids = sorted(self.cells)
        if not self.state["sample"]:
            random.Random(a.sample_seed).shuffle(ids)
            self.state["sample"] = ids[: a.n_sample]
            self.save()
        sample = [self.cells[i] for i in self.state["sample"]]
        disc = fa.seeds("discovery", a.n_seeds)
        if self.state["calibration"] is None:
            print("[stage1] calibrating kappa on discovery null twins", flush=True)
            kappa, info = fa.calibrate_family_kappa(sample, disc, alpha=0.1, mapper=self.pool.map)
            self.state["kappa"] = kappa
            self.state["calibration"] = {
                "kappa": kappa,
                "calibrated": info["calibrated"],
                "n_twins": info["n_twins"],
                "table": {str(k): v for k, v in info["table"].items()},
                "seeds": [disc[0], disc[-1]],
            }
            self.save()
        print(f"[stage1] kappa = {self.state['kappa']}", flush=True)
        first = self.evaluate(sample, disc, "discover")
        fails = [c for c, _, cl in first if cl["shared_failure"]]
        # adaptive refinement near shared failures (not yet evaluated)
        if not self.state["refine"] and fails:
            seen = set(self.state["sample"])
            near = sorted(
                {
                    n.cell_id
                    for c in fails
                    for n in fa.neighbours(c)
                    if n.cell_id not in seen and n.cell_id in self.cells
                }
            )
            random.Random(a.sample_seed + 1).shuffle(near)
            self.state["refine"] = near[: a.n_refine]
            self.save()
        refine = [self.cells[i] for i in self.state["refine"]]
        second = self.evaluate(refine, disc, "refine") if refine else []
        self.disc = first + second
        self.state["stage"] = max(self.state["stage"], 2)
        self.save()

    def rank_candidates(self) -> list[str]:
        a = self.args
        fail_ids = {c.cell_id for c, _, cl in self.disc if cl["shared_failure"]}
        scored = []
        for c, _, cl in self.disc:
            if cl["shared_failure"]:
                nn = sum(n.cell_id in fail_ids for n in fa.neighbours(c))
                scored.append((cl["severity"] * (1 + nn), c.cell_id))
        scored.sort(reverse=True)
        top = [cid for _, cid in scored[: a.top_k]]
        self.state["smoke_forced"] = False
        if not top and a.smoke:  # exercise downstream stages only; flagged everywhere
            pool = sorted(self.disc, key=lambda x: -x[2]["H"])
            top = [c.cell_id for c, _, cl in pool[:2]]
            self.state["smoke_forced"] = True
        return top

    def stage2_reproduce(self) -> None:
        a = self.args
        self.state["candidates"] = self.rank_candidates()
        self.save()
        cands = [self.cells[i] for i in self.state["candidates"]]
        print(f"[stage2] reproducing {len(cands)} candidate failure cells", flush=True)
        seeds_ = fa.seeds("discovery", a.n_reproduce, offset=1000)
        rep = self.evaluate(cands, seeds_, "reproduce") if cands else []
        self.rep = rep
        forced = self.state.get("smoke_forced", False)
        # stage 3 (avoidability) is the information-limit test inside classify_cell
        self.state["survivors"] = [
            c.cell_id
            for c, _, cl in rep
            if (cl["shared_failure"] and not cl["info_limited"]) or forced
        ]
        self.state["failures"] = [
            {
                "cell_id": c.cell_id,
                "label": cl["label"],
                "severity": cl["severity"],
                "H": cl["H"],
                "H_ci": cl["H_ci"],
                "best_safe": cl["best_safe"],
                "gaps": cl["gaps"],
                "info_gap": cl["info_gap"],
                "fp": cl["ref_family_null_fp"],
                "smoke_forced": forced,
            }
            for c, _, cl in rep
        ]
        self.state["stage"] = max(self.state["stage"], 4)
        self.save()
        if not self.state["survivors"]:
            raise StopLoop("no failure survives stage 2/3")

    def stage2b_diagnose(self) -> None:
        """Descriptive decomposition on every reproduced survivor (evaluator-side, Amendment 1)."""
        a = self.args
        surv = [self.cells[i] for i in self.state["survivors"]]
        sd = fa.seeds("discovery", a.n_diag, offset=3000)
        kappa, tag = self.state["kappa"], self._tag(sd)
        items = [(f"diag|{c.cell_id}|{tag}|k{kappa}", "diag", (c, tuple(sd), kappa)) for c in surv]
        self.run_items(fa.diagnose_task, items, "diagnose")
        self.state["diagnostics"] = {
            c.cell_id: self.rows[it[0]]["payload"] for c, it in zip(surv, items, strict=True)
        }
        self.state["stage"] = max(self.state["stage"], 3)
        self.save()

    def stage4_isolate(self) -> None:
        a = self.args
        surv = [self.cells[i] for i in self.state["survivors"]]
        seeds_ = fa.seeds("discovery", a.n_seeds, offset=2000)
        kappa, tag = self.state["kappa"], self._tag(seeds_)
        items = []
        for c in surv:
            for ax in fa.AXES:
                if getattr(c, ax) != fa.EASIEST[ax]:
                    mc = c.easiest(ax)
                    items.append(
                        (
                            f"iso|{c.cell_id}|{ax}|{tag}|k{kappa}",
                            "iso",
                            (mc, tuple(seeds_), kappa, None),
                        )
                    )
        self.run_items(isolate_worker, items, "isolate")
        mech = {}
        for c in surv:
            iso = {}
            for ax in fa.AXES:
                row = self.rows.get(f"iso|{c.cell_id}|{ax}|{tag}|k{kappa}")
                if row is not None:
                    cl = row["payload"]
                    cl["removes_failure"] = bool(not cl["H_ci"][0] > fa.MATERIAL)
                    iso[ax] = cl
            removing = [ax for ax, cl in iso.items() if cl["removes_failure"]]
            mech[c.cell_id] = {"isolation": iso, "axes_removing": removing}
        self.state["mechanism"] = mech
        self.state["stage"] = max(self.state["stage"], 5)
        self.save()

    def _components(self):
        try:
            return importlib.import_module(COMPONENTS_MODULE)
        except Exception as exc:  # noqa: BLE001
            msg = f"stage 5/6 skipped: cannot import {COMPONENTS_MODULE} ({type(exc).__name__}: {exc})"
            print(f"[stage5] {msg}", flush=True)
            self.state["stage56_status"] = msg
            return None

    def _baseline_costs(self, cell, seed_list, stage):
        """Gated baselines + references on the given seeds (cached through the archive)."""
        res = self.evaluate([cell], seed_list, stage)[0]
        return res[2], res[1]

    def stage5_6_mechanism(self) -> None:
        comp = self._components()
        if comp is None:
            return
        a = self.args
        kappa = self.state["kappa"]
        dev = fa.seeds("development", a.n_seeds)
        val = fa.seeds("mechanism", a.n_seeds, offset=a.val_offset)
        for cid in self.state["survivors"]:
            cell = self.cells[cid]
            info = self.state["mechanism"][cid]
            rem = info["axes_removing"]
            # Amendment 1: onset-axis proposals when onset removes the failure; the generic
            # fallback ("unknown") when no single axis removes it
            axis = "onset" if "onset" in rem else (rem[0] if rem else "unknown")
            try:
                proposed = list(comp.propose_candidates(axis))
            except Exception as exc:  # noqa: BLE001
                info["stage5"] = f"propose_candidates failed: {type(exc).__name__}: {exc}"
                continue
            specs, rejected = [], []
            for sp in proposed:  # every proposal is archived, including rejections
                ok, why = comp.validate_spec(sp)
                (specs if ok else rejected).append(sp if ok else (sp, why))
            for sp, why in rejected:
                self.archive(
                    f"mechrej|{cid}|{sp.spec_id}",
                    "mechrej",
                    "mechanism_search",
                    {"spec": spec_info(sp), "reasons": why},
                    0,
                )
            base_cl, base_res = self._baseline_costs(cell, dev, "mech_dev")
            fam = float(np.mean(base_res["methods"]["ref_family"]["cost"]))
            safe = base_cl["mean_cost"][base_cl["best_safe"]]
            items = [
                (
                    f"mech|{cid}|{sp.spec_id}|{self._tag(dev)}|k{kappa}",
                    "mech",
                    (cell, sp, tuple(dev), kappa, False),
                )
                for sp in specs
            ]
            self.run_items(mech_worker, items, "mechanism_search")
            cand_rows = []
            for (key, _, _), sp in zip(items, specs, strict=True):
                r = self.rows[key]["payload"]
                if "error" in r:
                    cand_rows.append({"id": sp.spec_id, "error": r["error"]})
                    continue
                cost = float(np.mean(r["cost"]))
                closure = (safe - cost) / (safe - fam) if safe > fam else float("nan")
                cand_rows.append(
                    {
                        "id": sp.spec_id,
                        "focus": sp.focus,
                        "gated": bool(sp.is_safety_gated),
                        "cost": cost,
                        "gap_closure": closure,
                        "fp_null": float(np.mean(r["fp_null"])),
                    }
                )
            info["stage5"] = {
                "n_proposed": len(proposed),
                "n_invalid": len(rejected),
                "run": cand_rows,
            }
            ok = [
                r
                for r in cand_rows
                if "error" not in r and r["gated"] and r["fp_null"] <= cell.alpha + fa.FP_SLACK
            ]
            if not ok:
                info["stage6"] = "no safety-gated candidate passed the null-twin screen"
                continue
            best = min(ok, key=lambda r: r["cost"])
            spec = next(sp for sp in specs if sp.spec_id == best["id"])
            info["stage6"] = self._validate(comp, cell, spec, axis, val, kappa)
        self.state["stage"] = max(self.state["stage"], 7)
        self.save()

    def _log_val_use(self, cell, spec) -> None:
        """Log one validation-seed use per (cell, spec_id) after a fresh, completed computation."""
        log = self.state.setdefault("val_log", {})
        log.setdefault(f"{cell.cell_id}|{spec.spec_id}", []).append(time.strftime("%H:%M:%S"))

    def _cand_eval(self, comp, cell, spec, val, kappa, with_ablation):
        tag = self._tag(val)
        variants = {"candidate": False}
        if with_ablation and spec.focus is not None:
            variants["ablated"] = True
        items = [
            (
                f"mechval|{cell.cell_id}|{spec.spec_id}|{v}|{tag}|k{kappa}",
                "mechval",
                (cell, spec, tuple(val), kappa, abl),
            )
            for v, abl in variants.items()
        ]
        fresh = not all(i[0] in self.rows for i in items)
        self.run_items(mech_worker, items, "mechanism_validation")
        if fresh:
            self._log_val_use(cell, spec)
        return {v: self.rows[i[0]]["payload"] for i, v in zip(items, variants, strict=True)}

    def _neighbour_check(self, comp, cell, spec, axis, val, kappa) -> list[dict]:
        cand = [n for n in fa.neighbours(cell) if n.cell_id in self.cells]
        on_axis = [n for n in cand if getattr(n, axis, None) != getattr(cell, axis, None)]
        chosen = (on_axis or cand)[:2]
        out = []
        for n in chosen:
            bcl, bres = self._baseline_costs(n, val, "mech_val_neighbour")
            r = self._cand_eval(comp, n, spec, val, kappa, False)["candidate"]
            if "cost" not in r:
                out.append({"cell": n.cell_id, "error": r.get("error")})
                continue
            cc = np.asarray(r["cost"], dtype=float)
            safe = np.asarray(bres["methods"][bcl["best_safe"]]["cost"], dtype=float)
            fam = np.asarray(bres["methods"]["ref_family"]["cost"], dtype=float)
            m, lo, hi = paired_ci(cc - safe)
            gm, glo, ghi = paired_ci(cc - fam)
            out.append(
                {
                    "cell": n.cell_id,
                    "best_safe": bcl["best_safe"],
                    "cand_minus_best_safe": [m, lo, hi],
                    "cand_minus_R_family": [gm, glo, ghi],
                    "null_fp": float(np.mean(r["fp_null"])),
                    "no_worse_than_best_safe": bool(hi < fa.MATERIAL),
                }
            )
        return out

    def _validate(self, comp, cell, spec, axis, val, kappa) -> dict:
        tag = self._tag(val)
        base_cl, base_res = self._baseline_costs(cell, val, "mech_val")
        fam = float(np.mean(base_res["methods"]["ref_family"]["cost"]))
        safe = base_cl["mean_cost"][base_cl["best_safe"]]
        out = {"candidate": spec.spec_id, "seeds": f"mechanism {tag}"}
        res = self._cand_eval(comp, cell, spec, val, kappa, True)
        costs = {
            v: (float(np.mean(r["cost"])), float(np.mean(r["fp_null"]))) if "cost" in r else None
            for v, r in res.items()
        }
        if costs["candidate"] is None:
            out["repair"] = False
            out["reason"] = "candidate errored"
            return out
        cost, fp = costs["candidate"]
        closure = (safe - cost) / (safe - fam) if safe > fam else float("nan")
        out.update({"cost": cost, "gap_closure": closure, "null_fp": fp})
        c_ok = bool(closure >= 0.5)
        fp_ok = bool(fp <= cell.alpha + fa.FP_SLACK)
        if costs.get("ablated") is not None:
            gain, gain_abl = safe - cost, safe - costs["ablated"][0]
            abl_ok = bool(gain > 0 and gain_abl <= 0.5 * gain)
            out["ablated_cost"] = costs["ablated"][0]
        else:
            abl_ok = None
        nb = self._neighbour_check(comp, cell, spec, axis, val, kappa)
        nb_ok = bool(nb) and all(x.get("no_worse_than_best_safe", False) for x in nb)
        out.update(
            {
                "closes_50": c_ok,
                "null_ok": fp_ok,
                "ablation_removes_gain": abl_ok,
                "neighbours": nb,
                "neighbours_ok": nb_ok,
            }
        )
        out["repair"] = bool(c_ok and fp_ok and abl_ok and nb_ok) if abl_ok is not None else None
        n_uses = len(self.state.get("val_log", {}).get(f"{cell.cell_id}|{spec.spec_id}", []))
        out["validation_uses"] = n_uses
        if n_uses > 1:
            out["status"] = "reclassified_development"
        return out

    # -- summary -----------------------------------------------------------------
    def summary(self) -> None:
        st = self.state
        md = [
            "# Failure Atlas v1 summary (EXPLORATORY discovery; no claim; do not cite without the protocol)\n",
            f"git head `{self.git['head'][:10]}` dirty={self.git['dirty']}; sources "
            + ", ".join(f"{k} `{v[:10]}`" for k, v in self.git["src_sha256"].items())
            + f"; T={self.T}; smoke={st['smoke']}; method-runs={st['runs']}; elapsed={st['elapsed_s']:.0f}s"
            + (f"; STOPPED: {st['stopped']}" if st["stopped"] else ""),
            "## Limitations",
            (
                "- 2-state Bernoulli D only; no covariates or drift. Several R6 baselines are missing"
                " (registry below), so a shared failure is a failure against the implemented baselines only."
            ),
            "- `best_safe` (including `no_switch`) is chosen on the evaluation seeds, which favours the baselines.",
            "- R_family is calibrated empirically on one declared family, not an anytime-valid test.",
        ]
        if st.get("smoke_forced"):
            md.append(
                "**SMOKE: no shared failure existed, so the top cells by H were forced through stages 2-4 "
                "only to exercise the code. They are not failures.**"
            )
        md.append("## Registry (stage 0)")
        md.append(
            md_table(
                ["baseline", "status", "role", "guarantee", "notes"],
                [
                    [r["name"], r["status"], r["role"], r["guarantee"], r["notes"]]
                    for r in fa.BASELINE_REGISTRY
                ],
            )
        )
        cal = st.get("calibration")
        if cal:
            md.append("## R_family kappa calibration (discovery null twins)")
            md.append(
                f"chosen kappa = {cal['kappa']} (calibrated={cal['calibrated']}, {cal['n_twins']} distinct twins, "
                f"seeds {cal['seeds']})\n\n"
                + md_table(
                    ["kappa", "FP count", "n", "pooled any-FP rate"],
                    [[k, v["k"], v["n"], f"{v['rate']:.3f}"] for k, v in cal["table"].items()],
                )
            )
        disc = getattr(self, "disc", None)
        if disc:
            cnt = Counter(cl["label"] for _, _, cl in disc)
            md.append("## Discovery counts by class (stage 1)")
            md.append(
                md_table(
                    ["class", "cells"],
                    [[k, v] for k, v in sorted(cnt.items())] + [["total", len(disc)]],
                )
            )
            il = [(c, cl) for c, _, cl in disc if cl["info_limited"]]
            md.append("## Information-limited cells")
            md.append(
                md_table(
                    ["cell", "no_switch - R_law [95% CI]"],
                    [
                        [
                            c.cell_id,
                            fmt_ci(
                                cl["info_gap"]["mean"], (cl["info_gap"]["lo"], cl["info_gap"]["hi"])
                            ),
                        ]
                        for c, cl in il[:40]
                    ],
                )
                if il
                else "none"
            )
            near = sorted(
                (x for x in disc if x[2]["label"] == "headroom_not_shared"),
                key=lambda x: -x[2]["H"],
            )[:10]
            if near:
                md.append("## Headroom but not shared (top 10 by H)")
                md.append(
                    md_table(
                        ["cell", "best_safe", "H [95% CI]"],
                        [
                            [c.cell_id, cl["best_safe"], fmt_ci(cl["H"], cl["H_ci"])]
                            for c, _, cl in near
                        ],
                    )
                )
        if st["failures"]:
            md.append("## Reproduced failures (stage 2, fresh discovery seeds)")
            names = [*fa.SAFETY_GATED, fa.FLOOR]
            rows = []
            for f in st["failures"]:
                rows.append(
                    [
                        f["cell_id"] + (" (smoke-forced)" if f["smoke_forced"] else ""),
                        f["label"],
                        f"{f['severity']:.4f}",
                        fmt_ci(f["H"], f["H_ci"]),
                        f["best_safe"],
                        f"{f['fp']['rate']:.3f} [{f['fp']['wilson'][0]:.3f},{f['fp']['wilson'][1]:.3f}]",
                    ]
                )
            md.append(
                md_table(
                    [
                        "cell",
                        "label",
                        "severity",
                        "H [95% CI]",
                        "best_safe",
                        "R_family null FP [Wilson]",
                    ],
                    rows,
                )
            )
            md.append("### Per-baseline gap to R_family (mean, lower CI bound; cost per round)")
            md.append(
                md_table(
                    ["cell", *names],
                    [
                        [f["cell_id"]]
                        + [
                            f"{f['gaps'][n]['mean']:+.3f} ({f['gaps'][n]['lo']:+.3f})"
                            if n in f["gaps"]
                            else "-"
                            for n in names
                        ]
                        for f in st["failures"]
                    ],
                )
            )
        if st["mechanism"]:
            md.append(
                "## Isolation (stage 4): does moving one axis to its easiest level remove the failure?"
            )
            rows = []
            for cid, info in st["mechanism"].items():
                row = [cid]
                for ax in fa.AXES:
                    cl = info["isolation"].get(ax)
                    row.append(
                        "at easiest"
                        if cl is None
                        else f"{'REMOVES' if cl['removes_failure'] else 'keeps'} (H lo {cl['H_ci'][0]:+.3f}, {cl['label']})"
                    )
                rows.append(row)
            md.append(md_table(["failure cell", *fa.AXES], rows))
            md.append("## Mechanism stages 5-6")
            md.append(st.get("stage56_status", "see per-failure rows below"))
            for cid, info in st["mechanism"].items():
                s5, s6 = info.get("stage5"), info.get("stage6")
                if s5 is None and s6 is None:
                    continue
                line = f"- `{cid}` (axes removing: {info['axes_removing']}): "
                if isinstance(s5, dict):
                    runs = [r for r in s5["run"] if "error" not in r]
                    best = min(runs, key=lambda r: r["cost"]) if runs else None
                    line += (
                        f"{s5['n_proposed']} proposed, {s5['n_invalid']} invalid, {len(runs)} run"
                    )
                    if best:
                        line += (
                            f"; best `{best['id']}` cost {best['cost']:.4f}, gap closure {best['gap_closure']:.2f}, "
                            f"null FP {best['fp_null']:.2f}, gated={best['gated']}"
                        )
                else:
                    line += str(s5)
                if isinstance(s6, dict):
                    line += "; validation: " + ", ".join(f"{k}={v}" for k, v in s6.items())
                elif s6:
                    line += f"; validation: {s6}"
                md.append(line)
        md += self.summary_cycle2()
        (self.out / "summary.md").write_text("\n\n".join(md) + "\n", encoding="utf-8")

    def summary_cycle2(self) -> list[str]:
        st, md = self.state, []
        if st.get("stage_times"):
            prev, rows = 0.0, []
            for k, v in st["stage_times"].items():
                rows.append([k, f"{v - prev:.0f}"])
                prev = v
            md.append("## Wall time per stage (s)")
            md.append(md_table(["stage", "seconds"], rows))
        if st.get("reused_cells_from"):
            md.append(
                f"Sampled and refinement cells reused from `{st['reused_cells_from']}` "
                "(same seeds and cells as the previous cycle)."
            )
        prior = getattr(self, "prior", None)
        disc = getattr(self, "disc", None)
        if prior and disc:
            labels = sorted(
                {cl["label"] for cl in prior.values()} | {cl["label"] for _, _, cl in disc}
            )
            now = {c.cell_id: cl["label"] for c, _, cl in disc}
            hnow = {c.cell_id: cl["H"] for c, _, cl in disc}
            cnt = Counter((prior[c]["label"], now[c]) for c in now if c in prior)
            md.append("## Class transitions: previous cycle (rows) -> this cycle (columns)")
            md.append(
                md_table(
                    ["prev \\ now", *labels, "total"],
                    [
                        [
                            pl,
                            *[cnt.get((pl, nl), 0) for nl in labels],
                            sum(cnt.get((pl, nl), 0) for nl in labels),
                        ]
                        for pl in labels
                    ],
                )
            )
            pc = Counter(cl["label"] for cl in prior.values())
            md.append(
                "Previous-cycle class counts recomputed from its archive: "
                + ", ".join(f"{k}={v}" for k, v in sorted(pc.items()))
                + f" (total {sum(pc.values())})"
            )
            moved = [
                (c, prior[c]["label"], now[c], hnow[c])
                for c in now
                if c in prior
                and prior[c]["label"] != now[c]
                and "shared_failure" in (prior[c]["label"], now[c])
            ]
            if moved:
                md.append("### Cells entering or leaving shared_failure")
                md.append(
                    md_table(
                        ["cell", "previous", "now", "H (now)"],
                        [[c, a, b, f"{h:+.4f}"] for c, a, b, h in sorted(moved)],
                    )
                )
        diag = st.get("diagnostics")
        if diag:
            thr = next(iter(diag.values()))["log_threshold"]
            nd = len(next(iter(diag.values()))["seeds"])
            md.append(
                f"## Diagnostic decomposition (stage 2b; evaluator-side, descriptive, {nd} seeds)"
            )
            md.append(
                "Cost is per round. `front` = `episode_front`, the decision rule shared by the "
                "`diag_oracle_*` variants (oracle: onset and/or Kelly stake given by the evaluator; "
                "never methods). Parts: onset = front - known_onset; stake = front - known_stake; "
                "interaction = (front - known_both) - onset - stake; residual = known_both - R_family; "
                "gap = best_safe - R_family = (best_safe - front) + onset + stake + interaction + residual. "
                "Brackets are paired 95% CIs."
            )

            def f(x):
                return f"{x['mean']:+.4f} [{x['lo']:+.4f}, {x['hi']:+.4f}]"

            order = (
                "gap_best_safe_vs_family",
                "best_safe_minus_front",
                "onset_uncertainty",
                "stake_mismatch",
                "interaction",
                "residual_known_both_minus_family",
            )
            md.append(
                md_table(
                    [
                        "cell",
                        "best_safe",
                        "Kelly stake",
                        "gap",
                        "best_safe-front",
                        "onset",
                        "stake",
                        "interaction",
                        "residual",
                    ],
                    [
                        [
                            cid,
                            d["best_safe"],
                            f"{d['kelly_stake']:.3f}",
                            *[f(d["parts"][k]) for k in order],
                        ]
                        for cid, d in diag.items()
                    ],
                )
            )
            md.append(f"### Per-baseline exposure (log(1/alpha) = {thr:.3f})")
            rows = []
            for cid, d in diag.items():
                for name, v in d["per_method"].items():
                    if name in ("ref_family", "ref_law"):
                        continue
                    an = v["analytic"]["labels"]
                    rows.append(
                        [
                            cid,
                            name,
                            f"{v['mean_cost']:.4f}",
                            "-"
                            if v["labels_after_onset"] is None
                            else f"{v['labels_after_onset']:.1f}",
                            f"{v['frac_promoted']:.2f}",
                            "none"
                            if v["mean_first_promotion_round"] is None
                            else f"{v['mean_first_promotion_round']:.0f}",
                            "-"
                            if v["mean_final_log_e"] is None
                            else f"{v['mean_final_log_e']:+.2f}",
                            "-" if an is None else f"{an:.1f}",
                        ]
                    )
            md.append(
                md_table(
                    [
                        "cell",
                        "method",
                        "cost",
                        "labels from favourable state",
                        "frac promoted",
                        "mean first-promotion round",
                        "final log e (episode 0)",
                        "analytic labels needed",
                    ],
                    rows,
                )
            )
        mech = st.get("mechanism") or {}
        rows = []
        for cid, info in mech.items():
            s5, s6 = info.get("stage5"), info.get("stage6")
            if not isinstance(s5, dict):
                continue
            runs = [r for r in s5["run"] if "error" not in r]
            best = min(runs, key=lambda r: r["cost"]) if runs else None
            bid = best["id"] if best else "-"
            head = [cid, info["axes_removing"] or "none", f"{s5['n_proposed']}/{s5['n_invalid']}"]
            if isinstance(s6, dict) and "cost" in s6:
                nb = s6.get("neighbours", [])
                detail = "; ".join(
                    f"{x['cell']}: "
                    + (
                        "err"
                        if "error" in x
                        else f"vs best_safe {x['cand_minus_best_safe'][0]:+.3f} "
                        f"[{x['cand_minus_best_safe'][1]:+.3f},{x['cand_minus_best_safe'][2]:+.3f}], "
                        f"ok={x['no_worse_than_best_safe']}"
                    )
                    for x in nb
                )
                rows.append(
                    [
                        *head,
                        s6.get("candidate"),
                        f"{s6['cost']:.4f}",
                        f"{s6['gap_closure']:.2f}",
                        f"{s6['null_fp']:.2f}",
                        s6.get("closes_50"),
                        s6.get("ablation_removes_gain"),
                        s6.get("neighbours_ok"),
                        detail,
                        s6.get("repair"),
                        s6.get("status", ""),
                        bid,
                    ]
                )
            else:
                rows.append([*head, "-", "-", "-", "-", "-", "-", "-", str(s6), None, "", bid])
        if rows:
            md.append("## Candidate and repair table (stages 5-6)")
            md.append(
                md_table(
                    [
                        "failure cell",
                        "axes removing",
                        "proposed/invalid",
                        "stage-6 candidate",
                        "val cost",
                        "gap closure",
                        "null FP",
                        "closes >=50%",
                        "ablation removes gain",
                        "neighbours ok",
                        "neighbour detail",
                        "repair",
                        "status",
                        "best dev candidate",
                    ],
                    rows,
                )
            )
        vl = st.get("val_log") or {}
        if vl:
            md.append(
                "## Validation-seed use log (pairs used more than once are reclassified_development)"
            )
            md.append(
                md_table(
                    ["cell|spec", "uses", "status"],
                    [
                        [k, len(v), "reclassified_development" if len(v) > 1 else "first use"]
                        for k, v in sorted(vl.items())
                    ],
                )
            )
        return md


def build_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs/failure_atlas_v1")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--max-hours", type=float, default=4.0)
    ap.add_argument("--max-runs", type=int, default=2_000_000)
    ap.add_argument("--sample-seed", type=int, default=12345)
    ap.add_argument("--n-sample", type=int, default=240)
    ap.add_argument("--n-refine", type=int, default=120)
    ap.add_argument("--n-seeds", type=int, default=20)
    ap.add_argument("--n-reproduce", type=int, default=100)
    ap.add_argument("--n-null-seeds", type=int, default=100)
    ap.add_argument("--top-k", type=int, default=12)
    ap.add_argument("--n-diag", type=int, default=100)
    ap.add_argument(
        "--val-offset", type=int, default=0, help="offset into the mechanism seed range"
    )
    ap.add_argument(
        "--reuse-cells-from", default=None, help="state.json whose sample/refine cells to reuse"
    )
    ap.add_argument(
        "--compare-to", default=None, help="previous cycle output dir (class transitions)"
    )
    args = ap.parse_args()
    if args.smoke:
        args.n_sample, args.n_refine, args.n_seeds = 12, 4, 4
        args.n_reproduce, args.top_k, args.n_null_seeds = 8, 4, 12
        args.n_diag = 4
    if args.workers is None:
        # protocol default is cpu_count - 2; each worker holds ~150-250 MB, so cap for 16 GB machines
        args.workers = max(1, min((os.cpu_count() or 4) - 2, 12))
    out = Path(args.out)
    args.out = str(out if out.is_absolute() else ROOT / out)
    for k in ("reuse_cells_from", "compare_to"):
        v = getattr(args, k)
        if v:
            pv = Path(v)
            setattr(args, k, str(pv if pv.is_absolute() else ROOT / pv))
    return args


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = build_args()
    print(f"[atlas] out={args.out} smoke={args.smoke} workers={args.workers}", flush=True)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        run = Runner(args, pool)
        try:
            if args.compare_to:
                run.prior = run.prior_classes(args.compare_to)
            run.stage0_registry()
            run.stage1_discover()
            run.mark("stage1_discover")
            run.stage2_reproduce()
            run.mark("stage2_reproduce")
            run.stage2b_diagnose()
            run.mark("stage2b_diagnose")
            run.stage4_isolate()
            run.mark("stage4_isolate")
            run.stage5_6_mechanism()
            run.mark("stage5_6_mechanism")
            run.state["stopped"] = "completed all stages"
        except StopLoop as stop:
            run.state["stopped"] = str(stop)
            print(f"[atlas] stopping: {stop}", flush=True)
        run.save()
        run.summary()
    print(f"[atlas] done -> {args.out}/summary.md", flush=True)


if __name__ == "__main__":
    main()
