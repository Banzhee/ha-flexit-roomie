"""Flexit Roomie Wifi (EcoVent v1 protocol, local UDP)."""
from __future__ import annotations

from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.const import CONF_IP_ADDRESS, CONF_NAME, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RoomieClient, RoomieError, RoomieStatus

_LOGGER = logging.getLogger(__name__)

DOMAIN = "flexit_roomie"
CONF_DEVICES = "devices"
SCAN_INTERVAL = timedelta(seconds=30)
PLATFORMS = [Platform.FAN, Platform.SENSOR]

DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_IP_ADDRESS): cv.string,
        vol.Optional(CONF_PORT, default=4000): cv.port,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [DEVICE_SCHEMA])})},
    extra=vol.ALLOW_EXTRA,
)


class RoomieCoordinator(DataUpdateCoordinator[RoomieStatus]):
    def __init__(self, hass: HomeAssistant, name: str, client: RoomieClient) -> None:
        super().__init__(hass, _LOGGER, name=name, update_interval=SCAN_INTERVAL)
        self.client = client

    async def _async_update_data(self) -> RoomieStatus:
        try:
            return await self.client.get_status()
        except RoomieError as err:
            raise UpdateFailed(str(err)) from err


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    coordinators: list[RoomieCoordinator] = []
    for device in config[DOMAIN][CONF_DEVICES]:
        client = RoomieClient(device[CONF_IP_ADDRESS], device[CONF_PORT])
        coordinator = RoomieCoordinator(hass, device[CONF_NAME], client)
        # Don't block startup if the fan is offline; entities show unavailable until it answers.
        await coordinator.async_refresh()
        coordinators.append(coordinator)
    hass.data[DOMAIN] = coordinators

    for platform in PLATFORMS:
        hass.async_create_task(async_load_platform(hass, platform, DOMAIN, {}, config))
    return True
