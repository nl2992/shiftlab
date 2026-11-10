"""Compose DATASET_DISCOVERY_LEDGER.csv and DATASET_SOURCE_REGISTRY.json from the metadata artefacts.

Inputs: outputs/paper1_scale25/data/{existing_inventory,socrata_probe,confirm_avail}.json, dev build records in
docs/paper1_scale25/dev_builds/, curated metadata in new_sources.py. Nothing here reads label statistics of
any CONFIRM window; DEV-window validation statistics come from build records only.
"""

import csv
import glob
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import new_sources as ns  # noqa: E402
from new_sources_batch2 import BUILT2  # noqa: E402

ns.BUILT.update(BUILT2)

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/paper1_scale25/data"
DOCS = ROOT / "docs/paper1_scale25"
COLS = ["dataset_id", "publisher", "url", "license", "domain", "task_family", "parent_source_id", "earliest_ts", "latest_ts",
        "n_eligible_obs", "target_and_loss", "features", "label_delay_rule", "update_cadence", "dev_window", "confirm_window",
        "model_pair", "contract_ok", "leakage_risks", "quality_notes", "expected_dev_episodes", "prepared_hash", "d0_status",
        "d0_reason", "d1_status", "notes"]
EXTRA_COLS = ["org_id", "origin", "counted_as_new", "n_dev_24m", "n_confirm_12m", "confirm_available"]

inv = json.load(open(OUT / "existing_inventory.json"))
probe = json.load(open(OUT / "socrata_probe.json"))
catalog = {(d["domain"], d["id"]): d for d in json.load(open(OUT / "socrata_catalog.json"))}
recipe_text = "\n".join(Path(p).read_text(encoding="utf-8", errors="ignore") for p in glob.glob(str(ROOT / "scripts/qsg_methods_search/c4_sources/*.py")))
rows = []


def gates_failed(g):
    return [k for k, v in g.items() if not v]


# ---------------------------------------------------------------- existing 44
for r in inv:
    m, v = r["meta"], r["validation"]
    n = r["n_after_filter"]
    win = m["window"]
    dev = f"{win[0][:10]}..{win[1][:10]}" if isinstance(win, list) else str(win)
    if "fresh_window" in r:
        fw = r["fresh_window"]
        dev += f"; also fresh {fw[0][:10]}..{fw[1][:10]} (opened {'eligible' if r['fresh_eligible'] else 'ineligible'})"
    c = r.get("confirm") or {}
    if c:
        cw = f"{c['confirm_start']}..{c['confirm_end']}"
        if c["avail"] in ("yes", "yes (estimated)"):
            conf = f"{cw}: available ({c.get('count_kind', '')}{'; n=' + str(c['n_confirm']) if c.get('n_confirm') else ''})"
            ca = "yes"
        elif c["avail"] == "no":
            conf = f"none: {cw} {c['reason']}"
            ca = "no"
        else:
            conf = f"unverified: {cw}: {c['reason']}"
            ca = "unverified"
    else:
        conf, ca = "not assessed (ineligible dev build)", "n/a"
    gf = gates_failed(r["gates"])
    if r["dataset_id"] == "austin_animal":
        d0, d0r = "ineligible", "feature timing: sex_upon_outcome recorded at resolution (D0 criterion 5; pre-opening audit)"
    elif n < 150000:
        d0, d0r = "ineligible", f"size: {n} eligible rows < 150000 (D0 criterion 4)"
    else:
        d0, d0r = "eligible", "metadata criteria pass (recipe audited in c4_build_audit.md)"
    if r.get("registered"):
        d1 = "gate-pass (registered, opened)"
    elif not gf:
        d1 = "gate-pass (not registered)"
    else:
        d1 = "gate-fail: " + ",".join(gf) + f" (disagreement {v['disagreement']:.4f}, err_inc {v['err_incumbent']:.3f}, err_chal {v['err_challenger']:.3f}, episodes {r['episodes']})"
    ph = r.get("registered_hash", "") or r.get("fresh_registered_hash", "") or ""
    notes = []
    if r.get("registered"):
        notes.append(f"registered {r['batch']}; sealed hash re-verified {r['hash_ok']}")
    if "fresh_window" in r:
        notes.append(f"fresh window {r['fresh_window'][0][:10]}..{r['fresh_window'][1][:10]}: {r['fresh_episodes']} episodes, hash re-verified {r.get('fresh_hash_ok')}")
    row = dict(
        dataset_id=r["dataset_id"], publisher=m["publisher"], url=m["url"], license=m["license"], domain=r["domain"], task_family=r["task_family"],
        parent_source_id=r["parent_source_id"], earliest_ts=r["ts_bounds"]["train_old_start"][:19], latest_ts=r["ts_bounds"]["end"][:19],
        n_eligible_obs=n, target_and_loss=f"{m['task']}; 0-1 loss of fixed model pair", features=m["features_note"],
        label_delay_rule=f"{m['delay']} events", update_cadence="", dev_window=dev, confirm_window=conf, model_pair=ns.MODEL_PAIR,
        contract_ok="yes" if not gf else "no (gate fail)", leakage_risks=r["audit"], quality_notes=f"validation: disagreement {v['disagreement']:.4f}, err_incumbent {v['err_incumbent']:.3f}, err_challenger {v['err_challenger']:.3f}, base_rate {v['base_rate_y1']:.3f}; subsample {r['subsample']}",
        expected_dev_episodes=r["episodes"], prepared_hash=ph, d0_status=d0, d0_reason=d0r, d1_status=d1, notes="; ".join(notes),
        org_id=r["org"], origin="existing", counted_as_new="no", n_dev_24m="", n_confirm_12m="", confirm_available=ca)
    rows.append(row)

