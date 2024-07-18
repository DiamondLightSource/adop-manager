import asyncio
from argparse import ArgumentParser
from pathlib import Path

from . import __version__
from .app import AdOpManager

__all__ = ["main"]


async def main(args=None):
    parser = ArgumentParser()

    parser.add_argument("--version", "-v", action="version", version=__version__)

    parser.add_argument("name", "--name", "-n", type=str, required=True)
    parser.add_argument(
        "script_call", "--script-call", "-s", type=tuple[str, ...], required=True
    )
    parser.add_argument("log_path", "--log-path", "-l", type=Path, required=True)
    parser.add_argument("config_path", "--config-path", "-c", type=Path, required=True)
    parser.add_argument("mirror1", "--mirror1", "-m1", type=str, required=True)
    parser.add_argument("mirror2", "--mirror2", "-m2", type=str, required=True)
    parser.add_argument(
        "timeout", "--timeout", "-t", type=int, required=False, default=30
    )

    args = parser.parse_args(args)
    AdOpManager(
        args.name,
        args.script_call,
        args.log_path,
        args.config_path,
        args.mirror1,
        args.mirror2,
        args.timeout,
    )


# test with: pipenv run python -m adop_manager
if __name__ == "__main__":
    asyncio.run(main())
