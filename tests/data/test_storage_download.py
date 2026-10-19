import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from shiftlab.data.benchmark import evaluate_regression
from shiftlab.data.cli import generate
from shiftlab.data.provenance import sha256
from shiftlab.data.real.download import download
from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.validation import validate_dataset


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
    with (path / "observations.parquet").open("ab") as f:
        f.write(b"corrupt")
    with pytest.raises(ValueError):
        validate_dataset(path)


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
        assert download(url, path).read_bytes() == payload
        assert download(url, path, expected_sha256=sha256(path)) == path
        with pytest.raises(ValueError):
            download(url, path, expected_sha256="0" * 64)
    finally:
        server.shutdown()
        server.server_close()
