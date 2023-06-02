from typer import Typer

roadmap_cli = Typer(no_args_is_help=True)


@roadmap_cli.command()
def todo(goal: str):
    """List roadmap tasks which are not blocked by any other task."""
