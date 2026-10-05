"""Humidity sensor for Flexit Roomie."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FlexitRoomieConfigEntry, RoomieCoordinator

# No name: with has_entity_name the device class supplies it, translated by HA
# ("Humidity" / "Luftfuktighet").
HUMIDITY = SensorEntityDescription(
    key="humidity",
    device_class=SensorDeviceClass.HUMIDITY,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=PERCENTAGE,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FlexitRoomieConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([RoomieHumidity(entry.runtime_data)])


class RoomieHumidity(CoordinatorEntity[RoomieCoordinator], SensorEntity):
    _attr_has_entity_name = True
    entity_description = HUMIDITY

    def __init__(self, coordinator: RoomieCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.client.host}_humidity"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.humidity if self.coordinator.data else None
