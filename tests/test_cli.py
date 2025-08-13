import subprocess
import sys

from adop_manager import __version__


def test_cli_version():
    cmd = [sys.executable, "-m", "adop_manager", "--version"]
    assert (
        subprocess.check_output(cmd).decode().strip()
        == f"adop-manager version: {__version__}"
    )
