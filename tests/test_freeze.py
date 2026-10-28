import subprocess

import pytest

from shiftlab.freeze import check_freeze, file_sha256, require_freeze, write_freeze


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "protocol.md").write_bytes(b"protocol\r\nline\r\n")
    (tmp_path / "code.py").write_text("x = 1\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init"],
        cwd=tmp_path,
        check=True,
    )
    return tmp_path


def test_hash_ignores_line_endings(tmp_path):
    (tmp_path / "a").write_bytes(b"one\r\ntwo\r\n")
    (tmp_path / "b").write_bytes(b"one\ntwo\n")
    assert file_sha256(tmp_path / "a") == file_sha256(tmp_path / "b")


def test_freeze_passes_then_detects_change(repo):
    record = repo / "freeze.json"
    write_freeze(
        record,
        experiment="t",
        protocol="protocol.md",
        files=["code.py"],
        seed_blocks=["b"],
        repo_root=repo,
    )
    assert check_freeze(record, repo) == []
    require_freeze(record, repo)
    (repo / "code.py").write_text("x = 2\n")
    problems = check_freeze(record, repo)
    assert any("changed since freeze: code.py" in p for p in problems)
    with pytest.raises(RuntimeError):
        require_freeze(record, repo)


def test_freeze_refuses_missing_files(repo):
    with pytest.raises(FileNotFoundError):
        write_freeze(
            repo / "f.json",
            experiment="t",
            protocol="protocol.md",
            files=["absent.py"],
            seed_blocks=[],
            repo_root=repo,
        )
