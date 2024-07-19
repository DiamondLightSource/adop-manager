"""

Simulated ProcServ IOC

Creates a simulated IOC which has procServ PVs to start/stop/restart it

Arguments:
    device_name     Root name for PV generation

"""

import asyncio
import logging

from softioc import builder

from .datamodel import MbbFields


class SimulatedProcServIoc:
    ioc_statuses = ["Running", "Shutdown", "procServ Stopped", "Invalid portname"]

    def __init__(self, device_name: str) -> None:
        assert device_name is not None, "Device Name is None"

        self.logger = logging.getLogger(__name__)
        self.name = device_name
        self.ioc_status_fields = self.get_ioc_status_fields()
        self.ioc_stop_time = 2.0
        self.ioc_start_time = 5.0
        self.event_type = ""

        self.create_pvs()
        self.create_event_thread()
        self.logger.info("Created Simulated IOC: {0}".format(device_name))

    def create_event_thread(self) -> None:
        asyncio.run_coroutine_threadsafe(
            self.event_thread(), asyncio.get_running_loop()
        )

    async def event_thread(self) -> None:
        self.event = asyncio.Event()
        while True:
            await self.event.wait()

            match self.event_type:
                case "START":
                    self.logger.info(f"{self.name} starting...")
                    await asyncio.sleep(self.ioc_start_time)
                    self.status.set(0)
                    self.start.set(0)
                    self.logger.info(f"{self.name} started.")
                case "STOP":
                    self.logger.info(f"{self.name} stopping...")
                    await asyncio.sleep(self.ioc_stop_time)
                    self.status.set(1)
                    self.stop.set(0)
                    self.logger.info(f"{self.name} stopped.")
                case "RESTART":
                    self.logger.info(f"{self.name} restarting...")
                    await asyncio.sleep(self.ioc_stop_time)
                    self.status.set(1)
                    await asyncio.sleep(self.ioc_start_time)
                    self.status.set(0)
                    self.restart.set(0)
                    self.logger.info(f"{self.name} restarted.")
                case _:
                    self.logger.warn(f"Event type '{self.event_type}' unknown.")

            # Clear event type so an event isn't triggered accidentally if by chance
            # the event flag is set
            self.event_type = ""

    def create_pvs(self) -> None:
        builder.SetDeviceName(self.name)

        self.status = builder.mbbIn("STATUS", PINI="YES", **self.ioc_status_fields)

        self.start = builder.boolOut(
            "START", PINI="NO", ZNAM="Done", ONAM="Busy", on_update=self.do_start
        )

        self.stop = builder.boolOut(
            "STOP", PINI="NO", ZNAM="Done", ONAM="Busy", on_update=self.do_stop
        )

        self.restart = builder.boolOut(
            "RESTART", PINI="NO", ZNAM="Done", ONAM="Busy", on_update=self.do_restart
        )

        builder.UnsetDevice()

    def do_start(self, value: int) -> None:
        if value == 1:
            self.event_type = "START"
            self.event.set()

    def do_stop(self, value: int) -> None:
        if value == 1:
            self.event_type = "STOP"
            self.event.set()

    def do_restart(self, value: int) -> None:
        if value == 1:
            self.event_type = "RESTART"
            self.event.set()

    @staticmethod
    def get_ioc_status_fields() -> dict[str, str | int]:
        return MbbFields.generate_fields(SimulatedProcServIoc.ioc_statuses)
