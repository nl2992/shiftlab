"""Generate docs 02_DATASET_DISCOVERY.md and 03_DATASET_ELIGIBILITY.md from the ledger/registry."""

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "docs/paper1_scale25"
rows = list(csv.DictReader(open(D / "DATASET_DISCOVERY_LEDGER.csv", encoding="utf-8")))
reg = json.load(open(D / "DATASET_SOURCE_REGISTRY.json", encoding="utf-8"))
c = reg["counters"]
ex = [r for r in rows if r["origin"] == "existing"]
new = [r for r in rows if r["counted_as_new"] == "yes"]
built = [r for r in rows if r["origin"] == "new-built"]
fails = [json.loads(line) for line in open(ROOT / "outputs/paper1_scale25/data/build_failures.jsonl")] if (ROOT / "outputs/paper1_scale25/data/build_failures.jsonl").exists() else []
dom = Counter(r["domain"] for r in built)
dom_all = Counter(r["domain"] for r in built if r["d1_status"] == "gate-pass")

t = []
t.append("# 02 - Dataset discovery (WS-A)\n")
t.append("Written 2026-11-09. Rules: `DATASET_ELIGIBILITY_PROTOCOL.md`. Ledger: `DATASET_DISCOVERY_LEDGER.csv`; machine-readable: `DATASET_SOURCE_REGISTRY.json`; D1 table: `d1_summary.csv`; build records: `dev_builds/`.\n")
t.append("## Process\n")
t.append("1. Inventory of the 44 existing C4 recipes (the brief said 45; the directory holds 44 source modules plus two shared download helpers). The 26 registered sealed hashes and the 7 eligible fresh-window hashes were recomputed from the arrays and all match; oakland's fresh window was ineligible (27 episodes) and has no sealed array.")
t.append("2. Socrata catalogue harvest (20 query phrases, up to 400 hits each, 2,646 distinct datasets; `harvest_socrata.py`). Datasets updated after 2026-07-01 with a created-like and a closed-like date column (262) were probed by count queries for the DEV (2023-07..2025-07) and CONFIRM (2025-07..2026-07) periods and the date range (`probe_socrata.py`). Counts only; no label statistic was requested.")
t.append("3. Non-Socrata sources were found by direct portal/API checks (S3 listings, EPA AirData, NOAA GHCN, Toronto CKAN, Philadelphia Carto, openFDA, UK DfT) and local files; each was verified as stated in its ledger row. Wild-Time (arXiv, HuffPost, Yearbook) and WILDS image sets were not attempted (text/image featurisation is outside the frozen model pair; no local copy except a CivilComments mirror).")
t.append("4. Recipes were written before building (`scripts/paper1_scale25/data/sources/`), built through `dev_build.py` (a wrapper around the unchanged `c4_build.build`), with raw data in `data/raw/scale25/` and sealed dev losses in `data/scale25_dev/` (neither committed). No CONFIRM data was fetched or built. Failures are kept (below).\n")
t.append("## Counters (kept separate)\n")
t.append("| counter | value |\n|---|---|")
for k, v in c.items():
    if k != "new_by_domain":
        t.append(f"| {k} | {v} |")
t.append("\nNotes on the counters: `new_discovered` counts ledger rows that are not duplicates of an existing recipe; most are Socrata datasets that failed the size rule (D0 criterion 4). `new_d0_eligible` includes the 15 sources with a written recipe; the 4 `pending-review` rows and 4 `dev-only` rows are not built. 'Downloaded' is the number of new sources whose DEV raw data was fetched (13 builds ran; 1 more failed during the build and is listed below).\n")
t.append("## New sources by domain (discovered, all statuses)\n")
t.append("| domain | rows |\n|---|---|")
for k, v in c["new_by_domain"].items():
    t.append(f"| {k} | {v} |")
t.append("\n## New dev builds by domain\n")
t.append("| domain | built | gate-pass |\n|---|---|---|")
for k, v in dom.items():
    t.append(f"| {k} | {v} | {dom_all.get(k, 0)} |")
t.append("\nFamilies with at least one gate-pass dev build: " + ", ".join(sorted(dom_all)) + f" ({len(dom_all)} families; 311 and public-safety/emergency counted separately).\n")
t.append("## Failures (recorded, not repaired)\n")
for f in fails:
    t.append(f"- `{f['id']}`: {f['error']} (label rule not changed)")
