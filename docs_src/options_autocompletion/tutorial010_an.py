from typing import List

import click
import typer
from click.shell_completion import CompletionItem
from typing_extensions import Annotated

valid_completion_items = [
    ("Camila", "The reader of books."),
    ("Carlos", "The writer of scripts."),
    ("Sebastian", "The type hints guy."),
]


def complete_name(ctx: typer.Context, param: click.Parameter, incomplete: str):
    names = (ctx.params.get(param.name) if param.name else []) or []
    for name, help_text in valid_completion_items:
        if name.startswith(incomplete) and name not in names:
            yield CompletionItem(name, help=help_text)


app = typer.Typer()


@app.command()
def main(
    name: Annotated[
        List[str],
        typer.Option(help="The name to say hi to.", autocompletion=complete_name),
    ] = ["World"],
    greeter: Annotated[
        List[str],
        typer.Option(help="Who are the greeters?.", autocompletion=complete_name),
    ] = [],
):
    for n in name:
        print(f"Hello {n}, from {' and '.join(greeter)}")


if __name__ == "__main__":
    app()