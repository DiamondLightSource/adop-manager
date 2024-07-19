import asyncio
from functools import wraps
from pathlib import Path
from typing import Annotated

import typer

from . import __version__
from .app import AdOpManager

__all__ = ["main"]

app = typer.Typer()


def run_async(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


@app.command("version")
def version():
    """
    Print out the version of the AdOp Manager.
    """
    print(__version__)


@app.command("run")
@run_async
async def adop_manager_app(
    name: Annotated[str, typer.Argument()],
    script_call: Annotated[
        str,
        typer.Argument(
            help='If the script call has multiple arguments, enclose in quote marks, e.g. "python arg1 arh2"'
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


def main() -> None:
    app()


# test with: python -m adop_manager
if __name__ == "__main__":
    main()
