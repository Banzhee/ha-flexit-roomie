"""Polling coordinator for one Flexit Roomie fan."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RoomieClient, RoomieError, RoomieStatus
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class RoomieCoordinator(DataUpdateCoordinator[RoomieStatus]):
    """Reads the status of one fan and shares it with the fan and sensor entities."""

    def __init__(self, hass: HomeAssistant, client: RoomieClient) -> None:
        # config_entry is picked up from the setup context, so this must be
        # constructed inside async_setup_entry.
        super().__init__(hass, _LOGGER, name=client.host, update_interval=SCAN_INTERVAL)
        self.client = client

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.client.host)},
            manufacturer="Flexit",
            model="Roomie Wifi (EcoVent v1)",
            name=self.config_entry.title if self.config_entry else self.client.host,
        )

    async def _async_update_data(self) -> RoomieStatus:
        try:
            return await self.client.get_status()
        except RoomieError as err:
            raise UpdateFailed(str(err)) from err


FlexitRoomieConfigEntry = ConfigEntry[RoomieCoordinator]
