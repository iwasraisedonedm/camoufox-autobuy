"""Operator CLI."""

import typer
from rich.console import Console

from autobuy.settings import get_settings

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def doctor() -> None:
    """Show non-sensitive configuration readiness."""
    settings = get_settings()
    console.print(f"environment: {settings.environment}")
    console.print("database: configured")
    console.print("redis: configured")
    console.print(
        "internal service auth: "
        + ("configured" if settings.internal_service_token else "not configured")
    )


if __name__ == "__main__":
    app()
