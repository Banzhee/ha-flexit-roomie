"""Humidity sensor for Flexit Roomie."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, RoomieCoordinator


async def async_setup_platform(
    hass: HomeAssistant, config, async_add_entities: AddEntitiesCallback, discovery_info=None
) -> None:
    if discovery_info is None:
        return
    async_add_entities(RoomieHumidity(c) for c in hass.data[DOMAIN])


class RoomieHumidity(CoordinatorEntity[RoomieCoordinator], SensorEntity):
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator: RoomieCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.name} Luftfuktighet"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.client.host}_humidity"

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.humidity if self.coordinator.data else None
