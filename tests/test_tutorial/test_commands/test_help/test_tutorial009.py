import subprocess
import sys

from typer.testing import CliRunner

from docs_src.commands.help import tutorial009_py310 as mod

app = mod.app

runner = CliRunner()


def test_help_uses_custom_console_width():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output
    assert "Create a new user" in result.output
    assert max(len(line) for line in result.output.splitlines()) <= 60


def test_error_uses_custom_console_width():
    result = runner.invoke(app, [])
    assert result.exit_code == 2
    assert "Missing argument" in result.output
    assert max(len(line) for line in result.output.splitlines()) <= 60


def test_call():
    result = runner.invoke(app, ["Morty"])
    assert result.exit_code == 0
    assert "Creating user: Morty" in result.output


def test_script():
    result = subprocess.run(
        [sys.executable, "-m", "coverage", "run", mod.__file__, "--help"],
        capture_output=True,
        encoding="utf-8",
    )
    assert "Usage" in result.stdout
