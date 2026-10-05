"""Boost switch for Flexit Roomie."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FlexitRoomieConfigEntry, RoomieCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FlexitRoomieConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([RoomieBoost(entry.runtime_data)])


class RoomieBoost(CoordinatorEntity[RoomieCoordinator], SwitchEntity):
    """Boost mode. Unknown on fans that do not report parameter 0x14."""

    _attr_has_entity_name = True
    _attr_translation_key = "boost"
    _attr_icon = "mdi:fan-plus"

    def __init__(self, coordinator: RoomieCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.client.host}_boost"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.boost if self.coordinator.data else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_boost(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_boost(False)
        await self.coordinator.async_request_refresh()
