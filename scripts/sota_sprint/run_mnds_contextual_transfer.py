"""One-opening chronological MN-DS replay for publisher-context intervention policies."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import pickle
import platform
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))
sys.path.insert(0, str(ROOT / "scripts/promising_directions/sota"))
sys.path.insert(0, str(ROOT / "scripts/promising_directions/sota/competitors"))

from prepare_mnds_transfer import RAW_DIR, SEED, sha256
from simulator import Event, ReleasedFeedback

ARCHIVE = ROOT / "data/raw/chronological_news_transfer_20261106/mn_ds_news_classification.csv"
PILOT_DIR = ROOT / "research/scoped_method/pilots/context_stratified_mnds_20261106"
RUN_DIR = PILOT_DIR / "run"
MODEL_PATH = RAW_DIR / "frozen_models.pkl"
RAW_RECORDS_PATH = RAW_DIR / "context_stratified_mnds_q4_records.jsonl"
PROTOCOL_PATHS = (
    PILOT_DIR / "protocol.md",
    PILOT_DIR / "PROTOCOL_AMENDMENT_PREOPENING.md",
    PILOT_DIR / "PROTOCOL_AMENDMENT_ANALYSIS.md",
)
ELIGIBILITY_PATH = (
    ROOT
    / "research/scoped_method/pilots/chronological_news_transfer_20261106/run/mn_ds_zenodo_7394851/source_eligibility.json"
)
CONTEXTS = ("eveningstandard", "sputnik", "tass", "other")
CORE_SOURCES = frozenset(CONTEXTS[:-1])
LABEL_PRICE = 0.05
SWITCH_COST = 5.0
ALPHA_STAGE = 0.00625
STAKES = (0.05, 0.1, 0.2, 0.4, 0.8)
TEST_START = pd.Timestamp("2019-10-01", tz="UTC")
TEST_END = pd.Timestamp("2020-01-01", tz="UTC")
EXCLUDED_ID = "1809"
STATIC_THRESHOLD = 0.03
STATIC_MIN_ROWS = 100
STATIC_POSITIVE_BLOCKS = 2
BASELINE_NAMES = (
    "CONTROL_never_switch",
    "gated_adaptive_range",
    "discern_style",
    "SMCS+retain-incumbent",
    "xu_acquisition_only",
    "PFA-SR:gated_adaptive_range",
    "rmm:gated_adaptive_range+RMM",
    "E_rb:gated_adaptive_range",
    "E_swcert",
    "qiu_delayed_movement",
    "gong_zhang_paid_obs",
    "cams_adapter",
    "model_picker_adapter",
    "model_selector_causal",
    "economic_replacement",
)
PRIMARY_REFERENCES = frozenset(
    {
        "PFA-SR:gated_adaptive_range",
        "rmm:gated_adaptive_range+RMM",
        "E_rb:gated_adaptive_range",
        "E_swcert",
        "validation_selected_source_static",
    }
)


def file_hash(path: Path) -> str:
    return sha256(path)


def protocol_hashes() -> dict[str, str]:
    return {str(path.relative_to(ROOT)): file_hash(path) for path in PROTOCOL_PATHS}


def source_files() -> list[Path]:
    explicit = [
        Path(__file__),
        Path(__file__).with_name("prepare_mnds_transfer.py"),
        ROOT / "scripts/sota_sprint/bench.py",
        ROOT / "scripts/promising_directions/sota/simulator.py",
        ROOT / "scripts/sota_sprint/registry.py",
        ROOT / "scripts/sota_sprint/pfa_srr_baseline.py",
        ROOT / "scripts/failure_atlas_v2/restart_monitor.py",
        ROOT / "scripts/failure_atlas_v2_flq/strong_hosts.py",
        ROOT / "scripts/failure_atlas_v2_flq/suite.py",
        ROOT / "scripts/failure_atlas_v2_flq/v2_extra.py",
        ROOT / "scripts/failure_atlas_v2_flq/qce.py",
        ROOT / "scripts/failure_atlas_v2_flq/qsg.py",
        ROOT / "scripts/failure_atlas_v2_flq/r6_policies.py",
        ROOT / "scripts/promising_directions/sota/competitors/certificate_stops.py",
        ROOT / "scripts/promising_directions/sota/competitors/controls.py",
        ROOT / "scripts/promising_directions/sota/competitors/smcs.py",
        ROOT / "scripts/promising_directions/sota/competitors/xu_acquisition.py",
        ROOT / "scripts/promising_directions/sota/competitors/cams.py",
        ROOT / "scripts/promising_directions/sota/competitors/model_picker.py",
        ROOT / "scripts/promising_directions/sota/competitors/model_selector.py",
        ROOT / "scripts/promising_directions/sota/competitors/online_llm_picker.py",
        ROOT / "scripts/promising_directions/sota/competitors/variance_min.py",
        ROOT / "src/shiftlab/dive/eprocess.py",
        ROOT / "tests/sota_sprint/test_mnds_contextual_transfer.py",
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
        *PROTOCOL_PATHS,
    ]
    families = sorted((ROOT / "scripts/sota_sprint").glob("fam_*.py"))
    return explicit + families


def package_versions() -> dict[str, str]:
    names = ("numpy", "pandas", "scikit-learn", "scipy")
    return {name: importlib.metadata.version(name) for name in names}


def write_exclusive(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, default=str)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def frozen_context_frequencies() -> dict[str, float]:
    eligibility = json.loads(ELIGIBILITY_PATH.read_text(encoding="utf-8"))
    if eligibility["publisher_clusters_frozen"] != sorted(CORE_SOURCES):
        raise RuntimeError("the frozen MN-DS source registry differs from the protocol")
    return {
        "eveningstandard": 127 / 2091,
        "sputnik": 102 / 2091,
        "tass": 102 / 2091,
        "other": 1760 / 2091,
    }


def freeze() -> None:
    destination = RUN_DIR / "code_freeze.json"
    if destination.exists():
        raise RuntimeError("code freeze already exists; refusing to replace it")
    if not ARCHIVE.is_file() or not MODEL_PATH.is_file():
        raise FileNotFoundError("registered MN-DS source or frozen model pair is missing")
    files = source_files()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    diff = subprocess.check_output(["git", "diff", "HEAD", "--binary"], cwd=ROOT)
    write_exclusive(
        destination,
        {
            "stage": "pre_test_code_freeze",
            "git_head": head,
            "tracked_worktree_diff_sha256": hashlib.sha256(diff).hexdigest(),
            "source_hashes": {str(path.relative_to(ROOT)): file_hash(path) for path in files},
            "protocol_hashes": protocol_hashes(),
            "archive_sha256": file_hash(ARCHIVE),
            "model_sha256": file_hash(MODEL_PATH),
            "eligibility_sha256": file_hash(ELIGIBILITY_PATH),
            "context_registry": list(CONTEXTS),
            "q3_context_frequencies": frozen_context_frequencies(),
            "python": platform.python_version(),
            "packages": package_versions(),
        },
    )


def verify_freeze() -> dict:
    frozen = json.loads((RUN_DIR / "code_freeze.json").read_text(encoding="utf-8"))
    expected = {str(path.relative_to(ROOT)): file_hash(path) for path in source_files()}
    if frozen["source_hashes"] != expected:
        raise RuntimeError("source files differ from the pre-test code freeze")
    if frozen["protocol_hashes"] != protocol_hashes():
        raise RuntimeError("protocol files differ from the pre-test code freeze")
    if frozen["archive_sha256"] != file_hash(ARCHIVE):
        raise RuntimeError("MN-DS source archive differs from the code freeze")
    if frozen["model_sha256"] != file_hash(MODEL_PATH):
        raise RuntimeError("frozen model pair differs from the code freeze")
    if frozen["eligibility_sha256"] != file_hash(ELIGIBILITY_PATH):
        raise RuntimeError("validation eligibility differs from the code freeze")
    return frozen


def load_test_rows() -> pd.DataFrame:
    columns = ["data_id", "published_utc", "source", "title", "category_level_1"]
    rows = pd.read_csv(
        ARCHIVE,
        usecols=columns,
        dtype={"data_id": str, "source": str, "title": str, "category_level_1": str},
    )
    rows["timestamp"] = pd.to_datetime(
        pd.to_numeric(rows["published_utc"], errors="coerce"), unit="s", utc=True
    )
    rows = rows.loc[
        (rows["timestamp"] >= TEST_START)
        & (rows["timestamp"] < TEST_END)
        & rows["title"].notna()
        & rows["source"].notna()
        & rows["category_level_1"].notna()
        & (rows["data_id"] != EXCLUDED_ID)
    ].copy()
    rows = rows.sort_values(["timestamp", "data_id"], kind="stable").reset_index(drop=True)
    return rows


def static_source_decisions() -> dict[str, int]:
    from prepare_mnds_transfer import load_development_rows

    valid = load_development_rows()
    valid = valid.loc[
        (valid["_time"] >= pd.Timestamp("2019-07-01", tz="UTC")) & (valid["_time"] < TEST_START)
    ].copy()
    bundle = pickle.loads(MODEL_PATH.read_bytes())
    models, classes = bundle["models"], bundle["classes"]
    valid = valid.loc[valid["category_level_1"].isin(classes)].copy()
    valid["timestamp"] = valid["_time"]
    text = valid["title"].astype(str).tolist()
    pred0 = models["incumbent"][1].predict(models["incumbent"][0].transform(text))
    pred1 = models["challenger"][1].predict(models["challenger"][0].transform(text))
    code = {name: index for index, name in enumerate(classes)}
    labels = valid["category_level_1"].map(code).to_numpy(dtype=np.int64)
    valid["gain"] = (pred0 != labels).astype(int) - (pred1 != labels).astype(int)
    valid["context"] = valid["source"].where(valid["source"].isin(CORE_SOURCES), "other")
    decisions = {}
    for context in CONTEXTS:
        group = valid.loc[valid["context"] == context].sort_values(
            ["timestamp", "data_id"], kind="stable"
        )
        values = group["gain"].to_numpy()
        blocks = np.array_split(values, 3)
        gain = float(values.mean()) if len(values) else 0.0
        positive = sum(bool(len(block) and block.mean() > 0) for block in blocks)
        decisions[context] = int(
            len(values) >= STATIC_MIN_ROWS
            and gain >= STATIC_THRESHOLD
            and positive >= STATIC_POSITIVE_BLOCKS
        )
    return decisions


class StaticContextPolicy:
    def __init__(self, decisions: dict[str, int]):
        self.name = "validation_selected_source_static"
        self.decisions = decisions
        self.context_decisions = decisions

    def predict(self, event: Event) -> int:
        return self.decisions[str(event.context)]

    def request_labels(self, event: Event, remaining_budget: int):
        del event, remaining_budget
        from simulator import QueryRequest

        return QueryRequest(requested=False)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        if feedback:
            raise RuntimeError("static validation selector must not receive test labels")


class StratifiedGate:
    """Fixed-context, two-stage betting gate with delayed, ordered feedback."""

    name = "publisher_stratified_promotion_rollback"

    def __init__(self, *, horizon: int, context_rates: dict[str, float]):
        from shiftlab.dive.eprocess import PredictableBoundMeanEProcess

        self.horizon = int(horizon)
        self.states = {}
        for context in CONTEXTS:
            self.states[context] = {
                "rate": float(context_rates[context]),
                "deployed": 0,
                "promoted": False,
                "rolled_back": False,
                "issued": {"promotion": 0, "rollback": 0},
                "exhausted": {"promotion": False, "rollback": False},
                "promotion": PredictableBoundMeanEProcess(alpha=ALPHA_STAGE, stakes=STAKES),
                "rollback": PredictableBoundMeanEProcess(alpha=ALPHA_STAGE, stakes=STAKES),
                "events": [],
                "next_event": 0,
                "crossings": [],
                "promotion_event": None,
                "rollback_event": None,
            }

    @staticmethod
    def _stage(state: dict) -> str | None:
        if state["rolled_back"]:
            return None
        return "rollback" if state["promoted"] else "promotion"

    def predict(self, event: Event) -> int:
        return int(self.states[str(event.context)]["deployed"])

    def request_labels(self, event: Event, remaining_budget: int):
        from simulator import QueryRequest

        context = str(event.context)
        state = self.states[context]
        stage = self._stage(state)
        if stage is None or state["exhausted"][stage]:
            state["events"].append({"event_id": event.event_id, "known": True})
            self._drain(context)
            return QueryRequest(requested=False)
        h = max(0.0, (self.horizon - event.t - 1) * state["rate"])
        if h <= SWITCH_COST:
            state["exhausted"][stage] = True
            state["events"].append({"event_id": event.event_id, "known": True})
            self._drain(context)
            return QueryRequest(requested=False)
        kappa = SWITCH_COST / h
        predictions = np.asarray(event.model_predictions)
        disagreement = bool(predictions[0] != predictions[1])
        issued = state["issued"][stage]
        if not disagreement:
            state["events"].append(
                {
                    "event_id": event.event_id,
                    "known": True,
                    "gain": 0.0,
                    "stage": stage,
                    "kappa": kappa,
                    "bound": 1.0 + kappa,
                }
            )
            self._drain(context)
            return QueryRequest(requested=False)
        if issued >= 25 or remaining_budget <= 0:
            state["exhausted"][stage] = True
            state["events"].append({"event_id": event.event_id, "known": True})
            self._drain(context)
            return QueryRequest(requested=False)
        state["issued"][stage] += 1
        state["events"].append(
            {
                "event_id": event.event_id,
                "known": False,
                "stage": stage,
                "kappa": kappa,
                "bound": 1.0 + kappa,
            }
        )
        return QueryRequest(
            requested=True,
            probability=1.0,
            extra={"context": context, "stage": stage, "kappa": kappa, "bound": 1.0 + kappa},
        )

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for item in feedback:
            context = str(item.extra["context"])
            state = self.states[context]
            for record in state["events"]:
                if record["event_id"] == item.event_id:
                    if record["known"]:
                        raise RuntimeError("feedback was delivered twice")
                    record["known"] = True
                    record["gain"] = float(item.model_losses[0] - item.model_losses[1])
                    break
            else:
                raise RuntimeError("released label has no corresponding candidate request")
            self._drain(context, released_event=item.t_released)

    def _drain(self, context: str, released_event: int | None = None) -> None:
        state = self.states[context]
        events = state["events"]
        while state["next_event"] < len(events):
            record = events[state["next_event"]]
            if not record.get("known", False):
                break
            if "stage" not in record:
                state["next_event"] += 1
                continue
            stage = record["stage"]
            gain = float(record["gain"])
            kappa = float(record["kappa"])
            increment = gain - kappa if stage == "promotion" else -gain - kappa
            process = state[stage]
            process.update(increment, bound=float(record["bound"]))
            if process.alarm and stage == "promotion" and not state["promoted"]:
                state["promoted"] = True
                state["deployed"] = 1
                state["promotion_event"] = released_event or record["event_id"]
                state["crossings"].append(
                    {"kind": "promotion", "event_id": state["promotion_event"]}
                )
                state["exhausted"]["promotion"] = True
            elif process.alarm and stage == "rollback" and state["promoted"]:
                state["rolled_back"] = True
                state["deployed"] = 0
                state["rollback_event"] = released_event or record["event_id"]
                state["crossings"].append({"kind": "rollback", "event_id": state["rollback_event"]})
                state["exhausted"]["rollback"] = True
            state["next_event"] += 1


def _load_models_and_test() -> tuple[dict, list[str], pd.DataFrame]:
    bundle = pickle.loads(MODEL_PATH.read_bytes())
    return bundle["models"], bundle["classes"], load_test_rows()


def _build_global_baselines(horizon: int, budget: int, delay: int) -> list:
    from registry import EXTRA
    from suite import build_suite

    return build_suite(
        horizon,
        budget,
        SWITCH_COST,
        LABEL_PRICE,
        0.05,
        delay,
        ep=1,
        seed_base=SEED,
        names=BASELINE_NAMES,
        extra=EXTRA,
    )


def _release_batch(policy, items: list[ReleasedFeedback]) -> None:
    if items:
        policy.observe(items)


def replay_policy(
    policy,
    *,
    rows: pd.DataFrame,
    predictions: np.ndarray,
    labels: np.ndarray,
    budget: int,
) -> tuple[dict, list[dict]]:
    T = len(rows)
    timestamps = rows["timestamp"].tolist()
    contexts = rows["context"].astype(str).tolist()
    dates: dict[pd.Timestamp, list[int]] = defaultdict(list)
    for index, timestamp in enumerate(timestamps):
        dates[timestamp].append(index)
    release_queue: dict[pd.Timestamp, list[ReleasedFeedback]] = defaultdict(list)
    remaining = budget
    issued = denied = switches = loss_total = 0
    previous_deployed: dict[str, int] = {}
    event_rows = []
    for timestamp in sorted(dates):
        for release_time in sorted(key for key in release_queue if key < timestamp):
            released = release_queue.pop(release_time)
            timestamp_ns = rows["timestamp"].astype("int64").to_numpy()
            release_index = int(np.searchsorted(timestamp_ns, release_time.value, side="left"))
            _release_batch(
                policy,
                [
                    ReleasedFeedback(
                        event_id=fb.event_id,
                        t_requested=fb.t_requested,
                        t_released=min(release_index, T),
                        label=fb.label,
                        model_losses=fb.model_losses,
                        query_probability=fb.query_probability,
                        extra=fb.extra,
                    )
                    for fb in released
                ],
            )
        indices = dates[timestamp]
        for index in indices:
            context = contexts[index]
            event = Event(
                event_id=index,
                t=index,
                horizon=T,
                model_predictions=predictions[index],
                context=context,
            )
            deployed = int(policy.predict(event))
            scope = (
                context
                if isinstance(policy, (StaticContextPolicy, StratifiedGate))
                else "__global__"
            )
            prev = previous_deployed.get(scope, 0)
            switched = int(deployed != prev)
            previous_deployed[scope] = deployed
            loss = int(predictions[index, deployed] != labels[index])
            loss_total += loss
            request = policy.request_labels(event, remaining)
            granted = bool(request.requested and remaining > 0)
            if request.requested and not granted:
                denied += 1
            if granted:
                remaining -= 1
                issued += 1
                due = timestamp + pd.Timedelta(hours=24)
                release_queue[due].append(
                    ReleasedFeedback(
                        event_id=index,
                        t_requested=index,
                        t_released=-1,
                        label=int(labels[index]),
                        model_losses=(predictions[index] != labels[index]).astype(np.int8),
                        query_probability=float(request.probability),
                        extra={**dict(request.extra), "release_time": due.isoformat()},
                    )
                )
            switches += switched
            event_rows.append(
                {
                    "event_id": index,
                    "data_id": str(rows.iloc[index]["data_id"]),
                    "publisher": str(rows.iloc[index]["source"]),
                    "timestamp": timestamp.isoformat(),
                    "context": context,
                    "deployed_model": deployed,
                    "prediction_loss": loss,
                    "requested": int(granted),
                    "query_probability": float(request.probability),
                    "switch": switched,
                    "label_cost": LABEL_PRICE * int(granted),
                    "switch_cost": SWITCH_COST * switched,
                    "event_cost": loss + LABEL_PRICE * int(granted) + SWITCH_COST * switched,
                }
            )
        due_now = sorted(key for key in release_queue if key == timestamp)
        for release_time in due_now:
            released = release_queue.pop(release_time)
            release_index = max(indices) + 1
            _release_batch(
                policy,
                [
                    ReleasedFeedback(
                        event_id=fb.event_id,
                        t_requested=fb.t_requested,
                        t_released=release_index,
                        label=fb.label,
                        model_losses=fb.model_losses,
                        query_probability=fb.query_probability,
                        extra=fb.extra,
                    )
                    for fb in released
                ],
            )
    switch_details = getattr(policy, "states", None)
    transitions = []
    if isinstance(policy, (StaticContextPolicy, StratifiedGate)):
        for context in CONTEXTS:
            previous = 0
            for item in event_rows:
                if item["context"] != context:
                    continue
                if item["deployed_model"] != previous:
                    transitions.append(
                        {
                            "kind": "promotion" if item["deployed_model"] else "rollback",
                            "event_id": item["event_id"],
                            "timestamp": item["timestamp"],
                            "context": context,
                        }
                    )
                    previous = item["deployed_model"]
    else:
        previous = 0
        for item in event_rows:
            if item["deployed_model"] != previous:
                transitions.append(
                    {
                        "kind": "promotion" if item["deployed_model"] else "rollback",
                        "event_id": item["event_id"],
                        "timestamp": item["timestamp"],
                        "context": None,
                    }
                )
                previous = item["deployed_model"]
    net = loss_total + LABEL_PRICE * issued + SWITCH_COST * switches
    summary = {
        "policy": policy.name,
        "n_events": T,
        "net_cost": net,
        "net_cost_per_1000": 1000 * net / T,
        "prediction_loss": loss_total,
        "labels": issued,
        "label_expenditure": LABEL_PRICE * issued,
        "switches": switches,
        "switch_expenditure": SWITCH_COST * switches,
        "promotion_count": sum(item["kind"] == "promotion" for item in transitions),
        "rollback_count": sum(item["kind"] == "rollback" for item in transitions),
        "deployment_transitions": transitions,
        "denied_requests": denied,
        "budget_respected": issued <= budget,
        "context_outcomes": _context_summaries(event_rows),
    }
    if switch_details is not None:
        summary["context_decisions"] = {
            context: {
                "promoted": bool(state["promoted"]),
                "rolled_back": bool(state["rolled_back"]),
                "promotion_event": state["promotion_event"],
                "rollback_event": state["rollback_event"],
                "promotion_labels": state["issued"]["promotion"],
                "rollback_labels": state["issued"]["rollback"],
                "evidence_crossings": state["crossings"],
            }
            for context, state in switch_details.items()
        }
    else:
        if hasattr(policy, "context_decisions"):
            summary["context_decisions"] = policy.context_decisions
    return summary, event_rows


def load_and_freeze_test_rows(
    frozen: dict, static_decisions: dict[str, int]
) -> tuple[pd.DataFrame, dict]:
    rows = load_test_rows()
    classes = pickle.loads(MODEL_PATH.read_bytes())["classes"]
    rows = rows.loc[rows["category_level_1"].isin(classes)].copy()
    rows = rows.sort_values(["timestamp", "data_id"], kind="stable").reset_index(drop=True)
    source = rows["source"].astype(str)
    rows["context"] = source.where(source.isin(CORE_SOURCES), "other")
    metadata = {
        "stage": "exclusive_pre_outcome_test_opening",
        "protocol_hashes": frozen["protocol_hashes"],
        "code_freeze_sha256": file_hash(RUN_DIR / "code_freeze.json"),
        "git_head": frozen["git_head"],
        "archive_sha256": file_hash(ARCHIVE),
        "model_sha256": file_hash(MODEL_PATH),
        "event_time_window": [TEST_START.isoformat(), TEST_END.isoformat()],
        "valid_test_rows": len(rows),
        "ordered_data_id_sha256": hashlib.sha256(
            "\n".join(rows["data_id"].astype(str)).encode()
        ).hexdigest(),
        "context_counts": {str(k): int(v) for k, v in rows["context"].value_counts().items()},
        "publisher_registry": sorted(rows["source"].astype(str).unique().tolist()),
        "context_registry": list(CONTEXTS),
        "validation_static_decisions": static_decisions,
        "excluded_data_id": EXCLUDED_ID,
        "label_release_contract": "published_utc + 24 hours (simulated)",
    }
    write_exclusive(RUN_DIR / "TEST_OPENED.json", metadata)
    return rows, metadata


def _moving_block_interval(
    candidate_events: list[dict],
    reference_events: list[dict],
    *,
    replicates: int = 2000,
    context: str | None = None,
    familywise_primary: bool = False,
) -> dict:
    candidate = pd.DataFrame(candidate_events).set_index("data_id")
    reference = pd.DataFrame(reference_events).set_index("data_id")
    if not candidate.index.equals(reference.index):
        raise RuntimeError("paired rows differ between policies")
    if context is not None:
        keep = candidate["context"] == context
        candidate = candidate.loc[keep]
        reference = reference.loc[keep]
        if candidate.empty:
            raise RuntimeError(f"no paired events in context {context!r}")
    delta = candidate["event_cost"] - reference["event_cost"]
    dates = pd.to_datetime(candidate["timestamp"], utc=True).dt.floor("D")
    daily = delta.groupby(dates).sum()
    first = daily.index.min()
    last = daily.index.max()
    calendar = pd.date_range(first, last, freq="D", tz="UTC")
    values = daily.reindex(calendar, fill_value=0.0).to_numpy()
    width = min(7, max(1, len(values)))
    rng = np.random.default_rng(2026110642)
    starts = np.arange(max(1, len(values) - width + 1))
    estimates = np.empty(replicates, dtype=float)
    target_days = len(values)
    for b in range(replicates):
        parts = []
        length = 0
        while length < target_days:
            start = int(rng.choice(starts))
            part = values[start : start + width]
            parts.append(part)
            length += len(part)
        sample = np.concatenate(parts)[:target_days]
        estimates[b] = 1000 * sample.sum() / len(delta)
    mean = float(1000 * delta.sum() / len(delta))
    lower, upper = (0.005, 0.995) if familywise_primary else (0.025, 0.975)
    return {
        "mean_candidate_minus_reference_per_1000": mean,
        "moving_block_ci_95": [
            float(np.quantile(estimates, 0.025)),
            float(np.quantile(estimates, 0.975)),
        ],
        "family_interval": [
            float(np.quantile(estimates, lower)),
            float(np.quantile(estimates, upper)),
        ],
        "family_interval_level": 0.99 if familywise_primary else 0.95,
        "block_days": width,
        "replicates": replicates,
        "seed": 2026110642,
        "n_events": len(delta),
    }


def _publisher_cluster_interval(
    candidate_events: list[dict], reference_events: list[dict], *, replicates: int = 2000
) -> dict:
    candidate = pd.DataFrame(candidate_events).set_index("data_id")
    reference = pd.DataFrame(reference_events).set_index("data_id")
    if not candidate.index.equals(reference.index):
        raise RuntimeError("paired rows differ between policies")
    paired = pd.DataFrame(
        {
            "publisher": candidate["publisher"].astype(str),
            "difference": candidate["event_cost"] - reference["event_cost"],
        }
    )
    clusters = paired.groupby("publisher")["difference"].agg(["sum", "count"])
    totals = clusters["sum"].to_numpy(dtype=float)
    counts = clusters["count"].to_numpy(dtype=float)
    rng = np.random.default_rng(2026110643)
    sampled = rng.integers(0, len(clusters), size=(replicates, len(clusters)))
    estimates = 1000 * totals[sampled].sum(axis=1) / counts[sampled].sum(axis=1)
    return {
        "publisher_cluster_ci_95": [
            float(np.quantile(estimates, 0.025)),
            float(np.quantile(estimates, 0.975)),
        ],
        "publisher_clusters": len(clusters),
        "publisher_cost_differences": [
            {
                "publisher": str(publisher),
                "events": int(row["count"]),
                "candidate_minus_reference": float(row["sum"]),
                "candidate_minus_reference_per_1000": float(1000 * row["sum"] / row["count"]),
            }
            for publisher, row in clusters.iterrows()
        ],
        "replicates": replicates,
        "seed": 2026110643,
    }


def _context_summaries(events: list[dict]) -> dict[str, dict]:
    frame = pd.DataFrame(events)
    output = {}
    for context, group in frame.groupby("context", sort=True):
        output[str(context)] = {
            "events": len(group),
            "publishers": int(group["publisher"].nunique()),
            "net_cost": float(group["event_cost"].sum()),
            "net_cost_per_1000": float(1000 * group["event_cost"].sum() / len(group)),
            "prediction_loss": int(group["prediction_loss"].sum()),
            "labels": int(group["requested"].sum()),
            "label_expenditure": float(group["label_cost"].sum()),
            "switches": int(group["switch"].sum()),
            "switch_expenditure": float(group["switch_cost"].sum()),
        }
    return output


def run() -> None:
    frozen = verify_freeze()
    prior_outputs = (
        "TEST_OPENED.json",
        "records.jsonl",
        "summary.json",
        "RESULTS.md",
    )
    if any((RUN_DIR / name).exists() for name in prior_outputs) or RAW_RECORDS_PATH.exists():
        raise RuntimeError("test opening or results already exist; refusing to overwrite")
    static_decisions = static_source_decisions()
    rows, opening = load_and_freeze_test_rows(frozen, static_decisions)
    models, classes, _ = _load_models_and_test()
    labels = (
        rows["category_level_1"]
        .map({name: i for i, name in enumerate(classes)})
        .to_numpy(dtype=np.int64)
    )
    text = rows["title"].astype(str).tolist()
    predictions = np.column_stack(
        [
            models[name][1].predict(models[name][0].transform(text))
            for name in ("incumbent", "challenger")
        ]
    ).astype(np.int64)
    horizon = len(rows)
    budget = min(200, int(np.floor(0.10 * horizon)))
    from prepare_mnds_transfer import load_development_rows

    q3 = load_development_rows()
    q3 = q3.loc[(q3["_time"] >= "2019-07-01") & (q3["_time"] < TEST_START)]
    q3_days = pd.to_datetime(q3["_time"], utc=True).dt.floor("D")
    delay_rows = max(1, int(np.median(q3_days.value_counts().to_numpy())))
    context_rates = frozen_context_frequencies()
    policies = _build_global_baselines(horizon, budget, delay_rows)
    policies.append(StaticContextPolicy(static_decisions))
    policies.append(StratifiedGate(horizon=horizon, context_rates=context_rates))
    summaries = []
    all_records = {}
    for policy in policies:
        summary, events = replay_policy(
            policy,
            rows=rows,
            predictions=predictions,
            labels=labels,
            budget=budget,
        )
        summaries.append(summary)
        all_records[policy.name] = events
    rows_out = []
    for name, events in all_records.items():
        for item in events:
            rows_out.append({"policy": name, **item})
    fd = os.open(RAW_RECORDS_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        for item in rows_out:
            stream.write(json.dumps(item, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    row_frame = pd.DataFrame(rows_out)
    row_frame["day"] = pd.to_datetime(row_frame["timestamp"], utc=True).dt.floor("D").astype(str)
    sufficient = (
        row_frame.groupby(["policy", "day", "context"], sort=True)
        .agg(
            events=("event_id", "size"),
            prediction_loss=("prediction_loss", "sum"),
            labels=("requested", "sum"),
            label_expenditure=("label_cost", "sum"),
            switches=("switch", "sum"),
            switch_expenditure=("switch_cost", "sum"),
            net_cost=("event_cost", "sum"),
        )
        .reset_index()
    )
    sufficient_path = RUN_DIR / "daily_cost_sufficient_statistics.csv"
    with sufficient_path.open("x", encoding="utf-8", newline="") as stream:
        sufficient.to_csv(stream, index=False)
        stream.flush()
        os.fsync(stream.fileno())
    by_name = all_records
    candidate_name = StratifiedGate.name
    contrasts = []
    for name, events in by_name.items():
        if name == candidate_name:
            continue
        primary = name in PRIMARY_REFERENCES
        result = _moving_block_interval(by_name[candidate_name], events, familywise_primary=primary)
        cluster = _publisher_cluster_interval(by_name[candidate_name], events)
        contrasts.append({"reference": name, "primary_comparison": primary, **result, **cluster})
    available_contexts = set(pd.DataFrame(by_name[candidate_name])["context"].astype(str))
    context_contrasts = {
        context: _moving_block_interval(
            by_name[candidate_name],
            by_name["validation_selected_source_static"],
            context=context,
        )
        for context in CONTEXTS[:-1]
        if context in available_contexts
    }
    summary_payload = {
        "opening": opening,
        "protocol_hashes": frozen["protocol_hashes"],
        "run_command": "uv run python scripts/sota_sprint/run_mnds_contextual_transfer.py run",
        "budget": budget,
        "label_price": LABEL_PRICE,
        "switch_cost": SWITCH_COST,
        "simulated_label_delay_hours": 24,
        "delay_rows_for_legacy_policies": delay_rows,
        "static_context_decisions": static_decisions,
        "policies": summaries,
        "primary_contrasts": contrasts,
        "context_contrasts_vs_static": context_contrasts,
        "private_raw_records": {
            "path": str(RAW_RECORDS_PATH.relative_to(ROOT)),
            "sha256": file_hash(RAW_RECORDS_PATH),
        },
        "daily_cost_sufficient_statistics": {
            "path": str(sufficient_path.relative_to(ROOT)),
            "sha256": file_hash(sufficient_path),
        },
        "source_code_sha256": {
            str(path.relative_to(ROOT)): file_hash(path) for path in source_files()
        },
        "package_versions": package_versions(),
    }
    summary_path = RUN_DIR / "summary.json"
    write_exclusive(summary_path, summary_payload)
    (RUN_DIR / "RESULTS.md").write_text(render_results(summary_payload), encoding="utf-8")


def smoke() -> None:
    """Exercise method interfaces on Q3 development data; never reads Q4 rows."""
    from prepare_mnds_transfer import load_development_rows

    bundle = pickle.loads(MODEL_PATH.read_bytes())
    models, classes = bundle["models"], bundle["classes"]
    rows = load_development_rows()
    rows = rows.loc[(rows["_time"] >= "2019-07-01") & (rows["_time"] < "2019-10-01")].copy()
    rows = rows.sort_values(["_time", "data_id"], kind="stable").head(500).reset_index(drop=True)
    rows["timestamp"] = pd.to_datetime(rows["_time"], utc=True)
    rows["source"] = rows["source"].astype(str)
    rows["context"] = rows["source"].where(rows["source"].isin(CORE_SOURCES), "other")
    labels = (
        rows["category_level_1"]
        .astype(str)
        .map({name: i for i, name in enumerate(classes)})
        .to_numpy()
    )
    text = rows["title"].astype(str).tolist()
    predictions = np.column_stack(
        [
            models[name][1].predict(models[name][0].transform(text))
            for name in ("incumbent", "challenger")
        ]
    )
    budget = min(200, int(np.floor(0.10 * len(rows))))
    rates = frozen_context_frequencies()
    policies = _build_global_baselines(len(rows), budget, delay=1)
    policies.extend(
        [
            StaticContextPolicy(static_source_decisions()),
            StratifiedGate(horizon=len(rows), context_rates=rates),
        ]
    )
    results = []
    smoke_records = {}
    for policy in policies:
        summary, events = replay_policy(
            policy,
            rows=rows,
            predictions=predictions,
            labels=labels,
            budget=budget,
        )
        if not summary["budget_respected"]:
            raise AssertionError(f"{policy.name} exceeded the smoke budget")
        results.append(policy.name)
        smoke_records[policy.name] = events
    candidate_events = smoke_records[StratifiedGate.name]
    static_events = smoke_records["validation_selected_source_static"]
    _moving_block_interval(candidate_events, static_events)
    _publisher_cluster_interval(candidate_events, static_events)
    for context in CONTEXTS[:-1]:
        if any(event["context"] == context for event in candidate_events):
            _moving_block_interval(candidate_events, static_events, context=context)
    print(
        json.dumps(
            {
                "stage": "development_interface_smoke",
                "rows": len(rows),
                "methods_completed": results,
            }
        )
    )


def render_results(value: dict) -> str:
    lines = [
        "# Publisher-stratified MN-DS replay results",
        "",
        "**Feedback:** simulated 24-hour release delay. All figures are retrospective replay results.",
        "",
        "| Policy | Net / 1,000 | Error | Labels | Label cost | Switches | Switch cost | Promotions | Rollbacks |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in sorted(value["policies"], key=lambda item: item["net_cost"]):
        lines.append(
            f"| {row['policy']} | {row['net_cost_per_1000']:.2f} | {row['prediction_loss']} | "
            f"{row['labels']} | {row['label_expenditure']:.2f} | {row['switches']} | "
            f"{row['switch_expenditure']:.2f} | {row['promotion_count']} | {row['rollback_count']} |"
        )
    lines.extend(
        [
            "",
            "## Candidate paired cost contrasts",
            "",
            "| Reference | Primary | Candidate − reference / 1,000 | 95% block interval | registered interval | Level | publisher-cluster interval |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in value["primary_contrasts"]:
        lines.append(
            f"| {row['reference']} | {row['primary_comparison']} | "
            f"{row['mean_candidate_minus_reference_per_1000']:.2f} | "
            f"[{row['moving_block_ci_95'][0]:.2f}, {row['moving_block_ci_95'][1]:.2f}] | "
            f"[{row['family_interval'][0]:.2f}, {row['family_interval'][1]:.2f}] | "
            f"{100 * row['family_interval_level']:.1f}% | "
            f"[{row['publisher_cluster_ci_95'][0]:.2f}, {row['publisher_cluster_ci_95'][1]:.2f}] |"
        )
    lines.extend(
        [
            "",
            "## Named publisher contrasts vs validation-selected static",
            "",
            "| Publisher | Difference / 1,000 | 95% 7-day interval |",
            "|---|---:|---:|",
        ]
    )
    for context, row in value["context_contrasts_vs_static"].items():
        lines.append(
            f"| {context} | {row['mean_candidate_minus_reference_per_1000']:.2f} | "
            f"[{row['moving_block_ci_95'][0]:.2f}, {row['moving_block_ci_95'][1]:.2f}] |"
        )
    lines.extend(
        [
            "",
            (
                "The publisher-stratified gate is a standard composition, not a new statistical test. "
                "Its e-process interpretation is not asserted for this serial source without a matching "
                "conditional-mean assumption. Source-level cost results are descriptive; a single dataset "
                "does not establish external generalization."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("smoke", "freeze", "run"))
    args = parser.parse_args()
    if args.stage == "smoke":
        smoke()
    elif args.stage == "freeze":
        freeze()
    else:
        run()


if __name__ == "__main__":
    main()
