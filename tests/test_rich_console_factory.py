import io
import sys
from typing import Any

import pytest
import typer
from typer.main import except_hook
from typer.testing import CliRunner

from tests.utils import needs_rich

runner = CliRunner()


class RecordingFactory:
    """A console factory that records how it was called and captures output."""

    def __init__(self, **console_kwargs: Any) -> None:
        self.buffer = io.StringIO()
        self.stderr_flags: list[bool] = []
        self.console_kwargs = console_kwargs

    def __call__(self, stderr: bool) -> Any:
        from typer.rich_utils import get_rich_console

        self.stderr_flags.append(stderr)
        return get_rich_console(
            stderr=stderr, file=self.buffer, width=80, **self.console_kwargs
        )

    @property
    def output(self) -> str:
        return self.buffer.getvalue()


@needs_rich
def test_help_is_printed_to_factory_console():
    factory = RecordingFactory()
    app = typer.Typer(rich_console_factory=factory)

    @app.command()
    def main(name: str):
        print(f"Hello {name}")

    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert factory.stderr_flags == [False]
    assert "Usage" in factory.output
    assert "Show this message and exit" in factory.output
    assert "Usage" not in result.output


@needs_rich
def test_usage_error_is_printed_to_factory_console():
    factory = RecordingFactory()
    app = typer.Typer(rich_console_factory=factory)

    @app.command()
    def main(name: str):
        print(f"Hello {name}")  # pragma: no cover

    result = runner.invoke(app, [])
    assert result.exit_code == 2
    assert factory.stderr_flags == [True]
    assert "Missing argument" in factory.output
    assert "Missing argument" not in result.output


@needs_rich
def test_abort_is_printed_to_factory_console():
    factory = RecordingFactory()
    app = typer.Typer(rich_console_factory=factory)

    @app.command()
    def main():
        raise typer.Abort()

    result = runner.invoke(app, [])
    assert result.exit_code == 1
    assert factory.stderr_flags == [True]
    assert "Aborted" in factory.output
    assert "Aborted" not in result.output


@needs_rich
def test_pretty_exception_is_printed_to_factory_console(monkeypatch):
    monkeypatch.delenv("TYPER_STANDARD_TRACEBACK", raising=False)
    monkeypatch.delenv("_TYPER_STANDARD_TRACEBACK", raising=False)
    # Calling the app directly installs Typer's excepthook, restore it afterwards
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    factory = RecordingFactory()
    app = typer.Typer(rich_console_factory=factory)

    @app.command()
    def main():
        raise RuntimeError("boom")

    # Typer.__call__ is what attaches the exception config used by except_hook,
    # so call the app directly instead of going through the CliRunner
    with pytest.raises(RuntimeError) as exc_info:
        app([], standalone_mode=False)
    exc = exc_info.value

    except_hook(type(exc), exc, exc.__traceback__)

    assert factory.stderr_flags == [True]
    assert "Traceback" in factory.output
    assert "RuntimeError" in factory.output
    assert "boom" in factory.output


@needs_rich
def test_sub_app_inherits_root_factory():
    factory = RecordingFactory()
    app = typer.Typer(rich_console_factory=factory)
    sub_app = typer.Typer()

    @sub_app.command()
    def hello(name: str):
        print(f"Hello {name}")  # pragma: no cover

    @sub_app.command()
    def bye():
        print("Bye")  # pragma: no cover

    app.add_typer(sub_app, name="sub")

    result = runner.invoke(app, ["sub", "--help"])
    assert result.exit_code == 0
    assert "hello" in factory.output
    assert "hello" not in result.output

    result = runner.invoke(app, ["sub", "hello", "--help"])
    assert result.exit_code == 0
    assert factory.stderr_flags == [False, False]
    assert "Usage: root sub hello" in factory.output
    assert "Usage" not in result.output


@needs_rich
def test_factory_can_return_plain_console():
    """A console without Typer's theme must still render help without errors."""
    from typer.rich_utils import Console

    buffer = io.StringIO()
    app = typer.Typer(rich_console_factory=lambda stderr: Console(file=buffer))

    @app.command()
    def main(name: str, verbose: bool = False):
        print(f"Hello {name}")  # pragma: no cover

    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in buffer.getvalue()
    assert "--verbose" in buffer.getvalue()

    result = runner.invoke(app, [])
    assert result.exit_code == 2
    assert "Missing argument" in buffer.getvalue()


@needs_rich
def test_default_output_unchanged_without_factory():
    app = typer.Typer()

    @app.command()
    def main(name: str):
        print(f"Hello {name}")  # pragma: no cover

    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output

    result = runner.invoke(app, [])
    assert result.exit_code == 2
    assert "Missing argument" in result.output


@needs_rich
def test_get_rich_console_keeps_theme_and_applies_overrides():
    from typer.rich_utils import (
        STYLE_OPTION,
        _get_rich_console,
        get_rich_console,
        get_traceback,
    )

    console = get_rich_console(stderr=True, width=42, no_color=True)
    assert console.stderr is True
    assert console.width == 42
    assert console.no_color is True
    assert str(console.get_style("option")) == STYLE_OPTION

    default = get_rich_console()
    assert default.stderr is False
    assert default.get_style("option") == console.get_style("option")

    # Backwards compatible private alias
    assert _get_rich_console is get_rich_console
    assert get_traceback  # still exported


@needs_rich
def test_typer_command_and_group_accept_factory():
    from typer.core import TyperCommand, TyperGroup

    factory = RecordingFactory()
    command = TyperCommand(name="cmd", rich_console_factory=factory)
    group = TyperGroup(name="grp", rich_console_factory=factory)
    assert command.rich_console_factory is factory
    assert group.rich_console_factory is factory
    assert TyperCommand(name="cmd").rich_console_factory is None
    assert TyperGroup(name="grp").rich_console_factory is None
