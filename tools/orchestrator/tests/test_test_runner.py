import shlex
import sys

from formula_orchestrator.test_runner import FormulaTestRunner, TestGateStatus


def command(code: str) -> str:
    return f"{shlex.quote(sys.executable)} -c {shlex.quote(code)}"


def test_passing_command_is_pass(tmp_path):
    result = FormulaTestRunner().run(tmp_path, command("print('ok')"), 5)
    assert result.passed and result.gate_status == TestGateStatus.PASS and result.exit_code == 0


def test_failing_command_is_fail(tmp_path):
    result = FormulaTestRunner().run(tmp_path, command("import sys; print('bad'); sys.exit(3)"), 5)
    assert not result.passed and result.gate_status == TestGateStatus.FAIL and result.exit_code == 3


def test_timeout_is_explicit_and_not_retried(tmp_path):
    result = FormulaTestRunner().run(tmp_path, command("import time; time.sleep(2)"), 0.05)
    assert not result.passed and result.timed_out and result.execution_error == "Test command timed out"


def test_missing_executable_is_failure(tmp_path):
    result = FormulaTestRunner().run(tmp_path, "definitely-not-a-real-formula-test-command", 5)
    assert not result.passed and result.exit_code is None and result.execution_error


def test_credentials_are_removed_from_child_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai-secret")
    monkeypatch.setenv("CODEX_API_KEY", "fake-codex-secret")
    result = FormulaTestRunner().run(tmp_path, command("import os; print(os.getenv('OPENAI_API_KEY', 'missing')); print(os.getenv('CODEX_API_KEY', 'missing'))"), 5)
    assert "missing" in result.stdout
    assert "fake-openai-secret" not in result.stdout and "fake-codex-secret" not in result.stdout


def test_output_is_bounded_and_redacted(tmp_path, monkeypatch):
    secret = "fake-output-secret"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    result = FormulaTestRunner(output_limit=100).run(tmp_path, command(f"print('A' * 1000); print('{secret}')"), 5)
    assert len(result.stdout) <= 150
    assert "[REDACTED]" in result.stdout
    assert secret not in result.stdout

