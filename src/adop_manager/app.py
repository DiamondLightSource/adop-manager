import asyncio
import json
import logging
import signal
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
from aioca import caget, caput
from softioc import builder


class AdOpManager:
    def __init__(
        self,
        device_name: str,
        script_call: str | tuple[str],
        log_path: str,
        config_path: str,
        mirror_1: str,
        mirror_2: str,
        ioc_status_timeout: int = 30,
    ):
        self.device_name = device_name
        self.script_call = script_call
        self.log_path = Path(log_path)
        self.config_path = config_path
        self.mirror1 = mirror_1
        self.mirror2 = mirror_2
        self.ioc_status_timeout = ioc_status_timeout

        self.logger = logging.getLogger(__name__)

        if isinstance(script_call, tuple):
            self.script_call = " ".join(script_call)
        else:
            self.script_call = script_call
        self.file_error = False

        self.mirror_prefix = (mirror_1, mirror_2)

        try:
            with open(config_path, "r") as f:
                self.maps: dict[str, Any] = json.load(f)
        except IOError:
            self.file_error = True
            self.maps = {}

        self.map_config = None

        self.restart_iocs = None

        self.process: subprocess.Popen | None = None
        self.return_status = None

        self.log_file = None
        if self.log_path.exists():
            self.stdout = f"{log_path}/stdout.log"
            self.stderr = f"{log_path}/stderr.log"

        self.create_pvs()
        self.logger.info(f"Created ScriptManager: {self.device_name}")

    def create_pvs(self):
        builder.SetDeviceName(self.device_name)
        initial_status = "Ready"
        if self.file_error:
            initial_status = "File read error"
        self.status_string = builder.stringOut(
            "STATUSSTRING", PINI="YES", initial_value=initial_status
        )

        self.status = builder.mbbOut(
            "STATUS", ZRST="READY", ONST="RUNNING", TWST="ERROR", PINI="YES"
        )

        self.progress = builder.longIn("PROGRESS", PINI="YES", initial_value=0)

        self.run = builder.boolOut(
            "RUN",
            ZNAM="Done",
            ONAM="Busy",
            DISA=int(self.file_error),
            on_update=self.launch_script,
        )

        self.stop = builder.boolOut(
            "STOP",
            ZNAM="Done",
            ONAM="Busy",
            DISA=int(self.file_error),
            on_update=self.terminate_script,
            initial_value=0,
        )

        self.kill = builder.boolOut(
            "KILL",
            ZNAM="DONE",
            ONAM="Busy",
            DISA=int(self.file_error),
            on_update=self.kill_script,
        )

        self.apply_config = builder.boolOut(
            "APPLY_CONFIG",
            ZNAM="Done",
            ONAM="Busy",
            DISA=int(self.file_error),
            on_update=self.load_maps,
        )

        self.reset_mirrors = builder.boolOut(
            "RESET", ZNAM="Done", ONAM="Busy", on_update=self.do_mirror_reset
        )

        if self.file_error:
            self.optics_menu = builder.mbbOut("SETUP", ZRST="File error", DISA=1)
            self.optics_menu_strings = None
            self.logger.error("Can't load condensers array - file error")
        else:
            # There doesn't seem to be a way to access the mbbOut string fields after initialisation, only the VAL field, so
            # we cache the array of condenser strings in the order we set the menu fields so the indexing will be correct
            condensers: list[str] = self.maps["std_masks"].keys()
            assert (
                len(condensers) == 4
            ), f"Problem loading condensers array - expected 4 elements, got {condensers}"
            self.optics_menu = builder.mbbOut(
                "SETUP",
                ZRST=condensers[0],
                ONST=condensers[1],
                TWST=condensers[2],
                THST=condensers[3],
                on_update=self.set_map_config,
            )
            self.optics_menu_strings = condensers

        self.algorithm_menu = builder.mbbOut(
            "ALGORITHM", ZRST="ADAM", ONST="SPGD", TWST="BAYES"
        )
        self.mirror_menu = builder.mbbOut(
            "MIRROR",
            ZRST="DM1 Coarse",
            ONST="DM1 Fine",
            TWST="DM2 Coarse",
            THST="DM2 Fine",
        )

        self.arrayData = builder.WaveformOut("MERIT", length=10000)
        self.arrayData = builder.WaveformOut("POWER", length=10000)

        builder.UnsetDevice()

    def is_running(self) -> bool:
        if self.process is not None:
            # if self.process.poll() is not None:
            self.return_status = self.process.poll()
            return True if self.return_status is None else False

        # If process object is None or poll() returns None, it is not running
        else:
            return False

    async def log_script(self) -> None:
        while True:
            self.logger.info("Polling log loop")
            if self.process is not None:
                assert self.process.stdout is not None
                assert self.process.stderr is not None
                out = self.process.stdout.read().decode()
                err = self.process.stderr.read().decode()

                if self.log_file is not None:
                    with (
                        open(self.stdout, "w") as stdout,
                        open(self.stderr, "w") as stderr,
                    ):
                        stdout.write(out)
                        stdout.flush()

                        stderr.write(err)
                        stderr.flush()

                if len(out) > 0:
                    for line in out.split("\n"):
                        if len(line.strip()) > 0:
                            self.logger.info(f"{self.process.pid}: {line}")
                if len(err) > 0:
                    for line in err.split("\n"):
                        if len(line.strip()) > 0:
                            self.logger.warn(f"{self.process.pid}: {line}")
            await asyncio.sleep(10.0)

    def launch_script(self, value) -> None:
        if value == 1:
            if not self.is_running():
                self.process = subprocess.Popen(
                    self.script_call, shell=True
                )  # , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.logger.info(
                    f"Launched process {self.process.pid}, invocation {self.script_call}"
                )
                self.progress.set(0)
                self.status.set(1)
            else:
                assert isinstance(self.process, subprocess.Popen)
                self.logger.info(
                    f"Run called whilst script already active (PID {self.process.pid}); ignoring"
                )
            self.run.set(0)

    async def terminate_script(self, value: int) -> None:
        if value == 1:
            if self.process is not None:
                if self.is_running():
                    self.logger.info(f"terminating process {self.process.pid}")
                    self.process.send_signal(signal.SIGABRT)
                    self.status_string.set("Stopping")
                    await asyncio.sleep(10.0)

                    retries = 0
                    while self.is_running() and retries < 10:
                        print(
                            f"Process {self.process.pid} has not terminated, waiting..."
                        )
                        await asyncio.sleep(5.0)
                        retries += 1
                    if self.is_running() and retries == 10:
                        print(
                            f"Process failed to terminate, poll result {self.process.poll()}"
                        )
                        self.status_string.set("Stop Failed")
                    else:
                        print(f"Process {self.process.pid} terminated")
                        self.process = None
                        self.status_string.set("Ready")
                else:
                    print("Process already terminated")
                    self.process = None
        self.stop.set(0)

    async def kill_script(self, value: int) -> None:
        if value == 1:
            if self.process is not None:
                if self.is_running():
                    self.logger.info(f"Killing process {self.process.pid}")
                    self.process.send_signal(signal.SIGKILL)
                    await asyncio.sleep(0.5)

                    if not self.is_running():
                        print("Process killed")
                        self.process = None
                        self.status_string.set("Ready")
                    else:
                        print(
                            f"Process failed to kill, poll result {self.process.poll()}"
                        )
                else:
                    print("Process already terminated")
                    self.process = None
        self.kill.set(0)

    def set_map_config(self, value: int) -> None:
        # assert value in self.maps["std_masks"].keys(), "%s is not a known config" % value
        # TODO: For some reason whenever I set the PV, value here is always zero regardless of the actual value of VAL.
        # Moreover, this only seems to get called once, however many times I toggle the PV.
        # Will have to work around using cagets
        assert self.optics_menu_strings is not None
        self.map_config = self.optics_menu_strings[value]
        print(self.optics_menu_strings[value])
        print(f"Map config set to {self.map_config}")

    async def load_maps(self, value: int) -> None:
        mask_value = await caget("BL22B-DI-ADOP-01:SETUP")
        print(f"Mask Value: {mask_value}")
        assert self.optics_menu_strings is not None
        assert isinstance(mask_value, int)  # TODO: This may not work
        self.map_config = self.optics_menu_strings[mask_value]
        assert self.map_config is not None, "No config set"
        map1: str = self.maps["std_masks"][self.map_config]["dm1"]
        map2: str = self.maps["std_masks"][self.map_config]["dm2"]
        print(map1)
        print(map2)
        mapstring1 = np.append(np.fromstring(map1, dtype=np.uint8, sep=""), 0)
        mapstring2 = np.append(np.fromstring(map2, dtype=np.uint8, sep=""), 0)

        await caput(f"{self.mirror_prefix[0]}:MAP_READ_PATH", mapstring1)
        await caput(f"{self.mirror_prefix[1]}:MAP_READ_PATH", mapstring2)
        await caput(f"{self.mirror_prefix[0]}:MAP_READ", 1, wait=True)
        await caput(f"{self.mirror_prefix[1]}:MAP_READ", 1, wait=True)
        await caput(f"{self.mirror_prefix[0]}:CP_ST_TO_ACT.PROC", 1, wait=True)
        await caput(f"{self.mirror_prefix[1]}:CP_ST_TO_ACT.PROC", 1, wait=True)
        self.apply_config.set(0)

    async def do_mirror_reset(self, value):
        if value == 1:
            await caput(f"{self.mirror_prefix[0]}:RESET", 1)
            await caput(f"{self.mirror_prefix[1]}:RESET", 1)
            self.reset_mirrors.set(0)
