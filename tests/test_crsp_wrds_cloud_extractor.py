import hashlib
import json

from scripts.extract_crsp_ciz_wrds_cloud import build_query, query_hash, verify_completed_year


def test_crsp_query_uses_documented_universe_and_exclusive_year_bounds():
    query = build_query(2024)

    assert query.startswith("SELECT DISTINCT")
    assert "dlycaldt >= DATE '2024-01-01'" in query
    assert "dlycaldt < DATE '2025-01-01'" in query
    assert "securitytype = 'EQTY'" in query
    assert "securitysubtype = 'COM'" in query
    assert "sharetype = 'NS'" in query
    assert "primaryexch IN ('A', 'B', 'I', 'N', 'Q', 'R')" in query
    assert "tradingstatusflg =" not in query
    assert "dlyretmissflg =" not in query


def test_completed_year_is_skipped_only_when_manifest_and_checksum_match(tmp_path):
    year_dir = tmp_path / "year=2024"
    year_dir.mkdir()
    payload = year_dir / "part-0000.csv.gz"
    payload.write_bytes(b"private licensed output placeholder")
    query = build_query(2024)
    manifest = {
        "query_sha256": query_hash(query),
        "row_count": 1,
        "files": [
            {
                "name": payload.name,
                "sha256": hashlib.sha256(payload.read_bytes()).hexdigest(),
            }
        ],
    }
    (year_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    assert verify_completed_year(year_dir, query_hash(query))
    assert not verify_completed_year(year_dir, query_hash(build_query(2023)))

    payload.write_bytes(b"changed")
    assert not verify_completed_year(year_dir, query_hash(query))