t.append("- `usac_erate_invoices`: built, failed the incumbent-error gate (validation incumbent error .505 > .5; disagreement .506). Not repaired.")
t.append("- `uk_stats19_collisions`, `toronto_311`, `philly_permits`, `philly_incidents`: D0-ineligible by metadata (reasons in the ledger).")
t.append("- `la_crime` publisher dataset has no rows after 2024-12, `miamidade_311` changed schema in 2024-26, `denver_311` has no per-year layers after 2023, `pittsburgh_311`/`nyc_collisions`/`nola_311`/`sf_building_permits`/`dallas_animal_shelter`/`minneapolis_311` fall under the 150k CONFIRM rule (counts in `03`).")
t.append("\n## Limits and caveats\n")
t.append("- The Socrata harvest is a sample of the catalogue (top hits per query), not an exhaustive crawl. ArcGIS Hub, CKAN, and non-US portals other than Edmonton/Winnipeg/Calgary/Toronto were not systematically crawled.")
t.append("- Label horizons for new sources (7 days for 311, 600 s for police/EMS, 300 s for fire, 30 days for invoices/work orders) were fixed from domain conventions before building, not tuned.")
t.append("- `epa_aqi_county` and `ghcn_us_rain` use a next-day label, so META delay is 1000 events (about one day), not 100; downstream code must read the per-file delay from the sealed array. `divvy_chicago` and `capitalbikeshare_dc` have labels known at unlock; the delay of 100 is a simulated labelling lag.")
t.append("- Dev test-half summaries in `d1_summary.csv` are development data. `ghcn_us_rain` shows a large test-half incumbent error (about .48 vs .28 on validation), a strong shift within the window. No policy regret is computed here (WS-B).")
t.append("- `data/scale25_dev/` is not covered by `.gitignore` in this worktree; it was never staged.")
(D / "02_DATASET_DISCOVERY.md").write_text("\n".join(t) + "\n", encoding="utf-8")

u = ["# 03 - Dataset eligibility decisions (WS-A)\n",
     "Statuses follow `DATASET_ELIGIBILITY_PROTOCOL.md`. CONFIRM windows were never built or inspected; only counts and date ranges were read.\n",
     "## A. Existing recipes (44)\n",
     "| dataset | domain | D0 | D1 / registration | dev window | confirmation window |\n|---|---|---|---|---|---|"]
for r in ex:
    u.append(f"| {r['dataset_id']} | {r['domain']} | {r['d0_status']} | {r['d1_status'][:70]} | {r['dev_window'][:80]} | {r['confirm_window'][:110]} |")
u.append("\n## B. New sources with a recipe (dev builds)\n")
u.append("| dataset | domain | D1 | episodes | confirmation window | notes |\n|---|---|---|---|---|---|")
for r in built:
    u.append(f"| {r['dataset_id']} | {r['domain']} | {r['d1_status'][:60]} | {r['expected_dev_episodes']} | {r['confirm_window'][:120]} | {r['notes'][:90]} |")
u.append("\n## C. Other new candidates reviewed by hand\n")
u.append("| dataset | D0 | reason |\n|---|---|---|")
for r in new:
    if r["origin"] == "extra-verified" or (r["origin"] == "socrata-probe" and r["d0_status"] in ("pending-review", "dev-only", "eligible") or (r["origin"] == "socrata-probe" and r["task_family"] not in ("-", ""))):
        u.append(f"| {r['dataset_id']} ({r['publisher'][:30]}) | {r['d0_status']} | {r['d0_reason'][:150]} |")
rest = [r for r in new if r["origin"] == "socrata-probe" and r["d0_status"] == "ineligible" and r["task_family"] in ("-", "")]
u.append(f"\n## D. Mechanically screened Socrata probes ({len(rest)} ineligible by size, probe error or non-outcome date pair)\n")
u.append("Full rows with counts are in the ledger (`origin = socrata-probe`). Reasons by type:\n")
for k, v in Counter(r["d0_reason"].split(":")[0] for r in rest).most_common():
    u.append(f"- {k}: {v}")
(D / "03_DATASET_ELIGIBILITY.md").write_text("\n".join(u) + "\n", encoding="utf-8")
print("docs written")
