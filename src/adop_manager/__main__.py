import asyncio
import logging
from functools import wraps
from pathlib import Path
from typing import Annotated

import typer
from rich.logging import RichHandler

from . import __version__
from .app import AdOpManager

__all__ = ["main"]

app = typer.Typer(pretty_exceptions_show_locals=False)


def run_async(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


def version_callback(value: bool):
    if value:
        print(f"adop-manager version: {__version__}")
        raise typer.Exit()


def log_level(level: str):
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(omit_repeated_times=False, markup=True)],
    )


@app.command("run")
@run_async
async def adop_manager_app(
    name: Annotated[str, typer.Argument()],
    script_call: Annotated[
        str,
        typer.Argument(
            help='If the script call has multiple arguments, enclose in quote marks, \
e.g. "python arg1 arg2"'
        ),
    ],
    log_path: Annotated[Path, typer.Argument()],
    config_path: Annotated[Path, typer.Argument()],
    mirror1: Annotated[str, typer.Argument()],
    mirror2: Annotated[str, typer.Argument()],
    timeout: Annotated[int, typer.Argument()] = 30,
):
    """
    Run the AdOp Manager.
    """
    adop_manager = AdOpManager(
        name,
        script_call,
        log_path,
        config_path,
        mirror1,
        mirror2,
        timeout,
    )

    await adop_manager.log_script()


# This is the default behaviour when no command provided
@app.callback(invoke_without_command=True)
def main(
    version: Annotated[
        bool | None, typer.Option("--version", callback=version_callback)
    ] = None,
    loglevel: Annotated[
        str,
        typer.Option(
            "--log-level",
            help="Set log level to INFO, DEBUG, WARNING, ERROR or CRITICAL",
            case_sensitive=False,
            callback=log_level,
        ),
    ] = "INFO",
) -> None:
    """Default function called from cmd line tool."""

    pass


# test with: python -m adop_manager
if __name__ == "__main__":
    app()
