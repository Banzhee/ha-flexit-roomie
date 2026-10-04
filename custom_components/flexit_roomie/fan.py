"""Fan entity for Flexit Roomie."""
from __future__ import annotations

import math
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.percentage import percentage_to_ranged_value, ranged_value_to_percentage

from . import DOMAIN, RoomieCoordinator

SPEED_RANGE = (1, 3)
PRESET_MODES = ["ventilation", "heat_recovery", "air_supply"]  # index = protocol value


async def async_setup_platform(
    hass: HomeAssistant, config, async_add_entities: AddEntitiesCallback, discovery_info=None
) -> None:
    if discovery_info is None:
        return
    async_add_entities(RoomieFan(c) for c in hass.data[DOMAIN])


class RoomieFan(CoordinatorEntity[RoomieCoordinator], FanEntity):
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.PRESET_MODE
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )
    _attr_speed_count = 3
    _attr_preset_modes = PRESET_MODES
    _attr_icon = "mdi:hvac"
    _attr_translation_key = "ventilation"

    def __init__(self, coordinator: RoomieCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = coordinator.name
        self._attr_unique_id = f"{DOMAIN}_{coordinator.client.host}_fan"

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.is_on if self.coordinator.data else None

    @property
    def percentage(self) -> int | None:
        data = self.coordinator.data
        if data is None:
            return None
        if not data.is_on:
            return 0
        if data.speed == 4:  # manual speed set in the app, 0-255
            return round(data.manual_speed / 255 * 100)
        return ranged_value_to_percentage(SPEED_RANGE, data.speed)

    @property
    def preset_mode(self) -> str | None:
        data = self.coordinator.data
        if data is None or not 0 <= data.airflow < len(PRESET_MODES):
            return None
        return PRESET_MODES[data.airflow]

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        data = self.coordinator.data
        return {"speed_level": data.speed, "manual_speed": data.manual_speed} if data else None

    async def async_turn_on(
        self, percentage: int | None = None, preset_mode: str | None = None, **kwargs: Any
    ) -> None:
        client = self.coordinator.client
        await client.set_power(True)
        if percentage:
            await client.set_speed(math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage)))
        if preset_mode:
            await client.set_airflow(PRESET_MODES.index(preset_mode))
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_power(False)
        await self.coordinator.async_request_refresh()

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage == 0:
            await self.async_turn_off()
            return
        await self.async_turn_on(percentage=percentage)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        await self.coordinator.client.set_airflow(PRESET_MODES.index(preset_mode))
        await self.coordinator.async_request_refresh()
