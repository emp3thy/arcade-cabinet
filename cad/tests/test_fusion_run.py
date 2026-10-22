"""Tests for cad/fusion_run.py, the launcher that sends a bundled script to
Fusion through FusionHelper's MCP client and exits on the verdict."""
from dataclasses import dataclass

import fusion_run
from fusion_run import main, verdict_from


def test_verdict_from_takes_last_verdict_line():
    s = 'FH_CHECK1 {"a":1}\nFH_VERDICT1 {"status":"fail"}\nnoise\nFH_VERDICT1 {"status":"pass"}\n'
    assert verdict_from(s) == {"status": "pass"}


def test_verdict_from_none_without_line():
    assert verdict_from("hello\n") is None


@dataclass
class _Result:
    success: bool
    message: str
    error: str


class _StubClient:
    result = _Result(True, "", "")
    executed = []

    def __init__(self, url):
        self.url = url

    def initialize(self):
        return {"result": {"serverInfo": {"name": "stub"}}}

    def execute(self, text):
        _StubClient.executed.append(text)
        return _StubClient.result


def _run(monkeypatch, tmp_path, result):
    monkeypatch.setattr(fusion_run, "McpClient", _StubClient)
    _StubClient.result = result
    script = tmp_path / "x.bundled.py"
    script.write_text("def run(_c):\n    pass\n", encoding="utf-8")
    return main([str(script)])


def test_main_exit_0_on_pass(monkeypatch, tmp_path):
    assert _run(monkeypatch, tmp_path, _Result(True, 'FH_VERDICT1 {"status": "pass"}', "")) == 0
    assert _StubClient.executed[-1].startswith("def run")


def test_main_exit_0_on_pass_partial_with_no_failed_check(monkeypatch, tmp_path):
    # a one-body stage: interference and clearance are skipped, nothing failed
    msg = 'FH_VERDICT1 {"status": "pass_partial", "checks": {"constraints": "pass", "interference": "skip", "liveness": "pass"}}'
    assert _run(monkeypatch, tmp_path, _Result(True, msg, "")) == 0


def test_main_exit_2_on_pass_partial_with_a_failed_check(monkeypatch, tmp_path):
    msg = 'FH_VERDICT1 {"status": "pass_partial", "checks": {"constraints": "pass", "liveness": "fail"}}'
    assert _run(monkeypatch, tmp_path, _Result(True, msg, "")) == 2


def test_main_exit_2_on_fail_verdict(monkeypatch, tmp_path):
    assert _run(monkeypatch, tmp_path, _Result(True, 'FH_VERDICT1 {"status": "fail"}', "")) == 2


def test_main_exit_3_on_script_error(monkeypatch, tmp_path):
    assert _run(monkeypatch, tmp_path, _Result(False, "", "Traceback ...")) == 3


def test_main_exit_3_without_verdict_line(monkeypatch, tmp_path):
    assert _run(monkeypatch, tmp_path, _Result(True, "done\n", "")) == 3
