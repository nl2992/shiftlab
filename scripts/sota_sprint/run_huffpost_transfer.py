"""Single-opening, date-batched replay for the frozen Wild-Time HuffPost protocol."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import pickle
import platform
import subprocess
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import sklearn

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))
sys.path.insert(0, str(ROOT / "scripts/promising_directions/sota"))

from prepare_huffpost_transfer import (
    ARCHIVE,
    CATEGORIES,
    RAW_DIR,
    RUN_DIR,
    SEED,
    sha256,
)
from registry import EXTRA
from simulator import Event, ReleasedFeedback
from suite import build_suite

TEST_START = date(2018, 1, 1)
TEST_END = date(2018, 5, 26)  # half-open; last available registered date is May 25
ALPHA, LABEL_PRICE, SWITCH_COST = 0.05, 0.05, 5.0
POLICY_NAMES = (
    "PFA-SR:gated_adaptive_range",
    "rmm:gated_adaptive_range+RMM",
    "xu_acquisition_only",
    "E_rb:gated_adaptive_range",
    "E_swcert",
    "CONTROL_never_switch",
)


def load_test_metadata() -> list[dict]:
    """Select registered test rows and IDs only; do not derive predictions or losses here."""
    rows = []
    with ARCHIVE.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            row = json.loads(line)
            try:
                published = date.fromisoformat(row["date"])
            except (KeyError, TypeError, ValueError):
                continue
            title = row.get("headline")
            if not TEST_START <= published < TEST_END:
                continue
            if "category" not in row or not isinstance(title, str) or not title.strip():
                continue
            rows.append({"id": line_number, "date": published, "title": title})
    rows.sort(key=lambda row: (row["date"], row["id"]))
    return rows


def code_hash() -> str:
    files = source_files()
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def source_files() -> list[Path]:
    return [
        Path(__file__),
        Path(__file__).with_name("prepare_huffpost_transfer.py"),
        ROOT / "scripts/promising_directions/sota/simulator.py",
        ROOT / "scripts/sota_sprint/registry.py",
        ROOT / "scripts/sota_sprint/pfa_srr_baseline.py",
        ROOT / "scripts/sota_sprint/fam_e.py",
        ROOT / "scripts/failure_atlas_v2/restart_monitor.py",
        ROOT / "scripts/failure_atlas_v2_flq/strong_hosts.py",
        ROOT / "scripts/failure_atlas_v2_flq/suite.py",
        ROOT / "scripts/sota_sprint/fam_b.py",
        ROOT / "scripts/failure_atlas_v2_flq/v2_extra.py",
        ROOT / "scripts/failure_atlas_v2_flq/qce.py",
        ROOT / "scripts/failure_atlas_v2_flq/qsg.py",
        ROOT / "scripts/failure_atlas_v2_flq/r6_policies.py",
        ROOT / "scripts/promising_directions/sota/competitors/certificate_stops.py",
        ROOT / "scripts/promising_directions/sota/competitors/controls.py",
        ROOT / "scripts/promising_directions/sota/competitors/smcs.py",
        ROOT / "scripts/promising_directions/sota/competitors/xu_acquisition.py",
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
        ROOT / "research/scoped_method/pilots/chronological_news_transfer_20261106/protocol.md",
        ROOT
        / "research/scoped_method/pilots/chronological_news_transfer_20261106/PROTOCOL_AMENDMENT_20261106.md",
    ]


def installed_packages() -> dict[str, str]:
    return {
        dist.metadata["Name"]: dist.version
        for dist in importlib.metadata.distributions()
        if dist.metadata.get("Name")
    }


def freeze_code() -> None:
    freeze_path = RUN_DIR / "code_freeze.json"
    if freeze_path.exists():
        raise RuntimeError("code freeze already exists; refusing to replace it")
    files = source_files()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tracked_diff = subprocess.check_output(["git", "diff", "HEAD", "--binary"], cwd=ROOT)
    value = {
        "git_head": head,
        "tracked_worktree_diff_sha256": hashlib.sha256(tracked_diff).hexdigest(),
        "source_hashes": {str(p.relative_to(ROOT)): sha256(p) for p in files},
        "aggregate_code_sha256": code_hash(),
        "dataset_sha256": sha256(ARCHIVE),
        "models_sha256": sha256(RAW_DIR / "frozen_models.pkl"),
        "eligibility_sha256": sha256(RUN_DIR / "source_eligibility.json"),
        "pretest_manifest_sha256": sha256(RUN_DIR / "pretest_manifest.json"),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
        "installed_packages": installed_packages(),
    }
    fd = os.open(freeze_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(value, f, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def policy_factories(T: int, B: int, delay_rows: int):
    policies = build_suite(
        T,
        B,
        SWITCH_COST,
        LABEL_PRICE,
        ALPHA,
        delay_rows,
        ep=1,
        seed_base=SEED,
        names=POLICY_NAMES,
        extra=EXTRA,
    )
    return {policy.name: policy for policy in policies}


def date_batched_replay(policy, predictions, labels, dates, *, budget, delay_days):
    """Run requests for a date before delivering labels due at that same midnight."""
    T = len(labels)
    groups: dict[date, list[int]] = defaultdict(list)
    for i, d in enumerate(dates):
        groups[d].append(i)
    remaining = budget
    deployed = 0
    switches = label_count = 0
    total_loss = 0.0
    trace = []
    by_day: dict[date, list[tuple[int, ReleasedFeedback]]] = defaultdict(list)
    delay = timedelta(days=delay_days)
    for d in sorted(groups):
        # Releases strictly before today's timestamp are already available on arrival.
        earlier_due = sorted(day for day in by_day if day < d)
        if earlier_due:
            next_t = min(groups[d])
            released = [
                ReleasedFeedback(
                    event_id=feedback.event_id,
                    t_requested=feedback.t_requested,
                    t_released=next_t,
                    label=feedback.label,
                    model_losses=feedback.model_losses,
                    query_probability=feedback.query_probability,
                    extra=feedback.extra,
                )
                for due_day in earlier_due
                for _, feedback in by_day.pop(due_day)
            ]
            policy.observe(released)
        # Requests at midnight d precede releases whose timestamp is midnight d.
        for i in groups[d]:
            event = Event(
                event_id=i, t=i, horizon=T, model_predictions=predictions[i], context=None
            )
            deployed_new = int(policy.predict(event))
            switched = int(deployed_new != deployed)
            deployed = deployed_new
            loss = int(predictions[i, deployed] != labels[i])
            total_loss += loss
            req = policy.request_labels(event, remaining)
            granted = bool(req.requested and remaining > 0)
            if granted:
                remaining -= 1
                label_count += 1
                feedback = ReleasedFeedback(
                    event_id=i,
                    t_requested=i,
                    t_released=i + 1,
                    label=int(labels[i]),
                    model_losses=(predictions[i] != labels[i]).astype(np.int8),
                    query_probability=float(req.probability),
                    extra=dict(req.extra),
                )
                by_day[d + delay].append((i, feedback))
            switches += switched
            trace.append(
                {
                    "event_id": i,
                    "date": d.isoformat(),
                    "deployed_model": deployed,
                    "requested": int(granted),
                    "prediction_loss": loss,
                    "switch": switched,
                    "query_probability": float(req.probability),
                }
            )
        # Deliver all labels at the date boundary only after this date's requests.
        releasable_days = sorted(day for day in by_day if day == d)
        if releasable_days:
            next_t = max(groups[d]) + 1
            released = [
                ReleasedFeedback(
                    event_id=feedback.event_id,
                    t_requested=feedback.t_requested,
                    t_released=next_t,
                    label=feedback.label,
                    model_losses=feedback.model_losses,
                    query_probability=feedback.query_probability,
                    extra=feedback.extra,
                )
                for due_day in releasable_days
                for _, feedback in by_day.pop(due_day)
            ]
            policy.observe(released)
    # The stream has ended; no post-horizon feedback can affect deployment.
    net = total_loss + LABEL_PRICE * label_count + SWITCH_COST * switches
    promote = [
        x
        for i, x in enumerate(trace)
        if x["deployed_model"] == 1 and (i == 0 or trace[i - 1]["deployed_model"] == 0)
    ]
    rollback = [
        x
        for i, x in enumerate(trace)
        if x["deployed_model"] == 0 and i > 0 and trace[i - 1]["deployed_model"] == 1
    ]
    return {
        "net_cost": net,
        "prediction_loss": total_loss,
        "labels": label_count,
        "label_expenditure": LABEL_PRICE * label_count,
        "switches": switches,
        "switch_expenditure": SWITCH_COST * switches,
        "promotion_count": len(promote),
        "rollback_count": len(rollback),
        "first_promotion_event": promote[0]["event_id"] if promote else None,
        "first_promotion_date": promote[0]["date"] if promote else None,
        "time_to_promotion_events": promote[0]["event_id"] if promote else None,
        "final_model": deployed,
        "trace": trace,
    }


def moving_block_interval(diffs, dates, *, n_boot=2000, seed=SEED):
    """Paired 7-calendar-day moving-block bootstrap; one source cluster only."""
    daily = defaultdict(list)
    for value, day in zip(diffs, dates, strict=True):
        daily[day].append(float(value))
    first, last = min(daily), max(daily)
    day_values = [first + timedelta(days=i) for i in range((last - first).days + 1)]
    day_sums = np.asarray([np.sum(daily[d]) for d in day_values])
    day_counts = np.asarray([len(daily[d]) for d in day_values])
    n = len(day_sums)
    rng = np.random.default_rng(seed)
    blocks = [np.arange(s, min(s + 7, n)) for s in range(n)]
    estimates = np.empty(n_boot)
    for b in range(n_boot):
        chosen = []
        while len(chosen) < n:
            block = blocks[int(rng.integers(n))]
            chosen.extend(zip(day_sums[block], day_counts[block], strict=True))
        sample = chosen[:n]
        estimates[b] = sum(x[0] for x in sample) / sum(x[1] for x in sample)
    return {
        "mean_per_event": float(np.mean(diffs)),
        "per_1000_events": float(np.mean(diffs) * 1000),
        "ci95_per_1000_events": [float(x) for x in np.quantile(estimates, [0.025, 0.975]) * 1000],
        "bootstrap_resamples": n_boot,
        "calendar_block_days": 7,
    }


def open_and_run() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    marker = RUN_DIR / "TEST_OPENED.json"
    started_marker = RUN_DIR / "TEST_OPENING_STARTED.json"
    if marker.exists() or started_marker.exists():
        raise RuntimeError("test opening already started; refusing to overwrite its records")
    pretest = json.loads((RUN_DIR / "pretest_manifest.json").read_text())
    freeze_path = RUN_DIR / "code_freeze.json"
    if not freeze_path.exists():
        raise RuntimeError("run --freeze after review, before opening test outcomes")
    freeze = json.loads(freeze_path.read_text())
    if freeze["pretest_manifest_sha256"] != sha256(RUN_DIR / "pretest_manifest.json"):
        raise RuntimeError("pretest manifest changed after the pre-outcome code freeze")
    current_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    current_diff = subprocess.check_output(["git", "diff", "HEAD", "--binary"], cwd=ROOT)
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", freeze["git_head"], current_head],
        cwd=ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        raise RuntimeError("frozen code commit is not an ancestor of the current Git HEAD")
    if hashlib.sha256(current_diff).hexdigest() != freeze["tracked_worktree_diff_sha256"]:
        raise RuntimeError("tracked worktree changed after the pre-outcome code freeze")
    if freeze["aggregate_code_sha256"] != code_hash():
        raise RuntimeError("source code changed after the pre-outcome code freeze")
    if freeze["source_hashes"] != {str(p.relative_to(ROOT)): sha256(p) for p in source_files()}:
        raise RuntimeError("one or more frozen source or dependency files changed")
    if freeze["installed_packages"] != installed_packages():
        raise RuntimeError("installed Python dependency set changed after code freeze")
    if (
        freeze["python"] != platform.python_version()
        or freeze["numpy"] != np.__version__
        or freeze["scikit_learn"] != sklearn.__version__
    ):
        raise RuntimeError("runtime versions changed after code freeze")
    if (
        freeze["dataset_sha256"] != sha256(ARCHIVE)
        or freeze["dataset_sha256"] != pretest["archive_sha256"]
    ):
        raise RuntimeError("dataset does not match frozen pretest archive")
    if freeze["models_sha256"] != sha256(RAW_DIR / "frozen_models.pkl"):
        raise RuntimeError("model pair changed after code freeze")
    eligibility_path = RUN_DIR / "source_eligibility.json"
    eligibility = json.loads(eligibility_path.read_text())
    if not eligibility.get("eligible") or sha256(eligibility_path) != pretest["eligibility_sha256"]:
        raise RuntimeError("frozen eligible-source record missing or changed")
    model_path = RAW_DIR / "frozen_models.pkl"
    if sha256(model_path) != pretest["models_sha256"]:
        raise RuntimeError("frozen model pair changed")
    candidates = load_test_metadata()
    if len(candidates) < 2000:
        raise RuntimeError(f"test metadata has only {len(candidates)} candidate rows")
    candidate_ids = [r["id"] for r in candidates]
    candidate_hash = hashlib.sha256(
        json.dumps(candidate_ids, separators=(",", ":")).encode()
    ).hexdigest()
    started = {
        "status": "opening started before target cleaning; no predictions or losses computed",
        "candidate_row_ids_sha256": candidate_hash,
        "candidate_row_ids": candidate_ids,
        "dataset_sha256": sha256(ARCHIVE),
        "code_freeze_sha256": sha256(freeze_path),
    }
    fd = os.open(started_marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(started, f, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    candidate_set = set(candidate_ids)
    labels_by_id = {}
    with ARCHIVE.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if line_number in candidate_set:
                category = str(json.loads(line).get("category", "")).upper()
                if category in CATEGORIES:
                    labels_by_id[line_number] = CATEGORIES.index(category)
    rows = [row for row in candidates if row["id"] in labels_by_id]
    if len(rows) < 2000:
        raise RuntimeError(f"target-cleaned test set has only {len(rows)} usable rows")
    ids = [r["id"] for r in rows]
    id_hash = hashlib.sha256(json.dumps(ids, separators=(",", ":")).encode()).hexdigest()
    # Acquisition pacing needs an event-count delay; calculate its fixed value from validation.
    validation_counts = defaultdict(int)
    with ARCHIVE.open(encoding="utf-8") as stream:
        for line in stream:
            raw = json.loads(line)
            try:
                day = date.fromisoformat(raw["date"])
            except (KeyError, TypeError, ValueError):
                continue
            category = str(raw.get("category", "")).upper()
            title = raw.get("headline")
            if (
                date(2017, 1, 1) <= day < date(2018, 1, 1)
                and category in CATEGORIES
                and isinstance(title, str)
                and title.strip()
            ):
                validation_counts[day] += 1
    val_rows_per_day = max(1, int(np.median(list(validation_counts.values()))))
    budget = min(200, int(np.floor(0.10 * len(rows))))
    code_files = source_files()
    opening = {
        "status": "opened_before_test_outcomes",
        "dataset_sha256": sha256(ARCHIVE),
        "models_sha256": sha256(model_path),
        "eligibility_sha256": sha256(eligibility_path),
        "code_sha256": code_hash(),
        "source_file_hashes": {str(p.relative_to(ROOT)): sha256(p) for p in code_files},
        "pretest_manifest_sha256": sha256(RUN_DIR / "pretest_manifest.json"),
        "code_freeze_sha256": sha256(freeze_path),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
        "installed_packages": installed_packages(),
        "test_start_inclusive": TEST_START.isoformat(),
        "test_end_exclusive": TEST_END.isoformat(),
        "usable_rows": len(rows),
        "source_row_id_definition": "1-based original JSONL line number",
        "row_ids_sha256": id_hash,
        "row_ids": ids,
        "same_day_semantics": "request all rows at midnight before releasing labels due at midnight; stable original line order",
        "simulated_label_delay": "publication date + 24 hours at midnight UTC",
        "policy_delay_pacing_rows": val_rows_per_day,
        "label_budget": budget,
        "costs": {"label": LABEL_PRICE, "switch": SWITCH_COST, "alpha": ALPHA},
        "policy_names": POLICY_NAMES,
        "command": "python scripts/sota_sprint/run_huffpost_transfer.py",
        "candidate_row_ids_sha256": candidate_hash,
        "target_cleaning": "retain only the frozen Wild-Time 11-category mapping; unknown targets excluded before predictions/losses",
    }
    fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(opening, f, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    with model_path.open("rb") as f:
        pair = pickle.load(f)
    titles = [r["title"] for r in rows]
    predictions = np.column_stack(
        [pair[k][1].predict(pair[k][0].transform(titles)) for k in ("incumbent", "challenger")]
    ).astype(np.int8)
    labels = np.asarray([labels_by_id[r["id"]] for r in rows], dtype=np.int8)
    dates = [r["date"] for r in rows]
    factories = policy_factories(len(rows), budget, val_rows_per_day)
    summaries = {}
    traces = {}
    for name in POLICY_NAMES:
        result = date_batched_replay(
            factories[name], predictions, labels, dates, budget=budget, delay_days=1
        )
        traces[name] = result.pop("trace")
        summaries[name] = result
    paired = {}
    for comparator in ("rmm:gated_adaptive_range+RMM", "xu_acquisition_only"):
        diff = np.asarray(
            [
                a["prediction_loss"] - b["prediction_loss"]
                for a, b in zip(
                    traces["PFA-SR:gated_adaptive_range"], traces[comparator], strict=True
                )
            ],
            dtype=float,
        )
        # Add identical label and switch costs eventwise for the actual primary net-cost contrast.
        pfa, comp = traces["PFA-SR:gated_adaptive_range"], traces[comparator]
        diff = np.asarray(
            [
                (x["prediction_loss"] - y["prediction_loss"])
                + LABEL_PRICE * (x["requested"] - y["requested"])
                + SWITCH_COST * (x["switch"] - y["switch"])
                for x, y in zip(pfa, comp, strict=True)
            ]
        )
        paired[f"PFA-SR minus {comparator}"] = moving_block_interval(diff, dates)
    report = {
        "claim_boundary": "single-source time-blocked retrospective case study with simulated label delay; no cross-source/generalization or causal claim",
        "rows": len(rows),
        "budget": budget,
        "per_policy": summaries,
        "primary_paired_net_cost_contrasts": paired,
        "source_clusters": ["HuffPost"],
        "source_cluster_count": 1,
        "adverse_limitations": [
            "date-only timestamps",
            "simulated 24-hour feedback",
            "one independent source cluster",
            "no real publisher-level multiplicity",
        ],
    }
    for result in report["per_policy"].values():
        result["predictive_error_rate"] = result["prediction_loss"] / len(rows)
        result["net_cost_per_1000_events"] = result["net_cost"] * 1000 / len(rows)
    for comparison in report["primary_paired_net_cost_contrasts"].values():
        comparison["frozen_transfer_gate_pass"] = bool(
            comparison["per_1000_events"] <= -5.0 and comparison["ci95_per_1000_events"][1] < 0.0
        )
    (RUN_DIR / "transfer_results.json").write_text(json.dumps(report, indent=2) + "\n")
    (RUN_DIR / "prediction_stream_sha256.json").write_text(
        json.dumps(
            {
                "predictions_sha256": hashlib.sha256(predictions.tobytes()).hexdigest(),
                "test_labels_sha256_local_only": hashlib.sha256(labels.tobytes()).hexdigest(),
                "trace_hashes": {
                    name: hashlib.sha256(
                        json.dumps(rows_trace, separators=(",", ":")).encode()
                    ).hexdigest()
                    for name, rows_trace in traces.items()
                },
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    if sys.argv[1:] == ["--freeze"]:
        freeze_code()
    elif not sys.argv[1:]:
        open_and_run()
    else:
        raise SystemExit("usage: run_huffpost_transfer.py [--freeze]")
