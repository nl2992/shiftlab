import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import requests

from shiftlab.data.real.download import download


@contextmanager
def server_for(respond):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            respond(self)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/payload"
    finally:
        server.shutdown()
        server.server_close()


def test_unvalidated_partial_restarts_instead_of_splicing(tmp_path):
    def respond(handler):
        assert handler.headers.get("Range") is None
        handler.send_response(200)
        handler.send_header("Content-Length", "8")
        handler.end_headers()
        handler.wfile.write(b"new data")

    with server_for(respond) as url:
        path = tmp_path / "raw.bin"
        path.with_suffix(".bin.part").write_bytes(b"old prefix")
        assert download(url, path).read_bytes() == b"new data"


@pytest.mark.parametrize("status", [200, 206])
def test_changed_source_restarts_or_rejects(tmp_path, status):
    def respond(handler):
        assert handler.headers["If-Range"] == '"old"'
        assert handler.headers["Range"] == "bytes=3-"
        handler.send_response(status)
        handler.send_header("ETag", '"new"')
        handler.send_header("Content-Length", "3" if status == 206 else "6")
        if status == 206:
            handler.send_header("Content-Range", "bytes 3-5/6")
        handler.end_headers()
        handler.wfile.write(b"new" if status == 206 else b"newnew")

    with server_for(respond) as url:
        path = tmp_path / "raw.bin"
        path.with_suffix(".bin.part").write_bytes(b"old")
        path.with_suffix(".bin.part.json").write_text(json.dumps({"url": url, "etag": '"old"'}))
        if status == 206:
            with pytest.raises(ValueError, match="validator changed"):
                download(url, path)
            assert not path.exists()
            assert path.with_suffix(".bin.part").read_bytes() == b"old"
        else:
            assert download(url, path).read_bytes() == b"newnew"


@pytest.mark.parametrize("mode", ["budget", "truncated"])
def test_invalid_payload_never_published(tmp_path, mode):
    def respond(handler):
        handler.send_response(200)
        handler.send_header("Content-Length", "100")
        handler.end_headers()
        handler.wfile.write(b"short")

    with server_for(respond) as url:
        path = tmp_path / "raw.bin"
        with pytest.raises((ValueError, requests.RequestException)):
            download(url, path, max_bytes=20 if mode == "budget" else 200, retries=1)
        assert not path.exists()
        assert not path.with_suffix(".bin.receipt.json").exists()
