import typer


def get_console(stderr: bool):
    # Import inside the function, so Rich is only loaded when something is printed
    from typer.rich_utils import get_rich_console

    return get_rich_console(stderr=stderr, width=60)


app = typer.Typer(rich_console_factory=get_console)


@app.command()
def create(username: str):
    """
    Create a new user.
    """
    print(f"Creating user: {username}")


if __name__ == "__main__":
    app()
