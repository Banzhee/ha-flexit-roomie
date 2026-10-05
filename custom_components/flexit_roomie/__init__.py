"""Flexit Roomie Wifi (EcoVent v1 protocol, local UDP)."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import CONF_IP_ADDRESS, CONF_NAME, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .api import RoomieClient
from .const import CONF_DEVICES, DEFAULT_PORT, DOMAIN
from .coordinator import FlexitRoomieConfigEntry, RoomieCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.FAN, Platform.SENSOR, Platform.SWITCH]

DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_IP_ADDRESS): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [DEVICE_SCHEMA])})},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Import devices from a legacy configuration.yaml block."""
    if (domain_config := config.get(DOMAIN)) is None:
        return True

    _LOGGER.warning(
        "Configuring Flexit Roomie in configuration.yaml is deprecated. The devices "
        "found there have been imported, and the flexit_roomie: block can now be removed"
    )
    for device in domain_config[CONF_DEVICES]:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=dict(device)
            )
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: FlexitRoomieConfigEntry) -> bool:
    client = RoomieClient(entry.data[CONF_IP_ADDRESS], entry.data[CONF_PORT])
    coordinator = RoomieCoordinator(hass, client)
    # Raises ConfigEntryNotReady if the fan is silent, so HA retries with backoff.
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FlexitRoomieConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
