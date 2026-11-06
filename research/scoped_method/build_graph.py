#!/usr/bin/env python3
"""Build the scoped ShiftLab Graphify map from the audited file registry.

Run from the worktree root with the Graphify Python environment:
  uv tool run --from graphifyy python research/scoped_method/build_graph.py

The semantic fragment is produced by Graphify's installed extraction skill and
must exist at graphify-out/.graphify_semantic.json before this script runs.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from graphify.analyze import god_nodes, suggest_questions, surprising_connections
from graphify.build import build_from_json
from graphify.cluster import cluster, score_all
from graphify.detect import detect
from graphify.export import to_json
from graphify.extract import extract
from graphify.report import generate

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "graphify-out"
CODE_ROOTS = [
    "src/shiftlab",
    "scripts/failure_atlas_v2",
    "scripts/failure_atlas_v2_flq",
    "scripts/sota_sprint",
    "scripts/promising_directions/sota",
]
EXACT_CODE = [
    "tests/test_atlas_v2_qce.py",
    "tests/test_failure_atlas.py",
    "tests/failure_atlas_v2/test_restart_monitor.py",
    "tests/failure_atlas_v2/test_regimes.py",
    "tests/promising_directions/test_sota_simulator.py",
    "tests/sota_sprint/test_fam_a.py",
    "tests/sota_sprint/test_fam_b.py",
    "tests/sota_sprint/test_fam_c.py",
]
SEMANTIC = [
    "docs/research_charter.md",
    "docs/failure_atlas_v2_flq/protocol.md",
    "docs/failure_atlas_v2_flq/results/selected_mechanism.md",
    "docs/failure_atlas_v2_flq/results/REPORT.md",
    "docs/failure_atlas_v2_flq/results/validation_synthetic.md",
    "docs/failure_atlas_v2_flq/results/validation_real.md",
    "docs/failure_atlas_v2_flq/results/comparator_validity_audit_20261105.md",
    "docs/sota_sprint/novelty_audit.md",
    "docs/sprint2/novelty/NOVELTY.md",
    "docs/sprint2/wp1/RESULTS.md",
    "docs/sprint2/wp2/BENCHMARK.md",
    "docs/sprint2/SOTA_BENCHMARK_AUDIT.md",
    "docs/sprint2/REPRODUCIBILITY.md",
    "data/atlas_v2_losses/README.md",
]


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    code_paths: set[Path] = set()
    for rel in CODE_ROOTS:
        folder = ROOT / rel
        code_paths.update(p.resolve() for p in folder.rglob("*.py") if p.is_file())
    code_paths.update((ROOT / rel).resolve() for rel in EXACT_CODE)
    semantic_paths = [(ROOT / rel).resolve() for rel in SEMANTIC]
    missing = [str(p) for p in [*code_paths, *semantic_paths] if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing registered Graphify inputs: " + ", ".join(missing))

    full = detect(ROOT)
    selected = code_paths | set(semantic_paths)
    detection = dict(full)
    detection["files"] = {
        kind: [f for f in values if Path(f).resolve() in selected]
        for kind, values in full.get("files", {}).items()
    }
    for kind in ("code", "document", "paper", "image", "video"):
        detection["files"].setdefault(kind, [])
    detection["total_files"] = sum(map(len, detection["files"].values()))
    detection["total_words"] = sum(
        len(Path(f).read_text(encoding="utf-8", errors="ignore").split())
        for values in detection["files"].values()
        for f in values
    )
    detection["skipped_sensitive"] = []
    detection["unclassified"] = []
    detection["walk_errors"] = []
    detection["scope"] = "curated research methods, evidence, and tests"
    (OUT / ".graphify_detect.json").write_text(
        json.dumps(detection, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    ast = extract(sorted(code_paths), cache_root=ROOT, root=ROOT)
    (OUT / ".graphify_ast.json").write_text(
        json.dumps(ast, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    semantic_path = OUT / ".graphify_semantic.json"
    if not semantic_path.is_file():
        raise FileNotFoundError(
            f"Graphify semantic extraction is missing: {semantic_path}; "
            "finish the registered document extraction first."
        )
    semantic = json.loads(semantic_path.read_text(encoding="utf-8"))

    nodes: list[dict] = []
    seen: set[str] = set()
    for node in [*ast.get("nodes", []), *semantic.get("nodes", [])]:
        if node["id"] not in seen:
            nodes.append(node)
            seen.add(node["id"])
    extraction = {
        "nodes": nodes,
        "edges": [*ast.get("edges", []), *semantic.get("edges", [])],
        "hyperedges": semantic.get("hyperedges", []),
        "input_tokens": semantic.get("input_tokens", 0),
        "output_tokens": semantic.get("output_tokens", 0),
    }
    (OUT / ".graphify_extract.json").write_text(
        json.dumps(extraction, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    graph = build_from_json(extraction, root=ROOT, directed=True)
    if graph.number_of_nodes() == 0:
        raise RuntimeError("Graphify extraction yielded no nodes; no output was written.")
    communities = cluster(graph)
    cohesion = score_all(graph, communities)
    gods = god_nodes(graph)
    surprises = surprising_connections(graph, communities)
    labels = {cid: f"Community {cid}" for cid in communities}
    questions = suggest_questions(graph, communities, labels)
    to_json(
        graph,
        communities,
        str(OUT / "graph.json"),
        force=True,
        built_at_commit=git_head(),
        community_labels=labels,
    )
    report = generate(
        graph,
        communities,
        cohesion,
        labels,
        gods,
        surprises,
        detection,
        {"input": extraction["input_tokens"], "output": extraction["output_tokens"]},
        str(ROOT),
        suggested_questions=questions,
        built_at_commit=git_head(),
    )
    (OUT / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")
    analysis = {
        "communities": {str(k): v for k, v in communities.items()},
        "cohesion": {str(k): v for k, v in cohesion.items()},
        "gods": gods,
        "surprises": surprises,
        "questions": questions,
    }
    (OUT / ".graphify_analysis.json").write_text(
        json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(
        f"Graphify {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges, "
        f"{len(communities)} communities; commit {git_head()}; "
        f"scope {detection['total_files']} files / {detection['total_words']} words"
    )


if __name__ == "__main__":
    main()