# ---------------------------------------------------------------- new built / recipe-ready
dev_rec = {Path(p).stem: json.load(open(p)) for p in glob.glob(str(DOCS / "dev_builds/*.json"))}
built_soc = {v["socrata"] for v in ns.BUILT.values() if "socrata" in v}
for i, b in ns.BUILT.items():
    rec = dev_rec.get(i)
    pr = probe.get(f"{b['socrata'][0]}|{b['socrata'][1]}") if "socrata" in b else None
    if rec:
        v = rec["validation"]
        gf = gates_failed(rec["gates"])
        d1 = "gate-pass" if not gf else "gate-fail: " + ",".join(gf)
        qn = f"validation: disagreement {v['disagreement']:.4f}, err_incumbent {v['err_incumbent']:.3f}, err_challenger {v['err_challenger']:.3f}, base_rate {v['base_rate_y1']:.3f}; subsample {rec['subsample']}"
        ph = rec.get("sealed", {}).get("array_content_sha256", "")
        n, eps = rec["n_after_filter"], rec["episodes"]
        e0, e1 = rec["ts_bounds"]["train_old_start"][:19], rec["ts_bounds"]["end"][:19]
        win = rec["meta"]["window"]
        dev = f"{win[0][:10]}..{win[1][:10]}" if isinstance(win, list) else str(win)
        contract = "yes" if not gf else "no (gate fail)"
    else:
        d1, qn, ph, n, eps, e0, e1, dev, contract = "not-built-yet", "", "", "", "", "", "", "", "pending"
    if pr:
        conf = f"2025-07-01..2026-07-01: available (verified count {pr['n_conf']:,}; latest event {pr['max_ts'][:10]})"
        ca, n24, n12c = "yes", pr["n_dev"], pr["n_conf"]
        e0 = e0 or pr["min_ts"][:10]
    else:
        conf = b.get("conf_text", "see notes")
        ca, n24, n12c = "yes (estimated)", "", ""
    rows.append(dict(
        dataset_id=i, publisher=b["publisher"], url=b["url"], license=b["license"], domain=b["domain"], task_family=b["task_family"],
        parent_source_id=b["parent"], earliest_ts=e0, latest_ts=e1, n_eligible_obs=n, target_and_loss=f"binary: {b['label']}; 0-1 loss of fixed model pair",
        features=b["features"], label_delay_rule=b["delay_rule"], update_cadence=b["cadence"], dev_window=dev, confirm_window=conf, model_pair=ns.MODEL_PAIR,
        contract_ok=contract, leakage_risks=b["leak"], quality_notes=qn, expected_dev_episodes=eps, prepared_hash=ph, d0_status="eligible",
        d0_reason="metadata criteria pass; recipe written before the build", d1_status=d1, notes=b["notes"], org_id=b["org"], origin="new-built",
        counted_as_new="yes", n_dev_24m=n24, n_confirm_12m=n12c, confirm_available=ca))

