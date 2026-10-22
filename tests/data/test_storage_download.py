import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import pytest

from shiftlab.data.benchmark import evaluate_regression
from shiftlab.data.cli import generate
from shiftlab.data.provenance import commit, sha256
from shiftlab.data.real.adapters import standardize
from shiftlab.data.real.download import download
from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.storage import save_dataset
from shiftlab.data.validation import validate_dataset


def _one_row(sample_id, split, time):
    frame = standardize(np.array([[1.0, 2.0]]), np.array([3.0]), "domain-a", "fixture")
    frame["sample_id"] = sample_id
    frame["split"] = split
    frame["prediction_time"] = time
    frame["metadata"] = '{"source":"fixture"}'
    return frame


@pytest.mark.parametrize(
    ("chunks", "message"),
    [
        (
            [(_one_row("same", "train", 1), None), (_one_row("same", "test", 3), None)],
            "unique across Parquet row groups",
        ),
        (
            [
                (_one_row("validation-first", "validation", 1), None),
                (_one_row("train-later", "train", 3), None),
            ],
            "reversed across row groups",
        ),
    ],
)
def test_storage_rejects_cross_row_group_invariant_violations(tmp_path, chunks, message):
    provenance = {
        "publisher": "fixture",
        "source_url": "local://fixture",
        "citation": "fixture",
        "license": "fixture",
        "permitted_use": "test only",
    }
    with pytest.raises(ValueError, match=message):
        save_dataset(chunks, "chunk-integrity", tmp_path, provenance, {})
    assert not list((tmp_path / "manifests").glob("*.json"))


def test_storage_integrity_and_immutability(tmp_path):
    config = SyntheticConfig(n=100, chunk_size=32, output=str(tmp_path))
    path = generate(config)
    before = (path / "dataset_manifest.json").read_bytes()
    assert generate(config) == path
    assert before == (path / "dataset_manifest.json").read_bytes()
    assert validate_dataset(path)["rows"] == 100
    manifest = json.loads(before)
    assert manifest["oracle_file"].startswith("evaluator_only/")
    assert manifest["source_hash"]
    assert manifest["code_commit"] == commit()
    assert manifest["processing_config"]["seed"] == config.seed
    assert manifest["files"]["observations.parquet"] == sha256(path / "observations.parquet")
    assert manifest["files"]["evaluator_only/oracle.parquet"] == sha256(
        path / "evaluator_only/oracle.parquet"
    )
    with (path / "observations.parquet").open("ab") as f:
        f.write(b"corrupt")
    with pytest.raises(ValueError):
        validate_dataset(path)


def test_chunk_size_is_part_of_immutable_dataset_identity(tmp_path):
    first = generate(SyntheticConfig(n=100, seed=27, chunk_size=32, output=str(tmp_path)))
    second = generate(SyntheticConfig(n=100, seed=27, chunk_size=64, output=str(tmp_path)))
    assert first != second
    first_manifest = json.loads((first / "dataset_manifest.json").read_text())
    second_manifest = json.loads((second / "dataset_manifest.json").read_text())
    assert first_manifest["version"] != second_manifest["version"]
    assert first_manifest["processing_config"]["chunk_size"] == 32
    assert second_manifest["processing_config"]["chunk_size"] == 64


def test_shared_dataset_serves_three_papers(tmp_path):
    path = generate(SyntheticConfig(n=600, delay=3, missing=0.1, output=str(tmp_path)))
    for paper in [1, 2, 3]:
        metrics = evaluate_regression(path, paper, window=30)
        assert metrics and all(row["paper"] == paper for row in metrics)
        assert all(row["mse"] >= 0 for row in metrics)
        assert all(0 <= row["coverage"] <= 1 for row in metrics)


def test_resumable_download_and_receipt(tmp_path):
    payload = b"known payload" * 100

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            offset = int(self.headers.get("Range", "bytes=0-").split("=")[1].split("-")[0])
            self.send_response(206 if offset else 200)
            self.send_header("ETag", '"fixture-v1"')
            self.send_header("Content-Length", str(len(payload) - offset))
            if offset:
                self.send_header(
                    "Content-Range", f"bytes {offset}-{len(payload) - 1}/{len(payload)}"
                )
            self.end_headers()
            self.wfile.write(payload[offset:])

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        path = tmp_path / "payload.bin"
        path.with_suffix(".bin.part").write_bytes(payload[:12])
        url = f"http://127.0.0.1:{server.server_port}/data"
        path.with_suffix(".bin.part.json").write_text(
            json.dumps({"url": url, "etag": '"fixture-v1"'})
        )
        assert download(url, path).read_bytes() == payload
        assert download(url, path, expected_sha256=sha256(path)) == path
        with pytest.raises(ValueError):
            download(url, path, expected_sha256="0" * 64)
    finally:
        server.shutdown()
        server.server_close()
