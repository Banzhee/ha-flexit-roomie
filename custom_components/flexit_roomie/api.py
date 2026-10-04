"""Async UDP client for Flexit Roomie / Blauberg / TwinFresh fans (EcoVent v1 protocol).

Packets are HEADER + command + FOOTER sent to UDP port 4000. A status request
(0x01 0x00) is answered with b"master" followed by (parameter, value...) pairs.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

HEADER = bytes.fromhex("6D6F62696C65")  # "mobile"
FOOTER = bytes.fromhex("0D0A")
REPLY_HEADER = b"master"

CMD_STATUS = bytes.fromhex("0100")
CMD_TOGGLE_POWER = bytes.fromhex("0300")
CMD_SPEED = 0x04  # 1-3
CMD_AIRFLOW = 0x06  # 0-2

# Parameter id -> number of value bytes
PARAM_LENGTHS = {
    0x03: 1, 0x04: 1, 0x05: 1, 0x06: 1, 0x08: 1, 0x09: 1, 0x0B: 1, 0x0C: 1,
    0x0D: 1, 0x0E: 3, 0x0F: 3, 0x10: 3, 0x11: 3, 0x12: 1, 0x13: 1, 0x14: 1,
    0x15: 1, 0x16: 1, 0x17: 1, 0x19: 1, 0x1A: 1, 0x1B: 32, 0x1C: 4, 0x1F: 1,
    0x25: 1,
}


class RoomieError(Exception):
    """Raised when the fan does not answer or answers garbage."""


@dataclass
class RoomieStatus:
    is_on: bool
    speed: int  # 1-3, 4 = manual
    manual_speed: int  # 0-255
    airflow: int  # 0 ventilation, 1 heat recovery, 2 air supply
    humidity: int | None


def parse_status(data: bytes) -> RoomieStatus:
    if not data.startswith(REPLY_HEADER):
        raise RoomieError(f"Unexpected reply: {data.hex()}")
    body = data[len(REPLY_HEADER):]
    values: dict[int, bytes] = {}
    i = 0
    while i < len(body):
        param = body[i]
        length = PARAM_LENGTHS.get(param)
        if length is None or i + 1 + length > len(body):
            break  # unknown parameter or trailing bytes (e.g. footer)
        values[param] = body[i + 1 : i + 1 + length]
        i += 1 + length
    if 0x03 not in values:
        raise RoomieError(f"Reply without power state: {data.hex()}")

    def one(param: int, default: int = 0) -> int:
        return values[param][0] if param in values else default

    return RoomieStatus(
        is_on=one(0x03) == 1,
        speed=one(0x04, 1),
        manual_speed=one(0x05),
        airflow=one(0x06),
        humidity=one(0x08) if 0x08 in values else None,
    )


class _Protocol(asyncio.DatagramProtocol):
    def __init__(self) -> None:
        self.reply: asyncio.Future[bytes] = asyncio.get_running_loop().create_future()

    def datagram_received(self, data: bytes, addr) -> None:
        if not self.reply.done():
            self.reply.set_result(data)

    def error_received(self, exc: Exception) -> None:
        if not self.reply.done():
            self.reply.set_exception(exc)


class RoomieClient:
    """One request at a time, fresh socket per request so stale replies are ignored."""

    def __init__(self, host: str, port: int = 4000, timeout: float = 3.0, retries: int = 2) -> None:
        self.host = host
        self.port = port
        self._timeout = timeout
        self._retries = retries
        self._lock = asyncio.Lock()

    async def _request(self, command: bytes, expect_reply: bool) -> bytes | None:
        loop = asyncio.get_running_loop()
        async with self._lock:
            last_err: Exception | None = None
            for _ in range(self._retries + 1):
                transport, protocol = await loop.create_datagram_endpoint(
                    _Protocol, remote_addr=(self.host, self.port)
                )
                try:
                    transport.sendto(HEADER + command + FOOTER)
                    if not expect_reply:
                        return None
                    return await asyncio.wait_for(protocol.reply, self._timeout)
                except (asyncio.TimeoutError, OSError) as err:
                    last_err = err
                finally:
                    transport.close()
            raise RoomieError(f"No reply from {self.host}:{self.port}") from last_err

    async def get_status(self) -> RoomieStatus:
        return parse_status(await self._request(CMD_STATUS, expect_reply=True))

    async def _command(self, command: bytes) -> None:
        await self._request(command, expect_reply=False)
        await asyncio.sleep(0.3)  # give the fan time to apply before the next status read

    async def set_power(self, on: bool) -> None:
        # The fan only has a toggle command, so check the current state first.
        if (await self.get_status()).is_on != on:
            await self._command(CMD_TOGGLE_POWER)

    async def set_speed(self, speed: int) -> None:
        if not 1 <= speed <= 3:
            raise ValueError("speed must be 1-3")
        await self._command(bytes([CMD_SPEED, speed]))

    async def set_airflow(self, airflow: int) -> None:
        if not 0 <= airflow <= 2:
            raise ValueError("airflow must be 0-2")
        await self._command(bytes([CMD_AIRFLOW, airflow]))