# ---------------------------------------------------------------- Socrata probes (not built)
DOMAIN_KW = [("311|service request|citizen request|customer service|case", "municipal-311"), ("permit|license|licence|inspection|violation|code|zoning", "permits-enforcement"),
             ("crime|police|incident|arrest|crash|collision|citation", "public-safety"), ("fire|ems|ambulance|dispatch", "emergency-services"),
             ("animal|shelter|health|food|restaurant|radon|medic", "health"), ("complaint|insurance|e-rate|contract|tender|procure|invoice", "finance-economics"),
             ("tree|forestry|road|pothole|work order|street|sewer|water|park", "public-works")]


def infer_domain(name):
    for kw, dm in DOMAIN_KW:
        if re.search(kw, name, re.I):
            return dm
    return "other-public-records"


seen_parent = {i: True for i in ns.BUILT}
n_auto = 0
for key, p in sorted(probe.items()):
    dom, rid = key.split("|")
    if (dom, rid) in built_soc:
        continue
    cat = catalog.get((dom, rid), {})
    cur = ns.CURATED.get((dom, rid))
    in_existing = rid in recipe_text
    if "error" in p:
        d0, reason, dmn, fam = "ineligible", f"probe failed: {p['error']}", infer_domain(p["name"]), "-"
    elif cur:
        d0, reason, dmn, fam = cur[0], cur[1], cur[2], cur[3]
    elif in_existing:
        d0, reason, dmn, fam = "duplicate", "dataset id already used by an existing C4 recipe", infer_domain(p["name"]), "-"
    elif p["n_dev"] < 150000:
        d0, reason, dmn, fam = "ineligible", f"size: DEV 24-month count {p['n_dev']:,} < 150,000 (D0 criterion 4)", infer_domain(p["name"]), "-"
    elif p["n_conf"] < 150000:
        d0, reason, dmn, fam = "dev-only", f"CONFIRM 12-month count {p['n_conf']:,} < 150,000: no confirmation window", infer_domain(p["name"]), "-"
    else:
        d0, reason, dmn, fam = "pending-review", "counts pass; label/feature design and outcome-timing review not done", infer_domain(p["name"]), "-"
    n_auto += 1
    big = p.get("n_dev", 0) > 800000
    dev = ("2024-07-01..2025-07-01" if big else "2023-07-01..2025-07-01") if "n_dev" in p else ""
    ok_conf = p.get("n_conf", 0) >= 150000 and (p.get("max_ts") or "") >= "2026-06-30"
    conf = (f"2025-07-01..2026-07-01: available (verified count {p['n_conf']:,})" if ok_conf else
            f"2025-07-01..2026-07-01: none (count {p.get('n_conf', 'n/a')})")
    dup = d0 == "duplicate"
    rows.append(dict(
        dataset_id=f"soc_{dom.split('.')[0] if dom.count('.') < 3 else dom.split('.')[1]}_{rid}".replace("-", "_"), publisher=cat.get("attribution") or dom,
        url=f"https://{dom}/d/{rid}", license=p.get("license") or "see portal terms (not stated in catalog)", domain=dmn, task_family=fam,
        parent_source_id=f"{dom}:{rid}", earliest_ts=(p.get("min_ts") or "")[:19], latest_ts=(p.get("max_ts") or "")[:19], n_eligible_obs=p.get("n_dev", ""),
        target_and_loss=(cur[4] if cur and len(cur) > 4 and cur[4] else "not designed (excluded or not reviewed)"), features="not designed", label_delay_rule="",
        update_cadence="", dev_window=dev, confirm_window=conf, model_pair=ns.MODEL_PAIR, contract_ok="n/a", leakage_risks="", quality_notes=f"{p['name']}; open col {p.get('open_col')}, close col {p.get('close_col')}; catalog views {p.get('views')}",
        expected_dev_episodes="", prepared_hash="", d0_status=d0, d0_reason=reason, d1_status="not-run", notes=("duplicate of an existing recipe; not counted" if dup else ""),
        org_id=cat.get("attribution") or dom, origin="socrata-probe", counted_as_new="no" if dup else "yes", n_dev_24m=p.get("n_dev", ""),
        n_confirm_12m=p.get("n_conf", ""), confirm_available="yes" if ok_conf else "no"))

