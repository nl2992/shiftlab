"""Registry I/O for B3+ dataset screening.

``dataset_registry.json`` holds one entry per candidate. Entries are created here (all candidate
metadata and the *declared delay* are written before any locked window is read) and then updated
in place by the pipeline. Declared delays are never overwritten once ``declared_at_utc`` is set.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REGISTRY_PATH = HERE / "dataset_registry.json"
OUT_ROOT = ROOT / "docs/promising_directions/results/b3_plus/screening"
PROTOCOL = "docs/promising_directions/B3_PLUS_SCREENING_PROTOCOL.md"

# Streams already in the programme (selected or exposed). Anything in the same family is a duplicate.
EXPOSED_FAMILIES = {
    "spam_katakis": "SUCCESS (existing case 1/5)",
    "rialto": "SUCCESS (existing case 2/5)",
    "weather": "SUCCESS (existing case 3/5)",
    "airlines": "screened in B3, USELESS_NO_HEADROOM",
    "bank": "screened in B3, USELESS_NO_HEADROOM",
    "elec2": "exposed in the programme, USELESS_NO_HEADROOM",
    "criteo": "screened in B3, USELESS_NO_HEADROOM",
    "gas": "exposed in the programme",
}

STATUSES = (
    "QUEUED",
    "SUCCESS",
    "USELESS_INELIGIBLE",
    "USELESS_NO_HEADROOM",
    "USELESS_NO_IMPROVEMENT",
    "USELESS_UNSTABLE",
    "USELESS_DATA_QUALITY",
    "USELESS_DUPLICATE",
    "NOT_RUN",
)

IMPOSED_NO_LATENCY = (
    "No feedback latency is documented for this dataset in its source metadata; the audit rule "
    "(delay in events, capped at 100 so that it fits a 2,000-event episode) is applied at the cap."
)


def now() -> str:
    return datetime.now(UTC).isoformat()


def _delay(value: int, basis: str, why: str) -> dict:
    return {"value": value, "basis": basis, "justification": why, "declared_at_utc": None}


def _cand(rank, did, family, source, url, domain, n_rows, n_features, task, delay, chron, **kw):
    e = {
        "queue_rank": rank,
        "dataset_id": did,
        "family": family,
        "source": source,
        "url": url,
        "loader": kw.pop("loader", "dataset_sources.load"),
        "domain": domain,
        "n_rows": n_rows,
        "n_features": n_features,
        "task": task,
        "declared_delay": delay,
        "chronology": chron,
        "overlap_note": kw.pop("overlap_note", None),
        "status": "QUEUED",
        "status_reason": None,
        "timestamps": {"registered_at_utc": None},
        "files": {},
    }
    e.update(kw)
    return e


def _insects(variant, n, url, rank, status=None, reason=None):
    e = _cand(
        rank,
        f"insects_{variant}",
        "insects",
        f"river.datasets.Insects(variant='{variant}') / USP DS repository",
        url,
        "insect species from optical wingbeat sensor, drift induced by temperature",
        n,
        33,
        "multiclass (6) -> binarised by the single global rule",
        _delay(100, "imposed_cap", IMPOSED_NO_LATENCY),
        {
            "declared_basis": "documented_order",
            "justification": (
                "Souza et al. 2020 release the stream in recording order; concept drift is "
                "introduced by the temperature schedule over the course of the stream. No "
                "timestamp column exists, so order is documented, not independently verifiable."
            ),
            "time_column": None,
            "time_reliable": None,
        },
        overlap_note="Controlled-environment sensor stream; distinct from rialto (video) and weather.",
    )
    if status:
        e["status"], e["status_reason"] = status, reason
    return e


DUP_REASON = (
    "Variant of the Insects family. The goal forbids counting variants of one dataset as "
    "independent cases; the family is represented by insects_abrupt_balanced, and variants are "
    "not screened separately (a second screen of the same generator would be a retry)."
)

SEED = [
    _insects(
        "abrupt_balanced",
        52848,
        "https://drive.google.com/uc?export=download&id=1WQoIuuVgiuXfzv4kvao6XuLQG37V923O&confirm=t",
        1,
    ),
    _cand(
        2,
        "trec07",
        "trec07",
        "river.datasets.TREC07 (TREC 2007 Public Spam Corpus)",
        "https://maxhalford.github.io/files/datasets/trec07p.zip",
        "email spam filtering",
        75419,
        5,
        "binary (spam vs ham), text",
        _delay(100, "imposed_cap", IMPOSED_NO_LATENCY),
        {
            "declared_basis": "documented_order",
            "justification": (
                "The corpus is one inbox delivered 2007-04-08..2007-07-06 and distributed in "
                "arrival order (message index). The Date header is sender-controlled and forged "
                "for spam, so it is NOT used to sort; it is used only to corroborate that file "
                "order tracks time (Spearman >= 0.9 on headers inside the collection span)."
            ),
            "time_column": "date",
            "time_reliable": False,
            "plausible_time_range": ["2007-03-25T00:00:00Z", "2007-08-10T00:00:00Z"],
        },
        overlap_note=(
            "Domain overlap with the existing Katakis spam stream (email spam), but a different "
            "corpus, collection period and feature space (raw text vs preprocessed bag-of-words). "
            "Counted as a distinct dataset only because it is a different source; the domain "
            "overlap must be disclosed in any table that includes both."
        ),
    ),
    _cand(
        3,
        "keystroke",
        "keystroke",
        "river.datasets.Keystroke (CMU DSL-StrongPasswordData)",
        "http://www.cs.cmu.edu/~keystroke/DSL-StrongPasswordData.csv",
        "keystroke dynamics / user authentication",
        20400,
        31,
        "multiclass (51 subjects) -> binarised by the single global rule",
        _delay(100, "imposed_cap", IMPOSED_NO_LATENCY),
        {
            "declared_basis": "ordinal_columns",
            "justification": (
                "File is subject-major (not chronological). sessionIndex (1..8) and rep (1..50) "
                "are genuine ordinal time within subject; sessions were collected on different "
                "days. Across subjects no absolute date is published, so the stream sorts by "
                "(sessionIndex, rep): a session-ordinal chronology, not a calendar one. Declared "
                "as a caveat."
            ),
            "time_column": None,
            "time_reliable": None,
            "ordinal_columns": ["sessionIndex", "rep"],
        },
        overlap_note="Distinct behavioural-biometrics domain.",
    ),
    _cand(
        4,
        "creditcard",
        "creditcard",
        "river.datasets.CreditCard (Kaggle / ULB-Worldline credit-card fraud)",
        "https://maxhalford.github.io/files/datasets/creditcardfraud.zip",
        "card fraud",
        284807,
        30,
        "binary (fraud, 0.17%)",
        _delay(
            100,
            "documented_latency_capped",
            "Fraud confirmation comes from cardholder dispute / investigation, i.e. days, versus "
            "about 1.65 transactions per second here (100 events is about 1 minute). The real "
            "latency far exceeds the cap, so the delay is the cap (100).",
        ),
        {
            "declared_basis": "timestamp_column",
            "justification": "Time = seconds since the first transaction over two days; file is sorted by it.",
            "time_column": "Time",
            "time_reliable": True,
        },
        overlap_note="Distinct finance/fraud domain.",
    ),
    _cand(
        5,
        "beth",
        "beth",
        "river.datasets.BETH (Imperial College data archive)",
        "https://data.hpc.imperial.ac.uk/resolve/?doi=9422&file=4&access=",
        "cybersecurity process/kernel logs (honeypot)",
        2666118,
        11,
        "binary (evil)",
        _delay(100, "imposed_cap", IMPOSED_NO_LATENCY),
        {
            "declared_basis": "none",
            "justification": (
                "Declared conservatively: the per-host log files are concatenated host by host and "
                "the timestamp is not documented as a shared clock. The validator re-checks this "
                "from the data; if a shared monotone clock is found the entry may be upgraded "
                "before the locked window is read."
            ),
            "time_column": "timestamp",
            "time_reliable": None,
        },
        overlap_note="Distinct security domain.",
    ),
    _cand(
        6,
        "http",
        "kdd99",
        "river.datasets.HTTP (KDDCup99 http subset)",
        "https://maxhalford.github.io/files/datasets/kdd99_http.zip",
        "network intrusion",
        567498,
        3,
        "binary (attack 0.39%)",
        _delay(100, "imposed_cap", IMPOSED_NO_LATENCY),
        {
            "declared_basis": "none",
            "justification": (
                "The csv has no connection timestamp and no documentation of event order "
                "(it is a derived subset of KDDCup99, whose subsets are not order-preserving "
                "by contract). Order cannot be verified chronological; none is invented."
            ),
            "time_column": None,
            "time_reliable": None,
        },
        overlap_note="Same source family as smtp (KDDCup99); at most one of the two could count.",
    ),
    _cand(
        7,
        "smtp",
        "kdd99",
        "river.datasets.SMTP (KDDCup99 smtp subset)",
        "https://maxhalford.github.io/files/datasets/smtp.zip",
        "network intrusion",
        95156,
        3,
        "binary (attack 0.03%)",
        _delay(100, "imposed_cap", IMPOSED_NO_LATENCY),
        {
            "declared_basis": "none",
            "justification": "Same as http: no timestamp, no documented order.",
            "time_column": None,
            "time_reliable": None,
        },
        overlap_note="Same source family as http (KDDCup99).",
    ),
    _cand(
        8,
        "malicious_url",
        "malicious_url",
        "river.datasets.MaliciousURL (UCSD, Ma et al. 2009)",
        "http://www.sysnet.ucsd.edu/projects/url/url_svmlight.tar.gz",
        "malicious URL detection",
        2396130,
        3231961,
        "binary",
        _delay(100, "imposed_cap", IMPOSED_NO_LATENCY),
        {
            "declared_basis": "documented_order",
            "justification": "Day-ordered svmlight files (Day0..Day120) in the original release.",
            "time_column": None,
            "time_reliable": None,
        },
        status="NOT_RUN",
        status_reason=(
            "Skipped: 3,231,961 features and a 2.2 GB archive. Train-only featurisation plus LR/"
            "HGB on a 3.2M-dimensional sparse matrix is not CPU-tractable here, and the frozen "
            "protocol forbids per-dataset feature selection or model changes to make it so. Not "
            "downloaded. Counted in the denominator as NOT_RUN, never as a failure of the method."
        ),
    ),
]
for _v, _n, _u in [
    ("abrupt_imbalanced", 355275, "id=1Z9W2_mwawobXeTihZDTDnFOCtfdgmgDa"),
    ("gradual_balanced", 24150, "id=1fepYkDxwMbuoRUaG_fsymSzkuapS4vJp"),
    ("gradual_imbalanced", 143323, "id=1_WJ7lxK2sx1i6kq9Nqv4KrjT0ZXB0QbC"),
    ("incremental_balanced", 57018, "id=1tKQ2KL4m-ACHCVKUDLFPrM4cyhioiOpu"),
    ("incremental_abrupt_balanced", 79986, "id=1-J5WIBN8_F_tomdcrOaiLCxk9nzxtFsf"),
    ("incremental_reoccurring_balanced", 79986, "id=1mSKTSsxzYMjdV005AJqrcMGajuu7dUfW"),
]:
    SEED.append(
        _insects(
            _v,
            _n,
            f"https://drive.google.com/uc?export=download&{_u}&confirm=t",
            1,
            "USELESS_DUPLICATE",
            DUP_REASON,
        )
    )
# Programme-exposed streams listed for completeness of the denominator.
for _did, _why in [
    ("gas", "Exposed in the programme (6-class gas identity); not a fresh case."),
    ("elec2", "Already in B3 (USELESS_NO_HEADROOM, protocol section 6); not a fresh case."),
]:
    SEED.append(
        _cand(
            0,
            f"{_did}_programme",
            _did,
            "programme stream",
            None,
            _did,
            None,
            None,
            "see B3",
            _delay(0, "n/a", "not screened"),
            {"declared_basis": "n/a", "justification": "not screened"},
            status="USELESS_DUPLICATE",
            status_reason=_why,
        )
    )


NOT_FOUND = (
    "Searched OpenML by exact name (powersupply, PowerSupply, power-supply, sensor, Sensor, "
    "SensorStream, sensor_stream, sensor-stream, usenet, Usenet, USENET, usenet1, usenet2) via the "
    "/data/list/data_name API on 2026-11-02: no active dataset. Not locatable, therefore not run; "
    "no substitute was invented."
)


def _openml(rank, did_name, did, name, n, nf, domain, task, chron, delay_why=None, **kw):
    e = _cand(
        rank,
        did_name,
        kw.pop("family", did_name),
        f"OpenML data_id={did} ('{name}') via sklearn.datasets.fetch_openml",
        f"https://www.openml.org/d/{did}",
        domain,
        n,
        nf,
        task,
        _delay(100, "imposed_cap", delay_why or IMPOSED_NO_LATENCY),
        chron,
        **kw,
    )
    e["openml_did"] = did
    e["openml_name"] = name
    return e


EXTRA = [
    _cand(
        7.5, "openml_powersupply", "powersupply", "OpenML (name search)", None, "power supply stream",
        None, None, "multiclass", _delay(100, "imposed_cap", IMPOSED_NO_LATENCY),
        {"declared_basis": "none", "justification": "dataset not located"},
        status="NOT_RUN", status_reason=NOT_FOUND,
    ),
    _cand(
        7.6, "openml_sensor", "sensor", "OpenML (name search)", None, "sensor stream",
        None, None, "multiclass", _delay(100, "imposed_cap", IMPOSED_NO_LATENCY),
        {"declared_basis": "none", "justification": "dataset not located"},
        status="NOT_RUN", status_reason=NOT_FOUND,
    ),
    _cand(
        7.7, "openml_usenet", "usenet", "OpenML (name search)", None, "usenet text stream",
        None, None, "binary", _delay(100, "imposed_cap", IMPOSED_NO_LATENCY),
        {"declared_basis": "none", "justification": "dataset not located"},
        status="NOT_RUN", status_reason=NOT_FOUND,
    ),
    # ---- further candidates added because the named queue ran dry with 0 new successes --------
    _openml(
        9, "openml_eeg_eye_state", 1471, "eeg-eye-state", 14980, 14,
        "EEG eye-state detection (one continuous recording)", "binary (eye open/closed)",
        {
            "declared_basis": "documented_order",
            "justification": (
                "OpenML/UCI description: all data from one continuous 117 s EEG measurement and "
                "'all values are in chronological order with the first measured value at the top'. "
                "No timestamp column, so order is documented but not independently verifiable."
            ),
            "time_column": None,
            "time_reliable": None,
        },
        overlap_note="Distinct biosignal domain. K = 2 locked episodes, so any verdict is LOW-POWER.",
    ),
    _openml(
        10, "openml_ldpa", 1483, "ldpa", 164860, 7,
        "wearable localisation / human-activity recognition", "multiclass (11) -> binarised by rule",
        {
            "declared_basis": "timestamp_column",
            "justification": (
                "INFERENCE (OpenML does not document the transformation): V3 and V4 look like global ranks of the "
                "original UCI timestamp and date-string columns. The file is person-major and NOT in V3 order, "
                "so the stream is sorted by V3 and the validator requires Spearman(V3, V4) >= 0.99 between the two "
                "encodings as corroboration. Post-hoc structural evidence (features and ids only): after sorting by V3, "
                "person id changes only 4 times and the four tags interleave on 99.8% of consecutive rows, i.e. each "
                "recording sequence is contiguous. V1 (person) is kept as a covariate; V3/V4 are excluded from features."
            ),
            "time_column": "V3",
            "time_reliable": True,
            "time_corroboration_column": "V4",
        },
        overlap_note="Distinct HAR domain.",
        load_options={"time_col": "V3", "corroboration_col": "V4", "drop_cols": ["V3", "V4"]},
    ),
    _openml(
        11, "openml_run_or_walk", 40922, "Run_or_walk_information", 88588, 6,
        "smartphone accelerometer/gyroscope activity", "binary (run vs walk)",
        {
            "declared_basis": "none",
            "justification": (
                "The OpenML copy has only the six sensor axes and the label: the Kaggle date/time/"
                "username columns were dropped, and the description does not state row order. "
                "No defensible event order."
            ),
            "time_column": None,
            "time_reliable": None,
        },
        overlap_note="Distinct sensor-HAR domain.",
    ),
    _openml(
        12, "openml_covertype", 150, "covertype", 581012, 54,
        "forest cover type (cartographic)", "multiclass (7)",
        {
            "declared_basis": "none",
            "justification": "Spatial cartographic cells; row order is geographic, not a time stream.",
            "time_column": None,
            "time_reliable": None,
        },
        overlap_note="Named in the task brief as expected-ineligible.",
        load_options={},
    ),
    _openml(
        13, "openml_shuttle", 40685, "shuttle", 58000, 9,
        "Space Shuttle sensor data (Statlog)", "multiclass (7)",
        {
            "declared_basis": "none",
            "justification": "Statlog shuttle is not a documented time-ordered stream; no timestamp.",
            "time_column": None,
            "time_reliable": None,
        },
        overlap_note="Named in the task brief as expected-ineligible.",
        load_options={},
    ),
    _cand(
        14, "sms_spam", "sms_spam", "river.datasets.SMSSpam (UCI SMS Spam Collection)",
        "https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip",
        "SMS spam", 5574, 1, "binary, text", _delay(100, "imposed_cap", IMPOSED_NO_LATENCY),
        {
            "declared_basis": "none",
            "justification": "Collection of messages pooled from several sources; no timestamp or documented order.",
            "time_column": None, "time_reliable": None,
        },
        overlap_note="Spam domain overlap; also 5,574 rows leaves a 2,230-row locked window.",
    ),
    _cand(
        8.5, "uci_occupancy", "uci_occupancy",
        "UCI Occupancy Detection (Candanedo & Feldheim 2016), three files concatenated",
        "https://archive.ics.uci.edu/static/public/357/occupancy+detection.zip",
        "office-room occupancy from environmental sensors", 20560, 5, "binary (occupied)",
        _delay(100, "imposed_cap", IMPOSED_NO_LATENCY),
        {
            "declared_basis": "timestamp_column",
            "justification": (
                "Each row carries a minute-resolution timestamp (2015-02-02 .. 2015-02-18). The three "
                "released files (training, test, test2) are not in time order, so the combined stream "
                "is sorted by timestamp; the validator reports the file-order inversions."
            ),
            "time_column": "date",
            "time_reliable": True,
        },
        overlap_note="Distinct building-sensing domain. Locked window gives K = 4 (LOW-POWER).",
    ),
    _cand(
        15, "river_phishing", "phishing", "river.datasets.Phishing (UCI phishing websites, 1250 rows)",
        None, "phishing websites", 1250, 9, "binary", _delay(100, "imposed_cap", IMPOSED_NO_LATENCY),
        {
            "declared_basis": "none",
            "justification": "As shipped: no timestamp or documented order; 1,250 rows < one 2,000-event episode.",
            "time_column": None, "time_reliable": None,
        },
        overlap_note="Named in the task brief as expected-ineligible.",
    ),
]


def init_registry(path: Path = REGISTRY_PATH) -> dict:
    """Create the registry if missing; otherwise append any SEED/EXTRA entry that is not yet in it.

    Existing entries (and their declared delays and timestamps) are never altered.
    """
    t = now()
    if path.exists():
        r = load(path)
    else:
        r = {
            "schema_version": 1,
            "protocol": PROTOCOL,
            "created_utc": t,
            "note": (
                "Candidate metadata and declared delays are written at registration, before any "
                "locked window is read. See timestamps.* per entry."
            ),
            "candidates": [],
        }
    have = {e["dataset_id"] for e in r["candidates"]}
    added = False
    for e in SEED + EXTRA:
        if e["dataset_id"] in have:
            continue
        e = json.loads(json.dumps(e))
        e["timestamps"]["registered_at_utc"] = t
        if e["declared_delay"]["basis"] != "n/a":
            e["declared_delay"]["declared_at_utc"] = t
        r["candidates"].append(e)
        added = True
    if added or not path.exists():
        save(r, path)
    return r


def load(path: Path = REGISTRY_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(reg: dict, path: Path = REGISTRY_PATH) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(reg, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def get(reg: dict, dataset_id: str) -> dict:
    for e in reg["candidates"]:
        if e["dataset_id"] == dataset_id:
            return e
    raise KeyError(dataset_id)


def add_candidate(reg: dict, entry: dict) -> dict:
    """Append a new candidate (e.g. an OpenML id found by name); declared delay stamped now."""
    if any(e["dataset_id"] == entry["dataset_id"] for e in reg["candidates"]):
        raise ValueError(f"{entry['dataset_id']} already registered")
    entry["timestamps"]["registered_at_utc"] = now()
    entry["declared_delay"]["declared_at_utc"] = now()
    reg["candidates"].append(entry)
    return entry


def stamp(entry: dict, key: str) -> str:
    t = now()
    entry["timestamps"][key] = t
    return t


def declared_delay(entry: dict) -> int:
    """The declared delay, refusing to proceed unless it was declared and the locked window is unread."""
    d = entry["declared_delay"]
    if not d.get("declared_at_utc") or not d.get("justification"):
        raise RuntimeError(f"{entry['dataset_id']}: delay not declared with justification")
    if not 1 <= int(d["value"]) <= 100:
        raise RuntimeError(f"{entry['dataset_id']}: declared delay {d['value']} outside [1, 100]")
    return int(d["value"])