# ---------------------------------------------------------------- extras
for e in ns.EXTRAS:
    dup = e["d0"] == "duplicate"
    rows.append(dict(
        dataset_id=e["id"], publisher=e["publisher"], url=e["url"], license=e["license"], domain=e["domain"], task_family=e["task_family"], parent_source_id=e["parent"],
        earliest_ts=e["earliest"], latest_ts=e["latest"], n_eligible_obs=e["n_obs"], target_and_loss=e["label"], features=e["features"], label_delay_rule="",
        update_cadence=e["cadence"], dev_window=e["dev"], confirm_window=e["conf"], model_pair=ns.MODEL_PAIR, contract_ok="n/a", leakage_risks=e["leak"], quality_notes="",
        expected_dev_episodes="", prepared_hash="", d0_status=e["d0"], d0_reason=e["reason"], d1_status=e["d1"], notes=e["notes"], org_id=e["org"],
        origin="extra-verified", counted_as_new="no" if dup else "yes", n_dev_24m="", n_confirm_12m="", confirm_available="yes" if e["conf"] and "zips exist" in e["conf"] else "no"))

# ---------------------------------------------------------------- write
ids = [r["dataset_id"] for r in rows]
assert len(ids) == len(set(ids)), [i for i in ids if ids.count(i) > 1][:5]
with open(DOCS / "DATASET_DISCOVERY_LEDGER.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS + EXTRA_COLS)
    w.writeheader()
    w.writerows(rows)


def cnt(pred):
    return sum(1 for r in rows if pred(r))


new = [r for r in rows if r["counted_as_new"] == "yes"]
counters = {
    "existing_recipes": cnt(lambda r: r["origin"] == "existing"),
    "new_discovered": len(new),
    "new_discovered_distinct_parents": len({r["parent_source_id"] for r in new}),
    "new_downloaded_dev": len([r for r in new if r["origin"] == "new-built" and r["dataset_id"] in dev_rec]),
    "new_d0_eligible": cnt(lambda r: r["counted_as_new"] == "yes" and r["d0_status"] == "eligible"),
    "new_dev_only": cnt(lambda r: r["counted_as_new"] == "yes" and r["d0_status"] == "dev-only"),
    "new_pending_review": cnt(lambda r: r["counted_as_new"] == "yes" and r["d0_status"] == "pending-review"),
    "new_ineligible": cnt(lambda r: r["counted_as_new"] == "yes" and r["d0_status"] == "ineligible"),
    "new_dev_built": len(dev_rec),
    "new_dev_gate_pass": sum(1 for r in dev_rec.values() if r["eligible"]),
    "new_dev_gate_pass_with_confirm_window": cnt(lambda r: r["origin"] == "new-built" and r["d1_status"] == "gate-pass" and r["confirm_available"].startswith("yes")),
    "existing_registered_gate_pass": cnt(lambda r: r["origin"] == "existing" and r["d1_status"].startswith("gate-pass (registered")),
    "existing_with_confirm_window": cnt(lambda r: r["origin"] == "existing" and r["confirm_available"] == "yes" and r["d1_status"].startswith("gate-pass (registered")),
    "existing_confirm_unverified": cnt(lambda r: r["origin"] == "existing" and r["confirm_available"] == "unverified"),
}
dom_new = {}
for r in new:
    dom_new.setdefault(r["domain"], 0)
    dom_new[r["domain"]] += 1
counters["new_by_domain"] = dict(sorted(dom_new.items(), key=lambda kv: -kv[1]))
reg = {
    "generated": str(date.today()),
    "protocol": "docs/paper1_scale25/DATASET_ELIGIBILITY_PROTOCOL.md",
    "ledger": "docs/paper1_scale25/DATASET_DISCOVERY_LEDGER.csv",
    "ledger_sha256": hashlib.sha256((DOCS / "DATASET_DISCOVERY_LEDGER.csv").read_bytes()).hexdigest(),
    "counters": counters,
    "window_rules": {
        "registered": "DEV = registered C4 window; CONFIRM = [DEV end, min(DEV end + length, 2026-07-01))",
        "fresh_opened": "DEV includes fresh 2025-26 window; CONFIRM = [fresh end, min(fresh end + registered length, 2026-07-01)); empty -> none",
        "new_socrata": "DEV = 2023-07-01..2025-07-01 (24 months) or its last 12 months if the 24-month count > 800k; CONFIRM = 2025-07-01..2026-07-01",
        "size_rule_confirm": ">= 150000 rows (verified count) else none",
    },
    "datasets": [{k: r[k] for k in COLS + EXTRA_COLS} for r in rows],
}
(DOCS / "DATASET_SOURCE_REGISTRY.json").write_text(json.dumps(reg, indent=1), encoding="utf-8")
print(json.dumps(counters, indent=1))
print(len(rows), "rows")
